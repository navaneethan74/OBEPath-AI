import os
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import (
    User, Course, CourseOutcome, Topic, MasteryScore, StudentProfile,
    ClassModel, ClassEnrollment, OutcomeAttainment, AgentLog,
    TopicPrerequisite, TopicOutcomeMapping, LearningPath, LearningPathItem,
    AssessmentAttempt, MasteryHistory, QuestionAnswerHistory, QuestionBank,
    OutcomeAttainmentHistory, InterventionEvent
)
from schemas import ClassCreateRequest, ClassOut, TeacherFlagRequest
from core.security import require_role
from core.class_codes import (
    generate_unique_class_code,
    validate_custom_code
)
from core.thresholds import (
    PREREQ_UNLOCK, ASSESSMENT_PASS, TOPIC_MASTERY,
    CO_ACHIEVED_DEFAULT, AT_RISK_MASTERY, INACTIVE_DAYS, COMMON_GAP_PCT
)


import hashlib
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from core.rate_limiter import get_client_ip, enforce_rate_limit

def faculty_rate_limiter(request: Request):
    limit = int(os.getenv("FACULTY_RATE_LIMIT", "120"))
    auth_header = request.headers.get("authorization", "")
    if auth_header:
        token_hash = hashlib.sha256(auth_header.encode()).hexdigest()[:16]
        key = f"faculty:user:{token_hash}"
    else:
        ip = get_client_ip(request)
        key = f"faculty:ip:{ip}"
    enforce_rate_limit(
        key=key,
        limit=limit,
        window_seconds=60,
        detail="Rate limit exceeded for faculty operations. Please wait."
    )

router = APIRouter(
    prefix="/api/faculty",
    tags=["faculty"],
    dependencies=[Depends(faculty_rate_limiter)]
)

# ==============================================================================
# CLASS MANAGEMENT ENDPOINTS (Faculty & Admin Only)
# ==============================================================================

@router.post("/classes", status_code=status.HTTP_201_CREATED)
def create_class(
    payload: ClassCreateRequest,
    current_user: User = Depends(require_role("faculty", "admin")),
    db: Session = Depends(get_db)
):
    """
    Creates a new class for a course.
    Generates a unique 6-character code, or validates an optional teacher-proposed custom code.
    """
    course = db.query(Course).filter(Course.id == payload.course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {payload.course_id} was not found."
        )

    clean_name = payload.name.strip()
    if not clean_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Class name is required."
        )

    # Class Code Generation or Validation
    if payload.custom_code and payload.custom_code.strip():
        suggested_code = generate_unique_class_code(db)
        is_valid, err_msg = validate_custom_code(payload.custom_code, suggested_code)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=err_msg
            )
        candidate_code = payload.custom_code.strip().upper()
        existing = db.query(ClassModel).filter(ClassModel.class_code == candidate_code).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Class code '{candidate_code}' is already taken. Suggested code: '{suggested_code}'."
            )
        final_code = candidate_code
    else:
        final_code = generate_unique_class_code(db)

    new_class = ClassModel(
        faculty_id=current_user.id,
        course_id=course.id,
        name=clean_name,
        class_code=final_code,
        is_active=True,
        max_students=payload.max_students if (payload.max_students and payload.max_students > 0) else None,
        expires_at=payload.expires_at,
        created_at=datetime.utcnow()
    )
    db.add(new_class)

    db.add(AgentLog(
        user_id=current_user.id,
        agent_name="Faculty Portal",
        action="class_created",
        message=f"Faculty {current_user.email} created class '{new_class.name}' (Code: {new_class.class_code}) for course '{course.title}'.",
        created_at=datetime.utcnow()
    ))
    db.commit()
    db.refresh(new_class)

    return {
        "id": new_class.id,
        "faculty_id": new_class.faculty_id,
        "course_id": new_class.course_id,
        "course_code": course.code,
        "course_title": course.title,
        "name": new_class.name,
        "class_code": new_class.class_code,
        "is_active": new_class.is_active,
        "max_students": new_class.max_students,
        "expires_at": new_class.expires_at.isoformat() if new_class.expires_at else None,
        "created_at": new_class.created_at.isoformat() if new_class.created_at else None,
        "active_students_count": 0
    }

@router.get("/classes")
def get_classes(
    current_user: User = Depends(require_role("faculty", "admin")),
    db: Session = Depends(get_db)
):
    """
    Lists classes: faculty sees their own classes; admin sees all classes.
    Includes current active student enrollment count for each class.
    """
    if current_user.role == "admin":
        classes = db.query(ClassModel).order_by(ClassModel.created_at.desc()).all()
    else:
        classes = db.query(ClassModel).filter(
            ClassModel.faculty_id == current_user.id
        ).order_by(ClassModel.created_at.desc()).all()

    result = []
    for c in classes:
        active_count = db.query(ClassEnrollment).filter(
            ClassEnrollment.class_id == c.id,
            ClassEnrollment.status == "active"
        ).count()
        result.append({
            "id": c.id,
            "faculty_id": c.faculty_id,
            "faculty_name": c.faculty.full_name if c.faculty else "Instructor",
            "course_id": c.course_id,
            "course_code": c.course.code if c.course else "",
            "course_title": c.course.title if c.course else "",
            "name": c.name,
            "class_code": c.class_code,
            "is_active": c.is_active,
            "max_students": c.max_students,
            "expires_at": c.expires_at.isoformat() if c.expires_at else None,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "active_students_count": active_count
        })
    return result

@router.post("/classes/{class_id}/regenerate-code")
def regenerate_class_code(
    class_id: int,
    current_user: User = Depends(require_role("faculty", "admin")),
    db: Session = Depends(get_db)
):
    """
    Regenerates a new unique class code, immediately invalidating the old code.
    Only the owning faculty or admin may invoke this.
    """
    class_obj = db.query(ClassModel).filter(ClassModel.id == class_id).first()
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found."
        )

    if current_user.role != "admin" and class_obj.faculty_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not own this class."
        )

    old_code = class_obj.class_code
    new_code = generate_unique_class_code(db)
    class_obj.class_code = new_code
    db.commit()
    db.refresh(class_obj)

    return {
        "id": class_obj.id,
        "class_code": class_obj.class_code,
        "message": f"Class code successfully regenerated. Old code '{old_code}' is now invalid."
    }

@router.post("/classes/{class_id}/disable-code")
def disable_class_code(
    class_id: int,
    current_user: User = Depends(require_role("faculty", "admin")),
    db: Session = Depends(get_db)
):
    """
    Disables joining for this class. Existing students remain active.
    """
    class_obj = db.query(ClassModel).filter(ClassModel.id == class_id).first()
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found."
        )

    if current_user.role != "admin" and class_obj.faculty_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not own this class."
        )

    class_obj.is_active = False
    db.commit()
    return {
        "id": class_obj.id,
        "is_active": False,
        "message": "Class code disabled. New enrollments will be rejected."
    }

@router.post("/classes/{class_id}/enable-code")
def enable_class_code(
    class_id: int,
    current_user: User = Depends(require_role("faculty", "admin")),
    db: Session = Depends(get_db)
):
    """
    Enables joining for this class.
    """
    class_obj = db.query(ClassModel).filter(ClassModel.id == class_id).first()
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found."
        )

    if current_user.role != "admin" and class_obj.faculty_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not own this class."
        )

    class_obj.is_active = True
    db.commit()
    return {
        "id": class_obj.id,
        "is_active": True,
        "message": "Class code enabled. New enrollments are now allowed."
    }

# ==============================================================================
# FACULTY STEP 2C HELPERS: ACCESS CONTROL & BATCH ANALYTICS
# ==============================================================================

def check_new_endpoint_class_access(class_id: int, current_user: User, db: Session) -> ClassModel:
    """
    Validates that a class exists and that the requesting faculty member owns it
    (admin may access all). If not owned or non-existent, raises HTTP 404 to
    prevent leaking the existence of other faculty cohorts.
    """
    class_obj = db.query(ClassModel).filter(ClassModel.id == class_id).first()
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found."
        )
    if current_user.role != "admin" and class_obj.faculty_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found."
        )
    return class_obj

def check_new_endpoint_student_access(class_obj: ClassModel, student_id: int, db: Session) -> ClassEnrollment:
    """
    Validates that a student is actively enrolled in the specified class.
    If not actively enrolled, returns HTTP 404 to avoid leaking student enrollment existence.
    """
    enrollment = db.query(ClassEnrollment).filter(
        ClassEnrollment.class_id == class_obj.id,
        ClassEnrollment.student_id == student_id,
        ClassEnrollment.status == "active"
    ).first()
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found or not actively enrolled in this class."
        )
    return enrollment

def load_class_analytics_bundle(class_obj: ClassModel, db: Session) -> Dict[str, Any]:
    """
    Batch-loads all enrollment, mastery scores, outcome attainments, learning paths,
    prerequisites, and assessment attempts for a class cohort in a single bounded
    set of SQL queries (strictly avoiding N+1 queries).
    
    AT-RISK RULE DOCUMENTATION:
    A student is flagged as at-risk (`is_at_risk=True`) if ANY of the following 3 criteria apply:
    1. Prerequisite Deficit: Any prerequisite topic for the student's current active topic has an overall mastery below PREREQ_UNLOCK (60.0%).
    2. Overall Mastery Deficit: The student's overall average course mastery across all topics is below AT_RISK_MASTERY (50.0%).
    3. Cohort Inactivity: The student has logged no assessment activity for INACTIVE_DAYS (7 days) or more since their last recorded attempt or class join date.
    
    Explanatory reason strings are generated and returned in `at_risk_reasons` for each triggered condition.
    """
    enrollments = db.query(ClassEnrollment).filter(
        ClassEnrollment.class_id == class_obj.id,
        ClassEnrollment.status == "active"
    ).all()

    student_ids = [e.student_id for e in enrollments]

    # Course topics and outcomes
    course_topics = db.query(Topic).filter(Topic.course_id == class_obj.course_id).order_by(Topic.order_index).all()
    topic_ids = [t.id for t in course_topics]
    topic_map = {t.id: t for t in course_topics}

    course_outcomes = db.query(CourseOutcome).filter(CourseOutcome.course_id == class_obj.course_id).order_by(CourseOutcome.code).all()
    outcome_map = {co.id: co for co in course_outcomes}

    prerequisites = db.query(TopicPrerequisite).join(Topic, TopicPrerequisite.topic_id == Topic.id).filter(Topic.course_id == class_obj.course_id).all()
    prereqs_by_topic: Dict[int, List[TopicPrerequisite]] = {}
    for p in prerequisites:
        prereqs_by_topic.setdefault(p.topic_id, []).append(p)

    mappings = db.query(TopicOutcomeMapping).join(Topic, TopicOutcomeMapping.topic_id == Topic.id).filter(Topic.course_id == class_obj.course_id).all()
    mappings_by_co: Dict[int, List[TopicOutcomeMapping]] = {}
    for m in mappings:
        mappings_by_co.setdefault(m.outcome_id, []).append(m)

    if not student_ids:
        return {
            "enrollments": [],
            "students": [],
            "course_topics": course_topics,
            "course_outcomes": course_outcomes,
            "topic_map": topic_map,
            "outcome_map": outcome_map,
            "prereqs_by_topic": prereqs_by_topic,
            "mappings_by_co": mappings_by_co,
            "students_data": [],
            "student_map": {},
            "mastery_by_user_topic": {},
            "attainment_by_user_co": {},
            "lp_by_user": {},
            "items_by_lp": {},
            "attempts_by_user": {}
        }

    # Batch load all related records for cohort students
    students = db.query(User).filter(User.id.in_(student_ids)).all()
    user_map = {u.id: u for u in students}

    all_masteries = db.query(MasteryScore).filter(
        MasteryScore.user_id.in_(student_ids),
        MasteryScore.topic_id.in_(topic_ids)
    ).all()
    mastery_by_user_topic: Dict[tuple, MasteryScore] = {
        (m.user_id, m.topic_id): m for m in all_masteries
    }

    all_attainments = db.query(OutcomeAttainment).filter(
        OutcomeAttainment.user_id.in_(student_ids),
        OutcomeAttainment.course_id == class_obj.course_id
    ).all()
    attainment_by_user_co: Dict[tuple, OutcomeAttainment] = {
        (oa.user_id, oa.outcome_id): oa for oa in all_attainments
    }

    all_lps = db.query(LearningPath).filter(
        LearningPath.user_id.in_(student_ids),
        LearningPath.course_id == class_obj.course_id,
        LearningPath.status == "ACTIVE"
    ).all()
    lp_by_user = {lp.user_id: lp for lp in all_lps}
    lp_ids = [lp.id for lp in all_lps]

    all_lp_items = db.query(LearningPathItem).filter(
        LearningPathItem.learning_path_id.in_(lp_ids)
    ).order_by(LearningPathItem.sequence_order).all() if lp_ids else []
    items_by_lp: Dict[int, List[LearningPathItem]] = {}
    for item in all_lp_items:
        items_by_lp.setdefault(item.learning_path_id, []).append(item)

    all_attempts = db.query(AssessmentAttempt).filter(
        AssessmentAttempt.user_id.in_(student_ids),
        AssessmentAttempt.course_id == class_obj.course_id
    ).order_by(AssessmentAttempt.created_at.desc()).all()
    attempts_by_user: Dict[int, List[AssessmentAttempt]] = {}
    for att in all_attempts:
        attempts_by_user.setdefault(att.user_id, []).append(att)

    # Process each student
    students_data = []
    total_topics_count = len(course_topics)
    now = datetime.utcnow()

    for enr in enrollments:
        student = user_map.get(enr.student_id)
        if not student:
            continue

        sid = student.id
        student_topic_masteries = {
            t.id: mastery_by_user_topic.get((sid, t.id))
            for t in course_topics
        }

        # Completed topics count
        completed_count = 0
        for t in course_topics:
            m = student_topic_masteries[t.id]
            if m and (m.overall_mastery >= TOPIC_MASTERY or (m.completion_score or 0.0) >= 100.0):
                completed_count += 1

        # Overall average mastery across all course topics
        if total_topics_count > 0:
            avg_mastery = round(
                sum(
                    (student_topic_masteries[t.id].overall_mastery if student_topic_masteries[t.id] else 0.0)
                    for t in course_topics
                ) / total_topics_count,
                1
            )
        else:
            avg_mastery = 0.0

        # CO attainments
        co_attainments = []
        for co in course_outcomes:
            oa = attainment_by_user_co.get((sid, co.id))
            attainment_val = oa.attainment_percentage if oa else 0.0
            target_pct = co.target_attainment_pct if (co.target_attainment_pct is not None and co.target_attainment_pct > 0) else CO_ACHIEVED_DEFAULT
            is_achieved = attainment_val >= target_pct
            co_attainments.append({
                "outcome_id": co.id,
                "code": co.code,
                "description": co.description,
                "attainment_pct": round(attainment_val, 1),
                "target_pct": target_pct,
                "is_achieved": is_achieved
            })

        # Diagnostic score
        user_attempts = attempts_by_user.get(sid, [])
        diag_attempt = next((a for a in user_attempts if a.attempt_type == "diagnostic"), None)
        if diag_attempt:
            diagnostic_score = round(diag_attempt.percentage, 1)
        else:
            diag_vals = [
                student_topic_masteries[t.id].diagnostic_score
                for t in course_topics
                if student_topic_masteries[t.id] and student_topic_masteries[t.id].diagnostic_score is not None and student_topic_masteries[t.id].diagnostic_score > 0
            ]
            diagnostic_score = round(sum(diag_vals) / len(diag_vals), 1) if diag_vals else None

        # Last activity date & inactivity check
        last_attempt_date = user_attempts[0].created_at if user_attempts else None
        last_active = last_attempt_date if (last_attempt_date and last_attempt_date > enr.joined_at) else enr.joined_at
        days_inactive = (now - last_active).days if last_active else 0

        # Current topic determination
        lp = lp_by_user.get(sid)
        lp_items = items_by_lp.get(lp.id, []) if lp else []
        current_item = next((it for it in lp_items if it.status in ("CURRENT", "NEEDS REVISION")), None)
        if not current_item:
            current_item = next((it for it in lp_items if it.status != "COMPLETED"), None)

        if current_item and current_item.topic_id in topic_map:
            current_topic = topic_map[current_item.topic_id]
        else:
            current_topic = next(
                (t for t in course_topics if not (student_topic_masteries[t.id] and (student_topic_masteries[t.id].overall_mastery >= TOPIC_MASTERY or (student_topic_masteries[t.id].completion_score or 0.0) >= 100.0))),
                course_topics[0] if course_topics else None
            )

        # AT-RISK EVALUATION
        at_risk_reasons = []

        # Rule 1: Prerequisite below PREREQ_UNLOCK for current topic
        if current_topic:
            for prereq in prereqs_by_topic.get(current_topic.id, []):
                prereq_topic = topic_map.get(prereq.prerequisite_topic_id)
                prereq_name = prereq_topic.title if prereq_topic else f"Topic {prereq.prerequisite_topic_id}"
                m = student_topic_masteries.get(prereq.prerequisite_topic_id)
                p_mast = m.overall_mastery if m else 0.0
                req_val = prereq.required_mastery_pct if prereq.required_mastery_pct is not None else PREREQ_UNLOCK
                if p_mast < req_val:
                    at_risk_reasons.append(
                        f"Prerequisite '{prereq_name}' mastery ({p_mast:.1f}%) is below {req_val:.1f}% for current topic '{current_topic.title}'"
                    )

        # Rule 2: Overall mastery below AT_RISK_MASTERY
        if avg_mastery < AT_RISK_MASTERY:
            at_risk_reasons.append(
                f"Overall mastery ({avg_mastery:.1f}%) is below {AT_RISK_MASTERY:.1f}%"
            )

        # Rule 3: Inactivity for INACTIVE_DAYS
        if days_inactive >= INACTIVE_DAYS:
            at_risk_reasons.append(
                f"No activity for {days_inactive} days (inactivity threshold: {INACTIVE_DAYS} days)"
            )

        is_at_risk = len(at_risk_reasons) > 0
        baseline_comp = enr.baseline_completed_topics or 0

        s_dict = {
            "id": student.id,
            "name": student.full_name,
            "email": student.email,
            "joined_at": enr.joined_at.strftime("%Y-%m-%d %H:%M:%S") if enr.joined_at else None,
            "current_overall_mastery": avg_mastery,
            "completed_topics": f"{completed_count}/{total_topics_count}",
            "completed_topics_count": completed_count,
            "total_topics_count": total_topics_count,
            "baseline_completed_topics": baseline_comp,
            "progress_summary": f"joined with {baseline_comp}/{total_topics_count} already complete",
            "improvement_since_join": max(0, completed_count - baseline_comp),
            "co_attainments": co_attainments,
            "diagnostic_score": diagnostic_score,
            "last_activity_date": last_active.isoformat() if last_active else None,
            "is_at_risk": is_at_risk,
            "at_risk_reasons": at_risk_reasons,
            "current_topic": {
                "id": current_topic.id,
                "title": current_topic.title,
                "code": current_topic.code
            } if current_topic else None
        }
        students_data.append(s_dict)

    student_map = {s["id"]: s for s in students_data}

    return {
        "enrollments": enrollments,
        "students": students,
        "course_topics": course_topics,
        "course_outcomes": course_outcomes,
        "topic_map": topic_map,
        "outcome_map": outcome_map,
        "prereqs_by_topic": prereqs_by_topic,
        "mappings_by_co": mappings_by_co,
        "students_data": students_data,
        "student_map": student_map,
        "mastery_by_user_topic": mastery_by_user_topic,
        "attainment_by_user_co": attainment_by_user_co,
        "lp_by_user": lp_by_user,
        "items_by_lp": items_by_lp,
        "attempts_by_user": attempts_by_user
    }


# ==============================================================================
# FACULTY STEP 2C VIEWS (READ-ONLY)
# ==============================================================================

@router.get("/classes/{class_id}/overview")
def get_class_overview(
    class_id: int,
    current_user: User = Depends(require_role("faculty", "admin")),
    db: Session = Depends(get_db)
):
    """
    Step 2C.1: Class Overview
    Returns course info, active student count, average overall mastery,
    CO1-CO4 attainment metrics (class average, target %, students achieved vs total),
    topic-wise average mastery, completion distribution (0..N completed topics),
    at-risk count, and top learning gaps. Read-only.
    """
    class_obj = check_new_endpoint_class_access(class_id, current_user, db)
    bundle = load_class_analytics_bundle(class_obj, db)

    course = class_obj.course
    active_students_count = len(bundle["students_data"])

    if active_students_count > 0:
        avg_mastery = round(sum(s["current_overall_mastery"] for s in bundle["students_data"]) / active_students_count, 1)
        at_risk_count = sum(1 for s in bundle["students_data"] if s["is_at_risk"])
    else:
        avg_mastery = 0.0
        at_risk_count = 0

    # CO1-CO4 Metrics
    outcomes_list = []
    for co in bundle["course_outcomes"]:
        target_pct = co.target_attainment_pct if (co.target_attainment_pct is not None and co.target_attainment_pct > 0) else CO_ACHIEVED_DEFAULT
        if active_students_count > 0:
            student_co_scores = []
            achieved_students = 0
            for s in bundle["students_data"]:
                co_entry = next((c for c in s["co_attainments"] if c["outcome_id"] == co.id), None)
                score = co_entry["attainment_pct"] if co_entry else 0.0
                student_co_scores.append(score)
                if co_entry and co_entry["is_achieved"]:
                    achieved_students += 1
            avg_attainment = round(sum(student_co_scores) / active_students_count, 1)
        else:
            avg_attainment = 0.0
            achieved_students = 0

        outcomes_list.append({
            "outcome_id": co.id,
            "code": co.code,
            "description": co.description,
            "class_avg_attainment": avg_attainment,
            "target_attainment_pct": target_pct,
            "achieved_count": achieved_students,
            "total_students": active_students_count,
            "achieved_ratio": f"{achieved_students}/{active_students_count}"
        })

    # Topic-wise average mastery
    topic_masteries = []
    for t in bundle["course_topics"]:
        if active_students_count > 0:
            t_scores = []
            at_risk_topic_count = 0
            for s in bundle["students_data"]:
                m = bundle["mastery_by_user_topic"].get((s["id"], t.id))
                m_score = m.overall_mastery if m else 0.0
                t_scores.append(m_score)
                if m_score < PREREQ_UNLOCK:
                    at_risk_topic_count += 1
            topic_avg = round(sum(t_scores) / active_students_count, 1)
        else:
            topic_avg = 0.0
            at_risk_topic_count = 0

        topic_masteries.append({
            "topic_id": t.id,
            "code": t.code,
            "title": t.title,
            "order_index": t.order_index,
            "avg_mastery": topic_avg,
            "at_risk_count": at_risk_topic_count
        })

    # Completion distribution (0..N completed topics)
    total_topics_count = len(bundle["course_topics"])
    if active_students_count == 0:
        completion_dist = []
    else:
        completion_dist = []
        for k in range(total_topics_count + 1):
            s_count = sum(1 for s in bundle["students_data"] if s["completed_topics_count"] == k)
            completion_dist.append({
                "completed_topics": k,
                "student_count": s_count
            })

    # Top learning gaps (lowest average mastery topics)
    if active_students_count == 0 or not topic_masteries:
        top_learning_gaps = []
    else:
        sorted_topics = sorted(topic_masteries, key=lambda x: x["avg_mastery"])
        top_learning_gaps = sorted_topics[:min(3, len(sorted_topics))]

    return {
        "class_id": class_obj.id,
        "class_name": class_obj.name,
        "course": {
            "id": course.id if course else 0,
            "code": course.code if course else "",
            "title": course.title if course else "",
            "description": course.description if course else ""
        },
        "active_students_count": active_students_count,
        "average_overall_mastery": avg_mastery,
        "at_risk_count": at_risk_count,
        "thresholds": {
            "prereq_unlock": PREREQ_UNLOCK,
            "assessment_pass": ASSESSMENT_PASS,
            "topic_mastery": TOPIC_MASTERY,
            "co_achieved_default": CO_ACHIEVED_DEFAULT,
            "at_risk_mastery": AT_RISK_MASTERY,
            "inactive_days": INACTIVE_DAYS
        },
        "outcomes": outcomes_list,
        "topic_masteries": topic_masteries,
        "completion_distribution": completion_dist,
        "top_learning_gaps": top_learning_gaps
    }


@router.get("/classes/{class_id}/outcomes/{outcome_id}")
def get_class_outcome_drilldown(
    class_id: int,
    outcome_id: int,
    current_user: User = Depends(require_role("faculty", "admin")),
    db: Session = Depends(get_db)
):
    """
    Step 2C.3: Outcome Drill-down
    Returns CO details, contributing topics with weights, class average per contributing topic,
    and per-student rows (attainment %, achieved flag, concept-wise topic mastery).
    """
    class_obj = check_new_endpoint_class_access(class_id, current_user, db)
    outcome = db.query(CourseOutcome).filter(
        CourseOutcome.id == outcome_id,
        CourseOutcome.course_id == class_obj.course_id
    ).first()
    if not outcome:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Outcome not found for this class's course."
        )

    bundle = load_class_analytics_bundle(class_obj, db)
    mappings = bundle["mappings_by_co"].get(outcome.id, [])

    # Contributing topics
    contributing_topics = []
    active_count = len(bundle["students_data"])
    for m in mappings:
        t = bundle["topic_map"].get(m.topic_id)
        if not t:
            continue
        if active_count > 0:
            avg_m = round(
                sum((bundle["mastery_by_user_topic"].get((s["id"], t.id)).overall_mastery if bundle["mastery_by_user_topic"].get((s["id"], t.id)) else 0.0) for s in bundle["students_data"]) / active_count,
                1
            )
        else:
            avg_m = 0.0
        contributing_topics.append({
            "topic_id": t.id,
            "code": t.code,
            "title": t.title,
            "weight": m.weight,
            "class_avg_mastery": avg_m
        })

    target_pct = outcome.target_attainment_pct if (outcome.target_attainment_pct is not None and outcome.target_attainment_pct > 0) else CO_ACHIEVED_DEFAULT

    # Per-student rows
    student_rows = []
    achieved_count = 0
    total_attainment_sum = 0.0

    for s in bundle["students_data"]:
        co_entry = next((c for c in s["co_attainments"] if c["outcome_id"] == outcome.id), None)
        attainment_pct = co_entry["attainment_pct"] if co_entry else 0.0
        is_achieved = co_entry["is_achieved"] if co_entry else False
        if is_achieved:
            achieved_count += 1
        total_attainment_sum += attainment_pct

        concept_mastery = []
        for ct in contributing_topics:
            tid = ct["topic_id"]
            m = bundle["mastery_by_user_topic"].get((s["id"], tid))
            m_val = round(m.overall_mastery, 1) if m else 0.0
            concept_mastery.append({
                "topic_id": tid,
                "code": ct["code"],
                "title": ct["title"],
                "mastery_score": m_val
            })

        student_rows.append({
            "student_id": s["id"],
            "student_name": s["name"],
            "student_email": s["email"],
            "co_attainment_pct": attainment_pct,
            "is_achieved": is_achieved,
            "concept_mastery": concept_mastery
        })

    class_avg_attainment = round(total_attainment_sum / max(active_count, 1), 1) if active_count > 0 else 0.0

    return {
        "class_id": class_obj.id,
        "class_name": class_obj.name,
        "outcome": {
            "id": outcome.id,
            "code": outcome.code,
            "description": outcome.description,
            "target_attainment_pct": target_pct
        },
        "class_avg_attainment": class_avg_attainment,
        "achieved_count": achieved_count,
        "total_students": active_count,
        "achieved_ratio": f"{achieved_count}/{active_count}",
        "contributing_topics": contributing_topics,
        "thresholds": {
            "prereq_unlock": PREREQ_UNLOCK,
            "assessment_pass": ASSESSMENT_PASS,
            "topic_mastery": TOPIC_MASTERY,
            "co_achieved_default": CO_ACHIEVED_DEFAULT,
            "at_risk_mastery": AT_RISK_MASTERY
        },
        "student_rows": student_rows
    }


@router.get("/classes/{class_id}/students")
def get_class_students(
    class_id: int,
    current_user: User = Depends(require_role("faculty", "admin")),
    db: Session = Depends(get_db)
):
    """
    Step 2C.4: Extended Student List
    Lists active enrolled students in the class with current overall mastery,
    completed topics count (x/N), CO1-CO4 attainments, diagnostic initial score,
    last activity date, at-risk flag + reasons, and baseline progress summary.
    Enforces isolation: only owning faculty or admin may access.
    """
    class_obj = db.query(ClassModel).filter(ClassModel.id == class_id).first()
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found."
        )

    if current_user.role != "admin" and class_obj.faculty_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have permission to view students of this class."
        )

    bundle = load_class_analytics_bundle(class_obj, db)

    return {
        "class_id": class_obj.id,
        "class_name": class_obj.name,
        "course_id": class_obj.course_id,
        "total_active_students": len(bundle["students_data"]),
        "thresholds": {
            "prereq_unlock": PREREQ_UNLOCK,
            "assessment_pass": ASSESSMENT_PASS,
            "topic_mastery": TOPIC_MASTERY,
            "co_achieved_default": CO_ACHIEVED_DEFAULT,
            "at_risk_mastery": AT_RISK_MASTERY,
            "inactive_days": INACTIVE_DAYS
        },
        "students": bundle["students_data"]
    }


@router.get("/classes/{class_id}/students/{student_id}")
def get_class_student_detail(
    class_id: int,
    student_id: int,
    current_user: User = Depends(require_role("faculty", "admin")),
    db: Session = Depends(get_db)
):
    """
    Step 2C.5: Full Read-Only Student Profile
    Includes per-topic mastery and status (completed/current/locked/recommended),
    completed vs incomplete topics breakdown, CO attainment now vs join baseline and delta,
    diagnostic score, recent assessment attempts, and prerequisite gaps.
    """
    class_obj = check_new_endpoint_class_access(class_id, current_user, db)
    enrollment = check_new_endpoint_student_access(class_obj, student_id, db)
    bundle = load_class_analytics_bundle(class_obj, db)

    student_data = bundle["student_map"].get(student_id)
    if not student_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student data not found in class cohort."
        )

    # 1. Topics with status (completed / current / locked / recommended)
    lp = bundle["lp_by_user"].get(student_id)
    lp_items = bundle["items_by_lp"].get(lp.id, []) if lp else []
    lp_status_map = {item.topic_id: item.status for item in lp_items}

    topics_profile = []
    completed_topics = []
    incomplete_topics = []

    for t in bundle["course_topics"]:
        m = bundle["mastery_by_user_topic"].get((student_id, t.id))
        ov_mast = round(m.overall_mastery, 1) if m else 0.0
        q_sc = round(m.quiz_score, 1) if m else 0.0
        p_sc = round(m.practice_score, 1) if m else 0.0
        c_sc = round(m.completion_score, 1) if (m and m.completion_score is not None) else 0.0

        is_completed = bool(ov_mast >= TOPIC_MASTERY or c_sc >= 100.0)

        # Determine topic status
        if is_completed:
            topic_status = "completed"
        elif t.id in lp_status_map:
            topic_status = lp_status_map[t.id].lower()
        else:
            prereqs = bundle["prereqs_by_topic"].get(t.id, [])
            all_prereqs_met = all(
                (bundle["mastery_by_user_topic"].get((student_id, p.prerequisite_topic_id)).overall_mastery if bundle["mastery_by_user_topic"].get((student_id, p.prerequisite_topic_id)) else 0.0) >= (p.required_mastery_pct or PREREQ_UNLOCK)
                for p in prereqs
            )
            if not all_prereqs_met:
                topic_status = "locked"
            elif student_data.get("current_topic") and student_data["current_topic"]["id"] == t.id:
                topic_status = "current"
            else:
                topic_status = "recommended"

        topic_entry = {
            "topic_id": t.id,
            "code": t.code,
            "title": t.title,
            "order_index": t.order_index,
            "overall_mastery": ov_mast,
            "quiz_score": q_sc,
            "practice_score": p_sc,
            "completion_score": c_sc,
            "status": topic_status,
            "is_completed": is_completed
        }
        topics_profile.append(topic_entry)
        if is_completed:
            completed_topics.append(topic_entry)
        else:
            incomplete_topics.append(topic_entry)

    # 2. Outcome Attainments: Now vs Baseline vs Delta
    baseline_co_map = {}
    if enrollment.baseline_co_json:
        try:
            parsed = json.loads(enrollment.baseline_co_json)
            if isinstance(parsed, list):
                for item in parsed:
                    oid = item.get("outcome_id") or item.get("id")
                    if oid:
                        baseline_co_map[int(oid)] = item.get("attainment_percentage", 0.0)
            elif isinstance(parsed, dict):
                for k, v in parsed.items():
                    val = v if isinstance(v, (int, float)) else v.get("attainment_percentage", 0.0)
                    baseline_co_map[int(k)] = val
        except Exception:
            pass

    outcomes_profile = []
    for co in bundle["course_outcomes"]:
        oa = bundle["attainment_by_user_co"].get((student_id, co.id))
        current_attain = round(oa.attainment_percentage, 1) if oa else 0.0
        baseline_attain = round(baseline_co_map.get(co.id, 0.0), 1)
        delta = round(current_attain - baseline_attain, 1)
        target_pct = co.target_attainment_pct if (co.target_attainment_pct is not None and co.target_attainment_pct > 0) else CO_ACHIEVED_DEFAULT
        is_achieved = current_attain >= target_pct

        outcomes_profile.append({
            "outcome_id": co.id,
            "code": co.code,
            "description": co.description,
            "current_attainment": current_attain,
            "baseline_attainment": baseline_attain,
            "delta": delta,
            "target_pct": target_pct,
            "is_achieved": is_achieved
        })

    # 3. Recent Assessment Attempts
    user_attempts = bundle["attempts_by_user"].get(student_id, [])
    recent_attempts = []
    for att in user_attempts[:15]:
        t = bundle["topic_map"].get(att.topic_id)
        recent_attempts.append({
            "id": att.id,
            "topic_id": att.topic_id,
            "topic_title": t.title if t else ("Diagnostic Assessment" if att.attempt_type == "diagnostic" else "Comprehensive"),
            "topic_code": t.code if t else "ALL",
            "attempt_type": att.attempt_type,
            "score": att.score,
            "max_score": att.max_score,
            "percentage": round(att.percentage, 1),
            "passed": att.passed,
            "created_at": att.created_at.strftime("%Y-%m-%d %H:%M:%S") if att.created_at else None
        })

    # 4. Prerequisite Gaps
    prerequisite_gaps = []
    for t in bundle["course_topics"]:
        for p in bundle["prereqs_by_topic"].get(t.id, []):
            prereq_topic = bundle["topic_map"].get(p.prerequisite_topic_id)
            m = bundle["mastery_by_user_topic"].get((student_id, p.prerequisite_topic_id))
            p_mast = round(m.overall_mastery, 1) if m else 0.0
            req = p.required_mastery_pct if p.required_mastery_pct is not None else PREREQ_UNLOCK
            if p_mast < req:
                prerequisite_gaps.append({
                    "topic_id": t.id,
                    "topic_title": t.title,
                    "prereq_id": p.prerequisite_topic_id,
                    "prereq_title": prereq_topic.title if prereq_topic else f"Topic {p.prerequisite_topic_id}",
                    "current_mastery": p_mast,
                    "required_mastery": req,
                    "gap": round(req - p_mast, 1)
                })

    # 5. Assessment Summary (Initial vs Reassessment vs Best)
    chronological_attempts = sorted(user_attempts, key=lambda a: (a.created_at or datetime.min, a.id))
    diag_att = next((a for a in chronological_attempts if a.attempt_type == "diagnostic"), None)
    initial_diag_score = round(diag_att.percentage, 1) if diag_att else student_data.get("diagnostic_score")

    non_diag_attempts = [a for a in chronological_attempts if a.attempt_type != "diagnostic"]
    first_attempt_score = round(non_diag_attempts[0].percentage, 1) if non_diag_attempts else None
    latest_attempt_score = round(non_diag_attempts[-1].percentage, 1) if non_diag_attempts else None
    best_score = round(max(a.percentage for a in chronological_attempts), 1) if chronological_attempts else None
    reassessment_scores = [
        round(a.percentage, 1)
        for a in chronological_attempts
        if a.attempt_type == "reassessment"
    ]

    assessment_summary = {
        "initial_diagnostic_score": initial_diag_score,
        "first_attempt_score": first_attempt_score,
        "latest_attempt_score": latest_attempt_score,
        "best_score": best_score,
        "reassessment_scores": reassessment_scores,
        "total_attempts": len(chronological_attempts)
    }

    # 6. Weakest Concepts for this student
    student_attempt_ids = [a.id for a in user_attempts]
    qah_rows = db.query(QuestionAnswerHistory).filter(
        QuestionAnswerHistory.user_id == student_id,
        QuestionAnswerHistory.attempt_id.in_(student_attempt_ids)
    ).all() if student_attempt_ids else []

    concept_stats: Dict[str, Dict[str, Any]] = {}
    q_ids = [r.question_id for r in qah_rows if r.question_id]
    qb_rows = db.query(QuestionBank).filter(QuestionBank.id.in_(q_ids)).all() if q_ids else []
    qb_topic_map = {q.id: q.topic_id for q in qb_rows}

    for r in qah_rows:
        c_name = r.concept or "General"
        tid = qb_topic_map.get(r.question_id)
        if c_name not in concept_stats:
            concept_stats[c_name] = {"concept": c_name, "topic_id": tid, "correct": 0, "total": 0}
        concept_stats[c_name]["total"] += 1
        if r.is_correct:
            concept_stats[c_name]["correct"] += 1

    weakest_concepts = []
    for c_name, c_info in concept_stats.items():
        t = bundle["topic_map"].get(c_info["topic_id"])
        acc = round((c_info["correct"] / max(c_info["total"], 1)) * 100.0, 1)
        weakest_concepts.append({
            "concept": c_name,
            "topic_id": c_info["topic_id"],
            "topic_title": t.title if t else "General",
            "accuracy_pct": acc,
            "attempts_count": c_info["total"]
        })
    weakest_concepts.sort(key=lambda x: (x["accuracy_pct"], -x["attempts_count"]))
    weakest_concepts = weakest_concepts[:8]

    return {
        "student": {
            "id": student_data["id"],
            "name": student_data["name"],
            "email": student_data["email"],
            "joined_at": student_data["joined_at"],
            "baseline_completed_topics": student_data["baseline_completed_topics"],
            "progress_summary": student_data["progress_summary"],
            "improvement_since_join": student_data["improvement_since_join"]
        },
        "class_id": class_obj.id,
        "class_name": class_obj.name,
        "course_id": class_obj.course_id,
        "current_overall_mastery": student_data["current_overall_mastery"],
        "completed_topics_count": student_data["completed_topics_count"],
        "total_topics_count": student_data["total_topics_count"],
        "diagnostic_score": student_data["diagnostic_score"],
        "last_activity_date": student_data["last_activity_date"],
        "is_at_risk": student_data["is_at_risk"],
        "at_risk_reasons": student_data["at_risk_reasons"],
        "thresholds": {
            "prereq_unlock": PREREQ_UNLOCK,
            "assessment_pass": ASSESSMENT_PASS,
            "topic_mastery": TOPIC_MASTERY,
            "co_achieved_default": CO_ACHIEVED_DEFAULT,
            "at_risk_mastery": AT_RISK_MASTERY,
            "inactive_days": INACTIVE_DAYS,
            "common_gap_pct": COMMON_GAP_PCT
        },
        "assessment_summary": assessment_summary,
        "weakest_concepts": weakest_concepts,
        "topics": topics_profile,
        "completed_topics": completed_topics,
        "incomplete_topics": incomplete_topics,
        "outcomes": outcomes_profile,
        "recent_attempts": recent_attempts,
        "prerequisite_gaps": prerequisite_gaps
    }


@router.get("/classes/{class_id}/students/{student_id}/learning-path")
def get_class_student_learning_path(
    class_id: int,
    student_id: int,
    current_user: User = Depends(require_role("faculty", "admin")),
    db: Session = Depends(get_db)
):
    """
    Step 2C.6: Student Learning Path (Read-Only)
    Returns the student's current learning path items in order with status,
    recommendation rationale, and any remedial modules.
    """
    class_obj = check_new_endpoint_class_access(class_id, current_user, db)
    enrollment = check_new_endpoint_student_access(class_obj, student_id, db)

    lp = db.query(LearningPath).filter(
        LearningPath.user_id == student_id,
        LearningPath.course_id == class_obj.course_id,
        LearningPath.status == "ACTIVE"
    ).first()

    if not lp:
        lp = db.query(LearningPath).filter(
            LearningPath.user_id == student_id,
            LearningPath.course_id == class_obj.course_id
        ).order_by(LearningPath.updated_at.desc()).first()

    if not lp:
        return {
            "student_id": student_id,
            "class_id": class_obj.id,
            "course_id": class_obj.course_id,
            "learning_path_id": None,
            "status": "NOT_GENERATED",
            "adaptation_reason": "No learning path generated yet.",
            "items": []
        }

    items = db.query(LearningPathItem).filter(
        LearningPathItem.learning_path_id == lp.id
    ).order_by(LearningPathItem.sequence_order).all()

    items_list = []
    for item in items:
        topic = item.topic
        items_list.append({
            "id": item.id,
            "sequence_order": item.sequence_order,
            "topic_id": item.topic_id,
            "topic_title": topic.title if topic else f"Topic {item.topic_id}",
            "topic_code": topic.code if topic else "",
            "difficulty": topic.difficulty if topic else "Beginner",
            "status": item.status,
            "recommendation_reason": item.recommendation_reason,
            "is_remedial": bool(item.is_remedial),
            "remedial_title": item.remedial_title,
            "remedial_description": item.remedial_description
        })

    return {
        "student_id": student_id,
        "class_id": class_obj.id,
        "course_id": class_obj.course_id,
        "learning_path_id": lp.id,
        "status": lp.status,
        "adaptation_reason": lp.adaptation_reason,
        "generated_at": lp.generated_at.strftime("%Y-%m-%d %H:%M:%S") if lp.generated_at else None,
        "updated_at": lp.updated_at.strftime("%Y-%m-%d %H:%M:%S") if lp.updated_at else None,
        "items": items_list
    }


@router.delete("/classes/{class_id}/students/{student_id}")
def remove_student_from_class(
    class_id: int,
    student_id: int,
    current_user: User = Depends(require_role("faculty", "admin")),
    db: Session = Depends(get_db)
):
    """
    Removes a student from a class (status='removed').
    Student's underlying user account and progress data are NOT deleted.
    """
    class_obj = db.query(ClassModel).filter(ClassModel.id == class_id).first()
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found."
        )

    if current_user.role != "admin" and class_obj.faculty_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have permission to modify enrollments for this class."
        )

    enrollment = db.query(ClassEnrollment).filter(
        ClassEnrollment.class_id == class_obj.id,
        ClassEnrollment.student_id == student_id,
        ClassEnrollment.status == "active"
    ).first()

    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active enrollment for this student in this class was not found."
        )

    enrollment.status = "removed"
    enrollment.left_at = datetime.utcnow()

    db.add(AgentLog(
        user_id=current_user.id,
        agent_name="Faculty Portal",
        action="student_removed_from_class",
        message=f"Faculty {current_user.email} removed student ID {student_id} from class '{class_obj.name}'.",
        created_at=datetime.utcnow()
    ))
    db.commit()

    return {
        "status": "success",
        "message": f"Student removed from class '{class_obj.name}'. Student account and history are preserved."
    }

# ==============================================================================
# FACULTY DASHBOARD & TOPIC ANALYTICS (Scoped to Faculty's Own Classes)
# ==============================================================================

@router.get("/dashboard")
def get_faculty_dashboard(
    course_id: int = 1,
    current_user: User = Depends(require_role("faculty", "admin")),
    db: Session = Depends(get_db)
):
    """
    Dynamic Faculty Dashboard scoped strictly to students actively enrolled in the
    faculty's own classes for the given course (admin sees all enrolled students).
    Zero hardcoded mock data. Returns real metrics or empty defaults without errors.
    """
    # 1. Resolve classes owned by this faculty (or all classes if admin)
    if current_user.role == "admin":
        classes = db.query(ClassModel).filter(ClassModel.course_id == course_id).all()
    else:
        classes = db.query(ClassModel).filter(
            ClassModel.faculty_id == current_user.id,
            ClassModel.course_id == course_id
        ).all()

    class_ids = [c.id for c in classes]

    # 2. Get distinct active enrolled students
    if not class_ids:
        return {
            "metrics": {
                "total_students": 0,
                "average_progress": 0.0,
                "average_mastery": 0.0,
                "average_co_attainment": 0.0,
                "students_needing_intervention": 0
            },
            "intervention_list": []
        }

    enrollments = db.query(ClassEnrollment).filter(
        ClassEnrollment.class_id.in_(class_ids),
        ClassEnrollment.status == "active"
    ).all()

    student_ids = list({e.student_id for e in enrollments})
    if not student_ids:
        return {
            "metrics": {
                "total_students": 0,
                "average_progress": 0.0,
                "average_mastery": 0.0,
                "average_co_attainment": 0.0,
                "students_needing_intervention": 0
            },
            "intervention_list": []
        }

    # 3. Compute real live statistics for enrolled students
    course_topics = db.query(Topic).filter(Topic.course_id == course_id).all()
    course_topic_ids = [t.id for t in course_topics]
    total_topics_count = max(len(course_topics), 1)

    total_progress_sum = 0.0
    total_mastery_sum = 0.0
    intervention_students = []

    for sid in student_ids:
        student = db.query(User).filter(User.id == sid).first()
        if not student:
            continue

        masteries = db.query(MasteryScore).filter(
            MasteryScore.user_id == sid,
            MasteryScore.topic_id.in_(course_topic_ids)
        ).all()
        m_map = {m.topic_id: m for m in masteries}

        completed_count = sum(
            1 for t in course_topics
            if (t.id in m_map and (m_map[t.id].overall_mastery >= TOPIC_MASTERY or (m_map[t.id].completion_score or 0.0) >= 100.0))
        )
        avg_student_mastery = round(
            sum(m_map[t.id].overall_mastery for t in course_topics if t.id in m_map) / total_topics_count,
            1
        )
        student_progress = round(
            (completed_count / total_topics_count) * 50.0 + (avg_student_mastery / 100.0) * 50.0,
            1
        )

        total_progress_sum += student_progress
        total_mastery_sum += avg_student_mastery

        # Flag for intervention if average mastery < PREREQ_UNLOCK or any topic mastery < 40%
        weakest_topic = min((m_map[t.id] for t in course_topics if t.id in m_map), key=lambda x: x.overall_mastery, default=None)
        if avg_student_mastery < PREREQ_UNLOCK or (weakest_topic and weakest_topic.overall_mastery < 40.0):
            t_obj = db.query(Topic).filter(Topic.id == weakest_topic.topic_id).first() if weakest_topic else None
            intervention_students.append({
                "id": student.id,
                "name": student.full_name,
                "email": student.email,
                "course": classes[0].course.title if classes and classes[0].course else "Course",
                "struggling_topic": t_obj.title if t_obj else "Fundamentals",
                "mastery": round(weakest_topic.overall_mastery, 1) if weakest_topic else avg_student_mastery,
                "status": "Needs Review" if avg_student_mastery < 50.0 else "Developing",
                "last_active": "Enrolled in active class"
            })

    total_count = len(student_ids)
    avg_prog = round(total_progress_sum / max(total_count, 1), 1)
    avg_mast = round(total_mastery_sum / max(total_count, 1), 1)

    # Average CO attainment for enrolled students
    attainments = db.query(OutcomeAttainment).filter(
        OutcomeAttainment.user_id.in_(student_ids),
        OutcomeAttainment.course_id == course_id
    ).all()
    avg_co = round(
        sum(a.attainment_percentage for a in attainments) / max(len(attainments), 1),
        1
    ) if attainments else 0.0

    return {
        "metrics": {
            "total_students": total_count,
            "average_progress": avg_prog,
            "average_mastery": avg_mast,
            "average_co_attainment": avg_co,
            "students_needing_intervention": len(intervention_students)
        },
        "intervention_list": intervention_students
    }

@router.get("/topic-analytics")
def get_topic_analytics(
    course_id: int = 1,
    current_user: User = Depends(require_role("faculty", "admin")),
    db: Session = Depends(get_db)
):
    """
    Dynamic Topic Analytics calculated from the faculty's enrolled class students.
    """
    if current_user.role == "admin":
        classes = db.query(ClassModel).filter(ClassModel.course_id == course_id).all()
    else:
        classes = db.query(ClassModel).filter(
            ClassModel.faculty_id == current_user.id,
            ClassModel.course_id == course_id
        ).all()

    class_ids = [c.id for c in classes]
    enrollments = db.query(ClassEnrollment).filter(
        ClassEnrollment.class_id.in_(class_ids),
        ClassEnrollment.status == "active"
    ).all() if class_ids else []

    student_ids = list({e.student_id for e in enrollments})
    course_topics = db.query(Topic).filter(Topic.course_id == course_id).order_by(Topic.order_index).all()

    if not student_ids:
        # Return empty state with informative guidance
        topic_performances = [
            {
                "topic": t.title,
                "outcome": (t.outcome_mappings[0].outcome.code if t.outcome_mappings else "CO1"),
                "avg_mastery": 0.0,
                "status": "No Enrollments",
                "at_risk": 0
            }
            for t in course_topics
        ]
        return {
            "topics": topic_performances,
            "critical_insight": "No active student enrollments found in your classes for this course.",
            "recommended_action": "Share your class code with students to begin tracking real-time mastery analytics."
        }

    topic_performances = []
    lowest_topic = None
    lowest_mastery = 999.0

    for t in course_topics:
        m_scores = db.query(MasteryScore).filter(
            MasteryScore.topic_id == t.id,
            MasteryScore.user_id.in_(student_ids)
        ).all()

        if m_scores:
            avg_m = round(sum(m.overall_mastery for m in m_scores) / len(m_scores), 1)
            at_risk = sum(1 for m in m_scores if m.overall_mastery < PREREQ_UNLOCK)
        else:
            avg_m = 0.0
            at_risk = 0

        status_label = "Mastered" if avg_m >= TOPIC_MASTERY else ("Proficient" if avg_m >= CO_ACHIEVED_DEFAULT else ("Developing" if avg_m >= 50.0 else "Needs Improvement"))

        if avg_m < lowest_mastery:
            lowest_mastery = avg_m
            lowest_topic = t.title

        co_code = t.outcome_mappings[0].outcome.code if t.outcome_mappings else "CO1"

        topic_performances.append({
            "topic": t.title,
            "outcome": co_code,
            "avg_mastery": avg_m,
            "status": status_label,
            "at_risk": at_risk
        })

    return {
        "topics": topic_performances,
        "critical_insight": f"{lowest_topic or 'Core topics'} currently has the lowest cohort mastery ({lowest_mastery if lowest_topic else 0.0}%).",
        "recommended_action": "Review struggling topics and direct cohort to targeted practice modules."
    }


# ==============================================================================
# STEP 2D: REASSESSMENT TRACKING, LEARNING GAPS & INTERVENTION IMPACT ENDPOINTS
# ==============================================================================

@router.post("/classes/{class_id}/students/{student_id}/flag")
def flag_student_intervention(
    class_id: int,
    student_id: int,
    payload: TeacherFlagRequest,
    current_user: User = Depends(require_role("faculty", "admin")),
    db: Session = Depends(get_db)
):
    """
    POST /api/faculty/classes/{class_id}/students/{student_id}/flag
    Records a teacher intervention event for a student actively enrolled in this class.
    Faculty only for classes they own and students with ACTIVE enrollment. Admin all. Otherwise 404.
    """
    class_obj = check_new_endpoint_class_access(class_id, current_user, db)
    enrollment = check_new_endpoint_student_access(class_obj, student_id, db)

    clean_note = payload.note.strip()
    if not clean_note:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Intervention note cannot be empty."
        )

    event = InterventionEvent(
        student_id=student_id,
        class_id=class_obj.id,
        topic_id=None,
        type="teacher_flag",
        created_at=datetime.utcnow(),
        note=clean_note
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    return {
        "success": True,
        "event": {
            "id": event.id,
            "student_id": event.student_id,
            "class_id": event.class_id,
            "type": event.type,
            "note": event.note,
            "created_at": event.created_at.strftime("%Y-%m-%d %H:%M:%S") if event.created_at else None
        }
    }


@router.get("/classes/{class_id}/assessments")
def get_class_assessments(
    class_id: int,
    current_user: User = Depends(require_role("faculty", "admin")),
    db: Session = Depends(get_db)
):
    """
    GET /api/faculty/classes/{class_id}/assessments:
    Per-student: initial (diagnostic) score, per-topic first attempt vs latest attempt vs best,
    number of attempts, improvement delta, reassessment scores list.
    Class-level averages for initial vs latest vs improvement.
    """
    class_obj = check_new_endpoint_class_access(class_id, current_user, db)
    bundle = load_class_analytics_bundle(class_obj, db)

    thresholds_dict = {
        "prereq_unlock": PREREQ_UNLOCK,
        "assessment_pass": ASSESSMENT_PASS,
        "topic_mastery": TOPIC_MASTERY,
        "co_achieved_default": CO_ACHIEVED_DEFAULT,
        "at_risk_mastery": AT_RISK_MASTERY,
        "inactive_days": INACTIVE_DAYS,
        "common_gap_pct": COMMON_GAP_PCT
    }

    if not bundle["students_data"]:
        return {
            "class_id": class_obj.id,
            "class_name": class_obj.name,
            "course_id": class_obj.course_id,
            "total_students": 0,
            "class_initial_avg": None,
            "class_latest_avg": None,
            "class_avg_improvement": None,
            "students": [],
            "class_averages": {
                "initial_average": None,
                "latest_average": None,
                "improvement_average": None
            },
            "thresholds": thresholds_dict
        }

    students_list = []
    initial_scores_all = []
    latest_scores_all = []
    improvement_deltas_all = []

    for s_data in bundle["students_data"]:
        sid = s_data["id"]
        user_attempts = bundle["attempts_by_user"].get(sid, [])
        sorted_attempts = sorted(user_attempts, key=lambda a: (a.created_at or datetime.min, a.id))

        diag_att = next((a for a in sorted_attempts if a.attempt_type == "diagnostic"), None)
        initial_score = round(diag_att.percentage, 1) if diag_att else s_data.get("diagnostic_score")
        if initial_score is not None:
            initial_scores_all.append(initial_score)

        topic_attempts_map: Dict[int, List[AssessmentAttempt]] = {}
        for a in sorted_attempts:
            if a.topic_id is not None:
                topic_attempts_map.setdefault(a.topic_id, []).append(a)

        per_topic = []
        student_deltas = []
        all_reassessments = []
        for t in bundle["course_topics"]:
            t_atts = topic_attempts_map.get(t.id, [])
            if t_atts:
                first_score = round(t_atts[0].percentage, 1)
                latest_score = round(t_atts[-1].percentage, 1)
                best_score = round(max(a.percentage for a in t_atts), 1)
                reassessments = [
                    round(a.percentage, 1)
                    for a in t_atts
                    if a.attempt_type == "reassessment" or t_atts.index(a) > 0
                ]
                all_reassessments.extend(reassessments)
                delta = round(latest_score - first_score, 1) if len(t_atts) >= 2 else 0.0
                if len(t_atts) >= 2:
                    student_deltas.append(delta)
            else:
                first_score = None
                latest_score = None
                best_score = None
                reassessments = []
                delta = 0.0

            per_topic.append({
                "topic_id": t.id,
                "topic_code": t.code,
                "topic_title": t.title,
                "attempts_count": len(t_atts),
                "first_attempt_score": first_score,
                "latest_attempt_score": latest_score,
                "best_score": best_score,
                "improvement_delta": delta,
                "reassessment_scores": reassessments
            })

        non_diag_attempts = [a for a in sorted_attempts if a.attempt_type != "diagnostic"]
        student_initial_score = round(non_diag_attempts[0].percentage, 1) if non_diag_attempts else initial_score
        student_latest_score = round(non_diag_attempts[-1].percentage, 1) if non_diag_attempts else initial_score
        student_best_score = round(max((a.percentage for a in sorted_attempts), default=0.0), 1) if sorted_attempts else None

        if student_latest_score is not None:
            latest_scores_all.append(student_latest_score)

        avg_student_delta = round(sum(student_deltas) / len(student_deltas), 1) if student_deltas else 0.0
        if student_deltas:
            improvement_deltas_all.append(avg_student_delta)

        students_list.append({
            "student_id": sid,
            "name": s_data["name"],
            "email": s_data["email"],
            "initial_diagnostic_score": initial_score,
            "initial_score": student_initial_score,
            "latest_score": student_latest_score,
            "best_score": student_best_score,
            "total_attempts": len(sorted_attempts),
            "total_attempts_count": len(sorted_attempts),
            "reassessments_count": len(all_reassessments),
            "reassessment_scores": all_reassessments,
            "improvement_delta": avg_student_delta if len(sorted_attempts) >= 2 else None,
            "per_topic": per_topic
        })

    class_initial_avg = round(sum(initial_scores_all) / len(initial_scores_all), 1) if initial_scores_all else None
    class_latest_avg = round(sum(latest_scores_all) / len(latest_scores_all), 1) if latest_scores_all else None
    class_improvement_avg = round(sum(improvement_deltas_all) / len(improvement_deltas_all), 1) if improvement_deltas_all else None

    return {
        "class_id": class_obj.id,
        "class_name": class_obj.name,
        "course_id": class_obj.course_id,
        "total_students": len(bundle["students_data"]),
        "class_initial_avg": class_initial_avg,
        "class_latest_avg": class_latest_avg,
        "class_avg_improvement": class_improvement_avg,
        "students": students_list,
        "class_averages": {
            "initial_average": class_initial_avg,
            "latest_average": class_latest_avg,
            "improvement_average": class_improvement_avg
        },
        "thresholds": thresholds_dict
    }


@router.get("/classes/{class_id}/gaps")
def get_class_gaps(
    class_id: int,
    current_user: User = Depends(require_role("faculty", "admin")),
    db: Session = Depends(get_db)
):
    """
    GET /api/faculty/classes/{class_id}/gaps:
    - concept-level gaps (concept, topic, % students below ASSESSMENT_PASS, avg score, number of attempts, students affected)
    - prerequisite gaps (prerequisite topic -> dependent topics blocked, number of students whose prerequisite is below PREREQ_UNLOCK)
    - common class gaps (top N concepts/prerequisites affecting at least COMMON_GAP_PCT of class)
    """
    class_obj = check_new_endpoint_class_access(class_id, current_user, db)
    bundle = load_class_analytics_bundle(class_obj, db)

    thresholds_dict = {
        "prereq_unlock": PREREQ_UNLOCK,
        "assessment_pass": ASSESSMENT_PASS,
        "topic_mastery": TOPIC_MASTERY,
        "co_achieved_default": CO_ACHIEVED_DEFAULT,
        "at_risk_mastery": AT_RISK_MASTERY,
        "inactive_days": INACTIVE_DAYS,
        "common_gap_pct": COMMON_GAP_PCT
    }

    total_students = len(bundle["students_data"])
    if total_students == 0:
        return {
            "class_id": class_obj.id,
            "class_name": class_obj.name,
            "course_id": class_obj.course_id,
            "total_students": 0,
            "concept_gaps": [],
            "prerequisite_gaps": [],
            "common_class_gaps": [],
            "thresholds": thresholds_dict
        }

    student_ids = [s["id"] for s in bundle["students_data"]]
    course_topics = bundle["course_topics"]
    topic_map = bundle["topic_map"]

    # 1. Batch load QuestionAnswerHistory for enrolled students
    qah_rows = db.query(QuestionAnswerHistory).join(
        AssessmentAttempt, QuestionAnswerHistory.attempt_id == AssessmentAttempt.id
    ).filter(
        QuestionAnswerHistory.user_id.in_(student_ids),
        AssessmentAttempt.course_id == class_obj.course_id
    ).all()

    qb_rows = db.query(QuestionBank).filter(QuestionBank.course_id == class_obj.course_id).all()
    qb_topic_map = {q.id: q.topic_id for q in qb_rows}

    concept_map: Dict[str, Dict[str, Any]] = {}
    for r in qah_rows:
        c_name = r.concept or "General"
        tid = qb_topic_map.get(r.question_id)
        if c_name not in concept_map:
            concept_map[c_name] = {
                "concept": c_name,
                "topic_id": tid,
                "students": {}
            }
        elif tid and not concept_map[c_name]["topic_id"]:
            concept_map[c_name]["topic_id"] = tid

        s_dict = concept_map[c_name]["students"].setdefault(r.user_id, {"correct": 0, "total": 0})
        s_dict["total"] += 1
        if r.is_correct:
            s_dict["correct"] += 1

    concept_gaps = []
    for c_name, c_data in concept_map.items():
        tid = c_data["topic_id"]
        t = topic_map.get(tid)
        students_tested = c_data["students"]
        if not students_tested:
            continue

        struggling_students = [
            uid for uid, st in students_tested.items()
            if (st["correct"] / max(st["total"], 1)) * 100.0 < ASSESSMENT_PASS
        ]
        struggling_count = len(struggling_students)
        pct_students_affected = round((struggling_count / total_students) * 100.0, 1)
        total_questions = sum(st["total"] for st in students_tested.values())
        total_correct = sum(st["correct"] for st in students_tested.values())
        avg_score = round((total_correct / max(total_questions, 1)) * 100.0, 1)

        is_common = pct_students_affected >= COMMON_GAP_PCT

        concept_gaps.append({
            "gap_key": f"concept:{c_name}",
            "gap_type": "concept",
            "concept": c_name,
            "topic_id": tid,
            "topic_title": t.title if t else "General",
            "topic_code": t.code if t else "GEN",
            "avg_score": avg_score,
            "total_attempts": total_questions,
            "students_tested_count": len(students_tested),
            "students_affected_count": struggling_count,
            "pct_students_affected": pct_students_affected,
            "is_common_gap": is_common
        })

    concept_gaps.sort(key=lambda x: (x["pct_students_affected"], -x["avg_score"]), reverse=True)

    # 2. Prerequisite gaps
    prereq_gaps = []
    for t in course_topics:
        prereqs = bundle["prereqs_by_topic"].get(t.id, [])
        for p in prereqs:
            prereq_t = topic_map.get(p.prerequisite_topic_id)
            req = p.required_mastery_pct if p.required_mastery_pct is not None else PREREQ_UNLOCK
            struggling_uids = []
            for s_data in bundle["students_data"]:
                m = bundle["mastery_by_user_topic"].get((s_data["id"], p.prerequisite_topic_id))
                m_score = m.overall_mastery if m else 0.0
                if m_score < req:
                    struggling_uids.append(s_data["id"])

            struggling_count = len(struggling_uids)
            pct_affected = round((struggling_count / total_students) * 100.0, 1)
            is_common = pct_affected >= COMMON_GAP_PCT

            prereq_gaps.append({
                "gap_key": f"prereq:{p.prerequisite_topic_id}:{t.id}",
                "gap_type": "prerequisite",
                "prereq_topic_id": p.prerequisite_topic_id,
                "prereq_topic_title": prereq_t.title if prereq_t else f"Topic {p.prerequisite_topic_id}",
                "prereq_topic_code": prereq_t.code if prereq_t else "REQ",
                "dependent_topic_id": t.id,
                "dependent_topic_title": t.title,
                "dependent_topic_code": t.code,
                "required_mastery": req,
                "students_affected_count": struggling_count,
                "pct_students_affected": pct_affected,
                "is_common_gap": is_common
            })

    prereq_gaps.sort(key=lambda x: x["pct_students_affected"], reverse=True)

    # 3. Common class gaps
    common_class_gaps = [g for g in concept_gaps if g["is_common_gap"]] + [g for g in prereq_gaps if g["is_common_gap"]]
    common_class_gaps.sort(key=lambda x: x["pct_students_affected"], reverse=True)

    return {
        "class_id": class_obj.id,
        "class_name": class_obj.name,
        "course_id": class_obj.course_id,
        "total_students": total_students,
        "concept_gaps": concept_gaps,
        "prerequisite_gaps": prereq_gaps,
        "common_class_gaps": common_class_gaps,
        "thresholds": thresholds_dict
    }


@router.get("/classes/{class_id}/gaps/{gap_key:path}")
def get_class_gap_drilldown(
    class_id: int,
    gap_key: str,
    current_user: User = Depends(require_role("faculty", "admin")),
    db: Session = Depends(get_db)
):
    """
    GET /api/faculty/classes/{class_id}/gaps/{gap_key}:
    Lists student names and details affected by a specific concept or prerequisite gap.
    """
    class_obj = check_new_endpoint_class_access(class_id, current_user, db)
    bundle = load_class_analytics_bundle(class_obj, db)

    affected_students = []
    gap_title = gap_key

    if gap_key.startswith("concept:"):
        concept_name = gap_key[len("concept:"):].strip()
        gap_title = f"Concept: {concept_name}"

        student_ids = [s["id"] for s in bundle["students_data"]]
        qah_rows = db.query(QuestionAnswerHistory).join(
            AssessmentAttempt, QuestionAnswerHistory.attempt_id == AssessmentAttempt.id
        ).filter(
            QuestionAnswerHistory.user_id.in_(student_ids),
            AssessmentAttempt.course_id == class_obj.course_id,
            QuestionAnswerHistory.concept == concept_name
        ).all()

        user_acc: Dict[int, Dict[str, int]] = {}
        for r in qah_rows:
            d = user_acc.setdefault(r.user_id, {"correct": 0, "total": 0})
            d["total"] += 1
            if r.is_correct:
                d["correct"] += 1

        for s_data in bundle["students_data"]:
            sid = s_data["id"]
            if sid in user_acc:
                acc = round((user_acc[sid]["correct"] / max(user_acc[sid]["total"], 1)) * 100.0, 1)
                if acc < ASSESSMENT_PASS:
                    affected_students.append({
                        "student_id": sid,
                        "name": s_data["name"],
                        "email": s_data["email"],
                        "score": acc,
                        "attempts_count": user_acc[sid]["total"],
                        "threshold": ASSESSMENT_PASS,
                        "status": "Struggling (<60%)"
                    })
    elif gap_key.startswith("prereq:"):
        parts = gap_key.split(":")
        prereq_id = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
        dep_id = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else None
        prereq_t = bundle["topic_map"].get(prereq_id)
        dep_t = bundle["topic_map"].get(dep_id)
        gap_title = f"Prerequisite Gap: {prereq_t.title if prereq_t else prereq_id} blocks {dep_t.title if dep_t else dep_id}"

        for s_data in bundle["students_data"]:
            sid = s_data["id"]
            m = bundle["mastery_by_user_topic"].get((sid, prereq_id))
            m_score = m.overall_mastery if m else 0.0
            if m_score < PREREQ_UNLOCK:
                affected_students.append({
                    "student_id": sid,
                    "name": s_data["name"],
                    "email": s_data["email"],
                    "mastery": m_score,
                    "threshold": PREREQ_UNLOCK,
                    "gap": round(PREREQ_UNLOCK - m_score, 1),
                    "status": "Below Prerequisite Unlock (<60%)"
                })

    return {
        "class_id": class_obj.id,
        "gap_key": gap_key,
        "gap_title": gap_title,
        "total_affected": len(affected_students),
        "affected_students": affected_students
    }


@router.get("/classes/{class_id}/impact-summary")
def get_class_impact_summary(
    class_id: int,
    current_user: User = Depends(require_role("faculty", "admin")),
    db: Session = Depends(get_db)
):
    """
    GET /api/faculty/classes/{class_id}/impact-summary:
    Class-level: average CO delta since joining, number of students improved/unchanged/declined.
    """
    class_obj = check_new_endpoint_class_access(class_id, current_user, db)
    bundle = load_class_analytics_bundle(class_obj, db)

    total_students = len(bundle["students_data"])
    if total_students == 0:
        return {
            "class_id": class_obj.id,
            "class_name": class_obj.name,
            "course_id": class_obj.course_id,
            "total_students": 0,
            "avg_co_delta_since_joining": 0.0,
            "improved_count": 0,
            "unchanged_count": 0,
            "declined_count": 0,
            "has_enough_data": False,
            "students_summary": []
        }

    students_summary = []
    deltas = []
    improved_count = 0
    unchanged_count = 0
    declined_count = 0

    enrollment_map = {e.student_id: e for e in bundle["enrollments"]}

    for s_data in bundle["students_data"]:
        sid = s_data["id"]
        enr = enrollment_map.get(sid)

        baseline_map = {}
        if enr and enr.baseline_co_json:
            try:
                parsed = json.loads(enr.baseline_co_json)
                if isinstance(parsed, list):
                    for item in parsed:
                        oid = item.get("outcome_id") or item.get("id")
                        if oid:
                            baseline_map[int(oid)] = item.get("attainment_percentage", 0.0)
                elif isinstance(parsed, dict):
                    for k, v in parsed.items():
                        baseline_map[int(k)] = v if isinstance(v, (int, float)) else v.get("attainment_percentage", 0.0)
            except Exception:
                pass

        co_list = bundle["course_outcomes"]
        baseline_vals = [baseline_map.get(co.id, 0.0) for co in co_list]
        current_vals = [
            (bundle["attainment_by_user_co"].get((sid, co.id)).attainment_percentage if bundle["attainment_by_user_co"].get((sid, co.id)) else 0.0)
            for co in co_list
        ]

        b_avg = round(sum(baseline_vals) / len(baseline_vals), 1) if baseline_vals else 0.0
        c_avg = round(sum(current_vals) / len(current_vals), 1) if current_vals else 0.0
        delta = round(c_avg - b_avg, 1)
        deltas.append(delta)

        if delta > 1.0:
            status_label = "improved"
            improved_count += 1
        elif delta < -1.0:
            status_label = "declined"
            declined_count += 1
        else:
            status_label = "unchanged"
            unchanged_count += 1

        students_summary.append({
            "student_id": sid,
            "name": s_data["name"],
            "email": s_data["email"],
            "baseline_avg_co": b_avg,
            "baseline_co_avg": b_avg,
            "current_avg_co": c_avg,
            "current_co_avg": c_avg,
            "delta": delta,
            "status": status_label
        })

    avg_delta = round(sum(deltas) / len(deltas), 1) if deltas else 0.0

    return {
        "class_id": class_obj.id,
        "class_name": class_obj.name,
        "course_id": class_obj.course_id,
        "total_students": total_students,
        "avg_co_delta_since_joining": avg_delta,
        "improved_count": improved_count,
        "unchanged_count": unchanged_count,
        "declined_count": declined_count,
        "has_enough_data": total_students > 0,
        "students_summary": students_summary
    }


@router.get("/classes/{class_id}/students/{student_id}/impact")
def get_class_student_impact(
    class_id: int,
    student_id: int,
    current_user: User = Depends(require_role("faculty", "admin")),
    db: Session = Depends(get_db)
):
    """
    GET /api/faculty/classes/{class_id}/students/{student_id}/impact:
    CO attainment timeline from outcome_attainment_history, baseline at join, current, delta,
    intervention events on the timeline, and before/after comparison for each intervention.
    Clearly labeled as correlation, not proof of cause.
    """
    class_obj = check_new_endpoint_class_access(class_id, current_user, db)
    enrollment = check_new_endpoint_student_access(class_obj, student_id, db)
    bundle = load_class_analytics_bundle(class_obj, db)

    student_data = bundle["student_map"].get(student_id)
    if student_data:
        s_id = student_data["id"]
        s_name = student_data["name"]
        s_email = student_data["email"]
    else:
        student_user = db.query(User).filter(User.id == student_id).first()
        s_id = student_user.id if student_user else student_id
        s_name = (student_user.full_name or student_user.email) if student_user else "Student"
        s_email = student_user.email if student_user else ""

    baseline_co_map = {}
    if enrollment.baseline_co_json:
        try:
            parsed = json.loads(enrollment.baseline_co_json)
            if isinstance(parsed, list):
                for item in parsed:
                    oid = item.get("outcome_id") or item.get("id")
                    if oid:
                        baseline_co_map[int(oid)] = item.get("attainment_percentage", 0.0)
            elif isinstance(parsed, dict):
                for k, v in parsed.items():
                    baseline_co_map[int(k)] = v if isinstance(v, (int, float)) else v.get("attainment_percentage", 0.0)
        except Exception:
            pass

    outcome_code_map = {co.id: co.code for co in bundle["course_outcomes"]}
    current_co_map = {}
    co_delta_map = {}
    for co in bundle["course_outcomes"]:
        oa = bundle["attainment_by_user_co"].get((student_id, co.id))
        c_val = round(oa.attainment_percentage, 1) if oa else 0.0
        b_val = round(baseline_co_map.get(co.id, 0.0), 1)
        current_co_map[co.code] = c_val
        co_delta_map[co.code] = round(c_val - b_val, 1)

    overall_delta = round(sum(co_delta_map.values()) / max(len(co_delta_map), 1), 1)

    history_rows = db.query(OutcomeAttainmentHistory).filter(
        OutcomeAttainmentHistory.user_id == student_id,
        OutcomeAttainmentHistory.course_id == class_obj.course_id
    ).order_by(OutcomeAttainmentHistory.created_at.asc(), OutcomeAttainmentHistory.id.asc()).all()

    co_timeline = []
    for h in history_rows:
        date_str = h.created_at.strftime("%Y-%m-%d %H:%M:%S") if h.created_at else None
        co_timeline.append({
            "id": h.id,
            "outcome_id": h.outcome_id,
            "outcome_code": outcome_code_map.get(h.outcome_id, f"CO{h.outcome_id}"),
            "attainment_pct": round(h.attainment_pct, 1),
            "trigger": h.trigger,
            "date": date_str,
            "created_at": date_str
        })

    events = db.query(InterventionEvent).filter(
        InterventionEvent.student_id == student_id
    ).order_by(InterventionEvent.created_at.asc()).all()

    mastery_histories = db.query(MasteryHistory).filter(
        MasteryHistory.user_id == student_id
    ).order_by(MasteryHistory.created_at.asc()).all()

    interventions_list = []
    before_after_comparisons = []

    for ev in events:
        ev_t = bundle["topic_map"].get(ev.topic_id) if ev.topic_id else None
        ev_date_str = ev.created_at.strftime("%Y-%m-%d %H:%M:%S") if ev.created_at else None
        interventions_list.append({
            "id": ev.id,
            "type": ev.type,
            "created_at": ev_date_str,
            "date": ev_date_str,
            "topic_id": ev.topic_id,
            "topic_title": ev_t.title if ev_t else None,
            "note": ev.note
        })

        ev_date = ev.created_at or datetime.utcnow()
        hist_before = [h for h in history_rows if h.created_at and h.created_at <= ev_date]
        hist_after = [h for h in history_rows if h.created_at and h.created_at > ev_date]

        mast_before = [m for m in mastery_histories if m.created_at and m.created_at <= ev_date]
        mast_after = [m for m in mastery_histories if m.created_at and m.created_at > ev_date]

        has_data = len(hist_before) > 0 and len(hist_after) > 0

        avg_co_before = round(sum(h.attainment_pct for h in hist_before) / len(hist_before), 1) if hist_before else round(sum(baseline_co_map.values()) / max(len(baseline_co_map), 1), 1)
        avg_co_after = round(sum(h.attainment_pct for h in hist_after) / len(hist_after), 1) if hist_after else round(sum(current_co_map.values()) / max(len(current_co_map), 1), 1)

        avg_mast_before = round(sum(m.new_mastery for m in mast_before) / len(mast_before), 1) if mast_before else 0.0
        avg_mast_after = round(sum(m.new_mastery for m in mast_after) / len(mast_after), 1) if mast_after else 0.0

        before_after_comparisons.append({
            "intervention_id": ev.id,
            "type": ev.type,
            "date": ev_date_str,
            "note": ev.note,
            "has_enough_data": has_data,
            "co_before": avg_co_before,
            "co_before_avg": avg_co_before,
            "co_after": avg_co_after,
            "co_after_avg": avg_co_after,
            "co_delta": round(avg_co_after - avg_co_before, 1),
            "mastery_before": avg_mast_before,
            "mastery_before_avg": avg_mast_before,
            "mastery_after": avg_mast_after,
            "mastery_after_avg": avg_mast_after,
            "mastery_delta": round(avg_mast_after - avg_mast_before, 1),
            "attribution_label": "Association, not proof of causation"
        })

    has_enough_data = len(co_timeline) >= 2
    baseline_co_avg = round(sum(baseline_co_map.values()) / max(len(baseline_co_map), 1), 1) if baseline_co_map else 0.0
    current_co_avg = round(sum(current_co_map.values()) / max(len(current_co_map), 1), 1) if current_co_map else 0.0
    joined_at_str = enrollment.joined_at.strftime("%Y-%m-%d %H:%M:%S") if enrollment.joined_at else None

    return {
        "student_id": s_id,
        "student_name": s_name,
        "student_email": s_email,
        "joined_at": joined_at_str,
        "student": {
            "id": s_id,
            "name": s_name,
            "email": s_email,
            "joined_at": joined_at_str
        },
        "class_id": class_obj.id,
        "class_name": class_obj.name,
        "course_id": class_obj.course_id,
        "baseline_co_avg": baseline_co_avg,
        "current_co_avg": current_co_avg,
        "baseline_co_attainment": {
            outcome_code_map.get(co.id, co.code): round(baseline_co_map.get(co.id, 0.0), 1)
            for co in bundle["course_outcomes"]
        },
        "current_co_attainment": current_co_map,
        "co_delta": co_delta_map,
        "overall_co_delta": overall_delta,
        "has_enough_data": has_enough_data,
        "timeline": co_timeline,
        "co_timeline": co_timeline,
        "interventions": interventions_list,
        "before_after_comparisons": before_after_comparisons,
        "attribution_notice": "Association, not proof of causation. Reported trends reflect temporal observation and do not constitute experimental proof of causation."
    }


