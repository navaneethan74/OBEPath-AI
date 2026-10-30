"""
Comprehensive Test Suite for Class Communication Features:
Resources, Announcements, Doubts, Access Control, Sanitization, Rate Limits, and Class Code Validation.
"""

import sys
import os
import unittest
import uuid

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
from models import (
    User, ClassModel, ClassEnrollment, Topic, AgentLog,
    ClassResource, ClassAnnouncement, AnnouncementRead,
    ClassDoubt, ClassDoubtReply
)
from core.security import hash_password, create_access_token
from core.rate_limiter import reset_rate_limits
from core.class_codes import validate_custom_code

client = TestClient(app)


class TestClassCommunication(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.uid = uuid.uuid4().hex[:8]
        cls.pwd = "SecurePass123!"

        cls.f1_email = f"comm_faculty1_{cls.uid}@obe.edu"
        cls.f2_email = f"comm_faculty2_{cls.uid}@obe.edu"
        cls.s1_email = f"comm_student1_{cls.uid}@obe.edu"
        cls.s2_email = f"comm_student2_{cls.uid}@obe.edu"
        cls.s3_left_email = f"comm_student_left_{cls.uid}@obe.edu"
        cls.s4_nonmember_email = f"comm_student_non_{cls.uid}@obe.edu"
        cls.admin_email = f"comm_admin_{cls.uid}@obe.edu"

        with SessionLocal() as db:
            # Users
            f1 = User(email=cls.f1_email, password_hash=hash_password(cls.pwd), full_name="Professor Alpha", role="faculty")
            f2 = User(email=cls.f2_email, password_hash=hash_password(cls.pwd), full_name="Professor Beta", role="faculty")
            s1 = User(email=cls.s1_email, password_hash=hash_password(cls.pwd), full_name="Alice Wonder", role="student")
            s2 = User(email=cls.s2_email, password_hash=hash_password(cls.pwd), full_name="Bob Builder", role="student")
            s3 = User(email=cls.s3_left_email, password_hash=hash_password(cls.pwd), full_name="Charlie Dropped", role="student")
            s4 = User(email=cls.s4_nonmember_email, password_hash=hash_password(cls.pwd), full_name="Dave Outsider", role="student")
            adm = User(email=cls.admin_email, password_hash=hash_password(cls.pwd), full_name="Admin Chief", role="admin")

            db.add_all([f1, f2, s1, s2, s3, s4, adm])
            db.commit()

            cls.f1_id = f1.id
            cls.f2_id = f2.id
            cls.s1_id = s1.id
            cls.s2_id = s2.id
            cls.s3_id = s3.id
            cls.s4_id = s4.id
            cls.adm_id = adm.id

            # Class owned by Faculty 1 in Course 1
            c1 = ClassModel(
                faculty_id=f1.id,
                course_id=1,
                name=f"CS101 Communication Section {cls.uid}",
                class_code=f"SEC101{cls.uid[:4].upper()}",
                is_active=True
            )
            db.add(c1)
            db.commit()
            cls.class1_id = c1.id

            # Active enrollments for s1 and s2
            db.add(ClassEnrollment(class_id=c1.id, student_id=s1.id, status="active"))
            db.add(ClassEnrollment(class_id=c1.id, student_id=s2.id, status="active"))
            # Left enrollment for s3
            db.add(ClassEnrollment(class_id=c1.id, student_id=s3.id, status="left"))
            db.commit()

            # Find topics in Course 1 and Course 2 for validation tests
            t_c1 = db.query(Topic).filter(Topic.course_id == 1).first()
            cls.topic_c1_id = t_c1.id if t_c1 else 1

            t_c2 = db.query(Topic).filter(Topic.course_id == 2).first()
            cls.topic_c2_id = t_c2.id if t_c2 else 999

        # Generate tokens
        cls.h_f1 = {"Authorization": f"Bearer {create_access_token(cls.f1_id, 'faculty')}"}
        cls.h_f2 = {"Authorization": f"Bearer {create_access_token(cls.f2_id, 'faculty')}"}
        cls.h_s1 = {"Authorization": f"Bearer {create_access_token(cls.s1_id, 'student')}"}
        cls.h_s2 = {"Authorization": f"Bearer {create_access_token(cls.s2_id, 'student')}"}
        cls.h_s3_left = {"Authorization": f"Bearer {create_access_token(cls.s3_id, 'student')}"}
        cls.h_s4_non = {"Authorization": f"Bearer {create_access_token(cls.s4_id, 'student')}"}
        cls.h_adm = {"Authorization": f"Bearer {create_access_token(cls.adm_id, 'admin')}"}

    def setUp(self):
        reset_rate_limits()

    # =========================================================================
    # 1. Class Code Validation (small fix)
    # =========================================================================
    def test_01_class_code_validation_rejects_weak_and_short_codes(self):
        """Class code validation must reject short or guessable codes like 'PON12' and require 6+ chars with both letters & digits."""
        # 5 characters: PON12 -> reject
        ok, err = validate_custom_code("PON12", "SAFE6X")
        self.assertFalse(ok, "Expected PON12 to be rejected (length < 6)")
        self.assertIn("between 6 and 12", err)

        # 6 letters only: ABCDEF -> reject (no digits)
        ok, err = validate_custom_code("ABCDEF", "SAFE6X")
        self.assertFalse(ok, "Expected ABCDEF to be rejected (no digits)")
        self.assertIn("both letters and digits", err)

        # 6 digits only: 123456 -> reject (no letters)
        ok, err = validate_custom_code("123456", "SAFE6X")
        self.assertFalse(ok, "Expected 123456 to be rejected (no letters)")
        self.assertIn("both letters and digits", err)

        # Valid custom code: CS101A (6 chars, letters and digits) -> accept
        ok, err = validate_custom_code("CS101A", "SAFE6X")
        self.assertTrue(ok, f"Expected CS101A to be accepted, got error: {err}")
        self.assertIsNone(err)

    # =========================================================================
    # 2. Access Control: Anonymous 401, Other Faculty 404, Non-Member 404, Left 404
    # =========================================================================
    def test_02_access_control_isolation(self):
        """Unauthenticated gets 401; non-owner faculty gets 404; non-member / left student gets 404."""
        cid = self.class1_id

        # Anonymous -> 401
        self.assertEqual(client.get(f"/api/faculty/classes/{cid}/resources").status_code, 401)
        self.assertEqual(client.get(f"/api/student/classes/{cid}/resources").status_code, 401)
        self.assertEqual(client.get(f"/api/student/classes/{cid}/announcements").status_code, 401)
        self.assertEqual(client.get(f"/api/student/classes/{cid}/doubts").status_code, 401)

        # Other faculty (f2) -> 404 (does not leak existence of class to non-owner)
        self.assertEqual(client.get(f"/api/faculty/classes/{cid}/resources", headers=self.h_f2).status_code, 404)
        self.assertEqual(client.get(f"/api/faculty/classes/{cid}/announcements", headers=self.h_f2).status_code, 404)
        self.assertEqual(client.get(f"/api/faculty/classes/{cid}/doubts", headers=self.h_f2).status_code, 404)

        # Non-member student (s4) -> 404
        self.assertEqual(client.get(f"/api/student/classes/{cid}/resources", headers=self.h_s4_non).status_code, 404)
        self.assertEqual(client.get(f"/api/student/classes/{cid}/announcements", headers=self.h_s4_non).status_code, 404)
        self.assertEqual(client.get(f"/api/student/classes/{cid}/doubts", headers=self.h_s4_non).status_code, 404)

        # Left / removed student (s3) -> 404
        self.assertEqual(client.get(f"/api/student/classes/{cid}/resources", headers=self.h_s3_left).status_code, 404)
        self.assertEqual(client.get(f"/api/student/classes/{cid}/announcements", headers=self.h_s3_left).status_code, 404)
        self.assertEqual(client.get(f"/api/student/classes/{cid}/doubts", headers=self.h_s3_left).status_code, 404)

        # Empty lists for authorized members return 200
        res_f1 = client.get(f"/api/faculty/classes/{cid}/resources", headers=self.h_f1)
        self.assertEqual(res_f1.status_code, 200)
        self.assertEqual(res_f1.json(), [])

        res_s1 = client.get(f"/api/student/classes/{cid}/resources", headers=self.h_s1)
        self.assertEqual(res_s1.status_code, 200)
        self.assertEqual(res_s1.json(), [])

    # =========================================================================
    # 3. Class Resources: Validation, Dangerous URLs, Soft Delete & Audit
    # =========================================================================
    def test_03_class_resources_workflow_and_validation(self):
        """Test URL validation (reject javascript:, data:), topic course integrity, soft-delete and audit."""
        cid = self.class1_id

        # Dangerous URL scheme rejected
        for bad_url in ["javascript:alert(1)", "data:text/html,<script>alert(1)</script>", "file:///etc/passwd"]:
            res = client.post(f"/api/faculty/classes/{cid}/resources", json={
                "title": "Bad Resource",
                "url": bad_url,
                "resource_type": "article"
            }, headers=self.h_f1)
            self.assertEqual(res.status_code, 400, f"Expected {bad_url} to be rejected")
            self.assertIn("http or https", res.json()["detail"])

        # Topic from another course rejected
        res_bad_topic = client.post(f"/api/faculty/classes/{cid}/resources", json={
            "title": "Cross Course Topic",
            "url": "https://example.com/guide",
            "resource_type": "article",
            "topic_id": self.topic_c2_id  # Belongs to course 2, not class's course 1
        }, headers=self.h_f1)
        self.assertEqual(res_bad_topic.status_code, 400)
        self.assertIn("does not belong to the class course", res_bad_topic.json()["detail"])

        # Valid resource created
        res_create = client.post(f"/api/faculty/classes/{cid}/resources", json={
            "title": "<b>Clean Variables Guide</b>\x00\x07",
            "description": "Comprehensive reference on Python variables\x0b",
            "url": "https://docs.python.org/3/tutorial/introduction.html",
            "resource_type": "notes",
            "topic_id": self.topic_c1_id
        }, headers=self.h_f1)
        self.assertEqual(res_create.status_code, 201)
        data = res_create.json()
        rid = data["id"]
        # HTML stored and returned as plain text; control chars stripped
        self.assertEqual(data["title"], "<b>Clean Variables Guide</b>")
        self.assertNotIn("\x00", data["title"])
        self.assertEqual(data["resource_type"], "notes")

        # Student reads resource
        stu_res = client.get(f"/api/student/classes/{cid}/resources", headers=self.h_s1)
        self.assertEqual(stu_res.status_code, 200)
        self.assertEqual(len(stu_res.json()), 1)
        self.assertEqual(stu_res.json()[0]["id"], rid)

        # Faculty soft deletes resource
        del_res = client.delete(f"/api/faculty/classes/{cid}/resources/{rid}", headers=self.h_f1)
        self.assertEqual(del_res.status_code, 200)

        # Student no longer sees soft-deleted resource
        stu_res_after = client.get(f"/api/student/classes/{cid}/resources", headers=self.h_s1)
        self.assertEqual(stu_res_after.status_code, 200)
        self.assertEqual(len(stu_res_after.json()), 0)

        # Audit log verified in AgentLog
        with SessionLocal() as db:
            log = db.query(AgentLog).filter(
                AgentLog.user_id == self.f1_id,
                AgentLog.action == "resource_deleted"
            ).first()
            self.assertIsNotNone(log)
            self.assertIn(str(rid), log.message)

    # =========================================================================
    # 4. Announcements: Pinned Ordering, Unread Counts & Mark Read
    # =========================================================================
    def test_04_announcements_pinned_ordering_and_read_tracking(self):
        """Announcements ordered with pinned first; read status and unread counts tracked per student."""
        cid = self.class1_id

        # Post unpinned announcement
        res1 = client.post(f"/api/faculty/classes/{cid}/announcements", json={
            "title": "Regular Notice",
            "body": "Welcome to class communication hub.",
            "pinned": False
        }, headers=self.h_f1)
        self.assertEqual(res1.status_code, 201)
        a1_id = res1.json()["id"]

        # Post pinned announcement
        res2 = client.post(f"/api/faculty/classes/{cid}/announcements", json={
            "title": "Urgent Exam Schedule",
            "body": "Midterm test on Friday.",
            "pinned": True
        }, headers=self.h_f1)
        self.assertEqual(res2.status_code, 201)
        a2_id = res2.json()["id"]

        # Student checks unread count: should be 2
        count_res = client.get(f"/api/student/classes/{cid}/announcements/unread-count", headers=self.h_s1)
        self.assertEqual(count_res.status_code, 200)
        self.assertEqual(count_res.json()["unread_count"], 2)

        # Student reads announcement list: pinned announcement should come FIRST
        list_res = client.get(f"/api/student/classes/{cid}/announcements", headers=self.h_s1)
        self.assertEqual(list_res.status_code, 200)
        items = list_res.json()
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["id"], a2_id)  # Pinned first
        self.assertTrue(items[0]["pinned"])
        self.assertFalse(items[0]["is_read"])
        self.assertFalse(items[1]["is_read"])

        # Student marks a2 as read
        mark_res = client.post(f"/api/student/classes/{cid}/announcements/{a2_id}/read", headers=self.h_s1)
        self.assertEqual(mark_res.status_code, 200)

        # Unread count now 1 for student 1
        count_after = client.get(f"/api/student/classes/{cid}/announcements/unread-count", headers=self.h_s1)
        self.assertEqual(count_after.json()["unread_count"], 1)

        # Student 2 still has 2 unread (isolation of read markers)
        count_s2 = client.get(f"/api/student/classes/{cid}/announcements/unread-count", headers=self.h_s2)
        self.assertEqual(count_s2.json()["unread_count"], 2)

    # =========================================================================
    # 5. Doubts: Visibility, Name Masking, No Student Reply, Faculty Close
    # =========================================================================
    def test_05_doubts_visibility_masking_and_lifecycle(self):
        """Private doubts invisible to classmates; class doubts show first name only; students cannot reply."""
        cid = self.class1_id

        # Student 1 posts a private doubt
        res_priv = client.post(f"/api/student/classes/{cid}/doubts", json={
            "title": "Private Question on Loop Indexing",
            "body": "I am struggling with off-by-one errors.",
            "visibility": "private"
        }, headers=self.h_s1)
        self.assertEqual(res_priv.status_code, 201)
        priv_id = res_priv.json()["id"]

        # Student 1 posts a class-visible doubt
        res_pub = client.post(f"/api/student/classes/{cid}/doubts", json={
            "title": "Class Question on Time Complexity",
            "body": "Is binary search always O(log n)?",
            "visibility": "class"
        }, headers=self.h_s1)
        self.assertEqual(res_pub.status_code, 201)
        pub_id = res_pub.json()["id"]

        # Student 1 sees both doubts
        s1_doubts = client.get(f"/api/student/classes/{cid}/doubts", headers=self.h_s1).json()
        s1_ids = [d["id"] for d in s1_doubts]
        self.assertIn(priv_id, s1_ids)
        self.assertIn(pub_id, s1_ids)

        # Student 2 sees ONLY the class-visible doubt, NEVER the private doubt
        s2_doubts = client.get(f"/api/student/classes/{cid}/doubts", headers=self.h_s2).json()
        s2_ids = [d["id"] for d in s2_doubts]
        self.assertNotIn(priv_id, s2_ids, "Private doubt must be invisible to classmate")
        self.assertIn(pub_id, s2_ids, "Class-visible doubt must be visible to classmate")

        # Check name masking for Student 2: Alice Wonder -> 'Alice' only, no email, no password hash
        classmate_doubt = next(d for d in s2_doubts if d["id"] == pub_id)
        self.assertEqual(classmate_doubt["author_name"], "Alice", "Author name must be first name only")
        self.assertNotIn("@", str(classmate_doubt), "Never expose author email")
        self.assertNotIn("password", str(classmate_doubt).lower())

        # Student 2 attempts to reply to doubt -> 403 Forbidden
        reply_stu = client.post(f"/api/student/classes/{cid}/doubts/{pub_id}/replies", json={
            "body": "I think it is log n."
        }, headers=self.h_s2)
        self.assertEqual(reply_stu.status_code, 403, "Students cannot reply to doubts in this version")

        # Faculty replies to doubt -> status auto-updates from 'open' to 'answered'
        reply_fac = client.post(f"/api/faculty/classes/{cid}/doubts/{pub_id}/replies", json={
            "body": "Yes, binary search is O(log n) when the input array is sorted."
        }, headers=self.h_f1)
        self.assertEqual(reply_fac.status_code, 201)
        rep_id = reply_fac.json()["id"]

        # Verify doubt status updated to 'answered'
        doubt_check = client.get(f"/api/faculty/classes/{cid}/doubts", headers=self.h_f1).json()
        answered_d = next(d for d in doubt_check if d["id"] == pub_id)
        self.assertEqual(answered_d["status"], "answered")
        self.assertEqual(len(answered_d["replies"]), 1)
        self.assertEqual(answered_d["replies"][0]["id"], rep_id)

        # Faculty closes doubt
        close_res = client.patch(f"/api/faculty/classes/{cid}/doubts/{pub_id}/close", headers=self.h_f1)
        self.assertEqual(close_res.status_code, 200)
        self.assertEqual(close_res.json()["status"], "closed")

        # Faculty soft-deletes inappropriate reply
        del_rep = client.delete(f"/api/faculty/classes/{cid}/doubts/{pub_id}/replies/{rep_id}", headers=self.h_f1)
        self.assertEqual(del_rep.status_code, 200)

        # Deleted reply not returned in doubt
        doubt_after = client.get(f"/api/faculty/classes/{cid}/doubts", headers=self.h_f1).json()
        closed_d = next(d for d in doubt_after if d["id"] == pub_id)
        self.assertEqual(len(closed_d["replies"]), 0)

    # =========================================================================
    # 6. Rate Limits: Student 5/hr & 20/day; Faculty 30/hr -> 429 Retry-After
    # =========================================================================
    def test_06_rate_limits_and_retry_after_headers(self):
        """Rate limits return HTTP 429 with Retry-After header."""
        cid = self.class1_id

        # Student rate limit: max 5 doubts per hour
        for i in range(5):
            res = client.post(f"/api/student/classes/{cid}/doubts", json={
                "title": f"Doubt {i+1}",
                "body": "Content body question."
            }, headers=self.h_s1)
            self.assertEqual(res.status_code, 201)

        # 6th doubt -> 429
        res_limit = client.post(f"/api/student/classes/{cid}/doubts", json={
            "title": "Doubt 6 Exceeding",
            "body": "Content body question."
        }, headers=self.h_s1)
        self.assertEqual(res_limit.status_code, 429)
        self.assertIn("Retry-After", res_limit.headers)
        self.assertIn("Hourly doubt limit", res_limit.json()["detail"])

        # Reset rate limits for faculty test
        reset_rate_limits()

        # Faculty rate limit: max 30 posts per hour
        for i in range(30):
            res_ann = client.post(f"/api/faculty/classes/{cid}/announcements", json={
                "title": f"Announcement {i+1}",
                "body": "Announcement text"
            }, headers=self.h_f1)
            self.assertEqual(res_ann.status_code, 201)

        # 31st post -> 429
        res_fac_limit = client.post(f"/api/faculty/classes/{cid}/announcements", json={
            "title": "Announcement 31 Exceeding",
            "body": "Announcement text"
        }, headers=self.h_f1)
        self.assertEqual(res_fac_limit.status_code, 429)
        self.assertIn("Retry-After", res_fac_limit.headers)
        self.assertIn("Hourly post limit", res_fac_limit.json()["detail"])

    def test_07_regression_empty_class_returns_200_with_empty_lists(self):
        """
        Regression Test:
        Faculty owner opens an empty class and gets 200 with [] on resources,
        announcements, and doubts through the exact URLs used by the frontend.
        Non-owner faculty gets 404. Non-enrolled student gets 404.
        """
        # Faculty 1 creates an empty class
        res_create = client.post("/api/faculty/classes", json={
            "course_id": 1,
            "name": "Regression Empty Class",
            "max_students": 25
        }, headers=self.h_f1)
        self.assertEqual(res_create.status_code, 201)
        empty_cid = res_create.json()["id"]

        # Exact frontend URLs: Faculty owner GET resources, announcements, doubts
        res_r = client.get(f"/api/faculty/classes/{empty_cid}/resources", headers=self.h_f1)
        self.assertEqual(res_r.status_code, 200)
        self.assertEqual(res_r.json(), [])

        res_a = client.get(f"/api/faculty/classes/{empty_cid}/announcements", headers=self.h_f1)
        self.assertEqual(res_a.status_code, 200)
        self.assertEqual(res_a.json(), [])

        res_d = client.get(f"/api/faculty/classes/{empty_cid}/doubts", headers=self.h_f1)
        self.assertEqual(res_d.status_code, 200)
        self.assertEqual(res_d.json(), [])

        # Non-owner faculty (f2) gets 404 on the same empty class
        self.assertEqual(client.get(f"/api/faculty/classes/{empty_cid}/resources", headers=self.h_f2).status_code, 404)
        self.assertEqual(client.get(f"/api/faculty/classes/{empty_cid}/announcements", headers=self.h_f2).status_code, 404)
        self.assertEqual(client.get(f"/api/faculty/classes/{empty_cid}/doubts", headers=self.h_f2).status_code, 404)

        # Non-enrolled student gets 404
        self.assertEqual(client.get(f"/api/student/classes/{empty_cid}/resources", headers=self.h_s1).status_code, 404)
        self.assertEqual(client.get(f"/api/student/classes/{empty_cid}/announcements", headers=self.h_s1).status_code, 404)
        self.assertEqual(client.get(f"/api/student/classes/{empty_cid}/doubts", headers=self.h_s1).status_code, 404)

        # Enrolled student gets 200 with []
        with SessionLocal() as db:
            db.add(ClassEnrollment(class_id=empty_cid, student_id=self.s1_id, status="active"))
            db.commit()

        s_res_r = client.get(f"/api/student/classes/{empty_cid}/resources", headers=self.h_s1)
        self.assertEqual(s_res_r.status_code, 200)
        self.assertEqual(s_res_r.json(), [])

        s_res_a = client.get(f"/api/student/classes/{empty_cid}/announcements", headers=self.h_s1)
        self.assertEqual(s_res_a.status_code, 200)
        self.assertEqual(s_res_a.json(), [])

        s_res_d = client.get(f"/api/student/classes/{empty_cid}/doubts", headers=self.h_s1)
        self.assertEqual(s_res_d.status_code, 200)
        self.assertEqual(s_res_d.json(), [])



if __name__ == "__main__":
    unittest.main()

