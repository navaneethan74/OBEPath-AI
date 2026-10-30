from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict
import json

from database import get_db
from models import (
    User, ClassModel, ClassEnrollment, Course, CourseOutcome,
    MasteryScore, OutcomeAttainment, Topic, AgentLog
)
from schemas import StudentPreviewRequest, StudentJoinRequest
from core.security import require_role
from core.thresholds import TOPIC_MASTERY

router = APIRouter(prefix="/api/student", tags=["student"])

CONSENT_TEXT = (
    "Joining this class lets your teacher see your current progress, scores, "
    "and learning path, including progress made before joining. "
    "You can leave the class at any time."
)

# In-memory rate limiter: user_id -> list of attempt timestamps
_rate_limit_records = defaultdict(list)
RATE_LIMIT_WINDOW = timedelta(minutes=10)
RATE_LIMIT_MAX_ATTEMPTS = 10

def check_rate_limit(user_id: int):
    now = datetime.utcnow()
    window_start = now - RATE_LIMIT_WINDOW
    # Keep only timestamps within window
    _rate_limit_records[user_id] = [
        ts for ts in _rate_limit_records[user_id] if ts >= window_start
    ]
    if len(_rate_limit_records[user_id]) >= RATE_LIMIT_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many class join or preview attempts. Please try again later."
        )
    _rate_limit_records[user_id].append(now)

def reset_rate_limits():
    """Helper for testing to reset rate limit counters."""
    _rate_limit_records.clear()

def get_valid_active_class(db: Session, class_code: str) -> ClassModel:
    cleaned_code = class_code.strip().upper()
    class_obj = db.query(ClassModel).filter(ClassModel.class_code == cleaned_code).first()
    if not class_obj or not class_obj.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or inactive class code"
        )
    if class_obj.expires_at and class_obj.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or inactive class code"
        )
    return class_obj

def capture_baseline_snapshot(db: Session, student_id: int, course_id: int):
    course_topics = db.query(Topic).filter(Topic.course_id == course_id).order_by(Topic.order_index).all()
    masteries = db.query(MasteryScore).filter(MasteryScore.user_id == student_id).all()
    m_map = {m.topic_id: m for m in masteries}

    baseline_completed_count = 0
    mastery_dict = {}
    for t in course_topics:
        m = m_map.get(t.id)
        is_completed = bool(m and (m.overall_mastery >= TOPIC_MASTERY or (m.completion_score or 0.0) >= 100.0))
        if is_completed:
            baseline_completed_count += 1
        mastery_dict[str(t.id)] = {
            "topic_id": t.id,
            "title": t.title,
            "overall_mastery": m.overall_mastery if m else 0.0,
            "diagnostic_score": m.diagnostic_score if m else 0.0,
            "quiz_score": m.quiz_score if m else 0.0,
            "practice_score": m.practice_score if m else 0.0,
            "completion_score": m.completion_score if m else 0.0,
            "completed": is_completed
        }

    course_outcomes = db.query(CourseOutcome).filter(CourseOutcome.course_id == course_id).order_by(CourseOutcome.code).all()
    attainments = db.query(OutcomeAttainment).filter(
        OutcomeAttainment.user_id == student_id,
        OutcomeAttainment.course_id == course_id
    ).all()
    oa_map = {oa.outcome_id: oa for oa in attainments}

    co_list = []
    for co in course_outcomes:
        oa = oa_map.get(co.id)
        co_list.append({
            "outcome_id": co.id,
            "code": co.code,
            "description": co.description,
            "attainment_percentage": oa.attainment_percentage if oa else 0.0,
            "status": oa.status if oa else "Not Started"
        })

    return json.dumps(mastery_dict), json.dumps(co_list), baseline_completed_count

@router.post("/classes/preview")
def preview_class(
    payload: StudentPreviewRequest,
    current_user: User = Depends(require_role("student")),
    db: Session = Depends(get_db)
):
    """
    Step D.13: Previews class information and consent text without enrolling.
    Generic 404 for invalid, inactive, or expired codes.
    Rate limited to prevent brute forcing.
    """
    check_rate_limit(current_user.id)
    class_obj = get_valid_active_class(db, payload.class_code)

    teacher_name = class_obj.faculty.full_name if class_obj.faculty else "Unknown Faculty"
    course_title = class_obj.course.title if class_obj.course else ""
    course_code = class_obj.course.code if class_obj.course else ""

    return {
        "class_id": class_obj.id,
        "class_name": class_obj.name,
        "class_code": class_obj.class_code,
        "course_id": class_obj.course_id,
        "course_title": course_title,
        "course_code": course_code,
        "teacher_name": teacher_name,
        "consent_text": CONSENT_TEXT
    }

@router.post("/classes/join")
def join_class(
    payload: StudentJoinRequest,
    current_user: User = Depends(require_role("student")),
    db: Session = Depends(get_db)
):
    """
    Step D.14: Enrolls student in class after validating consent and class status.
    Takes a baseline snapshot (topic mastery, CO attainment, completed topics count).
    Supports re-joining with a refreshed baseline.
    """
    check_rate_limit(current_user.id)

    if not payload.accept_consent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Consent must be accepted to join the class."
        )

    class_obj = get_valid_active_class(db, payload.class_code)

    # Capacity check: active enrollments
    active_count = db.query(ClassEnrollment).filter(
        ClassEnrollment.class_id == class_obj.id,
        ClassEnrollment.status == "active"
    ).count()

    if class_obj.max_students and active_count >= class_obj.max_students:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Class is full"
        )

    # Check existing enrollment
    enrollment = db.query(ClassEnrollment).filter(
        ClassEnrollment.class_id == class_obj.id,
        ClassEnrollment.student_id == current_user.id
    ).first()

    if enrollment and enrollment.status == "active":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already enrolled in this class"
        )

    baseline_mastery, baseline_co, baseline_completed = capture_baseline_snapshot(
        db, current_user.id, class_obj.course_id
    )
    now = datetime.utcnow()

    if enrollment:
        # Re-joining after leaving or being removed: reactivate with new baseline snapshot
        enrollment.status = "active"
        enrollment.joined_at = now
        enrollment.left_at = None
        enrollment.consent_accepted_at = now
        enrollment.baseline_mastery_json = baseline_mastery
        enrollment.baseline_co_json = baseline_co
        enrollment.baseline_completed_topics = baseline_completed
    else:
        enrollment = ClassEnrollment(
            class_id=class_obj.id,
            student_id=current_user.id,
            status="active",
            joined_at=now,
            left_at=None,
            consent_accepted_at=now,
            baseline_mastery_json=baseline_mastery,
            baseline_co_json=baseline_co,
            baseline_completed_topics=baseline_completed
        )
        db.add(enrollment)

    db.add(AgentLog(
        user_id=current_user.id,
        agent_name="Enrollment Service",
        action="class_joined",
        message=f"Student {current_user.id} joined class {class_obj.id} ({class_obj.name}) with baseline {baseline_completed} topics completed."
    ))

    from models import InterventionEvent
    db.add(InterventionEvent(
        student_id=current_user.id,
        class_id=class_obj.id,
        topic_id=None,
        type="class_joined",
        created_at=now,
        note=f"Joined class '{class_obj.name}'"
    ))

    db.commit()

    db.refresh(enrollment)

    teacher_name = class_obj.faculty.full_name if class_obj.faculty else "Unknown Faculty"
    course_title = class_obj.course.title if class_obj.course else ""

    return {
        "message": f"Successfully joined class '{class_obj.name}'.",
        "enrollment_id": enrollment.id,
        "class_id": class_obj.id,
        "class_name": class_obj.name,
        "course_title": course_title,
        "teacher_name": teacher_name,
        "baseline_completed_topics": baseline_completed,
        "joined_at": enrollment.joined_at.strftime("%Y-%m-%d %H:%M:%S")
    }

@router.get("/classes")
def list_student_classes(
    current_user: User = Depends(require_role("student")),
    db: Session = Depends(get_db)
):
    """
    Step D.16: Lists active classes that the student is currently enrolled in.
    """
    enrollments = db.query(ClassEnrollment).filter(
        ClassEnrollment.student_id == current_user.id,
        ClassEnrollment.status == "active"
    ).all()

    result = []
    for enr in enrollments:
        cls = enr.class_obj
        if not cls:
            continue
        teacher_name = cls.faculty.full_name if cls.faculty else "Unknown Faculty"
        course_title = cls.course.title if cls.course else ""
        course_code = cls.course.code if cls.course else ""
        result.append({
            "enrollment_id": enr.id,
            "class_id": cls.id,
            "name": cls.name,
            "class_code": cls.class_code,
            "course_id": cls.course_id,
            "course_title": course_title,
            "course_code": course_code,
            "teacher_name": teacher_name,
            "joined_at": enr.joined_at.strftime("%Y-%m-%d %H:%M:%S") if enr.joined_at else None,
            "baseline_completed_topics": enr.baseline_completed_topics
        })
    return result

@router.post("/classes/{class_id}/leave")
def leave_class(
    class_id: int,
    current_user: User = Depends(require_role("student")),
    db: Session = Depends(get_db)
):
    """
    Step D.16: Student leaves a class. Status changes to 'left'; faculty loses view access immediately.
    Student data is preserved.
    """
    enrollment = db.query(ClassEnrollment).filter(
        (ClassEnrollment.class_id == class_id) | (ClassEnrollment.id == class_id),
        ClassEnrollment.student_id == current_user.id,
        ClassEnrollment.status == "active"
    ).first()

    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active enrollment not found for this class."
        )

    enrollment.status = "left"
    enrollment.left_at = datetime.utcnow()

    db.add(AgentLog(
        user_id=current_user.id,
        agent_name="Enrollment Service",
        action="class_left",
        message=f"Student {current_user.id} left class {enrollment.class_id}."
    ))

    db.commit()

    return {
        "message": "Successfully left the class. Teacher access has been revoked.",
        "class_id": enrollment.class_id
    }

class AccountDeletionRequestPayload(BaseModel):
    reason: Optional[str] = None

@router.post("/account-deletion-request")
def request_account_deletion(
    payload: Optional[AccountDeletionRequestPayload] = None,
    current_user: User = Depends(require_role("student")),
    db: Session = Depends(get_db)
):
    """
    Step 18: Student submits an authenticated account deletion request.
    Creates an audit log record for administrator handling and returns confirmation.
    """
    reason_text = payload.reason.strip() if (payload and payload.reason) else "Requested by student"
    now = datetime.utcnow()

    db.add(AgentLog(
        user_id=current_user.id,
        agent_name="Student Privacy & Governance",
        action="account_deletion_requested",
        message=f"Student {current_user.email} (ID: {current_user.id}) requested account deletion. Reason: {reason_text}",
        created_at=now
    ))
    db.commit()

    return {
        "success": True,
        "status": "pending_admin_review",
        "message": "Your account deletion request has been received and will be reviewed by the institution administrator.",
        "user_id": current_user.id,
        "email": current_user.email,
        "requested_at": now.strftime("%Y-%m-%d %H:%M:%S")
    }

