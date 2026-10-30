import os
import sys

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, DEFAULT_DB_PATH
from models import User, Course, Topic, QuestionBank, MasteryScore, CourseOutcome, AssessmentAttempt, QuestionAnswerHistory, LearningPath, LearningPathItem
from progress_engine import (
    select_adaptive_questions,
    record_assessment_attempt,
    get_central_student_state,
    generate_adapted_learning_path,
    recalculate_course_outcomes
)

def run_tests():
    db = SessionLocal()
    try:
        course = db.query(Course).filter(Course.code == "CS201").first()
        assert course is not None, "Course CS201 must exist"
        course_id = course.id
        topic = db.query(Topic).filter(Topic.course_id == course_id, Topic.order_index == 1).first()
        assert topic is not None, "Topic 1 of CS201 must exist"
        topic_id = topic.id

        user = db.query(User).filter(User.role == "student").first()
        if not user:
            user = User(
                email="flow_student_isolated@obe.edu",
                full_name="Flow Student",
                password_hash="somehash",
                role="student"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        user_id = user.id

        print(f"Testing for student: {user.full_name} ({user.email}), Course: {course.title}, Topic: {topic.title}")

        # ----------------------------------------------------
        # TEST C: PREFER UNSEEN QUESTIONS & NO IMMEDIATE REPEAT
        # ----------------------------------------------------
        print("\n=== TEST C: QUESTION SELECTION & REPEAT AVOIDANCE ===")
        all_topic_q = db.query(QuestionBank).filter(QuestionBank.topic_id == topic_id).all()
        print(f"Total questions in question_bank for Topic {topic_id}: {len(all_topic_q)}")
        assert len(all_topic_q) >= 4, "Must have at least 4 questions for Topic 1"

        # Clear answer history for Topic 1 for clean test start
        topic_q_ids = [q.id for q in all_topic_q]
        db.query(QuestionAnswerHistory).filter(
            QuestionAnswerHistory.user_id == user_id,
            QuestionAnswerHistory.question_id.in_(topic_q_ids)
        ).delete(synchronize_session=False)
        db.commit()

        # Round 1: Fetch 3 questions
        q_round1 = select_adaptive_questions(db, user_id=user_id, course_id=course_id, topic_id=topic_id, count=3, attempt_type="practice")
        assert len(q_round1) == 3, f"Expected 3 questions, got {len(q_round1)}"
        r1_ids = [q["id"] for q in q_round1]
        print(f"Round 1 question IDs: {r1_ids}")

        # Verify metadata
        for q in q_round1:
            assert "explanation" in q, "Question must have explanation"
            assert "outcome_code" in q, "Question must have outcome_code"
            assert "correct_answer" not in q, "Question payload to client must NOT expose correct_answer"

        # Simulate answering Round 1
        r1_answers = {str(q["id"]): "Option A" for q in q_round1}
        res1 = record_assessment_attempt(
            db, user_id=user_id, course_id=course_id,
            topic_id=topic_id, attempt_type="practice",
            submitted_answers=r1_answers
        )
        print(f"Round 1 completed. Recorded attempt score: {res1['score']}/{res1['max_score']}")

        # Round 2: Fetch 2 questions. Should NOT repeat r1_ids if unseen questions exist!
        q_round2 = select_adaptive_questions(db, user_id=user_id, course_id=course_id, topic_id=topic_id, count=2, attempt_type="practice")
        r2_ids = [q["id"] for q in q_round2]
        print(f"Round 2 question IDs: {r2_ids}")
        for r2_id in r2_ids:
            assert r2_id not in r1_ids, f"Round 2 repeated question {r2_id} from Round 1 when unseen questions were available!"
        print("[PASS] TEST C Passed: Unseen questions prioritized, no immediate repetition!")

        # ----------------------------------------------------
        # TEST A: LOW SCORE FLOW
        # ----------------------------------------------------
        print("\n=== TEST A: LOW SCORE FLOW (< 60%) ===")
        # Fetch 4 questions for topic 2 (Queue Basics)
        t2_obj = db.query(Topic).filter(Topic.course_id == course_id, Topic.order_index == 2).first()
        t2_id = t2_obj.id if t2_obj else 2
        q_low = select_adaptive_questions(db, user_id=user_id, course_id=course_id, topic_id=t2_id, count=4, attempt_type="practice")
        # Intentionally give wrong answers to all except 1
        low_answers = {}
        for idx, q in enumerate(q_low):
            real_q = db.query(QuestionBank).filter(QuestionBank.id == q["id"]).first()
            if idx == 0:
                low_answers[str(q["id"])] = real_q.correct_answer # 1 correct
            else:
                # pick a wrong answer
                wrong_opt = [opt for opt in q["options"] if opt != real_q.correct_answer][0]
                low_answers[str(q["id"])] = wrong_opt

        res_low = record_assessment_attempt(
            db, user_id=user_id, course_id=course_id,
            topic_id=t2_id, attempt_type="practice",
            submitted_answers=low_answers
        )
        print(f"Low score attempt: {res_low['score']}/{res_low['max_score']} ({res_low['percentage']}%)")
        assert res_low["percentage"] == 25.0, f"Expected 25.0%, got {res_low['percentage']}"
        assert res_low["score"] == 1
        assert res_low["max_score"] == 4
        assert res_low["passed"] == False, "Score < 60% must have passed=False"
        assert len(res_low["weak_sub_concepts"]) > 0, "Must identify weak sub-concepts"
        assert res_low["primary_mastery"] is not None
        print(f"Primary topic mastery: prev={res_low['primary_mastery']['previous_mastery']}, new={res_low['primary_mastery']['new_mastery']}, classification={res_low['primary_mastery']['classification']}")
        assert res_low['primary_mastery']['classification'] in ["BEGINNER", "DEVELOPING", "NEEDS PRACTICE", "WEAK", "Remedial Needed"], "Low score should keep classification developing or beginner"
        print("[PASS] TEST A Passed: Low score accurately calculated, weak sub-concepts identified, passed=False!")

        # ----------------------------------------------------
        # TEST B: HIGH SCORE FLOW
        # ----------------------------------------------------
        print("\n=== TEST B: HIGH SCORE FLOW (>= 60%) ===")
        # Answer all 4 questions correctly for Topic 1
        q_high = select_adaptive_questions(db, user_id=user_id, course_id=course_id, topic_id=topic_id, count=4, attempt_type="practice")
        high_answers = {}
        for q in q_high:
            real_q = db.query(QuestionBank).filter(QuestionBank.id == q["id"]).first()
            high_answers[str(q["id"])] = real_q.correct_answer

        res_high = record_assessment_attempt(
            db, user_id=user_id, course_id=course_id,
            topic_id=topic_id, attempt_type="practice",
            submitted_answers=high_answers
        )
        print(f"High score attempt: {res_high['score']}/{res_high['max_score']} ({res_high['percentage']}%)")
        assert res_high["percentage"] == 100.0, f"Expected 100%, got {res_high['percentage']}"
        assert res_high["score"] == 4
        assert res_high["passed"] == True, "Score 100% must have passed=True"
        assert res_high["primary_mastery"]["new_mastery"] > res_high["primary_mastery"]["previous_mastery"], "Mastery must increase on 100% score"
        print(f"Topic 1 mastery increased: {res_high['primary_mastery']['previous_mastery']} -> {res_high['primary_mastery']['new_mastery']}")

        # Verify prerequisite check & learning path
        state_after_high = get_central_student_state(db, user_id, course_id)
        assert state_after_high["learningPath"] is not None
        print(f"Learning path status: {state_after_high['learningPath']['status']}")
        print("[PASS] TEST B Passed: High score increased mastery, evaluated prerequisites, updated learning path!")

        # ----------------------------------------------------
        # TEST D: AI TUTOR TEST ME FLOW
        # ----------------------------------------------------
        print("\n=== TEST D: AI TUTOR TEST ME (3 QUESTIONS) ===")
        q_tutor = select_adaptive_questions(db, user_id=user_id, course_id=course_id, topic_id=topic_id, count=3, attempt_type="practice")
        assert len(q_tutor) == 3, f"Expected 3 questions for mini test-me, got {len(q_tutor)}"
        tutor_answers = {}
        for idx, q in enumerate(q_tutor):
            real_q = db.query(QuestionBank).filter(QuestionBank.id == q["id"]).first()
            # 2 correct, 1 wrong = 66.7%
            if idx < 2:
                tutor_answers[str(q["id"])] = real_q.correct_answer
            else:
                wrong_opt = [opt for opt in q["options"] if opt != real_q.correct_answer][0]
                tutor_answers[str(q["id"])] = wrong_opt

        res_tutor = record_assessment_attempt(
            db, user_id=user_id, course_id=course_id,
            topic_id=topic_id, attempt_type="practice",
            submitted_answers=tutor_answers
        )
        print(f"Test Me attempt: {res_tutor['score']}/{res_tutor['max_score']} ({res_tutor['percentage']}%)")
        assert res_tutor["score"] == 2
        assert res_tutor["max_score"] == 3
        assert res_tutor["percentage"] == 66.7
        assert len(res_tutor["question_details"]) == 3
        # Check details include explanations
        for d in res_tutor["question_details"]:
            assert "explanation" in d and len(d["explanation"]) > 0, "Details must include explanation"
        print("[PASS] TEST D Passed: AI Tutor Test Me 3-question mini assessment evaluated with explanations and progress recorded!")

        # ----------------------------------------------------
        # TEST E: REFRESH / PERSISTENCE IN SQLITE
        # ----------------------------------------------------
        print("\n=== TEST E: REFRESH / PERSISTENCE IN SQLITE ===")
        # Re-open a fresh DB session
        db.close()
        db2 = SessionLocal()
        state_refreshed = get_central_student_state(db2, user_id, course_id)
        assert state_refreshed["overallProgress"] is not None
        assert len(state_refreshed["topicMastery"]) > 0
        topic1_meta = [tm for tm in state_refreshed["topicMastery"] if tm["topic_id"] == topic_id][0]
        print(f"Persisted Topic 1 Mastery in DB: {topic1_meta['mastery']}%, Classification: {topic1_meta['classification']}")
        assert topic1_meta["mastery"] == res_tutor["primary_mastery"]["new_mastery"], "Mastery must persist exactly across sessions!"
        db2.close()
        print("[PASS] TEST E Passed: State persists across sessions in SQLite database!")

        print("\n==============================================")
        print("ALL TESTS (A, B, C, D, E) PASSED SUCCESSFULLY!")
        print("==============================================")

    finally:
        db.close()

if __name__ == "__main__":
    run_tests()
