from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import User, Course, AgentLog, LearningPath
from schemas import FacultyCreateRequest
from core.security import require_role, hash_password, validate_password_rules

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/metrics")
def get_admin_metrics(
    admin_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    total_users = db.query(User).count()
    student_count = db.query(User).filter(User.role == "student").count()
    faculty_count = db.query(User).filter(User.role == "faculty").count()
    courses_count = db.query(Course).count()
    active_paths = db.query(LearningPath).filter(LearningPath.status == "ACTIVE").count()
    agent_executions = db.query(AgentLog).count()

    return {
        "total_users": total_users,
        "students": student_count,
        "faculty": faculty_count,
        "courses": courses_count,
        "active_learning_sessions": active_paths,
        "ai_agent_executions": agent_executions,
        "system_status": "All AI Agents Operational",
        "llm_engine": "Modular Hybrid (OpenAI + Deterministic Fallback Active)"
    }

@router.get("/logs")
def get_system_logs(
    limit: int = 50,
    admin_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    logs = db.query(AgentLog).order_by(AgentLog.created_at.desc()).limit(limit).all()
    return [
        {
            "id": l.id,
            "agent": l.agent_name,
            "action": l.action,
            "message": l.message,
            "timestamp": l.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }
        for l in logs
    ]

@router.post("/users")
def create_faculty_user(
    payload: FacultyCreateRequest,
    admin_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """
    Admin-only endpoint to create a new faculty account.
    Role is strictly fixed to 'faculty', must_change_password is initialized to True.
    """
    raw_name = (payload.full_name or payload.name or "").strip()
    if not raw_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Faculty name is required."
        )

    raw_email = payload.email.strip().lower()
    if not raw_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Faculty email is required."
        )

    raw_pwd = (payload.temporary_password or payload.password or "").strip()
    if not raw_pwd:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Temporary password is required."
        )

    validate_password_rules(raw_pwd)

    existing = db.query(User).filter(User.email.ilike(raw_email)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An account with email '{raw_email}' already exists."
        )

    new_faculty = User(
        email=raw_email,
        full_name=raw_name,
        password_hash=hash_password(raw_pwd),
        role="faculty",
        must_change_password=True,
        created_at=datetime.utcnow()
    )
    db.add(new_faculty)

    db.add(AgentLog(
        user_id=admin_user.id,
        agent_name="Admin Agent",
        action="faculty_account_created",
        message=f"Admin {admin_user.email} created faculty account for {new_faculty.email} (must_change_password=True).",
        created_at=datetime.utcnow()
    ))
    db.commit()
    db.refresh(new_faculty)

    return {
        "id": new_faculty.id,
        "email": new_faculty.email,
        "full_name": new_faculty.full_name,
        "role": new_faculty.role,
        "must_change_password": new_faculty.must_change_password,
        "created_at": new_faculty.created_at.isoformat() if new_faculty.created_at else None
    }

@router.get("/users")
def get_admin_users(
    role: Optional[str] = "faculty",
    admin_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """
    Admin-only endpoint to list accounts, defaults to filtering by role=faculty.
    """
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    users = query.order_by(User.created_at.desc()).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role,
            "must_change_password": bool(getattr(u, "must_change_password", False)),
            "created_at": u.created_at.isoformat() if u.created_at else None
        }
        for u in users
    ]

