import os
import re
import logging
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from models import User
from core.security import hash_password, validate_password_rules

logger = logging.getLogger("obe.bootstrap")

DEMO_SEED_ENV_VARS = [
    "STUDENT_PASSWORD",
    "FACULTY_PASSWORD",
    "DEMO_SEED",
    "SEED_DEMO_USERS",
    "SEED_DATA"
]

def run_production_startup_checks():
    """
    Strict validation performed when ENV=production.
    Refuses to start if:
    1. JWT_SECRET is missing or shorter than 32 characters.
    2. DATABASE_URL is SQLite (production requires PostgreSQL such as Neon).
    3. Any demo-seed environment variables are set.
    4. ALLOWED_ORIGINS is unset or '*'.
    """
    env_val = os.getenv("ENV", os.getenv("ENVIRONMENT", "development")).strip().lower()
    is_prod = env_val in ("production", "prod")
    if not is_prod:
        return

    # 1. JWT_SECRET check
    jwt_secret = os.getenv("JWT_SECRET", "").strip()
    if not jwt_secret or len(jwt_secret) < 32:
        raise RuntimeError(
            "Production startup error: JWT_SECRET environment variable is missing or shorter than 32 characters. "
            "Refusing to start in ENV=production without a secure key."
        )

    # 2. DATABASE_URL check (SQLite rejected in production)
    db_url = os.getenv("DATABASE_URL", "").strip().lower()
    if not db_url or "sqlite" in db_url:
        raise RuntimeError(
            "Production startup error: SQLite database is not permitted in ENV=production. "
            "DATABASE_URL must be configured with a PostgreSQL database (e.g. Neon Postgres)."
        )

    # 3. Demo-seed environment variables check
    found_demo_vars = [var for var in DEMO_SEED_ENV_VARS if os.getenv(var)]
    if found_demo_vars:
        raise RuntimeError(
            f"Production startup error: Demo seeding environment variables {found_demo_vars} are not permitted in ENV=production. "
            "Production deployments must not contain demo credentials or demo seed flags."
        )

    # 4. ALLOWED_ORIGINS check
    cors_raw = os.getenv("ALLOWED_ORIGINS", "").strip()
    if not cors_raw or cors_raw == "*":
        raise RuntimeError(
            "Production startup error: ALLOWED_ORIGINS must be an explicit comma-separated list and cannot be unset or '*' in ENV=production."
        )
    origins = [o.strip() for o in cors_raw.split(",") if o.strip()]
    if "*" in origins:
        raise RuntimeError(
            "Production startup error: Wildcard '*' is strictly rejected in ALLOWED_ORIGINS."
        )


def bootstrap_admin_if_needed(db: Session) -> Optional[User]:
    """
    On startup, if no admin exists and ADMIN_EMAIL and ADMIN_PASSWORD env vars are set
    (password rules enforced), create that admin once.
    CRITICAL: Never log the password.
    """
    admin_email = os.getenv("ADMIN_EMAIL", "").strip().lower()
    admin_password = os.getenv("ADMIN_PASSWORD", "").strip()

    if not admin_email or not admin_password:
        return None

    # Check if ANY admin account currently exists
    existing_admin = db.query(User).filter(User.role == "admin").first()
    if existing_admin:
        logger.info("[Admin Bootstrap] Admin account already exists. Skipping bootstrap.")
        return existing_admin

    # Enforce password rules (at least 8 chars, 1 letter, 1 number)
    validate_password_rules(admin_password)

    # Basic email validation
    if "@" not in admin_email or "." not in admin_email:
        raise ValueError("[Admin Bootstrap] ADMIN_EMAIL must be a valid email address.")

    user = db.query(User).filter(User.email.ilike(admin_email)).first()
    if user:
        user.role = "admin"
        user.password_hash = hash_password(admin_password)
        user.must_change_password = False
    else:
        user = User(
            email=admin_email,
            password_hash=hash_password(admin_password),
            full_name=os.getenv("ADMIN_NAME", "System Administrator").strip(),
            role="admin",
            must_change_password=False,
            created_at=datetime.utcnow()
        )
        db.add(user)

    db.commit()
    db.refresh(user)
    # Log safe confirmation: NEVER print or log passwords
    logger.info(f"[Admin Bootstrap] Successfully bootstrapped initial admin account: {admin_email}")
    return user
