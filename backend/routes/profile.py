from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import StudentProfile, User
from schemas import ProfileUpdate, ProfileOut
from core.security import get_current_user, resolve_target_user_id

router = APIRouter(prefix="/api/profile", tags=["profile"])

@router.get("")
def get_profile(
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_id = resolve_target_user_id(current_user, user_id)
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == target_id).first()
    if not profile:
        profile = StudentProfile(user_id=target_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)

    user = db.query(User).filter(User.id == target_id).first()
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "full_name": user.full_name if user else "Student",
        "email": user.email if user else "",
        "student_id": profile.student_id or "S101",
        "program": profile.program or "B.Tech AI & Data Science",
        "semester": profile.semester or 4,
        "current_level": profile.current_level or "Beginner",
        "academic_level": profile.academic_level,
        "selected_course_id": profile.selected_course_id,
        "learning_goal": profile.learning_goal,
        "prior_knowledge": profile.prior_knowledge,
        "preferred_format": profile.preferred_format,
        "daily_time_minutes": profile.daily_time_minutes,
        "target_completion_date": profile.target_completion_date,
        "department": profile.department or "Computer Science & Engineering",
        "onboarding_completed": getattr(profile, 'onboarding_completed', False),
        "diagnostic_completed": profile.diagnostic_completed
    }

@router.put("")
def update_profile(
    data: ProfileUpdate,
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_id = resolve_target_user_id(current_user, user_id)
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == target_id).first()
    if not profile:
        profile = StudentProfile(user_id=target_id)
        db.add(profile)

    user = db.query(User).filter(User.id == target_id).first()
    data_dict = data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else data.dict(exclude_unset=True)
    if user and "full_name" in data_dict and data_dict["full_name"]:
        user.full_name = data_dict["full_name"]

    for field, val in data_dict.items():
        if hasattr(profile, field):
            setattr(profile, field, val)

    db.commit()
    db.refresh(profile)
    return get_profile(user_id=target_id, current_user=current_user, db=db)
