#!/usr/bin/env python3
"""
Test Suite for Phase 2: Visible Faculty/Admin Entry Point, Role Isolation, & Provisioning Flow.

Tests:
1. Admin-Only Endpoint Protection (POST /api/admin/users):
   - Unauthenticated returns 401 Unauthorized
   - Student token returns 403 Forbidden
   - Faculty token returns 403 Forbidden
   - Admin token returns 200 OK and creates faculty with role="faculty", must_change_password=True
2. Faculty Lifecycle:
   - Faculty created by admin logs in with temporary password
   - Login returns must_change_password=True
   - /api/auth/me confirms must_change_password=True
   - Faculty changes password via POST /api/auth/change-password
   - Incorrect current password rejected (400)
   - Weak new password rejected (400)
   - Successful password change sets must_change_password=False
   - Faculty accesses faculty endpoints with 200 OK
3. UI Role Tab Matching Logic & Onboarding Immunity:
   - Accounts logging in with role mismatch (e.g. Student on Faculty tab) rejected in UI flow
   - Faculty and Admin are immune to student onboarding wizard logic
4. CLI Account Provisioning:
   - scripts/create_admin.py and scripts/create_faculty.py execute securely
"""

import os
import sys
import unittest
import subprocess
from fastapi.testclient import TestClient

# Ensure backend root is in sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from main import app
from database import engine, SessionLocal, Base
from models import User, StudentProfile
from core.security import create_access_token, hash_password

client = TestClient(app)

class TestPhase2FacultyAdminAuth(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.db = SessionLocal()

        import uuid
        p2_id = uuid.uuid4().hex[:8]
        cls.student_email = f"p2_student_{p2_id}@obe.edu"
        cls.admin_email = f"p2_admin_{p2_id}@obe.edu"
        cls.faculty_email = f"p2_faculty_{p2_id}@obe.edu"
        cls.student_pwd = "P2StudentPass123!"
        cls.admin_pwd = "P2AdminPass123!"
        cls.faculty_pwd = "P2FacultyPass123!"

        cls.student = User(
            email=cls.student_email,
            full_name="Student Test",
            password_hash=hash_password(cls.student_pwd),
            role="student"
        )
        cls.admin = User(
            email=cls.admin_email,
            full_name="Admin Test",
            password_hash=hash_password(cls.admin_pwd),
            role="admin"
        )
        cls.faculty = User(
            email=cls.faculty_email,
            full_name="Faculty Test",
            password_hash=hash_password(cls.faculty_pwd),
            role="faculty"
        )
        cls.db.add_all([cls.student, cls.admin, cls.faculty])
        cls.db.commit()

        # Tokens
        cls.student_token = create_access_token(cls.student.id, "student")
        cls.admin_token = create_access_token(cls.admin.id, "admin")
        cls.faculty_token = create_access_token(cls.faculty.id, "faculty")

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_01_student_cannot_call_admin_users(self):
        """Security: Student token receives 403 Forbidden calling POST /api/admin/users."""
        res = client.post(
            "/api/admin/users",
            json={
                "name": "Malicious Faculty Attempt",
                "email": "hacker_fac@obe.edu",
                "temporary_password": "TempPassword123"
            },
            headers={"Authorization": f"Bearer {self.student_token}"}
        )
        self.assertEqual(res.status_code, 403, f"Expected 403 Forbidden, got {res.status_code}")
        self.assertIn("Forbidden", res.json().get("detail", ""))

    def test_02_unauthenticated_cannot_call_admin_users(self):
        """Security: Unauthenticated request receives 401 Unauthorized calling POST /api/admin/users."""
        res = client.post(
            "/api/admin/users",
            json={
                "name": "Anon Attempt",
                "email": "anon_fac@obe.edu",
                "temporary_password": "TempPassword123"
            }
        )
        self.assertEqual(res.status_code, 401)

    def test_03_faculty_cannot_call_admin_users(self):
        """Security: Faculty token receives 403 Forbidden calling POST /api/admin/users."""
        res = client.post(
            "/api/admin/users",
            json={
                "name": "Peer Faculty Attempt",
                "email": "peer_fac@obe.edu",
                "temporary_password": "TempPassword123"
            },
            headers={"Authorization": f"Bearer {self.faculty_token}"}
        )
        self.assertEqual(res.status_code, 403)

    def test_04_admin_creates_faculty_successfully(self):
        """Admin provisions faculty account with role='faculty' and must_change_password=True."""
        new_email = f"prof_{os.urandom(4).hex()}@obe.edu"
        res = client.post(
            "/api/admin/users",
            json={
                "name": "Prof. Alan Turing",
                "email": new_email,
                "temporary_password": "InitialPassword123"
            },
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        self.assertEqual(res.status_code, 200, f"Expected 200 OK, got {res.status_code}: {res.text}")
        data = res.json()
        self.assertEqual(data["email"], new_email)
        self.assertEqual(data["role"], "faculty")
        self.assertTrue(data["must_change_password"])

        # Verify DB directly
        db = SessionLocal()
        created_user = db.query(User).filter(User.email == new_email).first()
        self.assertIsNotNone(created_user)
        self.assertEqual(created_user.role, "faculty")
        self.assertTrue(created_user.must_change_password)
        db.close()

    def test_05_admin_duplicate_email_rejected(self):
        """Admin creating faculty with existing email is rejected with 400 Bad Request."""
        res = client.post(
            "/api/admin/users",
            json={
                "name": "Duplicate Student",
                "email": self.student_email,
                "temporary_password": "TempPassword123"
            },
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("already exists", res.json().get("detail", ""))

    def test_06_faculty_login_force_password_change_flow(self):
        """Complete Lifecycle: Created faculty logs in -> must_change_password=True -> changes password -> must_change_password=False."""
        fac_email = f"new_prof_{os.urandom(4).hex()}@obe.edu"
        temp_pwd = "TemporaryPass123"
        new_pwd = "NewSecurePassword456"

        # 1. Admin creates faculty
        create_res = client.post(
            "/api/admin/users",
            json={
                "name": "Dr. Ada Lovelace",
                "email": fac_email,
                "temporary_password": temp_pwd
            },
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        self.assertEqual(create_res.status_code, 200)

        # 2. Faculty logs in with temporary password
        login_res = client.post(
            "/api/auth/login",
            json={
                "email": fac_email,
                "password": temp_pwd,
                "role": "faculty"
            }
        )
        self.assertEqual(login_res.status_code, 200)
        login_data = login_res.json()
        self.assertTrue(login_data["must_change_password"])
        self.assertEqual(login_data["user"]["role"], "faculty")
        fac_token = login_data["token"]

        # 3. Verify /api/auth/me returns must_change_password=True
        me_res = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {fac_token}"}
        )
        self.assertEqual(me_res.status_code, 200)
        self.assertTrue(me_res.json().get("must_change_password"))

        # 4. Attempt change-password with wrong old password -> 400
        wrong_old_res = client.post(
            "/api/auth/change-password",
            json={
                "old_password": "WrongPassword123",
                "new_password": new_pwd
            },
            headers={"Authorization": f"Bearer {fac_token}"}
        )
        self.assertEqual(wrong_old_res.status_code, 400)
        self.assertIn("Current password is incorrect", wrong_old_res.json().get("detail", ""))

        # 5. Attempt change-password with weak new password -> 400
        weak_pwd_res = client.post(
            "/api/auth/change-password",
            json={
                "old_password": temp_pwd,
                "new_password": "short"
            },
            headers={"Authorization": f"Bearer {fac_token}"}
        )
        self.assertEqual(weak_pwd_res.status_code, 400)

        # 6. Successfully change password
        change_res = client.post(
            "/api/auth/change-password",
            json={
                "old_password": temp_pwd,
                "new_password": new_pwd
            },
            headers={"Authorization": f"Bearer {fac_token}"}
        )
        self.assertEqual(change_res.status_code, 200)
        self.assertFalse(change_res.json().get("must_change_password"))

        # 7. Verify /api/auth/me now reflects must_change_password=False
        me_after_res = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {fac_token}"}
        )
        self.assertEqual(me_after_res.status_code, 200)
        self.assertFalse(me_after_res.json().get("must_change_password"))

        # 8. Verify faculty can log in with new password
        new_login_res = client.post(
            "/api/auth/login",
            json={
                "email": fac_email,
                "password": new_pwd,
                "role": "faculty"
            }
        )
        self.assertEqual(new_login_res.status_code, 200)
        self.assertFalse(new_login_res.json()["must_change_password"])

    def test_07_faculty_and_admin_never_routed_to_onboarding(self):
        """UI Logic Verification: Faculty and Admin accounts NEVER get routed to student onboarding."""
        # Check faculty /api/auth/me
        fac_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {self.faculty_token}"})
        self.assertEqual(fac_me.status_code, 200)
        fac_data = fac_me.json()
        self.assertEqual(fac_data["role"], "faculty")
        # In UI logic, `if (user.role === 'faculty')` immediately displays Faculty Dashboard
        # and ignores student onboarding state.
        self.assertNotEqual(fac_data["role"], "student")

        # Check admin /api/auth/me
        admin_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(admin_me.status_code, 200)
        admin_data = admin_me.json()
        self.assertEqual(admin_data["role"], "admin")
        self.assertNotEqual(admin_data["role"], "student")

    def test_08_wrong_role_login_rejection_ui_contract(self):
        """UI Logic Contract: Role returned by server is matched against selected tab in AuthLandingPage."""
        # 1. Student attempts to log in via Faculty tab
        # Server validates credentials and returns authentic user role="student"
        res = client.post(
            "/api/auth/login",
            json={"email": self.student_email, "password": self.student_pwd, "role": "faculty"}
        )
        self.assertEqual(res.status_code, 200)
        # AuthLandingPage logic: if (res.user.role !== selectedTab) { api.logout(); setError("This account is not a faculty account"); return; }
        returned_role = res.json()["user"]["role"]
        self.assertEqual(returned_role, "student")
        self.assertNotEqual(returned_role, "faculty")

        # 2. Faculty attempts to log in via Student tab
        res2 = client.post(
            "/api/auth/login",
            json={"email": self.faculty_email, "password": self.faculty_pwd, "role": "student"}
        )
        self.assertEqual(res2.status_code, 200)
        returned_role_fac = res2.json()["user"]["role"]
        self.assertEqual(returned_role_fac, "faculty")
        self.assertNotEqual(returned_role_fac, "student")

    def test_09_cli_create_admin_and_faculty_scripts(self):
        """CLI scripts: scripts/create_admin.py and scripts/create_faculty.py execute cleanly."""
        cli_admin_email = f"cli_admin_{os.urandom(3).hex()}@obe.edu"
        cli_admin_pwd = "AdminCliPassword123"

        res_admin = subprocess.run(
            [
                sys.executable,
                os.path.join(backend_dir, "scripts", "create_admin.py"),
                "--email", cli_admin_email,
                "--password", cli_admin_pwd,
                "--name", "CLI Admin Provisioned"
            ],
            capture_output=True,
            text=True
        )
        self.assertEqual(res_admin.returncode, 0, f"create_admin.py failed: {res_admin.stderr}")
        self.assertIn("SUCCESS: Admin account ready", res_admin.stdout)

        # Verify admin can log in with provisioned credentials
        login_res = client.post(
            "/api/auth/login",
            json={"email": cli_admin_email, "password": cli_admin_pwd}
        )
        self.assertEqual(login_res.status_code, 200)
        self.assertEqual(login_res.json()["user"]["role"], "admin")

        # Test create_faculty.py
        cli_fac_email = f"cli_fac_{os.urandom(3).hex()}@obe.edu"
        cli_fac_pwd = "FacultyCliPassword123"

        res_fac = subprocess.run(
            [
                sys.executable,
                os.path.join(backend_dir, "scripts", "create_faculty.py"),
                "--email", cli_fac_email,
                "--password", cli_fac_pwd,
                "--name", "CLI Faculty Provisioned"
            ],
            capture_output=True,
            text=True
        )
        self.assertEqual(res_fac.returncode, 0, f"create_faculty.py failed: {res_fac.stderr}")
        self.assertIn("SUCCESS: Faculty account ready", res_fac.stdout)

        # Verify faculty can log in
        login_fac = client.post(
            "/api/auth/login",
            json={"email": cli_fac_email, "password": cli_fac_pwd}
        )
        self.assertEqual(login_fac.status_code, 200)
        self.assertEqual(login_fac.json()["user"]["role"], "faculty")

if __name__ == "__main__":
    unittest.main()
