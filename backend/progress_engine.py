import json
import uuid
import random
from collections import Counter
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from models import (
    User, StudentProfile, Course, CourseOutcome, Topic, TopicPrerequisite,
    TopicOutcomeMapping, MasteryScore, LearningPath, LearningPathItem,
    AgentLog, OutcomeAttainment, OutcomeAttainmentHistory, QuestionBank, AssessmentAttempt,
    QuestionAnswerHistory, MasteryHistory, ClassEnrollment, InterventionEvent
)
from core.thresholds import PREREQ_UNLOCK, ASSESSMENT_PASS, TOPIC_MASTERY, CO_ACHIEVED_DEFAULT

# ------------------------------------------------------------------------------
# 1. Configurable Scoring Weights & Mastery Classifications
# ------------------------------------------------------------------------------

WEIGHTS = {
    "diagnostic": {"prev": 0.0, "new": 1.0},
    "practice": {"prev": 0.6, "new": 0.4},
    "quiz": {"prev": 0.5, "new": 0.5},
    "assessment": {"prev": 0.4, "new": 0.6},
    "reassessment": {"prev": 0.3, "new": 0.7},
    "remedial": {"prev": 0.3, "new": 0.7},
    "completion": {"prev": 0.0, "new": 1.0}
}

def classify_mastery(percentage: float) -> str:
    """
    Classify student mastery percentage according to specification:
    >= 80% = MASTERED
    60-79% = DEVELOPING
    40-59% = NEEDS PRACTICE
    < 40% = WEAK
    """
    if percentage >= TOPIC_MASTERY:
        return "MASTERED"
    elif percentage >= PREREQ_UNLOCK:
        return "DEVELOPING"
    elif percentage >= 40.0:
        return "NEEDS PRACTICE"
    else:
        return "WEAK"

def get_action_for_topic(classification: str, is_locked: bool) -> str:
    if is_locked:
        return "Locked"
    if classification == "MASTERED":
        return "Review"
    elif classification == "DEVELOPING":
        return "Practice"
    elif classification == "NEEDS PRACTICE":
        return "Take Assessment"
    else: # WEAK
        return "Start Learning"

# ------------------------------------------------------------------------------
# 2. Prerequisite Integrity & Lock Status
# ------------------------------------------------------------------------------

def get_prerequisite_statuses(db: Session, user_id: int, course_id: int) -> Dict[int, Dict[str, Any]]:
    """
    Returns map of topic_id -> {is_locked: bool, unsatisfied_prereqs: list[str], prereqs: list[str]}
    Prerequisite is satisfied if overall_mastery >= required_mastery_pct (default 60%).
    """
    topics = db.query(Topic).filter(Topic.course_id == course_id).all()
    mastery_records = db.query(MasteryScore).filter(MasteryScore.user_id == user_id).all()
    mastery_map = {m.topic_id: m for m in mastery_records}

    result = {}
    for t in topics:
        prereq_records = db.query(TopicPrerequisite).filter(TopicPrerequisite.topic_id == t.id).all()
        unsatisfied = []
        all_prereqs = []

        prereq_details = []
        for pr in prereq_records:
            pr_topic = db.query(Topic).filter(Topic.id == pr.prerequisite_topic_id).first()
            pr_title = pr_topic.title if pr_topic else f"Topic {pr.prerequisite_topic_id}"
            pr_code = pr_topic.code if pr_topic else ""
            all_prereqs.append(pr_title)
            m_obj = mastery_map.get(pr.prerequisite_topic_id)
            pr_mastery = m_obj.overall_mastery if m_obj else 0.0
            is_pr_completed = bool(m_obj and (m_obj.completion_score or 0.0) >= 100.0)
            satisfied = (pr_mastery >= pr.required_mastery_pct) or is_pr_completed
            prereq_details.append({
                "topic_id": pr.prerequisite_topic_id,
                "title": pr_title,
                "code": pr_code,
                "required_mastery": float(pr.required_mastery_pct),
                "current_mastery": round(pr_mastery, 1),
                "is_satisfied": satisfied
            })
            if not satisfied:
                unsatisfied.append(f"{pr_title} ({round(pr_mastery)}% < {int(pr.required_mastery_pct)}%)")

        result[t.id] = {
            "is_locked": len(unsatisfied) > 0,
            "unsatisfied": unsatisfied,
            "prerequisites": all_prereqs,
            "prerequisite_details": prereq_details
        }

    return result

# ------------------------------------------------------------------------------
# 3. Course Outcome Evidence Attainment
# ------------------------------------------------------------------------------

def recalculate_course_outcomes(
    db: Session,
    user_id: int,
    course_id: int,
    trigger: str = "recalculation",
    write_history: bool = True
) -> List[Dict[str, Any]]:
    """
    Computes Course Outcome (CO1..CO4) attainment directly from contributing topics' mastery using TopicOutcomeMapping.weight.
    Guards against division by zero and ensures safe concurrent upsert and outcome history tracking.
    """
    outcomes = db.query(CourseOutcome).filter(CourseOutcome.course_id == course_id).order_by(CourseOutcome.code).all()
    if not outcomes:
        return []

    masteries = {
        m.topic_id: m.overall_mastery
        for m in db.query(MasteryScore).filter(MasteryScore.user_id == user_id).all()
    }

    results = []
    for co in outcomes:
        mappings = db.query(TopicOutcomeMapping).filter(TopicOutcomeMapping.outcome_id == co.id).all()
        contributing_topics = []
        total_weighted_score = 0.0
        total_weight = 0.0

        for m in mappings:
            t = db.query(Topic).filter(Topic.id == m.topic_id).first()
            if t:
                score = masteries.get(t.id, 0.0)
                w = float(m.weight) if (m.weight is not None and m.weight > 0) else 1.0
                total_weighted_score += score * w
                total_weight += w
                contributing_topics.append({
                    "topic_id": t.id,
                    "title": t.title,
                    "code": t.code,
                    "mastery": score,
                    "weight": w,
                    "status": classify_mastery(score)
                })

        # Guard against division by zero (Requirement 8)
        avg_score = round(total_weighted_score / total_weight, 1) if total_weight > 0 else 0.0
        target_pct = float(co.target_attainment_pct) if (co.target_attainment_pct is not None) else CO_ACHIEVED_DEFAULT
        status_label = "Achieved" if avg_score >= target_pct else ("In Progress" if avg_score >= 40.0 else "Needs Improvement")

        # Safe upsert to OutcomeAttainment (Requirement 9)
        attain = db.query(OutcomeAttainment).filter(
            OutcomeAttainment.user_id == user_id,
            OutcomeAttainment.course_id == course_id,
            OutcomeAttainment.outcome_id == co.id
        ).first()

        if not attain:
            try:
                attain = OutcomeAttainment(
                    user_id=user_id,
                    course_id=course_id,
                    outcome_id=co.id,
                    attainment_percentage=avg_score,
                    status=status_label
                )
                db.add(attain)
                db.flush()
            except IntegrityError:
                db.rollback()
                attain = db.query(OutcomeAttainment).filter(
                    OutcomeAttainment.user_id == user_id,
                    OutcomeAttainment.course_id == course_id,
                    OutcomeAttainment.outcome_id == co.id
                ).first()
                if attain:
                    attain.attainment_percentage = avg_score
                    attain.status = status_label
                    attain.updated_at = datetime.utcnow()
        else:
            attain.attainment_percentage = avg_score
            attain.status = status_label
            attain.updated_at = datetime.utcnow()

        # Record outcome_attainment_history snapshot once per event (Rule 2)
        if write_history:
            db.add(OutcomeAttainmentHistory(
                user_id=user_id,
                course_id=course_id,
                outcome_id=co.id,
                attainment_pct=avg_score,
                trigger=trigger,
                created_at=datetime.utcnow()
            ))

        weak_areas = [ct["title"] for ct in contributing_topics if ct["mastery"] < PREREQ_UNLOCK]
        remediation = (
            f"Review foundational topics: {', '.join(weak_areas)}"
            if weak_areas else "Target outcome criteria successfully satisfied."
        )

        results.append({
            "outcome_id": co.id,
            "code": co.code,
            "description": co.description,
            "target_pct": target_pct,
            "attainment_percentage": avg_score,
            "status": status_label,
            "contributing_topics": contributing_topics,
            "weak_areas": weak_areas,
            "remediation": remediation
        })

    db.commit()
    return results

# ------------------------------------------------------------------------------
# 4. Adaptive Learning Path Generation
# ------------------------------------------------------------------------------

def generate_adapted_learning_path(db: Session, user_id: int, course_id: int, reason: str = "Adaptive update") -> LearningPath:
    """
    Generates personalized learning path prioritizing prerequisite gaps and weak topics.
    """
    topics = db.query(Topic).filter(Topic.course_id == course_id).order_by(Topic.order_index).all()
    if not topics:
        raise ValueError(f"No topics found for course {course_id}")

    masteries_objs = db.query(MasteryScore).filter(MasteryScore.user_id == user_id).all()
    mastery_map = {m.topic_id: m for m in masteries_objs}
    prereq_status = get_prerequisite_statuses(db, user_id, course_id)

    # Categorize and prioritize topics according to curriculum sequence and prerequisite rules:
    # 1. Unlocked, incomplete topics sorted by curriculum order (Topic 1 -> Topic 2 -> ...)
    # 2. Locked topics (will unlock as prerequisites reach >= 60%)
    # 3. Mastered / completed topics -> placed at end as completed
    def priority_key(t: Topic):
        m_obj = mastery_map.get(t.id)
        m_pct = m_obj.overall_mastery if m_obj else 0.0
        is_completed = bool((m_obj and (m_obj.completion_score or 0.0) >= 100.0) or (m_pct >= TOPIC_MASTERY))
        is_locked = prereq_status[t.id]["is_locked"]

        # If completed, place at end
        if is_completed:
            return (3, t.order_index)
        # If locked, place after unlocked
        if is_locked:
            return (2, t.order_index)
        # Unlocked incomplete topics strictly follow curriculum order
        return (1, t.order_index)

    sorted_topics = sorted(topics, key=priority_key)

    # Archive previous active path
    active_paths = db.query(LearningPath).filter(
        LearningPath.user_id == user_id,
        LearningPath.course_id == course_id,
        LearningPath.status == "ACTIVE"
    ).all()
    for ap in active_paths:
        ap.status = "REPLACED"

    new_path = LearningPath(
        user_id=user_id,
        course_id=course_id,
        status="ACTIVE",
        adaptation_reason=reason
    )
    db.add(new_path)
    db.commit()

    current_assigned = False
    seq = 1

    for t in sorted_topics:
        m_obj = mastery_map.get(t.id)
        m_pct = m_obj.overall_mastery if m_obj else 0.0
        is_completed = bool((m_obj and (m_obj.completion_score or 0.0) >= 100.0) or (m_pct >= TOPIC_MASTERY))
        is_locked = prereq_status[t.id]["is_locked"]
        cls_name = "MASTERED" if is_completed else classify_mastery(m_pct)

        if is_completed:
            status = "COMPLETED"
            recom_reason = f"Completed ({round(m_pct)}% mastery) — review optional."
        elif is_locked:
            status = "LOCKED"
            recom_reason = f"Locked until prerequisite is improved: {', '.join(prereq_status[t.id]['unsatisfied'])}"
        else:
            if not current_assigned:
                status = "CURRENT"
                current_assigned = True
                if cls_name == "WEAK":
                    recom_reason = f"Primary prerequisite focus: Current mastery is {round(m_pct)}% (Weak). Targeted remediation required."
                else:
                    recom_reason = f"Current target: {cls_name} ({round(m_pct)}%). Focus on practice & assessment."
            else:
                status = "RECOMMENDED"
                recom_reason = f"Next in sequence: {cls_name} ({round(m_pct)}%)."

        item = LearningPathItem(
            learning_path_id=new_path.id,
            topic_id=t.id,
            sequence_order=seq,
            status=status,
            recommendation_reason=recom_reason,
            is_remedial=(cls_name == "WEAK" and not is_locked),
            remedial_title=f"{t.title} (Remediation)" if (cls_name == "WEAK" and not is_locked) else None
        )
        db.add(item)
        seq += 1

    # Record intervention events for class cohort tracking
    active_enr = db.query(ClassEnrollment).filter(
        ClassEnrollment.student_id == user_id,
        ClassEnrollment.status == "active"
    ).order_by(ClassEnrollment.joined_at.desc()).first()
    active_class_id = active_enr.class_id if active_enr else None

    db.add(InterventionEvent(
        student_id=user_id,
        class_id=active_class_id,
        topic_id=None,
        type="path_adapted",
        created_at=datetime.utcnow(),
        note=reason
    ))

    # Check if any remedial items were inserted
    remedial_items = [i for i in sorted_topics if (classify_mastery(mastery_map.get(i.id).overall_mastery if mastery_map.get(i.id) else 0.0) == "WEAK" and not prereq_status[i.id]["is_locked"])]
    for rt in remedial_items:
        db.add(InterventionEvent(
            student_id=user_id,
            class_id=active_class_id,
            topic_id=rt.id,
            type="remedial_inserted",
            created_at=datetime.utcnow(),
            note=f"Remedial module inserted for {rt.title} (demonstrated deficit)"
        ))

    db.commit()
    return new_path

# ------------------------------------------------------------------------------
# 5. Mastery Update with Activity Weights
# ------------------------------------------------------------------------------

def update_topic_mastery(
    db: Session,
    user_id: int,
    topic_id: int,
    score: float,
    activity_type: str = "practice",
    reason: str = ""
) -> Dict[str, Any]:
    """
    Updates student mastery for a topic using configurable activity weights:
    - Practice: 60% prev + 40% score
    - Quiz: 50% prev + 50% score
    - Assessment: 40% prev + 60% score
    - Remedial: 30% prev + 70% score
    - Diagnostic: 100% score (baseline)
    """
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise ValueError(f"Topic {topic_id} not found")

    mastery_obj = db.query(MasteryScore).filter(
        MasteryScore.user_id == user_id,
        MasteryScore.topic_id == topic_id
    ).first()

    if not mastery_obj:
        mastery_obj = MasteryScore(user_id=user_id, topic_id=topic_id)
        db.add(mastery_obj)
        prev_mastery = 0.0
    else:
        prev_mastery = mastery_obj.overall_mastery

    weight_info = WEIGHTS.get(activity_type.lower(), WEIGHTS["practice"])
    new_mastery = round((prev_mastery * weight_info["prev"]) + (score * weight_info["new"]), 1)
    new_mastery = min(max(new_mastery, 0.0), 100.0)

    # Update scores
    if activity_type == "diagnostic":
        mastery_obj.diagnostic_score = score
    elif activity_type in ["quiz", "assessment"]:
        mastery_obj.quiz_score = score
    elif activity_type in ["practice", "remedial"]:
        mastery_obj.practice_score = score
    elif activity_type == "completion":
        mastery_obj.completion_score = score
        mastery_obj.quiz_score = max(mastery_obj.quiz_score or 0.0, score)
        mastery_obj.practice_score = max(mastery_obj.practice_score or 0.0, score)

    mastery_obj.overall_mastery = new_mastery
    mastery_obj.classification = classify_mastery(new_mastery)
    mastery_obj.updated_at = datetime.utcnow()

    # Record history
    history = MasteryHistory(
        user_id=user_id,
        topic_id=topic_id,
        previous_mastery=prev_mastery,
        new_mastery=new_mastery,
        activity_type=activity_type,
        source=activity_type,
        score=score,
        reason=reason or f"{activity_type.capitalize()} completed with score {score}%"
    )
    db.add(history)

    # Re-evaluate prerequisites and learning path
    generate_adapted_learning_path(db, user_id, topic.course_id, reason=f"Mastery updated for {topic.title} ({prev_mastery}% -> {new_mastery}%)")
    recalculate_course_outcomes(db, user_id, topic.course_id, trigger=activity_type)

    db.commit()
    return {
        "topic_id": topic_id,
        "topic_title": topic.title,
        "previous_mastery": prev_mastery,
        "new_mastery": new_mastery,
        "classification": mastery_obj.classification,
        "activity_type": activity_type
    }

# ------------------------------------------------------------------------------
# 6. Adaptive Question Selection & Assessment Engine
# ------------------------------------------------------------------------------

def select_adaptive_questions(
    db: Session,
    user_id: int,
    course_id: int,
    topic_id: Optional[int] = None,
    count: int = 5,
    attempt_type: str = "assessment"
) -> List[Dict[str, Any]]:
    """
    Selects questions from QuestionBank:
    - Never serves the exact same questions repeatedly.
    - Tracks recent attempts to prevent immediate question repetition across consecutive sessions.
    - Rotates questions based on recency and historical answer frequency.
    - Adjusts difficulty according to student mastery (Beginner / Intermediate / Advanced).
    - Randomizes selection among candidate questions so retakes are dynamic and varied.
    - Prioritizes weak topics when topic_id is None.
    """
    # 1. Fetch user's historical answers with attempt and timestamps
    history_records = (
        db.query(
            QuestionAnswerHistory.question_id,
            QuestionAnswerHistory.created_at,
            QuestionAnswerHistory.attempt_id
        )
        .filter(QuestionAnswerHistory.user_id == user_id)
        .order_by(QuestionAnswerHistory.created_at.desc())
        .all()
    )

    answer_counts = Counter(r[0] for r in history_records)
    all_answered_ids = set(answer_counts.keys())

    last_answered_time = {}
    for qid, dt, _ in reversed(history_records):
        last_answered_time[qid] = dt

    # Identify questions from the most recent 2 attempts for this user
    recent_attempt_ids = []
    seen_attempts = set()
    for _, _, att_id in history_records:
        if att_id and att_id not in seen_attempts:
            seen_attempts.add(att_id)
            recent_attempt_ids.append(att_id)
            if len(recent_attempt_ids) >= 2:
                break

    recent_qids = {
        r[0] for r in history_records if r[2] in set(recent_attempt_ids)
    }

    selected_questions = []

    if topic_id:
        topic_obj = db.query(Topic).filter(Topic.id == topic_id).first()
        if not topic_obj or topic_obj.course_id != course_id:
            return []

        # Single-topic quiz / practice
        m = db.query(MasteryScore).filter(
            MasteryScore.user_id == user_id,
            MasteryScore.topic_id == topic_id
        ).first()
        m_pct = m.overall_mastery if m else 0.0

        # Determine target difficulty based on student mastery
        target_diff = "Beginner" if m_pct < 40.0 else ("Intermediate" if m_pct < TOPIC_MASTERY else "Advanced")

        all_topic_q = db.query(QuestionBank).filter(
            QuestionBank.topic_id == topic_id,
            QuestionBank.course_id == course_id
        ).all()
        if not all_topic_q:
            return []

        # Tier 1: Brand new (never answered), matching target difficulty
        tier1 = [q for q in all_topic_q if q.id not in all_answered_ids and q.difficulty == target_diff]
        random.shuffle(tier1)

        # Tier 2: Brand new (never answered), other difficulties
        tier2 = [q for q in all_topic_q if q.id not in all_answered_ids and q.difficulty != target_diff]
        random.shuffle(tier2)

        # Tier 3: Answered previously, but NOT in recent attempts (least answered + oldest first, shuffled on ties)
        tier3 = [q for q in all_topic_q if q.id in all_answered_ids and q.id not in recent_qids]
        random.shuffle(tier3)
        tier3.sort(key=lambda q: (answer_counts.get(q.id, 0), last_answered_time.get(q.id, datetime.min)))

        # Tier 4: Answered in recent attempts (least answered + oldest first, shuffled on ties)
        tier4 = [q for q in all_topic_q if q.id in recent_qids]
        random.shuffle(tier4)
        tier4.sort(key=lambda q: (answer_counts.get(q.id, 0), last_answered_time.get(q.id, datetime.min)))

        candidates = tier1 + tier2 + tier3 + tier4
        selected_questions = candidates[:count]
        # Shuffle final questions so they don't always appear in difficulty clusters or predictable order
        random.shuffle(selected_questions)

    else:
        # Multi-topic / Course-Level Adaptive Assessment
        topics = db.query(Topic).filter(Topic.course_id == course_id).all()
        masteries = {
            m.topic_id: m.overall_mastery
            for m in db.query(MasteryScore).filter(MasteryScore.user_id == user_id).all()
        }

        # Group topics by 10% mastery bands to randomize within similar performance
        topic_buckets = {}
        for t in topics:
            bucket = round(masteries.get(t.id, 0.0) / 10.0) * 10
            topic_buckets.setdefault(bucket, []).append(t)

        sorted_topics = []
        for bucket in sorted(topic_buckets.keys()):
            b_topics = list(topic_buckets[bucket])
            random.shuffle(b_topics)
            sorted_topics.extend(b_topics)

        chosen_ids = set()

        for t in sorted_topics:
            if len(selected_questions) >= count:
                break
            m_pct = masteries.get(t.id, 0.0)
            diff = "Beginner" if m_pct < 40.0 else ("Intermediate" if m_pct < TOPIC_MASTERY else "Advanced")

            all_t_q = db.query(QuestionBank).filter(
                QuestionBank.topic_id == t.id,
                QuestionBank.course_id == course_id
            ).all()
            if not all_t_q:
                continue

            t_tier1 = [q for q in all_t_q if q.id not in all_answered_ids and q.id not in chosen_ids and q.difficulty == diff]
            random.shuffle(t_tier1)

            t_tier2 = [q for q in all_t_q if q.id not in all_answered_ids and q.id not in chosen_ids]
            random.shuffle(t_tier2)

            t_tier3 = [q for q in all_t_q if q.id not in recent_qids and q.id not in chosen_ids]
            random.shuffle(t_tier3)
            t_tier3.sort(key=lambda q: (answer_counts.get(q.id, 0), last_answered_time.get(q.id, datetime.min)))

            t_tier4 = [q for q in all_t_q if q.id not in chosen_ids]
            random.shuffle(t_tier4)
            t_tier4.sort(key=lambda q: (answer_counts.get(q.id, 0), last_answered_time.get(q.id, datetime.min)))

            picked = None
            for pool in (t_tier1, t_tier2, t_tier3, t_tier4):
                if pool:
                    pool_slice = pool[:max(3, len(pool) // 2)]
                    picked = random.choice(pool_slice)
                    break

            if picked:
                selected_questions.append(picked)
                chosen_ids.add(picked.id)

        # Fill up to count if needed from remaining course questions
        if len(selected_questions) < count:
            remaining_q = db.query(QuestionBank).filter(
                QuestionBank.course_id == course_id,
                ~QuestionBank.id.in_(chosen_ids)
            ).all()
            random.shuffle(remaining_q)
            remaining_q.sort(key=lambda q: (
                1 if q.id in recent_qids else 0,
                answer_counts.get(q.id, 0),
                last_answered_time.get(q.id, datetime.min)
            ))
            for q in remaining_q:
                if len(selected_questions) >= count:
                    break
                selected_questions.append(q)
                chosen_ids.add(q.id)

        random.shuffle(selected_questions)

    # Sanitize payload for client
    result = []
    for q in selected_questions:
        opts = json.loads(q.options_json) if isinstance(q.options_json, str) else q.options_json
        t = db.query(Topic).filter(Topic.id == q.topic_id).first()
        co = db.query(CourseOutcome).filter(CourseOutcome.id == q.outcome_id).first() if q.outcome_id else None
        result.append({
            "id": q.id,
            "course_id": q.course_id,
            "topic_id": q.topic_id,
            "topic_title": t.title if t else "General",
            "sub_concept": q.sub_concept,
            "outcome_id": q.outcome_id,
            "outcome_code": co.code if co else None,
            "difficulty": q.difficulty,
            "question_type": q.question_type,
            "question_text": q.question_text,
            "code_snippet": q.code_snippet,
            "options": opts,
            "explanation": q.explanation
        })

    return result

def record_assessment_attempt(
    db: Session,
    user_id: int,
    course_id: int,
    attempt_type: str,
    submitted_answers: Dict[str, str], # question_id (str) -> selected_answer
    topic_id: Optional[int] = None,
    coding_submission: Optional[Dict[str, Any]] = None # optional coding challenge compiler submission
) -> Dict[str, Any]:
    """
    Evaluates answers and optional coding challenge submission, creates a unique AssessmentAttempt,
    logs QuestionAnswerHistory, updates topic mastery, and executes closed-loop adaptation.
    """
    from fastapi import HTTPException

    # 0. Check prerequisite locking for specific topic
    if topic_id:
        topic = db.query(Topic).filter(Topic.id == topic_id).first()
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")
        prereq_status = get_prerequisite_statuses(db, user_id, course_id)
        if prereq_status.get(topic_id, {}).get("is_locked", False):
            unsat = prereq_status[topic_id].get("unsatisfied", [])
            detail_msg = f"Topic is locked. Prerequisite mastery threshold not met: {', '.join(unsat)}" if unsat else "Topic is locked. Complete prerequisites first."
            raise HTTPException(status_code=403, detail=detail_msg)

    q_ids = [int(qid) for qid in submitted_answers.keys() if str(qid).isdigit()]
    questions = db.query(QuestionBank).filter(QuestionBank.id.in_(q_ids)).all() if q_ids else []
    q_map = {q.id: q for q in questions}

    correct_count = 0
    total_q = max(len(submitted_answers), 1)
    topic_eval: Dict[int, Dict[str, int]] = {} # topic_id -> {correct, total}
    question_details = []

    for qid_str, user_ans in submitted_answers.items():
        if not str(qid_str).isdigit():
            continue
        qid = int(qid_str)
        q = q_map.get(qid)
        if not q:
            continue

        is_correct = (user_ans.strip() == q.correct_answer.strip())
        if is_correct:
            correct_count += 1

        tid = q.topic_id
        if tid not in topic_eval:
            topic_eval[tid] = {"correct": 0, "total": 0}
        topic_eval[tid]["total"] += 1
        if is_correct:
            topic_eval[tid]["correct"] += 1

        t = db.query(Topic).filter(Topic.id == q.topic_id).first()
        co = db.query(CourseOutcome).filter(CourseOutcome.id == q.outcome_id).first() if q.outcome_id else None
        question_details.append({
            "question_id": q.id,
            "topic_id": q.topic_id,
            "topic_title": t.title if t else None,
            "sub_concept": q.sub_concept,
            "difficulty": q.difficulty,
            "outcome_id": q.outcome_id,
            "outcome_code": co.code if co else None,
            "question_text": q.question_text,
            "selected_answer": user_ans,
            "correct_answer": q.correct_answer,
            "is_correct": is_correct,
            "explanation": q.explanation
        })

    # Calculate per-topic percentages
    topic_scores = {}
    for tid, info in topic_eval.items():
        topic_scores[tid] = round((info["correct"] / max(info["total"], 1)) * 100.0, 1)

    # Evaluate optional coding submission from in-assignment compiler
    # Security Rule: Browser/client code execution results are UNTRUSTED and marked "self-verified".
    # They are displayed for formative student practice feedback only, but NEVER count toward
    # official assessment score percentage, topic completion evidence, topic mastery, or course outcome attainment.
    has_coding = coding_submission is not None and isinstance(coding_submission, dict)
    if has_coding:
        coding_submission["self_verified"] = True
        coding_submission["status"] = "self-verified"
        coding_submission["is_practice_feedback"] = True

    # Official percentage and passed status are determined strictly by server-graded MCQ questions
    percentage = round((correct_count / max(total_q, 1)) * 100.0, 1)
    display_score = correct_count
    display_max = total_q

    passed = percentage >= ASSESSMENT_PASS

    # Reassessment rule:
    # An attempt is "initial" if attempt_type="diagnostic"
    # An attempt is "reassessment" if the student attempts a topic again after a previous attempt on that topic
    # (or after a remedial module was inserted).
    effective_attempt_type = attempt_type
    if attempt_type != "diagnostic" and topic_id:
        prior_attempt = db.query(AssessmentAttempt).filter(
            AssessmentAttempt.user_id == user_id,
            AssessmentAttempt.topic_id == topic_id
        ).first()
        if not prior_attempt:
            for pa in db.query(AssessmentAttempt).filter(
                AssessmentAttempt.user_id == user_id,
                AssessmentAttempt.topic_id == None
            ).all():
                if pa.topic_scores_json:
                    try:
                        scores = json.loads(pa.topic_scores_json)
                        if str(topic_id) in scores or topic_id in scores:
                            prior_attempt = pa
                            break
                    except Exception:
                        pass

        prior_remedial = db.query(LearningPathItem).join(LearningPath).filter(
            LearningPath.user_id == user_id,
            LearningPathItem.topic_id == topic_id,
            LearningPathItem.is_remedial == True
        ).first()

        if prior_attempt or prior_remedial:
            effective_attempt_type = "reassessment"

    # 1. Create unique AssessmentAttempt in ONE transaction
    attempt_uuid = f"att-{uuid.uuid4().hex[:12]}"
    attempt = AssessmentAttempt(
        attempt_uuid=attempt_uuid,
        user_id=user_id,
        course_id=course_id,
        topic_id=topic_id,
        attempt_type=effective_attempt_type,
        score=display_score,
        max_score=display_max,
        percentage=percentage,
        passed=passed,
        topic_scores_json=json.dumps(topic_scores),
        answers_json=json.dumps({
            "questions": question_details,
            "coding_submission": coding_submission if has_coding else None
        }),
        created_at=datetime.utcnow()
    )
    db.add(attempt)
    db.flush()

    # 2. Save QuestionAnswerHistory
    for q_detail in question_details:
        concept_val = q_detail.get("sub_concept") or "General"
        db.add(QuestionAnswerHistory(
            attempt_id=attempt.id,
            user_id=user_id,
            question_id=q_detail["question_id"],
            concept=concept_val,
            selected_answer=q_detail["selected_answer"],
            is_correct=q_detail["is_correct"]
        ))

    # 3. Update Mastery for each topic evaluated (Rule 2 & 3)
    target_topics = dict(topic_scores)
    if topic_id and not target_topics:
        target_topics[topic_id] = percentage

    updated_masteries = {}
    for tid, t_pct in target_topics.items():
        m_obj = db.query(MasteryScore).filter(
            MasteryScore.user_id == user_id,
            MasteryScore.topic_id == tid
        ).first()
        if not m_obj:
            m_obj = MasteryScore(user_id=user_id, topic_id=tid, diagnostic_score=0.0, quiz_score=0.0, practice_score=0.0, completion_score=0.0, overall_mastery=0.0)
            db.add(m_obj)
            prev_mastery = 0.0
        else:
            prev_mastery = m_obj.overall_mastery or 0.0

        if passed:
            # Rule 2: set overall_mastery = max(current, score), mark topic COMPLETED
            new_mastery = max(prev_mastery, t_pct)
            m_obj.completion_score = 100.0
            m_obj.overall_mastery = new_mastery
            m_obj.practice_score = max(m_obj.practice_score or 0.0, t_pct)
            if attempt_type == "quiz":
                m_obj.quiz_score = max(m_obj.quiz_score or 0.0, t_pct)
            m_obj.classification = classify_mastery(new_mastery)
            m_obj.updated_at = datetime.utcnow()
            history_reason = f"Passed {attempt_type} assessment with score {t_pct}%. Topic marked completed."
        else:
            # Rule 3: update mastery with max/weighted logic, keep topic CURRENT
            weight_info = WEIGHTS.get(attempt_type.lower(), WEIGHTS["practice"])
            weighted_val = round((prev_mastery * weight_info["prev"]) + (t_pct * weight_info["new"]), 1)
            new_mastery = min(max(weighted_val, 0.0), 100.0)
            m_obj.overall_mastery = new_mastery
            m_obj.practice_score = t_pct
            if attempt_type == "quiz":
                m_obj.quiz_score = t_pct
            m_obj.classification = classify_mastery(new_mastery)
            m_obj.updated_at = datetime.utcnow()
            history_reason = f"{attempt_type.capitalize()} assessment attempt scored {t_pct}%. Requires further practice."

        # Write MasteryHistory ONCE
        db.add(MasteryHistory(
            user_id=user_id,
            topic_id=tid,
            previous_mastery=prev_mastery,
            new_mastery=new_mastery,
            activity_type=effective_attempt_type,
            source="reassessment" if effective_attempt_type == "reassessment" else effective_attempt_type,
            score=t_pct,
            reason=history_reason,
            created_at=datetime.utcnow()
        ))

        updated_masteries[tid] = {
            "topic_id": tid,
            "previous_mastery": prev_mastery,
            "new_mastery": new_mastery,
            "classification": m_obj.classification,
            "activity_type": effective_attempt_type
        }

    # 4. Update StudentProfile diagnostic flag if applicable
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()
    if profile:
        profile.diagnostic_completed = True

    # Flush session to DB so learning path synthesis and prerequisite checks see updated mastery immediately
    db.flush()

    # 5. Adapt learning path: marks topic COMPLETED, unlocks dependent topics, assigns next to CURRENT
    adaptation_reason = f"{attempt_type.capitalize()} evaluated: {percentage}% ({'Passed ✓' if passed else 'Needs Practice'})."
    generate_adapted_learning_path(db, user_id, course_id, reason=adaptation_reason)

    # 6. Recalculate Course Outcomes (weighted) once
    recalculate_course_outcomes(db, user_id, course_id, trigger=attempt_type, write_history=True)

    # 7. Log agent event
    log = AgentLog(
        user_id=user_id,
        agent_name="Progress Monitoring Agent",
        action=f"{attempt_type}_evaluation",
        message=f"Assessment evaluated: Score = {correct_count}/{total_q} ({percentage}%). Passed: {passed}. Learning path adapted."
    )
    db.add(log)
    db.commit()

    # 8. Query adapted learning path for next_topic and course_completed
    active_path = db.query(LearningPath).filter(
        LearningPath.user_id == user_id,
        LearningPath.course_id == course_id,
        LearningPath.status == "ACTIVE"
    ).order_by(LearningPath.id.desc()).first()

    active_items = db.query(LearningPathItem).filter(
        LearningPathItem.learning_path_id == (active_path.id if active_path else -1)
    ).order_by(LearningPathItem.sequence_order).all() if active_path else []

    next_topic_item = next((i for i in active_items if i.status == "CURRENT"), None)
    all_completed = len(active_items) > 0 and all(i.status == "COMPLETED" for i in active_items if not i.is_remedial)

    next_topic_data = None
    if next_topic_item:
        nt_topic = db.query(Topic).filter(Topic.id == next_topic_item.topic_id).first()
        next_topic_data = {
            "id": next_topic_item.topic_id,
            "title": nt_topic.title if nt_topic else f"Topic {next_topic_item.topic_id}",
            "status": next_topic_item.status
        }

    # 9. Fetch synchronized CentralStudentState
    state = get_central_student_state(db, user_id=user_id, course_id=course_id)

    primary_update = updated_masteries.get(topic_id) if topic_id else (
        list(updated_masteries.values())[0] if updated_masteries else None
    )

    weak_sub_concepts = list({
        d["sub_concept"]
        for d in question_details
        if not d["is_correct"] and d.get("sub_concept")
    })

    adaptation_message = f"Assessment completed with score {percentage}%. " + (
        "Topic marked completed and next module unlocked." if passed else
        "Remedial learning path generated to reinforce fundamental concepts."
    )

    primary_new_mastery = primary_update["new_mastery"] if primary_update else percentage

    eval_data = {
        "attempt_uuid": attempt_uuid,
        "attempt_type": attempt_type,
        "score": display_score,
        "max_score": display_max,
        "mcq_score": correct_count,
        "mcq_total": len(question_details),
        "percentage": percentage,
        "score_percentage": percentage,
        "passed": passed,
        "pass_mark": float(ASSESSMENT_PASS),
        "adaptation_message": adaptation_message,
        "topic_scores": topic_scores,
        "weak_sub_concepts": weak_sub_concepts,
        "updated_masteries": updated_masteries,
        "primary_mastery": primary_update,
        "question_details": question_details,
        "per_question_results": question_details,
        "coding_result": coding_submission if has_coding else None,
        "new_mastery": primary_new_mastery,
        "topic_status": "COMPLETED" if passed else "CURRENT",
        "next_topic": next_topic_data,
        "course_completed": all_completed or bool(state.get("courseCompleted")),
        "state": state
    }

    return eval_data

# ------------------------------------------------------------------------------
# 7. Central Persistent Student State Provider
# ------------------------------------------------------------------------------

def get_central_student_state(db: Session, user_id: int, course_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Returns the single unified source of truth for the student across all pages.
    """
    # 1. User & Profile
    user = db.query(User).filter(User.id == user_id).first()
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()

    if not profile:
        profile = StudentProfile(user_id=user_id, selected_course_id=1)
        db.add(profile)
        db.commit()
        db.refresh(profile)

    actual_course_id = course_id or profile.selected_course_id or 1

    # 2. Course & Topics
    course = db.query(Course).filter(Course.id == actual_course_id).first()
    topics = db.query(Topic).filter(Topic.course_id == actual_course_id).order_by(Topic.order_index).all()
    if not topics:
        topics = db.query(Topic).order_by(Topic.order_index).all()
        if topics:
            actual_course_id = topics[0].course_id
            course = db.query(Course).filter(Course.id == actual_course_id).first()

    # 3. Topic Mastery & Status
    masteries = db.query(MasteryScore).filter(MasteryScore.user_id == user_id).all()
    mastery_map = {m.topic_id: m for m in masteries}

    # Safe backfill: handle old attempts that passed but never completed (Rule 6)
    passed_attempts = db.query(AssessmentAttempt).filter(
        AssessmentAttempt.user_id == user_id,
        AssessmentAttempt.passed == True,
        AssessmentAttempt.topic_id.isnot(None)
    ).all()

    backfilled_any = False
    for att in passed_attempts:
        m = mastery_map.get(att.topic_id)
        if not m:
            m = MasteryScore(
                user_id=user_id,
                topic_id=att.topic_id,
                diagnostic_score=0.0,
                quiz_score=0.0,
                practice_score=att.percentage or 0.0,
                completion_score=100.0,
                overall_mastery=att.percentage or 0.0,
                classification=classify_mastery(att.percentage or 0.0)
            )
            db.add(m)
            mastery_map[att.topic_id] = m
            backfilled_any = True
        elif (m.completion_score or 0.0) < 100.0:
            m.completion_score = 100.0
            m.overall_mastery = max(m.overall_mastery or 0.0, att.percentage or 0.0)
            m.classification = classify_mastery(m.overall_mastery)
            backfilled_any = True

    if backfilled_any:
        db.commit()
        masteries = db.query(MasteryScore).filter(MasteryScore.user_id == user_id).all()
        mastery_map = {m.topic_id: m for m in masteries}

    prereq_status = get_prerequisite_statuses(db, user_id, actual_course_id)

    # 4. Learning Path (ensure active path exists)
    path = db.query(LearningPath).filter(
        LearningPath.user_id == user_id,
        LearningPath.course_id == actual_course_id,
        LearningPath.status == "ACTIVE"
    ).order_by(LearningPath.updated_at.desc()).first()

    if not path and topics:
        path = generate_adapted_learning_path(db, user_id, actual_course_id, "Initial path synthesis")

    path_items_objs = db.query(LearningPathItem).filter(
        LearningPathItem.learning_path_id == (path.id if path else -1)
    ).order_by(LearningPathItem.sequence_order).all()

    item_status_map = {i.topic_id: i.status for i in path_items_objs if not i.is_remedial}

    # Format Topic Mastery
    topic_mastery_list = []
    for t in topics:
        m_obj = mastery_map.get(t.id)
        ovr = m_obj.overall_mastery if m_obj else 0.0
        cls_name = classify_mastery(ovr)
        status = item_status_map.get(t.id, "LOCKED" if prereq_status[t.id]["is_locked"] else "RECOMMENDED")
        if ovr >= TOPIC_MASTERY or (m_obj and (m_obj.completion_score or 0.0) >= 100.0):
            status = "COMPLETED"
            cls_name = "MASTERED"
        elif prereq_status[t.id]["is_locked"]:
            status = "LOCKED"
        cos = [m.outcome.code for m in t.outcome_mappings]

        topic_mastery_list.append({
            "topic_id": t.id,
            "title": t.title,
            "code": t.code,
            "order_index": t.order_index,
            "difficulty": t.difficulty,
            "est_minutes": t.est_minutes,
            "mastery": ovr,
            "classification": cls_name,
            "status": status,
            "is_locked": prereq_status[t.id]["is_locked"],
            "prerequisites": prereq_status[t.id]["prerequisites"],
            "unsatisfied_prerequisites": prereq_status[t.id]["unsatisfied"],
            "prerequisite_details": prereq_status[t.id].get("prerequisite_details", []),
            "outcomes": cos,
            "action": get_action_for_topic(cls_name, prereq_status[t.id]["is_locked"])
        })

    # 5. Course Outcome Attainments (read synchronization: do not write duplicate history rows)
    co_list = recalculate_course_outcomes(db, user_id, actual_course_id, trigger="state_sync", write_history=False)
    overall_obe = round(sum(c["attainment_percentage"] for c in co_list) / max(len(co_list), 1), 1)

    # 6. Overall Metrics
    total_topics_count = len(topics)
    mastered_count = sum(1 for tm in topic_mastery_list if tm["mastery"] >= TOPIC_MASTERY or tm["status"] == "COMPLETED")
    overall_mastery = round(sum(tm["mastery"] for tm in topic_mastery_list) / max(total_topics_count, 1), 1)
    # Overall Progress = weighted completion + mastery progress
    overall_progress = round(
        (mastered_count / max(total_topics_count, 1)) * 50.0 +
        (overall_mastery / 100.0) * 50.0,
        1
    )

    # 7. Current Target Topic Resolution
    current_target = None
    # 1. Topic explicitly marked CURRENT that is incomplete and not locked
    for tm in topic_mastery_list:
        if tm["status"] == "CURRENT" and tm["mastery"] < TOPIC_MASTERY and tm["status"] != "COMPLETED" and not tm["is_locked"]:
            current_target = tm
            break
    # 2. First unlocked, incomplete topic according to curriculum sequence
    if not current_target:
        for tm in topic_mastery_list:
            if not tm["is_locked"] and tm["mastery"] < TOPIC_MASTERY and tm["status"] != "COMPLETED":
                current_target = tm
                break
    # 3. If all unlocked topics are completed, check if any incomplete topic remains (could be locked)
    if not current_target:
        for tm in topic_mastery_list:
            if tm["mastery"] < TOPIC_MASTERY and tm["status"] != "COMPLETED":
                current_target = tm
                break
    # If all eligible topics are complete, current_target remains None (course complete)

    is_course_completed = (mastered_count == total_topics_count) or (current_target is None and total_topics_count > 0)

    # 8. AI Recommendation
    # Find weakest prerequisite gap
    weakest_prereq_gap = None
    for tm in topic_mastery_list:
        if tm["unsatisfied_prerequisites"] and tm["status"] != "COMPLETED":
            weakest_prereq_gap = tm
            break

    weakest_topic = min((tm for tm in topic_mastery_list if tm["status"] != "COMPLETED"), key=lambda x: x["mastery"], default=None)

    if is_course_completed:
        rec_text = "Outstanding achievement! You have mastered all topics and satisfied course learning outcomes."
    elif weakest_prereq_gap:
        pr_text = weakest_prereq_gap["unsatisfied_prerequisites"][0]
        rec_text = f"Your biggest current prerequisite gap is {pr_text}. Complete prerequisite fundamentals before attempting {weakest_prereq_gap['title']}."
    elif weakest_topic and weakest_topic["mastery"] < PREREQ_UNLOCK:
        rec_text = f"Focus on {weakest_topic['title']} ({round(weakest_topic['mastery'])}% mastery). Ask the AI Tutor for scaffolded practice."
    else:
        rec_text = "Keep up the momentum! You are progressing steadily through your outcome targets."

    # 9. Learning Path Output Items
    path_items_data = []
    for item in path_items_objs:
        t = db.query(Topic).filter(Topic.id == item.topic_id).first()
        m_obj = mastery_map.get(item.topic_id)
        m_val = m_obj.overall_mastery if m_obj else 0.0
        cls_name = classify_mastery(m_val)
        cos = [m.outcome.code for m in t.outcome_mappings] if t else []
        prereqs = [p.prerequisite_topic.title for p in t.prerequisites] if t else []

        path_items_data.append({
            "id": item.id,
            "sequence_order": item.sequence_order,
            "topic_id": item.topic_id,
            "topic_title": (item.remedial_title or (t.title if t else "Topic")),
            "topic_code": t.code if t else "",
            "difficulty": "Beginner" if item.is_remedial else (t.difficulty if t else "Beginner"),
            "est_minutes": item.topic.est_minutes if item.topic else 45,
            "mastery_percentage": m_val,
            "classification": cls_name,
            "status": item.status,
            "recommendation_reason": item.recommendation_reason,
            "related_outcomes": cos,
            "prerequisites": prereqs,
            "is_remedial": item.is_remedial,
            "action": get_action_for_topic(cls_name, item.status == "LOCKED")
        })

    # 10. Assessment History & Study Time Calculation
    attempts = db.query(AssessmentAttempt).filter(
        AssessmentAttempt.user_id == user_id,
        AssessmentAttempt.course_id == actual_course_id
    ).order_by(AssessmentAttempt.created_at.desc()).limit(10).all()

    # Sum estimated minutes of completed & developing modules + assessment activity
    completed_mins = sum(
        t["est_minutes"] for t in topic_mastery_list if t["mastery"] >= PREREQ_UNLOCK
    )
    attempts_mins = len(attempts) * 10
    total_study_mins = completed_mins + attempts_mins
    base_hours = 0.5 if profile.diagnostic_completed else 0.0
    study_hours = round(max(total_study_mins / 60.0, base_hours), 1)

    attempts_data = [
        {
            "id": a.id,
            "attempt_uuid": a.attempt_uuid,
            "attempt_type": a.attempt_type,
            "score": a.score,
            "max_score": a.max_score,
            "percentage": a.percentage,
            "passed": a.passed,
            "topic_id": a.topic_id,
            "created_at": a.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }
        for a in attempts
    ]

    # Latest diagnostic
    latest_diag = next((a for a in attempts if a.attempt_type == "diagnostic"), None)

    return {
        "studentProfile": {
            "id": profile.id,
            "user_id": profile.user_id,
            "full_name": user.full_name if user else "Student",
            "email": user.email if user else "",
            "student_id": profile.student_id or "S101",
            "program": profile.program or "B.Tech AI & Data Science",
            "semester": profile.semester or 4,
            "current_level": profile.current_level or "Beginner",
            "learning_goal": profile.learning_goal,
            "diagnostic_completed": profile.diagnostic_completed,
            "daily_time_minutes": profile.daily_time_minutes
        },
        "enrolledCourse": {
            "id": course.id if course else actual_course_id,
            "code": course.code if course else "CS201",
            "title": course.title if course else "Data Structures",
            "description": course.description if course else ""
        },
        "overallProgress": overall_progress,
        "overallMastery": overall_mastery,
        "overallOBEAttainment": overall_obe,
        "topicsMastered": f"{mastered_count} / {total_topics_count}",
        "masteredCount": mastered_count,
        "totalTopics": total_topics_count,
        "courseCompleted": is_course_completed,
        "studyTimeHours": study_hours,
        "currentTargetTopic": current_target,
        "aiRecommendation": rec_text,
        "topicMastery": topic_mastery_list,
        "courseOutcomeAttainment": co_list,
        "learningPath": {
            "id": path.id if path else None,
            "status": path.status if path else "ACTIVE",
            "adaptation_reason": path.adaptation_reason if path else "",
            "items": path_items_data
        },
        "assessmentResults": attempts_data,
        "latestDiagnostic": {
            "completed": profile.diagnostic_completed,
            "score": latest_diag.percentage if latest_diag else (overall_mastery if profile.diagnostic_completed else 0.0),
            "attempt_uuid": latest_diag.attempt_uuid if latest_diag else None
        }
    }
