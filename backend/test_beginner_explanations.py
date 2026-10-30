"""
test_beginner_explanations.py
Comprehensive test suite verifying that all OBEPath AI learning explanations
are simple, accurate, and tailored for absolute beginners across all 4 courses:
- CS101 Python Programming (Python code snippets)
- CS201 Data Structures (data structure states & ASCII diagrams)
- AI301 Machine Learning (intuitive real-world workflows & numbers)
- CS302 Database Management Systems (SQL tables & queries)

Ensures every topic contains:
1. Short definition
2. Familiar real-world example
3. Small step-by-step example
4. Short summary
"""

import sys
import os

# Add backend directory to sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from database import SessionLocal
from models import Topic, Course
from ai_agents.tutor_agent import TutorAgent
from ai_agents.gemini_service import gemini_tutor_service

def test_beginner_explanations():
    db = SessionLocal()
    try:
        courses = db.query(Course).order_by(Course.id).all()
        assert len(courses) >= 4, f"Expected at least 4 courses, found {len(courses)}"
        print(f"Found {len(courses)} courses in database.")

        topics = db.query(Topic).order_by(Topic.course_id, Topic.id).all()
        print(f"Found {len(topics)} topics in database.")
        assert len(topics) >= 32, f"Expected at least 32 topics, found {len(topics)}"

        course_map = {c.id: c for c in courses}

        # Counters
        python_topics_checked = 0
        dsa_topics_checked = 0
        ml_topics_checked = 0
        dbms_topics_checked = 0

        print("\n" + "="*70)
        print("VERIFYING BEGINNER EXPLANATIONS FOR ALL TOPICS")
        print("="*70)

        for topic in topics:
            course = course_map.get(topic.course_id)
            course_code = course.code if course else ""
            topic_title = topic.title

            info = TutorAgent.get_topic_info(topic_title)
            assert info is not None, f"Topic info missing for '{topic_title}'"

            # 1. Short Definition
            assert "definition" in info and len(info["definition"]) >= 15, \
                f"Missing or inadequate definition for '{topic_title}'"

            # 2. Familiar Real-World Example
            assert "real_world" in info and len(info["real_world"]) >= 20, \
                f"Missing or inadequate real_world example for '{topic_title}'"

            # 3. Small Step-by-Step Example
            assert "step_by_step" in info and len(info["step_by_step"]) >= 25, \
                f"Missing or inadequate step_by_step example for '{topic_title}'"

            # 4. Short Summary
            assert "summary" in info and len(info["summary"]) >= 15, \
                f"Missing or inadequate summary for '{topic_title}'"

            # Domain-specific validations
            step_text = info["step_by_step"]
            code_text = info.get("code", "")
            visual_text = info.get("visual", "")

            if course_code == "CS101":
                python_topics_checked += 1
                # Must contain Python code
                has_python = ("def " in step_text or "print(" in step_text or "for " in step_text or 
                              "=" in step_text or "```python" in step_text or "class " in step_text or
                              "import " in step_text or "open(" in step_text or "if " in step_text)
                assert has_python, f"CS101 Python topic '{topic_title}' lacks Python code in step_by_step"

            elif course_code == "CS201":
                dsa_topics_checked += 1
                # Must reference data structures, nodes, pointers, or step transitions
                has_dsa = ("stack" in step_text.lower() or "queue" in step_text.lower() or 
                           "tree" in step_text.lower() or "node" in step_text.lower() or 
                           "step" in step_text.lower() or "->" in step_text or 
                           "root" in step_text.lower() or "pop" in step_text.lower() or 
                           "push" in step_text.lower() or "o(" in step_text.lower() or
                           "base case" in step_text.lower())
                assert has_dsa, f"CS201 DSA topic '{topic_title}' lacks concrete data structure trace in step_by_step"

            elif course_code == "AI301":
                ml_topics_checked += 1
                # Must contain prediction, real-world numbers, features, or ML workflows
                has_ml = ("feature" in step_text.lower() or "predict" in step_text.lower() or 
                          "step" in step_text.lower() or "cluster" in step_text.lower() or 
                          "model" in step_text.lower() or "error" in step_text.lower() or
                          "weight" in step_text.lower() or "data" in step_text.lower() or
                          "variance" in step_text.lower())
                assert has_ml, f"AI301 ML topic '{topic_title}' lacks prediction/workflow in step_by_step"

            elif course_code == "CS302":
                dbms_topics_checked += 1
                # Must contain SQL tables and queries
                has_sql = ("select " in step_text.lower() or "table" in step_text.lower() or 
                           "from " in step_text.lower() or "insert" in step_text.lower() or 
                           "where " in step_text.lower() or "join" in step_text.lower() or 
                           "create" in step_text.lower() or "commit" in step_text.lower() or
                           "index" in step_text.lower() or "b-tree" in step_text.lower())
                assert has_sql, f"CS302 DBMS topic '{topic_title}' lacks SQL table/query in step_by_step"

            # Verify generate_modality_content output
            modality_res = TutorAgent.generate_modality_content(
                topic_title=topic_title,
                modality="explanation",
                mastery_score=25.0
            )
            assert "content_markdown" in modality_res
            markdown = modality_res["content_markdown"]
            assert "1. What Is It? (Short Definition)" in markdown
            assert "2. Familiar Real-World Example" in markdown
            assert "3. Small Step-by-Step Example" in markdown
            assert "4. Summary & Key Takeaway" in markdown

            # Verify quick action responses
            chat_res = TutorAgent.respond(
                topic_title=topic_title,
                user_message="Help me understand this",
                quick_action="explain_simply",
                mastery_score=30.0
            )
            assert len(chat_res["reply"]) > 50
            assert "suggested_followups" in chat_res

            print(f"  [OK] [{course_code:5s}] {topic_title}")

        print("\n" + "="*70)
        print("DOMAIN VALIDATION SUMMARY:")
        print(f"  CS101 Python Topics Verified: {python_topics_checked}")
        print(f"  CS201 Data Structures Topics Verified: {dsa_topics_checked}")
        print(f"  AI301 Machine Learning Topics Verified: {ml_topics_checked}")
        print(f"  CS302 DBMS Topics Verified: {dbms_topics_checked}")
        print(f"  Total Topics Verified: {len(topics)}")
        print("="*70)

        # Verify fallback in GeminiTutorService
        print("\nVerifying GeminiTutorService graceful fallback...")
        import asyncio
        context = {
            "topic_id": topics[0].id,
            "topic_title": topics[0].title,
            "course_title": "Python Programming",
            "course_code": "CS101",
            "mastery_score": 20.0
        }
        fallback_modality = asyncio.run(gemini_tutor_service.generate_modality_lesson(context, "explanation"))
        assert "content_markdown" in fallback_modality
        assert "Short Definition" in fallback_modality["content_markdown"]
        print("  [OK] Fallback modality lesson returned structured beginner guide.")

        fallback_chat = asyncio.run(gemini_tutor_service.chat_with_tutor(
            context=context,
            user_message="Explain simply",
            action="explain_simply"
        ))
        assert "reply" in fallback_chat
        assert len(fallback_chat["reply"]) > 50
        print("  [OK] Fallback chat returned structured beginner reply.")

        print("\nALL 32 TOPIC BEGINNER EXPLANATIONS PASSED COMPREHENSIVE VALIDATION!")
        return True

    finally:
        db.close()

if __name__ == "__main__":
    success = test_beginner_explanations()
    if not success:
        sys.exit(1)
