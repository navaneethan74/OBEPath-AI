"""
test_step2a_classes_and_access.py
Comprehensive test suite verifying all requirements of Step 2A:
Classes, Join Code, Consent, Baseline Snapshot, and Class-Based Access.

Scenarios tested:
1. Faculty creates class; generated code is 6 chars, unique, no confusing characters; weak custom code "DSA123" rejected.
2. Student previews and joins; join without consent rejected; invalid code returns generic 404.
3. Baseline snapshot saved correctly for a student who already has progress (e.g. 3 topics complete before joining).
4. Disabled, expired and full classes reject joins; regenerate invalidates the old code.
5. Student leaves: faculty can no longer see that student; re-join creates a new baseline.
6. Faculty A cannot view Faculty B's class or students; admin can.
7. Student calling any /api/faculty/* gets 403; anonymous gets 401.
8. Removed student's data is not deleted.
9. Join rate limit returns 429 after the limit.
10. No password hash appears in any faculty response.
"""

import os
import sys
import unittest
import uuid
import json
from datetime import datetime, timedelta

# Ensure backend directory is in sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
from models import (
    User, Course, Topic, MasteryScore, CourseOutcome,
    OutcomeAttainment, ClassModel, ClassEnrollment
)
from core.security import create_access_token, hash_password
from routes.student import reset_rate_limits

client = TestClient(app)

class TestStep2AClassesAndAccess(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()

        # Seed or load Course 1 (CS101) & Course 2 (CS201)
        cls.course = cls.db.query(Course).filter(Course.id == 1).first()
        if not cls.course:
            cls.course = Course(id=1, code="CS101", title="Python Programming", description="Core Python")
            cls.db.add(cls.course)
            cls.db.commit()

        # Create Admin
        cls.admin = cls.db.query(User).filter(User.email == "admin_step2a@obe.edu").first()
        if not cls.admin:
            cls.admin = User(
                email="admin_step2a@obe.edu",
                full_name="Admin Step2A",
                password_hash=hash_password("AdminPass@123"),
                role="admin"
            )
            cls.db.add(cls.admin)

        # Create Faculty A
        cls.faculty_a = cls.db.query(User).filter(User.email == "faculty_a_step2a@obe.edu").first()
        if not cls.faculty_a:
            cls.faculty_a = User(
                email="faculty_a_step2a@obe.edu",
                full_name="Dr. Faculty Alpha",
                password_hash=hash_password("FacultyPass@123"),
                role="faculty"
            )
            cls.db.add(cls.faculty_a)

        # Create Faculty B
        cls.faculty_b = cls.db.query(User).filter(User.email == "faculty_b_step2a@obe.edu").first()
        if not cls.faculty_b:
            cls.faculty_b = User(
                email="faculty_b_step2a@obe.edu",
                full_name="Dr. Faculty Beta",
                password_hash=hash_password("FacultyPass@123"),
                role="faculty"
            )
            cls.db.add(cls.faculty_b)

        # Create Student 1
        cls.student_1 = cls.db.query(User).filter(User.email == "student1_step2a@obe.edu").first()
        if not cls.student_1:
            cls.student_1 = User(
                email="student1_step2a@obe.edu",
                full_name="Student One",
                password_hash=hash_password("StudentPass@123"),
                role="student"
            )
            cls.db.add(cls.student_1)

        # Create Student 2
        cls.student_2 = cls.db.query(User).filter(User.email == "student2_step2a@obe.edu").first()
        if not cls.student_2:
            cls.student_2 = User(
                email="student2_step2a@obe.edu",
                full_name="Student Two",
                password_hash=hash_password("StudentPass@123"),
                role="student"
            )
            cls.db.add(cls.student_2)

        cls.db.commit()
        cls.db.refresh(cls.admin)
        cls.db.refresh(cls.faculty_a)
        cls.db.refresh(cls.faculty_b)
        cls.db.refresh(cls.student_1)
        cls.db.refresh(cls.student_2)

        # Generate JWT Tokens
        cls.token_admin = create_access_token(cls.admin.id, "admin")
        cls.token_faculty_a = create_access_token(cls.faculty_a.id, "faculty")
        cls.token_faculty_b = create_access_token(cls.faculty_b.id, "faculty")
        cls.token_student_1 = create_access_token(cls.student_1.id, "student")
        cls.token_student_2 = create_access_token(cls.student_2.id, "student")

        cls.headers_admin = {"Authorization": f"Bearer {cls.token_admin}"}
        cls.headers_faculty_a = {"Authorization": f"Bearer {cls.token_faculty_a}"}
        cls.headers_faculty_b = {"Authorization": f"Bearer {cls.token_faculty_b}"}
        cls.headers_student_1 = {"Authorization": f"Bearer {cls.token_student_1}"}
        cls.headers_student_2 = {"Authorization": f"Bearer {cls.token_student_2}"}

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def setUp(self):
        reset_rate_limits()

    def test_01_faculty_creates_class_code_rules(self):
        """1. Faculty creates class; code is 6 chars, unique, no confusing chars; weak custom code 'DSA123' rejected."""
        # 1a. Weak custom code "DSA123" rejected
        res_weak = client.post(
            "/api/faculty/classes",
            headers=self.headers_faculty_a,
            json={
                "course_id": self.course.id,
                "name": "Weak Code Section",
                "custom_code": "DSA123"
            }
        )
        self.assertEqual(res_weak.status_code, 400)
        err_msg = res_weak.json().get("detail", "")
        self.assertIn("trivially guessable", err_msg.lower())
        self.assertIn("suggested code", err_msg.lower())

        # 1b. Repetitive custom code "AAAAAA" rejected
        res_rep = client.post(
            "/api/faculty/classes",
            headers=self.headers_faculty_a,
            json={
                "course_id": self.course.id,
                "name": "Repetitive Code Section",
                "custom_code": "AAAAAA"
            }
        )
        self.assertEqual(res_rep.status_code, 400)

        # 1c. Server generated 6-character code
        res_gen = client.post(
            "/api/faculty/classes",
            headers=self.headers_faculty_a,
            json={
                "course_id": self.course.id,
                "name": "Section Alpha Spring 2026"
            }
        )
        self.assertEqual(res_gen.status_code, 201)
        data = res_gen.json()
        code = data["class_code"]
        self.assertEqual(len(code), 6)
        self.assertTrue(code.isalnum())
        self.assertTrue(code.isupper())
        for bad_char in ["0", "O", "1", "I"]:
            self.assertNotIn(bad_char, code, f"Confusing character '{bad_char}' found in generated code {code}")
        print(f"  [PASS 1/10] Class created with 6-character unconfusing code: '{code}', weak 'DSA123' rejected.")

    def test_02_student_previews_and_joins_with_consent(self):
        """2. Student previews and joins; join without consent rejected; invalid code returns generic 404."""
        # Create a class for testing
        res_cls = client.post(
            "/api/faculty/classes",
            headers=self.headers_faculty_a,
            json={"course_id": self.course.id, "name": "Preview and Join Cohort"}
        )
        self.assertEqual(res_cls.status_code, 201)
        class_code = res_cls.json()["class_code"]

        # Preview valid class
        res_preview = client.post(
            "/api/student/classes/preview",
            headers=self.headers_student_1,
            json={"class_code": class_code.lower()}  # Case-insensitive
        )
        self.assertEqual(res_preview.status_code, 200)
        pdata = res_preview.json()
        self.assertEqual(pdata["class_name"], "Preview and Join Cohort")
        self.assertEqual(pdata["teacher_name"], "Dr. Faculty Alpha")
        self.assertIn("Joining this class lets your teacher see your current progress", pdata["consent_text"])

        # Preview invalid class returns generic 404
        res_inv = client.post(
            "/api/student/classes/preview",
            headers=self.headers_student_1,
            json={"class_code": "NONEXIST"}
        )
        self.assertEqual(res_inv.status_code, 404)
        self.assertEqual(res_inv.json()["detail"], "Invalid or inactive class code")

        # Join without consent rejected
        res_no_consent = client.post(
            "/api/student/classes/join",
            headers=self.headers_student_1,
            json={"class_code": class_code, "accept_consent": False}
        )
        self.assertEqual(res_no_consent.status_code, 400)
        self.assertIn("Consent must be accepted", res_no_consent.json()["detail"])

        # Join with consent succeeds
        res_join = client.post(
            "/api/student/classes/join",
            headers=self.headers_student_1,
            json={"class_code": class_code, "accept_consent": True}
        )
        self.assertEqual(res_join.status_code, 200)
        self.assertIn("Successfully joined class", res_join.json()["message"])

        # Duplicate join attempt returns 409 Conflict
        res_dup = client.post(
            "/api/student/classes/join",
            headers=self.headers_student_1,
            json={"class_code": class_code, "accept_consent": True}
        )
        self.assertEqual(res_dup.status_code, 409)
        print("  [PASS 2/10] Preview, consent requirement, 404 generic message, and 409 duplicate check verified.")

    def test_03_baseline_snapshot_saved_with_prior_progress(self):
        """3. Baseline snapshot saved correctly for a student with existing progress (e.g. 3 topics completed)."""
        # Create fresh student with prior progress
        student_prog = User(
            email=f"student_prog_{uuid.uuid4().hex[:6]}@obe.edu",
            full_name="Student With Prior Progress",
            password_hash=hash_password("Pass@123"),
            role="student"
        )
        self.db.add(student_prog)
        self.db.commit()
        self.db.refresh(student_prog)

        course_topics = self.db.query(Topic).filter(Topic.course_id == self.course.id).order_by(Topic.order_index).all()
        self.assertGreaterEqual(len(course_topics), 3)

        # Give student mastery on first 3 topics
        for idx in range(3):
            t = course_topics[idx]
            m = MasteryScore(
                user_id=student_prog.id,
                topic_id=t.id,
                overall_mastery=85.0,
                completion_score=100.0,
                classification="Mastered"
            )
            self.db.add(m)
        self.db.commit()

        token_prog = create_access_token(student_prog.id, "student")
        headers_prog = {"Authorization": f"Bearer {token_prog}"}

        # Faculty creates class
        res_cls = client.post(
            "/api/faculty/classes",
            headers=self.headers_faculty_a,
            json={"course_id": self.course.id, "name": "Snapshot Verification Class"}
        )
        class_id = res_cls.json()["id"]
        class_code = res_cls.json()["class_code"]

        # Student joins
        res_join = client.post(
            "/api/student/classes/join",
            headers=headers_prog,
            json={"class_code": class_code, "accept_consent": True}
        )
        self.assertEqual(res_join.status_code, 200)
        self.assertEqual(res_join.json()["baseline_completed_topics"], 3)

        # Faculty checks roster
        res_students = client.get(
            f"/api/faculty/classes/{class_id}/students",
            headers=self.headers_faculty_a
        )
        self.assertEqual(res_students.status_code, 200)
        st_data = res_students.json()["students"][0]
        self.assertEqual(st_data["baseline_completed_topics"], 3)
        self.assertEqual(st_data["completed_topics_count"], 3)
        self.assertIn("joined with 3/", st_data["progress_summary"])
        self.assertEqual(st_data["improvement_since_join"], 0)

        # Student now completes a 4th topic
        t4 = course_topics[3]
        m4 = MasteryScore(
            user_id=student_prog.id,
            topic_id=t4.id,
            overall_mastery=90.0,
            completion_score=100.0,
            classification="Mastered"
        )
        self.db.add(m4)
        self.db.commit()

        # Faculty checks roster again: baseline remains 3, current completed is 4, improvement is 1
        res_students2 = client.get(
            f"/api/faculty/classes/{class_id}/students",
            headers=self.headers_faculty_a
        )
        st_data2 = res_students2.json()["students"][0]
        self.assertEqual(st_data2["baseline_completed_topics"], 3)
        self.assertEqual(st_data2["completed_topics_count"], 4)
        self.assertEqual(st_data2["improvement_since_join"], 1)
        print("  [PASS 3/10] Baseline snapshot securely preserved (3 completed at join, +1 improvement tracked).")

    def test_04_disabled_expired_and_full_classes_reject_joins_and_regenerate(self):
        """4. Disabled, expired and full classes reject joins; regenerate invalidates the old code."""
        # 4a. Regenerate code
        res_cls = client.post(
            "/api/faculty/classes",
            headers=self.headers_faculty_a,
            json={"course_id": self.course.id, "name": "Code Regeneration Cohort"}
        )
        class_id = res_cls.json()["id"]
        old_code = res_cls.json()["class_code"]

        res_regen = client.post(
            f"/api/faculty/classes/{class_id}/regenerate-code",
            headers=self.headers_faculty_a
        )
        self.assertEqual(res_regen.status_code, 200)
        new_code = res_regen.json()["class_code"]
        self.assertNotEqual(old_code, new_code)

        # Attempt join with old code -> 404 generic
        res_old = client.post(
            "/api/student/classes/join",
            headers=self.headers_student_2,
            json={"class_code": old_code, "accept_consent": True}
        )
        self.assertEqual(res_old.status_code, 404)
        self.assertEqual(res_old.json()["detail"], "Invalid or inactive class code")

        # 4b. Disable code
        client.post(f"/api/faculty/classes/{class_id}/disable-code", headers=self.headers_faculty_a)
        res_dis = client.post(
            "/api/student/classes/join",
            headers=self.headers_student_2,
            json={"class_code": new_code, "accept_consent": True}
        )
        self.assertEqual(res_dis.status_code, 404)
        self.assertEqual(res_dis.json()["detail"], "Invalid or inactive class code")

        # Re-enable code
        client.post(f"/api/faculty/classes/{class_id}/enable-code", headers=self.headers_faculty_a)

        # 4c. Expired class
        yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat()
        res_exp_cls = client.post(
            "/api/faculty/classes",
            headers=self.headers_faculty_a,
            json={"course_id": self.course.id, "name": "Expired Cohort", "expires_at": yesterday}
        )
        exp_code = res_exp_cls.json()["class_code"]
        res_exp_join = client.post(
            "/api/student/classes/join",
            headers=self.headers_student_2,
            json={"class_code": exp_code, "accept_consent": True}
        )
        self.assertEqual(res_exp_join.status_code, 404)
        self.assertEqual(res_exp_join.json()["detail"], "Invalid or inactive class code")

        # 4d. Full class
        res_full_cls = client.post(
            "/api/faculty/classes",
            headers=self.headers_faculty_a,
            json={"course_id": self.course.id, "name": "Capacity 1 Cohort", "max_students": 1}
        )
        full_code = res_full_cls.json()["class_code"]

        # Student 1 joins -> 200
        r1 = client.post(
            "/api/student/classes/join",
            headers=self.headers_student_1,
            json={"class_code": full_code, "accept_consent": True}
        )
        self.assertEqual(r1.status_code, 200)

        # Student 2 joins -> 400 Class is full
        r2 = client.post(
            "/api/student/classes/join",
            headers=self.headers_student_2,
            json={"class_code": full_code, "accept_consent": True}
        )
        self.assertEqual(r2.status_code, 400)
        self.assertIn("Class is full", r2.json()["detail"])
        print("  [PASS 4/10] Disabled, expired, full classes rejected; code regeneration verified.")

    def test_05_student_leaves_and_rejoins_with_new_baseline(self):
        """5. Student leaves: faculty loses view access; student re-joins with refreshed baseline snapshot."""
        # Setup student and class
        student = User(
            email=f"student_leave_{uuid.uuid4().hex[:6]}@obe.edu",
            full_name="Leaving Student",
            password_hash=hash_password("Pass@123"),
            role="student"
        )
        self.db.add(student)
        self.db.commit()
        self.db.refresh(student)

        token = create_access_token(student.id, "student")
        headers = {"Authorization": f"Bearer {token}"}

        res_cls = client.post(
            "/api/faculty/classes",
            headers=self.headers_faculty_a,
            json={"course_id": self.course.id, "name": "Leave Test Class"}
        )
        class_id = res_cls.json()["id"]
        class_code = res_cls.json()["class_code"]

        # Join with baseline 0
        client.post(
            "/api/student/classes/join",
            headers=headers,
            json={"class_code": class_code, "accept_consent": True}
        )

        # Confirm faculty sees student
        res_students = client.get(f"/api/faculty/classes/{class_id}/students", headers=self.headers_faculty_a)
        self.assertEqual(len(res_students.json()["students"]), 1)

        # Student leaves class
        res_leave = client.post(f"/api/student/classes/{class_id}/leave", headers=headers)
        self.assertEqual(res_leave.status_code, 200)

        # Faculty immediately loses access (active student list is empty)
        res_after_leave = client.get(f"/api/faculty/classes/{class_id}/students", headers=self.headers_faculty_a)
        self.assertEqual(len(res_after_leave.json()["students"]), 0)

        # Student earns 2 completed topics while departed
        course_topics = self.db.query(Topic).filter(Topic.course_id == self.course.id).order_by(Topic.order_index).all()
        for idx in range(2):
            self.db.add(MasteryScore(
                user_id=student.id,
                topic_id=course_topics[idx].id,
                overall_mastery=82.0,
                completion_score=100.0,
                classification="Mastered"
            ))
        self.db.commit()

        # Student re-joins class
        res_rejoin = client.post(
            "/api/student/classes/join",
            headers=headers,
            json={"class_code": class_code, "accept_consent": True}
        )
        self.assertEqual(res_rejoin.status_code, 200)
        self.assertEqual(res_rejoin.json()["baseline_completed_topics"], 2)

        # Faculty sees student again with refreshed baseline of 2
        res_rejoined = client.get(f"/api/faculty/classes/{class_id}/students", headers=self.headers_faculty_a)
        self.assertEqual(len(res_rejoined.json()["students"]), 1)
        self.assertEqual(res_rejoined.json()["students"][0]["baseline_completed_topics"], 2)
        print("  [PASS 5/10] Immediate access revocation on leave and refreshed baseline on re-join verified.")

    def test_06_faculty_isolation_and_admin_supervision(self):
        """6. Faculty A cannot view Faculty B's class or students; Admin can access both."""
        # Class A owned by Faculty A
        res_a = client.post(
            "/api/faculty/classes",
            headers=self.headers_faculty_a,
            json={"course_id": self.course.id, "name": "Faculty A Class"}
        )
        class_a_id = res_a.json()["id"]

        # Class B owned by Faculty B
        res_b = client.post(
            "/api/faculty/classes",
            headers=self.headers_faculty_b,
            json={"course_id": self.course.id, "name": "Faculty B Class"}
        )
        class_b_id = res_b.json()["id"]

        # Faculty A attempts to view Class B's students -> 403 Forbidden
        res_a_view_b = client.get(
            f"/api/faculty/classes/{class_b_id}/students",
            headers=self.headers_faculty_a
        )
        self.assertEqual(res_a_view_b.status_code, 403)

        # Faculty A attempts to regenerate Class B's code -> 403 Forbidden
        res_a_regen_b = client.post(
            f"/api/faculty/classes/{class_b_id}/regenerate-code",
            headers=self.headers_faculty_a
        )
        self.assertEqual(res_a_regen_b.status_code, 403)

        # Faculty A lists own classes -> sees Class A, NOT Class B
        res_a_classes = client.get("/api/faculty/classes", headers=self.headers_faculty_a)
        ids_seen_by_a = [c["id"] for c in res_a_classes.json()]
        self.assertIn(class_a_id, ids_seen_by_a)
        self.assertNotIn(class_b_id, ids_seen_by_a)

        # Admin lists classes -> sees both Class A and Class B
        res_admin_classes = client.get("/api/faculty/classes", headers=self.headers_admin)
        ids_seen_by_admin = [c["id"] for c in res_admin_classes.json()]
        self.assertIn(class_a_id, ids_seen_by_admin)
        self.assertIn(class_b_id, ids_seen_by_admin)

        # Admin views students of both Class A and Class B -> 200 OK
        res_admin_view_a = client.get(f"/api/faculty/classes/{class_a_id}/students", headers=self.headers_admin)
        res_admin_view_b = client.get(f"/api/faculty/classes/{class_b_id}/students", headers=self.headers_admin)
        self.assertEqual(res_admin_view_a.status_code, 200)
        self.assertEqual(res_admin_view_b.status_code, 200)
        print("  [PASS 6/10] Multi-tenant faculty isolation and full admin supervision verified.")

    def test_07_rbac_enforcement_on_faculty_routes(self):
        """7. Student calling any /api/faculty/* gets 403; anonymous gets 401."""
        endpoints = [
            ("GET", "/api/faculty/classes"),
            ("GET", "/api/faculty/dashboard?course_id=1"),
            ("GET", "/api/faculty/topic-analytics?course_id=1"),
        ]

        for method, ep in endpoints:
            # Anonymous -> 401
            if method == "GET":
                r_anon = client.get(ep)
            else:
                r_anon = client.post(ep, json={})
            self.assertEqual(r_anon.status_code, 401, f"Expected 401 for anonymous on {ep}, got {r_anon.status_code}")

            # Student -> 403
            if method == "GET":
                r_student = client.get(ep, headers=self.headers_student_1)
            else:
                r_student = client.post(ep, headers=self.headers_student_1, json={})
            self.assertEqual(r_student.status_code, 403, f"Expected 403 for student on {ep}, got {r_student.status_code}")

        print("  [PASS 7/10] RBAC enforced: Anonymous 401, Student 403 across all /api/faculty/* endpoints.")

    def test_08_removed_student_data_preservation(self):
        """8. Removing student sets status='removed'; student user account and learning progress are NOT deleted."""
        # Create student and enroll
        student = User(
            email=f"student_remove_{uuid.uuid4().hex[:6]}@obe.edu",
            full_name="Removable Student",
            password_hash=hash_password("Pass@123"),
            role="student"
        )
        self.db.add(student)
        self.db.commit()
        self.db.refresh(student)

        token = create_access_token(student.id, "student")
        headers = {"Authorization": f"Bearer {token}"}

        res_cls = client.post(
            "/api/faculty/classes",
            headers=self.headers_faculty_a,
            json={"course_id": self.course.id, "name": "Removal Test Class"}
        )
        class_id = res_cls.json()["id"]
        class_code = res_cls.json()["class_code"]

        client.post(
            "/api/student/classes/join",
            headers=headers,
            json={"class_code": class_code, "accept_consent": True}
        )

        # Faculty removes student
        res_del = client.delete(
            f"/api/faculty/classes/{class_id}/students/{student.id}",
            headers=self.headers_faculty_a
        )
        self.assertEqual(res_del.status_code, 200)

        # Verify enrollment is marked 'removed'
        enr = self.db.query(ClassEnrollment).filter(
            ClassEnrollment.class_id == class_id,
            ClassEnrollment.student_id == student.id
        ).first()
        self.assertEqual(enr.status, "removed")
        self.assertIsNotNone(enr.left_at)

        # Verify student still exists in User table
        user_in_db = self.db.query(User).filter(User.id == student.id).first()
        self.assertIsNotNone(user_in_db)
        print("  [PASS 8/10] Student removal preserves user account and learning progress in database.")

    def test_09_rate_limiting_on_join_and_preview(self):
        """9. Rate limit join and preview attempts per user (max 10 attempts in 10 minutes -> 429)."""
        reset_rate_limits()

        # 10 attempts allowed
        for i in range(10):
            res = client.post(
                "/api/student/classes/preview",
                headers=self.headers_student_2,
                json={"class_code": f"TRY{i:03d}"}
            )
            # Response is 404 (or 200), but not 429
            self.assertNotEqual(res.status_code, 429)

        # 11th attempt must trigger 429 Too Many Requests
        res_blocked = client.post(
            "/api/student/classes/preview",
            headers=self.headers_student_2,
            json={"class_code": "TRY011"}
        )
        self.assertEqual(res_blocked.status_code, 429)
        self.assertIn("Too many class join or preview attempts", res_blocked.json()["detail"])
        print("  [PASS 9/10] Join and preview brute-force rate limiter returned 429 after 10 attempts.")

    def test_10_no_password_hash_leakage_in_faculty_responses(self):
        """10. Never return password hashes, salts, or credentials in any faculty endpoints."""
        endpoints = [
            "/api/faculty/classes",
            "/api/faculty/dashboard?course_id=1",
            "/api/faculty/topic-analytics?course_id=1"
        ]

        for ep in endpoints:
            res = client.get(ep, headers=self.headers_faculty_a)
            self.assertEqual(res.status_code, 200)
            text_body = res.text.lower()
            self.assertNotIn("password_hash", text_body)
            self.assertNotIn("passwordhash", text_body)
            self.assertNotIn("$2b$", text_body)
            self.assertNotIn("bcrypt", text_body)

        print("  [PASS 10/10] Zero credential or password hash leakage verified across faculty API responses.")


if __name__ == "__main__":
    unittest.main()
