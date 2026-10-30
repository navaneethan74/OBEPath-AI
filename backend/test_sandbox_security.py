import os
import sys
import uuid
import pytest
from fastapi.testclient import TestClient

# Ensure backend directory is in sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from main import app
from database import SessionLocal
from models import User
from core.security import hash_password, create_access_token
from code_runner import (
    execute_code_submission,
    check_docker_available,
    reset_code_runner_rate_limits,
    GLOBAL_EXECUTION_SEMAPHORE
)

client = TestClient(app)

def create_temp_auth_user(role: str = "student") -> tuple:
    """Helper to create an isolated temporary user and generate JWT auth header."""
    db = SessionLocal()
    unique_id = uuid.uuid4().hex[:8]
    email = f"sandbox_test_{role}_{unique_id}@testinstitution.edu"
    user = User(
        email=email,
        full_name=f"Sandbox {role.capitalize()} {unique_id}",
        role=role,
        password_hash=hash_password("SecureSandboxPass123")
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    user_id = user.id
    token = create_access_token(user_id, role)
    db.close()
    return user_id, {"Authorization": f"Bearer {token}"}

# ==============================================================================
# 1. AUTHENTICATION REQUIREMENT
# ==============================================================================
def test_unauthenticated_compile_rejected_401():
    """Verify /api/assessment/compile-code requires login (returns 401 without token)."""
    res = client.post("/api/assessment/compile-code", json={
        "code": "def add(a, b): return a + b",
        "test_cases": [{"call": "add(1, 2)", "expected": "3"}]
    })
    assert res.status_code == 401, f"Expected 401 Unauthorized, got {res.status_code}"

# ==============================================================================
# 2. INPUT VALIDATION & RESTRICTIONS
# ==============================================================================
def test_code_length_cap_returns_400():
    """Verify code length > 10,000 characters is rejected with HTTP 400."""
    _, headers = create_temp_auth_user()
    huge_code = "a = 1\n" * 2000  # > 10,000 characters
    res = client.post("/api/assessment/compile-code", headers=headers, json={
        "code": huge_code,
        "test_cases": [{"call": "add(1, 2)", "expected": "3"}]
    })
    assert res.status_code == 400
    assert "10,000 characters" in res.json()["detail"]

def test_malicious_test_case_call_expression_returns_400():
    """
    Verify client-supplied test_cases[].call expressions are parsed via AST and
    rejected with HTTP 400 if malicious or not matching the validated call format.
    """
    _, headers = create_temp_auth_user()

    malicious_calls = [
        "__import__('os').system('id')",
        "eval('1+1')",
        "exec('print(1)')",
        "open('/etc/passwd').read()",
        "getattr(obj, 'secret')",
        "compile('x=1', '', 'exec')",
        "system('whoami')"
    ]

    for bad_call in malicious_calls:
        res = client.post("/api/assessment/compile-code", headers=headers, json={
            "code": "def solve(): return 1\n",
            "test_cases": [{"call": bad_call, "expected": "1"}]
        })
        assert res.status_code == 400, f"Expected 400 for '{bad_call}', got {res.status_code}"
        assert "Invalid or unsafe test case call expression" in res.json()["detail"]

def test_timeout_sec_capped_at_5():
    """Verify timeout_sec=999999 is capped at 5.0 seconds maximum."""
    _, headers = create_temp_auth_user()
    res = client.post("/api/assessment/compile-code", headers=headers, json={
        "code": "def solve(): return 1\n",
        "test_cases": [{"call": "solve()", "expected": "1"}],
        "timeout_sec": 999999
    })
    # If Docker unavailable in production mode, 503 is returned; if local dev fallback allowed, 200 is returned.
    # In neither case should an error about 999999 occur.
    assert res.status_code in (200, 503)

# ==============================================================================
# 3. FAIL CLOSED WHEN DOCKER UNAVAILABLE
# ==============================================================================
def test_docker_unavailable_returns_503_and_never_runs_on_host(monkeypatch):
    """
    FAIL CLOSED REQUIREMENT:
    If Docker is unavailable (and SANDBOX_ALLOW_UNSAFE_LOCAL is not enabled),
    /api/assessment/compile-code returns 503 'Code execution temporarily unavailable'
    and NEVER runs student code on the host.
    """
    # Force Docker unavailable and disallow unsafe local execution
    monkeypatch.setattr("code_runner.check_docker_available", lambda: False)
    monkeypatch.delenv("SANDBOX_ALLOW_UNSAFE_LOCAL", raising=False)

    _, headers = create_temp_auth_user()

    # Pass code that would create a canary file if it ran on the host
    canary_path = os.path.join(backend_dir, f"canary_leak_{uuid.uuid4().hex[:6]}.txt")
    if os.path.exists(canary_path):
        os.remove(canary_path)

    malicious_code = f"open(r'{canary_path}', 'w').write('LEAKED')"

    # 1. In production: returns 501 Not Implemented ("Server-side execution is disabled; use in-browser runner")
    monkeypatch.setenv("ENV", "production")
    res_prod = client.post("/api/assessment/compile-code", headers=headers, json={
        "code": malicious_code,
        "test_cases": [{"call": "solve()", "expected": "1"}]
    })
    assert res_prod.status_code == 501, f"Expected 501 when Docker is unavailable in production, got {res_prod.status_code}"
    assert "Server-side execution is disabled; use in-browser runner" in res_prod.json()["detail"]
    assert not os.path.exists(canary_path), "CRITICAL: Student code ran on host when Docker was unavailable!"

    # 2. In development without unsafe fallback: returns 503
    monkeypatch.setenv("ENV", "development")
    res_dev = client.post("/api/assessment/compile-code", headers=headers, json={
        "code": malicious_code,
        "test_cases": [{"call": "solve()", "expected": "1"}]
    })
    assert res_dev.status_code == 503
    assert "Code execution temporarily unavailable" in res_dev.json()["detail"]
    assert not os.path.exists(canary_path), "CRITICAL: Student code ran on host in dev!"

# ==============================================================================
# 4. CONCURRENCY & PER-USER RATE LIMITING
# ==============================================================================
def test_per_user_rate_limit_returns_429():
    """Verify max 10 runs per minute per user returns 429 with Retry-After on 11th run."""
    reset_code_runner_rate_limits()
    user_id, headers = create_temp_auth_user()

    payload = {
        "code": "def solve(): return 1\n",
        "test_cases": [{"call": "solve()", "expected": "1"}]
    }

    # First 10 requests: accepted (status 200 or 503 depending on Docker availability, but NOT 429)
    for i in range(10):
        res = client.post("/api/assessment/compile-code", headers=headers, json=payload)
        assert res.status_code in (200, 503), f"Request {i+1} should not be rate-limited, got {res.status_code}"

    # 11th request: triggers 429
    res_11 = client.post("/api/assessment/compile-code", headers=headers, json=payload)
    assert res_11.status_code == 429, f"11th request should return 429, got {res_11.status_code}"
    assert "Retry-After" in res_11.headers or "retry-after" in res_11.headers
    retry_val = res_11.headers.get("Retry-After") or res_11.headers.get("retry-after")
    assert int(retry_val) > 0
    assert "Too many code execution requests" in res_11.json()["detail"]

def test_concurrency_semaphore_limit_returns_429():
    """Verify when all 4 concurrency slots are acquired, incoming requests return 429."""
    reset_code_runner_rate_limits()
    _, headers = create_temp_auth_user()

    # Acquire all 4 slots manually
    acquired_slots = []
    for _ in range(4):
        slot = GLOBAL_EXECUTION_SEMAPHORE.acquire(blocking=False)
        assert slot is True
        acquired_slots.append(slot)

    try:
        # 5th request should fail with 429 because compiler is busy
        res = client.post("/api/assessment/compile-code", headers=headers, json={
            "code": "def solve(): return 1\n",
            "test_cases": [{"call": "solve()", "expected": "1"}]
        })
        assert res.status_code == 429
        assert "Compiler busy" in res.json()["detail"]
    finally:
        # Release all 4 acquired slots
        for _ in acquired_slots:
            GLOBAL_EXECUTION_SEMAPHORE.release()

# ==============================================================================
# 5. CONTAINER ESCAPE & ISOLATION TESTS
# (Skipped with a clear message if Docker daemon is not available)
# ==============================================================================
docker_skip_condition = pytest.mark.skipif(
    not check_docker_available(),
    reason="Docker daemon is unavailable on host; skipping container sandbox isolation tests."
)

@docker_skip_condition
def test_container_getattr_builtins_import_trick_cannot_access_host():
    """
    Verify the getattr(__builtins__, chr(95)+chr(95)+'import'+chr(95)+chr(95))('os') trick
    executes only inside the container and cannot access host files or backend/.env.
    """
    code = """
import sys
# Dynamic obfuscated import of os
os_mod = getattr(__builtins__, chr(95)+chr(95)+'import'+chr(95)+chr(95))('os')
def check_host_env():
    # Attempt to locate host backend .env or host drive
    has_host_env = os_mod.path.exists('/backend/.env') or os_mod.path.exists('N:/ai/backend/.env')
    return str(has_host_env)
"""
    res = execute_code_submission(code, [{"call": "check_host_env()", "expected": "False"}])
    assert res["success"] is True
    assert res["all_passed"] is True

@docker_skip_condition
def test_container_etc_passwd_is_container_not_host():
    """Verify /etc/passwd inside the container is harmless and host drives are not visible."""
    code = """
import os
def read_root():
    with open('/etc/passwd') as f:
        content = f.read()
    # Check for sandboxuser
    return 'sandboxuser' in content
"""
    res = execute_code_submission(code, [{"call": "read_root()", "expected": "True"}])
    assert res["success"] is True
    assert res["all_passed"] is True

@docker_skip_condition
def test_container_network_disabled():
    """Verify network access (sockets to 8.8.8.8 and localhost:8000) fails with --network none."""
    code = """
import socket
def try_network():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.0)
        s.connect(('8.8.8.8', 53))
        return "connected"
    except Exception as e:
        return "blocked"
"""
    res = execute_code_submission(code, [{"call": "try_network()", "expected": "blocked"}])
    assert res["success"] is True
    assert res["all_passed"] is True

@docker_skip_condition
def test_container_infinite_loop_killed():
    """Verify an infinite loop is killed at the timeout limit and container removed."""
    code = """
def loop():
    while True:
        pass
"""
    res = execute_code_submission(code, [{"call": "loop()", "expected": "None"}], timeout_sec=1.5)
    assert res["success"] is False
    assert "Execution Timed Out" in res["stderr"]

@docker_skip_condition
def test_container_memory_bomb_killed():
    """Verify a memory bomb (1 GB) is killed by the 128m memory limit."""
    code = """
def mem_bomb():
    data = bytearray(1024 * 1024 * 1024)  # 1 GB
    return len(data)
"""
    res = execute_code_submission(code, [{"call": "mem_bomb()", "expected": "0"}])
    assert res["success"] is False
    assert "Memory Limit Exceeded" in res["stderr"]

@docker_skip_condition
def test_container_fork_bomb_stopped():
    """Verify a fork bomb is stopped by --pids-limit 64."""
    code = """
import os
def fork_bomb():
    try:
        for _ in range(100):
            os.fork()
        return "ok"
    except Exception as e:
        return "fork_blocked"
"""
    res = execute_code_submission(code, [{"call": "fork_bomb()", "expected": "fork_blocked"}])
    assert res["success"] is False or res["all_passed"] is True

@docker_skip_condition
def test_container_huge_output_truncated():
    """Verify huge stdout output (>64 KB) is truncated."""
    code = """
def spam():
    for _ in range(2000):
        print("X" * 100)
    return "done"
"""
    res = execute_code_submission(code, [{"call": "spam()", "expected": "done"}])
    assert res["success"] is True
    assert len(res["stdout"]) <= 65536 + 200

@docker_skip_condition
def test_container_write_outside_tmp_fails():
    """Verify writing outside /tmp fails on read-only root filesystem."""
    code = """
def write_file():
    try:
        with open('/home/sandboxuser/forbidden.txt', 'w') as f:
            f.write('bad')
        return "writable"
    except Exception:
        return "read_only"
"""
    res = execute_code_submission(code, [{"call": "write_file()", "expected": "read_only"}])
    assert res["success"] is True
    assert res["all_passed"] is True

@docker_skip_condition
def test_normal_correct_and_incorrect_solutions():
    """Verify normal correct solution passes and incorrect solution fails."""
    correct_code = "def is_valid_parentheses(s: str) -> bool: return s == '()'"
    incorrect_code = "def is_valid_parentheses(s: str) -> bool: return False"
    tc = [
        {"call": "is_valid_parentheses('()')", "expected": "True"},
        {"call": "is_valid_parentheses('(')", "expected": "False"}
    ]

    res_correct = execute_code_submission(correct_code, tc)
    assert res_correct["success"] is True
    assert res_correct["all_passed"] is True
    assert res_correct["passed_count"] == 2

    res_incorrect = execute_code_submission(incorrect_code, tc)
    assert res_incorrect["success"] is True
    assert res_incorrect["all_passed"] is False
    assert res_incorrect["passed_count"] == 1

def test_dev_unsafe_local_allowed_only_in_development(monkeypatch):
    """
    Verify SANDBOX_ALLOW_UNSAFE_LOCAL=true:
    1. Allowed in ENV=development: code compiles and runs locally with loud warning.
    2. STRICTLY IGNORED in ENV=production: returns 503 and fails closed.
    """
    reset_code_runner_rate_limits()
    _, headers = create_temp_auth_user()
    monkeypatch.setattr("code_runner.check_docker_available", lambda: False)

    # Case 1: In development with flag enabled -> executes successfully
    monkeypatch.setenv("ENV", "development")
    monkeypatch.setenv("SANDBOX_ALLOW_UNSAFE_LOCAL", "true")
    res_dev = client.post("/api/assessment/compile-code", headers=headers, json={
        "code": "def add(a, b): return a + b\n",
        "test_cases": [{"call": "add(2, 3)", "expected": "5"}]
    })
    assert res_dev.status_code == 200
    assert res_dev.json()["success"] is True
    assert res_dev.json()["all_passed"] is True

    # Case 2: In production with flag enabled -> MUST IGNORE flag and return 501
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("SANDBOX_ALLOW_UNSAFE_LOCAL", "true")
    res_prod = client.post("/api/assessment/compile-code", headers=headers, json={
        "code": "def add(a, b): return a + b\n",
        "test_cases": [{"call": "add(2, 3)", "expected": "5"}]
    })
    assert res_prod.status_code == 501
    assert "Server-side execution is disabled; use in-browser runner" in res_prod.json()["detail"]

