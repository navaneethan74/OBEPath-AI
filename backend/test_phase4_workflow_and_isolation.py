import sys
import os
import unittest
import json
import uuid

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
from models import (
    User, StudentProfile, AssessmentAttempt, MasteryScore,
    LearningPath, LearningPathItem, CourseOutcome, Topic, QuestionBank
)
from code_runner import get_coding_challenge, execute_code_submission

client = TestClient(app)

class TestPhase4WorkflowAndIsolation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.unique_id = uuid.uuid4().hex[:8]
        cls.low_email = f"student.low.{cls.unique_id}@obe.edu"
        cls.high_email = f"student.high.{cls.unique_id}@obe.edu"
        cls.baseline_email = f"student.base.{cls.unique_id}@obe.edu"
        cls.low_pwd = "lowpassword123"
        cls.high_pwd = "highpassword123"

        from core.security import hash_password
        with SessionLocal() as db:
            base_u = User(
                email=cls.baseline_email,
                password_hash=hash_password("BasePassword123!"),
                full_name="Baseline Student",
                role="student"
            )
            db.add(base_u)
            db.flush()
            prof = db.query(StudentProfile).filter(StudentProfile.user_id == base_u.id).first()
            if not prof:
                db.add(StudentProfile(user_id=base_u.id, onboarding_completed=True))
            else:
                prof.onboarding_completed = True
            db.commit()

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    # --------------------------------------------------------------------------
    # 1. LOW-SCORE STUDENT WORKFLOW
    # --------------------------------------------------------------------------
    def test_01_low_score_student_complete_flow(self):
        print("\n==================================================================")
        print("PHASE 4 - TEST 1: Low-Score Student End-to-End Workflow")
        print("==================================================================")
        email = self.low_email
        password = self.low_pwd
        full_name = f"Low Learner {self.unique_id}"

        # Step 1: Register
        r = client.post("/api/auth/register", json={
            "email": email,
            "password": password,
            "full_name": full_name,
            "role": "student"
        })
        self.assertEqual(r.status_code, 200, f"Register failed: {r.text}")
        data = r.json()
        user_id = data["user"]["id"]
        token = data["token"]
        auth_headers = {"Authorization": f"Bearer {token}"}
        self.assertTrue(data["is_new_user"])
        self.assertFalse(data["onboarding_completed"])
        print(f"  [PASS] Low-score student registered: {full_name} (ID: {user_id})")

        # Step 2: Complete Onboarding & Course Selection (Course 2: Data Structures)
        r = client.put(f"/api/profile?user_id={user_id}", headers=auth_headers, json={
            "full_name": full_name,
            "program": "B.Tech Computer Science",
            "department": "Computer Science & Engineering",
            "semester": 4,
            "academic_level": "Undergraduate (Semester 4)",
            "current_level": "Beginner",
            "selected_course_id": 2,
            "prior_knowledge": "Zero programming fundamentals",
            "learning_goal": "Need foundational remediation in Data Structures",
            "daily_time_minutes": 45,
            "onboarding_completed": True
        })
        self.assertEqual(r.status_code, 200, f"Profile onboarding update failed: {r.text}")
        prof = r.json()
        self.assertEqual(prof["selected_course_id"], 2)
        self.assertTrue(prof["onboarding_completed"])
        print(f"  [PASS] Onboarding completed & Course 2 (Data Structures) selected and persisted")

        # Step 3: AI Skill Check / Adaptive Assessment with LOW SCORE
        r_q = client.get(f"/api/progress/questions?course_id=2&count=5&attempt_type=assessment&user_id={user_id}", headers=auth_headers)
        self.assertEqual(r_q.status_code, 200)
        questions = r_q.json()
        self.assertGreaterEqual(len(questions), 4)

        # Deliberately submit incorrect answers
        wrong_answers = {str(q["id"]): "INTENTIONALLY_INCORRECT_ANSWER" for q in questions}

        # Include coding challenge with deliberate syntax/logic error
        challenge = get_coding_challenge(course_id=2, topic_id=1)
        self.assertIsNotNone(challenge)
        failing_code = "def is_valid_parentheses(s: str) -> bool:\n    return 'invalid_syntax_error"

        compile_res = execute_code_submission(code=failing_code, test_cases=challenge["test_cases"], timeout_sec=2.0)
        self.assertFalse(compile_res["all_passed"])
        self.assertEqual(compile_res["passed_count"], 0)

        coding_sub = {
            "challenge_id": challenge["id"],
            "title": challenge["title"],
            "topic_id": challenge["topic_id"],
            "code": failing_code,
            "passed_count": compile_res["passed_count"],
            "total_count": compile_res["total_count"],
            "percentage": compile_res["percentage"],
            "all_passed": compile_res["all_passed"],
            "results": compile_res["results"],
            "execution_time_ms": compile_res["execution_time_ms"],
            "stdout": compile_res["stdout"],
            "stderr": compile_res["stderr"]
        }

        # Submit assessment attempt
        r_sub = client.post(f"/api/progress/submit-assessment?user_id={user_id}", headers=auth_headers, json={
            "course_id": 2,
            "attempt_type": "assessment",
            "answers": wrong_answers,
            "coding_submission": coding_sub
        })
        self.assertEqual(r_sub.status_code, 200, f"Assessment submission failed: {r_sub.text}")
        sub_data = r_sub.json()
        eval_res = sub_data["evaluation"]
        self.assertLessEqual(eval_res["score_percentage"], 30.0, "Score must be low for wrong answers")
        print(f"  [PASS] Low-score assessment evaluated: Score = {eval_res['score_percentage']}% (Passed: {eval_res['passed']})")

        # Step 4: Verify Assessment Attempt Saved in Database
        attempts = self.db.query(AssessmentAttempt).filter(
            AssessmentAttempt.user_id == user_id,
            AssessmentAttempt.course_id == 2
        ).all()
        self.assertGreaterEqual(len(attempts), 1)
        self.assertTrue(attempts[0].attempt_uuid.startswith("att-") or attempts[0].attempt_uuid.startswith("diag-"))
        print(f"  [PASS] Assessment attempt persisted in database with UUID '{attempts[0].attempt_uuid}'")

        # Step 5: Verify Central Student State (Low Mastery & Dependent Topic Locked)
        r_state = client.get(f"/api/progress/state?user_id={user_id}&course_id=2", headers=auth_headers)
        self.assertEqual(r_state.status_code, 200)
        state = r_state.json()
        self.assertLessEqual(state["overallMastery"], 45.0)
        self.assertEqual(state["masteredCount"], 0)

        # Check prerequisite locking: Topic 5 (Tree Traversal) requires Topic 3 (Recursion)
        topic5 = next((t for t in state["topicMastery"] if t["topic_id"] == 5), None)
        if topic5:
            self.assertTrue(topic5["is_locked"], "Tree Traversal must be locked when Recursion mastery < 60%")
            self.assertGreater(len(topic5["unsatisfied_prerequisites"]), 0)
            print(f"  [PASS] Dependent topic {topic5['title']} correctly LOCKED: {topic5['unsatisfied_prerequisites']}")

        # Step 6: Verify Learning Path Adapted with Remediation
        lp = state["learningPath"]
        self.assertIsNotNone(lp)
        self.assertGreater(len(lp["items"]), 0)
        print(f"  [PASS] Adapted Learning Path generated with {len(lp['items'])} items (Reason: '{lp['adaptation_reason'][:60]}...')")

        # Step 7: Test AI Tutor Pedagogical Response for Weak Student
        r_tutor = client.post(f"/api/ai-tutor/chat?user_id={user_id}", headers=auth_headers, json={
            "topic_id": 1,
            "course_id": 2,
            "message": "I am struggling to understand why stack uses LIFO.",
            "action": "explain_simply"
        })
        self.assertEqual(r_tutor.status_code, 200)
        tutor_data = r_tutor.json()
        safe_reply = tutor_data['reply'][:65].encode('ascii', 'replace').decode('ascii')
        print(f"  [PASS] AI Tutor provided adapted response ({tutor_data.get('model_used', 'Gemini')}): '{safe_reply}...'")

    # --------------------------------------------------------------------------
    # 2. HIGH-SCORE STUDENT WORKFLOW
    # --------------------------------------------------------------------------
    def test_02_high_score_student_complete_flow(self):
        print("\n==================================================================")
        print("PHASE 4 - TEST 2: High-Score Student End-to-End Workflow")
        print("==================================================================")
        email = self.high_email
        password = self.high_pwd
        full_name = f"High Achiever {self.unique_id}"

        # Step 1: Register
        r = client.post("/api/auth/register", json={
            "email": email,
            "password": password,
            "full_name": full_name,
            "role": "student"
        })
        self.assertEqual(r.status_code, 200)
        reg_data = r.json()
        user_id = reg_data["user"]["id"]
        high_headers = {"Authorization": f"Bearer {reg_data['token']}"}
        print(f"  [PASS] High-score student registered: {full_name} (ID: {user_id})")

        # Step 2: Onboarding & Course Selection (Course 2: Data Structures)
        r = client.put(f"/api/profile?user_id={user_id}", headers=high_headers, json={
            "full_name": full_name,
            "program": "B.Tech Computer Science",
            "department": "CSE",
            "semester": 4,
            "current_level": "Advanced",
            "selected_course_id": 2,
            "prior_knowledge": "Advanced algorithmic concepts",
            "learning_goal": "Fast-track mastery of Data Structures",
            "daily_time_minutes": 120,
            "onboarding_completed": True
        })
        self.assertEqual(r.status_code, 200)
        print(f"  [PASS] Onboarding completed & Course 2 selected")

        # Step 3: Fetch Questions and Submit 100% Correct Answers from QuestionBank
        r_q = client.get(f"/api/progress/questions?course_id=2&count=5&attempt_type=assessment&user_id={user_id}", headers=high_headers)
        self.assertEqual(r_q.status_code, 200)
        questions = r_q.json()

        correct_answers = {}
        for q in questions:
            qb_row = self.db.query(QuestionBank).filter(QuestionBank.id == q["id"]).first()
            if qb_row:
                correct_answers[str(q["id"])] = qb_row.correct_answer

        # Step 4: Execute Coding Challenge with REFERENCE SOLUTION (100% Pass)
        challenge = get_coding_challenge(course_id=2, topic_id=1)
        ref_code = challenge["reference_solution"]
        compile_res = execute_code_submission(code=ref_code, test_cases=challenge["test_cases"], timeout_sec=4.0)
        self.assertTrue(compile_res["all_passed"], f"Reference solution must pass all tests: {compile_res.get('stderr')}")
        self.assertEqual(compile_res["passed_count"], len(challenge["test_cases"]))

        coding_sub = {
            "challenge_id": challenge["id"],
            "title": challenge["title"],
            "topic_id": challenge["topic_id"],
            "code": ref_code,
            "passed_count": compile_res["passed_count"],
            "total_count": compile_res["total_count"],
            "percentage": compile_res["percentage"],
            "all_passed": compile_res["all_passed"],
            "results": compile_res["results"],
            "execution_time_ms": compile_res["execution_time_ms"],
            "stdout": compile_res["stdout"],
            "stderr": compile_res["stderr"]
        }

        # Submit Assessment
        r_sub = client.post(f"/api/progress/submit-assessment?user_id={user_id}", headers=high_headers, json={
            "course_id": 2,
            "attempt_type": "assessment",
            "answers": correct_answers,
            "coding_submission": coding_sub
        })
        self.assertEqual(r_sub.status_code, 200)
        eval_res = r_sub.json()["evaluation"]
        self.assertGreaterEqual(eval_res["score_percentage"], 80.0)
        self.assertTrue(eval_res["passed"])
        print(f"  [PASS] High-score assessment evaluated: Score = {eval_res['score_percentage']}% (Coding 100% Passed)")

        # Step 5: Simulate high mastery across prerequisite topic (Topic 3: Recursion = 85%)
        r_sim = client.post(f"/api/progress/simulate-activity?user_id={user_id}", headers=high_headers, json={
            "topic_id": 3,
            "score": 85.0,
            "activity_type": "diagnostic",
            "reason": "Passed recursion unit with distinction"
        })
        self.assertEqual(r_sim.status_code, 200)

        # Also simulate high mastery for Tree Basics (Topic 4 = 80%)
        client.post(f"/api/progress/simulate-activity?user_id={user_id}", headers=high_headers, json={
            "topic_id": 4,
            "score": 80.0,
            "activity_type": "diagnostic",
            "reason": "Passed tree basics with high distinction"
        })

        r_state = client.get(f"/api/progress/state?user_id={user_id}&course_id=2", headers=high_headers)
        state = r_state.json()

        # Check that Topic 5 (Tree Traversal) is UNLOCKED since Topic 3 >= 60%
        topic5 = next((t for t in state["topicMastery"] if t["topic_id"] == 5), None)
        if topic5:
            self.assertFalse(topic5["is_locked"], "Tree Traversal must be UNLOCKED when Recursion >= 60%")
            print(f"  [PASS] Prerequisite threshold satisfied: Topic 5 '{topic5['title']}' is UNLOCKED!")

        # Step 6: Verify Outcome Attainment Dashboard (CO Attainment Elevated)
        r_co = client.get(f"/api/mastery/outcomes?user_id={user_id}&course_id=2", headers=high_headers)
        self.assertEqual(r_co.status_code, 200)
        outcomes_data = r_co.json()
        self.assertGreater(outcomes_data["overall_attainment"], 20.0)
        print(f"  [PASS] Outcome Attainment verified: Overall OBE Attainment = {outcomes_data['overall_attainment']}%")

    # --------------------------------------------------------------------------
    # 3. STUDENT DATA ISOLATION & EXISTING DATA INTEGRITY
    # --------------------------------------------------------------------------
    def test_03_student_data_isolation_and_integrity(self):
        print("\n==================================================================")
        print("PHASE 4 - TEST 3: Student Data Isolation & Existing Data Integrity")
        print("==================================================================")
        # Verify baseline student exists and data remains intact
        base_user = self.db.query(User).filter(User.email == self.baseline_email).first()
        self.assertIsNotNone(base_user, "Baseline student must exist")
        self.assertEqual(base_user.email, self.baseline_email)

        prof1 = self.db.query(StudentProfile).filter(StudentProfile.user_id == base_user.id).first()
        self.assertIsNotNone(prof1)
        self.assertTrue(prof1.onboarding_completed)
        print(f"  [PASS] Baseline Student verified: Name='{base_user.full_name}', Email='{base_user.email}', Data intact")

        # Verify low-score student and high-score student have distinct mastery records
        low_user = self.db.query(User).filter(User.email == self.low_email).first()
        high_user = self.db.query(User).filter(User.email == self.high_email).first()

        self.assertIsNotNone(low_user, "Low user must exist")
        self.assertIsNotNone(high_user, "High user must exist")

        self.db.expire_all()
        m_low = self.db.query(MasteryScore).filter(MasteryScore.user_id == low_user.id, MasteryScore.topic_id == 3).first()
        m_high = self.db.query(MasteryScore).filter(MasteryScore.user_id == high_user.id, MasteryScore.topic_id == 3).first()
        self.assertNotEqual(m_low.overall_mastery, m_high.overall_mastery, "Low and High users must have isolated masteries")
        print(f"  [PASS] Data Isolation verified: Low User Topic 3 = {m_low.overall_mastery}%, High User Topic 3 = {m_high.overall_mastery}%")

    # --------------------------------------------------------------------------
    # 4. REFRESH & RELOGIN PERSISTENCE
    # --------------------------------------------------------------------------
    def test_04_refresh_and_relogin_persistence(self):
        print("\n==================================================================")
        print("PHASE 4 - TEST 4: Refresh & Relogin Session Persistence")
        print("==================================================================")
        low_email = self.low_email
        password = self.low_pwd

        # Relogin
        r_login = client.post("/api/auth/login", json={
            "email": low_email,
            "password": password
        })
        self.assertEqual(r_login.status_code, 200, f"Login failed for {low_email}")
        login_res = r_login.json()
        self.assertFalse(login_res["is_new_user"], "Returning user must have is_new_user = False")
        self.assertTrue(login_res["onboarding_completed"], "Returning user must have onboarding_completed = True")

        # Refresh / retrieve student state
        user_id = login_res["user"]["id"]
        relogin_headers = {"Authorization": f"Bearer {login_res['token']}"}
        r_state = client.get(f"/api/progress/state?user_id={user_id}&course_id=2", headers=relogin_headers)
        self.assertEqual(r_state.status_code, 200)
        state = r_state.json()
        self.assertEqual(state["enrolledCourse"]["id"], 2)
        print(f"  [PASS] Relogin for '{low_email}' restored state without routing back to onboarding")

    # --------------------------------------------------------------------------
    # 5. SECURITY & PROTECTED ROUTES
    # --------------------------------------------------------------------------
    def test_05_security_and_protected_routes(self):
        print("\n==================================================================")
        print("PHASE 4 - TEST 5: Security & Protected Routes")
        print("==================================================================")
        # 1. No auth header on /api/auth/me
        r1 = client.get("/api/auth/me")
        self.assertEqual(r1.status_code, 401, f"Expected 401, got {r1.status_code}")
        print("  [PASS] Missing authorization header correctly rejected with 401")

        # 2. Invalid auth token
        r2 = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid_malformed_token"})
        self.assertEqual(r2.status_code, 401)
        print("  [PASS] Invalid token correctly rejected with 401")

        # 3. Valid token
        valid_login = client.post("/api/auth/login", json={"email": self.low_email, "password": self.low_pwd})
        self.assertEqual(valid_login.status_code, 200)
        valid_token = valid_login.json()["token"]
        r3 = client.get("/api/auth/me", headers={"Authorization": f"Bearer {valid_token}"})
        self.assertEqual(r3.status_code, 200)
        self.assertEqual(r3.json()["email"], self.low_email)
        print("  [PASS] Valid token correctly authenticated with 200")

        # 4. Wrong password
        r4 = client.post("/api/auth/login", json={
            "email": self.low_email,
            "password": "incorrect_password_xyz"
        })
        self.assertEqual(r4.status_code, 401)
        print("  [PASS] Incorrect password correctly rejected with 401")

        # 5. Tutor status does not expose secret key
        r5 = client.get("/api/ai-tutor/status")
        self.assertEqual(r5.status_code, 200)
        tutor_stat = r5.json()
        self.assertIn("gemini_configured", tutor_stat)
        self.assertNotIn("api_key", tutor_stat)
        self.assertNotIn("GEMINI_API_KEY", str(tutor_stat))
        print("  [PASS] /api/ai-tutor/status reports gemini_configured=True without exposing secret key")

if __name__ == "__main__":
    unittest.main()
