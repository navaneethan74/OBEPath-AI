import sys
import os
import json
import uuid

# Ensure sys.path includes the current directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
from models import User, StudentProfile
from core.security import hash_password

def test_auth_and_onboarding():
    client = TestClient(app)

    # Pre-create a dedicated returning student for Step 1
    test_id = uuid.uuid4().hex[:8]
    returning_email = f"returning.student.{test_id}@obe.edu"
    returning_password = "ReturningPass123!"

    db = SessionLocal()
    try:
        ret_user = User(
            email=returning_email,
            password_hash=hash_password(returning_password),
            full_name="Returning Student",
            role="student"
        )
        db.add(ret_user)
        db.flush()
        prof = db.query(StudentProfile).filter(StudentProfile.user_id == ret_user.id).first()
        if not prof:
            prof = StudentProfile(user_id=ret_user.id)
            db.add(prof)
        prof.onboarding_completed = True
        db.commit()
    finally:
        db.close()

    print("======================================================================")
    print("STEP 1: Test Returning User Login")
    print("======================================================================")
    r = client.post("/api/auth/login", json={
        "email": returning_email,
        "password": returning_password
    })
    assert r.status_code == 200, f"Returning login failed: {r.text}"
    ret_data = r.json()
    print(f"Returning user: {ret_data['user']['full_name']} (ID: {ret_data['user']['id']})")
    print(f"Is new user: {ret_data['is_new_user']}, Onboarding completed: {ret_data['onboarding_completed']}")
    assert ret_data["onboarding_completed"] == True, "Expected returning user to have onboarding_completed == True"
    assert ret_data["is_new_user"] == False, "Expected returning user to have is_new_user == False"

    print("\n======================================================================")
    print("STEP 2: Test Invalid Password & Invalid Email Error Messages")
    print("======================================================================")
    r = client.post("/api/auth/login", json={
        "email": returning_email,
        "password": "wrongpassword123"
    })
    assert r.status_code == 401, f"Expected 401 for wrong password, got {r.status_code}"
    print(f"Wrong password message: {r.json()['detail']}")

    r = client.post("/api/auth/login", json={
        "email": f"nonexistent_{test_id}@obe.edu",
        "password": "somepassword"
    })
    assert r.status_code == 401, f"Expected 401 for nonexistent email, got {r.status_code}"
    assert r.json()["detail"] == "Invalid email or password"
    print(f"Nonexistent email message: {r.json()['detail']}")

    print("\n======================================================================")
    print("STEP 3: Test New User Account Registration")
    print("======================================================================")
    new_email = f"test.learner.{test_id}@obe.edu"
    r = client.post("/api/auth/register", json={
        "email": new_email,
        "password": "securepassword123",
        "full_name": "Deepa Sundar",
        "role": "student"
    })
    assert r.status_code == 200, f"Registration failed: {r.text}"
    reg_data = r.json()
    new_token = reg_data["token"]
    new_auth_headers = {"Authorization": f"Bearer {new_token}"}
    print(f"New registered user: {reg_data['user']['full_name']} (ID: {reg_data['user']['id']})")
    print(f"Is new user: {reg_data['is_new_user']}, Onboarding completed: {reg_data['onboarding_completed']}")
    assert reg_data["is_new_user"] == True
    assert reg_data["onboarding_completed"] == False

    print("\n======================================================================")
    print("STEP 4: Test Duplicate Email Prevention on Registration")
    print("======================================================================")
    r_dup = client.post("/api/auth/register", json={
        "email": new_email,
        "password": "anotherpassword1",
        "full_name": "Duplicate Tester",
        "role": "student"
    })
    assert r_dup.status_code == 400, f"Expected 400 for duplicate email, got {r_dup.status_code}"
    print(f"Duplicate email prevented with message: {r_dup.json()['detail']}")

    print("\n======================================================================")
    print("STEP 5: Test First-Time Google Login with Token Verification")
    print("======================================================================")
    from unittest.mock import patch
    google_email = f"google.learner.{test_id}@gmail.com"
    
    with patch.dict(os.environ, {"GOOGLE_CLIENT_ID": "mock-google-client-id"}), \
         patch("google.oauth2.id_token.verify_oauth2_token", return_value={
             "sub": f"google-sub-{test_id}",
             "email": google_email,
             "name": "Google New Student"
         }):
        r_g1 = client.post("/api/auth/google", json={"credential": "mock-google-id-token"})
        assert r_g1.status_code == 200, f"Google auth failed: {r_g1.text}"
        g1_data = r_g1.json()
        print(f"First-time Google user: {g1_data['user']['full_name']} (ID: {g1_data['user']['id']})")
        print(f"Is new user: {g1_data['is_new_user']}, Onboarding completed: {g1_data['onboarding_completed']}")
        assert g1_data["is_new_user"] == True
        assert g1_data["onboarding_completed"] == False

        print("\n======================================================================")
        print("STEP 6: Test Returning Google Login (No Duplicate Profile)")
        print("======================================================================")
        r_g2 = client.post("/api/auth/google", json={"credential": "mock-google-id-token"})
        assert r_g2.status_code == 200
        g2_data = r_g2.json()
        assert g2_data["user"]["id"] == g1_data["user"]["id"], "Google user ID must match, no duplicates!"
        print(f"Returning Google user ID verified: {g2_data['user']['id']}")

    print("\n======================================================================")
    print("STEP 7: Test Student Onboarding Wizard Completion")
    print("======================================================================")
    new_user_id = reg_data["user"]["id"]
    r_onboard = client.put(f"/api/profile?user_id={new_user_id}", headers=new_auth_headers, json={
        "full_name": "Deepa Sundar",
        "department": "Artificial Intelligence & Data Science",
        "semester": 4,
        "academic_level": "Undergraduate (Semester 4)",
        "selected_course_id": 2,
        "current_level": "Intermediate",
        "learning_goal": "Problem solving: Master algorithmic complexity and tree traversal",
        "prior_knowledge": "I know the basics",
        "onboarding_completed": True
    })
    assert r_onboard.status_code == 200, f"Onboarding profile save failed: {r_onboard.text}"
    prof_data = r_onboard.json()
    print(f"Saved student profile:")
    print(f"  - Full Name: {prof_data['full_name']}")
    print(f"  - Department: {prof_data['department']}")
    print(f"  - Course ID: {prof_data['selected_course_id']}")
    print(f"  - Onboarding completed: {prof_data['onboarding_completed']}")
    assert prof_data["onboarding_completed"] == True

    print("\n======================================================================")
    print("STEP 8: Test AI Skill Check Adaptive Questions Retrieval")
    print("======================================================================")
    r_q = client.get(f"/api/progress/questions?user_id={new_user_id}&course_id=2&count=5&attempt_type=assessment", headers=new_auth_headers)
    assert r_q.status_code == 200, f"Failed to get skill check questions: {r_q.text}"
    qs = r_q.json()
    print(f"Retrieved {len(qs)} AI Skill Check questions:")
    for q in qs:
        print(f"  - Q{q['id']} ({q.get('topic_title', '')}) [{q.get('difficulty')}]: {q['question_text'][:45]}...")
    assert len(qs) >= 5, "Expected at least 5 questions for skill check"

    print("\n======================================================================")
    print("STEP 9: Submit AI Skill Check & Verify Learning Path Synthesized")
    print("======================================================================")
    answers = {}
    for q in qs:
        opts = q.get("options", [])
        answers[str(q["id"])] = opts[0] if opts else "test"

    r_sub = client.post(f"/api/progress/submit-assessment?user_id={new_user_id}", headers=new_auth_headers, json={
        "course_id": 2,
        "attempt_type": "assessment",
        "answers": answers
    })
    assert r_sub.status_code == 200, f"Skill check submit failed: {r_sub.text}"
    sub_res = r_sub.json()
    print(f"Skill check evaluated: score = {sub_res['evaluation']['score']}/{sub_res['evaluation']['max_score']} ({sub_res['evaluation']['percentage']}%)")
    lp_items = sub_res["state"]["learningPath"]["items"]
    print(f"Personalized Learning Path generated with {len(lp_items)} sequential modules:")
    for item in lp_items[:4]:
        print(f"  Seq {item['sequence_order']}: {item['topic_title']} ({item['status']})")
    assert len(lp_items) > 0

    print("\n======================================================================")
    print("ALL AUTHENTICATION, GOOGLE, ONBOARDING & SKILL CHECK TESTS PASSED!")
    print("======================================================================")

if __name__ == "__main__":
    test_auth_and_onboarding()
