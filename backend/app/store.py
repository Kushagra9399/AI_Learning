import datetime,json,sqlite3,threading,uuid
from pathlib import Path
DB_PATH=Path(__file__).resolve().parents[1]/"rpl.sqlite3"
class Store:
 def __init__(self): self.db=DB_PATH; self._init()
 def _conn(self):
  c=sqlite3.connect(self.db,check_same_thread=False); c.row_factory=sqlite3.Row; return c
 def _init(self):
  with self._conn() as c:
   c.executescript("""CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,type TEXT,status TEXT,progress INTEGER,result TEXT,error TEXT,payload TEXT,acknowledged INTEGER DEFAULT 0,created_at TEXT,updated_at TEXT);
   CREATE TABLE IF NOT EXISTS submissions(assessment_id TEXT PRIMARY KEY,payload TEXT,created_at TEXT);
   CREATE TABLE IF NOT EXISTS assessments(assessment_id TEXT PRIMARY KEY,candidate TEXT,level INTEGER,level_suggestion TEXT,level_approved INTEGER DEFAULT 0,questions TEXT,questions_approved INTEGER DEFAULT 0,started INTEGER DEFAULT 0,created_at TEXT);
   CREATE TABLE IF NOT EXISTS signoffs(assessment_id TEXT PRIMARY KEY,payload TEXT,created_at TEXT);
   CREATE TABLE IF NOT EXISTS evidence(evidence_id TEXT PRIMARY KEY,assessment_id TEXT,task_id TEXT,filename TEXT,media_type TEXT,path TEXT,created_at TEXT);""")
 def job(self,kind,payload):
  jid="job_"+uuid.uuid4().hex[:12]; now=datetime.datetime.utcnow().isoformat()
  with self._conn() as c:c.execute("INSERT INTO jobs VALUES(?,?,?,?,?,?,?,?,?,?)",(jid,kind,"queued",0,None,None,json.dumps(payload),0,now,now))
  return {"id":jid,"status":"queued"}
 def run_async(self,job,fn):
  def run():
   try:
    with self._conn() as c:c.execute("UPDATE jobs SET status='running',progress=20,updated_at=? WHERE id=?",(datetime.datetime.utcnow().isoformat(),job["id"]))
    result=fn()
    with self._conn() as c:c.execute("UPDATE jobs SET status='completed',progress=100,result=?,updated_at=? WHERE id=?",(json.dumps(result),datetime.datetime.utcnow().isoformat(),job["id"]))
   except Exception as e:
    with self._conn() as c:c.execute("UPDATE jobs SET status='failed',error=?,updated_at=? WHERE id=?",(str(e),datetime.datetime.utcnow().isoformat(),job["id"]))
  threading.Thread(target=run,daemon=True).start()
 def get(self,jid):
  with self._conn() as c:r=c.execute("SELECT * FROM jobs WHERE id=?",(jid,)).fetchone()
  if not r:return None
  return {"id":r["id"],"type":r["type"],"status":r["status"],"progress":r["progress"],"result":json.loads(r["result"]) if r["result"] else None,"error":r["error"],"acknowledged":bool(r["acknowledged"])}
 def ack(self,jid):
  with self._conn() as c:c.execute("UPDATE jobs SET acknowledged=1 WHERE id=?",(jid,))
 def ensure_assessment(self,aid,candidate):
  with self._conn() as c:c.execute("INSERT OR IGNORE INTO assessments VALUES(?,?,?,?,?,?,?,?,?,?)",(aid,json.dumps(candidate),None,None,0,None,0,0,datetime.datetime.utcnow().isoformat()))
 def approve_level(self,p):
  aid=p["assessment_id"]; self.ensure_assessment(aid,p.get("candidate",{}))
  with self._conn() as c:c.execute("UPDATE assessments SET level=?,level_suggestion=?,level_approved=1 WHERE assessment_id=?",(int(p["nsqf_level"]),json.dumps(p.get("suggestion",{})),aid))
  return {"assessment_id":aid,"level":int(p["nsqf_level"]),"approved":True}
 def approve_questions(self,p):
  with self._conn() as c:c.execute("UPDATE assessments SET questions=?,questions_approved=1 WHERE assessment_id=?",(json.dumps(p["questions"]),p["assessment_id"]))
  return {"assessment_id":p["assessment_id"],"approved":True}
 def admin_candidate(self,aid):
  with self._conn() as c:r=c.execute("SELECT * FROM assessments WHERE assessment_id=?",(aid,)).fetchone()
  return dict(r) if r else {"assessment_id":aid}
 def user_assessment(self,aid):
  with self._conn() as c:r=c.execute("SELECT * FROM assessments WHERE assessment_id=?",(aid,)).fetchone()
  if not r:return {"exists":False}
  return {"exists":True,"assessment_id":aid,"level":r["level"],"level_approved":bool(r["level_approved"]),"questions":json.loads(r["questions"]) if r["questions"] and r["questions_approved"] else None,"questions_approved":bool(r["questions_approved"]),"started":bool(r["started"])}
 def start_assessment(self,aid):
  with self._conn() as c:
   r=c.execute("SELECT started,questions_approved FROM assessments WHERE assessment_id=?",(aid,)).fetchone()
   if not r:return {"accepted":False,"reason":"assessment_not_found"}
   if not r["questions_approved"]:return {"accepted":False,"reason":"questions_not_approved"}
   if r["started"]:return {"accepted":False,"reason":"attempt_already_started"}
   c.execute("UPDATE assessments SET started=1 WHERE assessment_id=?",(aid,))
  return {"accepted":True,"started":True}
 def submit(self,p):
  aid=p["assessment_id"]
  with self._conn() as c:
   r=c.execute("SELECT started FROM assessments WHERE assessment_id=?",(aid,)).fetchone()
   if not r or not r["started"]:return {"accepted":False,"reason":"assessment_not_started"}
   try:c.execute("INSERT INTO submissions VALUES(?,?,?)",(aid,json.dumps(p),datetime.datetime.utcnow().isoformat()))
   except sqlite3.IntegrityError:return {"accepted":False,"reason":"single_attempt_already_submitted"}
  return {"accepted":True,"assessment_id":aid}
 def add_evidence(self,*args):
  with self._conn() as c:c.execute("INSERT INTO evidence VALUES(?,?,?,?,?,?,?)",(*args,datetime.datetime.utcnow().isoformat()))
 def assessor(self,aid):
  with self._conn() as c:
   s=c.execute("SELECT payload FROM submissions WHERE assessment_id=?",(aid,)).fetchone()
   a=c.execute("SELECT * FROM assessments WHERE assessment_id=?",(aid,)).fetchone()
   f=c.execute("SELECT payload FROM signoffs WHERE assessment_id=?",(aid,)).fetchone()
   ev=c.execute("SELECT evidence_id,task_id,filename,media_type,created_at FROM evidence WHERE assessment_id=?",(aid,)).fetchall()
  return {"assessment_id":aid,"submission":json.loads(s["payload"]) if s else None,"assessment":dict(a) if a else None,"evidence":[dict(x) for x in ev],"signoff":json.loads(f["payload"]) if f else None,"final_authority":"human_assessor"}
 def signoff(self,aid,p):
  with self._conn() as c:c.execute("INSERT OR REPLACE INTO signoffs VALUES(?,?,?)",(aid,json.dumps(p),datetime.datetime.utcnow().isoformat()))
  return {"assessment_id":aid,"signed_off":True,"final_authority":"human_assessor"}
store=Store()
