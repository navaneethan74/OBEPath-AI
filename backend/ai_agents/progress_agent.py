from typing import Dict, Any, List
from models import MasteryScore, AgentLog
from core.thresholds import PREREQ_UNLOCK, TOPIC_MASTERY

class ProgressMonitoringAgent:
    """
    Progress Monitoring Agent:
    Tracks student completion, quiz attempts, practice accuracy, and study time.
    Calculates mastery using transparent OBE formula.
    Detects low mastery, stagnation, or acceleration, and triggers path adaptations.
    """

    @staticmethod
    def calculate_mastery(
        diagnostic_score: float,
        quiz_score: float,
        practice_score: float,
        completion_score: float
    ) -> Dict[str, Any]:
        """
        Mastery Formula:
        mastery = 40% diagnostic + 30% latest quiz + 20% practice + 10% completion
        """
        score = (0.40 * diagnostic_score) + (0.30 * quiz_score) + (0.20 * practice_score) + (0.10 * completion_score)
        score = round(min(max(score, 0.0), 100.0), 1)

        if score < 40.0:
            classification = "Needs Improvement"
        elif score < PREREQ_UNLOCK:
            classification = "Developing"
        elif score < TOPIC_MASTERY:
            classification = "Proficient"
        else:
            classification = "Mastered"

        return {
            "overall_mastery": score,
            "classification": classification,
            "formula_breakdown": {
                "diagnostic_component": round(0.40 * diagnostic_score, 1),
                "quiz_component": round(0.30 * quiz_score, 1),
                "practice_component": round(0.20 * practice_score, 1),
                "completion_component": round(0.10 * completion_score, 1)
            }
        }

    @staticmethod
    def evaluate_performance_event(
        topic_title: str,
        quiz_percentage: float,
        current_mastery: float
    ) -> Dict[str, Any]:
        """
        Detects whether an adaptation trigger should fire:
        - Low score (<= 50%) -> 'REMEDIAL_INSERTION'
        - High score (>= 85%) -> 'ACCELERATION'
        - Normal progression (51% - 84%) -> 'CONTINUE'
        """
        if quiz_percentage <= 50.0:
            return {
                "trigger": "REMEDIAL_INSERTION",
                "severity": "HIGH",
                "message": f"Progress Agent detected low score ({int(quiz_percentage)}%) in {topic_title}. Prerequisite stability compromised. Adaptive remedial path activated.",
                "action": "insert_remedial_sequence"
            }
        elif quiz_percentage >= 85.0:
            return {
                "trigger": "ACCELERATION",
                "severity": "POSITIVE",
                "message": f"Progress Agent detected superior mastery ({int(quiz_percentage)}%) in {topic_title}. Fast-tracking course path.",
                "action": "accelerate_path"
            }
        else:
            return {
                "trigger": "CONTINUE",
                "severity": "NORMAL",
                "message": f"Progress Agent verified steady performance ({int(quiz_percentage)}%) in {topic_title}. Continuing planned sequence.",
                "action": "advance_next"
            }
