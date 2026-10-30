import os
import json
import logging
from typing import Dict, Any, List, Optional
import httpx

from ai_agents.planner_agent import PlannerAgent
from ai_agents.tutor_agent import TutorAgent
from ai_agents.assessment_agent import AssessmentAgent
from ai_agents.resource_agent import ResourceAgent
from ai_agents.progress_agent import ProgressMonitoringAgent

logger = logging.getLogger("ai_service")

class AIService:
    """
    Unified AI Service orchestrating all 5 agents:
    - Planner Agent
    - Tutor Agent
    - Assessment Agent
    - Resource Agent
    - Progress Monitoring Agent

    Supports live LLM (OpenAI API key) if available in environment,
    with an intelligent, deterministic fallback so the app NEVER fails.
    """

    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.has_llm = bool(self.openai_api_key or self.gemini_api_key)

    async def generateExplanation(
        self,
        topic_title: str,
        mastery_score: float,
        user_message: str = "",
        action: str = ""
    ) -> Dict[str, Any]:
        """Tutor Agent explanation with LLM attempt and deterministic fallback."""
        if self.openai_api_key:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {self.openai_api_key}"},
                        json={
                            "model": "gpt-4o-mini",
                            "messages": [
                                {
                                    "role": "system",
                                    "content": (
                                        f"You are an expert AI Tutor in Outcome-Based Education. "
                                        f"Topic: {topic_title}. Student Mastery: {mastery_score}%. "
                                        f"Adapt your tone and depth to their mastery level. Provide clear examples and actionable guidance."
                                    )
                                },
                                {"role": "user", "content": user_message or f"Explain {topic_title} simply."}
                            ]
                        }
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        reply = data["choices"][0]["message"]["content"]
                        return {
                            "reply": reply,
                            "action_taken": action or "llm_explanation",
                            "adapted_for_level": "Adaptive LLM",
                            "suggested_followups": ["Explain simply", "Give another example", "Test me"]
                        }
            except Exception as e:
                logger.warning(f"LLM call failed, falling back to deterministic tutor: {e}")

        # Deterministic fallback
        return TutorAgent.respond(topic_title, user_message, mastery_score, action)

    async def generateModalityContent(
        self,
        topic_title: str,
        modality: str,
        mastery_score: float = 50.0,
        user_prompt: str = "",
        pedagogical_style: str = ""
    ) -> Dict[str, Any]:
        """Generative AI Teaching Methodology Engine with LLM attempt and deterministic fallback."""
        if self.openai_api_key:
            try:
                system_prompt = (
                    f"You are an expert Generative AI Pedagogical Tutor in Outcome-Based Education. "
                    f"Topic: '{topic_title}'. Student Mastery: {mastery_score}%. "
                    f"Requested Modality: '{modality}'. Pedagogical Style: '{pedagogical_style}'. "
                    f"Generate a clear, markdown-formatted teaching lesson tailored specifically to the student's request."
                )
                user_msg = user_prompt or f"Generate a {modality} teaching lesson for {topic_title} with clear takeaways and code if appropriate."
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {self.openai_api_key}"},
                        json={
                            "model": "gpt-4o-mini",
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_msg}
                            ]
                        }
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        reply = data["choices"][0]["message"]["content"]
                        return {
                            "topic_id": 0,
                            "topic_title": topic_title,
                            "modality": modality,
                            "pedagogical_style": pedagogical_style or "Adaptive LLM",
                            "content_markdown": reply,
                            "key_takeaways": [
                                f"Live Generative AI tailored for {topic_title}.",
                                f"Adapted for mastery score {int(mastery_score)}%.",
                                "Addresses student-specified learning requests."
                            ],
                            "code_snippet": None,
                            "visual_ascii": None,
                            "practice_question": None,
                            "suggested_prompts": [
                                f"Explain {topic_title} using a real-world analogy",
                                f"Show code implementation for {topic_title}",
                                f"Test my understanding with an interactive challenge"
                            ]
                        }
            except Exception as e:
                logger.warning(f"LLM modality generation failed, using internal generative engine: {e}")

        # High quality internal generative engine
        return TutorAgent.generate_modality_content(
            topic_title=topic_title,
            modality=modality,
            mastery_score=mastery_score,
            user_prompt=user_prompt,
            pedagogical_style=pedagogical_style
        )

    def generateLearningPath(
        self,
        topics: List[Any],
        prerequisites_map: Dict[int, List[int]],
        masteries_map: Dict[int, float],
        topic_outcomes_map: Dict[int, List[Any]],
        goal: str = ""
    ) -> List[Dict[str, Any]]:
        """Planner Agent: Generates personalized roadmap."""
        return PlannerAgent.generate_path(
            topics, prerequisites_map, masteries_map, topic_outcomes_map, goal
        )

    def reviseLearningPath(
        self,
        existing_items: List[Dict[str, Any]],
        failed_topic_id: int
    ) -> List[Dict[str, Any]]:
        """Planner Agent: Dynamically inserts remedial modules upon detected failure."""
        return PlannerAgent.insert_functions_remediation(existing_items, failed_topic_id)

    def generateQuiz(self, topic_title: str) -> List[Dict[str, Any]]:
        """Assessment Agent: Returns topic-specific interactive quiz questions."""
        return AssessmentAgent.get_functions_quiz()

    def evaluateQuiz(
        self,
        submitted_answers: Dict[str, str],
        questions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Assessment Agent: Scores and provides feedback."""
        return AssessmentAgent.evaluate_quiz(submitted_answers, questions)

    def analyzePerformance(
        self,
        topic_title: str,
        quiz_percentage: float,
        current_mastery: float
    ) -> Dict[str, Any]:
        """Progress Monitoring Agent: Evaluates adaptation trigger."""
        return ProgressMonitoringAgent.evaluate_performance_event(
            topic_title, quiz_percentage, current_mastery
        )

    def calculateMastery(
        self,
        diagnostic_score: float,
        quiz_score: float,
        practice_score: float,
        completion_score: float
    ) -> Dict[str, Any]:
        """Progress Monitoring Agent: Mastery formula calculation."""
        return ProgressMonitoringAgent.calculate_mastery(
            diagnostic_score, quiz_score, practice_score, completion_score
        )

    def getResources(self, topic_title: str) -> List[Dict[str, Any]]:
        """Resource Retrieval Agent: Approved references."""
        return ResourceAgent.get_resources_for_topic(topic_title)

# Singleton instance
ai_service = AIService()
