from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text, UniqueConstraint, text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
from core.thresholds import PREREQ_UNLOCK

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, default="student") # student, faculty, admin
    must_change_password = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship("StudentProfile", back_populates="user", uselist=False)
    mastery_scores = relationship("MasteryScore", back_populates="user")
    learning_paths = relationship("LearningPath", back_populates="user")
    quiz_attempts = relationship("QuizAttempt", back_populates="user")
    agent_logs = relationship("AgentLog", back_populates="user")

class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    academic_level = Column(String, default="Undergraduate (Semester 4)") # Undergraduate, Postgraduate, Beginner
    student_id = Column(String, default="S101")
    program = Column(String, default="B.Tech AI & Data Science")
    semester = Column(Integer, default=4)
    current_level = Column(String, default="Beginner") # Beginner, Intermediate, Advanced
    selected_course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    learning_goal = Column(String, default="Master fundamentals and solve intermediate programming problems")
    prior_knowledge = Column(String, default="Beginner with basic concepts")
    preferred_format = Column(String, default="Interactive examples + practice")
    daily_time_minutes = Column(Integer, default=60) # 1 hour/day
    target_completion_date = Column(String, default="2026-12-31")
    department = Column(String, default="Computer Science & Engineering")
    onboarding_completed = Column(Boolean, default=False)
    diagnostic_completed = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="profile")
    course = relationship("Course")

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String, default="Computer Science")
    level = Column(String, default="Beginner to Intermediate")
    is_active = Column(Boolean, default=True)

    outcomes = relationship("CourseOutcome", back_populates="course", cascade="all, delete-orphan")
    topics = relationship("Topic", back_populates="course", cascade="all, delete-orphan", order_by="Topic.order_index")

class CourseOutcome(Base):
    __tablename__ = "course_outcomes"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    code = Column(String, nullable=False) # CO1, CO2, CO3, CO4
    description = Column(Text, nullable=False)
    target_attainment_pct = Column(Float, default=70.0)

    course = relationship("Course", back_populates="outcomes")
    mappings = relationship("TopicOutcomeMapping", back_populates="outcome")

class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    code = Column(String, nullable=False)
    title = Column(String, nullable=False)
    order_index = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)
    learning_objective = Column(Text, nullable=False)
    difficulty = Column(String, default="Beginner") # Beginner, Intermediate, Advanced
    est_minutes = Column(Integer, default=45)

    course = relationship("Course", back_populates="topics")
    prerequisites = relationship("TopicPrerequisite", foreign_keys="TopicPrerequisite.topic_id", back_populates="topic")
    outcome_mappings = relationship("TopicOutcomeMapping", back_populates="topic")
    resources = relationship("Resource", back_populates="topic")
    diagnostic_questions = relationship("DiagnosticQuestion", back_populates="topic")

class TopicPrerequisite(Base):
    __tablename__ = "topic_prerequisites"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    prerequisite_topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    required_mastery_pct = Column(Float, default=PREREQ_UNLOCK)

    topic = relationship("Topic", foreign_keys=[topic_id], back_populates="prerequisites")
    prerequisite_topic = relationship("Topic", foreign_keys=[prerequisite_topic_id])

class TopicOutcomeMapping(Base):
    __tablename__ = "topic_outcome_mappings"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    outcome_id = Column(Integer, ForeignKey("course_outcomes.id"), nullable=False)
    weight = Column(Float, default=1.0)

    topic = relationship("Topic", back_populates="outcome_mappings")
    outcome = relationship("CourseOutcome", back_populates="mappings")

class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    title = Column(String, nullable=False)
    url = Column(String, nullable=False)
    resource_type = Column(String, default="Documentation") # Documentation, Tutorial, Interactive, Video
    approved_by_faculty = Column(Boolean, default=True)
    website_name = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    difficulty = Column(String, default="Beginner")

    topic = relationship("Topic", back_populates="resources")

class DiagnosticQuestion(Base):
    __tablename__ = "diagnostic_questions"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    code_snippet = Column(Text, nullable=True)
    question_type = Column(String, default="mcq") # mcq, output_prediction, code_logic
    sub_concept = Column(String, nullable=True) # e.g. Stack basics, Queue basics, Tree basics, Recursion, Inorder
    options_json = Column(Text, nullable=False) # JSON array of string options
    correct_answer = Column(String, nullable=False)
    explanation = Column(Text, nullable=False)

    topic = relationship("Topic", back_populates="diagnostic_questions")

class MasteryScore(Base):
    __tablename__ = "mastery_scores"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    diagnostic_score = Column(Float, default=0.0) # 0-100
    quiz_score = Column(Float, default=0.0)       # 0-100
    practice_score = Column(Float, default=0.0)   # 0-100
    completion_score = Column(Float, default=0.0) # 0 or 100
    overall_mastery = Column(Float, default=0.0)  # Calculated: 0.4*diag + 0.3*quiz + 0.2*practice + 0.1*completion
    classification = Column(String, default="Needs Improvement") # Needs Improvement, Developing, Proficient, Mastered
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="mastery_scores")
    topic = relationship("Topic")

class LearningPath(Base):
    __tablename__ = "learning_paths"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    status = Column(String, default="ACTIVE") # ACTIVE, COMPLETED, REVISED
    adaptation_reason = Column(Text, default="Initial personalized path generated from diagnostic profile")
    generated_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="learning_paths")
    course = relationship("Course")
    items = relationship("LearningPathItem", back_populates="learning_path", cascade="all, delete-orphan", order_by="LearningPathItem.sequence_order")

class LearningPathItem(Base):
    __tablename__ = "learning_path_items"

    id = Column(Integer, primary_key=True, index=True)
    learning_path_id = Column(Integer, ForeignKey("learning_paths.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    sequence_order = Column(Integer, nullable=False)
    status = Column(String, default="LOCKED") # COMPLETED, CURRENT, RECOMMENDED, NEEDS REVISION, LOCKED
    recommendation_reason = Column(Text, nullable=False)
    is_remedial = Column(Boolean, default=False)
    remedial_title = Column(String, nullable=True)
    remedial_description = Column(Text, nullable=True)

    learning_path = relationship("LearningPath", back_populates="items")
    topic = relationship("Topic")

class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    score = Column(Integer, nullable=False)
    max_score = Column(Integer, default=10)
    percentage = Column(Float, nullable=False)
    passed = Column(Boolean, default=False)
    answers_json = Column(Text, nullable=True) # JSON details
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="quiz_attempts")
    topic = relationship("Topic")

class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    agent_name = Column(String, nullable=False) # Planner Agent, Tutor Agent, Assessment Agent, Resource Agent, Progress Agent
    action = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="agent_logs")

class OutcomeAttainment(Base):
    __tablename__ = "outcome_attainments"
    __table_args__ = (
        UniqueConstraint("user_id", "course_id", "outcome_id", name="uq_user_course_outcome"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    outcome_id = Column(Integer, ForeignKey("course_outcomes.id"), nullable=False)
    attainment_percentage = Column(Float, default=0.0)
    status = Column(String, default="Not Started") # Not Started, Needs Improvement, In Progress, Achieved
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    outcome = relationship("CourseOutcome")

class OutcomeAttainmentHistory(Base):
    __tablename__ = "outcome_attainment_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    outcome_id = Column(Integer, ForeignKey("course_outcomes.id"), nullable=False)
    attainment_pct = Column(Float, nullable=False)
    trigger = Column(String, nullable=False, default="recalculation") # quiz, completion, diagnostic, recalculation
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    course = relationship("Course")
    outcome = relationship("CourseOutcome")

class QuestionBank(Base):
    __tablename__ = "question_bank"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    outcome_id = Column(Integer, ForeignKey("course_outcomes.id"), nullable=True)
    sub_concept = Column(String, nullable=True)
    difficulty = Column(String, default="Beginner") # Beginner, Intermediate, Advanced
    question_type = Column(String, default="mcq") # mcq, code_logic, output_prediction
    question_text = Column(Text, nullable=False)
    code_snippet = Column(Text, nullable=True)
    options_json = Column(Text, nullable=False) # JSON list
    correct_answer = Column(String, nullable=False)
    explanation = Column(Text, nullable=False)

    bloom_level = Column(String, default="Understand") # Remember, Understand, Apply, Analyze, Evaluate, Create

    course = relationship("Course")
    topic = relationship("Topic")
    outcome = relationship("CourseOutcome")

class AssessmentAttempt(Base):
    __tablename__ = "assessment_attempts"

    id = Column(Integer, primary_key=True, index=True)
    attempt_uuid = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True) # None for multi-topic diagnostic/assessment
    attempt_type = Column(String, default="practice", nullable=False) # diagnostic, quiz, practice, assessment, reassessment
    score = Column(Float, nullable=False)
    max_score = Column(Float, nullable=False)
    percentage = Column(Float, nullable=False)
    passed = Column(Boolean, default=False)
    topic_scores_json = Column(Text, nullable=True) # JSON dict of topic_id -> percentage
    answers_json = Column(Text, nullable=True) # JSON details of answers submitted
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    course = relationship("Course")
    topic = relationship("Topic")
    answers = relationship("QuestionAnswerHistory", back_populates="attempt", cascade="all, delete-orphan")

class QuestionAnswerHistory(Base):
    __tablename__ = "question_answer_history"

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("assessment_attempts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("question_bank.id"), nullable=True)
    concept = Column(String, nullable=True, default="General")
    selected_answer = Column(String, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    attempt = relationship("AssessmentAttempt", back_populates="answers")
    question = relationship("QuestionBank", foreign_keys=[question_id])
    user = relationship("User")

class MasteryHistory(Base):
    __tablename__ = "mastery_histories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    previous_mastery = Column(Float, nullable=False)
    new_mastery = Column(Float, nullable=False)
    activity_type = Column(String, nullable=False)
    source = Column(String, default="practice", nullable=True)
    score = Column(Float, nullable=False)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    topic = relationship("Topic")

class StudySession(Base):
    __tablename__ = "study_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    activity_type = Column(String, nullable=False) # learning, practice, assessment, tutor
    duration_minutes = Column(Float, default=15.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    course = relationship("Course")

class ClassModel(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    faculty_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    name = Column(String, nullable=False)
    class_code = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    max_students = Column(Integer, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    faculty = relationship("User", foreign_keys=[faculty_id])
    course = relationship("Course", foreign_keys=[course_id])
    enrollments = relationship("ClassEnrollment", back_populates="class_obj", cascade="all, delete-orphan")

# Alias for standard import
Class = ClassModel

class ClassEnrollment(Base):
    __tablename__ = "class_enrollments"
    __table_args__ = (
        UniqueConstraint("class_id", "student_id", name="uq_class_student"),
    )

    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="active", nullable=False) # "active", "left", "removed"
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    left_at = Column(DateTime, nullable=True)
    consent_accepted_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    baseline_mastery_json = Column(Text, nullable=True)
    baseline_co_json = Column(Text, nullable=True)
    baseline_completed_topics = Column(Integer, default=0, nullable=False)

    class_obj = relationship("ClassModel", back_populates="enrollments")
    student = relationship("User", foreign_keys=[student_id])


class InterventionEvent(Base):
    __tablename__ = "intervention_events"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True)
    type = Column(String, nullable=False) # remedial_inserted, path_adapted, teacher_flag, class_joined
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    note = Column(Text, nullable=True)

    student = relationship("User", foreign_keys=[student_id])
    class_obj = relationship("ClassModel", foreign_keys=[class_id])
    topic = relationship("Topic", foreign_keys=[topic_id])


class ClassResource(Base):
    __tablename__ = "class_resources"

    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    url = Column(String(500), nullable=False)
    resource_type = Column(String(50), nullable=False)  # video, article, notes, practice, other
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_deleted = Column(Boolean, default=False, server_default=text('false'), nullable=False)

    class_obj = relationship("ClassModel", foreign_keys=[class_id])
    creator = relationship("User", foreign_keys=[created_by])
    topic = relationship("Topic", foreign_keys=[topic_id])


class ClassAnnouncement(Base):
    __tablename__ = "class_announcements"

    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(150), nullable=False)
    body = Column(Text, nullable=False)
    pinned = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_deleted = Column(Boolean, default=False, server_default=text('false'), nullable=False)

    class_obj = relationship("ClassModel", foreign_keys=[class_id])
    creator = relationship("User", foreign_keys=[created_by])
    reads = relationship("AnnouncementRead", back_populates="announcement", cascade="all, delete-orphan")


class AnnouncementRead(Base):
    __tablename__ = "announcement_reads"

    announcement_id = Column(Integer, ForeignKey("class_announcements.id", ondelete="CASCADE"), primary_key=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    read_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    announcement = relationship("ClassAnnouncement", back_populates="reads")
    student = relationship("User", foreign_keys=[student_id])


class ClassDoubt(Base):
    __tablename__ = "class_doubts"

    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(150), nullable=False)
    body = Column(Text, nullable=False)
    visibility = Column(String(20), default="private", nullable=False)  # "private" or "class"
    status = Column(String(20), default="open", nullable=False)  # "open", "answered", "closed"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    class_obj = relationship("ClassModel", foreign_keys=[class_id])
    student = relationship("User", foreign_keys=[student_id])
    topic = relationship("Topic", foreign_keys=[topic_id])
    replies = relationship("ClassDoubtReply", back_populates="doubt", cascade="all, delete-orphan")


class ClassDoubtReply(Base):
    __tablename__ = "class_doubt_replies"

    id = Column(Integer, primary_key=True, index=True)
    doubt_id = Column(Integer, ForeignKey("class_doubts.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_deleted = Column(Boolean, default=False, server_default=text('false'), nullable=False)

    doubt = relationship("ClassDoubt", back_populates="replies")
    author = relationship("User", foreign_keys=[author_id])



