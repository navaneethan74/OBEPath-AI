#!/usr/bin/env python3
"""
CLI Script to create or update a Faculty account for local development / testing.

Usage:
    export FACULTY_EMAIL="faculty@domain.com"
    export FACULTY_PASSWORD="SecurePassword123"
    python backend/scripts/create_faculty.py

Or with command-line arguments:
    python backend/scripts/create_faculty.py --email faculty@domain.com --password SecurePassword123 --name "Dr. Jane Doe"
"""

import os
import sys
import argparse
from datetime import datetime

# Add backend directory to sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from database import engine, SessionLocal
from models import User, AgentLog
from core.security import hash_password, validate_password_rules

def main():
    parser = argparse.ArgumentParser(description="Create or update a faculty user account.")
    parser.add_argument("--email", type=str, help="Faculty email address (or set FACULTY_EMAIL env var)")
    parser.add_argument("--password", type=str, help="Faculty password (or set FACULTY_PASSWORD env var)")
    parser.add_argument("--name", type=str, default=None, help="Faculty full name (optional)")
    parser.add_argument("--force-change-pwd", action="store_true", help="Require password change upon first login")

    args = parser.parse_args()

    email = (args.email or os.getenv("FACULTY_EMAIL", "")).strip().lower()
    password = (args.password or os.getenv("FACULTY_PASSWORD", "")).strip()
    full_name = (args.name or os.getenv("FACULTY_NAME", "Faculty Instructor")).strip()
    must_change = args.force_change_pwd or (os.getenv("FACULTY_MUST_CHANGE_PASSWORD", "false").lower() == "true")

    if not email:
        print("ERROR: Faculty email is required. Provide --email or set FACULTY_EMAIL environment variable.")
        sys.exit(1)

    if not password:
        print("ERROR: Faculty password is required. Provide --password or set FACULTY_PASSWORD environment variable.")
        sys.exit(1)

    try:
        validate_password_rules(password)
    except Exception as e:
        print(f"ERROR: Password validation failed: {getattr(e, 'detail', str(e))}")
        sys.exit(1)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email.ilike(email)).first()
        hashed_pw = hash_password(password)

        if user:
            print(f"Existing account found for {email}. Updating to role='faculty'...")
            user.role = "faculty"
            user.password_hash = hashed_pw
            if full_name:
                user.full_name = full_name
            user.must_change_password = must_change
            action_desc = "faculty_account_updated_via_cli"
        else:
            print(f"Creating new faculty account for {email}...")
            user = User(
                email=email,
                full_name=full_name,
                password_hash=hashed_pw,
                role="faculty",
                must_change_password=must_change,
                created_at=datetime.utcnow()
            )
            db.add(user)
            action_desc = "faculty_account_created_via_cli"

        db.add(AgentLog(
            user_id=user.id if user.id else None,
            agent_name="CLI Faculty Provisioner",
            action=action_desc,
            message=f"Faculty account for {email} provisioned via CLI (must_change={must_change}).",
            created_at=datetime.utcnow()
        ))

        db.commit()
        db.refresh(user)
        print(f"SUCCESS: Faculty account ready.")
        print(f"  User ID:             {user.id}")
        print(f"  Email:               {user.email}")
        print(f"  Name:                {user.full_name}")
        print(f"  Role:                {user.role}")
        print(f"  Must Change Password:{user.must_change_password}")
    except Exception as exc:
        db.rollback()
        print(f"FATAL: Failed to provision faculty account: {exc}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
