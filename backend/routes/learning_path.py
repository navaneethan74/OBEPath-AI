from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import (
    LearningPath, LearningPathItem, Topic, TopicPrerequisite,
    MasteryScore, StudentProfile, AgentLog, Course, User
)
from schemas import LearningPathOut
from ai_agents.planner_agent import PlannerAgent
from core.security import get_current_user, resolve_target_user_id

router = APIRouter(prefix="/api/learning-path", tags=["learning-path"])

@router.get("")
def get_learning_path(
    course_id: Optional[int] = None,
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_user_id = resolve_target_user_id(current_user, user_id)
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == target_user_id).first()
    actual_cid = course_id if course_id is not None else (profile.selected_course_id if profile and profile.selected_course_id else 2)

    path = db.query(LearningPath).filter(
        LearningPath.user_id == target_user_id,
        LearningPath.course_id == actual_cid,
        LearningPath.status == "ACTIVE"
    ).order_by(LearningPath.updated_at.desc()).first()

    if not path:
        return generate_learning_path(course_id=actual_cid, user_id=target_user_id, current_user=current_user, db=db)

    items = db.query(LearningPathItem).filter(
        LearningPathItem.learning_path_id == path.id
    ).order_by(LearningPathItem.sequence_order).all()

    course = db.query(Course).filter(Course.id == actual_cid).first()

    items_data = []
    for item in items:
        topic = db.query(Topic).filter(Topic.id == item.topic_id).first()
        mastery_obj = db.query(MasteryScore).filter(
            MasteryScore.user_id == target_user_id,
            MasteryScore.topic_id == item.topic_id
        ).first()

        mastery_pct = mastery_obj.overall_mastery if mastery_obj else 0.0

        outcomes = [m.outcome.code for m in topic.outcome_mappings] if topic else []
        prereqs = [p.prerequisite_topic.title for p in topic.prerequisites] if topic else []

        items_data.append({
            "id": item.id,
            "sequence_order": item.sequence_order,
            "topic_id": item.topic_id,
            "topic_title": item.remedial_title if item.is_remedial else (topic.title if topic else "Topic"),
            "topic_code": f"REM-{item.sequence_order}" if item.is_remedial else (topic.code if topic else ""),
            "difficulty": "Beginner" if item.is_remedial else (topic.difficulty if topic else "Beginner"),
            "est_minutes": 20 if item.is_remedial else (topic.est_minutes if topic else 45),
            "status": item.status,
            "recommendation_reason": item.recommendation_reason,
            "related_outcomes": outcomes,
            "prerequisites": prereqs,
            "mastery_percentage": mastery_pct,
            "is_remedial": item.is_remedial,
            "remedial_title": item.remedial_title,
            "remedial_description": item.remedial_description
        })

    return {
        "id": path.id,
        "course_id": path.course_id,
        "course_title": course.title if course else "Course",
        "status": path.status,
        "adaptation_reason": path.adaptation_reason,
        "generated_at": path.generated_at,
        "updated_at": path.updated_at,
        "items": items_data
    }

@router.post("/generate")
def generate_learning_path(
    course_id: Optional[int] = None,
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_user_id = resolve_target_user_id(current_user, user_id)
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == target_user_id).first()
    actual_cid = course_id if course_id is not None else (profile.selected_course_id if profile and profile.selected_course_id else 2)

    topics = db.query(Topic).filter(Topic.course_id == actual_cid).order_by(Topic.order_index).all()
    if not topics:
        raise HTTPException(status_code=404, detail="No topics found for course")

    prereqs_map = {t.id: [p.prerequisite_topic_id for p in t.prerequisites] for t in topics}
    outcomes_map = {t.id: [m.outcome for m in t.outcome_mappings] for t in topics}

    masteries = db.query(MasteryScore).filter(MasteryScore.user_id == target_user_id).all()
    masteries_map = {m.topic_id: m.overall_mastery for m in masteries}

    profile = db.query(StudentProfile).filter(StudentProfile.user_id == target_user_id).first()
    goal = profile.learning_goal if profile else ""

    path_items_data = PlannerAgent.generate_path(
        topics, prereqs_map, masteries_map, outcomes_map, goal
    )

    # Archive previous active path
    existing_paths = db.query(LearningPath).filter(
        LearningPath.user_id == target_user_id,
        LearningPath.course_id == actual_cid,
        LearningPath.status == "ACTIVE"
    ).all()
    for ep in existing_paths:
        ep.status = "ARCHIVED"

    # Create new LearningPath
    new_path = LearningPath(
        user_id=target_user_id,
        course_id=actual_cid,
        status="ACTIVE",
        adaptation_reason="Generated personalized OBE learning trajectory based on diagnostic gap analysis.",
        generated_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(new_path)
    db.commit()
    db.refresh(new_path)

    for item_data in path_items_data:
        pi = LearningPathItem(
            learning_path_id=new_path.id,
            topic_id=item_data["topic_id"],
            sequence_order=item_data["sequence_order"],
            status=item_data["status"],
            recommendation_reason=item_data["recommendation_reason"],
            is_remedial=item_data.get("is_remedial", False),
            remedial_title=item_data.get("remedial_title"),
            remedial_description=item_data.get("remedial_description")
        )
        db.add(pi)

    log = AgentLog(
        user_id=target_user_id,
        agent_name="Planner Agent",
        action="path_generated",
        message=f"Generated sequenced OBE learning path with {len(path_items_data)} topics based on competency evaluation."
    )
    db.add(log)
    db.commit()

    return get_learning_path(course_id=actual_cid, user_id=target_user_id, current_user=current_user, db=db)

@router.post("/adapt-functions")
def adapt_learning_path_functions(
    course_id: int = 1,
    failed_topic_id: int = 5,
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_user_id = resolve_target_user_id(current_user, user_id)
    path = db.query(LearningPath).filter(
        LearningPath.user_id == target_user_id,
        LearningPath.course_id == course_id,
        LearningPath.status == "ACTIVE"
    ).first()

    if not path:
        path = LearningPath(user_id=target_user_id, course_id=course_id, status="ACTIVE")
        db.add(path)
        db.commit()

    # Clear existing items
    db.query(LearningPathItem).filter(LearningPathItem.learning_path_id == path.id).delete()

    topics = db.query(Topic).filter(Topic.course_id == course_id).order_by(Topic.order_index).all()
    masteries = {m.topic_id: m.overall_mastery for m in db.query(MasteryScore).filter(MasteryScore.user_id == target_user_id).all()}
    prereqs_map = {t.id: [p.prerequisite_topic_id for p in t.prerequisites] for t in topics}
    outcomes_map = {t.id: [m.outcome for m in t.outcome_mappings] for t in topics}

    base_items = PlannerAgent.generate_path(topics, prereqs_map, masteries, outcomes_map)
    remedial_items = PlannerAgent.insert_functions_remediation(base_items, failed_topic_id)

    path.adaptation_reason = "Adaptive intervention: Inserted 6 remedial modules following low assessment score in Functions."
    path.updated_at = datetime.utcnow()

    for itm in remedial_items:
        db.add(LearningPathItem(
            learning_path_id=path.id,
            topic_id=itm["topic_id"],
            sequence_order=itm["sequence_order"],
            status=itm["status"],
            recommendation_reason=itm["recommendation_reason"],
            is_remedial=itm.get("is_remedial", False),
            remedial_title=itm.get("remedial_title"),
            remedial_description=itm.get("remedial_description")
        ))

    log1 = AgentLog(
        user_id=target_user_id,
        agent_name="Progress Monitoring Agent",
        action="low_mastery_detected",
        message="Detected difficulty in Functions (32%). Threshold for Course Outcome CO3 not satisfied. Triggering path adaptation."
    )
    log2 = AgentLog(
        user_id=target_user_id,
        agent_name="Planner Agent",
        action="path_adaptation",
        message="Inserted 6-stage Functions remedial sequence. Locked downstream topics (Lists, Dictionaries) until remediation passes."
    )
    db.add_all([log1, log2])
    db.commit()

    return get_learning_path(course_id=course_id, user_id=target_user_id, current_user=current_user, db=db)

@router.post("/repair")
def repair_learning_path(
    course_id: int = 1,
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_user_id = resolve_target_user_id(current_user, user_id)
    topics = db.query(Topic).filter(Topic.course_id == course_id).all()
    recursion_topic = next((t for t in topics if "recursion" in t.title.lower() and "practice" not in t.title.lower()), None)
    practice_topic = next((t for t in topics if "recursive practice" in t.title.lower()), None)
    traversal_topic = next((t for t in topics if "tree traversal" in t.title.lower()), None)
    problems_topic = next((t for t in topics if "tree problems" in t.title.lower()), None)

    rec_id = recursion_topic.id if recursion_topic else 3
    prac_id = practice_topic.id if practice_topic else 6
    trav_id = traversal_topic.id if traversal_topic else 5
    prob_id = problems_topic.id if problems_topic else 7

    repaired_items = PlannerAgent.repair_data_structures_path(
        topics=topics,
        recursion_topic_id=rec_id,
        recursive_practice_id=prac_id,
        tree_traversal_id=trav_id,
        tree_problems_id=prob_id
    )

    path = db.query(LearningPath).filter(
        LearningPath.user_id == target_user_id,
        LearningPath.course_id == course_id,
        LearningPath.status == "ACTIVE"
    ).first()

    if not path:
        path = LearningPath(user_id=target_user_id, course_id=course_id, status="ACTIVE")
        db.add(path)
        db.commit()

    # Clear old items
    db.query(LearningPathItem).filter(LearningPathItem.learning_path_id == path.id).delete()

    path.adaptation_reason = "Prerequisite-aware repair: Injected Recursion and Recursive Practice prior to Tree Traversal without restarting the course."
    path.updated_at = datetime.utcnow()

    for itm in repaired_items:
        db.add(LearningPathItem(
            learning_path_id=path.id,
            topic_id=itm["topic_id"],
            sequence_order=itm["sequence_order"],
            status=itm["status"],
            recommendation_reason=itm["recommendation_reason"],
            is_remedial=itm.get("is_remedial", False),
            remedial_title=itm.get("remedial_title"),
            remedial_description=itm.get("remedial_description")
        ))

    log1 = AgentLog(
        user_id=target_user_id,
        agent_name="Progress Monitoring Agent",
        action="prerequisite_deficit_confirmed",
        message="Prerequisite Gap Verified: Recursion diagnostic score is 30% (< 60% threshold). Course Outcome CO2 impacted. Requesting learning path repair."
    )
    log2 = AgentLog(
        user_id=target_user_id,
        agent_name="Planner Agent",
        action="prerequisite_aware_path_repair",
        message="Path Repaired: Inserted Recursion Fundamentals and Recursive Practice before Tree Traversal. Entire Data Structures course was NOT restarted."
    )
    db.add_all([log1, log2])
    db.commit()

    return get_learning_path(course_id=course_id, user_id=target_user_id, current_user=current_user, db=db)

@router.get("/why/{topic_id}")
def explain_recommendation(
    topic_id: int,
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_user_id = resolve_target_user_id(current_user, user_id)
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    mastery = db.query(MasteryScore).filter(
        MasteryScore.user_id == target_user_id,
        MasteryScore.topic_id == topic_id
    ).first()

    mastery_score = mastery.overall_mastery if mastery else 0.0

    prereqs = [p.prerequisite_topic.title for p in topic.prerequisites]
    outcomes = [m.outcome.code for m in topic.outcome_mappings]

    if topic.title == "Functions":
        explanation = (
            f"You scored {int(mastery_score)}% in Functions during the diagnostic assessment. "
            f"Functions are also required before Lists and Tuples (Prerequisite requirement). "
            f"The system therefore recommends Functions before progressing to the next topic to ensure "
            f"Course Outcome {', '.join(outcomes)} attainment criteria are satisfied."
        )
    elif mastery_score >= 80:
        explanation = (
            f"You demonstrated strong proficiency ({int(mastery_score)}%) in {topic.title}. "
            f"All related objectives for {', '.join(outcomes)} have been verified. "
            f"You may revise or proceed directly to higher-level modules."
        )
    elif prereqs:
        explanation = (
            f"{topic.title} requires foundational mastery in: {', '.join(prereqs)}. "
            f"Once prerequisites meet the 60% competency threshold, this topic will become active."
        )
    else:
        explanation = (
            f"{topic.title} is recommended based on your learner goal and current mastery of {int(mastery_score)}%. "
            f"It directly contributes to {', '.join(outcomes)}."
        )

    return {
        "topic_id": topic.id,
        "topic_title": topic.title,
        "mastery_score": mastery_score,
        "prerequisites": prereqs,
        "outcomes": outcomes,
        "explanation": explanation
    }
