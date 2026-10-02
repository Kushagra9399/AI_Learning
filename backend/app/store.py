import datetime
import json
import sqlite3
import threading
import uuid
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[1] / "rpl.sqlite3"


class Store:
    def __init__(self):
        self.db = DB_PATH
        self._init_database()

    def _connection(self):
        connection = sqlite3.connect(
            self.db,
            check_same_thread=False,
        )
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _now():
        return datetime.datetime.now(datetime.timezone.utc).isoformat()

    def _init_database(self):
        with self._connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    type TEXT,
                    status TEXT,
                    progress INTEGER,
                    result TEXT,
                    error TEXT,
                    payload TEXT,
                    acknowledged INTEGER DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT
                );

                CREATE TABLE IF NOT EXISTS submissions (
                    assessment_id TEXT PRIMARY KEY,
                    payload TEXT,
                    created_at TEXT
                );

                CREATE TABLE IF NOT EXISTS assessments (
                    assessment_id TEXT PRIMARY KEY,
                    candidate TEXT,
                    level INTEGER,
                    level_suggestion TEXT,
                    level_approved INTEGER DEFAULT 0,
                    questions TEXT,
                    questions_approved INTEGER DEFAULT 0,
                    started INTEGER DEFAULT 0,
                    created_at TEXT
                );

                CREATE TABLE IF NOT EXISTS signoffs (
                    assessment_id TEXT PRIMARY KEY,
                    payload TEXT,
                    created_at TEXT
                );

                CREATE TABLE IF NOT EXISTS evidence (
                    evidence_id TEXT PRIMARY KEY,
                    assessment_id TEXT,
                    task_id TEXT,
                    filename TEXT,
                    media_type TEXT,
                    path TEXT,
                    created_at TEXT
                );
                """
            )

    def ensure_assessment(self, assessment_id, candidate):
        with self._connection() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO assessments
                (assessment_id, candidate, created_at)
                VALUES (?, ?, ?)
                """,
                (
                    assessment_id,
                    json.dumps(candidate),
                    self._now(),
                ),
            )

    def job(self, kind, payload):
        job_id = "job_" + uuid.uuid4().hex[:12]
        now = self._now()

        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO jobs
                (id, type, status, progress, result, error, payload,
                 acknowledged, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    kind,
                    "queued",
                    0,
                    None,
                    None,
                    json.dumps(payload),
                    0,
                    now,
                    now,
                ),
            )

        return {"id": job_id, "status": "queued"}

    def run_async(self, job, function):
        def runner():
            try:
                with self._connection() as connection:
                    connection.execute(
                        "UPDATE jobs SET status='running', progress=20, updated_at=? WHERE id=?",
                        (self._now(), job["id"]),
                    )

                result = function()

                with self._connection() as connection:
                    connection.execute(
                        """
                        UPDATE jobs
                        SET status='completed', progress=100, result=?,
                            updated_at=?
                        WHERE id=?
                        """,
                        (
                            json.dumps(result),
                            self._now(),
                            job["id"],
                        ),
                    )
            except Exception as exc:
                with self._connection() as connection:
                    connection.execute(
                        """
                        UPDATE jobs
                        SET status='failed', error=?, updated_at=?
                        WHERE id=?
                        """,
                        (str(exc), self._now(), job["id"]),
                    )

        threading.Thread(
            target=runner,
            daemon=True,
        ).start()

    def save_level_suggestion(self, assessment_id, suggestion):
        with self._connection() as connection:
            connection.execute(
                """
                UPDATE assessments
                SET level_suggestion=?
                WHERE assessment_id=?
                """,
                (json.dumps(suggestion), assessment_id),
            )

    def approve_level(self, payload):
        assessment_id = payload["assessment_id"]
        self.ensure_assessment(
            assessment_id,
            payload.get("candidate", {}),
        )

        with self._connection() as connection:
            connection.execute(
                """
                UPDATE assessments
                SET level=?, level_suggestion=?, level_approved=1
                WHERE assessment_id=?
                """,
                (
                    int(payload["nsqf_level"]),
                    json.dumps(payload.get("suggestion", {})),
                    assessment_id,
                ),
            )

        return {
            "assessment_id": assessment_id,
            "level": int(payload["nsqf_level"]),
            "approved": True,
        }

    def approve_questions(self, payload):
        questions = payload.get("questions", [])

        with self._connection() as connection:
            result = connection.execute(
                """
                UPDATE assessments
                SET questions=?, questions_approved=1
                WHERE assessment_id=? AND level_approved=1
                """,
                (
                    json.dumps(questions),
                    payload["assessment_id"],
                ),
            )

        if result.rowcount == 0:
            return {
                "assessment_id": payload["assessment_id"],
                "approved": False,
                "reason": "level_not_approved_or_assessment_not_found",
            }

        return {
            "assessment_id": payload["assessment_id"],
            "approved": True,
        }

    def get_job(self, job_id):
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM jobs WHERE id=?",
                (job_id,),
            ).fetchone()

        if not row:
            return None

        return {
            "id": row["id"],
            "type": row["type"],
            "status": row["status"],
            "progress": row["progress"],
            "result": (
                json.loads(row["result"])
                if row["result"]
                else None
            ),
            "error": row["error"],
            "acknowledged": bool(row["acknowledged"]),
        }

    def acknowledge_job(self, job_id):
        with self._connection() as connection:
            connection.execute(
                "UPDATE jobs SET acknowledged=1 WHERE id=?",
                (job_id,),
            )

    def admin_candidate(self, assessment_id):
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM assessments WHERE assessment_id=?",
                (assessment_id,),
            ).fetchone()

        if not row:
            return {"assessment_id": assessment_id}

        return dict(row)

    def user_assessment(self, assessment_id):
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM assessments WHERE assessment_id=?",
                (assessment_id,),
            ).fetchone()

        if not row:
            return {"exists": False}

        return {
            "exists": True,
            "assessment_id": assessment_id,
            "level": row["level"],
            "level_approved": bool(row["level_approved"]),
            "questions": (
                json.loads(row["questions"])
                if row["questions"] and row["questions_approved"]
                else None
            ),
            "questions_approved": bool(row["questions_approved"]),
            "started": bool(row["started"]),
            "submitted": self.has_submission(assessment_id),
        }

    def start_assessment(self, assessment_id):
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT started, questions_approved
                FROM assessments
                WHERE assessment_id=?
                """,
                (assessment_id,),
            ).fetchone()

            if not row:
                return {
                    "accepted": False,
                    "reason": "assessment_not_found",
                }

            if not row["questions_approved"]:
                return {
                    "accepted": False,
                    "reason": "questions_not_approved",
                }

            if row["started"]:
                return {
                    "accepted": False,
                    "reason": "attempt_already_started",
                }

            connection.execute(
                "UPDATE assessments SET started=1 WHERE assessment_id=?",
                (assessment_id,),
            )

        return {"accepted": True, "started": True}

    def has_submission(self, assessment_id):
        with self._connection() as connection:
            row = connection.execute(
                "SELECT 1 FROM submissions WHERE assessment_id=?",
                (assessment_id,),
            ).fetchone()
        return row is not None

    def submit(self, payload):
        assessment_id = payload["assessment_id"]

        with self._connection() as connection:
            row = connection.execute(
                "SELECT started FROM assessments WHERE assessment_id=?",
                (assessment_id,),
            ).fetchone()

            if not row or not row["started"]:
                return {
                    "accepted": False,
                    "reason": "assessment_not_started",
                }

            try:
                connection.execute(
                    """
                    INSERT INTO submissions
                    (assessment_id, payload, created_at)
                    VALUES (?, ?, ?)
                    """,
                    (
                        assessment_id,
                        json.dumps(payload),
                        self._now(),
                    ),
                )
            except sqlite3.IntegrityError:
                return {
                    "accepted": False,
                    "reason": "single_attempt_already_submitted",
                }

        return {
            "accepted": True,
            "assessment_id": assessment_id,
        }

    def add_evidence(
        self,
        evidence_id,
        assessment_id,
        task_id,
        filename,
        media_type,
        path,
    ):
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO evidence
                (evidence_id, assessment_id, task_id, filename,
                 media_type, path, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    evidence_id,
                    assessment_id,
                    task_id,
                    filename,
                    media_type,
                    path,
                    self._now(),
                ),
            )

    def assessor(self, assessment_id):
        with self._connection() as connection:
            submission = connection.execute(
                "SELECT payload FROM submissions WHERE assessment_id=?",
                (assessment_id,),
            ).fetchone()
            assessment = connection.execute(
                "SELECT * FROM assessments WHERE assessment_id=?",
                (assessment_id,),
            ).fetchone()
            signoff = connection.execute(
                "SELECT payload FROM signoffs WHERE assessment_id=?",
                (assessment_id,),
            ).fetchone()
            evidence = connection.execute(
                """
                SELECT evidence_id, task_id, filename, media_type, created_at
                FROM evidence
                WHERE assessment_id=?
                """,
                (assessment_id,),
            ).fetchall()

        return {
            "assessment_id": assessment_id,
            "submission": (
                json.loads(submission["payload"])
                if submission
                else None
            ),
            "assessment": dict(assessment) if assessment else None,
            "evidence": [dict(item) for item in evidence],
            "signoff": (
                json.loads(signoff["payload"])
                if signoff
                else None
            ),
            "final_authority": "human_assessor",
        }

    def signoff(self, assessment_id, payload):
        with self._connection() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO signoffs
                (assessment_id, payload, created_at)
                VALUES (?, ?, ?)
                """,
                (
                    assessment_id,
                    json.dumps(payload),
                    self._now(),
                ),
            )

        return {
            "assessment_id": assessment_id,
            "signed_off": True,
            "final_authority": "human_assessor",
        }


store = Store()
