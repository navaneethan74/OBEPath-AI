"""
Comprehensive Phase 3 Test Suite:
1. Every new coding challenge and all its test cases (reference solution 100% pass)
2. Course-to-challenge mapping
3. No cross-course challenge fallback
4. Course selection and persistence
5. Fresh student with no mastery history
6. Student with prerequisite mastery below the threshold
7. Student meeting the prerequisite threshold
8. Course switching and state synchronization
9. Learning Path and Topic Map (Knowledge Map) synchronization
"""
import sys
import os
import unittest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(__file__))

from main import app
from database import SessionLocal
from models import User, StudentProfile, Topic, TopicPrerequisite, MasteryScore
from code_runner import CODING_CHALLENGES, get_coding_challenge, execute_code_submission
from progress_engine import get_central_student_state, get_prerequisite_statuses

client = TestClient(app)

class TestPhase3CoverageAndLocking(unittest.TestCase):

    def setUp(self):
        self.db = SessionLocal()
        student = self.db.query(User).filter(User.email == "phase3_base_student@example.com").first()
        if not student:
            student = User(email="phase3_base_student@example.com", password_hash="dummy_hash_123", full_name="Phase 3 Student", role="student")
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
        from core.security import create_access_token
        self.auth_headers = {"Authorization": f"Bearer {create_access_token(student.id, 'student')}"}

    def tearDown(self):
        self.db.close()

    # --------------------------------------------------------------------------
    # 1. Every coding challenge and all its test cases
    # --------------------------------------------------------------------------
    def test_all_coding_challenges_and_test_cases(self):
        print("\n--- TEST 1: Validating All Coding Challenges & Test Cases ---")
        self.assertGreaterEqual(len(CODING_CHALLENGES), 32, "Must have at least 32 coding challenges (8 per course)")

        for c in CODING_CHALLENGES:
            cid = c["id"]
            ref_solution = c.get("reference_solution")
            test_cases = c.get("test_cases", [])
            self.assertTrue(ref_solution, f"Challenge {cid} must have a reference solution")
            self.assertGreater(len(test_cases), 0, f"Challenge {cid} must have test cases")

            res = execute_code_submission(code=ref_solution, test_cases=test_cases, timeout_sec=4.0)
            self.assertTrue(res["success"], f"Execution failed for {cid}: {res.get('stderr')}")
            self.assertTrue(res["all_passed"], f"Test cases failed for {cid}: {res.get('results')}")
            self.assertEqual(res["passed_count"], len(test_cases), f"Not all passed for {cid}")
            print(f"  [PASS] Challenge '{cid}' (Course {c.get('course_id')}, Topic {c.get('topic_id')}): {res['passed_count']}/{len(test_cases)} tests passed")

    # --------------------------------------------------------------------------
    # 2. Course-to-challenge mapping
    # --------------------------------------------------------------------------
    def test_course_to_challenge_mapping(self):
        print("\n--- TEST 2: Validating Course-to-Challenge Mapping ---")
        # Course 1: Topics 9..16
        for tid in range(9, 17):
            c = get_coding_challenge(course_id=1, topic_id=tid)
            self.assertIsNotNone(c, f"Course 1 Topic {tid} must have challenge")
            self.assertEqual(c["course_id"], 1)
            self.assertEqual(c["topic_id"], tid)

        # Course 2: Topics 1..8
        for tid in range(1, 9):
            c = get_coding_challenge(course_id=2, topic_id=tid)
            self.assertIsNotNone(c, f"Course 2 Topic {tid} must have challenge")
            self.assertEqual(c["course_id"], 2)
            self.assertEqual(c["topic_id"], tid)

        # Course 3: Topics 17..24
        for tid in range(17, 25):
            c = get_coding_challenge(course_id=3, topic_id=tid)
            self.assertIsNotNone(c, f"Course 3 Topic {tid} must have challenge")
            self.assertEqual(c["course_id"], 3)
            self.assertEqual(c["topic_id"], tid)

        # Course 4: Topics 25..32
        for tid in range(25, 33):
            c = get_coding_challenge(course_id=4, topic_id=tid)
            self.assertIsNotNone(c, f"Course 4 Topic {tid} must have challenge")
            self.assertEqual(c["course_id"], 4)
            self.assertEqual(c["topic_id"], tid)

        print("  [PASS] All 32 topics mapped accurately to challenges in their respective courses.")

    # --------------------------------------------------------------------------
    # 3. No cross-course challenge fallback
    # --------------------------------------------------------------------------
    def test_no_cross_course_challenge_fallback(self):
        print("\n--- TEST 3: Validating Prevention of Cross-Course Challenge Fallback ---")
        # Querying topic 1 (Course 2) while asking for Course 3 must NOT return Stack challenge
        c_ai_topic1 = get_coding_challenge(course_id=3, topic_id=1)
        self.assertIsNone(c_ai_topic1, "Course 3 with invalid topic 1 must return None, not Course 2 Stack")

        # Querying topic 1 (Course 2) while asking for Course 4 must NOT return Stack challenge
        c_db_topic1 = get_coding_challenge(course_id=4, topic_id=1)
        self.assertIsNone(c_db_topic1, "Course 4 with invalid topic 1 must return None, not Course 2 Stack")

        # Querying non-existent topic 999 must return None
        c_invalid = get_coding_challenge(course_id=2, topic_id=999)
        self.assertIsNone(c_invalid, "Non-existent topic must return None")

        # API endpoint check
        resp = client.get("/api/assessment/coding-challenge?course_id=3&topic_id=1")
        data = resp.json()
        self.assertFalse(data.get("has_coding"), "API endpoint must return has_coding=False for invalid course/topic pair")

        print("  [PASS] Cross-course fallback successfully eliminated.")

    # --------------------------------------------------------------------------
    # 4. Course selection and persistence
    # --------------------------------------------------------------------------
    def test_course_selection_and_persistence(self):
        print("\n--- TEST 4: Validating Course Selection & Persistence ---")
        user_id = self.student_id

        # Select Course 3 (AI301)
        res_put = client.put(f"/api/profile?user_id={user_id}", json={"selected_course_id": 3}, headers=self.auth_headers)
        self.assertEqual(res_put.status_code, 200)
        self.assertEqual(res_put.json()["selected_course_id"], 3)

        # Verify profile GET persistence
        res_get = client.get(f"/api/profile?user_id={user_id}", headers=self.auth_headers)
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.json()["selected_course_id"], 3)

        # Verify Central Student State defaults to selected_course_id when course_id is not passed
        res_state = client.get(f"/api/progress/state?user_id={user_id}", headers=self.auth_headers)
        self.assertEqual(res_state.status_code, 200)
        state_data = res_state.json()
        self.assertEqual(state_data["enrolledCourse"]["id"], 3)
        self.assertEqual(state_data["enrolledCourse"]["code"], "AI301")

        # Switch to Course 4 (CS302)
        res_put4 = client.put(f"/api/profile?user_id={user_id}", json={"selected_course_id": 4}, headers=self.auth_headers)
        self.assertEqual(res_put4.status_code, 200)
        self.assertEqual(res_put4.json()["selected_course_id"], 4)
        res_state4 = client.get(f"/api/progress/state?user_id={user_id}", headers=self.auth_headers)
        self.assertEqual(res_state4.status_code, 200)
        self.assertEqual(res_state4.json()["enrolledCourse"]["id"], 4)
        self.assertEqual(res_state4.json()["enrolledCourse"]["code"], "CS302")

        # Restore to Course 2 (CS201)
        client.put(f"/api/profile?user_id={user_id}", json={"selected_course_id": 2}, headers=self.auth_headers)
        print("  [PASS] Course selection persists to StudentProfile and drives central student state.")

    # --------------------------------------------------------------------------
    # 5. Fresh student with no mastery history
    # --------------------------------------------------------------------------
    def test_fresh_student_no_mastery_history(self):
        print("\n--- TEST 5: Validating Fresh Student Beginner Topic Access ---")
        fresh_user = self.db.query(User).filter(User.email == "phase3_fresh_student@example.com").first()
        if not fresh_user:
            fresh_user = User(email="phase3_fresh_student@example.com", password_hash="dummy_hash_123", full_name="Fresh Student", role="student")
            self.db.add(fresh_user)
            self.db.commit()
            self.db.refresh(fresh_user)
            prof = StudentProfile(user_id=fresh_user.id, selected_course_id=2)
            self.db.add(prof)
            self.db.commit()

        # Clean any mastery scores for this user
        self.db.query(MasteryScore).filter(MasteryScore.user_id == fresh_user.id).delete()
        self.db.commit()

        # Check all 4 courses for the fresh student
        course_beginner_topics = {
            1: [9],            # CS101: Topic 9 has no prereqs
            2: [1, 2, 3, 4],   # CS201: Topics 1..4 have no prereqs
            3: [17],           # AI301: Topic 17 has no prereqs
            4: [25]            # CS302: Topic 25 has no prereqs
        }

        for cid, expected_unlocked in course_beginner_topics.items():
            state = get_central_student_state(self.db, user_id=fresh_user.id, course_id=cid)
            tm_map = {t["topic_id"]: t for t in state["topicMastery"]}

            # Beginner topics must be unlocked
            for tid in expected_unlocked:
                self.assertFalse(tm_map[tid]["is_locked"], f"Course {cid} Topic {tid} must be unlocked for fresh student")
                self.assertEqual(len(tm_map[tid]["unsatisfied_prerequisites"]), 0)

            # Dependent topics must be locked with structured prerequisite details
            for t in state["topicMastery"]:
                if t["topic_id"] not in expected_unlocked:
                    self.assertTrue(t["is_locked"], f"Dependent Topic {t['topic_id']} must be locked for fresh student")
                    self.assertGreater(len(t["unsatisfied_prerequisites"]), 0)
                    self.assertIn("prerequisite_details", t)
                    self.assertGreater(len(t["prerequisite_details"]), 0)
                    p0 = t["prerequisite_details"][0]
                    self.assertIn("topic_id", p0)
                    self.assertIn("title", p0)
                    self.assertIn("required_mastery", p0)
                    self.assertIn("current_mastery", p0)
                    self.assertEqual(p0["current_mastery"], 0.0)
                    self.assertFalse(p0["is_satisfied"])

        print("  [PASS] Fresh student immediately accesses first eligible topics across all courses with zero prerequisites.")

    # --------------------------------------------------------------------------
    # 6. Student with prerequisite mastery below the threshold
    # --------------------------------------------------------------------------
    def test_student_prerequisite_below_threshold(self):
        print("\n--- TEST 6: Validating Prerequisite Below Threshold Locks Dependent Topic ---")
        fresh_user = self.db.query(User).filter(User.email == "phase3_fresh_student@example.com").first()
        if not fresh_user:
            fresh_user = User(email="phase3_fresh_student@example.com", password_hash="dummy_hash_123", full_name="Fresh Student", role="student")
            self.db.add(fresh_user)
            self.db.commit()
            self.db.refresh(fresh_user)

        # In Course 2, Tree Traversal (Topic 5) requires Recursion (Topic 3) >= 60% and Tree Basics (Topic 4) >= 60%
        # Set Topic 3 to 45% (below threshold) and Topic 4 to 80%
        self.db.query(MasteryScore).filter(MasteryScore.user_id == fresh_user.id).delete()
        self.db.add(MasteryScore(user_id=fresh_user.id, topic_id=3, overall_mastery=45.0))
        self.db.add(MasteryScore(user_id=fresh_user.id, topic_id=4, overall_mastery=80.0))
        self.db.commit()

        prereqs = get_prerequisite_statuses(self.db, user_id=fresh_user.id, course_id=2)
        topic5_status = prereqs[5]

        self.assertTrue(topic5_status["is_locked"], "Topic 5 must be locked when Topic 3 is 45%")
        self.assertEqual(len(topic5_status["unsatisfied"]), 1)
        self.assertIn("Recursion Fundamentals (45% < 60%)", topic5_status["unsatisfied"][0])

        details_map = {d["topic_id"]: d for d in topic5_status["prerequisite_details"]}
        self.assertFalse(details_map[3]["is_satisfied"])
        self.assertEqual(details_map[3]["current_mastery"], 45.0)
        self.assertTrue(details_map[4]["is_satisfied"])
        self.assertEqual(details_map[4]["current_mastery"], 80.0)

        print("  [PASS] Prerequisite below threshold (45% < 60%) correctly locks dependent topic and reports accurate mastery.")

    # --------------------------------------------------------------------------
    # 7. Student meeting the prerequisite threshold
    # --------------------------------------------------------------------------
    def test_student_prerequisite_meeting_threshold(self):
        print("\n--- TEST 7: Validating Prerequisite Meeting Threshold Unlocks Dependent Topic ---")
        fresh_user = self.db.query(User).filter(User.email == "phase3_fresh_student@example.com").first()
        if not fresh_user:
            fresh_user = User(email="phase3_fresh_student@example.com", password_hash="dummy_hash_123", full_name="Fresh Student", role="student")
            self.db.add(fresh_user)
            self.db.commit()
            self.db.refresh(fresh_user)

        # Set Topic 3 to 75% (>= 60%) and Topic 4 to 80%
        self.db.query(MasteryScore).filter(MasteryScore.user_id == fresh_user.id).delete()
        self.db.add(MasteryScore(user_id=fresh_user.id, topic_id=3, overall_mastery=75.0))
        self.db.add(MasteryScore(user_id=fresh_user.id, topic_id=4, overall_mastery=80.0))
        self.db.commit()

        prereqs = get_prerequisite_statuses(self.db, user_id=fresh_user.id, course_id=2)
        topic5_status = prereqs[5]

        self.assertFalse(topic5_status["is_locked"], "Topic 5 MUST unlock when Topic 3 reaches 75% and Topic 4 is 80%")
        self.assertEqual(len(topic5_status["unsatisfied"]), 0)

        details_map = {d["topic_id"]: d for d in topic5_status["prerequisite_details"]}
        self.assertTrue(details_map[3]["is_satisfied"])
        self.assertTrue(details_map[4]["is_satisfied"])

        print("  [PASS] Prerequisite meeting threshold (75% >= 60%) immediately unlocks dependent topic.")

    # --------------------------------------------------------------------------
    # 8. Course switching and state synchronization
    # --------------------------------------------------------------------------
    def test_course_switching_and_state_synchronization(self):
        print("\n--- TEST 8: Validating Course Switching & State Synchronization ---")
        user_id = self.student_id
        for cid, expected_code in [(1, "CS101"), (2, "CS201"), (3, "AI301"), (4, "CS302")]:
            res = client.get(f"/api/progress/state?user_id={user_id}&course_id={cid}", headers=self.auth_headers)
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data["enrolledCourse"]["id"], cid)
            self.assertEqual(data["enrolledCourse"]["code"], expected_code)
            self.assertEqual(len(data["topicMastery"]), 8)
            # Verify learning path items are generated and belong to this course
            self.assertGreater(len(data["learningPath"]["items"]), 0)
            course_topic_ids = {t["topic_id"] for t in data["topicMastery"]}
            for item in data["learningPath"]["items"]:
                self.assertIn(item["topic_id"], course_topic_ids)
            print(f"  [PASS] Course {cid} ({expected_code}) state synchronized: 8 topics, learning path generated.")

    # --------------------------------------------------------------------------
    # 9. Learning Path and Topic Map (Knowledge Map) synchronization
    # --------------------------------------------------------------------------
    def test_learning_path_and_knowledge_map_synchronization(self):
        print("\n--- TEST 9: Validating Learning Path & Knowledge Map Synchronization ---")
        user_id = self.student_id
        for cid in [1, 2, 3, 4]:
            kmap_res = client.get(f"/api/mastery/knowledge-map?user_id={user_id}&course_id={cid}", headers=self.auth_headers)
            self.assertEqual(kmap_res.status_code, 200)
            kmap = kmap_res.json()

            state_res = client.get(f"/api/progress/state?user_id={user_id}&course_id={cid}", headers=self.auth_headers)
            self.assertEqual(state_res.status_code, 200)
            state = state_res.json()

            # Number of nodes in knowledge map matches topicMastery count
            self.assertEqual(len(kmap["nodes"]), len(state["topicMastery"]))

            # Verify topics and prerequisites match
            kmap_topic_ids = {int(n["id"]) for n in kmap["nodes"]}
            state_topic_ids = {t["topic_id"] for t in state["topicMastery"]}
            self.assertEqual(kmap_topic_ids, state_topic_ids, f"Topic mismatch in course {cid}")

            print(f"  [PASS] Course {cid} Knowledge Map ({len(kmap['nodes'])} nodes, {len(kmap['edges'])} edges) synchronized with learning state.")

if __name__ == "__main__":
    unittest.main()
