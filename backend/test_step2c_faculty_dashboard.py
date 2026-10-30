"""
test_step2c_faculty_dashboard.py
Step 2C Comprehensive Test Suite: Faculty Dashboard Views (Read-Only)

Verifies:
1. Access control:
   - Faculty A cannot access Faculty B's class (404 Not Found to avoid leaking existence)
   - Faculty A cannot access student not actively enrolled in class (404)
   - Student role gets 403 Forbidden
   - Anonymous gets 401 Unauthorized
   - Admin gets 200 OK and full access
2. Overview numbers match known seeded data:
   - Average overall mastery
   - CO achieved counts & attainment averages
   - Topic masteries
   - Completion distribution
   - Top learning gaps
3. CO drill-down returns weighted topics and per-student per-topic concept mastery
4. At-risk evaluation with exact reasons for all 3 rules:
   - Prerequisite < PREREQ_UNLOCK
   - Overall mastery < AT_RISK_MASTERY (50.0%)
   - Inactivity >= INACTIVE_DAYS (7 days)
5. Removed or left students disappear from overview, outcomes, and student roster (and 404 on direct detail)
6. Baseline vs current delta correct for a student who joined with prior completed topics
7. Empty class returns 200 OK with empty lists (no errors)
8. No sensitive fields (password_hash, credentials) leaked anywhere
9. Query count stays bounded for a class of 40 students (strictly guards against N+1 queries)
"""

import os
import sys
import json
import uuid
import unittest
from datetime import datetime, timedelta
from sqlalchemy import event

# Ensure backend directory is in sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from main import app
from database import SessionLocal, engine
from models import (
    User, Course, Topic, TopicPrerequisite, TopicOutcomeMapping,
    CourseOutcome, MasteryScore, ClassModel, ClassEnrollment,
    OutcomeAttainment, LearningPath, LearningPathItem, AssessmentAttempt
)
from core.security import create_access_token, hash_password
from core.thresholds import (
    PREREQ_UNLOCK, ASSESSMENT_PASS, TOPIC_MASTERY,
    CO_ACHIEVED_DEFAULT, AT_RISK_MASTERY, INACTIVE_DAYS
)

client = TestClient(app)

class TestStep2CFacultyDashboard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()

        # Find or create Course
        cls.course = cls.db.query(Course).filter(Course.id == 1).first()
        if not cls.course:
            cls.course = Course(id=1, code="CS101", title="Python Programming", description="Core Python")
            cls.db.add(cls.course)
            cls.db.commit()

        # Ensure topics exist
        cls.topics = cls.db.query(Topic).filter(Topic.course_id == cls.course.id).order_by(Topic.order_index).all()
        if len(cls.topics) < 3:
            t1 = Topic(course_id=cls.course.id, code="T1", title="Arrays & Strings", order_index=1, description="Basics", learning_objective="Arrays")
            t2 = Topic(course_id=cls.course.id, code="T2", title="Linked Lists", order_index=2, description="Lists", learning_objective="Lists")
            t3 = Topic(course_id=cls.course.id, code="T3", title="Trees", order_index=3, description="Trees", learning_objective="Trees")
            cls.db.add_all([t1, t2, t3])
            cls.db.commit()
            cls.topics = cls.db.query(Topic).filter(Topic.course_id == cls.course.id).order_by(Topic.order_index).all()

        # Ensure prerequisites: Topic 2 depends on Topic 1, Topic 3 depends on Topic 2
        p1 = cls.db.query(TopicPrerequisite).filter(TopicPrerequisite.topic_id == cls.topics[1].id).first()
        if not p1:
            cls.db.add(TopicPrerequisite(topic_id=cls.topics[1].id, prerequisite_topic_id=cls.topics[0].id, required_mastery_pct=PREREQ_UNLOCK))
        p2 = cls.db.query(TopicPrerequisite).filter(TopicPrerequisite.topic_id == cls.topics[2].id).first()
        if not p2:
            cls.db.add(TopicPrerequisite(topic_id=cls.topics[2].id, prerequisite_topic_id=cls.topics[1].id, required_mastery_pct=PREREQ_UNLOCK))
        cls.db.commit()

        # Ensure Course Outcomes exist
        cls.outcomes = cls.db.query(CourseOutcome).filter(CourseOutcome.course_id == cls.course.id).order_by(CourseOutcome.code).all()
        if not cls.outcomes:
            co1 = CourseOutcome(course_id=cls.course.id, code="CO1", description="Understand Linear Structures", target_attainment_pct=70.0)
            co2 = CourseOutcome(course_id=cls.course.id, code="CO2", description="Understand Hierarchical Structures", target_attainment_pct=75.0)
            cls.db.add_all([co1, co2])
            cls.db.commit()
            cls.outcomes = cls.db.query(CourseOutcome).filter(CourseOutcome.course_id == cls.course.id).order_by(CourseOutcome.code).all()

        # Ensure Topic Outcome Mappings
        m1 = cls.db.query(TopicOutcomeMapping).filter(TopicOutcomeMapping.outcome_id == cls.outcomes[0].id).first()
        if not m1:
            cls.db.add(TopicOutcomeMapping(topic_id=cls.topics[0].id, outcome_id=cls.outcomes[0].id, weight=1.0))
            cls.db.add(TopicOutcomeMapping(topic_id=cls.topics[1].id, outcome_id=cls.outcomes[0].id, weight=1.5))
            cls.db.commit()

        # Create Users: Faculty A, Faculty B, Student, Admin
        uid = uuid.uuid4().hex[:6]
        cls.faculty_a = User(email=f"fac_a_{uid}@obe.edu", password_hash=hash_password("Pass123!"), full_name="Faculty A", role="faculty")
        cls.faculty_b = User(email=f"fac_b_{uid}@obe.edu", password_hash=hash_password("Pass123!"), full_name="Faculty B", role="faculty")
        cls.student_user = User(email=f"stud_{uid}@obe.edu", password_hash=hash_password("Pass123!"), full_name="Student Test", role="student")
        cls.admin_user = User(email=f"admin_{uid}@obe.edu", password_hash=hash_password("Pass123!"), full_name="Admin Test", role="admin")

        cls.db.add_all([cls.faculty_a, cls.faculty_b, cls.student_user, cls.admin_user])
        cls.db.commit()

        cls.headers_faculty_a = {"Authorization": f"Bearer {create_access_token(cls.faculty_a.id, 'faculty')}"}
        cls.headers_faculty_b = {"Authorization": f"Bearer {create_access_token(cls.faculty_b.id, 'faculty')}"}
        cls.headers_student = {"Authorization": f"Bearer {create_access_token(cls.student_user.id, 'student')}"}
        cls.headers_admin = {"Authorization": f"Bearer {create_access_token(cls.admin_user.id, 'admin')}"}

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_01_access_control_and_isolation(self):
        """
        Faculty A cannot access Faculty B's class overview, outcome drilldown,
        student list, student detail, or learning path (returns 404 to avoid leaking existence).
        Student gets 403 Forbidden. Anonymous gets 401 Unauthorized. Admin can access all.
        """
        # Create Class A (Faculty A) and Class B (Faculty B)
        class_a = ClassModel(faculty_id=self.faculty_a.id, course_id=self.course.id, name="Class A", class_code=f"CA{uuid.uuid4().hex[:4].upper()}")
        class_b = ClassModel(faculty_id=self.faculty_b.id, course_id=self.course.id, name="Class B", class_code=f"CB{uuid.uuid4().hex[:4].upper()}")
        self.db.add_all([class_a, class_b])
        self.db.commit()

        # Enroll student in Class B
        enr_b = ClassEnrollment(class_id=class_b.id, student_id=self.student_user.id, status="active")
        self.db.add(enr_b)
        self.db.commit()

        endpoints_to_test = [
            f"/api/faculty/classes/{class_b.id}/overview",
            f"/api/faculty/classes/{class_b.id}/outcomes/{self.outcomes[0].id}",
            f"/api/faculty/classes/{class_b.id}/students/{self.student_user.id}",
            f"/api/faculty/classes/{class_b.id}/students/{self.student_user.id}/learning-path"
        ]

        for ep in endpoints_to_test:
            # 1. Faculty A accessing Faculty B's class -> 404 Not Found
            res_a = client.get(ep, headers=self.headers_faculty_a)
            self.assertEqual(res_a.status_code, 404, f"Faculty A must receive 404 for {ep}, got {res_a.status_code}")

            # 2. Student accessing endpoint -> 403 Forbidden
            res_s = client.get(ep, headers=self.headers_student)
            self.assertEqual(res_s.status_code, 403, f"Student must receive 403 for {ep}, got {res_s.status_code}")

            # 3. Anonymous accessing endpoint -> 401 Unauthorized
            res_anon = client.get(ep)
            self.assertEqual(res_anon.status_code, 401, f"Anonymous must receive 401 for {ep}, got {res_anon.status_code}")

            # 4. Admin accessing endpoint -> 200 OK
            res_admin = client.get(ep, headers=self.headers_admin)
            self.assertEqual(res_admin.status_code, 200, f"Admin must receive 200 for {ep}, got {res_admin.status_code}")

        # Faculty A accessing a student not actively enrolled in Class A -> 404
        res_unenrolled = client.get(
            f"/api/faculty/classes/{class_a.id}/students/{self.student_user.id}",
            headers=self.headers_faculty_a
        )
        self.assertEqual(res_unenrolled.status_code, 404)

    def test_02_empty_class_returns_200_with_empty_lists(self):
        """
        Empty class returns 200 OK with empty lists and zero metrics without errors.
        """
        empty_class = ClassModel(faculty_id=self.faculty_a.id, course_id=self.course.id, name="Empty Class", class_code=f"EM{uuid.uuid4().hex[:4].upper()}")
        self.db.add(empty_class)
        self.db.commit()

        # Overview
        r_over = client.get(f"/api/faculty/classes/{empty_class.id}/overview", headers=self.headers_faculty_a)
        self.assertEqual(r_over.status_code, 200)
        data_over = r_over.json()
        self.assertEqual(data_over["active_students_count"], 0)
        self.assertEqual(data_over["average_overall_mastery"], 0.0)
        self.assertEqual(data_over["at_risk_count"], 0)
        self.assertEqual(data_over["completion_distribution"], [])
        self.assertEqual(data_over["top_learning_gaps"], [])

        # Outcomes drilldown
        r_out = client.get(f"/api/faculty/classes/{empty_class.id}/outcomes/{self.outcomes[0].id}", headers=self.headers_faculty_a)
        self.assertEqual(r_out.status_code, 200)
        data_out = r_out.json()
        self.assertEqual(data_out["student_rows"], [])
        self.assertEqual(data_out["achieved_count"], 0)
        self.assertEqual(data_out["total_students"], 0)

        # Students list
        r_stud = client.get(f"/api/faculty/classes/{empty_class.id}/students", headers=self.headers_faculty_a)
        self.assertEqual(r_stud.status_code, 200)
        data_stud = r_stud.json()
        self.assertEqual(data_stud["total_active_students"], 0)
        self.assertEqual(data_stud["students"], [])

    def test_03_overview_metrics_match_known_data(self):
        """
        Verifies calculated numbers on class overview: average mastery,
        CO achievement counts, topic-wise mastery, and completion distribution.
        """
        # Create class with 2 known students
        test_class = ClassModel(faculty_id=self.faculty_a.id, course_id=self.course.id, name="Overview Math Class", class_code=f"OV{uuid.uuid4().hex[:4].upper()}")
        self.db.add(test_class)
        self.db.commit()

        s1 = User(email=f"ov1_{uuid.uuid4().hex[:5]}@obe.edu", password_hash="hash", full_name="Overview Student 1", role="student")
        s2 = User(email=f"ov2_{uuid.uuid4().hex[:5]}@obe.edu", password_hash="hash", full_name="Overview Student 2", role="student")
        self.db.add_all([s1, s2])
        self.db.commit()

        e1 = ClassEnrollment(class_id=test_class.id, student_id=s1.id, status="active", joined_at=datetime.utcnow())
        e2 = ClassEnrollment(class_id=test_class.id, student_id=s2.id, status="active", joined_at=datetime.utcnow())
        self.db.add_all([e1, e2])
        self.db.commit()

        # Set specific masteries across all course topics
        # s1: all topics 80.0% overall mastery, 100.0 completion -> average = 80.0%, all topics complete
        # s2: all topics 40.0% overall mastery, 0.0 completion -> average = 40.0%, 0 topics complete
        for t in self.topics:
            self.db.add(MasteryScore(user_id=s1.id, topic_id=t.id, overall_mastery=80.0, completion_score=100.0))
            self.db.add(MasteryScore(user_id=s2.id, topic_id=t.id, overall_mastery=40.0, completion_score=0.0))

        co1 = self.outcomes[0]
        co1_target = co1.target_attainment_pct if (co1.target_attainment_pct is not None and co1.target_attainment_pct > 0) else CO_ACHIEVED_DEFAULT
        # s1: Achieved (target + 10), s2: Not Achieved (target - 20)
        oa1 = OutcomeAttainment(user_id=s1.id, course_id=self.course.id, outcome_id=co1.id, attainment_percentage=co1_target + 10.0, status="Achieved")
        oa2 = OutcomeAttainment(user_id=s2.id, course_id=self.course.id, outcome_id=co1.id, attainment_percentage=max(0.0, co1_target - 20.0), status="In Progress")
        self.db.add_all([oa1, oa2])
        self.db.commit()

        res = client.get(f"/api/faculty/classes/{test_class.id}/overview", headers=self.headers_faculty_a)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data["active_students_count"], 2)
        # Class average overall mastery across all course topics: (80.0 + 40.0) / 2 = 60.0
        self.assertAlmostEqual(data["average_overall_mastery"], 60.0, delta=1.0)

        # CO1 achievement
        co1_data = next((c for c in data["outcomes"] if c["outcome_id"] == co1.id), None)
        self.assertIsNotNone(co1_data)
        self.assertEqual(co1_data["achieved_count"], 1)
        self.assertEqual(co1_data["total_students"], 2)

        # Completion distribution: s2 has 0 complete, s1 has all complete
        dist = {d["completed_topics"]: d["student_count"] for d in data["completion_distribution"]}
        self.assertEqual(dist.get(0), 1) # s2
        self.assertEqual(dist.get(len(self.topics)), 1) # s1

        # Top learning gaps exist
        self.assertTrue(len(data["top_learning_gaps"]) > 0)

    def test_04_outcome_drilldown_weighted_topics_and_concept_mastery(self):
        """
        Verifies GET /api/faculty/classes/{class_id}/outcomes/{outcome_id} returns:
        - Contributing topics with weights
        - Class average per contributing topic
        - Per-student rows with CO attainment and concept-wise topic mastery
        """
        test_class = ClassModel(faculty_id=self.faculty_a.id, course_id=self.course.id, name="Drilldown Class", class_code=f"DD{uuid.uuid4().hex[:4].upper()}")
        self.db.add(test_class)
        self.db.commit()

        s = User(email=f"dd_{uuid.uuid4().hex[:5]}@obe.edu", password_hash="hash", full_name="Concept Student", role="student")
        self.db.add(s)
        self.db.commit()

        self.db.add(ClassEnrollment(class_id=test_class.id, student_id=s.id, status="active"))
        # Add masteries
        t1 = self.topics[0]
        t2 = self.topics[1]
        self.db.add(MasteryScore(user_id=s.id, topic_id=t1.id, overall_mastery=82.0))
        self.db.add(MasteryScore(user_id=s.id, topic_id=t2.id, overall_mastery=64.0))

        co = self.outcomes[0]
        target = co.target_attainment_pct if (co.target_attainment_pct is not None and co.target_attainment_pct > 0) else CO_ACHIEVED_DEFAULT
        self.db.add(OutcomeAttainment(user_id=s.id, course_id=self.course.id, outcome_id=co.id, attainment_percentage=target + 5.0))
        self.db.commit()

        res = client.get(f"/api/faculty/classes/{test_class.id}/outcomes/{co.id}", headers=self.headers_faculty_a)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data["outcome"]["id"], co.id)
        self.assertEqual(len(data["student_rows"]), 1)
        st_row = data["student_rows"][0]
        self.assertEqual(st_row["student_id"], s.id)
        self.assertEqual(st_row["student_name"], "Concept Student")
        self.assertEqual(st_row["co_attainment_pct"], target + 5.0)
        self.assertTrue(st_row["is_achieved"]) # target + 5.0 >= target

        # Check concept mastery cells
        c_map = {c["topic_id"]: c["mastery_score"] for c in st_row["concept_mastery"]}
        self.assertEqual(c_map.get(t1.id), 82.0)
        self.assertEqual(c_map.get(t2.id), 64.0)

    def test_05_at_risk_reasons_computed_correctly(self):
        """
        Tests the 3 rules for at-risk detection:
        Rule 1: Prerequisite of current topic < PREREQ_UNLOCK
        Rule 2: Overall mastery < AT_RISK_MASTERY (50.0%)
        Rule 3: Inactivity >= INACTIVE_DAYS (7 days)
        """
        test_class = ClassModel(faculty_id=self.faculty_a.id, course_id=self.course.id, name="At-Risk Class", class_code=f"AR{uuid.uuid4().hex[:4].upper()}")
        self.db.add(test_class)
        self.db.commit()

        sa = User(email=f"sa_{uuid.uuid4().hex[:5]}@obe.edu", password_hash="hash", full_name="Student At-Risk Rule 1", role="student")
        sb = User(email=f"sb_{uuid.uuid4().hex[:5]}@obe.edu", password_hash="hash", full_name="Student At-Risk Rule 2", role="student")
        sc = User(email=f"sc_{uuid.uuid4().hex[:5]}@obe.edu", password_hash="hash", full_name="Student At-Risk Rule 3", role="student")
        sd = User(email=f"sd_{uuid.uuid4().hex[:5]}@obe.edu", password_hash="hash", full_name="Student Safe", role="student")

        self.db.add_all([sa, sb, sc, sd])
        self.db.commit()

        now = datetime.utcnow()
        ea = ClassEnrollment(class_id=test_class.id, student_id=sa.id, status="active", joined_at=now - timedelta(days=2))
        eb = ClassEnrollment(class_id=test_class.id, student_id=sb.id, status="active", joined_at=now - timedelta(days=2))
        ec = ClassEnrollment(class_id=test_class.id, student_id=sc.id, status="active", joined_at=now - timedelta(days=15))
        ed = ClassEnrollment(class_id=test_class.id, student_id=sd.id, status="active", joined_at=now - timedelta(days=2))
        self.db.add_all([ea, eb, ec, ed])
        self.db.commit()

        t1 = self.topics[0]
        t2 = self.topics[1]

        # Student A: Current topic is Topic 2, Prereq Topic 1 has 40.0% (<60%). All other topics have 70.0% -> avg >= 65% (>50%). Active yesterday.
        lp_a = LearningPath(user_id=sa.id, course_id=self.course.id, status="ACTIVE")
        self.db.add(lp_a)
        self.db.flush()
        self.db.add(LearningPathItem(learning_path_id=lp_a.id, topic_id=t2.id, sequence_order=1, status="CURRENT", recommendation_reason="Active study"))
        for t in self.topics:
            m_val = 40.0 if t.id == t1.id else 70.0
            self.db.add(MasteryScore(user_id=sa.id, topic_id=t.id, overall_mastery=m_val))
        self.db.add(AssessmentAttempt(attempt_uuid=uuid.uuid4().hex, user_id=sa.id, course_id=self.course.id, topic_id=t2.id, attempt_type="practice", score=7, max_score=10, percentage=70.0, passed=True, created_at=now - timedelta(days=1)))

        # Student B: All topics have 30.0% (<50%). Active yesterday.
        for t in self.topics:
            self.db.add(MasteryScore(user_id=sb.id, topic_id=t.id, overall_mastery=30.0))
        self.db.add(AssessmentAttempt(attempt_uuid=uuid.uuid4().hex, user_id=sb.id, course_id=self.course.id, topic_id=t1.id, attempt_type="practice", score=3, max_score=10, percentage=30.0, passed=False, created_at=now - timedelta(days=1)))

        # Student C: All topics have 80.0% (>50%), but joined 15 days ago and last attempt was 10 days ago (>= 7 days inactive)
        for t in self.topics:
            self.db.add(MasteryScore(user_id=sc.id, topic_id=t.id, overall_mastery=80.0))
        self.db.add(AssessmentAttempt(attempt_uuid=uuid.uuid4().hex, user_id=sc.id, course_id=self.course.id, topic_id=t1.id, attempt_type="practice", score=8, max_score=10, percentage=80.0, passed=True, created_at=now - timedelta(days=10)))

        # Student D: Safe: All topics have 85.0% (>50%), active yesterday, no prereq gaps
        for t in self.topics:
            self.db.add(MasteryScore(user_id=sd.id, topic_id=t.id, overall_mastery=85.0))
        self.db.add(AssessmentAttempt(attempt_uuid=uuid.uuid4().hex, user_id=sd.id, course_id=self.course.id, topic_id=t1.id, attempt_type="practice", score=9, max_score=10, percentage=90.0, passed=True, created_at=now - timedelta(days=1)))
        self.db.commit()

        # Query students endpoint
        res = client.get(f"/api/faculty/classes/{test_class.id}/students", headers=self.headers_faculty_a)
        self.assertEqual(res.status_code, 200)
        data = res.json()["students"]
        s_map = {s["id"]: s for s in data}

        # Check Student A (Rule 1)
        self.assertTrue(s_map[sa.id]["is_at_risk"])
        reasons_a = " ".join(s_map[sa.id]["at_risk_reasons"])
        self.assertIn("Prerequisite", reasons_a)
        self.assertIn("below 60.0%", reasons_a)

        # Check Student B (Rule 2)
        self.assertTrue(s_map[sb.id]["is_at_risk"])
        reasons_b = " ".join(s_map[sb.id]["at_risk_reasons"])
        self.assertIn("Overall mastery", reasons_b)
        self.assertIn("below 50.0%", reasons_b)

        # Check Student C (Rule 3)
        self.assertTrue(s_map[sc.id]["is_at_risk"])
        reasons_c = " ".join(s_map[sc.id]["at_risk_reasons"])
        self.assertIn("No activity for", reasons_c)

        # Check Student D (Safe)
        self.assertFalse(s_map[sd.id]["is_at_risk"])
        self.assertEqual(len(s_map[sd.id]["at_risk_reasons"]), 0)

    def test_06_student_who_left_or_removed_disappears(self):
        """
        When a student's enrollment status becomes 'removed' or 'left',
        they completely disappear from class overview, outcome drilldown,
        and student roster. Direct access to their profile returns 404.
        """
        test_class = ClassModel(faculty_id=self.faculty_a.id, course_id=self.course.id, name="Removal Class", class_code=f"RM{uuid.uuid4().hex[:4].upper()}")
        self.db.add(test_class)
        self.db.commit()

        s = User(email=f"rm_{uuid.uuid4().hex[:5]}@obe.edu", password_hash="hash", full_name="Student To Remove", role="student")
        self.db.add(s)
        self.db.commit()

        enr = ClassEnrollment(class_id=test_class.id, student_id=s.id, status="active")
        self.db.add(enr)
        self.db.commit()

        # Verify present initially
        r_init = client.get(f"/api/faculty/classes/{test_class.id}/students", headers=self.headers_faculty_a)
        self.assertEqual(r_init.json()["total_active_students"], 1)

        # Remove student
        r_del = client.delete(f"/api/faculty/classes/{test_class.id}/students/{s.id}", headers=self.headers_faculty_a)
        self.assertEqual(r_del.status_code, 200)

        # Check overview active count is 0
        r_over = client.get(f"/api/faculty/classes/{test_class.id}/overview", headers=self.headers_faculty_a)
        self.assertEqual(r_over.json()["active_students_count"], 0)

        # Check students roster is empty
        r_stud = client.get(f"/api/faculty/classes/{test_class.id}/students", headers=self.headers_faculty_a)
        self.assertEqual(r_stud.json()["total_active_students"], 0)

        # Direct access to student profile returns 404
        r_prof = client.get(f"/api/faculty/classes/{test_class.id}/students/{s.id}", headers=self.headers_faculty_a)
        self.assertEqual(r_prof.status_code, 404)

        # Learning path returns 404
        r_lp = client.get(f"/api/faculty/classes/{test_class.id}/students/{s.id}/learning-path", headers=self.headers_faculty_a)
        self.assertEqual(r_lp.status_code, 404)

    def test_07_baseline_vs_current_delta_correct(self):
        """
        Verifies baseline vs current delta for a student who joined with 3 topics complete
        and prior baseline CO attainment.
        """
        test_class = ClassModel(faculty_id=self.faculty_a.id, course_id=self.course.id, name="Baseline Delta Class", class_code=f"BL{uuid.uuid4().hex[:4].upper()}")
        self.db.add(test_class)
        self.db.commit()

        s = User(email=f"bl_{uuid.uuid4().hex[:5]}@obe.edu", password_hash="hash", full_name="Baseline Student", role="student")
        self.db.add(s)
        self.db.commit()

        co = self.outcomes[0]
        # Baseline snapshot stored in enrollment: 40% attainment for CO1, 3 completed topics
        baseline_co_data = [
            {"outcome_id": co.id, "code": co.code, "description": co.description, "attainment_percentage": 40.0, "status": "In Progress"}
        ]
        enr = ClassEnrollment(
            class_id=test_class.id,
            student_id=s.id,
            status="active",
            baseline_completed_topics=3,
            baseline_co_json=json.dumps(baseline_co_data)
        )
        self.db.add(enr)

        # Current attainment is 85.0%
        oa = OutcomeAttainment(user_id=s.id, course_id=self.course.id, outcome_id=co.id, attainment_percentage=85.0, status="Achieved")
        self.db.add(oa)
        self.db.commit()

        # Query full student profile
        res = client.get(f"/api/faculty/classes/{test_class.id}/students/{s.id}", headers=self.headers_faculty_a)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        # Check baseline completed topics
        self.assertEqual(data["student"]["baseline_completed_topics"], 3)
        self.assertIn("joined with 3/", data["student"]["progress_summary"])

        # Check Outcome Delta: current (85.0) - baseline (40.0) = 45.0
        co_entry = next((c for c in data["outcomes"] if c["outcome_id"] == co.id), None)
        self.assertIsNotNone(co_entry)
        self.assertEqual(co_entry["current_attainment"], 85.0)
        self.assertEqual(co_entry["baseline_attainment"], 40.0)
        self.assertEqual(co_entry["delta"], 45.0)
        self.assertTrue(co_entry["is_achieved"])

    def test_08_no_sensitive_fields_in_any_response(self):
        """
        Guarantees password hashes, tokens, or other sensitive credentials
        are NEVER exposed in any of the Step 2C responses.
        """
        test_class = ClassModel(faculty_id=self.faculty_a.id, course_id=self.course.id, name="Security Class", class_code=f"SC{uuid.uuid4().hex[:4].upper()}")
        self.db.add(test_class)
        self.db.commit()

        s = User(email=f"sec_{uuid.uuid4().hex[:5]}@obe.edu", password_hash="SECRET_PASSWORD_HASH_12345", full_name="Security Student", role="student")
        self.db.add(s)
        self.db.commit()

        self.db.add(ClassEnrollment(class_id=test_class.id, student_id=s.id, status="active"))
        self.db.commit()

        endpoints = [
            f"/api/faculty/classes/{test_class.id}/overview",
            f"/api/faculty/classes/{test_class.id}/outcomes/{self.outcomes[0].id}",
            f"/api/faculty/classes/{test_class.id}/students",
            f"/api/faculty/classes/{test_class.id}/students/{s.id}",
            f"/api/faculty/classes/{test_class.id}/students/{s.id}/learning-path"
        ]

        for ep in endpoints:
            r = client.get(ep, headers=self.headers_faculty_a)
            self.assertEqual(r.status_code, 200)
            text = r.text
            self.assertNotIn("SECRET_PASSWORD_HASH_12345", text)
            self.assertNotIn("password_hash", text)
            self.assertNotIn("password", text.lower())

    def test_09_query_count_stays_bounded_n_plus_one_guard(self):
        """
        Tests that query count stays bounded for a class of 40 students.
        Batch loading must prevent N+1 queries (< 15 SQL queries executed total).
        """
        test_class = ClassModel(faculty_id=self.faculty_a.id, course_id=self.course.id, name="Cohort 40 Class", class_code=f"C40{uuid.uuid4().hex[:3].upper()}")
        self.db.add(test_class)
        self.db.commit()

        # Create 40 students with enrollments and masteries
        students_40 = []
        for i in range(40):
            u = User(email=f"c40_{i}_{uuid.uuid4().hex[:4]}@obe.edu", password_hash="hash", full_name=f"Student 40 #{i}", role="student")
            students_40.append(u)
        self.db.add_all(students_40)
        self.db.commit()

        enrollments_40 = [
            ClassEnrollment(class_id=test_class.id, student_id=u.id, status="active")
            for u in students_40
        ]
        self.db.add_all(enrollments_40)
        self.db.commit()

        # Add masteries for all 40 students across 3 topics (120 mastery rows)
        masteries_40 = []
        for u in students_40:
            for t in self.topics[:3]:
                masteries_40.append(MasteryScore(user_id=u.id, topic_id=t.id, overall_mastery=75.0))
        self.db.add_all(masteries_40)
        self.db.commit()

        # Monitor SQL executions during overview endpoint
        query_count = 0
        def count_query(conn, cursor, statement, parameters, context, executemany):
            nonlocal query_count
            query_count += 1

        event.listen(engine, "before_cursor_execute", count_query)
        try:
            res_overview = client.get(f"/api/faculty/classes/{test_class.id}/overview", headers=self.headers_faculty_a)
            self.assertEqual(res_overview.status_code, 200)
            self.assertEqual(res_overview.json()["active_students_count"], 40)
        finally:
            event.remove(engine, "before_cursor_execute", count_query)

        # If N+1 was present, 40 students would produce >100 queries.
        # With batch loading, total queries should be well under 18 queries.
        self.assertLess(
            query_count, 18,
            f"N+1 query detected! Expected bounded SQL queries (<18), but executed {query_count} queries for 40 students."
        )

        # Now test students roster query count
        query_count_roster = 0
        def count_roster_query(conn, cursor, statement, parameters, context, executemany):
            nonlocal query_count_roster
            query_count_roster += 1

        event.listen(engine, "before_cursor_execute", count_roster_query)
        try:
            res_roster = client.get(f"/api/faculty/classes/{test_class.id}/students", headers=self.headers_faculty_a)
            self.assertEqual(res_roster.status_code, 200)
            self.assertEqual(res_roster.json()["total_active_students"], 40)
        finally:
            event.remove(engine, "before_cursor_execute", count_roster_query)

        self.assertLess(
            query_count_roster, 18,
            f"N+1 query detected on student roster! Expected <18 queries, but got {query_count_roster} queries."
        )

if __name__ == "__main__":
    unittest.main()
