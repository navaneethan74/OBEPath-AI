import sys
import os
import unittest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(__file__))

from main import app
from database import SessionLocal
from models import User, StudentProfile, Course, Topic, DiagnosticQuestion, QuestionBank, CourseOutcome
from core.security import create_access_token

client = TestClient(app)

class TestCourseSwitchIsolation(unittest.TestCase):

    def setUp(self):
        self.db = SessionLocal()
        student = self.db.query(User).filter(User.email == "course_switch_test_student@example.com").first()
        if not student:
            student = User(
                email="course_switch_test_student@example.com",
                password_hash="dummy_hash_switch_123",
                full_name="Course Switch Student",
                role="student"
            )
            self.db.add(student)
            self.db.commit()
            self.db.refresh(student)
            prof = self.db.query(StudentProfile).filter(StudentProfile.user_id == student.id).first()
            if not prof:
                prof = StudentProfile(user_id=student.id, selected_course_id=2)
                self.db.add(prof)
                self.db.commit()
        self.student = student
        self.student_id = student.id
        self.auth_headers = {"Authorization": f"Bearer {create_access_token(student.id, 'student')}"}

    def tearDown(self):
        self.db.close()

    def test_all_four_courses_return_only_their_own_questions(self):
        """
        Verify that for all 4 courses (CS101, CS201, AI301, CS302),
        /api/progress/questions returns ONLY questions belonging to that specific course.
        """
        courses = self.db.query(Course).all()
        self.assertGreaterEqual(len(courses), 4)

        for course in courses:
            res = client.get(
                f"/api/progress/questions?course_id={course.id}&count=5",
                headers=self.auth_headers
            )
            self.assertEqual(res.status_code, 200, f"Failed for course {course.code} (id={course.id})")
            questions = res.json()
            self.assertGreater(len(questions), 0, f"No questions returned for course {course.code}")

            for q in questions:
                self.assertEqual(
                    q["course_id"],
                    course.id,
                    f"Cross-course question contamination: expected course {course.id}, got {q['course_id']}"
                )
                topic = self.db.query(Topic).filter(Topic.id == q["topic_id"]).first()
                self.assertIsNotNone(topic)
                self.assertEqual(
                    topic.course_id,
                    course.id,
                    f"Question topic {q['topic_id']} belongs to course {topic.course_id}, not {course.id}"
                )

    def test_diagnostic_questions_are_strictly_course_isolated(self):
        """
        Verify that /api/diagnostic/{course_id} returns only questions for that course
        and never falls back to other courses.
        """
        for cid in [1, 2, 3, 4]:
            res = client.get(f"/api/diagnostic/{cid}", headers=self.auth_headers)
            self.assertEqual(res.status_code, 200, f"Diagnostic failed for course {cid}")
            questions = res.json()
            self.assertGreater(len(questions), 0, f"No diagnostic questions for course {cid}")

            for q in questions:
                self.assertEqual(q["course_id"], cid, f"Diagnostic question {q['id']} has course_id {q['course_id']} != {cid}")
                topic = self.db.query(Topic).filter(Topic.id == q["topic_id"]).first()
                self.assertIsNotNone(topic)
                self.assertEqual(topic.course_id, cid)

    def test_cs302_course_outcomes_and_state(self):
        """
        Verify that with CS302 selected, the state contains Database Management Systems outcomes,
        not Data Structures outcomes.
        """
        res = client.get("/api/progress/state?course_id=4", headers=self.auth_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data["enrolledCourse"]["id"], 4)
        self.assertEqual(data["enrolledCourse"]["code"], "CS302")
        self.assertIn("Database", data["enrolledCourse"]["title"])

        outcomes = data["courseOutcomeAttainment"]
        self.assertGreaterEqual(len(outcomes), 4)
        co_descriptions = " ".join([co["description"] for co in outcomes])
        # Must contain database / relational concepts
        self.assertTrue(
            "relational" in co_descriptions.lower() or "database" in co_descriptions.lower() or "sql" in co_descriptions.lower(),
            f"CS302 outcomes do not mention database concepts: {co_descriptions}"
        )
        # Must NOT mention Stack, Queue, or Trees from CS201
        self.assertNotIn("stack, queue", co_descriptions.lower())
        self.assertNotIn("tree traversals", co_descriptions.lower())

    def test_cross_course_topic_mismatch_rejected_with_400(self):
        """
        A topic_id from Course 2 (e.g. Topic 1 Stack Basics) sent with Course 4 (CS302)
        MUST be rejected with HTTP 400.
        A topic_id from Course 4 (e.g. Topic 25 Relational Model) sent with Course 2 (CS201)
        MUST be rejected with HTTP 400.
        """
        # 1. /api/progress/questions with mismatched topic
        res = client.get("/api/progress/questions?course_id=4&topic_id=1", headers=self.auth_headers)
        self.assertEqual(res.status_code, 400)
        self.assertIn("does not belong to course", res.json()["detail"])

        res2 = client.get("/api/progress/questions?course_id=2&topic_id=25", headers=self.auth_headers)
        self.assertEqual(res2.status_code, 400)
        self.assertIn("does not belong to course", res2.json()["detail"])

        # 2. /api/progress/submit-assessment with mismatched topic
        res_submit1 = client.post(
            "/api/progress/submit-assessment",
            json={
                "course_id": 4,
                "attempt_type": "practice",
                "topic_id": 1, # Belongs to course 2
                "answers": {"1": "Some Option"}
            },
            headers=self.auth_headers
        )
        self.assertEqual(res_submit1.status_code, 400)
        self.assertIn("does not belong to course", res_submit1.json()["detail"])

        res_submit2 = client.post(
            "/api/progress/submit-assessment",
            json={
                "course_id": 2,
                "attempt_type": "practice",
                "topic_id": 25, # Belongs to course 4
                "answers": {"101": "Some Option"}
            },
            headers=self.auth_headers
        )
        self.assertEqual(res_submit2.status_code, 400)
        self.assertIn("does not belong to course", res_submit2.json()["detail"])

        # 3. /api/assessment/coding-challenge with mismatched topic
        res_cc = client.get("/api/assessment/coding-challenge?course_id=4&topic_id=1", headers=self.auth_headers)
        self.assertEqual(res_cc.status_code, 400)
        self.assertIn("does not belong to course", res_cc.json()["detail"])

    def test_diagnostic_submit_cross_course_rejection(self):
        """
        Submitting diagnostic answers for questions belonging to a different course
        must be rejected with 400.
        """
        # Question 1 belongs to course 2 (or course 1 depending on seed)
        q1 = self.db.query(DiagnosticQuestion).filter(DiagnosticQuestion.course_id == 2).first()
        self.assertIsNotNone(q1)

        # Attempt to submit q1 against course 4
        res = client.post(
            "/api/diagnostic/submit",
            json={
                "course_id": 4,
                "answers": [{"question_id": q1.id, "selected_answer": "Arbitrary"}]
            },
            headers=self.auth_headers
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("does not belong to course", res.json()["detail"])

    def test_switching_courses_back_and_forth_has_no_stale_data(self):
        """
        Switching A -> B -> A returns only the active course's questions at every step.
        """
        # 1. Start with Course 2 (CS201 Data Structures)
        res_a1 = client.get("/api/progress/questions?course_id=2&count=5", headers=self.auth_headers)
        self.assertEqual(res_a1.status_code, 200)
        for q in res_a1.json():
            self.assertEqual(q["course_id"], 2)

        # 2. Switch to Course 4 (CS302 DBMS)
        res_b = client.get("/api/progress/questions?course_id=4&count=5", headers=self.auth_headers)
        self.assertEqual(res_b.status_code, 200)
        for q in res_b.json():
            self.assertEqual(q["course_id"], 4)

        # 3. Switch back to Course 2 (CS201 Data Structures)
        res_a2 = client.get("/api/progress/questions?course_id=2&count=5", headers=self.auth_headers)
        self.assertEqual(res_a2.status_code, 200)
        for q in res_a2.json():
            self.assertEqual(q["course_id"], 2)

    def test_nonexistent_course_returns_404(self):
        """
        Nonexistent course ID returns 404 for diagnostic and adaptive questions.
        """
        res_diag = client.get("/api/diagnostic/9999", headers=self.auth_headers)
        self.assertEqual(res_diag.status_code, 404)

        res_q = client.get("/api/progress/questions?course_id=9999", headers=self.auth_headers)
        self.assertEqual(res_q.status_code, 404)


if __name__ == "__main__":
    unittest.main()
