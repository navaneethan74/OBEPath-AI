from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from database import get_db
from models import (
    Topic, Course, MasteryScore, StudentProfile, LearningPath,
    LearningPathItem, AgentLog, QuestionBank, QuestionAnswerHistory, User
)
from schemas import (
    TutorChatRequest, TutorChatResponse,
    TutorModalityRequest, TutorModalityResponse
)
from ai_agents.gemini_service import gemini_tutor_service
from core.security import get_current_user, resolve_target_user_id
from core.rate_limiter import (
    get_requester_key,
    enforce_rate_limit,
    get_cached_tutor_explanation,
    set_cached_tutor_explanation
)

router = APIRouter(prefix="/api/ai-tutor", tags=["ai-tutor"])

@router.get("/status")
def get_tutor_status():
    """
    Returns safe AI Tutor status confirming if GEMINI_API_KEY is configured
    WITHOUT exposing the actual key.
    """
    configured = gemini_tutor_service.is_configured()
    return {
        "status": "online",
        "gemini_configured": configured,
        "model": gemini_tutor_service.primary_model
    }

@router.post("/chat", response_model=TutorChatResponse)
async def chat_with_tutor(
    req: TutorChatRequest,
    request: Request,
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Personalized AI Tutor conversation endpoint powered by Google Gemini.
    Embeds student's current learning context (course, topic, mastery, level, weak sub-concepts).
    Rate limited to 10 requests per minute per user/IP.
    Caches repeated explanations in memory.
    """
    # 1. Rate limiting (10 requests/minute)
    rate_key = get_requester_key(request, current_user, prefix="tutor_chat")
    enforce_rate_limit(
        key=rate_key,
        limit=10,
        window_seconds=60,
        detail="Rate limit exceeded for AI Tutor chat (max 10 requests per minute). Please wait."
    )

    target_user_id = resolve_target_user_id(current_user, user_id)
    topic = db.query(Topic).filter(Topic.id == req.topic_id).first()
    if not topic:
        topic = db.query(Topic).first()
        if not topic:
            raise HTTPException(status_code=404, detail="No topics found")

    course = db.query(Course).filter(Course.id == (req.course_id or topic.course_id)).first()

    # 1. Fetch real mastery
    mastery_obj = db.query(MasteryScore).filter(
        MasteryScore.user_id == target_user_id,
        MasteryScore.topic_id == topic.id
    ).first()
    mastery_score = round(mastery_obj.overall_mastery, 1) if mastery_obj else 0.0
    classification = mastery_obj.classification if mastery_obj else "DEVELOPING"

    # 2. Student profile & level
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == target_user_id).first()
    learning_level = profile.current_level if profile else "Beginner"

    # 3. Identify weak sub-concepts from real student attempts
    recent_wrong = (
        db.query(QuestionBank.sub_concept)
        .join(QuestionAnswerHistory, QuestionAnswerHistory.question_id == QuestionBank.id)
        .filter(
            QuestionAnswerHistory.user_id == target_user_id,
            QuestionBank.topic_id == topic.id,
            QuestionAnswerHistory.is_correct == False
        )
        .limit(5)
        .all()
    )
    weak_sub_concepts = list({w[0] for w in recent_wrong if w[0]})

    # 4. Learning path item status
    path = db.query(LearningPath).filter(
        LearningPath.user_id == target_user_id,
        LearningPath.course_id == (course.id if course else topic.course_id),
        LearningPath.status == "ACTIVE"
    ).first()

    path_item = None
    if path:
        path_item = db.query(LearningPathItem).filter(
            LearningPathItem.learning_path_id == path.id,
            LearningPathItem.topic_id == topic.id
        ).first()

    path_status = path_item.status if path_item else "ACTIVE"

    # Assemble comprehensive learning context for Gemini
    outcomes = [m.outcome.code for m in topic.outcome_mappings] if topic.outcome_mappings else []
    prerequisites = [p.prerequisite_topic.title for p in topic.prerequisites] if topic.prerequisites else []

    context = {
        "course_id": course.id if course else topic.course_id,
        "course_title": course.title if course else "Computer Science",
        "course_code": course.code if course else "CS201",
        "topic_id": topic.id,
        "topic_title": topic.title,
        "topic_code": topic.code or f"TOPIC-{topic.id}",
        "learning_objective": topic.learning_objective or "",
        "mastery_score": mastery_score,
        "topic_classification": classification,
        "learning_level": learning_level,
        "outcomes": outcomes,
        "prerequisites": prerequisites,
        "weak_sub_concepts": weak_sub_concepts,
        "path_status": path_status
    }

    # Check in-memory explanation cache
    cache_key = f"chat:{topic.id}:{req.action or ''}:{(req.message or '').strip().lower()}:{int(mastery_score)}"
    cached_reply = get_cached_tutor_explanation(cache_key)
    if cached_reply:
        return cached_reply

    # Execute Gemini API call
    res = await gemini_tutor_service.chat_with_tutor(
        context=context,
        user_message=req.message,
        action=req.action,
        history=req.history
    )

    # Save to memory cache for repeated explanations
    set_cached_tutor_explanation(cache_key, res)

    # Log safe event to AgentLog
    log = AgentLog(
        user_id=target_user_id,
        agent_name="Gemini Tutor Agent",
        action=req.action or "gemini_tutor_explanation",
        message=f"Provided pedagogical response for topic '{topic.title}' (Mastery: {int(mastery_score)}%, Status: {classification}). Model: {res.get('model_used')}"
    )
    db.add(log)
    db.commit()

    return res

@router.post("/generate-modality", response_model=TutorModalityResponse)
async def generate_modality(
    req: TutorModalityRequest,
    request: Request,
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generates dynamic educational modality lessons powered by Google Gemini.
    Rate limited to 10 requests per minute per user/IP.
    Caches repeated modality explanations in memory.
    """
    # 1. Rate limiting (10 requests/minute)
    rate_key = get_requester_key(request, current_user, prefix="tutor_modality")
    enforce_rate_limit(
        key=rate_key,
        limit=10,
        window_seconds=60,
        detail="Rate limit exceeded for modality generation (max 10 requests per minute). Please wait."
    )

    target_user_id = resolve_target_user_id(current_user, user_id)
    topic = db.query(Topic).filter(Topic.id == req.topic_id).first()
    if not topic:
        topic = db.query(Topic).first()
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")

    course = db.query(Course).filter(Course.id == topic.course_id).first()

    mastery_obj = db.query(MasteryScore).filter(
        MasteryScore.user_id == target_user_id,
        MasteryScore.topic_id == topic.id
    ).first()
    mastery_score = mastery_obj.overall_mastery if mastery_obj else 50.0

    context = {
        "course_id": course.id if course else topic.course_id,
        "course_title": course.title if course else "Course",
        "topic_id": topic.id,
        "topic_title": topic.title,
        "mastery_score": mastery_score
    }

    # Check in-memory explanation cache
    cache_key = f"modality:{topic.id}:{req.modality}:{(req.user_prompt or '').strip().lower()}:{req.pedagogical_style or ''}:{int(mastery_score)}"
    cached_modality = get_cached_tutor_explanation(cache_key)
    if cached_modality:
        return cached_modality

    res = await gemini_tutor_service.generate_modality_lesson(
        context=context,
        modality=req.modality,
        user_prompt=req.user_prompt or "",
        pedagogical_style=req.pedagogical_style or ""
    )
    res["topic_id"] = topic.id

    # Store in memory cache
    set_cached_tutor_explanation(cache_key, res)

    log = AgentLog(
        user_id=target_user_id,
        agent_name="Gemini Content Agent",
        action="modality_generation",
        message=f"Generated {req.modality} modality for '{topic.title}' (Mastery: {int(mastery_score)}%)."
    )
    db.add(log)
    db.commit()

    return res
