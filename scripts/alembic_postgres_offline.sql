BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 2eff8e0f240d

CREATE TABLE courses (
    id SERIAL NOT NULL, 
    code VARCHAR NOT NULL, 
    title VARCHAR NOT NULL, 
    description TEXT NOT NULL, 
    category VARCHAR, 
    level VARCHAR, 
    is_active BOOLEAN, 
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_courses_code ON courses (code);

CREATE INDEX ix_courses_id ON courses (id);

CREATE TABLE users (
    id SERIAL NOT NULL, 
    email VARCHAR NOT NULL, 
    password_hash VARCHAR NOT NULL, 
    full_name VARCHAR NOT NULL, 
    role VARCHAR, 
    must_change_password BOOLEAN, 
    created_at TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_users_email ON users (email);

CREATE INDEX ix_users_id ON users (id);

CREATE TABLE agent_logs (
    id SERIAL NOT NULL, 
    user_id INTEGER, 
    agent_name VARCHAR NOT NULL, 
    action VARCHAR NOT NULL, 
    message TEXT NOT NULL, 
    metadata_json TEXT, 
    created_at TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_agent_logs_id ON agent_logs (id);

CREATE TABLE classes (
    id SERIAL NOT NULL, 
    faculty_id INTEGER NOT NULL, 
    course_id INTEGER NOT NULL, 
    name VARCHAR NOT NULL, 
    class_code VARCHAR NOT NULL, 
    is_active BOOLEAN NOT NULL, 
    max_students INTEGER, 
    expires_at TIMESTAMP WITHOUT TIME ZONE, 
    created_at TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(course_id) REFERENCES courses (id), 
    FOREIGN KEY(faculty_id) REFERENCES users (id)
);

CREATE UNIQUE INDEX ix_classes_class_code ON classes (class_code);

CREATE INDEX ix_classes_id ON classes (id);

CREATE TABLE course_outcomes (
    id SERIAL NOT NULL, 
    course_id INTEGER NOT NULL, 
    code VARCHAR NOT NULL, 
    description TEXT NOT NULL, 
    target_attainment_pct FLOAT, 
    PRIMARY KEY (id), 
    FOREIGN KEY(course_id) REFERENCES courses (id)
);

CREATE INDEX ix_course_outcomes_id ON course_outcomes (id);

CREATE TABLE learning_paths (
    id SERIAL NOT NULL, 
    user_id INTEGER NOT NULL, 
    course_id INTEGER NOT NULL, 
    status VARCHAR, 
    adaptation_reason TEXT, 
    generated_at TIMESTAMP WITHOUT TIME ZONE, 
    updated_at TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(course_id) REFERENCES courses (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_learning_paths_id ON learning_paths (id);

CREATE TABLE student_profiles (
    id SERIAL NOT NULL, 
    user_id INTEGER, 
    academic_level VARCHAR, 
    student_id VARCHAR, 
    program VARCHAR, 
    semester INTEGER, 
    current_level VARCHAR, 
    selected_course_id INTEGER, 
    learning_goal VARCHAR, 
    prior_knowledge VARCHAR, 
    preferred_format VARCHAR, 
    daily_time_minutes INTEGER, 
    target_completion_date VARCHAR, 
    department VARCHAR, 
    onboarding_completed BOOLEAN, 
    diagnostic_completed BOOLEAN, 
    updated_at TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(selected_course_id) REFERENCES courses (id), 
    FOREIGN KEY(user_id) REFERENCES users (id), 
    UNIQUE (user_id)
);

CREATE INDEX ix_student_profiles_id ON student_profiles (id);

CREATE TABLE study_sessions (
    id SERIAL NOT NULL, 
    user_id INTEGER NOT NULL, 
    course_id INTEGER, 
    activity_type VARCHAR NOT NULL, 
    duration_minutes FLOAT, 
    created_at TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(course_id) REFERENCES courses (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_study_sessions_id ON study_sessions (id);

CREATE TABLE topics (
    id SERIAL NOT NULL, 
    course_id INTEGER NOT NULL, 
    code VARCHAR NOT NULL, 
    title VARCHAR NOT NULL, 
    order_index INTEGER NOT NULL, 
    description TEXT NOT NULL, 
    learning_objective TEXT NOT NULL, 
    difficulty VARCHAR, 
    est_minutes INTEGER, 
    PRIMARY KEY (id), 
    FOREIGN KEY(course_id) REFERENCES courses (id)
);

CREATE INDEX ix_topics_id ON topics (id);

CREATE TABLE assessment_attempts (
    id SERIAL NOT NULL, 
    attempt_uuid VARCHAR NOT NULL, 
    user_id INTEGER NOT NULL, 
    course_id INTEGER NOT NULL, 
    topic_id INTEGER, 
    attempt_type VARCHAR NOT NULL, 
    score FLOAT NOT NULL, 
    max_score FLOAT NOT NULL, 
    percentage FLOAT NOT NULL, 
    passed BOOLEAN, 
    topic_scores_json TEXT, 
    answers_json TEXT, 
    created_at TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(course_id) REFERENCES courses (id), 
    FOREIGN KEY(topic_id) REFERENCES topics (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE UNIQUE INDEX ix_assessment_attempts_attempt_uuid ON assessment_attempts (attempt_uuid);

CREATE INDEX ix_assessment_attempts_id ON assessment_attempts (id);

CREATE TABLE class_enrollments (
    id SERIAL NOT NULL, 
    class_id INTEGER NOT NULL, 
    student_id INTEGER NOT NULL, 
    status VARCHAR NOT NULL, 
    joined_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    left_at TIMESTAMP WITHOUT TIME ZONE, 
    consent_accepted_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    baseline_mastery_json TEXT, 
    baseline_co_json TEXT, 
    baseline_completed_topics INTEGER NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(class_id) REFERENCES classes (id), 
    FOREIGN KEY(student_id) REFERENCES users (id), 
    CONSTRAINT uq_class_student UNIQUE (class_id, student_id)
);

CREATE INDEX ix_class_enrollments_id ON class_enrollments (id);

CREATE TABLE diagnostic_questions (
    id SERIAL NOT NULL, 
    course_id INTEGER NOT NULL, 
    topic_id INTEGER NOT NULL, 
    question_text TEXT NOT NULL, 
    code_snippet TEXT, 
    question_type VARCHAR, 
    sub_concept VARCHAR, 
    options_json TEXT NOT NULL, 
    correct_answer VARCHAR NOT NULL, 
    explanation TEXT NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(course_id) REFERENCES courses (id), 
    FOREIGN KEY(topic_id) REFERENCES topics (id)
);

CREATE INDEX ix_diagnostic_questions_id ON diagnostic_questions (id);

CREATE TABLE intervention_events (
    id SERIAL NOT NULL, 
    student_id INTEGER NOT NULL, 
    class_id INTEGER, 
    topic_id INTEGER, 
    type VARCHAR NOT NULL, 
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    note TEXT, 
    PRIMARY KEY (id), 
    FOREIGN KEY(class_id) REFERENCES classes (id), 
    FOREIGN KEY(student_id) REFERENCES users (id), 
    FOREIGN KEY(topic_id) REFERENCES topics (id)
);

CREATE INDEX ix_intervention_events_id ON intervention_events (id);

CREATE TABLE learning_path_items (
    id SERIAL NOT NULL, 
    learning_path_id INTEGER NOT NULL, 
    topic_id INTEGER NOT NULL, 
    sequence_order INTEGER NOT NULL, 
    status VARCHAR, 
    recommendation_reason TEXT NOT NULL, 
    is_remedial BOOLEAN, 
    remedial_title VARCHAR, 
    remedial_description TEXT, 
    PRIMARY KEY (id), 
    FOREIGN KEY(learning_path_id) REFERENCES learning_paths (id), 
    FOREIGN KEY(topic_id) REFERENCES topics (id)
);

CREATE INDEX ix_learning_path_items_id ON learning_path_items (id);

CREATE TABLE mastery_histories (
    id SERIAL NOT NULL, 
    user_id INTEGER NOT NULL, 
    topic_id INTEGER NOT NULL, 
    previous_mastery FLOAT NOT NULL, 
    new_mastery FLOAT NOT NULL, 
    activity_type VARCHAR NOT NULL, 
    source VARCHAR, 
    score FLOAT NOT NULL, 
    reason TEXT, 
    created_at TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(topic_id) REFERENCES topics (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_mastery_histories_id ON mastery_histories (id);

CREATE TABLE mastery_scores (
    id SERIAL NOT NULL, 
    user_id INTEGER NOT NULL, 
    topic_id INTEGER NOT NULL, 
    diagnostic_score FLOAT, 
    quiz_score FLOAT, 
    practice_score FLOAT, 
    completion_score FLOAT, 
    overall_mastery FLOAT, 
    classification VARCHAR, 
    updated_at TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(topic_id) REFERENCES topics (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_mastery_scores_id ON mastery_scores (id);

CREATE TABLE outcome_attainment_history (
    id SERIAL NOT NULL, 
    user_id INTEGER NOT NULL, 
    course_id INTEGER NOT NULL, 
    outcome_id INTEGER NOT NULL, 
    attainment_pct FLOAT NOT NULL, 
    trigger VARCHAR NOT NULL, 
    created_at TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(course_id) REFERENCES courses (id), 
    FOREIGN KEY(outcome_id) REFERENCES course_outcomes (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_outcome_attainment_history_id ON outcome_attainment_history (id);

CREATE TABLE outcome_attainments (
    id SERIAL NOT NULL, 
    user_id INTEGER NOT NULL, 
    course_id INTEGER NOT NULL, 
    outcome_id INTEGER NOT NULL, 
    attainment_percentage FLOAT, 
    status VARCHAR, 
    updated_at TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(course_id) REFERENCES courses (id), 
    FOREIGN KEY(outcome_id) REFERENCES course_outcomes (id), 
    FOREIGN KEY(user_id) REFERENCES users (id), 
    CONSTRAINT uq_user_course_outcome UNIQUE (user_id, course_id, outcome_id)
);

CREATE INDEX ix_outcome_attainments_id ON outcome_attainments (id);

CREATE TABLE question_bank (
    id SERIAL NOT NULL, 
    course_id INTEGER NOT NULL, 
    topic_id INTEGER NOT NULL, 
    outcome_id INTEGER, 
    sub_concept VARCHAR, 
    difficulty VARCHAR, 
    question_type VARCHAR, 
    question_text TEXT NOT NULL, 
    code_snippet TEXT, 
    options_json TEXT NOT NULL, 
    correct_answer VARCHAR NOT NULL, 
    explanation TEXT NOT NULL, 
    bloom_level VARCHAR, 
    PRIMARY KEY (id), 
    FOREIGN KEY(course_id) REFERENCES courses (id), 
    FOREIGN KEY(outcome_id) REFERENCES course_outcomes (id), 
    FOREIGN KEY(topic_id) REFERENCES topics (id)
);

CREATE INDEX ix_question_bank_id ON question_bank (id);

CREATE TABLE quiz_attempts (
    id SERIAL NOT NULL, 
    user_id INTEGER NOT NULL, 
    topic_id INTEGER NOT NULL, 
    score INTEGER NOT NULL, 
    max_score INTEGER, 
    percentage FLOAT NOT NULL, 
    passed BOOLEAN, 
    answers_json TEXT, 
    created_at TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(topic_id) REFERENCES topics (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_quiz_attempts_id ON quiz_attempts (id);

CREATE TABLE resources (
    id SERIAL NOT NULL, 
    topic_id INTEGER NOT NULL, 
    title VARCHAR NOT NULL, 
    url VARCHAR NOT NULL, 
    resource_type VARCHAR, 
    approved_by_faculty BOOLEAN, 
    website_name VARCHAR, 
    description TEXT, 
    difficulty VARCHAR, 
    PRIMARY KEY (id), 
    FOREIGN KEY(topic_id) REFERENCES topics (id)
);

CREATE INDEX ix_resources_id ON resources (id);

CREATE TABLE topic_outcome_mappings (
    id SERIAL NOT NULL, 
    topic_id INTEGER NOT NULL, 
    outcome_id INTEGER NOT NULL, 
    weight FLOAT, 
    PRIMARY KEY (id), 
    FOREIGN KEY(outcome_id) REFERENCES course_outcomes (id), 
    FOREIGN KEY(topic_id) REFERENCES topics (id)
);

CREATE INDEX ix_topic_outcome_mappings_id ON topic_outcome_mappings (id);

CREATE TABLE topic_prerequisites (
    id SERIAL NOT NULL, 
    topic_id INTEGER NOT NULL, 
    prerequisite_topic_id INTEGER NOT NULL, 
    required_mastery_pct FLOAT, 
    PRIMARY KEY (id), 
    FOREIGN KEY(prerequisite_topic_id) REFERENCES topics (id), 
    FOREIGN KEY(topic_id) REFERENCES topics (id)
);

CREATE INDEX ix_topic_prerequisites_id ON topic_prerequisites (id);

CREATE TABLE question_answer_history (
    id SERIAL NOT NULL, 
    attempt_id INTEGER NOT NULL, 
    user_id INTEGER NOT NULL, 
    question_id INTEGER, 
    concept VARCHAR, 
    selected_answer VARCHAR NOT NULL, 
    is_correct BOOLEAN NOT NULL, 
    created_at TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(attempt_id) REFERENCES assessment_attempts (id), 
    FOREIGN KEY(question_id) REFERENCES question_bank (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_question_answer_history_id ON question_answer_history (id);

INSERT INTO alembic_version (version_num) VALUES ('2eff8e0f240d') RETURNING alembic_version.version_num;

-- Running upgrade 2eff8e0f240d -> 3a1b2c4d5e6f

CREATE TABLE class_resources (
    id SERIAL NOT NULL, 
    class_id INTEGER NOT NULL, 
    created_by INTEGER NOT NULL, 
    title VARCHAR(150) NOT NULL, 
    description TEXT, 
    url VARCHAR(500) NOT NULL, 
    resource_type VARCHAR(50) NOT NULL, 
    topic_id INTEGER, 
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    is_deleted BOOLEAN DEFAULT false NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(class_id) REFERENCES classes (id) ON DELETE CASCADE, 
    FOREIGN KEY(created_by) REFERENCES users (id), 
    FOREIGN KEY(topic_id) REFERENCES topics (id) ON DELETE SET NULL
);

CREATE INDEX ix_class_resources_id ON class_resources (id);

CREATE INDEX ix_class_resources_class_id ON class_resources (class_id);

CREATE TABLE class_announcements (
    id SERIAL NOT NULL, 
    class_id INTEGER NOT NULL, 
    created_by INTEGER NOT NULL, 
    title VARCHAR(150) NOT NULL, 
    body TEXT NOT NULL, 
    pinned BOOLEAN DEFAULT false NOT NULL, 
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    is_deleted BOOLEAN DEFAULT false NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(class_id) REFERENCES classes (id) ON DELETE CASCADE, 
    FOREIGN KEY(created_by) REFERENCES users (id)
);

CREATE INDEX ix_class_announcements_id ON class_announcements (id);

CREATE INDEX ix_class_announcements_class_id ON class_announcements (class_id);

CREATE TABLE announcement_reads (
    announcement_id INTEGER NOT NULL, 
    student_id INTEGER NOT NULL, 
    read_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    PRIMARY KEY (announcement_id, student_id), 
    FOREIGN KEY(announcement_id) REFERENCES class_announcements (id) ON DELETE CASCADE, 
    FOREIGN KEY(student_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE class_doubts (
    id SERIAL NOT NULL, 
    class_id INTEGER NOT NULL, 
    student_id INTEGER NOT NULL, 
    topic_id INTEGER, 
    title VARCHAR(150) NOT NULL, 
    body TEXT NOT NULL, 
    visibility VARCHAR(20) DEFAULT 'private' NOT NULL, 
    status VARCHAR(20) DEFAULT 'open' NOT NULL, 
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(class_id) REFERENCES classes (id) ON DELETE CASCADE, 
    FOREIGN KEY(student_id) REFERENCES users (id), 
    FOREIGN KEY(topic_id) REFERENCES topics (id) ON DELETE SET NULL
);

CREATE INDEX ix_class_doubts_id ON class_doubts (id);

CREATE INDEX ix_class_doubts_class_id ON class_doubts (class_id);

CREATE TABLE class_doubt_replies (
    id SERIAL NOT NULL, 
    doubt_id INTEGER NOT NULL, 
    author_id INTEGER NOT NULL, 
    body TEXT NOT NULL, 
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    is_deleted BOOLEAN DEFAULT false NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(author_id) REFERENCES users (id), 
    FOREIGN KEY(doubt_id) REFERENCES class_doubts (id) ON DELETE CASCADE
);

CREATE INDEX ix_class_doubt_replies_id ON class_doubt_replies (id);

CREATE INDEX ix_class_doubt_replies_doubt_id ON class_doubt_replies (doubt_id);

UPDATE alembic_version SET version_num='3a1b2c4d5e6f' WHERE alembic_version.version_num = '2eff8e0f240d';

COMMIT;

