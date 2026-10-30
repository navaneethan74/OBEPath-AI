"""
Tests for:
1. /api/assessment/compile-code in ENV=production:
   - When Docker is unavailable, server NEVER executes code on host (ignores SANDBOX_ALLOW_UNSAFE_LOCAL).
   - Returns 501 Not Implemented with detail "Server-side execution is disabled; use in-browser runner".
   - In ENV=development without Docker and without unsafe local, returns 503.
   - In ENV=development with SANDBOX_ALLOW_UNSAFE_LOCAL=true, local execution works.
2. Untrusted client code challenge results:
   - Client-claimed code "pass" (e.g. passed_count=10, percentage=100.0) is marked "self-verified".
   - Does NOT count toward mastery, topic completion, or Course Outcome attainment.
   - MCQ server-graded questions remain the sole official evidence.
   - /topic/complete/{topic_id} strictly rejects completion without passed server-graded assessment.
"""
import os
import uuid
import pytest
from fastapi.testclient import TestClient

from main import app
from database import SessionLocal
from models import User, StudentProfile, MasteryScore, CourseOutcome, OutcomeAttainment, AssessmentAttempt
from core.security import hash_password, create_access_token

client = TestClient(app)

def create_temp_student() -> tuple[int, dict]:
    uid = uuid.uuid4().hex[:8]
    email = f"pyodide_test_{uid}@obe.edu"
    with SessionLocal() as db:
        user = User(
            email=email,
            password_hash=hash_password("SecurePass123!"),
            full_name="Pyodide Test Student",
            role="student"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        prof = StudentProfile(user_id=user.id, selected_course_id=2, onboarding_completed=True)
        db.add(prof)

        # Initialize topic masteries
        for tid in range(1, 9):
            db.add(MasteryScore(
                user_id=user.id,
                topic_id=tid,
                overall_mastery=0.0,
                classification="Needs Improvement"
            ))

        # Initialize COs
        for co in db.query(CourseOutcome).filter(CourseOutcome.course_id == 2).all():
            db.add(OutcomeAttainment(
                user_id=user.id,
                course_id=2,
                outcome_id=co.id,
                attainment_percentage=0.0,
                status="Needs Improvement"
            ))
        db.commit()
        user_id = user.id

    token = create_access_token(user_id, "student")
    return user_id, {"Authorization": f"Bearer {token}"}

# ==============================================================================
# 1. Server-side code execution disabled in production without Docker
# ==============================================================================

def test_production_without_docker_returns_501(monkeypatch):
    """
    When ENV=production and Docker is unavailable,
    /api/assessment/compile-code must NEVER execute code on the server and return 501.
    """
    monkeypatch.setattr("code_runner.check_docker_available", lambda: False)
    monkeypatch.setenv("ENV", "production")
    monkeypatch.delenv("SANDBOX_ALLOW_UNSAFE_LOCAL", raising=False)

    _, headers = create_temp_student()
    res = client.post("/api/assessment/compile-code", headers=headers, json={
        "code": "print('hello')",
        "test_cases": [{"call": "solve()", "expected": "1"}]
    })

    assert res.status_code == 501
    assert "Server-side execution is disabled; use in-browser runner" in res.json()["detail"]

def test_production_ignores_sandbox_allow_unsafe_local(monkeypatch):
    """
    In ENV=production, SANDBOX_ALLOW_UNSAFE_LOCAL=true MUST be strictly ignored.
    Still returns 501 and never executes code on the server host.
    """
    monkeypatch.setattr("code_runner.check_docker_available", lambda: False)
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("SANDBOX_ALLOW_UNSAFE_LOCAL", "true")

    canary_file = os.path.join(os.path.dirname(__file__), f"canary_{uuid.uuid4().hex[:6]}.tmp")
    if os.path.exists(canary_file):
        os.remove(canary_file)

    _, headers = create_temp_student()
    res = client.post("/api/assessment/compile-code", headers=headers, json={
        "code": f"open(r'{canary_file}', 'w').write('LEAK')",
        "test_cases": [{"call": "solve()", "expected": "1"}]
    })

    assert res.status_code == 501
    assert "Server-side execution is disabled; use in-browser runner" in res.json()["detail"]
    assert not os.path.exists(canary_file), "CRITICAL: Malicious code ran on host in production!"

def test_development_without_docker_and_without_unsafe_local_returns_503(monkeypatch):
    """
    In ENV=development with Docker unavailable and SANDBOX_ALLOW_UNSAFE_LOCAL=false,
    returns 503 Service Unavailable.
    """
    monkeypatch.setattr("code_runner.check_docker_available", lambda: False)
    monkeypatch.setenv("ENV", "development")
    monkeypatch.delenv("SANDBOX_ALLOW_UNSAFE_LOCAL", raising=False)

    _, headers = create_temp_student()
    res = client.post("/api/assessment/compile-code", headers=headers, json={
        "code": "def solve(): return 1\n",
        "test_cases": [{"call": "solve()", "expected": "1"}]
    })

    assert res.status_code == 503
    assert "Code execution temporarily unavailable" in res.json()["detail"]

# ==============================================================================
# 2. Untrusted client code results never affect official mastery or attainment
# ==============================================================================

def test_client_claimed_code_pass_does_not_count_toward_mastery():
    """
    When a student submits wrong MCQ answers (0% correct) but claims 100% passed coding challenge,
    their official score percentage MUST be 0.0% and mastery MUST NOT increase.
    The coding submission must be flagged self_verified=True.
    """
    user_id, headers = create_temp_student()

    fake_client_coding_claim = {
        "challenge_id": "ds_stack_parentheses",
        "title": "Stack Parentheses",
        "topic_id": 1,
        "code": "def is_valid_parentheses(s): return True # fake client claim",
        "passed_count": 10,
        "total_count": 10,
        "percentage": 100.0,
        "all_passed": True,
        "results": [{"test_idx": 1, "passed": True}],
        "execution_time_ms": 12
    }

    # Deliberately submit wrong MCQ answers
    wrong_answers = {
        "1": "Wrong Option A",
        "2": "Wrong Option B",
        "3": "Wrong Option C"
    }

    res = client.post(f"/api/progress/submit-assessment?user_id={user_id}", headers=headers, json={
        "course_id": 2,
        "attempt_type": "assessment",
        "topic_id": 1,
        "answers": wrong_answers,
        "coding_submission": fake_client_coding_claim
    })

    assert res.status_code == 200
    data = res.json()["evaluation"]

    # 1. Official score must be strictly 0.0% (not inflated by fake coding submission)
    assert data["score_percentage"] == 0.0
    assert data["passed"] is False

    # 2. Coding submission must be marked as self_verified
    coding_res = data.get("coding_result") or {}
    assert coding_res.get("self_verified") is True
    assert coding_res.get("status") == "self-verified"

    # 3. Topic 1 mastery must remain 0.0 in the database
    with SessionLocal() as db:
        m1 = db.query(MasteryScore).filter(MasteryScore.user_id == user_id, MasteryScore.topic_id == 1).first()
        assert m1 is not None
        assert m1.overall_mastery == 0.0, "Mastery must not be inflated by client-claimed code pass!"

def test_topic_complete_endpoint_rejects_without_passed_mcq():
    """
    /api/assessment/topic/complete/{topic_id} must reject with 400
    if the student has not passed the official server-graded assessment,
    even if they completed an in-browser coding challenge.
    """
    user_id, headers = create_temp_student()

    res = client.post(f"/api/assessment/topic/complete/1?user_id={user_id}", headers=headers)
    assert res.status_code == 400
    assert "Complete the practice assessment first" in res.json()["detail"]
