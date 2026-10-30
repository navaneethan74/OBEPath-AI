import os
import sys
import uuid
import re
import pytest
from fastapi.testclient import TestClient

# Ensure backend directory is in sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from main import app
from database import SessionLocal
from models import User
from core.security import hash_password
from routes.auth import reset_login_rate_limits
import seed_data

client = TestClient(app)

def create_temp_user(role: str, password: str = "TestSecurePassword123") -> str:
    """Helper to create an isolated temporary user with a random email."""
    db = SessionLocal()
    unique_id = uuid.uuid4().hex[:8]
    email = f"temp_{role}_{unique_id}@testinstitution.edu"
    user = User(
        email=email,
        full_name=f"Temp {role.capitalize()} {unique_id}",
        role=role,
        password_hash=hash_password(password)
    )
    db.add(user)
    db.commit()
    db.close()
    return email

# ==============================================================================
# TEST 1: /demo-student no longer exists (404)
# ==============================================================================
def test_demo_student_endpoint_removed():
    """Verify the /demo-student backdoor endpoint has been removed completely."""
    res = client.post("/api/auth/demo-student")
    assert res.status_code == 404, f"Expected 404 Not Found for /demo-student, got {res.status_code}"

    # Also check /demo-student without /api prefix if routed anywhere
    res_raw = client.post("/demo-student")
    assert res_raw.status_code == 404

# ==============================================================================
# TEST 2: with ENV=production no demo users are seeded and no default password works
# ==============================================================================
def test_env_production_seeding_and_no_default_password(monkeypatch):
    """
    Verify that with ENV=production, seed_users creates NO demo accounts,
    and no fallback default password works.
    """
    monkeypatch.setenv("ENV", "production")
    monkeypatch.delenv("STUDENT_PASSWORD", raising=False)
    monkeypatch.delenv("FACULTY_PASSWORD", raising=False)
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)

    db = SessionLocal()
    # Call seed_users directly under production environment
    users = seed_data.seed_users(db)
    assert users == (None, None, None), "seed_users must return (None, None, None) in production"

    # Verify that seed_users exited immediately without creating anything
    # And test that a nonexistent demo email with default password 'demo' is rejected with 401
    ghost_email = f"nonexistent_{uuid.uuid4().hex[:6]}@obe.edu"
    res = client.post("/api/auth/login", json={
        "email": ghost_email,
        "password": "demo"
    })
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid email or password"
    db.close()

# ==============================================================================
# TEST 3: Student credentials on Faculty tab: 403, no token
# ==============================================================================
def test_student_credentials_on_faculty_tab_rejected():
    """
    When a student tries to log in on the Faculty tab (expected_role='faculty'),
    server returns 403 Forbidden with generic message and NO token.
    """
    password = "StudentPassword123"
    student_email = create_temp_user("student", password)

    res = client.post("/api/auth/login", json={
        "email": student_email,
        "password": password,
        "expected_role": "faculty"
    })

    assert res.status_code == 403, f"Expected 403, got {res.status_code}: {res.text}"
    body = res.json()
    assert body["detail"] == "These credentials are not valid for this portal"
    assert "token" not in body

# ==============================================================================
# TEST 4: Faculty credentials on /admin-login: 403, no token
# ==============================================================================
def test_faculty_credentials_on_admin_login_rejected():
    """
    When faculty credentials are submitted to /admin-login (expected_role='admin'),
    server returns 403 Forbidden with generic message and NO token.
    """
    password = "FacultyPassword123"
    faculty_email = create_temp_user("faculty", password)

    res = client.post("/api/auth/login", json={
        "email": faculty_email,
        "password": password,
        "expected_role": "admin"
    })

    assert res.status_code == 403, f"Expected 403, got {res.status_code}: {res.text}"
    body = res.json()
    assert body["detail"] == "These credentials are not valid for this portal"
    assert "token" not in body

# ==============================================================================
# TEST 5: Admin credentials on public tabs: 403, no token
# ==============================================================================
def test_admin_credentials_on_public_tabs_rejected():
    """
    When admin credentials are submitted to the Student tab or Faculty tab,
    server returns 403 Forbidden with generic message and NO token.
    """
    password = "AdminPassword123"
    admin_email = create_temp_user("admin", password)

    # 1. Admin on Student tab
    res_student_tab = client.post("/api/auth/login", json={
        "email": admin_email,
        "password": password,
        "expected_role": "student"
    })
    assert res_student_tab.status_code == 403
    assert res_student_tab.json()["detail"] == "These credentials are not valid for this portal"
    assert "token" not in res_student_tab.json()

    # 2. Admin on Faculty tab
    res_faculty_tab = client.post("/api/auth/login", json={
        "email": admin_email,
        "password": password,
        "expected_role": "faculty"
    })
    assert res_faculty_tab.status_code == 403
    assert res_faculty_tab.json()["detail"] == "These credentials are not valid for this portal"
    assert "token" not in res_faculty_tab.json()

# ==============================================================================
# TEST 6: Admin tab/link not rendered on the public login page
# ==============================================================================
def test_admin_tab_not_rendered_on_public_login_page():
    """
    Verify that AuthLandingPage.tsx only supports 'student' | 'faculty' tabs,
    and no public navigation links to /admin-login exist.
    """
    project_root = os.path.dirname(backend_dir)
    auth_landing_path = os.path.join(project_root, "frontend", "src", "pages", "AuthLandingPage.tsx")

    assert os.path.exists(auth_landing_path), f"File not found: {auth_landing_path}"
    with open(auth_landing_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Ensure AuthRoleTab type does not contain 'admin'
    assert "export type AuthRoleTab = 'student' | 'faculty';" in content
    assert "'admin'" not in content[:content.find("export const AuthLandingPage")]

    # Ensure the tab switcher does not render an Admin button
    assert "['student', 'faculty'] as const" in content
    assert "tab === 'admin'" not in content

    # Ensure public pages do not link to /admin-login
    landing_page_path = os.path.join(project_root, "frontend", "src", "pages", "LandingPage.tsx")
    if os.path.exists(landing_page_path):
        with open(landing_page_path, "r", encoding="utf-8") as f:
            landing_content = f.read()
        assert "/admin-login" not in landing_content

# ==============================================================================
# TEST 7: 6th failed attempt returns 429 with Retry-After; success resets counter
# ==============================================================================
def test_brute_force_rate_limiting_and_reset():
    """
    Verify brute-force protection:
    - 5 failed attempts per email+IP return 401
    - 6th attempt returns 429 with Retry-After header
    - Successful login resets the failed attempts counter
    """
    reset_login_rate_limits()
    target_email = f"bruteforce_target_{uuid.uuid4().hex[:6]}@test.edu"

    # Attempt 1 through 5: each fails with 401
    for attempt in range(1, 6):
        res = client.post("/api/auth/login", json={
            "email": target_email,
            "password": f"WrongPass{attempt}"
        })
        assert res.status_code == 401, f"Attempt {attempt} should return 401, got {res.status_code}"

    # Attempt 6: triggers rate limit 429
    res_6 = client.post("/api/auth/login", json={
        "email": target_email,
        "password": "WrongPassAttempt6"
    })
    assert res_6.status_code == 429, f"6th attempt should return 429, got {res_6.status_code}"
    assert "Retry-After" in res_6.headers or "retry-after" in res_6.headers
    retry_after = res_6.headers.get("Retry-After") or res_6.headers.get("retry-after")
    assert int(retry_after) > 0
    assert "Too many failed login attempts" in res_6.json()["detail"]

    # Now verify reset on successful login:
    reset_login_rate_limits()
    valid_password = "CorrectPassword123"
    user_email = create_temp_user("student", valid_password)

    # 3 failed attempts
    for attempt in range(3):
        res_fail = client.post("/api/auth/login", json={
            "email": user_email,
            "password": "WrongPasswordX"
        })
        assert res_fail.status_code == 401

    # 1 successful login (must reset the counter)
    res_success = client.post("/api/auth/login", json={
        "email": user_email,
        "password": valid_password
    })
    assert res_success.status_code == 200
    assert "token" in res_success.json()

    # 3 more failed attempts (should not hit 429 because previous 3 were reset)
    for attempt in range(3):
        res_fail_again = client.post("/api/auth/login", json={
            "email": user_email,
            "password": "WrongPasswordY"
        })
        assert res_fail_again.status_code == 401

# ==============================================================================
# TEST 8: Unknown email and wrong password give identical responses
# ==============================================================================
def test_unknown_email_and_wrong_password_identical_responses():
    """
    Verify timing attack mitigation:
    Both unknown email and incorrect password for existing user must return
    identical status (401) and identical detail ('Invalid email or password').
    """
    reset_login_rate_limits()
    password = "KnownUserPassword123"
    known_email = create_temp_user("student", password)
    unknown_email = f"unknown_{uuid.uuid4().hex[:8]}@nonexistentinstitution.edu"

    # 1. Unknown email
    res_unknown = client.post("/api/auth/login", json={
        "email": unknown_email,
        "password": "SomeRandomPassword123"
    })

    # 2. Known user with wrong password
    res_wrong_pw = client.post("/api/auth/login", json={
        "email": known_email,
        "password": "IncorrectPassword123"
    })

    # Assert identical HTTP status code
    assert res_unknown.status_code == 401
    assert res_wrong_pw.status_code == 401

    # Assert identical JSON response payload
    assert res_unknown.json() == res_wrong_pw.json()
    assert res_unknown.json() == {"detail": "Invalid email or password"}
