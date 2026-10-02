import datetime
import json
import sqlite3
import threading
import uuid
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "rpl.sqlite3"

class Store:
    def __init__(self):
        self.lock = threading.Lock()
        self.db = DB_PATH
        self._init()

    def _conn(self):
        c = sqlite3.connect(self.db, check_same_thread=False)
        c.row_factory = sqlite3.Row
        return c

    def _init(self):
        with self._conn() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS jobs (
              id TEXT PRIMARY KEY, type TEXT, status TEXT, progress INTEGER,
              result TEXT, error TEXT, payload TEXT, acknowledged INTEGER DEFAULT 0,
              created_at TEXT, updated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS submissions (
              assessment_id TEXT PRIMARY KEY, payload TEXT, created_at TEXT
            );
            CREATE TABLE IF NOT EXISTS signoffs (
              assessment_id TEXT PRIMARY KEY, payload TEXT, created_at TEXT
            );
            CREATE TABLE IF NOT EXISTS evidence (
              evidence_id TEXT PRIMARY KEY, assessment_id TEXT, task_id TEXT,
              filename TEXT, media_type TEXT, path TEXT, created_at TEXT
            );
            """)

    def job(self, kind, payload):
        jid = "job_" + uuid.uuid4().hex[:12]
        now = datetime.datetime.utcnow().isoformat()
        with self._conn() as c:
            c.execute("INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?,?)",
                      (jid,kind,"queued",0,None,None,json.dumps(payload),0,now,now))
        return {"id":jid,"type":kind,"status":"queued","progress":0}

    def run_async(self, job, fn):
        def run():
            try:
                with self._conn() as c:
                    c.execute("UPDATE jobs SET status='running',progress=20,updated_at=? WHERE id=?",
                              (datetime.datetime.utcnow().isoformat(),job["id"]))
                result = fn()
                with self._conn() as c:
                    c.execute("UPDATE jobs SET status='completed',progress=100,result=?,updated_at=? WHERE id=?",
                              (json.dumps(result),datetime.datetime.utcnow().isoformat(),job["id"]))
            except Exception as e:
                with self._conn() as c:
                    c.execute("UPDATE jobs SET status='failed',error=?,updated_at=? WHERE id=?",
                              (str(e),datetime.datetime.utcnow().isoformat(),job["id"]))
        threading.Thread(target=run, daemon=True).start()

    def get(self,jid):
        with self._conn() as c:
            r=c.execute("SELECT * FROM jobs WHERE id=?",(jid,)).fetchone()
        if not r: return None
        return {"id":r["id"],"type":r["type"],"status":r["status"],"progress":r["progress"],
                "result":json.loads(r["result"]) if r["result"] else None,"error":r["error"],
                "acknowledged":bool(r["acknowledged"])}

    def ack(self,jid):
        with self._conn() as c:
            c.execute("UPDATE jobs SET acknowledged=1 WHERE id=?",(jid,))

    def submit(self,p):
        aid=p["assessment_id"]
        with self._conn() as c:
            try:
                c.execute("INSERT INTO submissions VALUES (?,?,?)",(aid,json.dumps(p),datetime.datetime.utcnow().isoformat()))
                return True
            except sqlite3.IntegrityError:
                return False

    def assessor(self,aid):
        with self._conn() as c:
            s=c.execute("SELECT payload FROM submissions WHERE assessment_id=?",(aid,)).fetchone()
            f=c.execute("SELECT payload FROM signoffs WHERE assessment_id=?",(aid,)).fetchone()
        return {"assessment_id":aid,"submission":json.loads(s["payload"]) if s else None,
                "signoff":json.loads(f["payload"]) if f else None,"final_authority":"human_assessor"}

    def signoff(self,aid,p):
        with self._conn() as c:
            c.execute("INSERT OR REPLACE INTO signoffs VALUES (?,?,?)",(aid,json.dumps(p),datetime.datetime.utcnow().isoformat()))
        return {"assessment_id":aid,"signed_off":True,"final_authority":"human_assessor"}

store=Store()
