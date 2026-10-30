import sys
import os
import unittest
import json

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def make_request(path, method="GET", payload=None, headers=None):
    if method == "POST":
        resp = client.post(path, json=payload, headers=headers)
    elif method == "PUT":
        resp = client.put(path, json=payload, headers=headers)
    else:
        resp = client.get(path, headers=headers)
    try:
        data = resp.json()
    except Exception:
        data = {"raw": resp.text}
    return resp.status_code, data

class TestRoleRoutingAndProtection(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import uuid
        from database import SessionLocal
        from models import User, StudentProfile
        from core.security import hash_password

        cls.uid = uuid.uuid4().hex[:8]
        cls.s_email = f"rr_student_{cls.uid}@obe.edu"
        cls.s_pwd = "StudentSecure123!"
        cls.f_email = f"rr_faculty_{cls.uid}@obe.edu"
        cls.f_pwd = "FacultySecure123!"
        cls.a_email = f"rr_admin_{cls.uid}@obe.edu"
        cls.a_pwd = "AdminSecure123!"

        with SessionLocal() as db:
            s = User(
                email=cls.s_email,
                password_hash=hash_password(cls.s_pwd),
                full_name="RR Student",
                role="student"
            )
            db.add(s)
            db.flush()
            db.add(StudentProfile(
                user_id=s.id,
                selected_course_id=2,
                onboarding_completed=True
            ))
            db.add(User(
                email=cls.f_email,
                password_hash=hash_password(cls.f_pwd),
                full_name="RR Faculty",
                role="faculty"
            ))
            db.add(User(
                email=cls.a_email,
                password_hash=hash_password(cls.a_pwd),
                full_name="RR Admin",
                role="admin"
            ))
            db.commit()

    def test_01_unauthenticated_admin_api_blocked(self):
        """Unauthenticated requests to admin endpoints must return 401"""
        status1, body1 = make_request("/api/admin/metrics")
        self.assertEqual(status1, 401, f"Expected 401, got {status1}")
        
        status2, body2 = make_request("/api/admin/logs")
        self.assertEqual(status2, 401, f"Expected 401, got {status2}")
        print("  [PASS] Unauthenticated calls to /api/admin/* return 401 Unauthorized")

    def test_02_invalid_or_tampered_token_blocked(self):
        """Invalid bearer tokens to admin endpoints must return 401"""
        headers = {"Authorization": "Bearer fake-token-random"}
        status, body = make_request("/api/admin/metrics", headers=headers)
        self.assertEqual(status, 401, f"Expected 401, got {status}")
        print("  [PASS] Invalid token to /api/admin/* returns 401 Unauthorized")

    def test_03_student_role_access_and_admin_isolation(self):
        """Student logs in, accesses student learning API, but is blocked from admin API (403)"""
        # Login
        status_login, data = make_request("/api/auth/login", method="POST", payload={
            "email": self.s_email,
            "password": self.s_pwd
        })
        self.assertEqual(status_login, 200)
        student_user = data["user"]
        self.assertEqual(student_user["role"], "student")
        token = data["token"]

        # Student accesses learning endpoints
        headers = {"Authorization": f"Bearer {token}"}
        status_prog, prog_data = make_request(f"/api/progress/state?user_id={student_user['id']}&course_id=2", headers=headers)
        self.assertEqual(status_prog, 200)
        self.assertIn("enrolledCourse", prog_data)

        # Student attempts admin API access
        headers = {"Authorization": f"Bearer {token}"}
        status_admin, admin_data = make_request("/api/admin/metrics", headers=headers)
        self.assertEqual(status_admin, 403, f"Expected 403 Forbidden for student, got {status_admin}")
        self.assertIn("Forbidden", admin_data.get("detail", ""))

        status_logs, logs_data = make_request("/api/admin/logs", headers=headers)
        self.assertEqual(status_logs, 403)
        print("  [PASS] Student authenticated, accesses learning interface, blocked from admin API with 403 Forbidden")

    def test_04_faculty_role_access_and_admin_isolation(self):
        """Faculty logs in, accesses faculty dashboard & analytics, but is blocked from admin API (403)"""
        # Login
        status_login, data = make_request("/api/auth/login", method="POST", payload={
            "email": self.f_email,
            "password": self.f_pwd
        })
        self.assertEqual(status_login, 200)
        faculty_user = data["user"]
        self.assertEqual(faculty_user["role"], "faculty")
        token = data["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Faculty accesses faculty analytics
        status_dash, dash_data = make_request("/api/faculty/dashboard?course_id=1", headers=headers)
        self.assertEqual(status_dash, 200)
        self.assertIn("metrics", dash_data)
        self.assertIn("intervention_list", dash_data)

        status_ana, ana_data = make_request("/api/faculty/topic-analytics?course_id=1", headers=headers)
        self.assertEqual(status_ana, 200)

        # Faculty attempts admin API access
        headers = {"Authorization": f"Bearer {token}"}
        status_admin, admin_data = make_request("/api/admin/metrics", headers=headers)
        self.assertEqual(status_admin, 403, f"Expected 403 Forbidden for faculty, got {status_admin}")
        self.assertIn("Forbidden", admin_data.get("detail", ""))

        status_logs, logs_data = make_request("/api/admin/logs", headers=headers)
        self.assertEqual(status_logs, 403)
        print("  [PASS] Faculty authenticated, accesses faculty dashboard & cohort analytics, blocked from admin API with 403 Forbidden")

    def test_05_admin_role_access_authorized(self):
        """Admin logs in and successfully accesses admin telemetry and audit logs with 200"""
        # Login
        status_login, data = make_request("/api/auth/login", method="POST", payload={
            "email": self.a_email,
            "password": self.a_pwd
        })
        self.assertEqual(status_login, 200)
        admin_user = data["user"]
        self.assertEqual(admin_user["role"], "admin")
        token = data["token"]

        # Admin accesses admin telemetry
        headers = {"Authorization": f"Bearer {token}"}
        status_metrics, metrics = make_request("/api/admin/metrics", headers=headers)
        self.assertEqual(status_metrics, 200)
        self.assertIn("total_users", metrics)
        self.assertIn("system_status", metrics)

        status_logs, logs = make_request("/api/admin/logs?limit=10", headers=headers)
        self.assertEqual(status_logs, 200)
        self.assertIsInstance(logs, list)
        print("  [PASS] Admin authenticated, accesses admin metrics & system telemetry with 200 OK")

    def test_06_student_blocked_from_faculty_api(self):
        """Student token must be strictly forbidden (403) from accessing faculty endpoints"""
        status_login, data = make_request("/api/auth/login", method="POST", payload={
            "email": self.s_email,
            "password": self.s_pwd
        })
        self.assertEqual(status_login, 200)
        token = data["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Student attempts to access faculty dashboard
        status_dash, dash_body = make_request("/api/faculty/dashboard?course_id=1", headers=headers)
        self.assertEqual(status_dash, 403, f"Expected 403 Forbidden, got {status_dash}")

        # Student attempts to access faculty topic analytics
        status_ana, ana_body = make_request("/api/faculty/topic-analytics?course_id=1", headers=headers)
        self.assertEqual(status_ana, 403, f"Expected 403 Forbidden, got {status_ana}")

        # Student attempts to access faculty classes
        status_cls, cls_body = make_request("/api/faculty/classes", headers=headers)
        self.assertEqual(status_cls, 403, f"Expected 403 Forbidden, got {status_cls}")
        print("  [PASS] Student token is rejected with 403 Forbidden on all faculty API endpoints")

    def test_07_faculty_blocked_from_student_only_api(self):
        """Faculty and Admin tokens must be rejected (403) from student-only API endpoints"""
        status_login, data = make_request("/api/auth/login", method="POST", payload={
            "email": self.f_email,
            "password": self.f_pwd
        })
        self.assertEqual(status_login, 200)
        token = data["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Faculty attempts to access student class join preview
        status_prev, prev_body = make_request(
            "/api/student/classes/preview",
            method="POST",
            payload={"class_code": "CS201-TEST"},
            headers=headers
        )
        self.assertEqual(status_prev, 403, f"Expected 403 Forbidden for faculty, got {status_prev}")

        # Faculty attempts to join class as student
        status_join, join_body = make_request(
            "/api/student/classes/join",
            method="POST",
            payload={"class_code": "CS201-TEST", "consent_agreed": True},
            headers=headers
        )
        self.assertEqual(status_join, 403, f"Expected 403 Forbidden for faculty, got {status_join}")

        # Admin also blocked from student join
        status_admin_login, a_data = make_request("/api/auth/login", method="POST", payload={
            "email": self.a_email,
            "password": self.a_pwd
        })
        self.assertEqual(status_admin_login, 200)
        a_headers = {"Authorization": f"Bearer {a_data['token']}"}
        status_a_join, a_join_body = make_request(
            "/api/student/classes/join",
            method="POST",
            payload={"class_code": "CS201-TEST", "consent_agreed": True},
            headers=a_headers
        )
        self.assertEqual(status_a_join, 403, f"Expected 403 Forbidden for admin, got {status_a_join}")
        print("  [PASS] Faculty and Admin tokens are rejected with 403 Forbidden on student-only API endpoints")

    def test_08_frontend_faculty_navigation_and_route_redirect_guarantees(self):
        """Verify frontend navigation definitions: faculty sidebar cleanup and route redirection to Cohort Analytics"""
        sidebar_path = os.path.join(backend_dir, "..", "frontend", "src", "components", "Sidebar.tsx")
        app_path = os.path.join(backend_dir, "..", "frontend", "src", "App.tsx")

        self.assertTrue(os.path.exists(sidebar_path), f"Sidebar.tsx not found at {sidebar_path}")
        self.assertTrue(os.path.exists(app_path), f"App.tsx not found at {app_path}")

        with open(sidebar_path, "r", encoding="utf-8") as f:
            sidebar_content = f.read()

        with open(app_path, "r", encoding="utf-8") as f:
            app_content = f.read()

        # 1. Faculty sidebar verification:
        # Must contain Cohort Analytics
        self.assertIn("Cohort Analytics", sidebar_content, "Sidebar must offer Cohort Analytics for faculty")
        # Must NOT contain Curriculum Oversight or Faculty Resources in facultyNavItems
        faculty_items_block = sidebar_content.split("const facultyNavItems")[1].split("];")[0]
        self.assertNotIn("Curriculum Oversight", faculty_items_block, "Curriculum Oversight must be removed from facultyNavItems")
        self.assertNotIn("'courses'", faculty_items_block, "courses tab must not be in facultyNavItems")
        self.assertNotIn("'resources'", faculty_items_block, "student resources tab must not be in facultyNavItems")

        # 2. Student sidebar verification:
        # Student items (My Course, Learning Path, Topic Map, AI Tutor, Assessments, My Skills) must be preserved
        student_items_block = sidebar_content.split("const studentNavItems")[1].split("];")[0]
        self.assertIn("My Course", student_items_block, "Student must retain My Course")
        self.assertIn("Learning Path", student_items_block, "Student must retain Learning Path")
        self.assertIn("Topic Map", student_items_block, "Student must retain Topic Map")
        self.assertIn("Assessments", student_items_block, "Student must retain Assessments")
        self.assertIn("AI Tutor", student_items_block, "Student must retain AI Tutor")
        self.assertIn("My Skills", student_items_block, "Student must retain My Skills")

        # 3. FacultyAppContent verification in App.tsx:
        # FacultyAppContent must NOT render CourseSelectionPage or ResourcesPage
        faculty_app_block = app_content.split("const FacultyAppContent:")[1].split("const AdminAppContent:")[0]
        self.assertNotIn("<CourseSelectionPage", faculty_app_block, "FacultyAppContent must NOT render CourseSelectionPage")
        self.assertNotIn("<ResourcesPage", faculty_app_block, "FacultyAppContent must NOT render ResourcesPage")
        self.assertIn("<FacultyDashboardPage />", faculty_app_block, "FacultyAppContent must render FacultyDashboardPage")
        self.assertIn("<SettingsPage />", faculty_app_block, "FacultyAppContent must render SettingsPage")

        # 4. Route redirect verification in App.tsx:
        # Must define STUDENT_ONLY_ROUTES with /courses, /learning-path, /knowledge-map, /assessments, etc.
        self.assertIn("STUDENT_ONLY_ROUTES", app_content)
        for route in ["/courses", "/learning-path", "/knowledge-map", "/assessments", "/ai-tutor", "/skills", "/resources"]:
            self.assertIn(route, app_content, f"STUDENT_ONLY_ROUTES must include {route}")

        # Must redirect faculty/admin hitting student routes to /dashboard (Cohort Analytics)
        self.assertIn("replaceState({}, '', '/dashboard')", app_content, "Redirect to /dashboard must use replaceState")
        print("  [PASS] Frontend faculty navigation cleaned up; route redirection and isolation guaranteed")

if __name__ == "__main__":
    unittest.main()
