"""
test_reproduce_practice_flow.py
Reproduction test for practice/adaptive assessment completion flow.

Reproduces:
(1) Topic not marked completed, mastery stays at ~28-29% despite passing score.
(2) Response lacks pass_mark and next_topic structure.
(3) Dependent topics remain LOCKED; learning path item is not COMPLETED.
"""

import os
import sys
import uuid
from datetime import datetime

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
from models import (
    User, Course, Topic, MasteryScore, LearningPath, LearningPathItem,
    AssessmentAttempt, QuestionBank, StudentProfile
)
from core.security import create_access_token, hash_password
from core.thresholds import ASSESSMENT_PASS, PREREQ_UNLOCK

client = TestClient(app)

def run_reproduction():
    db = SessionLocal()
    try:
        # 1. Create a fresh test student
        test_email = f"repro_{uuid.uuid4().hex[:8]}@obe.edu"
        user = User(
            email=test_email,
            full_name="Repro Student",
            role="student",
            password_hash=hash_password("demo123")
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        profile = StudentProfile(user_id=user.id, selected_course_id=1, onboarding_completed=True)
        db.add(profile)
        db.commit()

        token = create_access_token(user.id, "student")
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Finish diagnostic
        from models import DiagnosticQuestion
        diag_q_models = db.query(DiagnosticQuestion).filter(DiagnosticQuestion.course_id == 1).all()
        diag_answers = [{"question_id": q.id, "selected_answer": q.correct_answer} for q in diag_q_models]
        resp_diag = client.post("/api/diagnostic/submit", headers=headers, json={
            "course_id": 1,
            "answers": diag_answers
        })
        print(f"[REPRO] Diagnostic submit status: {resp_diag.status_code}")

        # Check initial mastery of Topic 1 (Variables, Data Types & Basic I/O)
        topic1 = db.query(Topic).filter(Topic.course_id == 1, Topic.order_index == 1).first()
        m_initial = db.query(MasteryScore).filter(
            MasteryScore.user_id == user.id,
            MasteryScore.topic_id == topic1.id
        ).first()
        print(f"[REPRO] Topic 1 initial mastery after diagnostic: {m_initial.overall_mastery if m_initial else 'None'}%")

        # Reset Topic 1 mastery to 0 to simulate starting from beginning
        if m_initial:
            m_initial.overall_mastery = 0.0
            m_initial.quiz_score = 0.0
            m_initial.practice_score = 0.0
            m_initial.completion_score = 0.0
            db.commit()

        # 3. Submit passing practice assessment for Topic 1 (score 80% or 100%)
        # Fetch 2 questions for Topic 1
        t1_questions = db.query(QuestionBank).filter(QuestionBank.topic_id == topic1.id).limit(3).all()
        practice_answers = {str(q.id): q.correct_answer for q in t1_questions}

        submit_payload = {
            "course_id": 1,
            "topic_id": topic1.id,
            "attempt_type": "practice",
            "answers": practice_answers
        }

        resp_submit = client.post(f"/api/progress/submit-assessment?user_id={user.id}", headers=headers, json=submit_payload)
        print(f"[REPRO] Practice submit status: {resp_submit.status_code}")
        submit_data = resp_submit.json()

        # Print attempt row
        attempt = db.query(AssessmentAttempt).filter(
            AssessmentAttempt.user_id == user.id,
            AssessmentAttempt.topic_id == topic1.id
        ).order_by(AssessmentAttempt.id.desc()).first()

        print(f"[REPRO] AssessmentAttempt row: id={attempt.id}, passed={attempt.passed}, percentage={attempt.percentage}%, attempt_type={attempt.attempt_type}")

        # Print mastery_scores
        m_after = db.query(MasteryScore).filter(
            MasteryScore.user_id == user.id,
            MasteryScore.topic_id == topic1.id
        ).first()
        print(f"[REPRO] Topic 1 MasteryScore: overall={m_after.overall_mastery}%, completion_score={m_after.completion_score}")

        # Print learning_path_items status
        active_lp = db.query(LearningPath).filter(
            LearningPath.user_id == user.id,
            LearningPath.course_id == 1,
            LearningPath.status == "ACTIVE"
        ).order_by(LearningPath.id.desc()).first()

        lp_items = db.query(LearningPathItem).filter(
            LearningPathItem.learning_path_id == active_lp.id
        ).order_by(LearningPathItem.sequence_order).all() if active_lp else []

        print("[REPRO] LearningPath items:")
        for item in lp_items:
            t = db.query(Topic).filter(Topic.id == item.topic_id).first()
            print(f"  Topic {item.topic_id} ({t.title if t else 'Unknown'}): status={item.status}")

        # Check response structure
        print(f"[REPRO] submit-assessment response keys: {list(submit_data.keys())}")
        print(f"[REPRO] evaluation keys: {list(submit_data.get('evaluation', {}).keys())}")
        print(f"[REPRO] Has 'pass_mark' in response? {'pass_mark' in submit_data or 'pass_mark' in submit_data.get('evaluation', {})}")
        print(f"[REPRO] Has 'next_topic' in response? {'next_topic' in submit_data or 'next_topic' in submit_data.get('evaluation', {})}")

    finally:
        db.close()

if __name__ == "__main__":
    run_reproduction()
