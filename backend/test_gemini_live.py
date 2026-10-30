import sys
import os
import asyncio
from dotenv import load_dotenv

# Load backend/.env
backend_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(backend_dir, ".env")
load_dotenv(env_path, override=True)

sys.path.insert(0, backend_dir)
from ai_agents.gemini_service import gemini_tutor_service

async def run_live_verification():
    # 1. Check key configuration safely
    is_conf = gemini_tutor_service.is_configured()
    print(f"1. GEMINI_API_KEY loaded: {is_conf}")
    if not is_conf:
        print("ERROR: GEMINI_API_KEY is not set or empty in backend/.env")
        return False

    context = {
        "course_id": 1,
        "course_title": "Data Structures & Algorithms",
        "course_code": "CS201",
        "topic_id": 1,
        "topic_title": "Stack",
        "topic_code": "STACK-101",
        "learning_objective": "Understand LIFO stack operations push, pop, peek",
        "mastery_score": 32.0,
        "topic_classification": "WEAK",
        "learning_level": "Beginner",
        "outcomes": ["CO1: Implement fundamental linear data structures"],
        "prerequisites": ["Arrays", "Pointers"],
        "weak_sub_concepts": ["Stack Overflow vs Underflow", "LIFO reversal"],
        "path_status": "ACTIVE"
    }

    # Step 5: Ask "What is Stack?"
    print("\n--- Test Step 5: Ask 'What is Stack?' ---")
    res1 = await gemini_tutor_service.chat_with_tutor(
        context=context,
        user_message="What is Stack?",
        action=None
    )
    if res1.get("error"):
        print(f"Error encountered: {res1.get('error')}")
        return False
    print(f"Model used: {res1.get('model_used')}")
    print(f"Adapted level: {res1.get('adapted_for_level')}")
    reply1 = res1.get("reply", "")
    print(f"Response preview (first 250 chars):\n{reply1[:250].encode('ascii', errors='replace').decode('ascii')}...")

    # Step 7: Ask "Explain it with a simple real-world example."
    print("\n--- Test Step 7: Ask 'Explain it with a simple real-world example.' ---")
    history = [
        {"role": "user", "content": "What is Stack?"},
        {"role": "model", "content": reply1}
    ]
    res2 = await gemini_tutor_service.chat_with_tutor(
        context=context,
        user_message="Explain it with a simple real-world example.",
        action="give_example",
        history=history
    )
    if res2.get("error"):
        print(f"Error encountered: {res2.get('error')}")
        return False
    reply2 = res2.get("reply", "")
    print(f"Response preview (first 250 chars):\n{reply2[:250].encode('ascii', errors='replace').decode('ascii')}...")

    # Step 9: Ask "I don't understand. Explain it more simply."
    print("\n--- Test Step 9: Ask 'I don't understand. Explain it more simply.' ---")
    history.append({"role": "user", "content": "Explain it with a simple real-world example."})
    history.append({"role": "model", "content": reply2})
    res3 = await gemini_tutor_service.chat_with_tutor(
        context=context,
        user_message="I don't understand. Explain it more simply.",
        action="explain_again",
        history=history
    )
    if res3.get("error"):
        print(f"Error encountered: {res3.get('error')}")
        return False
    reply3 = res3.get("reply", "")
    print(f"Response preview (first 250 chars):\n{reply3[:250].encode('ascii', errors='replace').decode('ascii')}...")

    print("\nALL 3 CONVERSATIONAL GEMINI STEPS COMPLETED SUCCESSFULLY!")
    return True

if __name__ == "__main__":
    success = asyncio.run(run_live_verification())
    if not success:
        sys.exit(1)
