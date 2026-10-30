import json
import hashlib
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import engine, SessionLocal, Base
from models import (
    User, StudentProfile, Course, CourseOutcome, Topic,
    TopicPrerequisite, TopicOutcomeMapping, Resource, DiagnosticQuestion,
    MasteryScore, LearningPath, LearningPathItem, AgentLog, OutcomeAttainment
)
from ai_agents.planner_agent import PlannerAgent
from ai_agents.progress_agent import ProgressMonitoringAgent

from core.security import hash_password

def seed_users(db: SessionLocal = None):
    """
    Seeds student@obe.edu, faculty@obe.edu, and admin@obe.edu ONLY when ENV=development
    and passwords come from environment variables (STUDENT_PASSWORD, FACULTY_PASSWORD, ADMIN_PASSWORD).
    If ENV=production, or any env password is missing, no demo users are seeded and no default
    password is used.
    """
    env_val = os.getenv("ENV", os.getenv("ENVIRONMENT", "development")).strip().lower()
    is_development = (env_val == "development")

    student_pw = os.getenv("STUDENT_PASSWORD")
    faculty_pw = os.getenv("FACULTY_PASSWORD")
    admin_pw = os.getenv("ADMIN_PASSWORD")

    if not is_development or not (student_pw and faculty_pw and admin_pw):
        return None, None, None

    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        student_user = db.query(User).filter_by(email="student@obe.edu").first()
        if not student_user:
            student_user = User(
                email="student@obe.edu",
                password_hash=hash_password(student_pw),
                full_name="Navaneethan",
                role="student"
            )
            db.add(student_user)

        faculty_user = db.query(User).filter_by(email="faculty@obe.edu").first()
        if not faculty_user:
            faculty_user = User(
                email="faculty@obe.edu",
                password_hash=hash_password(faculty_pw),
                full_name="Dr. Sarah Johnson",
                role="faculty"
            )
            db.add(faculty_user)

        admin_user = db.query(User).filter_by(email="admin@obe.edu").first()
        if not admin_user:
            admin_user = User(
                email="admin@obe.edu",
                password_hash=hash_password(admin_pw),
                full_name="System Administrator",
                role="admin"
            )
            db.add(admin_user)

        db.commit()
        return student_user, faculty_user, admin_user
    finally:
        if close_db:
            db.close()

def seed_resources(db: SessionLocal = None):
    """
    Idempotently seeds and updates curated learning resources for all topics across all courses.
    Never creates duplicates or touches genuine student progress, assessments, enrollments, or faculty resources.
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
    try:
        from ai_agents.resource_agent import ResourceAgent
        all_topics = db.query(Topic).all()
        created = 0
        updated = 0
        for topic in all_topics:
            res_list = ResourceAgent.get_resources_for_topic(topic.title)
            for res in res_list:
                if "wikipedia.org/wiki/Special:Search" in res.get("url", ""):
                    continue
                existing_res = db.query(Resource).filter(
                    Resource.topic_id == topic.id,
                    Resource.title == res["title"]
                ).first()
                if not existing_res:
                    existing_res = db.query(Resource).filter(
                        Resource.topic_id == topic.id,
                        Resource.resource_type == res.get("resource_type", res.get("type", "Documentation"))
                    ).first()
                if not existing_res:
                    db.add(Resource(
                        topic_id=topic.id,
                        title=res["title"],
                        url=res["url"],
                        resource_type=res.get("resource_type", res.get("type", "Documentation")),
                        website_name=res.get("website_name"),
                        description=res.get("description"),
                        difficulty=res.get("difficulty", "Beginner"),
                        approved_by_faculty=True
                    ))
                    created += 1
                else:
                    existing_res.title = res["title"]
                    existing_res.url = res["url"]
                    existing_res.resource_type = res.get("resource_type", res.get("type", "Documentation"))
                    existing_res.website_name = res.get("website_name")
                    existing_res.description = res.get("description")
                    existing_res.difficulty = res.get("difficulty", "Beginner")
                    existing_res.approved_by_faculty = True
                    updated += 1
        db.commit()
        return created, updated
    finally:
        if close_db:
            db.close()

def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if courses already seeded
        if db.query(Course).filter_by(code="CS201").first():
            print("Database core curriculum already seeded. Verifying topic resources idempotency...")
            created, updated = seed_resources(db)
            print(f"Topic resources sync complete: {created} created, {updated} verified/updated.")
            return

        print("Seeding database with OBE courses, outcomes, diagnostic questions...")

        # 1. Users & Credentials
        student_user, faculty_user, admin_user = seed_users(db)

        # 2. Courses
        ds_course = Course(
            code="CS201",
            title="Data Structures",
            description="Algorithmic problem solving, linear and non-linear data structures, trees, graphs, and dynamic programming.",
            category="Computer Science",
            level="Beginner to Intermediate",
            is_active=True
        )
        python_course = Course(
            code="CS101",
            title="Python Programming",
            description="Comprehensive outcome-based introduction to procedural and structured programming in Python, algorithms, data structures, and software construction.",
            category="Computer Science",
            level="Beginner to Intermediate",
            is_active=False
        )
        ml_course = Course(
            code="AI301",
            title="Machine Learning Fundamentals",
            description="Supervised and unsupervised learning algorithms, evaluation metrics, and neural network introductions.",
            category="Artificial Intelligence",
            level="Intermediate",
            is_active=False
        )
        dbms_course = Course(
            code="CS302",
            title="Database Management Systems",
            description="Relational data modeling, SQL queries, indexing, normalization, and ACID transaction semantics.",
            category="Database Systems",
            level="Intermediate",
            is_active=False
        )
        db.add_all([python_course, ds_course, ml_course, dbms_course])
        db.commit()

        # 3. Course Outcomes for Data Structures (Step 3)
        co1 = CourseOutcome(
            course_id=ds_course.id,
            code="CO1",
            description="Understand fundamental data structures (Stack, Queue, Tree basics)",
            target_attainment_pct=75.0
        )
        co2 = CourseOutcome(
            course_id=ds_course.id,
            code="CO2",
            description="Apply data structures to solve problems (Push/Pop, Enqueue/Dequeue, Simple problems)",
            target_attainment_pct=70.0
        )
        co3 = CourseOutcome(
            course_id=ds_course.id,
            code="CO3",
            description="Analyze algorithm efficiency (Basic Big-O concepts, Complexity comparison)",
            target_attainment_pct=70.0
        )
        db.add_all([co1, co2, co3])
        db.commit()

        # 4. Topics for Data Structures
        topics_data = [
            ("TOPIC-1", "Stack Basics & Operations", 1, "LIFO principle, push, pop, peek, and array/linked-list representations.", "Understand Stack operations, push/pop mechanics, and evaluate simple problems.", "Beginner", 40),
            ("TOPIC-2", "Queue Basics & Operations", 2, "FIFO principle, enqueue, dequeue, circular queues, and queue buffers.", "Understand Queue operations, enqueue/dequeue mechanics, and application buffers.", "Beginner", 40),
            ("TOPIC-3", "Recursion Fundamentals", 3, "Recursive function calls, base conditions, call-stack mechanics, and subproblem decomposition.", "Define recursive formulations with strict base condition stopping criteria.", "Intermediate", 45),
            ("TOPIC-4", "Tree Basics", 4, "Hierarchical data structure, root, leaf, parent, children, height, and binary tree representations.", "Identify binary tree components and calculate structural depth.", "Beginner", 40),
            ("TOPIC-5", "Tree Traversal", 5, "Systematic tree visits: Inorder, Preorder, Postorder, and recursive implementation.", "Trace and implement recursive tree traversal algorithms.", "Intermediate", 50),
            ("TOPIC-6", "Recursive Practice", 6, "Targeted practice on call-stack tracing, recursion accumulation, and tree calculations.", "Solve intermediate recursive computational problems with confidence.", "Intermediate", 35),
            ("TOPIC-7", "Tree Problems & Applications", 7, "Binary Search Tree search, insertion, range queries, and practical tree algorithms.", "Apply tree data structures to solve real-world indexing and search challenges.", "Intermediate", 60),
            ("TOPIC-8", "Algorithm Complexity & Big-O", 8, "Asymptotic notations: Big-O, Omega, Theta, and comparison of time/space complexities.", "Analyze the algorithmic efficiency and growth rate of data structure operations.", "Intermediate", 45)
        ]

        created_topics = []
        for code, title, order, desc, obj, diff, minutes in topics_data:
            t = Topic(
                course_id=ds_course.id,
                code=code,
                title=title,
                order_index=order,
                description=desc,
                learning_objective=obj,
                difficulty=diff,
                est_minutes=minutes
            )
            db.add(t)
            created_topics.append(t)
        db.commit()

        # 5. Topic Prerequisites (Recursion -> Tree Traversal, Tree Basics -> Tree Traversal, Traversal -> Tree Problems)
        t_map = {t.order_index: t.id for t in created_topics}
        # Topic 3 (Recursion) -> Topic 5 (Tree Traversal)
        db.add(TopicPrerequisite(topic_id=t_map[5], prerequisite_topic_id=t_map[3], required_mastery_pct=60.0))
        # Topic 4 (Tree Basics) -> Topic 5 (Tree Traversal)
        db.add(TopicPrerequisite(topic_id=t_map[5], prerequisite_topic_id=t_map[4], required_mastery_pct=60.0))
        # Topic 3 (Recursion) -> Topic 6 (Recursive Practice)
        db.add(TopicPrerequisite(topic_id=t_map[6], prerequisite_topic_id=t_map[3], required_mastery_pct=60.0))
        # Topic 5 (Tree Traversal) -> Topic 7 (Tree Problems)
        db.add(TopicPrerequisite(topic_id=t_map[7], prerequisite_topic_id=t_map[5], required_mastery_pct=60.0))
        db.commit()

        # 6. Topic -> Course Outcome Mappings
        # Stack (1) -> CO1, CO2
        # Queue (2) -> CO1, CO2
        # Recursion (3) -> CO1
        # Tree Basics (4) -> CO1
        # Tree Traversal (5) -> CO1, CO2
        # Recursive Practice (6) -> CO2
        # Tree Problems (7) -> CO2
        # Algorithm Complexity (8) -> CO3
        co_mappings = [
            (1, co1.id), (1, co2.id),
            (2, co1.id), (2, co2.id),
            (3, co1.id),
            (4, co1.id),
            (5, co1.id), (5, co2.id),
            (6, co2.id),
            (7, co2.id),
            (8, co3.id)
        ]
        for ord_idx, cid in co_mappings:
            tid = t_map[ord_idx]
            db.add(TopicOutcomeMapping(topic_id=tid, outcome_id=cid, weight=1.0))
        db.commit()

        # 7. Resources for Topics across all courses (Idempotent)
        seed_resources(db)


        # 8. Diagnostic Questions (Step 4 of PDF: 5 questions)
        diag_data = [
            (
                t_map[1], # Stack Basics
                "What principle does a Stack follow for storing and retrieving elements?",
                None,
                "mcq",
                "Stack basics",
                ["LIFO (Last In First Out)", "FIFO (First In First Out)", "Priority Based", "Random Access"],
                "LIFO (Last In First Out)",
                "A stack is a Last In First Out (LIFO) structure where elements are pushed and popped from the same top end."
            ),
            (
                t_map[1], # Stack Operations
                "Given an empty stack, perform: push(10), push(20), pop(), push(30). What element is now at the top of the stack?",
                "push(10)\npush(20)\npop()\npush(30)",
                "code_logic",
                "Stack operations",
                ["30", "20", "10", "Empty"],
                "30",
                "push(10) -> [10], push(20) -> [10, 20], pop() removes 20 -> [10], push(30) -> [10, 30]. The top element is 30."
            ),
            (
                t_map[2], # Queue Basics
                "Which operation removes an element from the front of a Queue following the FIFO principle?",
                None,
                "mcq",
                "Queue basics",
                ["Dequeue", "Enqueue", "Pop", "Peek"],
                "Dequeue",
                "In a Queue, enqueue inserts elements at the rear, while dequeue removes elements from the front."
            ),
            (
                t_map[4], # Tree Basics
                "What is the maximum number of children any node can have in a Binary Tree?",
                None,
                "mcq",
                "Tree basics",
                ["2", "1", "3", "Unlimited"],
                "2",
                "By definition, each node in a binary tree has at most two children (left child and right child)."
            ),
            (
                t_map[3], # Recursion
                "What essential condition must every recursive function define to prevent infinite recursion / stack overflow?",
                None,
                "mcq",
                "Recursion",
                ["Base condition / stopping case", "Global variable declaration", "While loop", "Break statement"],
                "Base condition / stopping case",
                "A base condition provides the terminating criterion where recursion stops and call frames begin returning."
            )
        ]

        for tid, qtext, snippet, qtype, sub_c, options, correct, expl in diag_data:
            q = DiagnosticQuestion(
                course_id=ds_course.id,
                topic_id=tid,
                question_text=qtext,
                code_snippet=snippet,
                question_type=qtype,
                sub_concept=sub_c,
                options_json=json.dumps(options),
                correct_answer=correct,
                explanation=expl
            )
            db.add(q)
        db.commit()

        # 9. Student Profile (Step 1 & Step 2 of PDF - development demo only)
        if student_user:
            profile = StudentProfile(
                user_id=student_user.id,
                student_id="S101",
                program="B.Tech AI & Data Science",
                semester=4,
                current_level="Beginner",
                academic_level="Undergraduate (Semester 4)",
                selected_course_id=ds_course.id,
                learning_goal="Master fundamental data structures and algorithmic problem solving.",
                prior_knowledge="Beginner with basic programming logic",
                preferred_format="Interactive examples + practice",
                daily_time_minutes=60,
                target_completion_date="2026-12-15",
                diagnostic_completed=True,
                onboarding_completed=True
            )
            db.add(profile)
            db.commit()

            # 10. Initial Mastery Scores for S101
            initial_masteries = {
                1: (80.0, 80.0, 80.0, 100.0, 80.0, "Mastered"),        # Stack Basics
                2: (70.0, 70.0, 70.0, 100.0, 72.0, "Proficient"),      # Queue Basics
                3: (25.0, 30.0, 20.0, 0.0, 25.0, "Needs Improvement"), # Recursion Fundamentals
                4: (35.0, 35.0, 35.0, 0.0, 35.0, "Needs Improvement"), # Tree Basics
                5: (30.0, 30.0, 0.0, 0.0, 25.0, "Needs Improvement"),  # Tree Traversal
                6: (20.0, 20.0, 0.0, 0.0, 15.0, "Needs Improvement"),  # Recursive Practice
                7: (10.0, 0.0, 0.0, 0.0, 5.0, "Needs Improvement"),    # Tree Problems
                8: (40.0, 40.0, 0.0, 0.0, 30.0, "Needs Improvement")   # Algorithm Complexity
            }

            masteries_dict = {}
            for topic in created_topics:
                d_s, q_s, p_s, c_s, ovr, cls_name = initial_masteries[topic.order_index]
                m = MasteryScore(
                    user_id=student_user.id,
                    topic_id=topic.id,
                    diagnostic_score=d_s,
                    quiz_score=q_s,
                    practice_score=p_s,
                    completion_score=c_s,
                    overall_mastery=ovr,
                    classification=cls_name
                )
                db.add(m)
                masteries_dict[topic.id] = ovr
            db.commit()

            # 11. Step 6 — Personalized Learning Path Generation
            learning_path = LearningPath(
                user_id=student_user.id,
                course_id=ds_course.id,
                status="ACTIVE",
                adaptation_reason="Personalized path generated: Bypassed already understood topics (Stack 80%, Queue 70%). Focused trajectory scheduled."
            )
            db.add(learning_path)
            db.commit()

            path_steps = [
                (t_map[3], 1, "CURRENT", "Target focus: Recursion is a mandatory prerequisite for Tree Traversal. Low diagnostic score (25%).", False),
                (t_map[4], 2, "RECOMMENDED", "Binary tree node properties and structure definitions.", False),
                (t_map[5], 3, "LOCKED", "Prerequisite requirement not satisfied: Requires Recursion Fundamentals and Tree Basics before unlocking.", False),
                (t_map[7], 4, "LOCKED", "Dependent algorithmic application topic scheduled after Tree Traversal.", False)
            ]

            for tid, seq, st, r_reason, is_rem in path_steps:
                db.add(LearningPathItem(
                    learning_path_id=learning_path.id,
                    topic_id=tid,
                    sequence_order=seq,
                    status=st,
                    recommendation_reason=r_reason,
                    is_remedial=is_rem
                ))
            db.commit()

            # 12. Outcome Attainments for Data Structures
            co_scores = [
                (co1, 65.0, "In Progress"),
                (co2, 55.0, "In Progress"),
                (co3, 35.0, "Needs Improvement")
            ]
            for co_obj, pct, st in co_scores:
                db.add(OutcomeAttainment(
                    user_id=student_user.id,
                    course_id=ds_course.id,
                    outcome_id=co_obj.id,
                    attainment_percentage=pct,
                    status=st
                ))
            db.commit()

            # 13. Initial Agent Logs documenting Step 1 to Step 6
            initial_logs = [
                ("Planner Agent", "path_generated", "Step 6: Personalized path generated: Recursion ➔ Tree Basics ➔ Tree Traversal ➔ Tree Problems. Bypassed Stack & Queue."),
                ("Assessment Agent", "gap_identification", "Step 5: Identified Understood concepts: Stack (80% ✓), Queue (70% ✓). Needs Learning: Trees (35% ✗), Recursion (25% ✗)."),
                ("Assessment Agent", "diagnostic_evaluated", "Step 4: Initial diagnostic test evaluated: 5 concept-mapped questions scored."),
                ("Planner Agent", "co_concept_mapping", "Step 3: Fixed CO–Concept–Level mapping established for Data Structures (CO1, CO2, CO3)."),
                ("Progress Agent", "profile_registered", "Step 1 & 2: Student S101 (B.Tech AI & Data Science, Semester 4) enrolled in Data Structures (Beginner Level).")
            ]
            for agent_name, action, msg in initial_logs:
                db.add(AgentLog(
                    user_id=student_user.id,
                    agent_name=agent_name,
                    action=action,
                    message=msg,
                    created_at=datetime.utcnow()
                ))
            db.commit()

        print("Seed completed successfully!")

    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
