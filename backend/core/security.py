import os
import re
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Tuple
from dotenv import load_dotenv
import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

# Ensure environment variables are loaded
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

from database import get_db
from models import User

# Password hashing context (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_jwt_secret() -> str:
    """
    Retrieves and validates the JWT_SECRET from environment.
    The app refuses to run if JWT_SECRET is missing or shorter than 32 characters.
    """
    secret = os.getenv("JWT_SECRET", "").strip()
    if not secret or len(secret) < 32:
        raise RuntimeError(
            "CRITICAL: JWT_SECRET environment variable is missing or shorter than 32 characters. "
            "The application refuses to start without a cryptographically secure key."
        )
    return secret

# Enforce JWT_SECRET requirement on module load
JWT_SECRET = get_jwt_secret()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def hash_password(password: str) -> str:
    """Hashes a plaintext password using bcrypt."""
    # Bcrypt maximum effective password length is 72 bytes
    return pwd_context.hash(password[:72])

def validate_password_rules(password: str) -> None:
    """Enforces basic password rules: minimum 8 characters, at least one letter and one number."""
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long."
        )
    if not re.search(r"[a-zA-Z]", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one letter."
        )
    if not re.search(r"[0-9]", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one number."
        )

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a bcrypt hash."""
    try:
        return pwd_context.verify(plain_password[:72], hashed_password)
    except Exception:
        return False

def verify_and_upgrade_password(plain_password: str, stored_hash: str) -> Tuple[bool, Optional[str]]:
    """
    Verifies a password against the stored hash.
    Supports backward compatibility: if stored_hash is an old unsalted SHA-256 hex string (64 chars),
    verifies it against SHA-256 and generates an upgraded bcrypt hash.
    Returns (is_valid, new_hash_if_upgraded_or_needed).
    """
    if not stored_hash or not plain_password:
        return False, None

    # Check for legacy 64-char hex SHA-256 hash
    is_sha256 = len(stored_hash) == 64 and bool(re.match(r"^[0-9a-fA-F]{64}$", stored_hash))
    if is_sha256:
        input_sha256 = hashlib.sha256(plain_password.encode()).hexdigest()
        if input_sha256.lower() == stored_hash.lower():
            # Password matches legacy hash; upgrade to bcrypt immediately
            new_hash = hash_password(plain_password)
            return True, new_hash
        return False, None

    # Standard bcrypt verification
    try:
        if pwd_context.verify(plain_password[:72], stored_hash):
            if pwd_context.needs_update(stored_hash):
                return True, hash_password(plain_password)
            return True, None
    except Exception:
        pass

    return False, None

def create_access_token(user_id: int, role: str) -> str:
    """
    Generates a cryptographically signed JWT access token.
    Claims: sub (subject user id), role, exp (expiration), iat (issued at).
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expire,
        "iat": now
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm=ALGORITHM)

def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency that extracts, verifies, and validates the Bearer JWT.
    Loads and returns the User model from the database.
    Raises HTTP 401 on missing, malformed, expired, invalid tokens, or nonexistent users.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Missing Authorization header.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    parts = authorization.strip().split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization format. Expected 'Bearer <token>'.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = parts[1].strip()

    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token payload missing subject identifier.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        user_id = int(user_id_str)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except (jwt.InvalidTokenError, ValueError, Exception):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or forged authentication token.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account associated with this token was not found.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return user

def require_role(*allowed_roles: str):
    """
    Dependency factory that checks whether the authenticated user has one of the allowed roles.
    The role is enforced from the live database record, preventing token claim tampering.
    Raises HTTP 403 Forbidden if not authorized.
    """
    def role_dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Access requires role in {allowed_roles}. Current role '{current_user.role}' is not authorized."
            )
        return current_user
    return role_dependency

require_faculty_or_admin = require_role("faculty", "admin")
require_faculty = require_role("faculty")

def resolve_target_user_id(current_user: User, requested_user_id: Optional[int]) -> int:
    """
    Safely resolves the target user_id for an operation.
    Enforces student data isolation: students cannot access or modify another student's data.
    Admins may access or override other user IDs.
    """
    if requested_user_id is not None and requested_user_id != current_user.id:
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: You are not authorized to access or modify data for user_id={requested_user_id}."
            )
        return requested_user_id
    return current_user.id

