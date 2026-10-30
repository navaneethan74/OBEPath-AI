from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime

class UserBase(BaseModel):
    email: str
    full_name: str
    role: str = "student"

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: str
    password: str
    role: Optional[str] = "student"
    expected_role: Optional[str] = None

class GoogleAuthRequest(BaseModel):
    credential: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    google_id: Optional[str] = None
    avatar_url: Optional[str] = None

class FacultyCreateRequest(BaseModel):
    name: Optional[str] = None
    full_name: Optional[str] = None
    email: str
    password: Optional[str] = None
    temporary_password: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class UserOut(UserBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    academic_level: Optional[str] = None
    student_id: Optional[str] = None
    program: Optional[str] = None
    semester: Optional[int] = None
    current_level: Optional[str] = None
    selected_course_id: Optional[int] = None
    learning_goal: Optional[str] = None
    prior_knowledge: Optional[str] = None
    preferred_format: Optional[str] = None
    daily_time_minutes: Optional[int] = None
    target_completion_date: Optional[str] = None
    department: Optional[str] = None
    onboarding_completed: Optional[bool] = None

class ProfileOut(BaseModel):
    id: int
    user_id: int
    full_name: Optional[str] = None
    email: Optional[str] = None
    student_id: str
    program: str
    semester: int
    current_level: str
    academic_level: str
    selected_course_id: Optional[int]
    learning_goal: str
    prior_knowledge: str
    preferred_format: str
    daily_time_minutes: int
    target_completion_date: str
    department: Optional[str] = "Computer Science & Engineering"
    onboarding_completed: bool = False
    diagnostic_completed: bool
    class Config:
        from_attributes = True

class OutcomeOut(BaseModel):
    id: int
    course_id: int
    code: str
    description: str
    target_attainment_pct: float
    class Config:
        from_attributes = True

class ResourceOut(BaseModel):
    id: Any
    topic_id: Optional[int] = None
    title: str
    url: str
    resource_type: str = "Documentation"
    approved_by_faculty: bool = False
    website_name: Optional[str] = None
    description: Optional[str] = None
    difficulty: Optional[str] = "Beginner"
    class Config:
        from_attributes = True

class TopicOut(BaseModel):
    id: int
    course_id: int
    code: str
    title: str
    order_index: int
    description: str
    learning_objective: str
    difficulty: str
    est_minutes: int
    prerequisites: Optional[List[int]] = []
    outcomes: Optional[List[str]] = []
    resources: Optional[List[Dict[str, Any]]] = []
    class Config:
        from_attributes = True

class CourseOut(BaseModel):
    id: int
    code: str
    title: str
    description: str
    category: str
    level: str
    is_active: bool
    outcomes: List[OutcomeOut] = []
    topics: List[TopicOut] = []
    class Config:
        from_attributes = True

class DiagnosticQuestionOut(BaseModel):
    id: int
    course_id: int
    topic_id: int
    topic_title: Optional[str] = None
    question_text: str
    code_snippet: Optional[str] = None
    question_type: str
    options: List[str]
    # Do not expose correct_answer in the test prompt

class DiagnosticAnswerItem(BaseModel):
    question_id: int
    selected_answer: str

class DiagnosticSubmitRequest(BaseModel):
    course_id: int
    answers: List[DiagnosticAnswerItem]

class MasteryScoreOut(BaseModel):
    topic_id: int
    topic_title: str
    topic_code: str
    diagnostic_score: float
    quiz_score: float
    practice_score: float
    completion_score: float
    overall_mastery: float
    classification: str

class LearningPathItemOut(BaseModel):
    id: int
    sequence_order: int
    topic_id: int
    topic_title: str
    topic_code: str
    difficulty: str
    est_minutes: int
    status: str
    recommendation_reason: str
    related_outcomes: List[str]
    prerequisites: List[str]
    mastery_percentage: float
    is_remedial: bool = False
    remedial_title: Optional[str] = None
    remedial_description: Optional[str] = None

class LearningPathOut(BaseModel):
    id: int
    course_id: int
    course_title: str
    status: str
    adaptation_reason: str
    generated_at: datetime
    updated_at: datetime
    items: List[LearningPathItemOut]

class TutorChatRequest(BaseModel):
    topic_id: int
    message: str = ""
    action: Optional[str] = None # "explain_simply", "give_example", "give_hint", "give_another_example", "test_me", "summarize"
    course_id: Optional[int] = None
    history: Optional[List[Dict[str, str]]] = None

class TutorChatResponse(BaseModel):
    reply: str
    action_taken: str
    adapted_for_level: str
    suggested_followups: List[str] = []
    model_used: Optional[str] = None
    error: Optional[str] = None

class TutorModalityRequest(BaseModel):
    topic_id: int
    modality: str # "explanation", "analogy", "worked_example", "code", "visual", "practice", "custom"
    user_prompt: Optional[str] = None
    pedagogical_style: Optional[str] = None

class TutorModalityResponse(BaseModel):
    topic_id: int
    topic_title: str
    modality: str
    pedagogical_style: str
    content_markdown: str
    key_takeaways: List[str]
    code_snippet: Optional[str] = None
    visual_ascii: Optional[str] = None
    practice_question: Optional[Dict[str, Any]] = None
    suggested_prompts: List[str]

class QuizSubmitRequest(BaseModel):
    topic_id: int
    score: int
    max_score: int = 10
    answers: Optional[Dict[str, Any]] = None

class PracticeSubmitRequest(BaseModel):
    topic_id: int
    score: int # 0-100

class AgentLogOut(BaseModel):
    id: int
    agent_name: str
    action: str
    message: str
    created_at: datetime
    metadata_json: Optional[str] = None
    class Config:
        from_attributes = True

class OutcomeAttainmentOut(BaseModel):
    outcome_id: int
    outcome_code: str
    description: str
    target_pct: float
    attainment_percentage: float
    status: str
    contributing_topics: List[Dict[str, Any]]
    evidence: Dict[str, Any]

class ClassCreateRequest(BaseModel):
    course_id: int
    name: str
    custom_code: Optional[str] = None
    max_students: Optional[int] = None
    expires_at: Optional[datetime] = None

class ClassOut(BaseModel):
    id: int
    faculty_id: int
    course_id: int
    course_code: Optional[str] = None
    course_title: Optional[str] = None
    name: str
    class_code: str
    is_active: bool
    max_students: Optional[int] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    active_students_count: int = 0

class StudentPreviewRequest(BaseModel):
    class_code: str

class StudentJoinRequest(BaseModel):
    class_code: str
    accept_consent: bool = False

class TeacherFlagRequest(BaseModel):
    note: str

# Class Communication Schemas
class ClassResourceCreate(BaseModel):
    title: str
    url: str
    resource_type: str = "other"
    description: Optional[str] = None
    topic_id: Optional[int] = None

class ClassResourceOut(BaseModel):
    id: int
    class_id: int
    created_by: int
    title: str
    description: Optional[str] = None
    url: str
    resource_type: str
    topic_id: Optional[int] = None
    topic_title: Optional[str] = None
    created_at: str
    is_deleted: bool = False

class ClassAnnouncementCreate(BaseModel):
    title: str
    body: str
    pinned: bool = False

class ClassAnnouncementOut(BaseModel):
    id: int
    class_id: int
    created_by: int
    title: str
    body: str
    pinned: bool
    created_at: str
    is_read: Optional[bool] = None

class ClassDoubtCreate(BaseModel):
    title: str
    body: str
    topic_id: Optional[int] = None
    visibility: str = "private"

class ClassDoubtReplyCreate(BaseModel):
    body: str

class ClassDoubtReplyOut(BaseModel):
    id: int
    doubt_id: int
    author_id: int
    author_name: str
    author_role: str = "faculty"
    body: str
    created_at: str

class ClassDoubtOut(BaseModel):
    id: int
    class_id: int
    student_id: Optional[int] = None
    title: str
    body: str
    visibility: str
    status: str
    topic_id: Optional[int] = None
    topic_title: Optional[str] = None
    created_at: str
    author_name: str
    is_my_doubt: Optional[bool] = None
    replies: List[ClassDoubtReplyOut] = []



