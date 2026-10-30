import sys
import os
import asyncio

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pytest
from ai_agents.gemini_service import gemini_tutor_service

@pytest.mark.asyncio
async def test_without_key():
    print("Testing Gemini Tutor Service when GEMINI_API_KEY is unset...")
    res = await gemini_tutor_service.chat_with_tutor(
        context={
            "course_title": "Data Structures",
            "course_code": "CS201",
            "topic_title": "Stack",
            "topic_code": "TOPIC-1",
            "mastery_score": 32.0,
            "topic_classification": "WEAK",
            "learning_level": "Beginner"
        },
        user_message="What is stack?",
        action=None
    )
    print("Status of configured:", gemini_tutor_service.is_configured())
    print("Reply preview:", res.get("reply")[:120].encode('ascii', errors='replace').decode('ascii'))
    print("Action taken:", res.get("action_taken"))
    print("Error:", res.get("error"))
    if not gemini_tutor_service.is_configured():
        assert res.get("error") == "GEMINI_API_KEY is not configured", "Expected missing key error"
        print("SUCCESS: Handled missing key gracefully with clear user guidance!")
    else:
        assert res.get("reply") is not None
        assert res.get("action_taken") in ("gemini_tutor_explanation", "beginner_tutor_explanation") or "fallback" in res.get("model_used", "")
        print("SUCCESS: Gemini tutor answered successfully with active API key or fallback!")

if __name__ == "__main__":
    asyncio.run(test_without_key())
