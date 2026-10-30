from typing import List, Dict, Any
from models import Topic, TopicPrerequisite, MasteryScore, CourseOutcome
from core.thresholds import PREREQ_UNLOCK, TOPIC_MASTERY

class PlannerAgent:
    """
    Planner Agent:
    Analyzes Course Outcomes, Topic Prerequisites, Learner Profile, Diagnostic Results,
    Topic Mastery, and Knowledge Gaps to generate and adapt an ordered personalized learning path.
    """

    @staticmethod
    def generate_path(
        topics: List[Topic],
        prerequisites_map: Dict[int, List[int]],
        masteries_map: Dict[int, float],
        topic_outcomes_map: Dict[int, List[CourseOutcome]],
        goal: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Determines the optimal pedagogical sequence and topic statuses:
        COMPLETED, CURRENT, RECOMMENDED, NEEDS REVISION, LOCKED
        """
        path_items = []
        # Sort topics primarily by prerequisites & order_index
        # We check mastery thresholds:
        # >= 80%: COMPLETED
        # 60 - 79%: Proficient (could be COMPLETED or RECOMMENDED)
        # 40 - 59%: NEEDS REVISION / CURRENT
        # < 40%: NEEDS REVISION or RECOMMENDED for foundational work
        
        current_assigned = False
        seq_order = 1

        for topic in sorted(topics, key=lambda t: t.order_index):
            mastery = masteries_map.get(topic.id, 0.0)
            prereqs = prerequisites_map.get(topic.id, [])
            
            # Check if all prerequisites have sufficient mastery (>= PREREQ_UNLOCK)
            prereqs_met = True
            unmet_prereqs = []
            for prereq_id in prereqs:
                p_mastery = masteries_map.get(prereq_id, 0.0)
                if p_mastery < PREREQ_UNLOCK:
                    prereqs_met = False
                    # Find topic title
                    p_topic = next((t for t in topics if t.id == prereq_id), None)
                    unmet_prereqs.append(p_topic.title if p_topic else f"Topic #{prereq_id}")

            cos = topic_outcomes_map.get(topic.id, [])
            co_codes = [co.code for co in cos]

            if mastery >= TOPIC_MASTERY:
                status = "COMPLETED"
                reason = f"Demonstrated high mastery ({int(mastery)}%). Aligns with {', '.join(co_codes) if co_codes else 'Course Outcomes'}."
            elif not prereqs_met:
                status = "LOCKED"
                reason = f"Prerequisite requirement not satisfied: Requires {', '.join(unmet_prereqs)} with >= 60% mastery before advancing."
            elif mastery < 40.0:
                if not current_assigned:
                    status = "CURRENT"
                    current_assigned = True
                    reason = f"Low diagnostic/quiz mastery ({int(mastery)}%). Target focus for immediate remediation to unlock dependent topics."
                else:
                    status = "NEEDS REVISION"
                    reason = f"Diagnostic score indicates foundational gaps ({int(mastery)}%). Scheduled for targeted revision."
            elif 40.0 <= mastery < 70.0:
                if not current_assigned:
                    status = "CURRENT"
                    current_assigned = True
                    reason = f"Developing mastery ({int(mastery)}%). Reinforce concepts and complete assessment to achieve Course Outcome mastery."
                else:
                    status = "RECOMMENDED"
                    reason = f"Prerequisites cleared. Ready for concept progression and practice (Current mastery: {int(mastery)}%)."
            else: # 70 - 79
                status = "COMPLETED"
                reason = f"Solid competency achieved ({int(mastery)}%). Prerequisites satisfied for subsequent modules."

            path_items.append({
                "sequence_order": seq_order,
                "topic_id": topic.id,
                "topic_title": topic.title,
                "topic_code": topic.code,
                "difficulty": topic.difficulty,
                "est_minutes": topic.est_minutes,
                "status": status,
                "recommendation_reason": reason,
                "related_outcomes": co_codes,
                "prerequisites": unmet_prereqs,
                "mastery_percentage": mastery,
                "is_remedial": False
            })
            seq_order += 1

        # If no topic got CURRENT (all completed or locked), make first non-completed current
        if not current_assigned:
            for item in path_items:
                if item["status"] in ["RECOMMENDED", "NEEDS REVISION"]:
                    item["status"] = "CURRENT"
                    break

        return path_items

    @staticmethod
    def insert_functions_remediation(existing_items: List[Dict[str, Any]], functions_topic_id: int) -> List[Dict[str, Any]]:
        """
        Inserts the 6 pedagogical remedial modules when the Progress Agent detects failure in Functions.
        1. Function Basics Revision
        2. Simple Function Examples
        3. Function Practice
        4. Parameters Practice
        5. Return Values
        6. Functions Reassessment
        """
        remedial_steps = [
            {
                "title": "Function Basics Revision",
                "desc": "Foundational syntax recap: 'def' keyword, naming conventions, indentation, and structure of callable code blocks.",
                "est_min": 15,
                "diff": "Beginner"
            },
            {
                "title": "Simple Function Examples",
                "desc": "Guided walkthroughs of zero-argument and single-argument functions with visual execution traces.",
                "est_min": 20,
                "diff": "Beginner"
            },
            {
                "title": "Function Practice",
                "desc": "Hands-on coding exercises building basic mathematical and text helper functions.",
                "est_min": 25,
                "diff": "Beginner"
            },
            {
                "title": "Parameters Practice",
                "desc": "Deep dive into positional arguments, default arguments, and keyword parameters with error prevention.",
                "est_min": 25,
                "diff": "Intermediate"
            },
            {
                "title": "Return Values & Scope",
                "desc": "Contrasting 'return' vs 'print', variable scope (local vs global), and handling multiple return values.",
                "est_min": 25,
                "diff": "Intermediate"
            },
            {
                "title": "Functions Reassessment",
                "desc": "Comprehensive evaluation to verify mastery threshold (>= 60%) before unlocking Lists & Tuples.",
                "est_min": 20,
                "diff": "Intermediate"
            }
        ]

        new_items = []
        seq = 1
        for item in existing_items:
            if item["topic_id"] == functions_topic_id:
                # Mark main function topic as NEEDS REVISION
                item["status"] = "NEEDS REVISION"
                item["sequence_order"] = seq
                item["recommendation_reason"] = "Diagnostic/Quiz analysis detected critical misconceptions. Remedial learning sequence activated."
                new_items.append(item)
                seq += 1

                # Insert the 6 remedial modules
                for i, r in enumerate(remedial_steps):
                    new_items.append({
                        "sequence_order": seq,
                        "topic_id": functions_topic_id,
                        "topic_title": f"Remediation: {r['title']}",
                        "topic_code": f"REM-FN-{i+1}",
                        "difficulty": r["diff"],
                        "est_minutes": r["est_min"],
                        "status": "CURRENT" if i == 0 else "RECOMMENDED",
                        "recommendation_reason": f"Remedial step {i+1}/6: {r['desc']}",
                        "related_outcomes": ["CO3"],
                        "prerequisites": [],
                        "mastery_percentage": item["mastery_percentage"],
                        "is_remedial": True,
                        "remedial_title": r["title"],
                        "remedial_description": r["desc"]
                    })
                    seq += 1
            else:
                # Other topics after functions stay LOCKED
                if item["sequence_order"] > 5 and not item["is_remedial"]:
                    item["status"] = "LOCKED"
                    item["recommendation_reason"] = "Locked until Functions remediation is completed and Course Outcome CO3 competency is reached."
                item["sequence_order"] = seq
                new_items.append(item)
                seq += 1

        return new_items

    @staticmethod
    def repair_data_structures_path(
        topics: List[Topic],
        recursion_topic_id: int,
        recursive_practice_id: int,
        tree_traversal_id: int,
        tree_problems_id: int
    ) -> List[Dict[str, Any]]:
        """
        Step 11 — Learning Path Repair ⭐:
        The student failed Tree Traversal because Recursion is weak.
        The system does not restart the whole Data Structures course.
        Instead, it repairs the existing path:
        Original:
            Tree Traversal
            ↓
            Tree Problems
        Becomes (Repaired Path):
            Recursion
            ↓
            Recursive Practice
            ↓
            Tree Traversal
            ↓
            Tree Problems
        The missing prerequisite is inserted into the path.
        That is why we call it: Prerequisite-aware learning path repair.
        """
        topic_map = {t.id: t for t in topics}

        repaired_steps = [
            {
                "topic_id": recursion_topic_id,
                "status": "CURRENT",
                "is_remedial": True,
                "remedial_title": "Targeted Prerequisite: Recursion Fundamentals",
                "remedial_description": "Remedial Module: Simple explanation, analogies, call-stack trace, and base condition mastery to repair prerequisite deficit.",
                "reason": "Prerequisite Repair: Injected to bridge verified misconception before retrying Tree Traversal (Course Outcome CO1/CO2)."
            },
            {
                "topic_id": recursive_practice_id,
                "status": "RECOMMENDED",
                "is_remedial": True,
                "remedial_title": "Remedial Practice: Recursive Function Tracing",
                "remedial_description": "Guided practice exercises tracing recursive tree calls and state accumulation.",
                "reason": "Prerequisite Practice: Hands-on call stack walkthroughs to reinforce recursion mastery."
            },
            {
                "topic_id": tree_traversal_id,
                "status": "LOCKED",
                "is_remedial": False,
                "remedial_title": None,
                "remedial_description": None,
                "reason": "Locked temporarily until Recursion prerequisite reaches >= 60% competency threshold."
            },
            {
                "topic_id": tree_problems_id,
                "status": "LOCKED",
                "is_remedial": False,
                "remedial_title": None,
                "remedial_description": None,
                "reason": "Dependent algorithmic applications scheduled after successful Tree Traversal attainment."
            }
        ]

        items = []
        for i, step in enumerate(repaired_steps, start=1):
            t = topic_map.get(step["topic_id"])
            items.append({
                "sequence_order": i,
                "topic_id": step["topic_id"],
                "topic_title": step["remedial_title"] or (t.title if t else "Topic"),
                "topic_code": f"REPAIR-{i}" if step["is_remedial"] else (t.code if t else f"TOPIC-{i}"),
                "difficulty": t.difficulty if t else "Intermediate",
                "est_minutes": 25 if step["is_remedial"] else (t.est_minutes if t else 45),
                "status": step["status"],
                "recommendation_reason": step["reason"],
                "related_outcomes": ["CO1", "CO2"],
                "prerequisites": ["Recursion Fundamentals"] if step["topic_id"] == tree_traversal_id else [],
                "mastery_percentage": 30.0 if step["topic_id"] in [recursion_topic_id, tree_traversal_id] else 0.0,
                "is_remedial": step["is_remedial"],
                "remedial_title": step["remedial_title"],
                "remedial_description": step["remedial_description"]
            })

        return items
