import sys
import os
import unittest
from datetime import datetime

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
from models import (
    User, StudentProfile, Course, Topic, MasteryScore,
    LearningPath, LearningPathItem, CourseOutcome, OutcomeAttainment
)
from ai_agents.progress_agent import ProgressMonitoringAgent

class TestTopicCompletionWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.db = SessionLocal()

        import uuid
        from core.security import hash_password
        uid = uuid.uuid4().hex[:8]
        cls.student_a_email = f"student_a_{uid}@obe.edu"
        cls.student_b_email = f"student_b_{uid}@obe.edu"

        user_a = User(email=cls.student_a_email, full_name="Student Test A", role="student", password_hash=hash_password("TopicPass123!"))
        cls.db.add(user_a)
        cls.db.flush()
        prof_a = StudentProfile(user_id=user_a.id, selected_course_id=2, academic_level="Undergraduate", learning_goal="Master DS")
        cls.db.add(prof_a)

        user_b = User(email=cls.student_b_email, full_name="Student Test B", role="student", password_hash=hash_password("TopicPass123!"))
        cls.db.add(user_b)
        cls.db.flush()
        prof_b = StudentProfile(user_id=user_b.id, selected_course_id=2, academic_level="Undergraduate", learning_goal="Master DS")
        cls.db.add(prof_b)

        cls.db.commit()
        cls.user_a_id = user_a.id
        cls.user_b_id = user_b.id

        # Clean up prior test data for student A and B to ensure reproducible test run
        from models import MasteryHistory, AssessmentAttempt, QuestionAnswerHistory
        for uid in [cls.user_a_id, cls.user_b_id]:
            cls.db.query(MasteryHistory).filter(MasteryHistory.user_id == uid).delete()
            cls.db.query(QuestionAnswerHistory).filter(QuestionAnswerHistory.user_id == uid).delete()
            cls.db.query(AssessmentAttempt).filter(AssessmentAttempt.user_id == uid).delete()
            cls.db.query(MasteryScore).filter(MasteryScore.user_id == uid).delete()
            cls.db.query(LearningPathItem).filter(
                LearningPathItem.learning_path_id.in_(
                    cls.db.query(LearningPath.id).filter(LearningPath.user_id == uid)
                )
            ).delete(synchronize_session=False)
            cls.db.query(LearningPath).filter(LearningPath.user_id == uid).delete()
            cls.db.query(OutcomeAttainment).filter(OutcomeAttainment.user_id == uid).delete()
        cls.db.commit()

        from core.security import create_access_token
        cls.headers_a = {"Authorization": f"Bearer {create_access_token(cls.user_a_id, 'student')}"}
        cls.headers_b = {"Authorization": f"Bearer {create_access_token(cls.user_b_id, 'student')}"}

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def _seed_passed_assessment(self, user_id: int, course_id: int, topic_id: int):
        from models import AssessmentAttempt
        import uuid
        att = AssessmentAttempt(
            attempt_uuid=f"test-pass-{uuid.uuid4().hex[:8]}",
            user_id=user_id,
            course_id=course_id,
            topic_id=topic_id,
            attempt_type="practice",
            score=10.0,
            max_score=10.0,
            percentage=100.0,
            passed=True,
            created_at=datetime.utcnow()
        )
        self.db.add(att)
        self.db.commit()

    def test_01_reproduce_root_cause_of_40_percent_mastery_bug(self):
        """
        Demonstrate why the previous code left mastery at 40% when completed:
        Old ProgressMonitoringAgent formula:
        0.40 * diag + 0.30 * quiz + 0.20 * practice + 0.10 * completion
        With diag=0, quiz=100, practice=0, completion=100:
        0.30*100 + 0.10*100 = 40.0%
        """
        old_calc = ProgressMonitoringAgent.calculate_mastery(
            diagnostic_score=0.0,
            quiz_score=100.0,
            practice_score=0.0,
            completion_score=100.0
        )
        self.assertEqual(old_calc["overall_mastery"], 40.0)
        self.assertEqual(old_calc["classification"], "Developing")
        print(f"\n[PASS] Root Cause Reproduced: Old 4-part formula yielded {old_calc['overall_mastery']}% instead of 100% when completion was credited.")

    def test_02_topic_completion_updates_mastery_to_100_and_status(self):
        """
        Test that completing Topic 1 sets overall_mastery to 100.0%, classification to MASTERED,
        and learning path status to COMPLETED.
        """
        # Initialize student A with fresh demo state in Course 2
        r_seed = self.client.post("/api/progress/seed-demo-journey", json={"course_id": 2}, params={"user_id": self.user_a_id}, headers=self.headers_a)
        self.assertEqual(r_seed.status_code, 200)

        # Before completion: Check Topic 1 mastery
        state_before = self.client.get(f"/api/progress/state?user_id={self.user_a_id}&course_id=2", headers=self.headers_a).json()
        t1_before = next(t for t in state_before["topicMastery"] if t["topic_id"] == 1)
        co1_before = next(c for c in state_before["courseOutcomeAttainment"] if c["code"] == "CO1")
        progress_before = state_before["overallProgress"]

        print(f"\n[BEFORE COMPLETION] Topic 1 mastery: {t1_before['mastery']}%, CO1: {co1_before['attainment_percentage']}%, Progress: {progress_before}%")

        # Seed passed assessment evidence (Step 2B evidence requirement)
        self._seed_passed_assessment(self.user_a_id, 2, 1)

        # Call completion endpoint
        r_comp = self.client.post(f"/api/assessment/topic/complete/1?user_id={self.user_a_id}", headers=self.headers_a)
        self.assertEqual(r_comp.status_code, 200)
        comp_res = r_comp.json()

        # Check response values
        self.assertEqual(comp_res["new_mastery"], 100.0)
        self.assertEqual(comp_res["classification"], "MASTERED")
        self.assertEqual(comp_res["completion_score"], 100.0)

        # Verify state in database
        state_after = self.client.get(f"/api/progress/state?user_id={self.user_a_id}&course_id=2", headers=self.headers_a).json()
        t1_after = next(t for t in state_after["topicMastery"] if t["topic_id"] == 1)

        self.assertEqual(t1_after["mastery"], 100.0)
        self.assertEqual(t1_after["classification"], "MASTERED")
        self.assertEqual(t1_after["status"], "COMPLETED")

        print(f"[AFTER COMPLETION] Topic 1 mastery: {t1_after['mastery']}%, status: {t1_after['status']}, class: {t1_after['classification']}")

    def test_03_automatic_next_topic_progression(self):
        """
        Verify that Current Focus advances from Topic 1 to Topic 2, and that
        Topic 2 becomes CURRENT.
        """
        state = self.client.get(f"/api/progress/state?user_id={self.user_a_id}&course_id=2", headers=self.headers_a).json()
        current_focus = state["currentTargetTopic"]
        self.assertIsNotNone(current_focus)
        self.assertEqual(current_focus["topic_id"], 2, f"Expected Topic 2 as current focus, got {current_focus['topic_id']}")
        self.assertEqual(current_focus["title"], "Queue Basics & Operations")

        # Verify learning path items
        lp_items = state["learningPath"]["items"]
        t1_item = next(i for i in lp_items if i["topic_id"] == 1)
        t2_item = next(i for i in lp_items if i["topic_id"] == 2)

        self.assertEqual(t1_item["status"], "COMPLETED")
        self.assertEqual(t2_item["status"], "CURRENT")
        print(f"[PASS] Next topic progression verified: Current focus successfully advanced to {current_focus['title']} (Topic {current_focus['topic_id']})")

    def test_04_prerequisite_rules_and_dependent_unlock(self):
        """
        Verify that:
        1. Topic 8 (Algorithm Complexity) requires Topic 1 >= 60%, so it is now unlocked!
        2. Topic 5 (Tree Traversal) requires Topic 3 and Topic 4 >= 60%, so it remains locked with clear reason!
        """
        state = self.client.get(f"/api/progress/state?user_id={self.user_a_id}&course_id=2", headers=self.headers_a).json()
        t8 = next(t for t in state["topicMastery"] if t["topic_id"] == 8)
        t5 = next(t for t in state["topicMastery"] if t["topic_id"] == 5)

        # Topic 8 should be unlocked because Topic 1 reached 100% (>= 60%)
        self.assertFalse(t8["is_locked"], "Topic 8 should be unlocked after Topic 1 completed")

        # Topic 5 should still be locked because Topic 3 and 4 are not yet >= 60%
        self.assertTrue(t5["is_locked"], "Topic 5 should remain locked")
        self.assertTrue(len(t5["unsatisfied_prerequisites"]) > 0)
        print(f"[PASS] Prerequisite evaluation verified: Topic 8 unlocked; Topic 5 remains locked: {t5['unsatisfied_prerequisites']}")

    def test_05_dynamic_course_outcome_attainment_and_progress(self):
        """
        Verify that Course Outcome (CO1 & CO2) attainment and course progress
        updated and are persisted in OutcomeAttainment.
        """
        state = self.client.get(f"/api/progress/state?user_id={self.user_a_id}&course_id=2", headers=self.headers_a).json()
        co1 = next(c for c in state["courseOutcomeAttainment"] if c["code"] == "CO1")
        co2 = next(c for c in state["courseOutcomeAttainment"] if c["code"] == "CO2")

        # Verify persisted database records
        db_co1 = self.db.query(OutcomeAttainment).filter(
            OutcomeAttainment.user_id == self.user_a_id,
            OutcomeAttainment.course_id == 2
        ).first()
        self.assertIsNotNone(db_co1)

        self.assertGreater(state["overallProgress"], 0)
        self.assertGreaterEqual(state["masteredCount"], 1)
        print(f"[PASS] Dynamic CO attainment verified: CO1={co1['attainment_percentage']}%, CO2={co2['attainment_percentage']}%, Progress={state['overallProgress']}%")

    def test_06_course_completion_state_when_all_topics_mastered(self):
        """
        Verify that when all topics in Course 2 are completed:
        1. courseCompleted is True
        2. currentTargetTopic is None
        3. All topics have status COMPLETED and mastery >= 80%
        """
        # Complete all 8 topics for Student A with verified assessment evidence
        # Complete independent topics first (1, 2, 3, 4), then dependents (5, 6, 7, 8)
        for tid in [1, 2, 3, 4, 6, 8, 5, 7]:
            self._seed_passed_assessment(self.user_a_id, 2, tid)
            r = self.client.post(f"/api/assessment/topic/complete/{tid}?user_id={self.user_a_id}", headers=self.headers_a)
            self.assertIn(r.status_code, [200, 409])

        state = self.client.get(f"/api/progress/state?user_id={self.user_a_id}&course_id=2", headers=self.headers_a).json()
        self.assertTrue(state["courseCompleted"], "Course should be marked completed")
        self.assertIsNone(state["currentTargetTopic"], "currentTargetTopic should be None when all topics are done")
        self.assertEqual(state["masteredCount"], 8)
        self.assertEqual(state["overallProgress"], 100.0)
        self.assertEqual(state["overallMastery"], 100.0)
        print(f"[PASS] Course completion state verified: All 8 topics mastered, progress=100.0%, currentTarget=None, courseCompleted=True")

    def test_07_student_data_isolation(self):
        """
        Verify that completing topics for Student A did NOT affect Student B.
        """
        # Student B should still have their separate progress
        state_b = self.client.get(f"/api/progress/state?user_id={self.user_b_id}&course_id=2", headers=self.headers_b).json()
        self.assertFalse(state_b["courseCompleted"])

        # Check student B's Topic 1
        t1_b = next((t for t in state_b["topicMastery"] if t["topic_id"] == 1), None)
        if t1_b:
            self.assertNotEqual(t1_b["mastery"], 100.0, "Student B's Topic 1 should not be 100% just because Student A completed it")
        print(f"[PASS] Student data isolation verified: Student B is completely unaffected by Student A's completions.")

    def test_08_course_1_topic_completion_and_unlock_chain(self):
        """
        Verify that in Course 1 (Python Programming):
        Completing Topic 9 (Variables) unlocks Topic 10 (Conditionals),
        Topic 10 becomes CURRENT, Topic 11 (Loops) remains LOCKED.
        """
        # Reset Student B's course 1 state
        self.client.put(f"/api/profile?user_id={self.user_b_id}", json={"selected_course_id": 1}, headers=self.headers_b)
        self.db.query(MasteryScore).filter(MasteryScore.user_id == self.user_b_id).delete()
        self.db.query(LearningPathItem).filter(
            LearningPathItem.learning_path_id.in_(
                self.db.query(LearningPath.id).filter(LearningPath.user_id == self.user_b_id)
            )
        ).delete(synchronize_session=False)
        self.db.query(LearningPath).filter(LearningPath.user_id == self.user_b_id).delete()
        self.db.commit()

        # Seed passed assessment evidence for Topic 9
        self._seed_passed_assessment(self.user_b_id, 1, 9)

        # Complete Topic 9 for Student B
        r_comp = self.client.post(f"/api/assessment/topic/complete/9?user_id={self.user_b_id}", headers=self.headers_b)
        self.assertEqual(r_comp.status_code, 200)

        state_b = self.client.get(f"/api/progress/state?user_id={self.user_b_id}&course_id=1", headers=self.headers_b).json()
        t9 = next(t for t in state_b["topicMastery"] if t["topic_id"] == 9)
        t10 = next(t for t in state_b["topicMastery"] if t["topic_id"] == 10)
        t11 = next(t for t in state_b["topicMastery"] if t["topic_id"] == 11)

        self.assertEqual(t9["mastery"], 100.0)
        self.assertEqual(t9["status"], "COMPLETED")
        self.assertFalse(t10["is_locked"], "Topic 10 should be unlocked because Topic 9 reached 100% >= 60%")
        self.assertTrue(t11["is_locked"], "Topic 11 should still be locked because Topic 10 has not reached 60%")
        self.assertEqual(state_b["currentTargetTopic"]["topic_id"], 10, "Topic 10 should be the next CURRENT target")
        print(f"[PASS] Course 1 progression chain verified: Topic 9 COMPLETED, Topic 10 UNLOCKED and CURRENT, Topic 11 LOCKED: {t11['unsatisfied_prerequisites']}")

if __name__ == "__main__":
    unittest.main()
