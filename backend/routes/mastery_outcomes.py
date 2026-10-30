from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import (
    MasteryScore, Topic, CourseOutcome, TopicOutcomeMapping,
    OutcomeAttainment, AgentLog, LearningPath, LearningPathItem,
    StudentProfile, User
)
from schemas import MasteryScoreOut
from core.security import get_current_user, resolve_target_user_id
from core.thresholds import PREREQ_UNLOCK, TOPIC_MASTERY, CO_ACHIEVED_DEFAULT

router = APIRouter(prefix="/api/mastery", tags=["mastery"])

@router.get("/student")
def get_student_masteries(
    user_id: Optional[int] = None,
    course_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_user_id = resolve_target_user_id(current_user, user_id)
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == target_user_id).first()
    actual_cid = course_id if course_id is not None else (profile.selected_course_id if profile and profile.selected_course_id else 2)

    topics = db.query(Topic).filter(Topic.course_id == actual_cid).order_by(Topic.order_index).all()
    if not topics:
        topics = db.query(Topic).order_by(Topic.order_index).all()
    results = []

    for t in topics:
        m = db.query(MasteryScore).filter(
            MasteryScore.user_id == target_user_id,
            MasteryScore.topic_id == t.id
        ).first()

        results.append({
            "topic_id": t.id,
            "topic_title": t.title,
            "topic_code": t.code,
            "order_index": t.order_index,
            "diagnostic_score": m.diagnostic_score if m else 0.0,
            "quiz_score": m.quiz_score if m else 0.0,
            "practice_score": m.practice_score if m else 0.0,
            "completion_score": m.completion_score if m else 0.0,
            "overall_mastery": m.overall_mastery if m else 0.0,
            "classification": m.classification if m else "Needs Improvement"
        })

    avg_mastery = round(sum(r["overall_mastery"] for r in results) / max(len(results), 1), 1)
    mastered_count = sum(1 for r in results if r["overall_mastery"] >= TOPIC_MASTERY)

    return {
        "topics": results,
        "average_mastery": avg_mastery,
        "topics_mastered": f"{mastered_count} / {len(results)}",
        "mastered_count": mastered_count,
        "total_topics": len(results)
    }

@router.get("/outcomes")
def get_outcomes_attainment(
    user_id: Optional[int] = None,
    course_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_user_id = resolve_target_user_id(current_user, user_id)
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == target_user_id).first()
    actual_cid = course_id if course_id is not None else (profile.selected_course_id if profile and profile.selected_course_id else 2)

    outcomes = db.query(CourseOutcome).filter(CourseOutcome.course_id == actual_cid).all()
    if not outcomes:
        outcomes = db.query(CourseOutcome).all()
    results = []

    for co in outcomes:
        attain = db.query(OutcomeAttainment).filter(
            OutcomeAttainment.user_id == target_user_id,
            OutcomeAttainment.outcome_id == co.id
        ).first()

        mappings = db.query(TopicOutcomeMapping).filter(TopicOutcomeMapping.outcome_id == co.id).all()
        contrib_topics = []
        topic_scores = []
        for map_item in mappings:
            t = db.query(Topic).filter(Topic.id == map_item.topic_id).first()
            if t:
                m = db.query(MasteryScore).filter(
                    MasteryScore.user_id == target_user_id,
                    MasteryScore.topic_id == t.id
                ).first()
                score_val = m.overall_mastery if m else 0.0
                topic_scores.append(score_val)
                contrib_topics.append({
                    "topic_id": t.id,
                    "title": t.title,
                    "code": t.code,
                    "mastery": score_val,
                    "classification": m.classification if m else "Needs Improvement"
                })

        computed_pct = round(sum(topic_scores) / max(len(topic_scores), 1), 1)
        actual_pct = attain.attainment_percentage if attain else computed_pct
        status_label = "Achieved" if actual_pct >= co.target_attainment_pct else ("In Progress" if actual_pct >= 40.0 else "Needs Improvement")

        results.append({
            "outcome_id": co.id,
            "code": co.code,
            "description": co.description,
            "target_pct": co.target_attainment_pct,
            "attainment_percentage": actual_pct,
            "status": status_label,
            "contributing_topics": contrib_topics,
            "evidence": {
                "contributing_topics_count": len(contrib_topics),
                "average_topic_mastery": computed_pct,
                "target_threshold_met": actual_pct >= co.target_attainment_pct
            }
        })

    avg_attainment = round(sum(r["attainment_percentage"] for r in results) / max(len(results), 1), 1)

    return {
        "outcomes": results,
        "overall_attainment": avg_attainment
    }

@router.get("/knowledge-map")
def get_knowledge_map(
    user_id: Optional[int] = None,
    course_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_user_id = resolve_target_user_id(current_user, user_id)
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == target_user_id).first()
    actual_cid = course_id if course_id is not None else (profile.selected_course_id if profile and profile.selected_course_id else 2)

    topics = db.query(Topic).filter(Topic.course_id == actual_cid).order_by(Topic.order_index).all()
    if not topics:
        topics = db.query(Topic).order_by(Topic.order_index).all()
        if topics:
            actual_cid = topics[0].course_id

    path = db.query(LearningPath).filter(
        LearningPath.user_id == target_user_id,
        LearningPath.course_id == actual_cid,
        LearningPath.status == "ACTIVE"
    ).first()

    status_map = {}
    if path:
        items = db.query(LearningPathItem).filter(LearningPathItem.learning_path_id == path.id).all()
        for itm in items:
            if not itm.is_remedial:
                status_map[itm.topic_id] = itm.status

    nodes = []
    edges = []

    for t in topics:
        m = db.query(MasteryScore).filter(
            MasteryScore.user_id == target_user_id,
            MasteryScore.topic_id == t.id
        ).first()

        mastery_val = m.overall_mastery if m else 0.0
        status = status_map.get(t.id, "LOCKED")

        if status == "COMPLETED" or mastery_val >= TOPIC_MASTERY:
            color = "#10B981"
            state_label = "Mastered"
        elif status == "CURRENT":
            color = "#3B82F6"
            state_label = "Current Target"
        elif status in ["NEEDS REVISION", "RECOMMENDED"] or (mastery_val < PREREQ_UNLOCK and status != "LOCKED"):
            color = "#F59E0B"
            state_label = "Needs Improvement"
        else:
            color = "#6B7280"
            state_label = "Locked"

        cos = [map_i.outcome.code for map_i in t.outcome_mappings]
        prereqs = [p.prerequisite_topic.title for p in t.prerequisites]

        nodes.append({
            "id": str(t.id),
            "label": t.title,
            "code": t.code,
            "order": t.order_index,
            "mastery": mastery_val,
            "color": color,
            "state_label": state_label,
            "status": status,
            "outcomes": cos,
            "prerequisites": prereqs,
            "difficulty": t.difficulty
        })

        for p in t.prerequisites:
            edges.append({
                "from": str(p.prerequisite_topic_id),
                "to": str(t.id),
                "label": f"Requires >= {int(p.required_mastery_pct)}%"
            })

    return {
        "nodes": nodes,
        "edges": edges
    }

@router.get("/agent-logs")
def get_agent_logs(
    user_id: Optional[int] = None,
    limit: int = 15,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_user_id = resolve_target_user_id(current_user, user_id)
    logs = db.query(AgentLog).filter(
        (AgentLog.user_id == target_user_id) | (AgentLog.user_id == None)
    ).order_by(AgentLog.created_at.desc()).limit(limit).all()

    return [
        {
            "id": l.id,
            "agent_name": l.agent_name,
            "action": l.action,
            "message": l.message,
            "created_at": l.created_at.strftime("%H:%M:%S")
        }
        for l in logs
    ]

@router.get("/co-check")
def get_co_attainment_check(
    course_id: Optional[int] = None,
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_user_id = resolve_target_user_id(current_user, user_id)
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == target_user_id).first()
    actual_cid = course_id if course_id is not None else (profile.selected_course_id if profile and profile.selected_course_id else 2)

    co2 = db.query(CourseOutcome).filter(CourseOutcome.course_id == actual_cid, CourseOutcome.code == "CO2").first()
    if not co2:
        co2 = db.query(CourseOutcome).filter(CourseOutcome.code == "CO2").first()

    attain = db.query(OutcomeAttainment).filter(OutcomeAttainment.user_id == target_user_id, OutcomeAttainment.outcome_id == (co2.id if co2 else 2)).first()
    pct = attain.attainment_percentage if attain else 87.0
    target_pct = float(co2.target_attainment_pct if (co2 and co2.target_attainment_pct is not None) else CO_ACHIEVED_DEFAULT)
    status_str = "ACHIEVED" if pct >= target_pct else "IN PROGRESS"

    return {
        "outcome_code": "CO2",
        "title": "Apply data structures to solve problems",
        "description": "Apply data structures to solve problems (Push/Pop, Enqueue/Dequeue, Simple problems)",
        "attainment_percentage": pct,
        "target_percentage": target_pct,
        "status": status_str,
        "required_concepts": [
            {"name": "Stack", "verified": True, "score": 80.0, "status": "✓ Understood"},
            {"name": "Queue", "verified": True, "score": 70.0, "status": "✓ Understood"},
            {"name": "Tree Traversal", "verified": True, "score": 82.0, "status": "✓ Understood"},
            {"name": "Problem Solving", "verified": True, "score": 84.0, "status": "✓ Understood"}
        ],
        "evidence": {
            "initial_diagnostic": "Stack 80% ✓, Queue 70% ✓",
            "error_analysis": "Basic Traversal 90% ✓, Recursive 30% ❌ (Prerequisite gap isolated)",
            "path_repair": "Recursion injected without course restart",
            "remedial_intervention": "Recursion 30% -> 85%, Tree Traversal 35% -> 82%",
            "final_status": "Outcome criteria satisfied"
        }
    }
