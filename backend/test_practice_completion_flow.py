"""
test_practice_completion_flow.py
Tests for the practice/adaptive assessment completion flow (Step D).

Covers:
1. Passing practice completes topic, overall_mastery >= score, completion_score = 100.
2. Next topic unlocked and assigned CURRENT.
3. COs recalculated once per submission.
4. Failing practice keeps topic CURRENT.
5. Response contains next_topic, pass_mark, and full payload.
6. No duplicate history rows on repeated submits.
7. Completed topic remains re-openable; complete endpoint returns 409 cleanly.
8. Locked topic submit rejected with 403.
9. Cannot submit for another user (403).
10. Passing the last topic sets course_completed = True.
11. Safe backfill handles old passed attempts without duplicates.
"""

import os
import sys
import uuid
import json
import pytest

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
from models import (
    User, Course, Topic, TopicPrerequisite, MasteryScore, LearningPath,
    LearningPathItem, AssessmentAttempt, QuestionBank, StudentProfile,
    MasteryHistory, OutcomeAttainmentHistory
)
from core.security import create_access_token, hash_password
from core.thresholds import ASSESSMENT_PASS, PREREQ_UNLOCK, TOPIC_MASTERY

client = TestClient(app)

def create_test_student(course_id=1):
    db = SessionLocal()
    try:
        email = f"student_{uuid.uuid4().hex[:8]}@obe.edu"
        user = User(
            email=email,
            full_name="Test Flow Student",
            role="student",
            password_hash=hash_password("demo123")
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        profile = StudentProfile(user_id=user.id, selected_course_id=course_id, onboarding_completed=True)
        db.add(profile)
        db.commit()

        token = create_access_token(user.id, "student")
        headers = {"Authorization": f"Bearer {token}"}
        return user.id, headers
    finally:
        db.close()


def test_passing_practice_completes_topic_and_unlocks_next():
    user_id, headers = create_test_student(course_id=1)
    db = SessionLocal()
    try:
        topics = db.query(Topic).filter(Topic.course_id == 1).order_by(Topic.order_index).all()
        t1, t2 = topics[0], topics[1]

        # Fetch questions for topic 1
        q_objs = db.query(QuestionBank).filter(QuestionBank.topic_id == t1.id).limit(3).all()
        assert len(q_objs) > 0, "QuestionBank needs questions for topic 1"
        answers = {str(q.id): q.correct_answer for q in q_objs}

        payload = {
            "course_id": 1,
            "topic_id": t1.id,
            "attempt_type": "practice",
            "answers": answers
        }

        resp = client.post("/api/progress/submit-assessment", headers=headers, json=payload)
        assert resp.status_code == 200
        data = resp.json()

        # Step B Rule 5 assertions on response
        assert data["passed"] is True
        assert data["percentage"] == 100.0
        assert data["pass_mark"] == float(ASSESSMENT_PASS)
        assert data["topic_status"] == "COMPLETED"
        assert data["new_mastery"] >= 100.0
        assert "score" in data
        assert "per_question_results" in data
        assert data["next_topic"] is not None
        assert data["next_topic"]["id"] == t2.id
        assert data["next_topic"]["status"] == "CURRENT"

        # Database assertions: Rule 2
        m1 = db.query(MasteryScore).filter(
            MasteryScore.user_id == user_id,
            MasteryScore.topic_id == t1.id
        ).first()
        assert m1 is not None
        assert m1.completion_score == 100.0
        assert m1.overall_mastery >= 100.0

        # Learning path items check
        active_lp = db.query(LearningPath).filter(
            LearningPath.user_id == user_id,
            LearningPath.course_id == 1,
            LearningPath.status == "ACTIVE"
        ).order_by(LearningPath.id.desc()).first()
        assert active_lp is not None

        lp_items = db.query(LearningPathItem).filter(
            LearningPathItem.learning_path_id == active_lp.id
        ).all()
        item_map = {item.topic_id: item.status for item in lp_items}

        assert item_map[t1.id] == "COMPLETED"
        assert item_map[t2.id] == "CURRENT"
    finally:
        db.close()


def test_co_recalculated_once():
    user_id, headers = create_test_student(course_id=1)
    db = SessionLocal()
    try:
        topics = db.query(Topic).filter(Topic.course_id == 1).order_by(Topic.order_index).all()
        t1 = topics[0]

        q_objs = db.query(QuestionBank).filter(QuestionBank.topic_id == t1.id).limit(2).all()
        answers = {str(q.id): q.correct_answer for q in q_objs}

        history_count_before = db.query(OutcomeAttainmentHistory).filter(
            OutcomeAttainmentHistory.user_id == user_id
        ).count()

        payload = {
            "course_id": 1,
            "topic_id": t1.id,
            "attempt_type": "practice",
            "answers": answers
        }
        resp = client.post("/api/progress/submit-assessment", headers=headers, json=payload)
        assert resp.status_code == 200

        history_count_after = db.query(OutcomeAttainmentHistory).filter(
            OutcomeAttainmentHistory.user_id == user_id
        ).count()

        # Outcome attainment history snapshot recorded
        assert history_count_after > history_count_before
        # Ensure no duplicates per CO for this single trigger
        recent_records = db.query(OutcomeAttainmentHistory).filter(
            OutcomeAttainmentHistory.user_id == user_id
        ).all()
        co_counts = {}
        for r in recent_records:
            co_counts[r.outcome_id] = co_counts.get(r.outcome_id, 0) + 1
        for co_id, count in co_counts.items():
            assert count == 1, f"CO {co_id} had duplicate history rows: {count}"
    finally:
        db.close()


def test_failing_practice_keeps_topic_current():
    user_id, headers = create_test_student(course_id=1)
    db = SessionLocal()
    try:
        topics = db.query(Topic).filter(Topic.course_id == 1).order_by(Topic.order_index).all()
        t1, t2 = topics[0], topics[1]

        q_objs = db.query(QuestionBank).filter(QuestionBank.topic_id == t1.id).limit(3).all()
        # Provide deliberately wrong answers
        answers = {str(q.id): "WRONG_ANSWER_XYZ" for q in q_objs}

        payload = {
            "course_id": 1,
            "topic_id": t1.id,
            "attempt_type": "practice",
            "answers": answers
        }

        resp = client.post("/api/progress/submit-assessment", headers=headers, json=payload)
        assert resp.status_code == 200
        data = resp.json()

        # Step B Rule 3 assertions
        assert data["passed"] is False
        assert data["percentage"] == 0.0
        assert data["topic_status"] == "CURRENT"

        m1 = db.query(MasteryScore).filter(
            MasteryScore.user_id == user_id,
            MasteryScore.topic_id == t1.id
        ).first()
        assert m1 is not None
        assert (m1.completion_score or 0.0) == 0.0

        # Topic 1 remains CURRENT, Topic 2 remains LOCKED
        active_lp = db.query(LearningPath).filter(
            LearningPath.user_id == user_id,
            LearningPath.course_id == 1,
            LearningPath.status == "ACTIVE"
        ).order_by(LearningPath.id.desc()).first()
        lp_items = db.query(LearningPathItem).filter(
            LearningPathItem.learning_path_id == active_lp.id
        ).all()
        item_map = {item.topic_id: item.status for item in lp_items}

        assert item_map[t1.id] == "CURRENT"
        assert item_map[t2.id] == "LOCKED"
    finally:
        db.close()


def test_no_duplicate_history_on_repeated_submits():
    user_id, headers = create_test_student(course_id=1)
    db = SessionLocal()
    try:
        t1 = db.query(Topic).filter(Topic.course_id == 1, Topic.order_index == 1).first()
        q_objs = db.query(QuestionBank).filter(QuestionBank.topic_id == t1.id).limit(2).all()
        answers = {str(q.id): q.correct_answer for q in q_objs}
        payload = {
            "course_id": 1,
            "topic_id": t1.id,
            "attempt_type": "practice",
            "answers": answers
        }

        # First submit
        resp1 = client.post("/api/progress/submit-assessment", headers=headers, json=payload)
        assert resp1.status_code == 200
        count1 = db.query(MasteryHistory).filter(
            MasteryHistory.user_id == user_id,
            MasteryHistory.topic_id == t1.id
        ).count()
        assert count1 == 1

        # Second submit
        resp2 = client.post("/api/progress/submit-assessment", headers=headers, json=payload)
        assert resp2.status_code == 200
        count2 = db.query(MasteryHistory).filter(
            MasteryHistory.user_id == user_id,
            MasteryHistory.topic_id == t1.id
        ).count()
        # Exactly one history row added per assessment submit attempt
        assert count2 == 2
    finally:
        db.close()


def test_completed_topic_reopenable_and_clean_409():
    user_id, headers = create_test_student(course_id=1)
    db = SessionLocal()
    try:
        t1 = db.query(Topic).filter(Topic.course_id == 1, Topic.order_index == 1).first()
        q_objs = db.query(QuestionBank).filter(QuestionBank.topic_id == t1.id).limit(2).all()
        answers = {str(q.id): q.correct_answer for q in q_objs}
        payload = {
            "course_id": 1,
            "topic_id": t1.id,
            "attempt_type": "practice",
            "answers": answers
        }
        resp = client.post("/api/progress/submit-assessment", headers=headers, json=payload)
        assert resp.status_code == 200

        # Topic is completed. Re-calling /complete/{topic_id} must return 409 cleanly
        resp_comp = client.post(f"/api/assessment/topic/complete/{t1.id}", headers=headers)
        assert resp_comp.status_code == 409
        assert "already completed" in resp_comp.json()["detail"].lower()

        # Verify topic remains openable for review in central student state
        resp_state = client.get("/api/progress/state", headers=headers)
        assert resp_state.status_code == 200
        state = resp_state.json()
        tm = next((t for t in state["topicMastery"] if t["topic_id"] == t1.id), None)
        assert tm is not None
        assert tm["status"] == "COMPLETED"
        assert tm["is_locked"] is False
    finally:
        db.close()


def test_locked_topic_submit_rejected_with_403():
    user_id, headers = create_test_student(course_id=1)
    db = SessionLocal()
    try:
        # Topic 2 requires Topic 1 (mastery 0% < PREREQ_UNLOCK 60%)
        t2 = db.query(Topic).filter(Topic.course_id == 1, Topic.order_index == 2).first()
        q_objs = db.query(QuestionBank).filter(QuestionBank.topic_id == t2.id).limit(2).all()
        assert len(q_objs) > 0
        answers = {str(q.id): q.correct_answer for q in q_objs}

        payload = {
            "course_id": 1,
            "topic_id": t2.id,
            "attempt_type": "practice",
            "answers": answers
        }
        resp = client.post("/api/progress/submit-assessment", headers=headers, json=payload)
        assert resp.status_code == 403
        assert "locked" in resp.json()["detail"].lower()
    finally:
        db.close()


def test_cannot_submit_for_another_user_403():
    user1_id, headers1 = create_test_student(course_id=1)
    user2_id, headers2 = create_test_student(course_id=1)
    db = SessionLocal()
    try:
        t1 = db.query(Topic).filter(Topic.course_id == 1, Topic.order_index == 1).first()
        q_objs = db.query(QuestionBank).filter(QuestionBank.topic_id == t1.id).limit(2).all()
        answers = {str(q.id): q.correct_answer for q in q_objs}

        payload = {
            "course_id": 1,
            "topic_id": t1.id,
            "attempt_type": "practice",
            "answers": answers
        }
        # Student 1 attempts to submit on behalf of Student 2
        resp = client.post(f"/api/progress/submit-assessment?user_id={user2_id}", headers=headers1, json=payload)
        assert resp.status_code == 403
    finally:
        db.close()


def test_passing_last_topic_sets_course_completed():
    user_id, headers = create_test_student(course_id=1)
    db = SessionLocal()
    try:
        topics = db.query(Topic).filter(Topic.course_id == 1).order_by(Topic.order_index).all()
        # Complete all topics except the last one
        for t in topics[:-1]:
            m = MasteryScore(
                user_id=user_id,
                topic_id=t.id,
                diagnostic_score=90.0,
                quiz_score=90.0,
                practice_score=90.0,
                completion_score=100.0,
                overall_mastery=90.0
            )
            db.add(m)
        db.commit()

        # Submit passing practice for the last topic
        last_t = topics[-1]
        q_objs = db.query(QuestionBank).filter(QuestionBank.topic_id == last_t.id).limit(2).all()
        if not q_objs:
            # Fallback to any questions if none for last topic
            q_objs = db.query(QuestionBank).limit(2).all()
        answers = {str(q.id): q.correct_answer for q in q_objs}

        payload = {
            "course_id": 1,
            "topic_id": last_t.id,
            "attempt_type": "practice",
            "answers": answers
        }
        resp = client.post("/api/progress/submit-assessment", headers=headers, json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["course_completed"] is True
    finally:
        db.close()


def test_safe_backfill_for_old_passed_attempts():
    user_id, headers = create_test_student(course_id=1)
    db = SessionLocal()
    try:
        t1 = db.query(Topic).filter(Topic.course_id == 1, Topic.order_index == 1).first()
        # Create an old passed attempt with no completion_score
        old_att = AssessmentAttempt(
            attempt_uuid=f"old-{uuid.uuid4().hex[:8]}",
            user_id=user_id,
            course_id=1,
            topic_id=t1.id,
            attempt_type="practice",
            score=5,
            max_score=5,
            percentage=85.0,
            passed=True
        )
        db.add(old_att)
        # MasteryScore with incomplete status
        m = MasteryScore(
            user_id=user_id,
            topic_id=t1.id,
            overall_mastery=30.0,
            completion_score=0.0
        )
        db.add(m)
        db.commit()

        history_count_before = db.query(MasteryHistory).filter(MasteryHistory.user_id == user_id).count()

        # Call get state, which triggers safe backfill
        resp = client.get("/api/progress/state", headers=headers)
        assert resp.status_code == 200

        # Verify backfill updated completion_score and overall_mastery
        db.refresh(m)
        assert m.completion_score == 100.0
        assert m.overall_mastery >= 85.0

        # Verify no duplicate history records were written
        history_count_after = db.query(MasteryHistory).filter(MasteryHistory.user_id == user_id).count()
        assert history_count_after == history_count_before
    finally:
        db.close()
