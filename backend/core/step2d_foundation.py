"""
core/step2d_foundation.py
Step 2D: Data Foundation Utilities
- Deduplication of duplicate OutcomeAttainmentHistory rows
- Reassessment classification and historical backfill
- QuestionAnswerHistory concept tagging and backfill
- Intervention events schema initialization and cohort event logging
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import text, inspect
from sqlalchemy.orm import Session

from database import engine
from models import (
    Base, OutcomeAttainmentHistory, AssessmentAttempt,
    QuestionAnswerHistory, QuestionBank, ClassEnrollment,
    InterventionEvent, MasteryHistory, LearningPath, LearningPathItem
)

logger = logging.getLogger("step2d_foundation")

def init_step2d_schema(db_engine=None):
    """
    Ensures intervention_events table exists and concept column is added
    to question_answer_history if not present.
    """
    eng = db_engine or engine
    Base.metadata.create_all(bind=eng)

    with eng.connect() as conn:
        inspector = inspect(eng)
        columns = [c["name"] for c in inspector.get_columns("question_answer_history")]
        if "concept" not in columns:
            logger.info("Adding 'concept' column to question_answer_history table")
            conn.execute(text("ALTER TABLE question_answer_history ADD COLUMN concept VARCHAR DEFAULT 'General'"))
            conn.commit()

def deduplicate_outcome_attainment_history(db: Session, window_seconds: int = 300) -> int:
    """
    Safe cleanup of duplicate outcome_attainment_history rows created by earlier state-read bug
    (same user, course, outcome, attainment_pct and trigger within a short window; keeps earliest).
    Returns count of removed duplicate rows.
    """
    rows = db.query(OutcomeAttainmentHistory).order_by(
        OutcomeAttainmentHistory.user_id,
        OutcomeAttainmentHistory.course_id,
        OutcomeAttainmentHistory.outcome_id,
        OutcomeAttainmentHistory.trigger,
        OutcomeAttainmentHistory.attainment_pct,
        OutcomeAttainmentHistory.created_at,
        OutcomeAttainmentHistory.id
    ).all()

    to_delete_ids = []
    prev = None

    for r in rows:
        if prev is not None:
            same_key = (
                r.user_id == prev.user_id and
                r.course_id == prev.course_id and
                r.outcome_id == prev.outcome_id and
                r.trigger == prev.trigger and
                abs(r.attainment_pct - prev.attainment_pct) < 0.001
            )
            if same_key:
                diff_sec = abs((r.created_at - prev.created_at).total_seconds()) if (r.created_at and prev.created_at) else 0
                if diff_sec <= window_seconds:
                    to_delete_ids.append(r.id)
                    # Keep prev as earliest anchor
                    continue
        prev = r

    if to_delete_ids:
        # Delete in chunks to prevent SQLite variable limits
        chunk_size = 500
        for i in range(0, len(to_delete_ids), chunk_size):
            chunk = to_delete_ids[i:i + chunk_size]
            db.query(OutcomeAttainmentHistory).filter(OutcomeAttainmentHistory.id.in_(chunk)).delete(synchronize_session=False)
        db.commit()

    return len(to_delete_ids)

def backfill_reassessment_attempts(db: Session) -> int:
    """
    Backfills old attempts safely:
    - Diagnostic attempts remain "diagnostic".
    - First attempt on a topic remains initial ("practice", "quiz", "assessment").
    - If a student attempts a topic again after a previous attempt on that topic (or after a remedial module was inserted),
      sets attempt_type="reassessment".
    Returns count of updated attempts.
    """
    attempts = db.query(AssessmentAttempt).order_by(
        AssessmentAttempt.user_id,
        AssessmentAttempt.topic_id,
        AssessmentAttempt.created_at,
        AssessmentAttempt.id
    ).all()

    # Pre-index remedial items: (user_id, topic_id) -> min created_at or True
    remedial_items = db.query(LearningPathItem).join(LearningPath).filter(
        LearningPathItem.is_remedial == True
    ).all()
    remedial_user_topics = set()
    for ri in remedial_items:
        if ri.learning_path and ri.topic_id:
            remedial_user_topics.add((ri.learning_path.user_id, ri.topic_id))

    seen_user_topics = set()
    updated_count = 0

    for att in attempts:
        if att.attempt_type == "diagnostic":
            # Diagnostic is always initial
            continue

        if att.topic_id is not None:
            key = (att.user_id, att.topic_id)
            has_prior_attempt = key in seen_user_topics
            has_remedial = key in remedial_user_topics

            if has_prior_attempt or has_remedial:
                if att.attempt_type != "reassessment":
                    att.attempt_type = "reassessment"
                    updated_count += 1
            else:
                seen_user_topics.add(key)

    if updated_count > 0:
        db.commit()

    return updated_count

def backfill_question_concepts(db: Session) -> Dict[str, Any]:
    """
    Verifies question-level sub_concept/concept tags in question_answer_histories.
    Populates missing concept tags from question_bank.sub_concept.
    Questions without a tag go to concept "General" for that topic.
    Returns stats dict: {total_rows, tagged_count, untagged_count, updated_count}.
    """
    qb_map = {q.id: (q.sub_concept or "").strip() for q in db.query(QuestionBank).all()}
    qah_rows = db.query(QuestionAnswerHistory).all()

    total_rows = len(qah_rows)
    tagged_count = 0
    untagged_count = 0
    updated_count = 0

    for row in qah_rows:
        sc = qb_map.get(row.question_id, "")
        target_concept = sc if sc else "General"

        if sc:
            tagged_count += 1
        else:
            untagged_count += 1

        if row.concept != target_concept:
            row.concept = target_concept
            updated_count += 1

    if updated_count > 0:
        db.commit()

    return {
        "total_rows": total_rows,
        "tagged_count": tagged_count,
        "untagged_count": untagged_count,
        "untagged_share_pct": round((untagged_count / max(total_rows, 1)) * 100.0, 1),
        "updated_count": updated_count
    }

def backfill_class_joined_interventions(db: Session) -> int:
    """
    Creates 'class_joined' InterventionEvent rows for existing class enrollments.
    Returns count of created events.
    """
    enrollments = db.query(ClassEnrollment).filter(ClassEnrollment.status == "active").all()
    created_count = 0

    for enr in enrollments:
        exists = db.query(InterventionEvent).filter(
            InterventionEvent.student_id == enr.student_id,
            InterventionEvent.class_id == enr.class_id,
            InterventionEvent.type == "class_joined"
        ).first()
        if not exists:
            event = InterventionEvent(
                student_id=enr.student_id,
                class_id=enr.class_id,
                topic_id=None,
                type="class_joined",
                created_at=enr.joined_at,
                note=f"Joined cohort enrollment"
            )
            db.add(event)
            created_count += 1

    if created_count > 0:
        db.commit()

    return created_count

def record_intervention_event(
    db: Session,
    student_id: int,
    event_type: str,
    class_id: Optional[int] = None,
    topic_id: Optional[int] = None,
    note: Optional[str] = None,
    created_at: Optional[datetime] = None
) -> InterventionEvent:
    """
    Inserts a new intervention event (remedial_inserted, path_adapted, teacher_flag, class_joined).
    Resolves class_id from active enrollment if not provided.
    """
    if class_id is None:
        enr = db.query(ClassEnrollment).filter(
            ClassEnrollment.student_id == student_id,
            ClassEnrollment.status == "active"
        ).order_by(ClassEnrollment.joined_at.desc()).first()
        if enr:
            class_id = enr.class_id

    event = InterventionEvent(
        student_id=student_id,
        class_id=class_id,
        topic_id=topic_id,
        type=event_type,
        created_at=created_at or datetime.utcnow(),
        note=note
    )
    db.add(event)
    db.commit()
    return event
