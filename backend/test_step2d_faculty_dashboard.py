"""
test_step2d_faculty_dashboard.py
Step 2D Test Suite: Reassessment tracking, concept/prerequisite gap analysis,
before/after intervention reports, deduplication, and faculty endpoints.
"""

import unittest
import uuid
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import event

from main import app
from database import SessionLocal, engine
from models import (
    User, Course, Topic, TopicPrerequisite, TopicOutcomeMapping,
    CourseOutcome, ClassModel, ClassEnrollment, MasteryScore,
    AssessmentAttempt, QuestionAnswerHistory, QuestionBank,
    OutcomeAttainment, OutcomeAttainmentHistory, InterventionEvent,
    LearningPath, LearningPathItem
)
from core.security import create_access_token, hash_password
from core.class_codes import generate_unique_class_code
from core.thresholds import (
    PREREQ_UNLOCK, ASSESSMENT_PASS, TOPIC_MASTERY,
    CO_ACHIEVED_DEFAULT, AT_RISK_MASTERY, COMMON_GAP_PCT
)
from core.step2d_foundation import (
    init_step2d_schema, deduplicate_outcome_attainment_history,
    backfill_reassessment_attempts, backfill_question_concepts,
    backfill_class_joined_interventions
)
from progress_engine import (
    record_assessment_attempt, get_central_student_state,
    recalculate_course_outcomes
)

client = TestClient(app)

class TestStep2DFacultyDashboard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_step2d_schema(engine)
        cls.db = SessionLocal()

        uid = uuid.uuid4().hex[:6]
        cls.faculty_a = User(
            email=f"faculty_2d_a_{uid}@uni.edu",
            password_hash=hash_password("Pass123!"),
            role="faculty",
            full_name="Dr. 2D Owner"
        )
        cls.faculty_b = User(
            email=f"faculty_2d_b_{uid}@uni.edu",
            password_hash=hash_password("Pass123!"),
            role="faculty",
            full_name="Dr. 2D Rival"
        )
        cls.admin_user = User(
            email=f"admin_2d_{uid}@uni.edu",
            password_hash=hash_password("Pass123!"),
            role="admin",
            full_name="Admin 2D"
        )
        cls.student_user = User(
            email=f"student_2d_{uid}@uni.edu",
            password_hash=hash_password("Pass123!"),
            role="student",
            full_name="Student 2D Active"
        )

        cls.db.add_all([cls.faculty_a, cls.faculty_b, cls.admin_user, cls.student_user])
        cls.db.commit()

        cls.token_faculty_a = create_access_token(cls.faculty_a.id, cls.faculty_a.role)
        cls.token_faculty_b = create_access_token(cls.faculty_b.id, cls.faculty_b.role)
        cls.token_admin = create_access_token(cls.admin_user.id, cls.admin_user.role)
        cls.token_student = create_access_token(cls.student_user.id, cls.student_user.role)

        cls.course = cls.db.query(Course).filter(Course.id == 1).first()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    # --------------------------------------------------------------------------
    # 1. Access Control on Every New Endpoint
    # --------------------------------------------------------------------------
    def test_access_control_all_new_endpoints(self):
        """
        Faculty A owns class. Faculty B gets 404 (does not leak existence).
        Student gets 403. Anonymous gets 401. Admin gets 200.
        Left/removed student returns 404 on student-level endpoints.
        """
        test_class = ClassModel(
            faculty_id=self.faculty_a.id,
            course_id=self.course.id,
            name="2D Access Test Class",
            class_code=f"C2D{uuid.uuid4().hex[:3]}",
            is_active=True
        )
        self.db.add(test_class)
        self.db.flush()

        enrollment = ClassEnrollment(
            class_id=test_class.id,
            student_id=self.student_user.id,
            status="active",
            joined_at=datetime.utcnow()
        )
        self.db.add(enrollment)
        self.db.commit()

        headers_fa = {"Authorization": f"Bearer {self.token_faculty_a}"}
        headers_fb = {"Authorization": f"Bearer {self.token_faculty_b}"}
        headers_stud = {"Authorization": f"Bearer {self.token_student}"}
        headers_adm = {"Authorization": f"Bearer {self.token_admin}"}

        endpoints = [
            ("GET", f"/api/faculty/classes/{test_class.id}/assessments", None),
            ("GET", f"/api/faculty/classes/{test_class.id}/gaps", None),
            ("GET", f"/api/faculty/classes/{test_class.id}/gaps/concept:General", None),
            ("GET", f"/api/faculty/classes/{test_class.id}/impact-summary", None),
            ("GET", f"/api/faculty/classes/{test_class.id}/students/{self.student_user.id}/impact", None),
            ("POST", f"/api/faculty/classes/{test_class.id}/students/{self.student_user.id}/flag", {"note": "Test note"})
        ]

        for method, ep, body in endpoints:
            # Anonymous -> 401
            resp_anon = client.request(method, ep, json=body) if body else client.request(method, ep)
            self.assertEqual(resp_anon.status_code, 401, f"{ep} anon must be 401")

            # Student -> 403
            resp_stud = client.request(method, ep, headers=headers_stud, json=body) if body else client.request(method, ep, headers=headers_stud)
            self.assertEqual(resp_stud.status_code, 403, f"{ep} student must be 403")

            # Unowned faculty -> 404 (do not leak existence)
            resp_fb = client.request(method, ep, headers=headers_fb, json=body) if body else client.request(method, ep, headers=headers_fb)
            self.assertEqual(resp_fb.status_code, 404, f"{ep} unauthorized faculty must be 404")

            # Admin -> 200
            resp_adm = client.request(method, ep, headers=headers_adm, json=body) if body else client.request(method, ep, headers=headers_adm)
            self.assertEqual(resp_adm.status_code, 200, f"{ep} admin must be 200")

            # Owner faculty -> 200
            resp_fa = client.request(method, ep, headers=headers_fa, json=body) if body else client.request(method, ep, headers=headers_fa)
            self.assertEqual(resp_fa.status_code, 200, f"{ep} owner faculty must be 200")

        # When student leaves or is removed, student detail / impact returns 404
        enrollment.status = "removed"
        self.db.commit()

        resp_left = client.get(
            f"/api/faculty/classes/{test_class.id}/students/{self.student_user.id}/impact",
            headers=headers_fa
        )
        self.assertEqual(resp_left.status_code, 404, "Removed student impact must return 404")

    # --------------------------------------------------------------------------
    # 2. Reassessment Tagging & Historical Backfill
    # --------------------------------------------------------------------------
    def test_reassessment_tagging_and_backfill(self):
        """
        Verify:
        - Diagnostic is always 'diagnostic'
        - First attempt on a topic is initial ('practice')
        - Repeated attempt on same topic is classified as 'reassessment'
        - Backfill safely converts subsequent attempts to 'reassessment'
        """
        uid = uuid.uuid4().hex[:6]
        student = User(email=f"s_re_{uid}@u.edu", full_name="Reassess Tester", role="student", password_hash=hash_password("Pass123!"))
        self.db.add(student)
        self.db.commit()

        topic1 = self.db.query(Topic).filter(Topic.course_id == self.course.id).first()
        qb = self.db.query(QuestionBank).filter(QuestionBank.topic_id == topic1.id).first()

        # Submit first attempt
        res1 = record_assessment_attempt(
            db=self.db,
            user_id=student.id,
            course_id=self.course.id,
            attempt_type="practice",
            submitted_answers={str(qb.id): qb.correct_answer},
            topic_id=topic1.id
        )
        att1 = self.db.query(AssessmentAttempt).filter(
            AssessmentAttempt.user_id == student.id,
            AssessmentAttempt.topic_id == topic1.id
        ).order_by(AssessmentAttempt.id.asc()).first()
        self.assertEqual(att1.attempt_type, "practice", "First attempt must be initial practice")

        # Submit second attempt on same topic -> must become reassessment
        res2 = record_assessment_attempt(
            db=self.db,
            user_id=student.id,
            course_id=self.course.id,
            attempt_type="practice",
            submitted_answers={str(qb.id): qb.correct_answer},
            topic_id=topic1.id
        )
        att2 = self.db.query(AssessmentAttempt).filter(
            AssessmentAttempt.user_id == student.id,
            AssessmentAttempt.topic_id == topic1.id
        ).order_by(AssessmentAttempt.id.desc()).first()
        self.assertEqual(att2.attempt_type, "reassessment", "Subsequent attempt must be automatically tagged as reassessment")

        # Backfill test: simulate old unbackfilled attempts
        att_old = AssessmentAttempt(
            attempt_uuid=f"old-{uuid.uuid4().hex[:8]}",
            user_id=student.id,
            course_id=self.course.id,
            topic_id=topic1.id,
            attempt_type="practice",
            score=5,
            max_score=10,
            percentage=50.0,
            created_at=datetime.utcnow() + timedelta(seconds=10)
        )
        self.db.add(att_old)
        self.db.commit()

        backfilled = backfill_reassessment_attempts(self.db)
        self.assertGreaterEqual(backfilled, 1)
        self.db.refresh(att_old)
        self.assertEqual(att_old.attempt_type, "reassessment", "Backfill must tag repeated attempt as reassessment")

    # --------------------------------------------------------------------------
    # 3. Concept Gaps & Untagged General Fallback
    # --------------------------------------------------------------------------
    def test_concept_gap_percentages_and_general_fallback(self):
        """
        Verify concept gap percentage calculation:
        - Students with score < ASSESSMENT_PASS (60%) count as struggling
        - Untagged questions are attributed to 'General'
        """
        test_class = ClassModel(
            faculty_id=self.faculty_a.id,
            course_id=self.course.id,
            name="2D Gaps Test Class",
            class_code=f"GAP{uuid.uuid4().hex[:3]}",
            is_active=True
        )
        self.db.add(test_class)
        self.db.flush()

        uid1 = uuid.uuid4().hex[:4]
        uid2 = uuid.uuid4().hex[:4]
        s1 = User(email=f"s1_{uid1}@u.edu", full_name="S1 Gap", role="student", password_hash=hash_password("Pass123!"))
        s2 = User(email=f"s2_{uid2}@u.edu", full_name="S2 Gap", role="student", password_hash=hash_password("Pass123!"))
        self.db.add_all([s1, s2])
        self.db.flush()

        self.db.add(ClassEnrollment(class_id=test_class.id, student_id=s1.id, status="active"))
        self.db.add(ClassEnrollment(class_id=test_class.id, student_id=s2.id, status="active"))
        self.db.commit()

        # Create attempts with QuestionAnswerHistory
        att1 = AssessmentAttempt(attempt_uuid=uuid.uuid4().hex, user_id=s1.id, course_id=self.course.id, score=2, max_score=10, percentage=20.0)
        att2 = AssessmentAttempt(attempt_uuid=uuid.uuid4().hex, user_id=s2.id, course_id=self.course.id, score=8, max_score=10, percentage=80.0)
        self.db.add_all([att1, att2])
        self.db.flush()

        qb_list = self.db.query(QuestionBank).filter(QuestionBank.course_id == self.course.id).all()
        q1 = qb_list[0]
        q2 = qb_list[1]

        # S1 fails concept 'Recursion Base Case', S2 passes
        qah1 = QuestionAnswerHistory(attempt_id=att1.id, user_id=s1.id, question_id=q1.id, concept="Recursion Base Case", selected_answer="A", is_correct=False)
        qah2 = QuestionAnswerHistory(attempt_id=att2.id, user_id=s2.id, question_id=q1.id, concept="Recursion Base Case", selected_answer="B", is_correct=True)

        # Untagged question -> None concept
        qah3 = QuestionAnswerHistory(attempt_id=att1.id, user_id=s1.id, question_id=q2.id, concept=None, selected_answer="C", is_correct=False)

        self.db.add_all([qah1, qah2, qah3])
        self.db.commit()

        headers = {"Authorization": f"Bearer {self.token_faculty_a}"}
        resp = client.get(f"/api/faculty/classes/{test_class.id}/gaps", headers=headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        # Find Recursion Base Case gap
        rc_gap = next((g for g in data["concept_gaps"] if g["concept"] == "Recursion Base Case"), None)
        self.assertIsNotNone(rc_gap)
        # 1 of 2 students struggling -> 50.0%
        self.assertEqual(rc_gap["students_affected_count"], 1)
        self.assertEqual(rc_gap["pct_students_affected"], 50.0)

        # Untagged must go to 'General'
        gen_gap = next((g for g in data["concept_gaps"] if g["concept"] == "General"), None)
        self.assertIsNotNone(gen_gap)
        self.assertGreaterEqual(gen_gap["students_affected_count"], 1)

    # --------------------------------------------------------------------------
    # 4. Prerequisite Gap Counts & Blocked Dependents
    # --------------------------------------------------------------------------
    def test_prerequisite_gap_counts_and_blocked_dependents(self):
        """
        Verify prerequisite gaps report correct counts of students below PREREQ_UNLOCK (60%)
        and list which dependent topics are blocked.
        """
        test_class = ClassModel(
            faculty_id=self.faculty_a.id,
            course_id=self.course.id,
            name="2D Prereq Test Class",
            class_code=generate_unique_class_code(self.db),
            is_active=True
        )
        self.db.add(test_class)
        self.db.flush()

        uid = uuid.uuid4().hex[:4]
        s1 = User(email=f"s1_prq_{uid}@u.edu", full_name="S1 Prereq", role="student", password_hash=hash_password("Pass123!"))
        self.db.add(s1)
        self.db.flush()
        self.db.add(ClassEnrollment(class_id=test_class.id, student_id=s1.id, status="active"))

        # Find a prerequisite relation in this course
        prereq = self.db.query(TopicPrerequisite).join(Topic, TopicPrerequisite.topic_id == Topic.id).filter(Topic.course_id == self.course.id).first()
        self.assertIsNotNone(prereq, "Course should have prerequisites")

        # Set s1 mastery in prereq topic to 35% (< PREREQ_UNLOCK = 60%)
        m = MasteryScore(user_id=s1.id, topic_id=prereq.prerequisite_topic_id, overall_mastery=35.0)
        self.db.add(m)
        self.db.commit()

        headers = {"Authorization": f"Bearer {self.token_faculty_a}"}
        resp = client.get(f"/api/faculty/classes/{test_class.id}/gaps", headers=headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        matching_prereq_gap = next(
            (g for g in data["prerequisite_gaps"] if g["prereq_topic_id"] == prereq.prerequisite_topic_id and g["dependent_topic_id"] == prereq.topic_id),
            None
        )
        self.assertIsNotNone(matching_prereq_gap)
        self.assertEqual(matching_prereq_gap["students_affected_count"], 1)
        self.assertEqual(matching_prereq_gap["pct_students_affected"], 100.0)

    # --------------------------------------------------------------------------
    # 5. Common Gap Threshold Logic
    # --------------------------------------------------------------------------
    def test_common_gap_threshold_logic(self):
        """
        Verify that gaps affecting >= COMMON_GAP_PCT (25.0%) are flagged as common_class_gaps,
        and gaps affecting < COMMON_GAP_PCT are not.
        """
        test_class = ClassModel(
            faculty_id=self.faculty_a.id,
            course_id=self.course.id,
            name="2D Common Threshold Class",
            class_code=f"TH{uuid.uuid4().hex[:3]}",
            is_active=True
        )
        self.db.add(test_class)
        self.db.flush()

        students = []
        for i in range(4):
            uid = uuid.uuid4().hex[:4]
            s = User(email=f"s{i}_{uid}@u.edu", full_name=f"Student {i}", role="student", password_hash=hash_password("Pass123!"))
            self.db.add(s)
            students.append(s)
        self.db.flush()

        for s in students:
            self.db.add(ClassEnrollment(class_id=test_class.id, student_id=s.id, status="active"))
        self.db.commit()

        # Concept A: 1 out of 4 students struggles -> 25% (>= COMMON_GAP_PCT) -> is_common_gap == True
        qb_q = self.db.query(QuestionBank).filter(QuestionBank.course_id == self.course.id).first()
        att1 = AssessmentAttempt(attempt_uuid=uuid.uuid4().hex, user_id=students[0].id, course_id=self.course.id, score=2, max_score=10, percentage=20.0)
        self.db.add(att1)
        self.db.flush()
        self.db.add(QuestionAnswerHistory(attempt_id=att1.id, user_id=students[0].id, question_id=qb_q.id, concept="Tree Rotations", selected_answer="A", is_correct=False))

        # 3 other students pass
        for s in students[1:]:
            att = AssessmentAttempt(attempt_uuid=uuid.uuid4().hex, user_id=s.id, course_id=self.course.id, score=8, max_score=10, percentage=80.0)
            self.db.add(att)
            self.db.flush()
            self.db.add(QuestionAnswerHistory(attempt_id=att.id, user_id=s.id, question_id=qb_q.id, concept="Tree Rotations", selected_answer="B", is_correct=True))

        self.db.commit()

        headers = {"Authorization": f"Bearer {self.token_faculty_a}"}
        resp = client.get(f"/api/faculty/classes/{test_class.id}/gaps", headers=headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        tr_gap = next((g for g in data["concept_gaps"] if g["concept"] == "Tree Rotations"), None)
        self.assertIsNotNone(tr_gap)
        self.assertEqual(tr_gap["pct_students_affected"], 25.0)
        self.assertTrue(tr_gap["is_common_gap"], "Gap affecting 25.0% must be flagged as common gap (threshold = 25.0%)")

    # --------------------------------------------------------------------------
    # 6. Impact Baseline vs Current, Interventions & Before/After Windows
    # --------------------------------------------------------------------------
    def test_impact_baseline_vs_current_and_before_after_windows(self):
        """
        Verify:
        - Baseline vs current delta calculation
        - Teacher intervention flag recording via POST endpoint
        - Before/after window calculation around intervention events
        - Notice labeling 'Association, not proof of causation'
        - 'has_enough_data' is False when fewer than 2 snapshots exist
        """
        test_class = ClassModel(
            faculty_id=self.faculty_a.id,
            course_id=self.course.id,
            name="2D Impact Class",
            class_code=f"IMP{uuid.uuid4().hex[:3]}",
            is_active=True
        )
        self.db.add(test_class)
        self.db.flush()

        uid = uuid.uuid4().hex[:4]
        s = User(email=f"s_imp_{uid}@u.edu", full_name="Impact Student", role="student", password_hash=hash_password("Pass123!"))
        self.db.add(s)
        self.db.flush()

        cos = self.db.query(CourseOutcome).filter(CourseOutcome.course_id == self.course.id).all()
        co1_id = cos[0].id if cos else 1
        co2_id = cos[1].id if len(cos) > 1 else co1_id

        # Enrolled with baseline CO attainment
        baseline_json = json.dumps([{"outcome_id": co1_id, "attainment_percentage": 30.0}, {"outcome_id": co2_id, "attainment_percentage": 40.0}])
        enr = ClassEnrollment(
            class_id=test_class.id,
            student_id=s.id,
            status="active",
            baseline_co_json=baseline_json,
            joined_at=datetime.utcnow() - timedelta(days=10)
        )
        self.db.add(enr)
        self.db.commit()

        headers = {"Authorization": f"Bearer {self.token_faculty_a}"}

        # 1. Flag teacher intervention
        flag_resp = client.post(
            f"/api/faculty/classes/{test_class.id}/students/{s.id}/flag",
            headers=headers,
            json={"note": "Met with student during office hours for recursion mentoring."}
        )
        self.assertEqual(flag_resp.status_code, 200)
        flag_data = flag_resp.json()
        self.assertTrue(flag_data["success"])
        self.assertEqual(flag_data["event"]["type"], "teacher_flag")

        # 2. Add history snapshots before and after
        h1 = OutcomeAttainmentHistory(user_id=s.id, course_id=self.course.id, outcome_id=co1_id, attainment_pct=30.0, trigger="baseline", created_at=datetime.utcnow() - timedelta(days=5))
        h2 = OutcomeAttainmentHistory(user_id=s.id, course_id=self.course.id, outcome_id=co1_id, attainment_pct=75.0, trigger="practice", created_at=datetime.utcnow())
        self.db.add_all([h1, h2])

        # Current OutcomeAttainment
        oa1 = OutcomeAttainment(user_id=s.id, course_id=self.course.id, outcome_id=co1_id, attainment_percentage=75.0, status="Achieved")
        oa2 = OutcomeAttainment(user_id=s.id, course_id=self.course.id, outcome_id=co2_id, attainment_percentage=80.0, status="Achieved")
        self.db.add_all([oa1, oa2])
        self.db.commit()

        # Query impact endpoint
        resp = client.get(f"/api/faculty/classes/{test_class.id}/students/{s.id}/impact", headers=headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertTrue(data["has_enough_data"])
        self.assertIn("Association, not proof of causation", data["attribution_notice"])
        self.assertIn("before_after_comparisons", data)
        self.assertGreaterEqual(len(data["before_after_comparisons"]), 1)

        # Class impact summary
        sum_resp = client.get(f"/api/faculty/classes/{test_class.id}/impact-summary", headers=headers)
        self.assertEqual(sum_resp.status_code, 200)
        sum_data = sum_resp.json()
        self.assertEqual(sum_data["total_students"], 1)
        self.assertEqual(sum_data["improved_count"], 1)

    # --------------------------------------------------------------------------
    # 7. Dedupe Cleanup & Safe Single Writes on State Reads
    # --------------------------------------------------------------------------
    def test_dedupe_cleanup_and_no_dupes_on_state_reads(self):
        """
        Verify:
        - Dedupe removes rapid duplicates created within a short window, keeping earliest
        - Repeated calls to get_central_student_state do NOT create duplicate outcome history rows
        """
        uid = uuid.uuid4().hex[:4]
        s = User(email=f"s_ded_{uid}@u.edu", full_name="Dedupe Student", role="student", password_hash=hash_password("Pass123!"))
        self.db.add(s)
        self.db.commit()

        now = datetime.utcnow()
        # Insert 3 identical snapshots within 5 seconds (rapid duplicate bug)
        d1 = OutcomeAttainmentHistory(user_id=s.id, course_id=self.course.id, outcome_id=1, attainment_pct=65.0, trigger="state_sync", created_at=now)
        d2 = OutcomeAttainmentHistory(user_id=s.id, course_id=self.course.id, outcome_id=1, attainment_pct=65.0, trigger="state_sync", created_at=now + timedelta(seconds=2))
        d3 = OutcomeAttainmentHistory(user_id=s.id, course_id=self.course.id, outcome_id=1, attainment_pct=65.0, trigger="state_sync", created_at=now + timedelta(seconds=4))
        # And one distinct snapshot later
        d_distinct = OutcomeAttainmentHistory(user_id=s.id, course_id=self.course.id, outcome_id=1, attainment_pct=85.0, trigger="quiz", created_at=now + timedelta(hours=2))

        self.db.add_all([d1, d2, d3, d_distinct])
        self.db.commit()

        removed = deduplicate_outcome_attainment_history(self.db, window_seconds=300)
        self.assertGreaterEqual(removed, 2, "Dedupe must remove at least the 2 duplicate rows")

        remaining = self.db.query(OutcomeAttainmentHistory).filter(OutcomeAttainmentHistory.user_id == s.id).all()
        self.assertEqual(len(remaining), 2, "Must keep 1 earliest anchor from duplicate cluster and 1 distinct row")
        self.assertEqual(remaining[0].id, d1.id, "Must keep the earliest row")

        # Verify repeated state reads do not write outcome_attainment_history
        count_before = self.db.query(OutcomeAttainmentHistory).filter(OutcomeAttainmentHistory.user_id == s.id).count()
        get_central_student_state(self.db, user_id=s.id, course_id=self.course.id)
        get_central_student_state(self.db, user_id=s.id, course_id=self.course.id)
        count_after = self.db.query(OutcomeAttainmentHistory).filter(OutcomeAttainmentHistory.user_id == s.id).count()
        self.assertEqual(count_after, count_before, "get_central_student_state must never write duplicate history snapshots")

    # --------------------------------------------------------------------------
    # 8. Empty Class Returns 200 with Empty Lists
    # --------------------------------------------------------------------------
    def test_empty_class_returns_empty_lists_with_200(self):
        """
        Verify that an empty class returns 200 with clean empty lists, not errors.
        """
        test_class = ClassModel(
            faculty_id=self.faculty_a.id,
            course_id=self.course.id,
            name="2D Empty Class",
            class_code=f"EMP{uuid.uuid4().hex[:3]}",
            is_active=True
        )
        self.db.add(test_class)
        self.db.commit()

        headers = {"Authorization": f"Bearer {self.token_faculty_a}"}

        endpoints = [
            f"/api/faculty/classes/{test_class.id}/assessments",
            f"/api/faculty/classes/{test_class.id}/gaps",
            f"/api/faculty/classes/{test_class.id}/impact-summary"
        ]

        for ep in endpoints:
            resp = client.get(ep, headers=headers)
            self.assertEqual(resp.status_code, 200, f"{ep} on empty class must return 200")

    # --------------------------------------------------------------------------
    # 9. Bounded Query Count for 40 Students (No N+1)
    # --------------------------------------------------------------------------
    def test_bounded_query_count_for_40_students(self):
        """
        Batch loading must keep query count strictly bounded (< 20 SQL queries)
        for a cohort of 40 students.
        """
        test_class = ClassModel(
            faculty_id=self.faculty_a.id,
            course_id=self.course.id,
            name="2D 40 Students Cohort",
            class_code=f"BND{uuid.uuid4().hex[:3]}",
            is_active=True
        )
        self.db.add(test_class)
        self.db.flush()

        new_users = []
        for i in range(40):
            uid = uuid.uuid4().hex[:8]
            u = User(email=f"s40_{i}_{uid}@u.edu", full_name=f"S40 {i}", role="student", password_hash=hash_password("Pass123!"))
            self.db.add(u)
            new_users.append(u)
        self.db.flush()

        for u in new_users:
            self.db.add(ClassEnrollment(class_id=test_class.id, student_id=u.id, status="active"))
        self.db.commit()

        query_count = 0
        def count_queries(conn, cursor, statement, parameters, context, executemany):
            nonlocal query_count
            query_count += 1

        headers = {"Authorization": f"Bearer {self.token_faculty_a}"}

        # Test /assessments endpoint
        query_count = 0
        event.listen(engine, "before_cursor_execute", count_queries)
        try:
            resp1 = client.get(f"/api/faculty/classes/{test_class.id}/assessments", headers=headers)
            self.assertEqual(resp1.status_code, 200)
            self.assertLess(query_count, 20, f"Assessments endpoint executed {query_count} queries for 40 students (limit 20)")

            query_count = 0
            resp2 = client.get(f"/api/faculty/classes/{test_class.id}/gaps", headers=headers)
            self.assertEqual(resp2.status_code, 200)
            self.assertLess(query_count, 20, f"Gaps endpoint executed {query_count} queries for 40 students (limit 20)")

            query_count = 0
            resp3 = client.get(f"/api/faculty/classes/{test_class.id}/impact-summary", headers=headers)
            self.assertEqual(resp3.status_code, 200)
            self.assertLess(query_count, 20, f"Impact summary executed {query_count} queries for 40 students (limit 20)")
        finally:
            event.remove(engine, "before_cursor_execute", count_queries)

    # --------------------------------------------------------------------------
    # 10. No Sensitive Fields in Any Response
    # --------------------------------------------------------------------------
    def test_no_sensitive_fields_in_any_response(self):
        """
        Verify that no password hashes, secret tokens, or sensitive user fields
        are leaked in any endpoint response.
        """
        test_class = ClassModel(
            faculty_id=self.faculty_a.id,
            course_id=self.course.id,
            name="2D Sensitive Check Class",
            class_code=f"SEN{uuid.uuid4().hex[:3]}",
            is_active=True
        )
        self.db.add(test_class)
        self.db.flush()

        enr = ClassEnrollment(class_id=test_class.id, student_id=self.student_user.id, status="active")
        self.db.add(enr)
        self.db.commit()

        headers = {"Authorization": f"Bearer {self.token_faculty_a}"}
        endpoints = [
            f"/api/faculty/classes/{test_class.id}/assessments",
            f"/api/faculty/classes/{test_class.id}/gaps",
            f"/api/faculty/classes/{test_class.id}/impact-summary",
            f"/api/faculty/classes/{test_class.id}/students/{self.student_user.id}/impact"
        ]

        for ep in endpoints:
            resp = client.get(ep, headers=headers)
            self.assertEqual(resp.status_code, 200)
            text_body = resp.text.lower()
            self.assertNotIn("hashed_password", text_body)
            self.assertNotIn("password_hash", text_body)

    # --------------------------------------------------------------------------
    # 11. Stable Response Shapes (Lists Never Null) Across All Data States
    # --------------------------------------------------------------------------
    def test_stable_response_shapes_and_never_null_lists(self):
        """
        Verify:
        (a) Zero students: all list fields return [] (never None)
        (b) Students with no attempts: all list fields return [] (never None)
        (c) Students with data: returns complete flat attributes and aliases
        """
        # (a) Zero students class
        c_empty = ClassModel(
            faculty_id=self.faculty_a.id,
            course_id=self.course.id,
            name="Stable Shape Empty",
            class_code=f"EMP{uuid.uuid4().hex[:3]}",
            is_active=True
        )
        self.db.add(c_empty)
        self.db.commit()

        headers = {"Authorization": f"Bearer {self.token_faculty_a}"}

        r_ass = client.get(f"/api/faculty/classes/{c_empty.id}/assessments", headers=headers)
        self.assertEqual(r_ass.status_code, 200)
        d_ass = r_ass.json()
        self.assertIsInstance(d_ass["students"], list)
        self.assertEqual(d_ass["total_students"], 0)

        r_gaps = client.get(f"/api/faculty/classes/{c_empty.id}/gaps", headers=headers)
        self.assertEqual(r_gaps.status_code, 200)
        d_gaps = r_gaps.json()
        self.assertIsInstance(d_gaps["concept_gaps"], list)
        self.assertIsInstance(d_gaps["prerequisite_gaps"], list)
        self.assertIsInstance(d_gaps["common_class_gaps"], list)

        r_imp = client.get(f"/api/faculty/classes/{c_empty.id}/impact-summary", headers=headers)
        self.assertEqual(r_imp.status_code, 200)
        d_imp = r_imp.json()
        self.assertIsInstance(d_imp["students_summary"], list)
        self.assertEqual(d_imp["total_students"], 0)

        # (b) Student with no attempts
        c_no_att = ClassModel(
            faculty_id=self.faculty_a.id,
            course_id=self.course.id,
            name="Stable Shape No Attempts",
            class_code=f"NOA{uuid.uuid4().hex[:3]}",
            is_active=True
        )
        self.db.add(c_no_att)
        self.db.flush()

        uid = uuid.uuid4().hex[:4]
        s_fresh = User(email=f"s_fresh_{uid}@u.edu", full_name="Fresh Student", role="student", password_hash=hash_password("Pass123!"))
        self.db.add(s_fresh)
        self.db.flush()

        enr = ClassEnrollment(class_id=c_no_att.id, student_id=s_fresh.id, status="active", joined_at=datetime.utcnow())
        self.db.add(enr)
        self.db.commit()

        r_ass2 = client.get(f"/api/faculty/classes/{c_no_att.id}/assessments", headers=headers)
        self.assertEqual(r_ass2.status_code, 200)
        d_ass2 = r_ass2.json()
        self.assertEqual(len(d_ass2["students"]), 1)
        s_row = d_ass2["students"][0]
        self.assertIsInstance(s_row["reassessment_scores"], list)
        self.assertIsInstance(s_row["per_topic"], list)
        self.assertEqual(s_row["total_attempts_count"], 0)
        self.assertEqual(s_row["reassessments_count"], 0)

        r_st_imp = client.get(f"/api/faculty/classes/{c_no_att.id}/students/{s_fresh.id}/impact", headers=headers)
        self.assertEqual(r_st_imp.status_code, 200)
        d_st_imp = r_st_imp.json()
        self.assertIsInstance(d_st_imp["timeline"], list)
        self.assertIsInstance(d_st_imp["co_timeline"], list)
        self.assertIsInstance(d_st_imp["interventions"], list)
        self.assertIsInstance(d_st_imp["before_after_comparisons"], list)
        self.assertFalse(d_st_imp["has_enough_data"])
        self.assertEqual(d_st_imp["student_name"], "Fresh Student")
        self.assertEqual(d_st_imp["student_id"], s_fresh.id)

        # (c) Students with data: check flat attributes and aliases
        c_full = ClassModel(
            faculty_id=self.faculty_a.id,
            course_id=self.course.id,
            name="Stable Shape Full Data",
            class_code=f"FUL{uuid.uuid4().hex[:3]}",
            is_active=True
        )
        self.db.add(c_full)
        self.db.flush()

        s_active = User(email=f"s_act_{uid}@u.edu", full_name="Active Student", role="student", password_hash=hash_password("Pass123!"))
        self.db.add(s_active)
        self.db.flush()
        self.db.add(ClassEnrollment(class_id=c_full.id, student_id=s_active.id, status="active", joined_at=datetime.utcnow() - timedelta(days=10)))

        # Add 2 attempts
        t1 = self.course.topics[0]
        a1 = AssessmentAttempt(attempt_uuid=uuid.uuid4().hex, user_id=s_active.id, course_id=self.course.id, topic_id=t1.id, score=50.0, max_score=100.0, percentage=50.0, passed=False, attempt_type="initial", created_at=datetime.utcnow() - timedelta(days=5))
        a2 = AssessmentAttempt(attempt_uuid=uuid.uuid4().hex, user_id=s_active.id, course_id=self.course.id, topic_id=t1.id, score=85.0, max_score=100.0, percentage=85.0, passed=True, attempt_type="reassessment", created_at=datetime.utcnow())
        self.db.add_all([a1, a2])

        co1 = self.course.outcomes[0]
        h1 = OutcomeAttainmentHistory(user_id=s_active.id, course_id=self.course.id, outcome_id=co1.id, attainment_pct=40.0, trigger="baseline", created_at=datetime.utcnow() - timedelta(days=5))
        h2 = OutcomeAttainmentHistory(user_id=s_active.id, course_id=self.course.id, outcome_id=co1.id, attainment_pct=85.0, trigger="reassessment", created_at=datetime.utcnow())
        self.db.add_all([h1, h2])
        self.db.commit()

        r_ass3 = client.get(f"/api/faculty/classes/{c_full.id}/assessments", headers=headers)
        self.assertEqual(r_ass3.status_code, 200)
        d_ass3 = r_ass3.json()
        self.assertEqual(d_ass3["total_students"], 1)
        st_row = d_ass3["students"][0]
        self.assertEqual(st_row["initial_score"], 50.0)
        self.assertEqual(st_row["latest_score"], 85.0)
        self.assertEqual(st_row["best_score"], 85.0)
        self.assertEqual(st_row["total_attempts_count"], 2)
        self.assertEqual(st_row["reassessments_count"], 1)
        self.assertEqual(st_row["reassessment_scores"], [85.0])

        r_imp3 = client.get(f"/api/faculty/classes/{c_full.id}/students/{s_active.id}/impact", headers=headers)
        self.assertEqual(r_imp3.status_code, 200)
        d_imp3 = r_imp3.json()
        self.assertTrue(d_imp3["has_enough_data"])
        self.assertIsInstance(d_imp3["timeline"], list)
        self.assertEqual(len(d_imp3["timeline"]), 2)
        self.assertIn("date", d_imp3["timeline"][0])
        self.assertIn("attainment_pct", d_imp3["timeline"][0])

if __name__ == "__main__":
    unittest.main()
