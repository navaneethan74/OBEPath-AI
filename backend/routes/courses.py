from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Course, CourseOutcome, Topic, TopicPrerequisite, TopicOutcomeMapping, Resource
from schemas import CourseOut, OutcomeOut, TopicOut

router = APIRouter(prefix="/api/courses", tags=["courses"])

@router.get("")
def list_courses(db: Session = Depends(get_db)):
    courses = db.query(Course).all()
    results = []
    for c in courses:
        co_count = db.query(CourseOutcome).filter(CourseOutcome.course_id == c.id).count()
        topic_count = db.query(Topic).filter(Topic.course_id == c.id).count()
        results.append({
            "id": c.id,
            "code": c.code,
            "title": c.title,
            "description": c.description,
            "category": c.category,
            "level": c.level,
            "is_active": c.is_active,
            "outcome_count": co_count,
            "topic_count": topic_count
        })
    return results

def format_topic_resources(t: Topic) -> List[dict]:
    """Formats resources for a topic, returning DB resources or catalog fallback."""
    res_list = [
        {
            "id": r.id,
            "topic_id": r.topic_id,
            "title": r.title,
            "url": r.url,
            "type": r.resource_type or "Documentation",
            "resource_type": r.resource_type or "Documentation",
            "website_name": r.website_name or ("Faculty Approved Repository" if r.approved_by_faculty else "Curated Reference"),
            "description": r.description or f"Faculty approved learning material for {t.title}.",
            "difficulty": r.difficulty or t.difficulty or "Beginner",
            "approved_by_faculty": bool(r.approved_by_faculty)
        }
        for r in t.resources
    ]

    # When a topic has no DB resources, return curated recommendations as fallback
    if not res_list:
        from ai_agents.resource_agent import ResourceAgent
        agent_recs = ResourceAgent.get_resources_for_topic(t.title)
        res_list = [
            {
                "id": f"rec-{t.id}-{i+1}",
                "topic_id": t.id,
                "title": item["title"],
                "url": item["url"],
                "type": item.get("type", "Documentation"),
                "resource_type": item.get("resource_type", item.get("type", "Documentation")),
                "website_name": item.get("website_name", "Curated Reference"),
                "description": item.get("description", f"Recommended study material for {t.title}."),
                "difficulty": item.get("difficulty", "Beginner"),
                "approved_by_faculty": False
            }
            for i, item in enumerate(agent_recs)
        ]
    return res_list

def format_topic(t: Topic) -> dict:
    """Formats full topic dictionary including prerequisites, outcomes, and resources."""
    prereqs = [p.prerequisite_topic_id for p in t.prerequisites]
    mapped_cos = [m.outcome.code for m in t.outcome_mappings]
    return {
        "id": t.id,
        "course_id": t.course_id,
        "code": t.code,
        "title": t.title,
        "order_index": t.order_index,
        "description": t.description,
        "learning_objective": t.learning_objective,
        "difficulty": t.difficulty,
        "est_minutes": t.est_minutes,
        "prerequisites": prereqs,
        "outcomes": mapped_cos,
        "resources": format_topic_resources(t)
    }

@router.get("/topics/{topic_id}")
def get_topic_by_id(topic_id: int, db: Session = Depends(get_db)):
    """Returns a single topic with all prerequisites, outcomes, and resources."""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return format_topic(topic)

@router.get("/topics/{topic_id}/resources")
def get_topic_resources_by_id(topic_id: int, db: Session = Depends(get_db)):
    """Topic resources API: returns all curated resources (reading, video, practice) for a topic."""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return format_topic_resources(topic)

@router.get("/{course_id}")
def get_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    outcomes = db.query(CourseOutcome).filter(CourseOutcome.course_id == course_id).all()
    topics = db.query(Topic).filter(Topic.course_id == course_id).order_by(Topic.order_index).all()
    topics_data = [format_topic(t) for t in topics]

    return {
        "id": course.id,
        "code": course.code,
        "title": course.title,
        "description": course.description,
        "category": course.category,
        "level": course.level,
        "is_active": course.is_active,
        "outcomes": [
            {
                "id": o.id,
                "course_id": o.course_id,
                "code": o.code,
                "description": o.description,
                "target_attainment_pct": o.target_attainment_pct
            }
            for o in outcomes
        ],
        "topics": topics_data
    }

@router.get("/{course_id}/outcomes")
def get_course_outcomes(course_id: int, db: Session = Depends(get_db)):
    outcomes = db.query(CourseOutcome).filter(CourseOutcome.course_id == course_id).all()
    return outcomes

@router.get("/{course_id}/topics")
def get_course_topics(course_id: int, db: Session = Depends(get_db)):
    """Returns all topics for a course including full learning resources."""
    topics = db.query(Topic).filter(Topic.course_id == course_id).order_by(Topic.order_index).all()
    return [format_topic(t) for t in topics]

@router.get("/{course_id}/topics/{topic_id}")
def get_course_topic_by_id(course_id: int, topic_id: int, db: Session = Depends(get_db)):
    topic = db.query(Topic).filter(Topic.id == topic_id, Topic.course_id == course_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found in this course")
    return format_topic(topic)

@router.get("/{course_id}/topics/{topic_id}/resources")
def get_course_topic_resources(course_id: int, topic_id: int, db: Session = Depends(get_db)):
    topic = db.query(Topic).filter(Topic.id == topic_id, Topic.course_id == course_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found in this course")
    return format_topic_resources(topic)
