import os
import sys
import json
import argparse
from typing import Optional

# Ensure backend root is on sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from database import SessionLocal, create_app_engine, normalize_database_url, Base
from sqlalchemy.orm import Session, sessionmaker
from models import (
    Course,
    CourseOutcome,
    Topic,
    TopicPrerequisite,
    TopicOutcomeMapping,
    QuestionBank,
    DiagnosticQuestion,
    Resource
)

DATA_FILE = os.path.join(SCRIPT_DIR, "data", "curriculum_clean.json")

def seed_curriculum(db: Optional[Session] = None, database_url: Optional[str] = None) -> dict:
    """
    Seeds ONLY the 4 core OBE courses, course outcomes, topics, prerequisites,
    topic-outcome mappings, curriculum resources, diagnostic questions, and the question bank.
    
    Contains NO users, classes, enrollments, attempts, histories, or agent logs.
    Strictly idempotent: safe to execute multiple times against any supported DB.
    """
    close_at_end = False
    if db is None:
        target_url = database_url or os.getenv("DATABASE_URL")
        if target_url:
            eng = create_app_engine(normalize_database_url(target_url))
            Base.metadata.create_all(bind=eng)
            CustomSession = sessionmaker(autocommit=False, autoflush=False, bind=eng)
            db = CustomSession()
        else:
            db = SessionLocal()
        close_at_end = True

    counts = {
        "courses_created": 0,
        "courses_existing": 0,
        "outcomes_created": 0,
        "outcomes_existing": 0,
        "topics_created": 0,
        "topics_existing": 0,
        "prerequisites_created": 0,
        "prerequisites_existing": 0,
        "mappings_created": 0,
        "mappings_existing": 0,
        "resources_created": 0,
        "resources_existing": 0,
        "diagnostic_questions_created": 0,
        "diagnostic_questions_existing": 0,
        "questions_created": 0,
        "questions_existing": 0,
    }

    if not os.path.exists(DATA_FILE):
        raise FileNotFoundError(f"Curriculum data file not found at: {DATA_FILE}")

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        courses_data = json.load(f)

    # Index by course code for predictable processing
    courses_by_code = {c["code"]: c for c in courses_data}
    ordered_course_codes = ["CS101", "CS201", "AI301", "CS302"]

    try:
        course_objs = {}
        # 1. Seed Courses in exact order: CS101 (id=1), CS201 (id=2), AI301 (id=3), CS302 (id=4)
        for code in ordered_course_codes:
            if code not in courses_by_code:
                continue
            cdata = courses_by_code[code]
            course = db.query(Course).filter(Course.code == code).first()
            if not course:
                course = Course(
                    code=cdata["code"],
                    title=cdata["title"],
                    description=cdata["description"],
                    category=cdata["category"],
                    level=cdata["level"],
                    is_active=cdata["is_active"]
                )
                db.add(course)
                db.flush()
                counts["courses_created"] += 1
            else:
                course.title = cdata["title"]
                course.description = cdata["description"]
                course.category = cdata["category"]
                course.level = cdata["level"]
                course.is_active = cdata["is_active"]
                counts["courses_existing"] += 1
            course_objs[code] = course

        # 2. Seed Course Outcomes for each course
        outcome_maps = {} # course_code -> {outcome_code: CourseOutcome}
        for code in ordered_course_codes:
            if code not in courses_by_code:
                continue
            cdata = courses_by_code[code]
            course = course_objs[code]
            outcome_map = {}
            for odata in cdata.get("outcomes", []):
                outcome = db.query(CourseOutcome).filter(
                    CourseOutcome.course_id == course.id,
                    CourseOutcome.code == odata["code"]
                ).first()
                if not outcome:
                    outcome = CourseOutcome(
                        course_id=course.id,
                        code=odata["code"],
                        description=odata["description"],
                        target_attainment_pct=odata.get("target_attainment_pct", 70.0)
                    )
                    db.add(outcome)
                    db.flush()
                    counts["outcomes_created"] += 1
                else:
                    outcome.description = odata["description"]
                    outcome.target_attainment_pct = odata.get("target_attainment_pct", 70.0)
                    counts["outcomes_existing"] += 1
                outcome_map[odata["code"]] = outcome
            outcome_maps[code] = outcome_map

        # 3. Seed Topics in canonical order: CS201 (1..8), CS101 (9..16), AI301 (17..24), CS302 (25..32)
        # This preserves strict ID backwards-compatibility across existing test assertions and workflows.
        topic_order = ["CS201", "CS101", "AI301", "CS302"]
        topic_maps = {} # course_code -> {topic_code: Topic}
        for code in topic_order:
            if code not in courses_by_code:
                continue
            cdata = courses_by_code[code]
            course = course_objs[code]
            topic_map = {}
            for tdata in cdata.get("topics", []):
                topic = db.query(Topic).filter(
                    Topic.course_id == course.id,
                    Topic.code == tdata["code"]
                ).first()
                if not topic:
                    topic = Topic(
                        course_id=course.id,
                        code=tdata["code"],
                        title=tdata["title"],
                        order_index=tdata["order_index"],
                        description=tdata["description"],
                        learning_objective=tdata["learning_objective"],
                        difficulty=tdata["difficulty"],
                        est_minutes=tdata.get("est_minutes", 45)
                    )
                    db.add(topic)
                    db.flush()
                    counts["topics_created"] += 1
                else:
                    topic.title = tdata["title"]
                    topic.order_index = tdata["order_index"]
                    topic.description = tdata["description"]
                    topic.learning_objective = tdata["learning_objective"]
                    topic.difficulty = tdata["difficulty"]
                    topic.est_minutes = tdata.get("est_minutes", 45)
                    counts["topics_existing"] += 1
                topic_map[tdata["code"]] = topic
            topic_maps[code] = topic_map

        # 4. Prerequisites
        for code in ordered_course_codes:
            if code not in courses_by_code:
                continue
            cdata = courses_by_code[code]
            t_map = topic_maps[code]
            for pdata in cdata.get("prerequisites", []):
                topic = t_map.get(pdata["topic_code"])
                prereq_topic = t_map.get(pdata["prereq_topic_code"])
                if not topic or not prereq_topic:
                    continue
                prereq = db.query(TopicPrerequisite).filter(
                    TopicPrerequisite.topic_id == topic.id,
                    TopicPrerequisite.prerequisite_topic_id == prereq_topic.id
                ).first()
                if not prereq:
                    prereq = TopicPrerequisite(
                        topic_id=topic.id,
                        prerequisite_topic_id=prereq_topic.id,
                        required_mastery_pct=pdata.get("required_mastery_pct", 60.0)
                    )
                    db.add(prereq)
                    db.flush()
                    counts["prerequisites_created"] += 1
                else:
                    counts["prerequisites_existing"] += 1

        # 5. Topic Outcome Mappings
        for code in ordered_course_codes:
            if code not in courses_by_code:
                continue
            cdata = courses_by_code[code]
            t_map = topic_maps[code]
            o_map = outcome_maps[code]
            for mdata in cdata.get("mappings", []):
                topic = t_map.get(mdata["topic_code"])
                outcome = o_map.get(mdata["outcome_code"])
                if not topic or not outcome:
                    continue
                mapping = db.query(TopicOutcomeMapping).filter(
                    TopicOutcomeMapping.topic_id == topic.id,
                    TopicOutcomeMapping.outcome_id == outcome.id
                ).first()
                if not mapping:
                    mapping = TopicOutcomeMapping(
                        topic_id=topic.id,
                        outcome_id=outcome.id,
                        weight=mdata.get("weight", 1.0)
                    )
                    db.add(mapping)
                    db.flush()
                    counts["mappings_created"] += 1
                else:
                    counts["mappings_existing"] += 1

        # 6. Resources
        for code in ordered_course_codes:
            if code not in courses_by_code:
                continue
            cdata = courses_by_code[code]
            t_map = topic_maps[code]
            for rdata in cdata.get("resources", []):
                topic = t_map.get(rdata["topic_code"])
                if not topic:
                    continue
                res = db.query(Resource).filter(
                    Resource.topic_id == topic.id,
                    Resource.title == rdata["title"]
                ).first()
                if not res:
                    res = Resource(
                        topic_id=topic.id,
                        title=rdata["title"],
                        url=rdata["url"],
                        resource_type=rdata.get("resource_type", "Documentation"),
                        approved_by_faculty=rdata.get("approved_by_faculty", True),
                        website_name=rdata.get("website_name"),
                        description=rdata.get("description"),
                        difficulty=rdata.get("difficulty", "Beginner")
                    )
                    db.add(res)
                    db.flush()
                    counts["resources_created"] += 1
                else:
                    counts["resources_existing"] += 1

        # 7. Diagnostic Questions
        for code in ordered_course_codes:
            if code not in courses_by_code:
                continue
            cdata = courses_by_code[code]
            course = course_objs[code]
            t_map = topic_maps[code]
            for dqdata in cdata.get("diagnostic_questions", []):
                topic = t_map.get(dqdata["topic_code"])
                if not topic:
                    continue
                dq = db.query(DiagnosticQuestion).filter(
                    DiagnosticQuestion.course_id == course.id,
                    DiagnosticQuestion.topic_id == topic.id,
                    DiagnosticQuestion.question_text == dqdata["question_text"]
                ).first()
                if not dq:
                    dq = DiagnosticQuestion(
                        course_id=course.id,
                        topic_id=topic.id,
                        question_text=dqdata["question_text"],
                        code_snippet=dqdata.get("code_snippet"),
                        question_type=dqdata.get("question_type", "mcq"),
                        sub_concept=dqdata.get("sub_concept"),
                        options_json=dqdata["options_json"],
                        correct_answer=dqdata["correct_answer"],
                        explanation=dqdata.get("explanation")
                    )
                    db.add(dq)
                    db.flush()
                    counts["diagnostic_questions_created"] += 1
                else:
                    counts["diagnostic_questions_existing"] += 1

        # 8. Question Bank
        for code in ordered_course_codes:
            if code not in courses_by_code:
                continue
            cdata = courses_by_code[code]
            course = course_objs[code]
            t_map = topic_maps[code]
            o_map = outcome_maps[code]
            for qdata in cdata.get("questions", []):
                topic = t_map.get(qdata.get("topic_code"))
                if not topic:
                    continue
                outcome = o_map.get(qdata.get("outcome_code"))
                outcome_id = outcome.id if outcome else None

                q = db.query(QuestionBank).filter(
                    QuestionBank.course_id == course.id,
                    QuestionBank.topic_id == topic.id,
                    QuestionBank.question_text == qdata["question_text"]
                ).first()
                if not q:
                    q = QuestionBank(
                        course_id=course.id,
                        topic_id=topic.id,
                        outcome_id=outcome_id,
                        sub_concept=qdata.get("sub_concept"),
                        difficulty=qdata.get("difficulty", "Beginner"),
                        question_type=qdata.get("question_type", "mcq"),
                        question_text=qdata["question_text"],
                        code_snippet=qdata.get("code_snippet"),
                        options_json=qdata["options_json"],
                        correct_answer=qdata["correct_answer"],
                        explanation=qdata["explanation"],
                        bloom_level=qdata.get("bloom_level", "Understand")
                    )
                    db.add(q)
                    db.flush()
                    counts["questions_created"] += 1
                else:
                    counts["questions_existing"] += 1

        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        if close_at_end:
            db.close()

    return counts

def main():
    parser = argparse.ArgumentParser(description="Clean Curriculum Seed for OBEPath Production")
    parser.add_argument("--database-url", type=str, default=None, help="Optional database URL override")
    args = parser.parse_args()

    if args.database_url:
        os.environ["DATABASE_URL"] = args.database_url

    print("=================================================================")
    print("OBEPath Production Curriculum Seeder")
    print("=================================================================")
    print(f"Loading data from: {DATA_FILE}")

    counts = seed_curriculum(database_url=args.database_url)

    print("\n[Curriculum Seeding Summary Report]")
    print(f"  Courses:              {counts['courses_created']} created, {counts['courses_existing']} already existed")
    print(f"  Outcomes:             {counts['outcomes_created']} created, {counts['outcomes_existing']} already existed")
    print(f"  Topics:               {counts['topics_created']} created, {counts['topics_existing']} already existed")
    print(f"  Prerequisites:        {counts['prerequisites_created']} created, {counts['prerequisites_existing']} already existed")
    print(f"  Mappings:             {counts['mappings_created']} created, {counts['mappings_existing']} already existed")
    print(f"  Resources:            {counts['resources_created']} created, {counts['resources_existing']} already existed")
    print(f"  Diagnostic Questions: {counts['diagnostic_questions_created']} created, {counts['diagnostic_questions_existing']} already existed")
    print(f"  Question Bank:        {counts['questions_created']} created, {counts['questions_existing']} already existed")
    print("=================================================================")
    print("Curriculum seed completed successfully (idempotent, 0 user/class records created).")

if __name__ == "__main__":
    main()
