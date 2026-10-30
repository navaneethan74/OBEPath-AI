import sys, os
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
from database import SessionLocal
from progress_engine import get_central_student_state
from models import User, Course

def test_courses_state():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.role == "student").first()
        if not user:
            user = User(
                email="courses_state_tester@obe.edu",
                full_name="State Student",
                password_hash="testhash",
                role="student"
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        courses = db.query(Course).all()
        for c in courses:
            st = get_central_student_state(db, user_id=user.id, course_id=c.id)
            c_info = st['enrolledCourse']
            assert c_info is not None
            assert "overallMastery" in st
            print(f"=== Course {c.id}: [{c_info['code']}] {c_info['title']} ===")
            print(f"Overall Mastery: {st['overallMastery']}%, Progress: {st['overallProgress']}%")
    finally:
        db.close()
