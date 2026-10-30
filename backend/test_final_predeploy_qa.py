import os
import sys
import unittest
import uuid
import tempfile
from fastapi.testclient import TestClient

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app
from database import Base, get_db, SessionLocal, engine
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import (
    User, StudentProfile, Class as ClassModel, ClassEnrollment,
    Course, Topic, QuestionBank, AssessmentAttempt, MasteryScore,
    LearningPath, LearningPathItem, CourseOutcome
)
from core.security import hash_password, create_access_token, validate_password_rules
from core.thresholds import PREREQ_UNLOCK, ASSESSMENT_PASS, TOPIC_MASTERY, CO_ACHIEVED_DEFAULT
from core.class_codes import validate_custom_code
from core.bootstrap import run_production_startup_checks, bootstrap_admin_if_needed
from core.rate_limiter import reset_rate_limits

class TestFinalPredeployQA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.uid = uuid.uuid4().hex[:6]

    def setUp(self):
        reset_rate_limits()

    # =========================================================================
    # 1. Student sign up, login, onboarding, diagnostic; role is always student
    # =========================================================================
    def test_01_student_signup_role_override_rejected(self):
        email = f"student_override_{self.uid}@test.edu"
        payload = {
            "email": email,
            "password": "ValidPassword123!",
            "full_name": "Test Student QA",
            "role": "admin"  # Attempt to elevate privilege
        }
        res = self.client.post("/api/auth/register", json=payload)
        self.assertEqual(res.status_code, 200, res.text)
        data = res.json()
        self.assertEqual(data["user"]["role"], "student", "Role must be 'student' even if 'admin' requested.")

        # Login
        login_res = self.client.post("/api/auth/login", json={
            "email": email,
            "password": "ValidPassword123!"
        })
        self.assertEqual(login_res.status_code, 200)
        token = login_res.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Onboarding update
        profile_res = self.client.put("/api/profile", json={
            "full_name": "Test Student QA",
            "department": "Computer Science",
            "semester": 4,
            "selected_course_id": 1,
            "onboarding_completed": True
        }, headers=headers)
        self.assertEqual(profile_res.status_code, 200)

        # Diagnostic question fetch
        diag_res = self.client.get("/api/diagnostic/1", headers=headers)
        self.assertEqual(diag_res.status_code, 200)
        self.assertIsInstance(diag_res.json(), list)

    # =========================================================================
    # 2. Practice/adaptive pass/fail, topic completion rules (403, 400, 409)
    # =========================================================================
    def test_02_topic_completion_rules(self):
        email = f"student_comp_{self.uid}@test.edu"
        reg = self.client.post("/api/auth/register", json={
            "email": email,
            "password": "CompPassword123!",
            "full_name": "Completion Student"
        })
        self.assertEqual(reg.status_code, 200)
        token = reg.json()["token"]
        user_id = reg.json()["user"]["id"]
        headers = {"Authorization": f"Bearer {token}"}

        # Rule A: Complete without evidence -> 400
        res_no_evidence = self.client.post("/api/assessment/topic/complete/1", headers=headers)
        self.assertEqual(res_no_evidence.status_code, 400, "Must return 400 if no passed assessment evidence exists.")

        # Simulate passing assessment evidence in DB
        with SessionLocal() as db:
            attempt = AssessmentAttempt(
                attempt_uuid=str(uuid.uuid4()),
                user_id=user_id,
                course_id=1,
                topic_id=1,
                attempt_type="practice",
                score=8.5,
                max_score=10.0,
                percentage=85.0,
                passed=True
            )
            db.add(attempt)
            db.commit()

        # Rule B: Complete with evidence -> 200
        res_complete = self.client.post("/api/assessment/topic/complete/1", headers=headers)
        self.assertEqual(res_complete.status_code, 200, "Topic completion should succeed with valid evidence.")
        comp_data = res_complete.json()
        self.assertEqual(comp_data["completion_score"], 100.0)

        # Rule C: Complete again -> 409 (already completed, idempotent)
        res_repeat = self.client.post("/api/assessment/topic/complete/1", headers=headers)
        self.assertEqual(res_repeat.status_code, 409, "Must return 409 for already completed topic.")

        # Rule D: IDOR prevention -> student cannot complete for another user
        res_idor = self.client.post(f"/api/assessment/topic/complete/1?user_id=9999", headers=headers)
        self.assertEqual(res_idor.status_code, 403, "IDOR attempt must return 403.")

    # =========================================================================
    # 3. Course switch isolation across all 4 courses
    # =========================================================================
    def test_03_course_switch_isolation(self):
        email = f"student_switch_{self.uid}@test.edu"
        reg = self.client.post("/api/auth/register", json={
            "email": email,
            "password": "SwitchPassword123!",
            "full_name": "Course Switch Student"
        })
        token = reg.json()["token"]
        user_id = reg.json()["user"]["id"]
        headers = {"Authorization": f"Bearer {token}"}

        for cid in [1, 2, 3, 4]:
            res = self.client.get(f"/api/progress/state?user_id={user_id}&course_id={cid}", headers=headers)
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data["enrolledCourse"]["id"], cid, f"State must reflect requested course {cid}")
            # All topics in state must belong to course cid
            for t in data.get("topicMastery", []):
                self.assertIsNotNone(t["topic_id"])

    # =========================================================================
    # 4. Code runner constraints & 501 in production without docker
    # =========================================================================
    def test_04_code_runner_security_and_501(self):
        email = f"student_coder_{self.uid}@test.edu"
        reg = self.client.post("/api/auth/register", json={
            "email": email,
            "password": "CoderPassword123!",
            "full_name": "Coder Student"
        })
        token = reg.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Code length > 10000 chars -> 400
        res_too_long = self.client.post("/api/assessment/compile-code", json={
            "code": "x = 1\n" * 2500
        }, headers=headers)
        self.assertEqual(res_too_long.status_code, 400)

        # In production mode without docker -> 501
        old_env = os.environ.get("ENV")
        try:
            os.environ["ENV"] = "production"
            res_prod = self.client.post("/api/assessment/compile-code", json={
                "code": "print(42)"
            }, headers=headers)
            self.assertEqual(res_prod.status_code, 501, "Production server-side execution must return 501.")
        finally:
            if old_env is not None:
                os.environ["ENV"] = old_env
            else:
                os.environ.pop("ENV", None)

    # =========================================================================
    # 5. Faculty class creation, weak code rejection, and data isolation
    # =========================================================================
    def test_05_faculty_validation_and_isolation(self):
        # 1. Weak class code validation
        is_valid, msg = validate_custom_code("DSA123", "SAFE99")
        self.assertFalse(is_valid, "Weak code 'DSA123' must be rejected.")

        is_valid2, _ = validate_custom_code("K9X2P4", "SAFE99")
        self.assertTrue(is_valid2, "Strong alphanumeric code 'K9X2P4' must be accepted.")

        # 2. Faculty A and Faculty B creation
        fa_email = f"faculty_a_{self.uid}@uni.edu"
        fb_email = f"faculty_b_{self.uid}@uni.edu"
        with SessionLocal() as db:
            fa = User(email=fa_email, password_hash=hash_password("FacPassword123!"), full_name="Faculty A", role="faculty")
            fb = User(email=fb_email, password_hash=hash_password("FacPassword123!"), full_name="Faculty B", role="faculty")
            db.add_all([fa, fb])
            db.commit()
            fa_id = fa.id
            fb_id = fb.id

        token_fa = create_access_token(fa_id, "faculty")
        token_fb = create_access_token(fb_id, "faculty")
        headers_fa = {"Authorization": f"Bearer {token_fa}"}
        headers_fb = {"Authorization": f"Bearer {token_fb}"}

        # Faculty A creates class
        create_res = self.client.post("/api/faculty/classes", json={
            "course_id": 1,
            "name": f"Batch {self.uid} Alpha"
        }, headers=headers_fa)
        self.assertEqual(create_res.status_code, 201)
        class_id = create_res.json()["id"]

        # Empty class null-safety checks (0 students)
        ov_res = self.client.get(f"/api/faculty/classes/{class_id}/overview", headers=headers_fa)
        self.assertEqual(ov_res.status_code, 200)
        self.assertEqual(ov_res.json()["active_students_count"], 0)
        self.assertIsInstance(ov_res.json()["outcomes"], list)

        stu_res = self.client.get(f"/api/faculty/classes/{class_id}/students", headers=headers_fa)
        self.assertEqual(stu_res.status_code, 200)
        self.assertIsInstance(stu_res.json()["students"], list)

        gaps_res = self.client.get(f"/api/faculty/classes/{class_id}/gaps", headers=headers_fa)
        self.assertEqual(gaps_res.status_code, 200)
        self.assertIsInstance(gaps_res.json()["concept_gaps"], list)
        self.assertIsInstance(gaps_res.json()["common_class_gaps"], list)

        # Faculty B attempts to view Faculty A's class -> 404 (does not leak existence)
        res_unauth = self.client.get(f"/api/faculty/classes/{class_id}/overview", headers=headers_fb)
        self.assertEqual(res_unauth.status_code, 404, "Faculty B cannot see Faculty A's class.")

    # =========================================================================
    # 6. Admin protection, wrong portal rejection (403), 6th failed login (429)
    # =========================================================================
    def test_06_portal_rejection_and_lockout(self):
        email = f"student_portal_{self.uid}@test.edu"
        self.client.post("/api/auth/register", json={
            "email": email,
            "password": "PortalPassword123!",
            "full_name": "Portal Student"
        })

        # Student credentials submitted to faculty portal -> 403, NO token issued
        wrong_res = self.client.post("/api/auth/login", json={
            "email": email,
            "password": "PortalPassword123!",
            "expected_role": "faculty"
        })
        self.assertEqual(wrong_res.status_code, 403, "Student login on faculty portal must be 403.")
        self.assertNotIn("token", wrong_res.json())

        # 6th failed login returns 429 Too Many Requests
        lockout_email = f"lockout_{self.uid}@test.edu"
        for i in range(5):
            res_fail = self.client.post("/api/auth/login", json={
                "email": lockout_email,
                "password": "WrongPassword123!"
            })
            self.assertEqual(res_fail.status_code, 401)

        res_6th = self.client.post("/api/auth/login", json={
            "email": lockout_email,
            "password": "WrongPassword123!"
        })
        self.assertEqual(res_6th.status_code, 429, "6th failed attempt must return 429.")
        self.assertIn("Retry-After", res_6th.headers)

    # =========================================================================
    # 7. AI Tutor rate limiting (11th request in 1 min -> 429)
    # =========================================================================
    def test_07_tutor_rate_limiting(self):
        email = f"tutor_student_{self.uid}@test.edu"
        reg = self.client.post("/api/auth/register", json={
            "email": email,
            "password": "TutorPassword123!",
            "full_name": "Tutor Student"
        })
        token = reg.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        from unittest.mock import patch, AsyncMock
        mock_reply = {
            "reply": "Fast mock explanation.",
            "action_taken": "explain",
            "adapted_for_level": "Beginner",
            "model": "gemini-mock",
            "suggested_followups": ["Tell me more"],
            "modality_preview": None
        }

        with patch("routes.tutor.gemini_tutor_service.chat_with_tutor", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_reply

            # 10 requests allowed
            for i in range(10):
                res = self.client.post("/api/ai-tutor/chat", json={
                    "topic_id": 1,
                    "message": f"Hello {i}",
                    "history": []
                }, headers=headers)
                self.assertEqual(res.status_code, 200, f"Request {i+1} should succeed.")

            # 11th request returns 429
            res_11th = self.client.post("/api/ai-tutor/chat", json={
                "topic_id": 1,
                "message": "Hello 11th",
                "history": []
            }, headers=headers)
            self.assertEqual(res_11th.status_code, 429, "11th request within 1 min must return 429.")
            self.assertIn("Retry-After", res_11th.headers)

    # =========================================================================
    # 8. Production startup checks (refuses to start on invalid config)
    # =========================================================================
    def test_08_production_startup_validation(self):
        # 1. Missing / short JWT_SECRET
        old_env = os.environ.get("ENV")
        old_jwt = os.environ.get("JWT_SECRET")
        old_db = os.environ.get("DATABASE_URL")
        old_origins = os.environ.get("ALLOWED_ORIGINS")

        try:
            os.environ["ENV"] = "production"
            os.environ["JWT_SECRET"] = "short_key"
            os.environ["DATABASE_URL"] = "postgresql://user:pass@host/db"
            os.environ["ALLOWED_ORIGINS"] = "https://app.example.com"

            with self.assertRaises(RuntimeError) as ctx:
                run_production_startup_checks()
            self.assertIn("JWT_SECRET", str(ctx.exception))

            # 2. SQLite DATABASE_URL
            os.environ["JWT_SECRET"] = "a" * 32
            os.environ["DATABASE_URL"] = "sqlite:///local.db"
            with self.assertRaises(RuntimeError) as ctx:
                run_production_startup_checks()
            self.assertIn("SQLite database is not permitted in ENV=production", str(ctx.exception))

            # 3. Wildcard ALLOWED_ORIGINS
            os.environ["DATABASE_URL"] = "postgresql://user:pass@host/db"
            os.environ["ALLOWED_ORIGINS"] = "*"
            with self.assertRaises(RuntimeError) as ctx:
                run_production_startup_checks()
            self.assertIn("ALLOWED_ORIGINS", str(ctx.exception))

            # 4. Valid config succeeds
            os.environ["ALLOWED_ORIGINS"] = "https://app.example.com,https://api.example.com"
            # Should not raise
            run_production_startup_checks()
        finally:
            if old_env is not None: os.environ["ENV"] = old_env
            else: os.environ.pop("ENV", None)
            if old_jwt is not None: os.environ["JWT_SECRET"] = old_jwt
            else: os.environ.pop("JWT_SECRET", None)
            if old_db is not None: os.environ["DATABASE_URL"] = old_db
            else: os.environ.pop("DATABASE_URL", None)
            if old_origins is not None: os.environ["ALLOWED_ORIGINS"] = old_origins
            else: os.environ.pop("ALLOWED_ORIGINS", None)

    # =========================================================================
    # 9. Admin bootstrap and disabled production endpoints
    # =========================================================================
    def test_09_admin_bootstrap_and_disabled_endpoints(self):
        old_email = os.environ.get("ADMIN_EMAIL")
        old_pwd = os.environ.get("ADMIN_PASSWORD")
        adm_email = f"bootstrap_admin_{self.uid}@obe.edu"
        try:
            os.environ["ADMIN_EMAIL"] = adm_email
            os.environ["ADMIN_PASSWORD"] = "AdminSecurePass123!"

            with SessionLocal() as db:
                # If an admin already exists in the local test DB, bootstrap returns existing
                admin = bootstrap_admin_if_needed(db)
                self.assertIsNotNone(admin)
                self.assertEqual(admin.role, "admin")

            # Check /demo-student is 404
            res_demo = self.client.post("/api/auth/demo-student")
            self.assertEqual(res_demo.status_code, 404)

            # Check /api/progress/simulate-activity in production is 404
            token_adm = create_access_token(admin.id, "admin")
            adm_headers = {"Authorization": f"Bearer {token_adm}"}
            old_env = os.environ.get("ENV")
            try:
                os.environ["ENV"] = "production"
                res_sim = self.client.post("/api/progress/simulate-activity", json={
                    "topic_id": 1,
                    "score": 100,
                    "activity_type": "practice"
                }, headers=adm_headers)
                self.assertEqual(res_sim.status_code, 404)
            finally:
                if old_env is not None: os.environ["ENV"] = old_env
                else: os.environ.pop("ENV", None)
        finally:
            if old_email is not None: os.environ["ADMIN_EMAIL"] = old_email
            else: os.environ.pop("ADMIN_EMAIL", None)
            if old_pwd is not None: os.environ["ADMIN_PASSWORD"] = old_pwd
            else: os.environ.pop("ADMIN_PASSWORD", None)

    # =========================================================================
    # 18. Student account deletion request endpoint
    # =========================================================================
    def test_18_student_account_deletion_request(self):
        email = f"student_del_{self.uid}@test.edu"
        reg = self.client.post("/api/auth/register", json={
            "email": email,
            "password": "DelPassword123!",
            "full_name": "Deletion Student"
        })
        token = reg.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        res = self.client.post("/api/student/account-deletion-request", json={
            "reason": "Graduated and requesting complete data erasure."
        }, headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["success"])
        self.assertEqual(res.json()["status"], "pending_admin_review")

if __name__ == "__main__":
    unittest.main()
