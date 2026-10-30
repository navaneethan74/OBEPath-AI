import sys
import os
import json

# Ensure sys.path includes the current directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
from models import AssessmentAttempt, MasteryScore, LearningPath, CourseOutcome, Topic

def run_verification():
    client = TestClient(app)
    user_id = 1
    course_id = 2

    print("======================================================================")
    print("STEP 1: Fetch CS201 Diagnostic Assessment Questions")
    print("======================================================================")
    r = client.get(f"/api/diagnostic/{course_id}")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    questions = r.json()
    print(f"Retrieved {len(questions)} diagnostic questions:")
    for q in questions:
        print(f"  - Q{q['id']} ({q.get('topic_title', 'Unknown')}): {q['question_text'][:50]}...")
    assert len(questions) >= 5, "Expected at least 5 questions for CS201"

    print("\n======================================================================")
    print("STEP 2 & 3: Answer all 5 questions with a LOW score and Submit")
    print("======================================================================")
    # Deliberately choose wrong answers for low score
    low_answers = []
    for q in questions:
        # choose an answer that is definitely wrong
        opts = q.get("options", [])
        wrong_opt = "Deliberately wrong answer"
        for opt in opts:
            if "LIFO" not in opt and opt != "30" and opt != "Dequeue" and opt != "2" and "Base condition" not in opt:
                wrong_opt = opt
                break
        low_answers.append({
            "question_id": q["id"],
            "selected_answer": wrong_opt
        })

    submit_payload = {
        "course_id": course_id,
        "answers": low_answers
    }
    r = client.post(f"/api/diagnostic/submit?user_id={user_id}", json=submit_payload)
    assert r.status_code == 200, f"Submission failed: {r.text}"
    diag_result = r.json()
    print(f"Diagnostic Submitted Successfully!")
    print(f"  - Overall Score: {diag_result['overall_score']}%")
    print(f"  - Correct Answers: {diag_result['correct_answers']}/{diag_result['total_questions']}")
    print(f"  - Needs Learning (Weak topics): {[w['title'] for w in diag_result['weaknesses']]}")
    assert diag_result['overall_score'] <= 40.0, "Expected low score for diagnostic test"

    print("\n======================================================================")
    print("STEP 4: Verify Assessment Attempt Saved in Database")
    print("======================================================================")
    db = SessionLocal()
    attempts = db.query(AssessmentAttempt).filter(
        AssessmentAttempt.user_id == user_id,
        AssessmentAttempt.course_id == course_id
    ).order_by(AssessmentAttempt.created_at.desc()).all()
    assert len(attempts) >= 1, "AssessmentAttempt must be saved in database"
    attempt_1 = attempts[0]
    print(f"Saved Attempt 1: UUID={attempt_1.attempt_uuid}, Type={attempt_1.attempt_type}, Score={attempt_1.score}/{attempt_1.max_score} ({attempt_1.percentage}%)")
    assert attempt_1.attempt_uuid is not None and len(attempt_1.attempt_uuid) > 0

    print("\n======================================================================")
    print("STEP 5 & 6: Verify Topic-Level Mastery & Dashboard Progress > 0%")
    print("======================================================================")
    r = client.get(f"/api/progress/state?user_id={user_id}&course_id={course_id}")
    assert r.status_code == 200, f"Failed to get student state: {r.text}"
    state = r.json()
    print(f"Central Student State:")
    print(f"  - Overall Progress: {state['overallProgress']}% (Must not be 0%)")
    print(f"  - Overall Mastery: {state['overallMastery']}%")
    print(f"  - Topics Mastered: {state['topicsMastered']}")
    print(f"  - Overall OBE Attainment: {state['overallOBEAttainment']}%")
    print(f"  - Current Target: {state['currentTargetTopic']['title'] if state['currentTargetTopic'] else 'None'}")
    assert state['overallProgress'] > 0, "Dashboard progress must change from 0%!"
    assert len(state['topicMastery']) == 8, f"Expected 8 topics, got {len(state['topicMastery'])}"

    print("\nTopic Mastery Breakdown:")
    for tm in state['topicMastery']:
        print(f"  - [{tm['code']}] {tm['title']}: {tm['mastery']}% ({tm['classification']}) | Status: {tm['status']} | Locked: {tm['is_locked']}")

    print("\n======================================================================")
    print("STEP 7: Verify My Learning Path is Generated & Sequenced")
    print("======================================================================")
    lp = state['learningPath']
    assert len(lp['items']) > 0, "Learning Path must have items"
    print(f"Learning Path Status: {lp['status']}, Reason: {lp['adaptation_reason']}")
    print(f"Path Items ({len(lp['items'])} items):")
    for item in lp['items']:
        print(f"  Seq {item['sequence_order']}: {item['topic_title']} | Status: {item['status']} | Action: {item.get('action')} | Remedial: {item['is_remedial']}")

    # Verify Recursion is marked before dependent Tree Traversal
    recursion_seq = None
    tree_seq = None
    for item in lp['items']:
        if "recursion" in item['topic_title'].lower():
            recursion_seq = item['sequence_order']
        if "tree traversal" in item['topic_title'].lower():
            tree_seq = item['sequence_order']
            assert item['status'] == 'LOCKED', "Tree Traversal must be LOCKED because Recursion mastery is low!"

    print(f"Prerequisite ordering check: Recursion seq={recursion_seq}, Tree Traversal seq={tree_seq} (LOCKED)")
    assert recursion_seq is not None and tree_seq is not None
    assert recursion_seq < tree_seq, "Prerequisite (Recursion) must precede dependent (Tree Traversal)"

    print("\n======================================================================")
    print("STEP 8: Verify Knowledge Map Node States")
    print("======================================================================")
    r = client.get(f"/api/knowledge-map?user_id={user_id}&course_id={course_id}")
    assert r.status_code == 200, f"Failed to get knowledge map: {r.text}"
    kmap = r.json()
    print(f"Knowledge Map has {len(kmap['nodes'])} nodes and {len(kmap['edges'])} edges")
    tree_node = next((n for n in kmap['nodes'] if "tree traversal" in (n.get('label') or n.get('title') or '').lower()), None)
    if tree_node:
        print(f"  Tree Traversal Node Color: {tree_node.get('color')} (Status: {tree_node.get('status')})")
        assert tree_node.get('status') == 'LOCKED', "Tree Traversal node must be marked LOCKED in Knowledge Map"

    print("\n======================================================================")
    print("STEP 9: Verify AI Tutor Receives Weak / Current Target Topic")
    print("======================================================================")
    current_target = state['currentTargetTopic']
    assert current_target is not None, "Current target topic must exist"
    print(f"AI Tutor Current Target: {current_target['title']} (Mastery: {current_target['mastery']}%)")
    r = client.post(f"/api/ai-tutor/chat?user_id={user_id}", json={
        "topic_id": current_target['topic_id'],
        "message": "Can you explain this concept to me step by step?",
        "action": "explain_simply"
    })
    assert r.status_code == 200
    tutor_data = r.json()
    print(f"AI Tutor Response for {current_target['title']}: {tutor_data['reply'][:90]}...")
    assert "reply" in tutor_data

    print("\n======================================================================")
    print("STEP 10 & 11: Verify Course Outcome Attainment Changes (CO1 - CO4)")
    print("======================================================================")
    co_list = state['courseOutcomeAttainment']
    assert len(co_list) >= 4, f"Expected 4 Course Outcomes, got {len(co_list)}"
    for co in co_list:
        print(f"  - [{co['code']}] {co['description'][:40]}...: {co['attainment_percentage']}% | Status: {co['status']}")
        assert co['attainment_percentage'] >= 0, "Attainment percentage must be calculated"

    print("\n======================================================================")
    print("STEP 12, 13, 14, 15: Take Assessment Again -> Verify NEW Attempt & Adaptation")
    print("======================================================================")
    # Fetch adaptive questions for reassessment
    r = client.get(f"/api/progress/questions?user_id={user_id}&course_id={course_id}&count=5&attempt_type=reassessment")
    assert r.status_code == 200
    adaptive_qs = r.json()
    print(f"Retrieved {len(adaptive_qs)} adaptive questions:")
    for aq in adaptive_qs:
        print(f"  - [{aq['difficulty']}] Q{aq['id']} ({aq.get('topic_title', '')}): {aq['question_text'][:50]}...")

    # Answer adaptive questions with high score
    good_answers = {}
    for aq in adaptive_qs:
        opts = aq.get("options", [])
        good_answers[str(aq["id"])] = opts[0] if opts else "answer"

    r = client.post(f"/api/progress/submit-assessment?user_id={user_id}", json={
        "course_id": course_id,
        "attempt_type": "reassessment",
        "answers": good_answers
    })
    assert r.status_code == 200
    res2 = r.json()
    attempt_2_info = res2["evaluation"]
    print(f"Submitted Second Assessment: Score={attempt_2_info['score']}/{attempt_2_info['max_score']} ({attempt_2_info['percentage']}%)")
    print(f"New Attempt UUID: {attempt_2_info['attempt_uuid']}")

    # Verify NEW attempt created in database (not overwriting attempt 1)
    db.expire_all()
    all_attempts = db.query(AssessmentAttempt).filter(
        AssessmentAttempt.user_id == user_id,
        AssessmentAttempt.course_id == course_id
    ).all()
    print(f"Total Attempts in DB: {len(all_attempts)}")
    assert len(all_attempts) >= 2, "A new attempt must be created instead of overwriting!"
    uuids = [a.attempt_uuid for a in all_attempts]
    assert len(set(uuids)) == len(uuids), "Attempt UUIDs must be unique!"
    print(f"All Unique Attempt UUIDs: {uuids}")

    print("\n======================================================================")
    print("STEP 16: Closed-Loop Adaptation - Improve Prerequisite (Recursion) -> Unlock Dependent (Tree Traversal)")
    print("======================================================================")
    # Find recursion topic
    rec_topic = db.query(Topic).filter(Topic.course_id == course_id, Topic.title.ilike("%recursion%")).first()
    assert rec_topic is not None, "Recursion topic not found"

    # First ensure Tree Basics prerequisite is satisfied (as diagnostic also lowered Tree Basics)
    tree_basics = db.query(Topic).filter(Topic.course_id == course_id, Topic.title.ilike("%tree basics%")).first()
    if tree_basics:
        client.post(f"/api/progress/simulate-activity?user_id={user_id}", json={
            "topic_id": tree_basics.id,
            "score": 90.0,
            "activity_type": "assessment",
            "reason": "Student completed Tree Basics review"
        })

    # Simulate remedial assessment with 85% score for Recursion
    # Formula: 30% previous (25-30%) + 70% remedial (85%) = 67% or assessment 40% prev + 60% score
    print(f"Simulating assessment score = 85.0% for Topic {rec_topic.id} ({rec_topic.title})...")
    r = client.post(f"/api/progress/simulate-activity?user_id={user_id}", json={
        "topic_id": rec_topic.id,
        "score": 85.0,
        "activity_type": "assessment",
        "reason": "Student completed intensive remediation and passed post-test"
    })
    assert r.status_code == 200
    sim_res = r.json()
    new_mastery = sim_res['new_mastery']
    print(f"Updated Recursion Mastery: {sim_res['previous_mastery']}% -> {new_mastery}% ({sim_res['classification']})")
    assert new_mastery >= 60.0, f"Expected Recursion mastery >= 60.0%, got {new_mastery}%"

    # Verify that Tree Traversal is now UNLOCKED!
    tree_topic = db.query(Topic).filter(Topic.course_id == course_id, Topic.title.ilike("%tree traversal%")).first()
    state_after = sim_res['state']
    tree_status_after = next((tm for tm in state_after['topicMastery'] if tm['topic_id'] == tree_topic.id), None)
    print(f"Tree Traversal Status After Prerequisite Improvement:")
    print(f"  - Status: {tree_status_after['status']}")
    print(f"  - Is Locked: {tree_status_after['is_locked']}")
    print(f"  - Unsatisfied Prereqs: {tree_status_after['unsatisfied_prerequisites']}")
    assert tree_status_after['is_locked'] == False, "Tree Traversal MUST be unlocked after Recursion reaches >= 60% mastery!"

    # Verify learning path reordered
    lp_after = state_after['learningPath']
    tree_path_item = next((i for i in lp_after['items'] if i['topic_id'] == tree_topic.id), None)
    assert tree_path_item is not None
    print(f"Tree Traversal in Learning Path: Status={tree_path_item['status']}, Action={tree_path_item.get('action')}")
    assert tree_path_item['status'] != 'LOCKED', "Tree Traversal in Learning Path must no longer be LOCKED!"

    print("\n======================================================================")
    print("ALL 16 VERIFICATION CRITERIA PASSED WITH ZERO ERRORS!")
    print("======================================================================")

if __name__ == "__main__":
    run_verification()
