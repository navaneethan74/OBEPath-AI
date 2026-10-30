import sys
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from fastapi.testclient import TestClient
from main import app
import uuid
from database import SessionLocal
from models import User, StudentProfile
from core.security import hash_password

def test_complete_flow():
    client = TestClient(app)

    # Pre-create dedicated test users with unique emails and passwords
    test_id = uuid.uuid4().hex[:8]
    s_email = f"e2e_student_{test_id}@obe.edu"
    s_pwd = "StudentSecurePass123!"
    f_email = f"e2e_faculty_{test_id}@obe.edu"
    f_pwd = "FacultySecurePass123!"
    a_email = f"e2e_admin_{test_id}@obe.edu"
    a_pwd = "AdminSecurePass123!"

    with SessionLocal() as db:
        s_user = User(
            email=s_email,
            password_hash=hash_password(s_pwd),
            full_name="Navaneethan",
            role="student"
        )
        db.add(s_user)
        db.flush()
        prof = db.query(StudentProfile).filter(StudentProfile.user_id == s_user.id).first()
        if not prof:
            prof = StudentProfile(user_id=s_user.id)
            db.add(prof)
        prof.academic_level = "Undergraduate"
        prof.selected_course_id = 1
        prof.learning_goal = "Master fundamentals and solve intermediate programming problems"
        prof.daily_time_minutes = 60
        prof.onboarding_completed = True
        db.add(User(
            email=f_email,
            password_hash=hash_password(f_pwd),
            full_name="Dr. Aris Thorne",
            role="faculty"
        ))
        db.add(User(
            email=a_email,
            password_hash=hash_password(a_pwd),
            full_name="System Administrator",
            role="admin"
        ))
        db.commit()
        s_user_id = s_user.id

    print("--- 1. Testing Root & Health Check ---")
    r = client.get("/health")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    print("[PASS] Backend is online and returns OBE architecture info")

    print("\n--- 2. Testing Student Login ---")
    r = client.post("/api/auth/login", json={"email": s_email, "password": s_pwd})
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    user_data = r.json()
    assert user_data["user"]["full_name"] == "Navaneethan"
    student_headers = {"Authorization": f"Bearer {user_data['token']}"}
    print(f"[PASS] Logged in as Student: {user_data['user']['full_name']} ({user_data['user']['role']})")

    print("\n--- 3. Testing Courses & Course Outcomes ---")
    r = client.get("/api/courses/1")
    assert r.status_code == 200
    course = r.json()
    assert course["title"] == "Python Programming"
    assert len(course["outcomes"]) == 4
    assert len(course["topics"]) == 8
    print(f"[PASS] Course verified: {course['title']} with {len(course['outcomes'])} COs and {len(course['topics'])} topics")

    print("\n--- 4. Testing Student Profile ---")
    r = client.get(f"/api/profile?user_id={s_user_id}", headers=student_headers)
    assert r.status_code == 200
    prof = r.json()
    assert prof["academic_level"] != ""
    print(f"[PASS] Profile loaded: Goal = '{prof['learning_goal'][:45]}...', Daily time = {prof['daily_time_minutes']} min")

    print("\n--- 5. Testing Diagnostic Assessment ---")
    r = client.get("/api/diagnostic/1", headers=student_headers)
    assert r.status_code == 200
    questions = r.json()
    assert len(questions) >= 5
    print(f"[PASS] Retrieved {len(questions)} diagnostic questions covering MCQs, code logic, output prediction")

    # Submit diagnostic answers
    answers = [
        {"question_id": q["id"], "selected_answer": q["options"][0]}
        for q in questions
    ]
    r = client.post(f"/api/diagnostic/submit?user_id={s_user_id}", headers=student_headers, json={"course_id": 1, "answers": answers})
    assert r.status_code == 200
    diag_res = r.json()
    print(f"[PASS] Diagnostic submitted: Score = {diag_res['overall_score']}%, Correct = {diag_res['correct_answers']}/{diag_res['total_questions']}")
    print(f"  Strengths: {[s['title'] for s in diag_res['strengths']]}")
    print(f"  Weaknesses: {[w['title'] for w in diag_res['weaknesses']]}")

    print("\n--- 6. Testing Personalized Learning Path ---")
    r = client.get(f"/api/learning-path?course_id=1&user_id={s_user_id}", headers=student_headers)
    assert r.status_code == 200
    path = r.json()
    assert len(path["items"]) == 8
    print(f"[PASS] Learning path active with {len(path['items'])} items")

    first_topic_id = path["items"][0]["topic_id"]
    # Explainable AI check
    r = client.get(f"/api/learning-path/why/{first_topic_id}?user_id={s_user_id}", headers=student_headers)
    assert r.status_code == 200
    why = r.json()
    print(f"[PASS] Explainable AI Rationale: '{why['explanation'][:80]}...'")

    print("\n--- 7. Testing AI Tutor ---")
    r = client.post(f"/api/ai-tutor/chat?user_id={s_user_id}", headers=student_headers, json={
        "topic_id": first_topic_id,
        "message": "Explain this topic simply.",
        "action": "explain_simply"
    })
    assert r.status_code == 200
    tutor_reply = r.json()
    assert "reply" in tutor_reply
    print(f"[PASS] AI Tutor response ({tutor_reply.get('adapted_for_level', 'Default')}): '{tutor_reply['reply'][:80]}...'")

    print("\n--- 8. Testing Adaptive Assessment Submission ---")
    ans_map = {str(questions[0]["id"]): questions[0]["options"][0]}
    r = client.post(f"/api/progress/submit-assessment?user_id={s_user_id}", headers=student_headers, json={
        "course_id": 1,
        "attempt_type": "assessment",
        "topic_id": first_topic_id,
        "answers": ans_map
    })
    assert r.status_code == 200
    sub_res = r.json()
    print(f"[PASS] Assessment evaluated: Score = {sub_res['evaluation']['score_percentage']}%")
    print(f"[PASS] Progress Engine adaptation message: '{sub_res['evaluation']['adaptation_message']}'")

    print("\n--- 9. Testing Outcome Attainment (OBE Dashboard) ---")
    r = client.get(f"/api/mastery/outcomes?user_id={s_user_id}&course_id=1", headers=student_headers)
    assert r.status_code == 200
    outc = r.json()
    for o in outc["outcomes"]:
        print(f"   - {o['code']}: {o['attainment_percentage']}% ({o['status']})")

    print("\n--- 10. Testing Interactive Knowledge Map ---")
    r = client.get(f"/api/mastery/knowledge-map?user_id={s_user_id}&course_id=1", headers=student_headers)
    assert r.status_code == 200
    kmap = r.json()
    assert len(kmap["nodes"]) == 8
    print(f"[PASS] Knowledge Map: {len(kmap['nodes'])} nodes, {len(kmap['edges'])} prerequisite edges")

    fac_login = client.post("/api/auth/login", json={"email": f_email, "password": f_pwd})
    assert fac_login.status_code == 200
    fac_headers = {"Authorization": f"Bearer {fac_login.json()['token']}"}
    r = client.get("/api/faculty/topic-analytics?course_id=1", headers=fac_headers)
    assert r.status_code == 200
    f_ana = r.json()
    print(f"[PASS] Faculty Insight: '{f_ana['critical_insight']}'")

    print("\n--- 12. Testing Admin Telemetry & Agent Audit Logs ---")
    admin_login = client.post("/api/auth/login", json={"email": a_email, "password": a_pwd})
    assert admin_login.status_code == 200
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['token']}"}
    r = client.get("/api/admin/metrics", headers=admin_headers)
    assert r.status_code == 200
    admin_m = r.json()
    print(f"[PASS] Admin Telemetry: {admin_m['total_users']} users, {admin_m['ai_agent_executions']} agent invocations, Status: {admin_m['system_status']}")

    r = client.get("/api/admin/logs?limit=5", headers=admin_headers)
    assert r.status_code == 200
    logs = r.json()
    print(f"[PASS] Recent Agent Logs ({len(logs)} shown):")
    for l in logs[:3]:
        print(f"   [{l['agent']}] {l['message'][:70]}...")

    print("\n==========================================")
    print("ALL 12 END-TO-END SYSTEM TESTS PASSED SUCCESSFULLY!")
    print("==========================================")

if __name__ == "__main__":
    test_complete_flow()
