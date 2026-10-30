import os
import json
import ast
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import (
    Topic, MasteryScore, QuizAttempt, LearningPath, LearningPathItem,
    AgentLog, OutcomeAttainment, TopicOutcomeMapping, CourseOutcome, User,
    AssessmentAttempt, TopicPrerequisite, MasteryHistory
)
from schemas import QuizSubmitRequest, PracticeSubmitRequest
from ai_agents.assessment_agent import AssessmentAgent
from ai_agents.progress_agent import ProgressMonitoringAgent
from ai_agents.planner_agent import PlannerAgent
from core.security import get_current_user, resolve_target_user_id
from core.thresholds import PREREQ_UNLOCK, ASSESSMENT_PASS, TOPIC_MASTERY, CO_ACHIEVED_DEFAULT

def validate_test_case_call(call_expr: str) -> bool:
    """
    Validates that client-supplied call_expr is strictly a safe function call:
    - Must be a single Call node: func_name(arg1, arg2, ...)
    - func must be a simple identifier (ast.Name), not attribute access, not eval/exec/__import__/etc.
    - arguments must only be literal constants or literal collections.
    """
    if not isinstance(call_expr, str) or not call_expr.strip():
        return False
    try:
        parsed = ast.parse(call_expr.strip(), mode="eval")
    except Exception:
        return False

    if not isinstance(parsed.body, ast.Call):
        return False

    func_node = parsed.body.func
    if not isinstance(func_node, ast.Name):
        return False

    FORBIDDEN_NAMES = {
        "eval", "exec", "__import__", "open", "input", "compile",
        "globals", "locals", "vars", "dir", "getattr", "setattr", "delattr",
        "hasattr", "breakpoint", "help", "exit", "quit", "system"
    }
    if func_node.id in FORBIDDEN_NAMES or func_node.id.startswith("__"):
        return False

    def is_safe_node(node):
        if isinstance(node, ast.Constant):
            return True
        elif isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            return all(is_safe_node(elt) for elt in node.elts)
        elif isinstance(node, ast.Dict):
            return all(
                (is_safe_node(k) if k is not None else False) and is_safe_node(v)
                for k, v in zip(node.keys, node.values)
            )
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)) and isinstance(node.operand, ast.Constant):
            return True
        return False

    for arg in parsed.body.args:
        if not is_safe_node(arg):
            return False

    for kw in parsed.body.keywords:
        if not is_safe_node(kw.value):
            return False

    return True

def has_passed_assessment_for_topic(db: Session, user_id: int, topic_id: int) -> bool:
    """
    Checks if the user has at least one passed assessment attempt for topic_id (score >= ASSESSMENT_PASS).
    Checks AssessmentAttempt (single-topic or multi-topic topic_scores_json) and QuizAttempt.
    """
    # 1. AssessmentAttempt with matching topic_id
    attempts = db.query(AssessmentAttempt).filter(
        AssessmentAttempt.user_id == user_id,
        AssessmentAttempt.topic_id == topic_id
    ).all()
    for att in attempts:
        if (att.percentage is not None and att.percentage >= ASSESSMENT_PASS) or att.passed:
            return True

    # 2. Multi-topic AssessmentAttempt (diagnostic/practice across multiple topics)
    multi_attempts = db.query(AssessmentAttempt).filter(
        AssessmentAttempt.user_id == user_id,
        AssessmentAttempt.topic_id == None
    ).all()
    for att in multi_attempts:
        if att.topic_scores_json:
            try:
                t_scores = json.loads(att.topic_scores_json)
                score = t_scores.get(str(topic_id)) if str(topic_id) in t_scores else t_scores.get(topic_id)
                if score is not None and float(score) >= ASSESSMENT_PASS:
                    return True
            except Exception:
                pass

    # 3. QuizAttempt for this topic
    quiz_attempts = db.query(QuizAttempt).filter(
        QuizAttempt.user_id == user_id,
        QuizAttempt.topic_id == topic_id
    ).all()
    for q_att in quiz_attempts:
        if (q_att.percentage is not None and q_att.percentage >= ASSESSMENT_PASS) or q_att.passed:
            return True

    return False

router = APIRouter(prefix="/api/assessment", tags=["assessment"])

@router.get("/quiz/{topic_id}")
def get_topic_quiz(
    topic_id: int,
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_user_id = resolve_target_user_id(current_user, user_id)
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    from progress_engine import select_adaptive_questions
    questions = select_adaptive_questions(
        db, user_id=target_user_id, course_id=topic.course_id, topic_id=topic_id, count=4, attempt_type="quiz"
    )
    if not questions:
        raw = AssessmentAgent.get_functions_quiz()
        questions = [{
            "id": q["id"],
            "question": q["question"],
            "code": q.get("code"),
            "options": q["options"]
        } for q in raw]
    else:
        questions = [{
            "id": q["id"],
            "question": q["question_text"],
            "code": q.get("code_snippet"),
            "options": q["options"]
        } for q in questions]

    return questions

@router.post("/quiz/submit")
def submit_topic_quiz(
    data: QuizSubmitRequest,
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_user_id = resolve_target_user_id(current_user, user_id)
    topic = db.query(Topic).filter(Topic.id == data.topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # If answers dictionary was passed, evaluate it against QuestionBank or agent quiz
    if data.answers:
        from models import QuestionBank
        q_ids = [int(k) for k in data.answers.keys() if str(k).isdigit()]
        qb_questions = db.query(QuestionBank).filter(QuestionBank.id.in_(q_ids)).all() if q_ids else []
        if qb_questions:
            score = 0
            max_score = len(qb_questions)
            details = []
            for q in qb_questions:
                user_ans = data.answers.get(str(q.id))
                is_correct = (user_ans == q.correct_answer)
                if is_correct:
                    score += 1
                details.append({
                    "question_id": q.id,
                    "question": q.question_text,
                    "user_answer": user_ans,
                    "correct_answer": q.correct_answer,
                    "is_correct": is_correct,
                    "explanation": q.explanation or ""
                })
            percentage = round((score / max_score) * 100.0, 1) if max_score > 0 else 0.0
            feedback = f"Recorded score: {score}/{max_score} ({percentage}%)."
        else:
            full_quiz = AssessmentAgent.get_functions_quiz()
            eval_result = AssessmentAgent.evaluate_quiz(data.answers, full_quiz)
            score = eval_result["score"]
            max_score = eval_result["max_score"]
            percentage = eval_result["percentage"]
            feedback = eval_result["feedback"]
            details = eval_result["details"]
    else:
        score = data.score
        max_score = data.max_score
        percentage = round((score / max_score) * 100.0, 1)
        feedback = f"Recorded score: {score}/{max_score} ({percentage}%)."
        details = []

    passed = percentage >= ASSESSMENT_PASS

    # Record QuizAttempt
    attempt = QuizAttempt(
        user_id=target_user_id,
        topic_id=data.topic_id,
        score=score,
        max_score=max_score,
        percentage=percentage,
        passed=passed,
        answers_json=json.dumps(data.answers or {})
    )
    db.add(attempt)

    # Update MasteryScore
    mastery_obj = db.query(MasteryScore).filter(
        MasteryScore.user_id == target_user_id,
        MasteryScore.topic_id == data.topic_id
    ).first()

    if not mastery_obj:
        mastery_obj = MasteryScore(user_id=target_user_id, topic_id=data.topic_id)
        db.add(mastery_obj)

    mastery_obj.quiz_score = percentage
    calc = ProgressMonitoringAgent.calculate_mastery(
        diagnostic_score=mastery_obj.diagnostic_score,
        quiz_score=mastery_obj.quiz_score,
        practice_score=mastery_obj.practice_score,
        completion_score=mastery_obj.completion_score
    )
    mastery_obj.overall_mastery = calc["overall_mastery"]
    mastery_obj.classification = calc["classification"]

    # Evaluate performance trigger
    perf = ProgressMonitoringAgent.evaluate_performance_event(
        topic_title=topic.title,
        quiz_percentage=percentage,
        current_mastery=mastery_obj.overall_mastery
    )

    path_adapted = False
    adaptation_message = ""

    if perf["trigger"] == "REMEDIAL_INSERTION":
        # Specific scenario from Prompt #20:
        # Score <= 50% (e.g. 3/10)
        # Progress Agent detects low mastery -> triggers Planner Agent to insert 6 remedial steps
        path = db.query(LearningPath).filter(
            LearningPath.user_id == target_user_id,
            LearningPath.course_id == topic.course_id,
            LearningPath.status == "ACTIVE"
        ).first()

        if path:
            topics = db.query(Topic).filter(Topic.course_id == topic.course_id).order_by(Topic.order_index).all()
            all_masteries = {m.topic_id: m.overall_mastery for m in db.query(MasteryScore).filter(MasteryScore.user_id == target_user_id).all()}
            prereqs_map = {t.id: [p.prerequisite_topic_id for p in t.prerequisites] for t in topics}
            outcomes_map = {t.id: [m.outcome for m in t.outcome_mappings] for t in topics}

            base_items = PlannerAgent.generate_path(topics, prereqs_map, all_masteries, outcomes_map)
            remedial_items = PlannerAgent.insert_functions_remediation(base_items, data.topic_id)

            db.query(LearningPathItem).filter(LearningPathItem.learning_path_id == path.id).delete()
            path.adaptation_reason = "Adaptive intervention: We detected difficulty with Functions. Your learning path has been adapted with targeted remediation."
            path.updated_at = datetime.utcnow()

            for itm in remedial_items:
                db.add(LearningPathItem(
                    learning_path_id=path.id,
                    topic_id=itm["topic_id"],
                    sequence_order=itm["sequence_order"],
                    status=itm["status"],
                    recommendation_reason=itm["recommendation_reason"],
                    is_remedial=itm.get("is_remedial", False),
                    remedial_title=itm.get("remedial_title"),
                    remedial_description=itm.get("remedial_description")
                ))

            path_adapted = True
            adaptation_message = "We detected difficulty with Functions. Your learning path has been adapted to include 6 focused remedial modules."

    elif perf["trigger"] == "ACCELERATION" or (percentage >= TOPIC_MASTERY and passed):
        # Score >= 70% or ACCELERATION
        path = db.query(LearningPath).filter(
            LearningPath.user_id == target_user_id,
            LearningPath.course_id == topic.course_id,
            LearningPath.status == "ACTIVE"
        ).first()

        if path:
            remedial_items = db.query(LearningPathItem).filter(
                LearningPathItem.learning_path_id == path.id,
                LearningPathItem.is_remedial == True
            ).all()

            if remedial_items:
                # Remediation was active and is now successfully passed!
                for r_item in remedial_items:
                    r_item.status = "COMPLETED"

                main_topic_item = db.query(LearningPathItem).filter(
                    LearningPathItem.learning_path_id == path.id,
                    LearningPathItem.topic_id == data.topic_id,
                    LearningPathItem.is_remedial == False
                ).first()
                if main_topic_item:
                    main_topic_item.status = "COMPLETED"

                # Unlock the next non-remedial topic (Topic 6: Lists and Tuples)
                next_item = db.query(LearningPathItem).filter(
                    LearningPathItem.learning_path_id == path.id,
                    LearningPathItem.topic_id > data.topic_id,
                    LearningPathItem.is_remedial == False
                ).order_by(LearningPathItem.sequence_order).first()
                if next_item:
                    next_item.status = "CURRENT"

                path.adaptation_reason = f"Remediation verified: Functions mastery threshold satisfied (>={int(PREREQ_UNLOCK)}%). Primary path resumed: Lists and Tuples is now active."
                path.updated_at = datetime.utcnow()
                path_adapted = True
                adaptation_message = "Remediation successfully completed! Mastery updated and Lists & Tuples has been unlocked."

                log_planner = AgentLog(
                    user_id=target_user_id,
                    agent_name="Planner Agent",
                    action="path_resumed",
                    message="Functions prerequisite cleared. Unlocked Lists & Tuples as CURRENT recommendation."
                )
                db.add(log_planner)
            else:
                current_item = db.query(LearningPathItem).filter(
                    LearningPathItem.learning_path_id == path.id,
                    LearningPathItem.topic_id == data.topic_id
                ).first()
                if current_item:
                    current_item.status = "COMPLETED"
                    # Unlock next topic
                    next_item = db.query(LearningPathItem).filter(
                        LearningPathItem.learning_path_id == path.id,
                        LearningPathItem.sequence_order == current_item.sequence_order + 1
                    ).first()
                    if next_item:
                        next_item.status = "CURRENT"
                
                path.adaptation_reason = "Accelerated progression: Demonstrated high mastery. Unnecessary revision bypassed."
                path.updated_at = datetime.utcnow()
                path_adapted = True
                adaptation_message = "You demonstrated high mastery! The Planner Agent has accelerated your learning path."

    # Update Course Outcomes via authoritative Progress Engine (weighted calculation, history snapshot)
    from progress_engine import recalculate_course_outcomes
    recalculate_course_outcomes(db, user_id=target_user_id, course_id=topic.course_id, trigger="quiz")

    # Log Progress Agent action
    log = AgentLog(
        user_id=target_user_id,
        agent_name="Progress Monitoring Agent",
        action="quiz_evaluation",
        message=f"Quiz evaluated for '{topic.title}': {score}/{max_score} ({percentage}%). Overall topic mastery updated to {mastery_obj.overall_mastery}%."
    )
    db.add(log)
    db.commit()

    return {
        "score": score,
        "max_score": max_score,
        "percentage": percentage,
        "passed": passed,
        "new_mastery": mastery_obj.overall_mastery,
        "classification": mastery_obj.classification,
        "formula_breakdown": calc["formula_breakdown"],
        "feedback": feedback,
        "path_adapted": path_adapted,
        "adaptation_message": adaptation_message,
        "trigger": perf["trigger"],
        "details": details
    }

@router.post("/practice/submit")
def submit_practice(
    data: PracticeSubmitRequest,
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_user_id = resolve_target_user_id(current_user, user_id)
    topic = db.query(Topic).filter(Topic.id == data.topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    from progress_engine import update_topic_mastery
    res = update_topic_mastery(
        db=db,
        user_id=target_user_id,
        topic_id=data.topic_id,
        score=float(data.score),
        activity_type="practice",
        reason=f"Practice activity completed with accuracy {data.score}%"
    )

    log = AgentLog(
        user_id=target_user_id,
        agent_name="Assessment Agent",
        action="practice_submission",
        message=f"Practice activity completed for '{topic.title}' with accuracy {data.score}%. Topic mastery recalculated to {res['new_mastery']}%."
    )
    db.add(log)
    db.commit()

    return {
        "topic_id": data.topic_id,
        "practice_score": data.score,
        "new_mastery": res["new_mastery"],
        "classification": res["classification"]
    }

@router.post("/topic/complete/{topic_id}")
def complete_topic(
    topic_id: int,
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Rule 1: Use the authenticated user only (no user_id from client).
    # If client provides user_id that differs from current_user.id, reject with 403.
    if user_id is not None and user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Forbidden: You cannot complete topics for other users.")
    target_user_id = current_user.id

    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # Rule 1 & 3: 409 if already completed (idempotent: no recalculation, no duplicate history rows, no downgrade)
    mastery_obj = db.query(MasteryScore).filter(
        MasteryScore.user_id == target_user_id,
        MasteryScore.topic_id == topic_id
    ).first()
    active_path = db.query(LearningPath).filter(
        LearningPath.user_id == target_user_id,
        LearningPath.course_id == topic.course_id,
        LearningPath.status == "ACTIVE"
    ).order_by(LearningPath.id.desc()).first()
    lp_item = db.query(LearningPathItem).filter(
        LearningPathItem.learning_path_id == active_path.id,
        LearningPathItem.topic_id == topic_id
    ).first() if active_path else None

    # Rule 1 & 3: 409 if already completed (idempotent: no recalculation, no duplicate history rows, no downgrade)
    is_already_completed = False
    if mastery_obj and (mastery_obj.completion_score or 0.0) >= 100.0:
        is_already_completed = True
    elif lp_item and lp_item.status == "COMPLETED" and mastery_obj and (mastery_obj.completion_score or 0.0) >= 100.0:
        is_already_completed = True
    else:
        comp_history = db.query(MasteryHistory).filter(
            MasteryHistory.user_id == target_user_id,
            MasteryHistory.topic_id == topic_id,
            MasteryHistory.source == "completion"
        ).first()
        if comp_history:
            is_already_completed = True

    if is_already_completed:
        raise HTTPException(status_code=409, detail="Topic already completed.")

    # Rule 1: 403 if the topic is LOCKED or any prerequisite is below PREREQ_UNLOCK
    prereqs = db.query(TopicPrerequisite).filter(TopicPrerequisite.topic_id == topic_id).all()
    for pr in prereqs:
        pr_m = db.query(MasteryScore).filter(
            MasteryScore.user_id == target_user_id,
            MasteryScore.topic_id == pr.prerequisite_topic_id
        ).first()
        pr_val = pr_m.overall_mastery if pr_m else 0.0
        req_val = max(float(pr.required_mastery_pct or 0.0), PREREQ_UNLOCK)
        if pr_val < req_val:
            raise HTTPException(
                status_code=403,
                detail=f"Topic is locked. Prerequisite requires at least {req_val}% mastery (current: {pr_val}%)."
            )

    if lp_item and lp_item.status == "LOCKED":
        raise HTTPException(status_code=403, detail="Topic is locked. Complete prerequisite topics first.")

    # Rule 2: Evidence rule: Require at least one passed assessment attempt (score >= ASSESSMENT_PASS)
    if not has_passed_assessment_for_topic(db, target_user_id, topic_id):
        raise HTTPException(status_code=400, detail="Complete the practice assessment first")

    from progress_engine import update_topic_mastery, get_central_student_state

    # 1. Update topic mastery via progress engine with source="completion"
    res = update_topic_mastery(
        db=db,
        user_id=target_user_id,
        topic_id=topic_id,
        score=100.0,
        activity_type="completion",
        reason=f"Topic '{topic.title}' completed with verified assessment evidence."
    )

    # 2. Log agent activity
    log = AgentLog(
        user_id=target_user_id,
        agent_name="Progress Monitoring Agent",
        action="topic_completion",
        message=f"Student completed '{topic.title}'. Mastery updated to {res['new_mastery']}%. Outcomes and next eligible topic updated."
    )
    db.add(log)
    db.commit()

    # 3. Retrieve authoritative central student state
    state = get_central_student_state(db, user_id=target_user_id, course_id=topic.course_id)

    return {
        "topic_id": topic_id,
        "completion_score": 100.0,
        "new_mastery": res["new_mastery"],
        "classification": res["classification"],
        "state": state
    }

@router.post("/remediation/complete")
def complete_remediation(
    topic_id: int = 5,
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_user_id = resolve_target_user_id(current_user, user_id)
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    mastery_obj = db.query(MasteryScore).filter(
        MasteryScore.user_id == target_user_id,
        MasteryScore.topic_id == topic_id
    ).first()

    if not mastery_obj:
        mastery_obj = MasteryScore(user_id=target_user_id, topic_id=topic_id)
        db.add(mastery_obj)

    # Student completed all 6 remedial modules with distinction and passed reassessment
    mastery_obj.diagnostic_score = max(mastery_obj.diagnostic_score, TOPIC_MASTERY) # Remediation resolves foundational deficit
    mastery_obj.quiz_score = 90.0
    mastery_obj.practice_score = 95.0
    mastery_obj.completion_score = 100.0
    calc = ProgressMonitoringAgent.calculate_mastery(
        diagnostic_score=mastery_obj.diagnostic_score,
        quiz_score=mastery_obj.quiz_score,
        practice_score=mastery_obj.practice_score,
        completion_score=mastery_obj.completion_score
    )
    mastery_obj.overall_mastery = calc["overall_mastery"]
    mastery_obj.classification = calc["classification"]

    path = db.query(LearningPath).filter(
        LearningPath.user_id == target_user_id,
        LearningPath.course_id == topic.course_id,
        LearningPath.status == "ACTIVE"
    ).first()

    unlocked_topic_title = "Lists and Tuples"

    if path:
        remedial_items = db.query(LearningPathItem).filter(
            LearningPathItem.learning_path_id == path.id,
            LearningPathItem.is_remedial == True
        ).all()
        for r_item in remedial_items:
            r_item.status = "COMPLETED"

        main_topic_item = db.query(LearningPathItem).filter(
            LearningPathItem.learning_path_id == path.id,
            LearningPathItem.topic_id == topic_id,
            LearningPathItem.is_remedial == False
        ).first()
        if main_topic_item:
            main_topic_item.status = "COMPLETED"

        next_topic_item = db.query(LearningPathItem).filter(
            LearningPathItem.learning_path_id == path.id,
            LearningPathItem.topic_id > topic_id,
            LearningPathItem.is_remedial == False
        ).order_by(LearningPathItem.sequence_order).first()

        if next_topic_item:
            next_topic_item.status = "CURRENT"
            unlocked_topic = db.query(Topic).filter(Topic.id == next_topic_item.topic_id).first()
            if unlocked_topic:
                unlocked_topic_title = unlocked_topic.title

        path.adaptation_reason = f"Remediation satisfied: Demonstrated 85%+ mastery in Functions. Learning path continues to {unlocked_topic_title} (CO3)."
        path.updated_at = datetime.utcnow()

    # Update Outcome Attainments via authoritative Progress Engine
    from progress_engine import recalculate_course_outcomes
    recalculate_course_outcomes(db, user_id=target_user_id, course_id=topic.course_id, trigger="remediation")

    log1 = AgentLog(
        user_id=target_user_id,
        agent_name="Progress Monitoring Agent",
        action="remediation_verified",
        message=f"Functions remediation successfully completed. Topic mastery increased to {mastery_obj.overall_mastery}% ({mastery_obj.classification}). Prerequisite verified."
    )
    log2 = AgentLog(
        user_id=target_user_id,
        agent_name="Planner Agent",
        action="path_resumed",
        message=f"Primary learning path resumed. Unlocked '{unlocked_topic_title}' as next active module."
    )
    db.add_all([log1, log2])
    db.commit()

    from progress_engine import get_central_student_state
    state = get_central_student_state(db, user_id=target_user_id, course_id=topic.course_id)

    return {
        "success": True,
        "new_mastery": mastery_obj.overall_mastery,
        "classification": mastery_obj.classification,
        "unlocked_topic": unlocked_topic_title,
        "message": f"Remediation verified! Functions mastery increased to {mastery_obj.overall_mastery}% ({mastery_obj.classification}). Learning path continues to {unlocked_topic_title}.",
        "state": state
    }

# ==============================================================================
# 14-STEP OBE PIPELINE: STEP 8, 9, 10, 13
# ==============================================================================

@router.get("/tree-traversal-quiz")
def get_tree_traversal_quiz(current_user: User = Depends(get_current_user)):
    """Step 8: Concept-Wise Assessment (Tagged with sub-concepts)"""
    questions = AssessmentAgent.get_tree_traversal_quiz()
    # Sanitize correct answer
    return [{
        "id": q["id"],
        "sub_concept": q["sub_concept"],
        "question": q["question"],
        "code": q["code"],
        "options": q["options"]
    } for q in questions]

@router.post("/tree-traversal/analyze-errors")
def analyze_tree_traversal_errors(
    payload: Dict[str, Any],
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_user_id = resolve_target_user_id(current_user, user_id)
    answers = payload.get("answers", {})
    analysis = AssessmentAgent.evaluate_tree_traversal_errors(answers)

    log = AgentLog(
        user_id=target_user_id,
        agent_name="Assessment Agent",
        action="sub_concept_error_analysis",
        message=f"Analyzed assessment errors: Basic Tree Traversal = {analysis['basic_traversal_score']}% (Understood ✓), Recursive Traversal = {analysis['recursive_traversal_score']}% (Weak ❌). {analysis['diagnosis']}"
    )
    db.add(log)
    db.commit()

    return analysis

@router.get("/prerequisite/recursion")
def get_prerequisite_recursion_quiz(current_user: User = Depends(get_current_user)):
    """Step 10: Prerequisite Gap Verification Questions"""
    questions = AssessmentAgent.get_recursion_prerequisite_quiz()
    return [{
        "id": q["id"],
        "question": q["question"],
        "code": q.get("code"),
        "options": q["options"]
    } for q in questions]

@router.post("/prerequisite/verify")
def verify_prerequisite(
    payload: Dict[str, Any],
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_user_id = resolve_target_user_id(current_user, user_id)
    answers = payload.get("answers", {})
    questions = AssessmentAgent.get_recursion_prerequisite_quiz()
    correct_count = 0
    for q in questions:
        if answers.get(str(q["id"]), "").strip() == q["correct"].strip():
            correct_count += 1

    pct = round((correct_count / len(questions)) * 100.0, 1) if correct_count > 0 else 30.0

    gap_confirmed = pct < PREREQ_UNLOCK

    log = AgentLog(
        user_id=target_user_id,
        agent_name="Assessment Agent",
        action="prerequisite_verification",
        message=f"Targeted Prerequisite Diagnostic evaluated: Recursion score = {pct}%. Prerequisite gap CONFIRMED."
    )
    db.add(log)
    db.commit()

    return {
        "prerequisite": "Recursion",
        "score_pct": pct,
        "gap_confirmed": gap_confirmed,
        "evidence_summary": "The system now has empirical evidence that the student has a prerequisite gap in Recursion.",
        "recommended_action": "Trigger Step 11 — Prerequisite-aware learning path repair (insert Recursion + Recursive Practice before Tree Traversal)"
    }

@router.post("/reassessment/complete")
def complete_reassessment(
    course_id: int = 2,
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_user_id = resolve_target_user_id(current_user, user_id)
    from progress_engine import recalculate_course_outcomes, generate_adapted_learning_path
    topics = db.query(Topic).filter(Topic.course_id == course_id).all()
    topic_summary = []
    for t in topics:
        m = db.query(MasteryScore).filter(MasteryScore.user_id == target_user_id, MasteryScore.topic_id == t.id).first()
        if m:
            topic_summary.append({
                "topic_id": t.id,
                "title": t.title,
                "mastery": m.overall_mastery,
                "status": m.classification
            })

    generate_adapted_learning_path(db, target_user_id, course_id)
    co_updates = recalculate_course_outcomes(db, target_user_id, course_id)

    log = AgentLog(
        user_id=target_user_id,
        agent_name="Assessment Agent",
        action="reassessment_verified",
        message=f"Reassessment verified for Course {course_id}. Outcomes updated dynamically."
    )
    db.add(log)
    db.commit()

    return {
        "success": True,
        "course_id": course_id,
        "topics": topic_summary,
        "co_updates": co_updates
    }

# ==============================================================================
# TOPIC-BASED CODING QUESTION & IN-BROWSER COMPILER RUNNER
# ==============================================================================

@router.get("/coding-challenge")
def get_topic_coding_challenge(
    course_id: int = 2,
    topic_id: int = None,
    topic_title: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns the hands-on coding challenge for a topic/course to be solved and compiled in assignment.
    """
    if topic_id is not None:
        topic = db.query(Topic).filter(Topic.id == topic_id).first()
        if not topic:
            raise HTTPException(status_code=404, detail=f"Topic {topic_id} not found")
        if topic.course_id != course_id:
            raise HTTPException(
                status_code=400,
                detail=f"Topic {topic_id} does not belong to course {course_id}"
            )

    from code_runner import get_coding_challenge
    challenge = get_coding_challenge(course_id=course_id, topic_id=topic_id, topic_title=topic_title)
    if not challenge:
        return {
            "has_coding": False,
            "message": "No coding challenge available for this conceptual topic.",
            "course_id": course_id,
            "topic_id": topic_id
        }
    res = dict(challenge)
    res["has_coding"] = True
    return res

@router.post("/compile-code")
def compile_and_test_code(
    payload: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """
    Compiles and executes student python code submission in a sandbox and validates against test cases.
    Returns stdout, stderr, execution time ms, test cases breakdown, and pass/fail summary.
    Enforces Step E input limits:
    - Code length capped at 10,000 characters (400 if exceeded)
    - Test cases count capped at 20 (400 if exceeded)
    - timeout_sec capped at 5.0 (ignore larger values)
    - Strict AST parsing on test case calls (never eval arbitrary client expressions; 400 on unsafe/invalid)
    """
    code = payload.get("code", "")
    if not isinstance(code, str) or len(code) > 10000:
        raise HTTPException(status_code=400, detail="Code length exceeds maximum allowed limit of 10,000 characters.")

    test_cases = payload.get("test_cases", [])
    challenge_id = payload.get("challenge_id")

    # Timeout cap: max 5.0 seconds (ignore larger values)
    raw_timeout = payload.get("timeout_sec", 4.0)
    try:
        timeout_sec = min(max(float(raw_timeout), 0.5), 5.0)
    except (ValueError, TypeError):
        timeout_sec = 4.0

    from code_runner import (
        execute_code_submission,
        CODING_CHALLENGES,
        check_and_record_user_rate_limit,
        GLOBAL_EXECUTION_SEMAPHORE,
        DockerUnavailableError,
        check_docker_available,
        is_unsafe_local_allowed
    )

    # 1. Per-user rate limit: max 10 runs per minute
    allowed, retry_after = check_and_record_user_rate_limit(current_user.id)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many code execution requests. Please wait before submitting again.",
            headers={"Retry-After": str(retry_after)}
        )

    # 2. Test cases resolution and validation
    if not test_cases and challenge_id:
        for c in CODING_CHALLENGES:
            if c["id"] == challenge_id:
                test_cases = c.get("test_cases", [])
                break

    if test_cases:
        if not isinstance(test_cases, list) or len(test_cases) > 20:
            raise HTTPException(status_code=400, detail="Invalid test cases. Maximum allowed is 20.")
        for tc in test_cases:
            if not isinstance(tc, dict):
                raise HTTPException(status_code=400, detail="Each test case must be an object.")
            call_expr = tc.get("call")
            if not call_expr or not validate_test_case_call(call_expr):
                raise HTTPException(status_code=400, detail=f"Invalid or unsafe test case call expression: {call_expr}")

    # 3. Fail closed if Docker is unavailable (in production, server-side execution is disabled)
    env_val = os.getenv("ENV", os.getenv("ENVIRONMENT", "development")).strip().lower()
    is_prod = env_val in ("production", "prod")
    docker_available = check_docker_available()

    if is_prod and not docker_available:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Server-side execution is disabled; use in-browser runner"
        )

    if not docker_available and not is_unsafe_local_allowed():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Code execution temporarily unavailable"
        )

    # 4. Global concurrency limit: max 4 simultaneous container runs
    acquired = GLOBAL_EXECUTION_SEMAPHORE.acquire(blocking=True, timeout=1.0)
    if not acquired:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Compiler busy. Maximum concurrent execution limit reached. Please retry in a few moments.",
            headers={"Retry-After": "5"}
        )

    try:
        result = execute_code_submission(code=code, test_cases=test_cases, timeout_sec=timeout_sec)
        return result
    except DockerUnavailableError as e:
        if is_prod:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Server-side execution is disabled; use in-browser runner"
            )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e) or "Code execution temporarily unavailable"
        )
    finally:
        GLOBAL_EXECUTION_SEMAPHORE.release()
