"""
Comprehensive Test Suite for Student Onboarding & Flow After Login
Tests all 6 required user flow cases:
CASE 1: New user register/login -> Onboarding required -> Select course -> AI Skill Check
CASE 2: Returning user login -> Already onboarded -> Straight to Dashboard
CASE 3: User refresh simulation -> Profile & draft persistence preserved
CASE 4: User completes onboarding -> onboarding_completed is True
CASE 5: Same user logs in again -> Never prompted for onboarding again -> Straight to Dashboard
CASE 6: Selected course is correctly passed and associated with AI Skill Check
"""
import sys
import os
import json
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
from models import User, StudentProfile, Course, QuestionBank, DiagnosticQuestion

client = TestClient(app)

def run_tests():
    print("=" * 70)
    print("RUNNING COMPLETE ONBOARDING & FLOW TESTS (ALL 6 CASES)")
    print("=" * 70)

    # ------------------------------------------------------------------
    # CASE 2: Returning User Login -> Straight to Dashboard
    # ------------------------------------------------------------------
    from core.security import hash_password
    ret_uuid = uuid.uuid4().hex[:6]
    ret_email = f"ret_student_{ret_uuid}@obe.edu"
    ret_pwd = "RetPassword123!"
    db = SessionLocal()
    try:
        ret_u = User(
            email=ret_email,
            password_hash=hash_password(ret_pwd),
            full_name="Returning Student",
            role="student"
        )
        db.add(ret_u)
        db.flush()
        db.add(StudentProfile(
            user_id=ret_u.id,
            onboarding_completed=True
        ))
        db.commit()
    finally:
        db.close()

    print("\n--- CASE 2: Returning User Login ---")
    r_ret = client.post("/api/auth/login", json={
        "email": ret_email,
        "password": ret_pwd,
        "role": "student"
    })
    assert r_ret.status_code == 200, f"Login failed: {r_ret.text}"
    ret_data = r_ret.json()
    print(f"Returning user: {ret_data['user']['full_name']} (ID: {ret_data['user']['id']})")
    print(f"  - is_new_user: {ret_data.get('is_new_user')}")
    print(f"  - onboarding_completed: {ret_data.get('onboarding_completed')}")
    assert ret_data["onboarding_completed"] == True, "Expected returning user to have onboarding_completed=True"
    assert ret_data["is_new_user"] == False, "Expected returning user to have is_new_user=False"
    print("[PASS] CASE 2 PASSED: Returning user routes straight to Dashboard.")

    # ------------------------------------------------------------------
    # CASE 1: New User Registration & First-Time Onboarding
    # ------------------------------------------------------------------
    print("\n--- CASE 1: New User Flow ---")
    test_uuid = uuid.uuid4().hex[:6]
    new_email = f"learner_{test_uuid}@obe.edu"
    new_name = f"Test Student {test_uuid}"

    r_reg = client.post("/api/auth/register", json={
        "email": new_email,
        "password": "securepassword123",
        "full_name": new_name,
        "role": "student"
    })
    assert r_reg.status_code == 200, f"Registration failed: {r_reg.text}"
    reg_data = r_reg.json()
    new_user_id = reg_data["user"]["id"]
    print(f"New user created: {new_name} (ID: {new_user_id})")
    print(f"  - is_new_user: {reg_data.get('is_new_user')}")
    print(f"  - onboarding_completed: {reg_data.get('onboarding_completed')}")
    assert reg_data["onboarding_completed"] == False, "New user must start with onboarding_completed=False"
    assert reg_data["is_new_user"] == True, "New user must have is_new_user=True"
    print("[PASS] New user correctly routed to Student Onboarding.")

    # ------------------------------------------------------------------
    # CASE 3: Step 1 & 2 Draft & Persistence Check (Simulating Refresh)
    # ------------------------------------------------------------------
    print("\n--- CASE 3: Profile Persistence & Intermediate Updates ---")
    # Step 1 update (Name, Department, Year)
    r_step1 = client.put(f"/api/profile?user_id={new_user_id}", json={
        "full_name": f"{new_name} Updated",
        "department": "CSE",
        "semester": 4,
        "academic_level": "2nd Year Undergraduate"
    })
    assert r_step1.status_code == 200, f"Profile step 1 update failed: {r_step1.text}"
    prof1 = r_step1.json()
    assert prof1["department"] == "CSE"
    assert prof1["full_name"] == f"{new_name} Updated"
    print(f"Profile saved at Step 1: {prof1['full_name']} | Dept: {prof1['department']}")

    # Refresh verification: fetch profile
    r_fetch1 = client.get(f"/api/profile?user_id={new_user_id}")
    assert r_fetch1.status_code == 200
    assert r_fetch1.json()["department"] == "CSE"
    print("[PASS] CASE 3 PASSED: Profile data preserved across refresh / intermediate steps.")

    # ------------------------------------------------------------------
    # CASE 4: Step 3 Completion -> onboarding_completed = True
    # ------------------------------------------------------------------
    print("\n--- CASE 4: Onboarding Completion with Course Selection ---")
    # Selecting course 2 (Data Structures, CS201)
    r_step3 = client.put(f"/api/profile?user_id={new_user_id}", json={
        "full_name": f"{new_name} Updated",
        "department": "CSE",
        "semester": 4,
        "academic_level": "2nd Year Undergraduate",
        "selected_course_id": 2,
        "current_level": "Intermediate",
        "prior_knowledge": "I know the basics",
        "learning_goal": "Master Data Structures through Outcome-Based Education",
        "onboarding_completed": True
    })
    assert r_step3.status_code == 200, f"Profile completion failed: {r_step3.text}"
    completed_prof = r_step3.json()
    print(f"Saved student profile after Step 3:")
    print(f"  - Full Name: {completed_prof['full_name']}")
    print(f"  - Department: {completed_prof['department']}")
    print(f"  - Course ID: {completed_prof['selected_course_id']}")
    print(f"  - Level: {completed_prof['current_level']}")
    print(f"  - Onboarding completed: {completed_prof['onboarding_completed']}")
    assert completed_prof["onboarding_completed"] == True
    print("[PASS] CASE 4 PASSED: onboarding_completed is now True.")

    # ------------------------------------------------------------------
    # CASE 5: Same User Logs in Again -> Straight to Dashboard
    # ------------------------------------------------------------------
    print("\n--- CASE 5: Same User Logs in Again ---")
    r_relogin = client.post("/api/auth/login", json={
        "email": new_email,
        "password": "securepassword123",
        "role": "student"
    })
    assert r_relogin.status_code == 200, f"Re-login failed: {r_relogin.text}"
    relogin_data = r_relogin.json()
    print(f"Relogin result for {new_email}:")
    print(f"  - is_new_user: {relogin_data.get('is_new_user')}")
    print(f"  - onboarding_completed: {relogin_data.get('onboarding_completed')}")
    assert relogin_data["onboarding_completed"] == True, "Completed student must return onboarding_completed=True"
    assert relogin_data["is_new_user"] == False, "Completed student must return is_new_user=False"
    print("[PASS] CASE 5 PASSED: Completed user never sees onboarding again -> goes straight to Dashboard.")

    # ------------------------------------------------------------------
    # CASE 6: Selected Course Passed to AI Skill Check & Submitted
    # ------------------------------------------------------------------
    print("\n--- CASE 6: Course Passed to Existing AI Skill Check ---")
    selected_cid = completed_prof["selected_course_id"]
    r_qs = client.get(f"/api/progress/questions?user_id={new_user_id}&course_id={selected_cid}&count=5&attempt_type=assessment")
    assert r_qs.status_code == 200, f"Failed to get questions: {r_qs.text}"
    qs = r_qs.json()
    print(f"Retrieved {len(qs)} adaptive questions for Course ID {selected_cid}:")
    for q in qs:
        print(f"  - Q{q['id']} ({q.get('topic_title', '')}): {q['question_text'][:50]}...")
    assert len(qs) >= 5, "Expected at least 5 questions for selected course"

    # Submit assessment with course_id
    answers = {str(q["id"]): q.get("options", ["A"])[0] for q in qs}
    r_sub = client.post(f"/api/progress/submit-assessment?user_id={new_user_id}", json={
        "course_id": selected_cid,
        "attempt_type": "assessment",
        "answers": answers
    })
    assert r_sub.status_code == 200, f"Submit failed: {r_sub.text}"
    sub_res = r_sub.json()
    eval_info = sub_res["evaluation"]
    print(f"Assessment evaluated for Course {selected_cid}: Score {eval_info['score']}/{eval_info['max_score']} ({eval_info['percentage']}%)")
    items = sub_res["state"]["learningPath"]["items"]
    print(f"Personalized Learning Path generated with {len(items)} topics:")
    for item in items[:3]:
        print(f"  - Seq {item['sequence_order']}: {item['topic_title']} ({item['status']})")
    assert len(items) > 0
    print("[PASS] CASE 6 PASSED: Selected course correctly passed into assessment & personalized learning path synthesized.")

    print("\n" + "=" * 70)
    print("ALL 6 FLOW CASES VERIFIED AND PASSED WITH 100% SUCCESS!")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
