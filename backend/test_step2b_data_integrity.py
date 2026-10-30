"""
test_step2b_data_integrity.py
Comprehensive test suite verifying all requirements of Step 2B:
Data Integrity, Security Fixes, Threshold Centralization, and Concurrency Protections.

Scenarios tested:
1. topic/complete on a LOCKED topic returns 403 and mastery is unchanged
2. topic/complete without a passed assessment returns 400
3. after a passed assessment, completion works; completing twice returns 409 with no duplicate history
4. a student cannot complete a topic for another user via any user_id parameter
5. weighted CO calculation gives the expected value (e.g. weights 1.0 and 2.0)
6. concurrent recalculation does not create duplicate OutcomeAttainment rows
7. diagnostic submit writes MasteryHistory and QuestionAnswerHistory
8. outcome_attainment_history gets a row per recalculation
9. compile-code with timeout_sec=999999 is capped; a malicious "call" expression returns 400
10. single source of truth for thresholds (grep test)
"""

import os
import re
import sys
import unittest
import uuid
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# Ensure backend directory is in sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
from models import (
    User, Course, Topic, MasteryScore, CourseOutcome,
    OutcomeAttainment, OutcomeAttainmentHistory, TopicOutcomeMapping,
    TopicPrerequisite, AssessmentAttempt, MasteryHistory,
    QuestionAnswerHistory, QuestionBank, StudentProfile
)
from core.security import create_access_token, hash_password
from core.thresholds import PREREQ_UNLOCK, ASSESSMENT_PASS, TOPIC_MASTERY, CO_ACHIEVED_DEFAULT
from progress_engine import recalculate_course_outcomes

client = TestClient(app)


class TestStep2BDataIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()

        # Create or fetch test users
        cls.student_a = cls.db.query(User).filter(User.email == "student_2b_a@obe.edu").first()
        if not cls.student_a:
            cls.student_a = User(
                email="student_2b_a@obe.edu",
                full_name="Student 2B A",
                role="student",
                password_hash=hash_password("demo123"),
            )
            cls.db.add(cls.student_a)
            cls.db.commit()
            cls.db.refresh(cls.student_a)

        cls.student_b = cls.db.query(User).filter(User.email == "student_2b_b@obe.edu").first()
        if not cls.student_b:
            cls.student_b = User(
                email="student_2b_b@obe.edu",
                full_name="Student 2B B",
                role="student",
                password_hash=hash_password("demo123"),
            )
            cls.db.add(cls.student_b)
            cls.db.commit()
            cls.db.refresh(cls.student_b)

        cls.token_a = create_access_token(cls.student_a.id, "student")
        cls.headers_a = {"Authorization": f"Bearer {cls.token_a}"}

        cls.token_b = create_access_token(cls.student_b.id, "student")
        cls.headers_b = {"Authorization": f"Bearer {cls.token_b}"}

        # Create a dedicated test course for Step 2B
        cls.course = cls.db.query(Course).filter(Course.code == "CS2B_TEST").first()
        if not cls.course:
            cls.course = Course(
                code="CS2B_TEST",
                title="Integrity Test Course",
                description="Testing Step 2B Integrity",
                category="Testing",
                level="Undergraduate",
            )
            cls.db.add(cls.course)
            cls.db.commit()
            cls.db.refresh(cls.course)

        # Create topics: Prereq Topic (T1) and Dependent Topic (T2)
        cls.topic1 = cls.db.query(Topic).filter(Topic.course_id == cls.course.id, Topic.code == "T2B_01").first()
        if not cls.topic1:
            cls.topic1 = Topic(
                course_id=cls.course.id,
                code="T2B_01",
                title="Foundational Topic 1",
                order_index=1,
                description="Prerequisite Topic",
                learning_objective="Foundations",
                difficulty="Beginner",
                est_minutes=30
            )
            cls.db.add(cls.topic1)
            cls.db.commit()
            cls.db.refresh(cls.topic1)

        cls.topic2 = cls.db.query(Topic).filter(Topic.course_id == cls.course.id, Topic.code == "T2B_02").first()
        if not cls.topic2:
            cls.topic2 = Topic(
                course_id=cls.course.id,
                code="T2B_02",
                title="Dependent Topic 2",
                order_index=2,
                description="Advanced Topic",
                learning_objective="Application",
                difficulty="Intermediate",
                est_minutes=45
            )
            cls.db.add(cls.topic2)
            cls.db.commit()
            cls.db.refresh(cls.topic2)

        # Add prerequisite relationship: T2 requires T1 (PREREQ_UNLOCK = 60.0)
        prereq = cls.db.query(TopicPrerequisite).filter(
            TopicPrerequisite.topic_id == cls.topic2.id,
            TopicPrerequisite.prerequisite_topic_id == cls.topic1.id
        ).first()
        if not prereq:
            prereq = TopicPrerequisite(
                topic_id=cls.topic2.id,
                prerequisite_topic_id=cls.topic1.id,
                required_mastery_pct=PREREQ_UNLOCK
            )
            cls.db.add(prereq)
            cls.db.commit()

        # Add standalone unlocked topic (T3)
        cls.topic3 = cls.db.query(Topic).filter(Topic.course_id == cls.course.id, Topic.code == "T2B_03").first()
        if not cls.topic3:
            cls.topic3 = Topic(
                course_id=cls.course.id,
                code="T2B_03",
                title="Standalone Topic 3",
                order_index=3,
                description="Standalone Topic",
                learning_objective="Independence",
                difficulty="Beginner",
                est_minutes=25
            )
            cls.db.add(cls.topic3)
            cls.db.commit()
            cls.db.refresh(cls.topic3)

        # Add Course Outcomes
        cls.co1 = cls.db.query(CourseOutcome).filter(CourseOutcome.course_id == cls.course.id, CourseOutcome.code == "CO2B_1").first()
        if not cls.co1:
            cls.co1 = CourseOutcome(
                course_id=cls.course.id,
                code="CO2B_1",
                description="Weighted CO Test",
                target_attainment_pct=CO_ACHIEVED_DEFAULT
            )
            cls.db.add(cls.co1)
            cls.db.commit()
            cls.db.refresh(cls.co1)

        # Setup TopicOutcomeMapping: T1 -> weight 1.0, T3 -> weight 2.0
        m1 = cls.db.query(TopicOutcomeMapping).filter(TopicOutcomeMapping.topic_id == cls.topic1.id, TopicOutcomeMapping.outcome_id == cls.co1.id).first()
        if not m1:
            cls.db.add(TopicOutcomeMapping(topic_id=cls.topic1.id, outcome_id=cls.co1.id, weight=1.0))
        m2 = cls.db.query(TopicOutcomeMapping).filter(TopicOutcomeMapping.topic_id == cls.topic3.id, TopicOutcomeMapping.outcome_id == cls.co1.id).first()
        if not m2:
            cls.db.add(TopicOutcomeMapping(topic_id=cls.topic3.id, outcome_id=cls.co1.id, weight=2.0))
        cls.db.commit()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def _reset_user_topic(self, user_id: int, topic_id: int):
        """Cleans up mastery, history, and attempts for a specific user and topic."""
        self.db.query(MasteryScore).filter(
            MasteryScore.user_id == user_id,
            MasteryScore.topic_id == topic_id
        ).delete()
        self.db.query(MasteryHistory).filter(
            MasteryHistory.user_id == user_id,
            MasteryHistory.topic_id == topic_id
        ).delete()
        self.db.query(AssessmentAttempt).filter(
            AssessmentAttempt.user_id == user_id,
            AssessmentAttempt.topic_id == topic_id
        ).delete()
        self.db.commit()

    # --------------------------------------------------------------------------
    # 1. topic/complete on a LOCKED topic returns 403 and mastery is unchanged
    # --------------------------------------------------------------------------
    def test_topic_complete_locked_topic_returns_403(self):
        # T1 is prerequisite to T2. Reset T1 mastery to 0 (unsatisfied)
        self._reset_user_topic(self.student_a.id, self.topic1.id)
        self._reset_user_topic(self.student_a.id, self.topic2.id)

        # Seed passed attempt for T2 to ensure it fails on LOCK, not evidence rule
        passed_attempt = AssessmentAttempt(
            attempt_uuid=f"test-lock-{uuid.uuid4().hex[:8]}",
            user_id=self.student_a.id,
            course_id=self.course.id,
            topic_id=self.topic2.id,
            attempt_type="practice",
            score=85.0,
            max_score=100.0,
            percentage=85.0,
            passed=True,
            created_at=datetime.utcnow()
        )
        self.db.add(passed_attempt)
        self.db.commit()

        # Attempt to complete locked Topic 2
        resp = client.post(f"/api/assessment/topic/complete/{self.topic2.id}", headers=self.headers_a)
        self.assertEqual(resp.status_code, 403, f"Expected 403 on locked topic completion, got {resp.status_code}: {resp.text}")
        self.assertIn("locked", resp.json()["detail"].lower())

        # Verify topic 2 mastery is not completed / unchanged
        m = self.db.query(MasteryScore).filter(
            MasteryScore.user_id == self.student_a.id,
            MasteryScore.topic_id == self.topic2.id
        ).first()
        overall = m.overall_mastery if m else 0.0
        self.assertNotEqual(overall, 100.0, "Mastery must not be set to 100 on a locked topic")

    # --------------------------------------------------------------------------
    # 2. topic/complete without a passed assessment returns 400
    # --------------------------------------------------------------------------
    def test_topic_complete_without_passed_assessment_returns_400(self):
        # Topic 3 is standalone (unlocked), but has NO passed assessment
        self._reset_user_topic(self.student_a.id, self.topic3.id)

        resp = client.post(f"/api/assessment/topic/complete/{self.topic3.id}", headers=self.headers_a)
        self.assertEqual(resp.status_code, 400, f"Expected 400 without passed assessment, got {resp.status_code}: {resp.text}")
        self.assertIn("Complete the practice assessment first", resp.json()["detail"])

        # Verify mastery remains unchanged
        m = self.db.query(MasteryScore).filter(
            MasteryScore.user_id == self.student_a.id,
            MasteryScore.topic_id == self.topic3.id
        ).first()
        self.assertTrue(m is None or m.overall_mastery < 100.0)

    # --------------------------------------------------------------------------
    # 3. after passed assessment, completion works; completing twice returns 409 with no duplicate history
    # --------------------------------------------------------------------------
    def test_topic_complete_with_evidence_and_idempotent_409(self):
        self._reset_user_topic(self.student_a.id, self.topic3.id)

        # Seed passed assessment
        passed_attempt = AssessmentAttempt(
            attempt_uuid=f"test-pass-{uuid.uuid4().hex[:8]}",
            user_id=self.student_a.id,
            course_id=self.course.id,
            topic_id=self.topic3.id,
            attempt_type="practice",
            score=75.0,
            max_score=100.0,
            percentage=75.0,
            passed=True,
            created_at=datetime.utcnow()
        )
        self.db.add(passed_attempt)
        self.db.commit()

        # First call: must succeed (200)
        resp1 = client.post(f"/api/assessment/topic/complete/{self.topic3.id}", headers=self.headers_a)
        self.assertEqual(resp1.status_code, 200, f"First completion must succeed, got {resp1.status_code}: {resp1.text}")
        data1 = resp1.json()
        self.assertEqual(data1["new_mastery"], 100.0)

        # Check MasteryHistory has exactly 1 completion row
        hist_count_1 = self.db.query(MasteryHistory).filter(
            MasteryHistory.user_id == self.student_a.id,
            MasteryHistory.topic_id == self.topic3.id,
            MasteryHistory.source == "completion"
        ).count()
        self.assertEqual(hist_count_1, 1, "Must have exactly 1 completion history entry")

        # Second call: must return 409 Conflict (idempotent, no recalculation/duplicates)
        resp2 = client.post(f"/api/assessment/topic/complete/{self.topic3.id}", headers=self.headers_a)
        self.assertEqual(resp2.status_code, 409, f"Second completion must return 409, got {resp2.status_code}: {resp2.text}")
        self.assertIn("already completed", resp2.json()["detail"].lower())

        # Verify MasteryHistory count is STILL 1
        hist_count_2 = self.db.query(MasteryHistory).filter(
            MasteryHistory.user_id == self.student_a.id,
            MasteryHistory.topic_id == self.topic3.id,
            MasteryHistory.source == "completion"
        ).count()
        self.assertEqual(hist_count_2, 1, "Duplicate completion must not add duplicate history rows")

    # --------------------------------------------------------------------------
    # 4. student cannot complete a topic for another user via any user_id parameter
    # --------------------------------------------------------------------------
    def test_cross_student_completion_forbidden(self):
        # Student A calls topic/complete passing Student B's user_id in query parameter
        resp = client.post(
            f"/api/assessment/topic/complete/{self.topic3.id}?user_id={self.student_b.id}",
            headers=self.headers_a
        )
        self.assertEqual(resp.status_code, 403, f"Expected 403 on cross-student complete, got {resp.status_code}: {resp.text}")

        # Verify Student B's mastery is completely untouched
        m_b = self.db.query(MasteryScore).filter(
            MasteryScore.user_id == self.student_b.id,
            MasteryScore.topic_id == self.topic3.id
        ).first()
        self.assertTrue(m_b is None or m_b.overall_mastery < 100.0)

    # --------------------------------------------------------------------------
    # 5. weighted CO calculation gives the expected value (e.g. weights 1.0 and 2.0)
    # --------------------------------------------------------------------------
    def test_weighted_course_outcome_calculation(self):
        # Setup: T1 mastery = 60.0 (weight 1.0), T3 mastery = 90.0 (weight 2.0)
        # Expected CO1 attainment = (60.0 * 1.0 + 90.0 * 2.0) / (1.0 + 2.0) = 240 / 3 = 80.0%
        m1 = self.db.query(MasteryScore).filter(MasteryScore.user_id == self.student_a.id, MasteryScore.topic_id == self.topic1.id).first()
        if not m1:
            m1 = MasteryScore(user_id=self.student_a.id, topic_id=self.topic1.id)
            self.db.add(m1)
        m1.overall_mastery = 60.0

        m3 = self.db.query(MasteryScore).filter(MasteryScore.user_id == self.student_a.id, MasteryScore.topic_id == self.topic3.id).first()
        if not m3:
            m3 = MasteryScore(user_id=self.student_a.id, topic_id=self.topic3.id)
            self.db.add(m3)
        m3.overall_mastery = 90.0
        self.db.commit()

        # Execute recalculation
        recalculate_course_outcomes(self.db, user_id=self.student_a.id, course_id=self.course.id, trigger="weighted_test")

        attainment = self.db.query(OutcomeAttainment).filter(
            OutcomeAttainment.user_id == self.student_a.id,
            OutcomeAttainment.course_id == self.course.id,
            OutcomeAttainment.outcome_id == self.co1.id
        ).first()

        self.assertIsNotNone(attainment, "OutcomeAttainment row must exist")
        self.assertAlmostEqual(attainment.attainment_percentage, 80.0, places=1,
                               msg=f"Expected weighted attainment of 80.0%, got {attainment.attainment_percentage}%")
        self.assertEqual(attainment.status, "Achieved", "80% >= 70% target should be 'Achieved'")

    # --------------------------------------------------------------------------
    # 6. concurrent recalculation does not create duplicate OutcomeAttainment rows
    # --------------------------------------------------------------------------
    def test_concurrent_recalculation_no_duplicate_rows(self):
        # Run 8 concurrent recalculations in separate threads/sessions
        def run_recalc():
            session = SessionLocal()
            try:
                recalculate_course_outcomes(session, user_id=self.student_a.id, course_id=self.course.id, trigger="concurrency_test")
            finally:
                session.close()

        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = [executor.submit(run_recalc) for _ in range(8)]
            for f in futures:
                f.result()

        # Query all OutcomeAttainment rows for this student, course, and outcome
        rows = self.db.query(OutcomeAttainment).filter(
            OutcomeAttainment.user_id == self.student_a.id,
            OutcomeAttainment.course_id == self.course.id,
            OutcomeAttainment.outcome_id == self.co1.id
        ).all()

        self.assertEqual(len(rows), 1, f"Expected exactly 1 OutcomeAttainment row due to unique constraint, found {len(rows)}")

    # --------------------------------------------------------------------------
    # 7. diagnostic submit writes MasteryHistory and QuestionAnswerHistory
    # --------------------------------------------------------------------------
    def test_diagnostic_submit_records_history(self):
        # Create a fresh student for diagnostic test
        diag_user = self.db.query(User).filter(User.email == "diag_student@obe.edu").first()
        if not diag_user:
            diag_user = User(
                email="diag_student@obe.edu",
                full_name="Diag Student",
                role="student",
                password_hash=hash_password("demo123"),
            )
            self.db.add(diag_user)
            self.db.commit()
            self.db.refresh(diag_user)

        # Ensure student profile exists
        prof = self.db.query(StudentProfile).filter(StudentProfile.user_id == diag_user.id).first()
        if not prof:
            prof = StudentProfile(user_id=diag_user.id, selected_course_id=1)
            self.db.add(prof)
            self.db.commit()

        diag_token = create_access_token(diag_user.id, "student")
        diag_headers = {"Authorization": f"Bearer {diag_token}"}

        # Fetch questions for course 1
        q_list = self.db.query(QuestionBank).filter(QuestionBank.course_id == 1).limit(3).all()
        answers = [{"question_id": q.id, "selected_answer": q.correct_answer} for q in q_list]

        submit_payload = {
            "course_id": 1,
            "answers": answers
        }

        resp = client.post("/api/diagnostic/submit", headers=diag_headers, json=submit_payload)
        self.assertEqual(resp.status_code, 200, f"Diagnostic submit failed: {resp.text}")

        # Check MasteryHistory has baseline entries with source="diagnostic"
        mh_entries = self.db.query(MasteryHistory).filter(
            MasteryHistory.user_id == diag_user.id,
            MasteryHistory.source == "diagnostic"
        ).all()
        self.assertTrue(len(mh_entries) > 0, "MasteryHistory must have baseline records with source='diagnostic'")

        # Check QuestionAnswerHistory has entries for every answered question in the diagnostic
        qah_entries = self.db.query(QuestionAnswerHistory).filter(
            QuestionAnswerHistory.user_id == diag_user.id
        ).all()
        # Course 1 has 5 diagnostic questions evaluated during diagnostic submit
        self.assertGreaterEqual(len(qah_entries), len(answers), "QuestionAnswerHistory must record each question")
        for qah in qah_entries:
            self.assertIsNotNone(qah.question_id)

    # --------------------------------------------------------------------------
    # 8. outcome_attainment_history gets a row per recalculation
    # --------------------------------------------------------------------------
    def test_outcome_attainment_history_snapshot(self):
        initial_count = self.db.query(OutcomeAttainmentHistory).filter(
            OutcomeAttainmentHistory.user_id == self.student_a.id,
            OutcomeAttainmentHistory.course_id == self.course.id,
            OutcomeAttainmentHistory.trigger == "history_snapshot_check"
        ).count()

        recalculate_course_outcomes(
            self.db,
            user_id=self.student_a.id,
            course_id=self.course.id,
            trigger="history_snapshot_check"
        )

        final_count = self.db.query(OutcomeAttainmentHistory).filter(
            OutcomeAttainmentHistory.user_id == self.student_a.id,
            OutcomeAttainmentHistory.course_id == self.course.id,
            OutcomeAttainmentHistory.trigger == "history_snapshot_check"
        ).count()

        self.assertGreater(final_count, initial_count, "recalculate_course_outcomes must create OutcomeAttainmentHistory snapshots")

    # --------------------------------------------------------------------------
    # 9. compile-code timeout capped and malicious call expression returns 400
    # --------------------------------------------------------------------------
    def test_compile_code_limits_and_ast_injection_prevention(self):
        # Subtest A: timeout capped at 5s (large timeout accepted without crash)
        resp_timeout = client.post(
            "/api/assessment/compile-code",
            headers=self.headers_a,
            json={
                "code": "def add(a, b):\n    return a + b\n",
                "test_cases": [{"call": "add(2, 3)", "expected": "5"}],
                "timeout_sec": 999999
            }
        )
        self.assertEqual(resp_timeout.status_code, 200, f"Expected 200 with capped timeout, got {resp_timeout.status_code}: {resp_timeout.text}")
        self.assertTrue(resp_timeout.json()["passed_count"] == 1)

        # Subtest B: code length exceeding 10,000 chars returns 400
        huge_code = "x = 1\n" * 2500 # > 12,000 chars
        resp_huge = client.post(
            "/api/assessment/compile-code",
            headers=self.headers_a,
            json={"code": huge_code, "test_cases": []}
        )
        self.assertEqual(resp_huge.status_code, 400, "Code > 10,000 chars must return 400")
        self.assertIn("10,000", resp_huge.json()["detail"])

        # Subtest C: test cases count exceeding 20 returns 400
        too_many_cases = [{"call": "add(1, 1)", "expected": "2"}] * 25
        resp_cases = client.post(
            "/api/assessment/compile-code",
            headers=self.headers_a,
            json={"code": "def add(a, b): return a + b", "test_cases": too_many_cases}
        )
        self.assertEqual(resp_cases.status_code, 400, "Test cases > 20 must return 400")

        # Subtest D: malicious eval / import / system calls return 400
        malicious_calls = [
            "__import__('os').system('dir')",
            "eval('1 + 1')",
            "exec('pass')",
            "open('secret.txt', 'r')",
            "getattr(os, 'system')",
            "__subclasses__()",
            "add(1, 2); import os"
        ]
        for bad_call in malicious_calls:
            resp_bad = client.post(
                "/api/assessment/compile-code",
                headers=self.headers_a,
                json={
                    "code": "def add(a, b): return a + b",
                    "test_cases": [{"call": bad_call, "expected": "0"}]
                }
            )
            self.assertEqual(resp_bad.status_code, 400, f"Expected 400 for unsafe call '{bad_call}', got {resp_bad.status_code}")
            self.assertIn("unsafe", resp_bad.json()["detail"].lower())

    # --------------------------------------------------------------------------
    # 10. single source of truth for thresholds (the grep test)
    # --------------------------------------------------------------------------
    def test_single_source_of_truth_thresholds_grep(self):
        import ast

        target_files = [
            "progress_engine.py",
            "ai_agents/assessment_agent.py",
            "routes/assessments.py",
            "routes/mastery_outcomes.py",
            "routes/progress.py",
            "routes/faculty.py",
            "routes/student.py"
        ]

        THRESHOLDS = {60, 60.0, 70, 70.0, 80, 80.0}

        class ThresholdVisitor(ast.NodeVisitor):
            def __init__(self, filename):
                self.filename = filename
                self.violations = []

            def visit_Compare(self, node):
                if isinstance(node.left, ast.Constant) and node.left.value in THRESHOLDS:
                    self.violations.append(f"{self.filename}:{node.lineno} (left comparator has literal {node.left.value})")
                for comp in node.comparators:
                    if isinstance(comp, ast.Constant) and comp.value in THRESHOLDS:
                        self.violations.append(f"{self.filename}:{node.lineno} (comparison has literal {comp.value})")
                self.generic_visit(node)

        all_violations = []

        for rel_path in target_files:
            abs_path = os.path.join(backend_dir, rel_path)
            if not os.path.isfile(abs_path):
                continue

            with open(abs_path, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source, filename=rel_path)
            visitor = ThresholdVisitor(rel_path)
            visitor.visit(tree)
            all_violations.extend(visitor.violations)

        self.assertEqual(
            len(all_violations), 0,
            f"Found {len(all_violations)} hardcoded threshold comparison literals! Use core.thresholds constants instead:\n" +
            "\n".join(all_violations)
        )

        # Sanity check: verify that the visitor WOULD catch a violation if present
        bad_code = "if score >= 60.0:\n    pass\n"
        bad_tree = ast.parse(bad_code)
        bad_visitor = ThresholdVisitor("mock_bad.py")
        bad_visitor.visit(bad_tree)
        self.assertEqual(len(bad_visitor.violations), 1, "Checker must detect hardcoded threshold comparisons")


if __name__ == "__main__":
    unittest.main()
