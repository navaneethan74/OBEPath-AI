import sys
sys.path.insert(0, 'backend')
from database import SessionLocal
from models import Course, Topic, TopicPrerequisite, StudentProfile, User, MasteryScore, QuestionBank, LearningPath

db = SessionLocal()
print("=== COURSES ===")
for c in db.query(Course).all():
    t_cnt = db.query(Topic).filter(Topic.course_id == c.id).count()
    q_cnt = db.query(QuestionBank).filter(QuestionBank.course_id == c.id).count()
    print(f"ID {c.id}: [{c.code}] {c.title} | Active: {c.is_active} | Topics: {t_cnt} | Questions: {q_cnt}")

print("\n=== TOPIC PREREQUISITES ===")
for p in db.query(TopicPrerequisite).all():
    t = db.query(Topic).filter(Topic.id == p.topic_id).first()
    pt = db.query(Topic).filter(Topic.id == p.prerequisite_topic_id).first()
    t_name = t.title if t else str(p.topic_id)
    pt_name = pt.title if pt else str(p.prerequisite_topic_id)
    cid = t.course_id if t else "?"
    print(f"Course {cid}: '{t_name}' (id={p.topic_id}) requires '{pt_name}' (id={p.prerequisite_topic_id}) >= {p.required_mastery_pct}%")

print("\n=== TOPICS WITH NO PREREQS (BEGINNER TOPICS) ===")
for c in db.query(Course).all():
    topics = db.query(Topic).filter(Topic.course_id == c.id).order_by(Topic.order_index).all()
    print(f"Course {c.id} ({c.code}):")
    for t in topics:
        pr = db.query(TopicPrerequisite).filter(TopicPrerequisite.topic_id == t.id).all()
        q_count = db.query(QuestionBank).filter(QuestionBank.topic_id == t.id).count()
        pr_names = [db.query(Topic).filter(Topic.id == x.prerequisite_topic_id).first().title for x in pr]
        print(f"  - [{t.order_index}] id={t.id}: '{t.title}' | Prereqs: {pr_names} | Questions in Bank: {q_count}")

print("\n=== USERS ===")
for u in db.query(User).all():
    p = u.profile
    cid = getattr(p, 'selected_course_id', None)
    diag = getattr(p, 'diagnostic_completed', False)
    onboard = getattr(p, 'onboarding_completed', False)
    print(f"User {u.id}: {u.email} ({u.role}) | Course: {cid} | Diag Done: {diag} | Onboard: {onboard}")

db.close()
