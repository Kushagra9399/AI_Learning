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
        connection = sqlite3.connect(self.db, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _now():
        return datetime.datetime.now(datetime.timezone.utc).isoformat()

    def _init_database(self):
        with self._connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('admin', 'worker')),
                    created_at TEXT NOT NULL
                );

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
                    worker_user_id INTEGER,
                    candidate TEXT,
                    level INTEGER,
                    level_suggestion TEXT,
                    level_approved INTEGER DEFAULT 0,
                    questions_draft TEXT,
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
            columns = {
                row["name"]
                for row in connection.execute(
                    "PRAGMA table_info(assessments)"
                ).fetchall()
            }
            migrations = {
                "worker_user_id": "ALTER TABLE assessments ADD COLUMN worker_user_id INTEGER",
                "questions_draft": "ALTER TABLE assessments ADD COLUMN questions_draft TEXT",
                "grading": "ALTER TABLE assessments ADD COLUMN grading TEXT",
                "marks_locked": "ALTER TABLE assessments ADD COLUMN marks_locked INTEGER DEFAULT 0",
                "marks_locked_at": "ALTER TABLE assessments ADD COLUMN marks_locked_at TEXT",
            }
            for name, statement in migrations.items():
                if name not in columns:
                    connection.execute(statement)

    def create_user(self, username, password_hash, role):
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO users (username, password_hash, role, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (username, password_hash, role, self._now()),
            )

    def get_user_by_username(self, username):
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM users WHERE username=?",
                (username,),
            ).fetchone()
        return dict(row) if row else None

    def get_user(self, user_id):
        with self._connection() as connection:
            row = connection.execute(
                "SELECT id, username, role, created_at FROM users WHERE id=?",
                (user_id,),
            ).fetchone()
        return dict(row) if row else None

    def create_worker_assessment(self, worker_user_id, candidate):
        with self._connection() as connection:
            existing = connection.execute(
                """
                SELECT assessment_id, level, level_suggestion,
                       level_approved, questions_approved, started
                FROM assessments
                WHERE worker_user_id=?
                  AND assessment_id NOT IN (
                      SELECT assessment_id FROM submissions
                  )
                ORDER BY a.created_at DESC
                LIMIT 1
                """,
                (worker_user_id,),
            ).fetchone()

            if existing:
                return {
                    "assessment_id": existing["assessment_id"],
                    "existing": True,
                    "level": existing["level"],
                    "level_suggestion": (
                        json.loads(existing["level_suggestion"])
                        if existing["level_suggestion"]
                        else None
                    ),
                    "level_approved": bool(existing["level_approved"]),
                    "questions_approved": bool(existing["questions_approved"]),
                    "started": bool(existing["started"]),
                }

            assessment_id = "assessment_" + uuid.uuid4().hex[:12]
            connection.execute(
                """
                INSERT INTO assessments
                (assessment_id, worker_user_id, candidate, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    assessment_id,
                    worker_user_id,
                    json.dumps(candidate),
                    self._now(),
                ),
            )

        return {
            "assessment_id": assessment_id,
            "existing": False,
            "level": None,
            "level_suggestion": None,
            "level_approved": False,
            "questions_approved": False,
            "started": False,
        }

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
                    job_id, kind, "queued", 0, None, None,
                    json.dumps(payload), 0, now, now,
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
                        SET status='completed', progress=100, result=?, updated_at=?
                        WHERE id=?
                        """,
                        (json.dumps(result), self._now(), job["id"]),
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

        threading.Thread(target=runner, daemon=True).start()

    def _assessment(self, assessment_id):
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM assessments WHERE assessment_id=?",
                (assessment_id,),
            ).fetchone()
        return dict(row) if row else None

    def save_level_suggestion(self, assessment_id, suggestion):
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT level_approved FROM assessments WHERE assessment_id=?
                """,
                (assessment_id,),
            ).fetchone()
            if not row or row["level_approved"]:
                return False
            connection.execute(
                "UPDATE assessments SET level_suggestion=? WHERE assessment_id=?",
                (json.dumps(suggestion), assessment_id),
            )
        return True

    def approve_level(self, payload):
        assessment_id = payload["assessment_id"]
        level = int(payload["nsqf_level"])
        if not 1 <= level <= 8:
            return {"approved": False, "reason": "invalid_nsqf_level"}

        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT level, level_approved
                FROM assessments WHERE assessment_id=?
                """,
                (assessment_id,),
            ).fetchone()
            if not row:
                return {"approved": False, "reason": "assessment_not_found"}
            if row["level_approved"]:
                return {
                    "assessment_id": assessment_id,
                    "approved": False,
                    "reason": "level_already_approved",
                    "level": row["level"],
                }

            connection.execute(
                """
                UPDATE assessments
                SET level=?, level_suggestion=?, level_approved=1
                WHERE assessment_id=? AND level_approved=0
                """,
                (level, json.dumps(payload.get("suggestion", {})), assessment_id),
            )

        return {"assessment_id": assessment_id, "level": level, "approved": True}

    def save_question_draft(self, assessment_id, questions):
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT level_approved, questions_approved
                FROM assessments WHERE assessment_id=?
                """,
                (assessment_id,),
            ).fetchone()
            if not row or not row["level_approved"] or row["questions_approved"]:
                return False
            connection.execute(
                """
                UPDATE assessments SET questions_draft=?
                WHERE assessment_id=? AND questions_approved=0
                """,
                (json.dumps(questions), assessment_id),
            )
        return True

    def approve_questions(self, payload):
        questions = payload.get("questions", [])
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT level_approved, questions_approved, questions_draft
                FROM assessments WHERE assessment_id=?
                """,
                (payload["assessment_id"],),
            ).fetchone()
            if not row:
                return {"assessment_id": payload["assessment_id"], "approved": False, "reason": "assessment_not_found"}
            if not row["level_approved"]:
                return {"assessment_id": payload["assessment_id"], "approved": False, "reason": "level_not_approved"}
            if row["questions_approved"]:
                return {"assessment_id": payload["assessment_id"], "approved": False, "reason": "questions_already_approved"}

            connection.execute(
                """
                UPDATE assessments
                SET questions=?, questions_draft=NULL, questions_approved=1
                WHERE assessment_id=? AND questions_approved=0
                """,
                (json.dumps(questions), payload["assessment_id"]),
            )
        return {"assessment_id": payload["assessment_id"], "approved": True}

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
            "result": json.loads(row["result"]) if row["result"] else None,
            "error": row["error"],
            "acknowledged": bool(row["acknowledged"]),
        }

    def acknowledge_job(self, job_id):
        with self._connection() as connection:
            connection.execute(
                "UPDATE jobs SET acknowledged=1 WHERE id=?",
                (job_id,),
            )

    @staticmethod
    def _candidate(row):
        return json.loads(row["candidate"]) if row["candidate"] else {}

    @staticmethod
    def _json_or_none(value):
        return json.loads(value) if value else None

    def admin_candidate(self, assessment_id):
        row = self._assessment(assessment_id)
        if not row:
            return None
        with self._connection() as connection:
            submission = connection.execute(
                """
                SELECT payload, created_at
                FROM submissions
                WHERE assessment_id=?
                """,
                (assessment_id,),
            ).fetchone()
            evidence = connection.execute(
                """
                SELECT evidence_id, task_id, filename, media_type, created_at
                FROM evidence
                WHERE assessment_id=?
                ORDER BY created_at
                """,
                (assessment_id,),
            ).fetchall()

        return {
            "assessment_id": assessment_id,
            "candidate": self._candidate(row),
            "level": row["level"],
            "level_suggestion": self._json_or_none(row["level_suggestion"]),
            "level_approved": bool(row["level_approved"]),
            "questions_draft": self._json_or_none(row["questions_draft"]),
            "questions": self._json_or_none(row["questions"]),
            "questions_approved": bool(row["questions_approved"]),
            "started": bool(row["started"]),
            "marks_locked": bool(row["marks_locked"]),
            "marks_locked_at": row["marks_locked_at"],
            "grading": self._json_or_none(row["grading"]),
            "submitted": submission is not None,
            "submitted_at": submission["created_at"] if submission else None,
            "submission": (
                json.loads(submission["payload"])
                if submission else None
            ),
            "evidence": [dict(item) for item in evidence],
        }

    def admin_assessments(self):
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT a.assessment_id, a.candidate, a.level, a.level_approved,
                       a.questions_approved, a.started, a.created_at,
                       CASE WHEN s.assessment_id IS NOT NULL THEN 1 ELSE 0 END AS submitted,
                       s.created_at AS submitted_at
                FROM assessments a
                LEFT JOIN submissions s ON s.assessment_id = a.assessment_id
                ORDER BY created_at DESC
                """
            ).fetchall()
        result = []
        for row in rows:
            candidate = self._candidate(row)
            result.append(
                {
                    "assessment_id": row["assessment_id"],
                    "candidate": candidate,
                    "level": row["level"],
                    "level_approved": bool(row["level_approved"]),
                    "questions_approved": bool(row["questions_approved"]),
                    "started": bool(row["started"]),
                    "submitted": bool(row["submitted"]),
                    "submitted_at": row["submitted_at"],
                    "created_at": row["created_at"],
                }
            )
        return result

    def worker_assessment(self, worker_user_id):
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM assessments
                WHERE worker_user_id=?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (worker_user_id,),
            ).fetchone()
        if not row:
            return {"exists": False}

        questions = self._json_or_none(row["questions"])
        return {
            "exists": True,
            "assessment_id": row["assessment_id"],
            "candidate": self._candidate(row),
            "level": row["level"],
            "level_suggestion": self._json_or_none(row["level_suggestion"]),
            "level_approved": bool(row["level_approved"]),
            "questions": questions if row["questions_approved"] else None,
            "questions_approved": bool(row["questions_approved"]),
            "started": bool(row["started"]),
            "marks_locked": bool(row["marks_locked"]),
            "marks_locked_at": row["marks_locked_at"],
            "grading": self._json_or_none(row["grading"]) if row["marks_locked"] else None,
            "total_marks": (self._json_or_none(row["grading"]) or {}).get("total_marks") if row["marks_locked"] else None,
            "max_marks": (self._json_or_none(row["grading"]) or {}).get("max_marks") if row["marks_locked"] else None,
            "submitted": self.has_submission(row["assessment_id"]),
        }

    def user_assessment(self, assessment_id, worker_user_id):
        row = self._assessment(assessment_id)
        if not row or row["worker_user_id"] != worker_user_id:
            return {"exists": False}
        return self.worker_assessment(worker_user_id)

    def start_assessment(self, assessment_id, worker_user_id):
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT started, questions_approved, worker_user_id
                FROM assessments WHERE assessment_id=?
                """,
                (assessment_id,),
            ).fetchone()
            if not row or row["worker_user_id"] != worker_user_id:
                return {"accepted": False, "reason": "assessment_not_found"}
            if not row["questions_approved"]:
                return {"accepted": False, "reason": "questions_not_approved"}
            if row["started"]:
                return {"accepted": False, "reason": "attempt_already_started"}
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

    def submit(self, payload, worker_user_id):
        assessment_id = payload["assessment_id"]
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT started, worker_user_id
                FROM assessments WHERE assessment_id=?
                """,
                (assessment_id,),
            ).fetchone()
            if not row or row["worker_user_id"] != worker_user_id:
                return {"accepted": False, "reason": "assessment_not_found"}
            if not row["started"]:
                return {"accepted": False, "reason": "assessment_not_started"}
            try:
                connection.execute(
                    """
                    INSERT INTO submissions
                    (assessment_id, payload, created_at)
                    VALUES (?, ?, ?)
                    """,
                    (assessment_id, json.dumps(payload), self._now()),
                )
            except sqlite3.IntegrityError:
                return {"accepted": False, "reason": "single_attempt_already_submitted"}
        return {"accepted": True, "assessment_id": assessment_id}


    def lock_grading(self, assessment_id, payload):
        with self._connection() as connection:
            row = connection.execute("SELECT questions, questions_approved, marks_locked FROM assessments WHERE assessment_id=?", (assessment_id,)).fetchone()
            if not row:
                return {"accepted": False, "reason": "assessment_not_found"}
            if not row["questions_approved"]:
                return {"accepted": False, "reason": "questions_not_approved"}
            if row["marks_locked"]:
                return {"accepted": False, "reason": "marks_already_locked"}
            submission = connection.execute("SELECT payload FROM submissions WHERE assessment_id=?", (assessment_id,)).fetchone()
            if not submission:
                return {"accepted": False, "reason": "assessment_submission_not_found"}

            questions = json.loads(row["questions"] or "[]")
            submitted = json.loads(submission["payload"] or "{}")
            answers = {str(a.get("id")): a for a in submitted.get("answers", [])}
            supplied = payload.get("marks", {})
            grading, total, maximum = [], 0, 0

            for question in questions:
                qid = str(question.get("id"))
                max_marks = max(0, int(question.get("marks", 0)))
                maximum += max_marks
                answer = answers.get(qid, {})
                status, awarded = "unanswered", 0
                if question.get("type") == "mcq":
                    try:
                        selected = int(answer.get("selected_option", -1))
                    except (TypeError, ValueError):
                        selected = -1
                    correct = int(question.get("correct_option", -1))
                    if selected >= 0:
                        status = "correct" if selected == correct else "incorrect"
                    awarded = max_marks if status == "correct" else 0
                else:
                    try:
                        awarded = int(supplied.get(qid, 0))
                    except (TypeError, ValueError):
                        awarded = 0
                    if awarded < 0 or awarded > max_marks:
                        return {"accepted": False, "reason": f"invalid_marks_for_{qid}"}
                    status = "marked" if awarded > 0 else "incorrect"
                total += awarded
                grading.append({"question_id": qid, "status": status, "marks_awarded": awarded, "max_marks": max_marks})

            grading_record = {"items": grading, "total_marks": total, "max_marks": maximum, "locked": True, "locked_at": self._now()}
            connection.execute("UPDATE assessments SET grading=?, marks_locked=1, marks_locked_at=? WHERE assessment_id=? AND marks_locked=0", (json.dumps(grading_record), grading_record["locked_at"], assessment_id))
        return {"accepted": True, "assessment_id": assessment_id, **grading_record}

    def worker_result(self, assessment_id, worker_user_id):
        row = self._assessment(assessment_id)
        if not row or row["worker_user_id"] != worker_user_id:
            return None
        if not row["marks_locked"]:
            return {"assessment_id": assessment_id, "locked": False, "total_marks": None, "max_marks": None}
        grading = self._json_or_none(row["grading"]) or {}
        return {
            "assessment_id": assessment_id,
            "locked": True,
            "total_marks": grading.get("total_marks", 0),
            "max_marks": grading.get("max_marks", 0),
            "locked_at": row["marks_locked_at"],
        }

    def add_evidence(self, evidence_id, assessment_id, task_id, filename, media_type, path, worker_user_id):
        with self._connection() as connection:
            row = connection.execute(
                "SELECT worker_user_id FROM assessments WHERE assessment_id=?",
                (assessment_id,),
            ).fetchone()
            if not row or row["worker_user_id"] != worker_user_id:
                return False
            connection.execute(
                """
                INSERT INTO evidence
                (evidence_id, assessment_id, task_id, filename, media_type, path, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (evidence_id, assessment_id, task_id, filename, media_type, path, self._now()),
            )
        return True

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
                FROM evidence WHERE assessment_id=?
                """,
                (assessment_id,),
            ).fetchall()
        return {
            "assessment_id": assessment_id,
            "submission": json.loads(submission["payload"]) if submission else None,
            "assessment": dict(assessment) if assessment else None,
            "evidence": [dict(item) for item in evidence],
            "signoff": json.loads(signoff["payload"]) if signoff else None,
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
                (assessment_id, json.dumps(payload), self._now()),
            )
        return {
            "assessment_id": assessment_id,
            "signed_off": True,
            "final_authority": "human_assessor",
        }


store = Store()
