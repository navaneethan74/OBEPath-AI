"""
test_phase1_auth_remediation.py
Automated test suite specifically verifying all 10 security requirements of Phase 1: Authentication Only.

Requirements tested:
1. Forged token ("token-3-admin") returns 401
2. Token signed with a wrong secret returns 401
3. Expired token returns 401
4. Student calling /api/admin/* returns 403
5. /api/admin/metrics?user_id=3 without a token returns 401
6. /api/auth/google with {"email":"admin@obe.edu"} and no valid credential returns 401 or 422
7. Register with {"role":"admin"} in the body creates a student
8. Weak password is rejected on register
9. Old sha256 user can still log in and the hash is upgraded to bcrypt
10. Student A cannot read or modify Student B's data by changing user_id (IDOR protection)
"""

import sys
import os
import unittest
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
import jwt

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
from models import User, StudentProfile
from core.security import get_jwt_secret, create_access_token, hash_password

client = TestClient(app)

class TestPhase1AuthRemediation(unittest.TestCase):

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_01_forged_legacy_token_returns_401(self):
        """1. Forged token ('token-3-admin') returns 401 Unauthorized"""
        forged_headers = {"Authorization": "Bearer token-3-admin"}
        
        # Test on admin endpoint
        r_admin = client.get("/api/admin/metrics", headers=forged_headers)
        self.assertEqual(r_admin.status_code, 401, f"Expected 401 for forged token, got {r_admin.status_code}")
        
        # Test on /me endpoint
        r_me = client.get("/api/auth/me", headers=forged_headers)
        self.assertEqual(r_me.status_code, 401)
        print("  [PASS 1/10] Forged token ('token-3-admin') rejected with 401")

    def test_02_token_signed_with_wrong_secret_returns_401(self):
        """2. Token signed with a wrong secret returns 401 Unauthorized"""
        wrong_secret = "completely_wrong_secret_key_that_is_at_least_32_characters_long"
        payload = {
            "sub": "1",
            "role": "admin",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=60),
            "iat": datetime.now(timezone.utc)
        }
        tampered_jwt = jwt.encode(payload, wrong_secret, algorithm="HS256")
        headers = {"Authorization": f"Bearer {tampered_jwt}"}

        r = client.get("/api/admin/metrics", headers=headers)
        self.assertEqual(r.status_code, 401, f"Expected 401 for bad signature, got {r.status_code}")
        print("  [PASS 2/10] Token signed with wrong secret rejected with 401")

    def test_03_expired_token_returns_401(self):
        """3. Expired token returns 401 Unauthorized"""
        real_secret = get_jwt_secret()
        expired_payload = {
            "sub": "1",
            "role": "student",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=10),
            "iat": datetime.now(timezone.utc) - timedelta(minutes=70)
        }
        expired_jwt = jwt.encode(expired_payload, real_secret, algorithm="HS256")
        headers = {"Authorization": f"Bearer {expired_jwt}"}

        r = client.get("/api/auth/me", headers=headers)
        self.assertEqual(r.status_code, 401, f"Expected 401 for expired token, got {r.status_code}")
        self.assertIn("expired", r.json().get("detail", "").lower())
        print("  [PASS 3/10] Expired token rejected with 401 (Token has expired)")

    def test_04_student_calling_admin_endpoints_returns_403(self):
        """4. Student calling /api/admin/* returns 403 Forbidden"""
        import uuid
        p1_uuid = uuid.uuid4().hex[:8]
        s_email = f"student_p1_{p1_uuid}@obe.edu"
        s_pwd = "StudentSecurePass123!"
        r_reg = client.post("/api/auth/register", json={
            "email": s_email,
            "password": s_pwd,
            "full_name": "P1 Student",
            "role": "student"
        })
        self.assertEqual(r_reg.status_code, 200)
        student_token = r_reg.json()["token"]
        headers = {"Authorization": f"Bearer {student_token}"}

        r_metrics = client.get("/api/admin/metrics", headers=headers)
        self.assertEqual(r_metrics.status_code, 403, f"Expected 403 for student calling admin metrics, got {r_metrics.status_code}")

        r_logs = client.get("/api/admin/logs", headers=headers)
        self.assertEqual(r_logs.status_code, 403, f"Expected 403 for student calling admin logs, got {r_logs.status_code}")
        print("  [PASS 4/10] Authenticated student calling /api/admin/* rejected with 403 Forbidden")

    def test_05_admin_metrics_with_user_id_param_without_token_returns_401(self):
        """5. /api/admin/metrics?user_id=3 without a token returns 401 (fallback removed)"""
        r = client.get("/api/admin/metrics?user_id=3")
        self.assertEqual(r.status_code, 401, f"Expected 401, got {r.status_code}")
        print("  [PASS 5/10] /api/admin/metrics?user_id=3 without token returns 401 (user_id fallback eliminated)")

    def test_06_google_auth_without_valid_credential_returns_401_or_422(self):
        """6. /api/auth/google with {'email':'admin@obe.edu'} and no valid credential returns 401 or 422"""
        # Case A: Missing credential field entirely
        r_missing = client.post("/api/auth/google", json={"email": "admin@obe.edu"})
        self.assertIn(r_missing.status_code, [400, 422], f"Expected 400 or 422 for missing credential, got {r_missing.status_code}")

        # Case B: Invalid/garbage credential with GOOGLE_CLIENT_ID set
        with patch.dict(os.environ, {"GOOGLE_CLIENT_ID": "mock-google-client-id"}):
            r_invalid = client.post("/api/auth/google", json={"credential": "invalid_forged_google_credential_xyz"})
            self.assertEqual(r_invalid.status_code, 401, f"Expected 401 for invalid Google token, got {r_invalid.status_code}")

        # Case C: Unconfigured GOOGLE_CLIENT_ID returns 503
        with patch.dict(os.environ, {"GOOGLE_CLIENT_ID": ""}):
            r_unconfigured = client.post("/api/auth/google", json={"credential": "any-token"})
            self.assertEqual(r_unconfigured.status_code, 503, f"Expected 503 when Google client id unset, got {r_unconfigured.status_code}")
        print("  [PASS 6/10] Google auth rejects uncredentialed email injection (422) and invalid Google token (401)")

    def test_07_register_with_role_admin_creates_student(self):
        """7. Register with {'role':'admin'} in the body always creates role='student'"""
        uid = uuid.uuid4().hex[:8]
        admin_exploit_email = f"attacker.{uid}@exploit.com"
        r = client.post("/api/auth/register", json={
            "email": admin_exploit_email,
            "password": "Password123",
            "full_name": "Privilege Escalation Attempt",
            "role": "admin",
            "is_admin": True
        })
        self.assertEqual(r.status_code, 200)
        res_data = r.json()
        self.assertEqual(res_data["user"]["role"], "student", "API response must reflect student role")

        # Verify DB user record directly
        db_user = self.db.query(User).filter(User.email == admin_exploit_email).first()
        self.assertIsNotNone(db_user)
        self.assertEqual(db_user.role, "student", "DB user record must be strictly role='student'")
        print("  [PASS 7/10] Privilege escalation prevented: Registration with role='admin' forces role='student' in DB")

    def test_08_weak_password_rejected_on_register(self):
        """8. Weak passwords are rejected on register (<8 chars, no letters, or no numbers)"""
        uid = uuid.uuid4().hex[:8]

        # Too short (< 8 chars)
        r1 = client.post("/api/auth/register", json={
            "email": f"short.{uid}@obe.edu",
            "password": "Pass1",
            "full_name": "Short Pass",
            "role": "student"
        })
        self.assertEqual(r1.status_code, 400)
        self.assertIn("at least 8 characters", r1.json()["detail"])

        # No digits
        r2 = client.post("/api/auth/register", json={
            "email": f"nodigits.{uid}@obe.edu",
            "password": "OnlyLettersLongPassword",
            "full_name": "No Digits",
            "role": "student"
        })
        self.assertEqual(r2.status_code, 400)
        self.assertIn("at least one number", r2.json()["detail"])

        # No letters
        r3 = client.post("/api/auth/register", json={
            "email": f"noletters.{uid}@obe.edu",
            "password": "1234567890",
            "full_name": "No Letters",
            "role": "student"
        })
        self.assertEqual(r3.status_code, 400)
        self.assertIn("at least one letter", r3.json()["detail"])
        print("  [PASS 8/10] Password validation enforced: Short, letter-only, and digit-only passwords rejected with 400")

    def test_09_old_sha256_user_login_upgrades_to_bcrypt(self):
        """9. An old sha256 user can still log in and the stored hash is upgraded to bcrypt"""
        uid = uuid.uuid4().hex[:8]
        legacy_email = f"legacy.student.{uid}@obe.edu"
        raw_password = "LegacyPassword123"
        legacy_sha256 = hashlib.sha256(raw_password.encode()).hexdigest()

        # Seed legacy user with raw SHA-256 hex string
        legacy_user = User(
            email=legacy_email,
            full_name=f"Legacy Learner {uid}",
            role="student",
            password_hash=legacy_sha256
        )
        self.db.add(legacy_user)
        self.db.commit()
        self.db.refresh(legacy_user)

        # Confirm initial hash is 64-char hex SHA-256
        self.assertEqual(len(legacy_user.password_hash), 64)
        self.assertEqual(legacy_user.password_hash, legacy_sha256)

        # Login with legacy password
        r = client.post("/api/auth/login", json={
            "email": legacy_email,
            "password": raw_password
        })
        self.assertEqual(r.status_code, 200, f"Legacy login failed: {r.text}")
        token = r.json()["token"]
        self.assertTrue(token.startswith("ey"))

        # Re-query DB to verify automatic upgrade to bcrypt ($2b$ or $2a$)
        self.db.expire_all()
        upgraded_user = self.db.query(User).filter(User.id == legacy_user.id).first()
        self.assertIsNotNone(upgraded_user)
        self.assertTrue(
            upgraded_user.password_hash.startswith("$2b$") or upgraded_user.password_hash.startswith("$2a$"),
            f"Expected bcrypt hash starting with $2b$ or $2a$, got {upgraded_user.password_hash[:10]}"
        )
        self.assertNotEqual(upgraded_user.password_hash, legacy_sha256)

        # Subsequent login continues to work with upgraded bcrypt hash
        r2 = client.post("/api/auth/login", json={
            "email": legacy_email,
            "password": raw_password
        })
        self.assertEqual(r2.status_code, 200)
        print("  [PASS 9/10] Legacy SHA-256 hash verified and transparently upgraded to bcrypt on login")

    def test_10_student_a_cannot_read_or_modify_student_b_data(self):
        """10. Student A cannot read or modify Student B's data by changing user_id (IDOR protection)"""
        # Create Student A
        uid_a = uuid.uuid4().hex[:8]
        r_a = client.post("/api/auth/register", json={
            "email": f"student.a.{uid_a}@obe.edu",
            "password": "Password123",
            "full_name": "Student A",
            "role": "student"
        })
        self.assertEqual(r_a.status_code, 200)
        user_a_id = r_a.json()["user"]["id"]
        token_a = r_a.json()["token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # Create Student B
        uid_b = uuid.uuid4().hex[:8]
        r_b = client.post("/api/auth/register", json={
            "email": f"student.b.{uid_b}@obe.edu",
            "password": "Password123",
            "full_name": "Student B",
            "role": "student"
        })
        self.assertEqual(r_b.status_code, 200)
        user_b_id = r_b.json()["user"]["id"]

        # Student A attempts to READ Student B's profile
        r_read_prof = client.get(f"/api/profile?user_id={user_b_id}", headers=headers_a)
        self.assertEqual(r_read_prof.status_code, 403, f"Expected 403 on cross-student profile read, got {r_read_prof.status_code}")

        # Student A attempts to MODIFY Student B's profile
        r_mod_prof = client.put(f"/api/profile?user_id={user_b_id}", headers=headers_a, json={
            "full_name": "Hacked Profile",
            "onboarding_completed": True
        })
        self.assertEqual(r_mod_prof.status_code, 403, f"Expected 403 on cross-student profile modify, got {r_mod_prof.status_code}")

        # Student A attempts to READ Student B's progress state
        r_prog = client.get(f"/api/progress/state?user_id={user_b_id}&course_id=2", headers=headers_a)
        self.assertEqual(r_prog.status_code, 403, f"Expected 403 on cross-student progress read, got {r_prog.status_code}")

        # Student A attempts to SUBMIT an assessment on behalf of Student B
        r_sub = client.post(f"/api/progress/submit-assessment?user_id={user_b_id}", headers=headers_a, json={
            "course_id": 2,
            "attempt_type": "assessment",
            "answers": {}
        })
        self.assertEqual(r_sub.status_code, 403, f"Expected 403 on cross-student assessment submit, got {r_sub.status_code}")

        # Student A attempts to COMPLETE a topic on behalf of Student B
        r_comp = client.post(f"/api/assessment/topic/complete/1?user_id={user_b_id}", headers=headers_a)
        self.assertEqual(r_comp.status_code, 403, f"Expected 403 on cross-student topic complete, got {r_comp.status_code}")

        # Verify Admin CAN access Student B's profile (admin override)
        admin_u = User(
            email=f"admin_p1_{uuid.uuid4().hex[:8]}@obe.edu",
            password_hash=hash_password("AdminSecurePass123!"),
            full_name="P1 Admin",
            role="admin"
        )
        self.db.add(admin_u)
        self.db.commit()
        admin_headers = {"Authorization": f"Bearer {create_access_token(admin_u.id, 'admin')}"}
        r_admin_access = client.get(f"/api/profile?user_id={user_b_id}", headers=admin_headers)
        self.assertEqual(r_admin_access.status_code, 200, "Admin must be able to view student profile")

        print("  [PASS 10/10] IDOR Protection verified: Student A receives 403 Forbidden attempting to read/modify Student B's data")

if __name__ == "__main__":
    unittest.main()
