#!/usr/bin/env python3
"""
CLI Script to create or update an Admin account.
Security Rule: Admin accounts can NEVER be created through public or authenticated APIs.
Only system operators with server access may execute this script.

Usage:
    export ADMIN_EMAIL="admin@domain.com"
    export ADMIN_PASSWORD="SecurePassword123"
    python backend/scripts/create_admin.py

Or with command-line arguments:
    python backend/scripts/create_admin.py --email admin@domain.com --password SecurePassword123 --name "Admin Name"
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
    parser = argparse.ArgumentParser(description="Create or update an administrative user account.")
    parser.add_argument("--email", type=str, help="Admin email address (or set ADMIN_EMAIL env var)")
    parser.add_argument("--password", type=str, help="Admin password (or set ADMIN_PASSWORD env var)")
    parser.add_argument("--name", type=str, default=None, help="Admin full name (optional)")

    args = parser.parse_args()

    email = (args.email or os.getenv("ADMIN_EMAIL", "")).strip().lower()
    password = (args.password or os.getenv("ADMIN_PASSWORD", "")).strip()
    full_name = (args.name or os.getenv("ADMIN_NAME", "System Administrator")).strip()

    if not email:
        print("ERROR: Admin email is required. Provide --email or set ADMIN_EMAIL environment variable.")
        sys.exit(1)

    if not password:
        print("ERROR: Admin password is required. Provide --password or set ADMIN_PASSWORD environment variable.")
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
            print(f"Existing account found for {email}. Updating to role='admin' with new credentials...")
            user.role = "admin"
            user.password_hash = hashed_pw
            if full_name:
                user.full_name = full_name
            user.must_change_password = False
            action_desc = "admin_account_updated_via_cli"
        else:
            print(f"Creating new admin account for {email}...")
            user = User(
                email=email,
                full_name=full_name,
                password_hash=hashed_pw,
                role="admin",
                must_change_password=False,
                created_at=datetime.utcnow()
            )
            db.add(user)
            action_desc = "admin_account_created_via_cli"

        db.add(AgentLog(
            user_id=user.id if user.id else None,
            agent_name="CLI Admin Provisioner",
            action=action_desc,
            message=f"Admin account for {email} provisioned securely via server CLI.",
            created_at=datetime.utcnow()
        ))

        db.commit()
        db.refresh(user)
        print(f"SUCCESS: Admin account ready.")
        print(f"  User ID: {user.id}")
        print(f"  Email:   {user.email}")
        print(f"  Name:    {user.full_name}")
        print(f"  Role:    {user.role}")
    except Exception as exc:
        db.rollback()
        print(f"FATAL: Failed to provision admin account: {exc}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
