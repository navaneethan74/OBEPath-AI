import os
import re
import uuid
import math
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from database import get_db
from models import (
    User, StudentProfile, Topic, MasteryScore, CourseOutcome,
    OutcomeAttainment, AgentLog
)
from schemas import UserCreate, UserLogin, GoogleAuthRequest, ChangePasswordRequest
from core.security import (
    hash_password,
    verify_password,
    verify_and_upgrade_password,
    create_access_token,
    get_current_user,
    validate_password_rules
)
from core.rate_limiter import get_client_ip, enforce_rate_limit, reset_rate_limits

router = APIRouter(prefix="/api/auth", tags=["auth"])

# In-memory failed login attempts tracker: key is f"{email}:{ip}" -> list of failed attempt datetimes
# NOTE: In-memory rate limiter for local/single-worker use. Production with multiple workers needs Redis or a distributed cache.
_login_failed_attempts: Dict[str, List[datetime]] = defaultdict(list)
LOGIN_MAX_FAILED_ATTEMPTS = 5
LOGIN_LOCKOUT_WINDOW = timedelta(minutes=15)

# Dummy bcrypt hash generated at startup to prevent timing attacks when checking nonexistent emails
DUMMY_BCRYPT_HASH = hash_password("dummy_password_for_constant_time_verification_12345")

def reset_login_rate_limits():
    """Clears in-memory login failed attempt records (used in tests)."""
    _login_failed_attempts.clear()
    reset_rate_limits()

@router.post("/register")
def register(user_in: UserCreate, request: Request, db: Session = Depends(get_db)):
    client_ip = get_client_ip(request)
    enforce_rate_limit(
        key=f"register:ip:{client_ip}",
        limit=10,
        window_seconds=60,
        detail="Too many registration attempts. Please try again later."
    )
    email_clean = user_in.email.strip().lower()
    existing = db.query(User).filter(User.email.ilike(email_clean)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered. Please sign in instead.")

    # Validate password complexity
    raw_password = user_in.password.strip()
    validate_password_rules(raw_password)

    # Security rule: Registration ALWAYS creates role="student".
    # Any role or admin flag submitted by the client is strictly ignored.
    user = User(
        email=email_clean,
        password_hash=hash_password(raw_password),
        full_name=user_in.full_name.strip(),
        role="student"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Initialize student profile & pedagogical baselines
    profile = StudentProfile(
        user_id=user.id,
        academic_level="Undergraduate (Semester 4)",
        department="Computer Science & Engineering",
        onboarding_completed=False,
        diagnostic_completed=False,
        learning_goal="Master core computing and algorithmic fundamentals",
        daily_time_minutes=60
    )
    db.add(profile)

    # Initialize baseline masteries for all topics
    topics = db.query(Topic).all()
    for t in topics:
        db.add(MasteryScore(
            user_id=user.id,
            topic_id=t.id,
            overall_mastery=0.0,
            classification="Needs Improvement"
        ))

    # Initialize baseline outcome attainments
    outcomes = db.query(CourseOutcome).all()
    for oc in outcomes:
        db.add(OutcomeAttainment(
            user_id=user.id,
            course_id=oc.course_id,
            outcome_id=oc.id,
            attainment_percentage=0.0,
            status="Needs Improvement"
        ))

    # Add welcome agent log
    db.add(AgentLog(
        user_id=user.id,
        agent_name="Planner Agent",
        action="account_created",
        message=f"Welcome {user.full_name}! Account created. Ready for student onboarding & course selection.",
        created_at=datetime.utcnow()
    ))
    db.commit()

    token = create_access_token(user.id, user.role)

    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role
        },
        "token": token,
        "is_new_user": True,
        "onboarding_completed": False
    }

@router.post("/login")
def login(login_data: UserLogin, request: Request, db: Session = Depends(get_db)):
    email_clean = login_data.email.strip().lower()

    # Determine client IP (reads X-Forwarded-For only when TRUST_PROXY=true)
    client_ip = get_client_ip(request)

    rate_key = f"{email_clean}:{client_ip}"
    now = datetime.utcnow()
    window_start = now - LOGIN_LOCKOUT_WINDOW

    # Prune expired attempts outside the 15-minute window
    _login_failed_attempts[rate_key] = [
        t for t in _login_failed_attempts[rate_key] if t >= window_start
    ]

    # Brute-force check: max 5 failed attempts per email+IP in 15 minutes
    if len(_login_failed_attempts[rate_key]) >= LOGIN_MAX_FAILED_ATTEMPTS:
        oldest_attempt = _login_failed_attempts[rate_key][0]
        seconds_remaining = max(1, math.ceil((oldest_attempt + LOGIN_LOCKOUT_WINDOW - now).total_seconds()))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please try again later.",
            headers={"Retry-After": str(seconds_remaining)}
        )

    user = db.query(User).filter(User.email.ilike(email_clean)).first()
    raw_password = login_data.password.strip()

    if not user:
        # Constant-time mitigation against email enumeration timing attacks
        verify_password(raw_password, DUMMY_BCRYPT_HASH)
        _login_failed_attempts[rate_key].append(now)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Verify password with bcrypt (and upgrade legacy SHA-256 hash if applicable)
    is_valid, upgraded_hash = verify_and_upgrade_password(raw_password, user.password_hash)

    if not is_valid:
        _login_failed_attempts[rate_key].append(now)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Server-Side Expected Role Verification
    if login_data.expected_role:
        expected_clean = login_data.expected_role.strip().lower()
        if user.role != expected_clean:
            # Credentials are valid, but not authorized for this specific portal.
            # Return 403 and issue NO token.
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="These credentials are not valid for this portal"
            )

    # Login succeeded: reset failed attempts counter for this email+IP
    _login_failed_attempts.pop(rate_key, None)

    # If user was stored with legacy SHA-256, upgrade to bcrypt in place
    if upgraded_hash:
        user.password_hash = upgraded_hash
        db.commit()

    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    onboarding_done = getattr(profile, "onboarding_completed", False) if profile else False

    token = create_access_token(user.id, user.role)

    must_change = bool(getattr(user, "must_change_password", False))

    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "must_change_password": must_change
        },
        "token": token,
        "is_new_user": not onboarding_done,
        "onboarding_completed": onboarding_done,
        "must_change_password": must_change
    }

@router.post("/google")
def google_auth(payload: GoogleAuthRequest, db: Session = Depends(get_db)):
    """
    Authenticates or registers a user via a verified Google OAuth2 ID token.
    Rejects direct client-provided emails and requires a valid 'credential' token verified with Google.
    """
    google_client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    if not google_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google login not configured"
        )

    credential = payload.credential.strip() if payload.credential else ""
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Google credential token."
        )

    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests
        id_info = id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            google_client_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Google token verification failed: {str(e)}"
        )

    email = id_info.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google ID token does not contain a verified email address."
        )

    email_clean = email.strip().lower()
    user = db.query(User).filter(User.email.ilike(email_clean)).first()

    is_new = False
    if not user:
        is_new = True
        user_name = id_info.get("name") or payload.full_name or email_clean.split("@")[0].title()
        user = User(
            email=email_clean,
            password_hash=hash_password(uuid.uuid4().hex + uuid.uuid4().hex),
            full_name=user_name.strip(),
            role="student"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        profile = StudentProfile(
            user_id=user.id,
            academic_level="Undergraduate (Semester 4)",
            department="Computer Science & Engineering",
            onboarding_completed=False,
            diagnostic_completed=False,
            learning_goal="Master core computing and algorithmic fundamentals",
            daily_time_minutes=60
        )
        db.add(profile)

        topics = db.query(Topic).all()
        for t in topics:
            db.add(MasteryScore(
                user_id=user.id,
                topic_id=t.id,
                overall_mastery=0.0,
                classification="Needs Improvement"
            ))

        outcomes = db.query(CourseOutcome).all()
        for oc in outcomes:
            db.add(OutcomeAttainment(
                user_id=user.id,
                course_id=oc.course_id,
                outcome_id=oc.id,
                attainment_percentage=0.0,
                status="Needs Improvement"
            ))

        db.add(AgentLog(
            user_id=user.id,
            agent_name="Planner Agent",
            action="google_account_created",
            message=f"Welcome {user.full_name}! Initialized student profile via verified Google Authentication.",
            created_at=datetime.utcnow()
        ))
        db.commit()

    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    onboarding_done = getattr(profile, "onboarding_completed", False) if profile else False

    token = create_access_token(user.id, user.role)

    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role
        },
        "token": token,
        "is_new_user": is_new or not onboarding_done,
        "onboarding_completed": onboarding_done
    }

@router.get("/me")
def get_auth_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns the currently authenticated user's profile and role from verified JWT.
    """
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    return {
        "id": current_user.id,
        "name": current_user.full_name,
        "email": current_user.email,
        "role": current_user.role,
        "onboarding_completed": getattr(profile, "onboarding_completed", False) if profile else False,
        "must_change_password": bool(getattr(current_user, "must_change_password", False))
    }

@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Authenticated endpoint to change user password. Requires old_password verification
    and enforces standard password complexity rules on new_password.
    Sets must_change_password = False upon success.
    """
    raw_old = payload.old_password.strip()
    raw_new = payload.new_password.strip()

    is_valid, _ = verify_and_upgrade_password(raw_old, current_user.password_hash)
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect."
        )

    if raw_old == raw_new:
        raise HTTPException(
            status_code=400,
            detail="New password must be different from your current password."
        )

    validate_password_rules(raw_new)

    current_user.password_hash = hash_password(raw_new)
    current_user.must_change_password = False
    db.commit()

    return {
        "status": "success",
        "message": "Password changed successfully.",
        "must_change_password": False
    }

