import os
import json
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import (
    User, StudentProfile, Course, Topic, MasteryScore,
    LearningPath, LearningPathItem, AgentLog
)
from progress_engine import (
    get_central_student_state,
    select_adaptive_questions,
    record_assessment_attempt,
    update_topic_mastery,
    generate_adapted_learning_path,
    recalculate_course_outcomes
)
from core.security import get_current_user, resolve_target_user_id
from core.thresholds import TOPIC_MASTERY

router = APIRouter(prefix="/api/progress", tags=["progress"])

class AssessmentSubmissionRequest(BaseModel):
    course_id: int = 2
    attempt_type: str = "assessment" # diagnostic, quiz, practice, assessment, reassessment
    topic_id: Optional[int] = None
    answers: Dict[str, str] # question_id (as str) -> selected_answer
    coding_submission: Optional[Dict[str, Any]] = None # optional coding challenge compiler submission

class ActivitySimulationRequest(BaseModel):
    topic_id: int
    score: float
    activity_type: str = "practice" # practice, quiz, assessment, remedial
    reason: Optional[str] = None

class SeedDemoRequest(BaseModel):
    course_id: int = 2

@router.get("/state")
def get_student_state(
    user_id: Optional[int] = None,
    course_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns the single central persistent student state across all modules.
    """
    target_user_id = resolve_target_user_id(current_user, user_id)
    return get_central_student_state(db, user_id=target_user_id, course_id=course_id)

@router.get("/questions")
def get_adaptive_questions(
    user_id: Optional[int] = None,
    course_id: int = 2,
    topic_id: Optional[int] = None,
    count: int = 5,
    attempt_type: str = "assessment",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns adaptive questions from QuestionBank:
    - Never serves the exact same questions repeatedly.
    - Adjusts difficulty according to student mastery.
    - Prioritizes weak topics for comprehensive assessments.
    """
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail=f"Course {course_id} not found")

    if topic_id is not None:
        topic = db.query(Topic).filter(Topic.id == topic_id).first()
        if not topic:
            raise HTTPException(status_code=404, detail=f"Topic {topic_id} not found")
        if topic.course_id != course_id:
            raise HTTPException(
                status_code=400,
                detail=f"Topic {topic_id} does not belong to course {course_id}"
            )

    target_user_id = resolve_target_user_id(current_user, user_id)
    questions = select_adaptive_questions(
        db=db,
        user_id=target_user_id,
        course_id=course_id,
        topic_id=topic_id,
        count=count,
        attempt_type=attempt_type
    )
    return questions

@router.post("/submit-assessment")
def submit_assessment(
    payload: AssessmentSubmissionRequest,
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Evaluates answers, records unique AssessmentAttempt, logs QuestionAnswerHistory,
    updates mastery using activity-specific weights, and triggers closed-loop adaptation.
    """
    course = db.query(Course).filter(Course.id == payload.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail=f"Course {payload.course_id} not found")

    if payload.topic_id is not None:
        topic = db.query(Topic).filter(Topic.id == payload.topic_id).first()
        if not topic:
            raise HTTPException(status_code=404, detail=f"Topic {payload.topic_id} not found")
        if topic.course_id != payload.course_id:
            raise HTTPException(
                status_code=400,
                detail=f"Topic {payload.topic_id} does not belong to course {payload.course_id}"
            )

    target_user_id = resolve_target_user_id(current_user, user_id)
    eval_result = record_assessment_attempt(
        db=db,
        user_id=target_user_id,
        course_id=payload.course_id,
        attempt_type=payload.attempt_type,
        submitted_answers=payload.answers,
        topic_id=payload.topic_id,
        coding_submission=payload.coding_submission
    )

    state = eval_result.get("state") or get_central_student_state(db, user_id=target_user_id, course_id=payload.course_id)
    return {
        **eval_result,
        "evaluation": eval_result,
        "state": state
    }

@router.post("/simulate-activity")
def simulate_activity(
    payload: ActivitySimulationRequest,
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Simulates completing a practice/quiz/reassessment for a specific topic with a given score.
    Only available in development/testing. Returns 404 in production.
    """
    env_val = os.getenv("ENV", os.getenv("ENVIRONMENT", "development")).strip().lower()
    if env_val in ("production", "prod"):
        raise HTTPException(
            status_code=404,
            detail="Endpoint /api/progress/simulate-activity is disabled in production environment"
        )

    topic = db.query(Topic).filter(Topic.id == payload.topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail=f"Topic {payload.topic_id} not found")

    target_user_id = resolve_target_user_id(current_user, user_id)
    res = update_topic_mastery(
        db=db,
        user_id=target_user_id,
        topic_id=payload.topic_id,
        score=payload.score,
        activity_type=payload.activity_type,
        reason=payload.reason or f"{payload.activity_type.capitalize()} completed with score {payload.score}%"
    )

    topic = db.query(Topic).filter(Topic.id == payload.topic_id).first()
    log = AgentLog(
        user_id=target_user_id,
        agent_name="Progress Monitoring Agent",
        action=f"{payload.activity_type}_completed",
        message=f"{payload.activity_type.capitalize()} for '{topic.title if topic else ''}' completed ({payload.score}%). Mastery updated: {res['previous_mastery']}% -> {res['new_mastery']}% ({res['classification']})."
    )
    db.add(log)
    db.commit()

    state = get_central_student_state(db, user_id=target_user_id, course_id=topic.course_id if topic else 2)
    return {
        **res,
        "mastery_update": res,
        "state": state
    }

@router.post("/seed-demo-journey")
def seed_demo_journey(
    payload: SeedDemoRequest,
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Initializes student state with the exact initial diagnostic values from specification.
    """
    target_user_id = resolve_target_user_id(current_user, user_id)
    topics = db.query(Topic).filter(Topic.course_id == payload.course_id).order_by(Topic.order_index).all()
    if not topics:
        topics = db.query(Topic).order_by(Topic.order_index).all()

    demo_scores = {
        1: 80.0,
        2: 70.0,
        3: 30.0,
        4: 65.0,
        5: 35.0,
        6: 20.0,
        7: 25.0,
        8: 75.0
    }

    for t in topics:
        score = demo_scores.get(t.order_index, 50.0)
        m = db.query(MasteryScore).filter(
            MasteryScore.user_id == target_user_id,
            MasteryScore.topic_id == t.id
        ).first()
        if not m:
            m = MasteryScore(user_id=target_user_id, topic_id=t.id)
            db.add(m)
        m.diagnostic_score = score
        m.overall_mastery = score
        from progress_engine import classify_mastery
        m.classification = classify_mastery(score)
        m.quiz_score = score
        m.practice_score = score
        m.completion_score = 0.0

    profile = db.query(StudentProfile).filter(StudentProfile.user_id == target_user_id).first()
    if profile:
        profile.diagnostic_completed = True
        profile.selected_course_id = payload.course_id

    generate_adapted_learning_path(
        db, target_user_id, payload.course_id,
        "Generated from diagnostic baseline: Stack 80%, Queue 70%, Recursion 30%, Tree Traversal 35%, Complexity 75%."
    )
    recalculate_course_outcomes(db, target_user_id, payload.course_id)

    db.commit()
    return get_central_student_state(db, user_id=target_user_id, course_id=payload.course_id)
