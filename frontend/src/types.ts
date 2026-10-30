export type UserRole = 'student' | 'faculty' | 'admin';

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  must_change_password?: boolean;
}

export interface FacultyAccount {
  id: number;
  email: string;
  full_name: string;
  role: string;
  must_change_password: boolean;
  created_at?: string;
}

export interface StudentProfile {
  id: number;
  user_id: number;
  full_name?: string;
  email?: string;
  student_id?: string;
  program?: string;
  semester?: number;
  year?: string;
  current_level?: string;
  academic_level: string;
  selected_course_id: number | null;
  learning_goal: string;
  prior_knowledge: string;
  preferred_format: string;
  daily_time_minutes: number;
  target_completion_date: string;
  department?: string;
  onboarding_completed?: boolean;
  diagnostic_completed: boolean;
}

export interface SubConceptScore {
  name: string;
  score: number;
  status: 'Understood' | 'Needs Attention' | 'Weak';
  details?: string;
}

export interface TreeTraversalErrorAnalysis {
  basic_traversal_score: number;
  recursive_traversal_score: number;
  diagnosis: string;
  pinpointed_issue: string;
  recommendation: string;
}

export interface PrerequisiteVerificationResult {
  prerequisite: string;
  score_pct: number;
  gap_confirmed: boolean;
  evidence_summary: string;
  recommended_action: string;
}

export interface ReassessmentResult {
  success: boolean;
  reassessment: {
    recursion: { before: number; after: number; status: string };
    recursive_tree_traversal: { before: number; after: number; status: string };
  };
  co2_check: {
    outcome_code: string;
    description: string;
    attainment_pct: number;
    status: string;
    required_concepts: { name: string; status: string; score: number }[];
  };
}

export interface CourseOutcome {
  id: number;
  course_id: number;
  code: string;
  description: string;
  target_attainment_pct: number;
}

export interface TopicResource {
  id: number | string;
  title: string;
  url: string;
  type?: string;
  resource_type?: string;
  website_name?: string;
  description?: string;
  difficulty?: string;
  approved_by_faculty?: boolean;
}

export interface Topic {
  id: number;
  course_id: number;
  code: string;
  title: string;
  order_index: number;
  description: string;
  learning_objective: string;
  difficulty: 'Beginner' | 'Intermediate' | 'Advanced';
  est_minutes: number;
  prerequisites: number[];
  outcomes: string[];
  resources?: TopicResource[];
}

export interface Course {
  id: number;
  code: string;
  title: string;
  description: string;
  category: string;
  level: string;
  is_active: boolean;
  outcome_count?: number;
  topic_count?: number;
  outcomes?: CourseOutcome[];
  topics?: Topic[];
}

export interface DiagnosticQuestion {
  id: number;
  course_id: number;
  topic_id: number;
  topic_title: string;
  question_text: string;
  code_snippet: string | null;
  question_type: 'mcq' | 'output_prediction' | 'code_logic';
  options: string[];
}

export interface DiagnosticAnswer {
  question_id: number;
  selected_answer: string;
}

export interface TopicScore {
  topic_id: number;
  title: string;
  score: number;
}

export interface DiagnosticResult {
  overall_score: number;
  total_questions: number;
  correct_answers: number;
  strengths: TopicScore[];
  weaknesses: TopicScore[];
  question_results: {
    question_id: number;
    topic_id: number;
    topic_title: string;
    question_text: string;
    selected_answer: string;
    correct_answer: string;
    is_correct: boolean;
    explanation: string;
  }[];
}

export interface MasteryScore {
  topic_id: number;
  topic_title: string;
  topic_code: string;
  order_index?: number;
  diagnostic_score: number;
  quiz_score: number;
  practice_score: number;
  completion_score: number;
  overall_mastery: number;
  classification: 'Needs Improvement' | 'Developing' | 'Proficient' | 'Mastered';
}

export type TopicPathStatus = 'COMPLETED' | 'CURRENT' | 'RECOMMENDED' | 'NEEDS REVISION' | 'LOCKED';

export interface LearningPathItem {
  id: number;
  sequence_order: number;
  topic_id: number;
  topic_title: string;
  topic_code: string;
  difficulty: string;
  est_minutes: number;
  status: TopicPathStatus;
  recommendation_reason: string;
  related_outcomes: string[];
  prerequisites: string[];
  mastery_percentage: number;
  mastery_score?: number;
  is_remedial: boolean;
  remedial_title?: string;
  remedial_description?: string;
  action?: string;
  classification?: string;
}

export interface LearningPath {
  id: number;
  course_id: number;
  course_title: string;
  status: string;
  adaptation_reason: string;
  generated_at: string;
  updated_at: string;
  items: LearningPathItem[];
}

export interface QuizQuestion {
  id: number;
  question: string;
  code: string | null;
  options: string[];
}

export interface QuizSubmissionResponse {
  score: number;
  max_score: number;
  percentage: number;
  passed: boolean;
  new_mastery: number;
  classification: string;
  feedback: string;
  path_adapted: boolean;
  adaptation_message: string;
  trigger: string;
  details: {
    id: number;
    question: string;
    user_answer: string;
    correct_answer: string;
    is_correct: boolean;
    explanation: string;
  }[];
}

export interface AgentLog {
  id: number;
  agent_name: string;
  action: string;
  message: string;
  created_at: string;
}

export interface OutcomeAttainment {
  outcome_id: number;
  code: string;
  description: string;
  target_pct: number;
  attainment_percentage: number;
  status: 'Achieved' | 'In Progress' | 'Needs Improvement' | 'Not Started';
  contributing_topics: {
    topic_id: number;
    title: string;
    code: string;
    mastery: number;
    classification: string;
  }[];
  evidence: {
    contributing_topics_count: number;
    average_topic_mastery: number;
    target_threshold_met: boolean;
  };
}

export interface KnowledgeNode {
  id: string;
  label: string;
  code: string;
  order: number;
  mastery: number;
  color: string;
  state_label: string;
  status: string;
  outcomes: string[];
  prerequisites: string[];
  difficulty: string;
}

export interface KnowledgeEdge {
  from: string;
  to: string;
  label: string;
}

export interface KnowledgeGraphData {
  nodes: KnowledgeNode[];
  edges: KnowledgeEdge[];
}

export interface PrerequisiteDetail {
  topic_id: number;
  title: string;
  code: string;
  required_mastery: number;
  current_mastery: number;
  is_satisfied: boolean;
}

export interface CentralStudentTopic {
  topic_id: number;
  title: string;
  code: string;
  order_index: number;
  difficulty: string;
  est_minutes: number;
  mastery: number;
  classification: 'MASTERED' | 'DEVELOPING' | 'NEEDS PRACTICE' | 'WEAK';
  status: TopicPathStatus;
  is_locked: boolean;
  prerequisites: string[];
  unsatisfied_prerequisites: string[];
  prerequisite_details?: PrerequisiteDetail[];
  outcomes: string[];
  action: string;
}

export interface CentralCourseOutcome {
  outcome_id: number;
  code: string;
  description: string;
  target_pct: number;
  attainment_percentage: number;
  status: string;
  contributing_topics: {
    topic_id: number;
    title: string;
    code: string;
    mastery: number;
    status: string;
  }[];
  weak_areas: string[];
  remediation: string;
}

export interface AssessmentAttemptRecord {
  id: number;
  attempt_uuid: string;
  attempt_type: string;
  score: number;
  max_score: number;
  percentage: number;
  passed: boolean;
  topic_id?: number | null;
  created_at: string;
}

export interface CentralStudentState {
  studentProfile: StudentProfile;
  enrolledCourse: {
    id: number;
    code: string;
    title: string;
    description: string;
  };
  overallProgress: number;
  overallMastery: number;
  overallOBEAttainment: number;
  topicsMastered: string;
  masteredCount: number;
  totalTopics: number;
  courseCompleted?: boolean;
  studyTimeHours: number;
  currentTargetTopic: CentralStudentTopic | null;
  aiRecommendation: string;
  topicMastery: CentralStudentTopic[];
  courseOutcomeAttainment: CentralCourseOutcome[];
  learningPath: {
    id: number | null;
    status: string;
    adaptation_reason: string;
    items: (LearningPathItem & { action?: string; classification?: string })[];
  };
  assessmentResults: AssessmentAttemptRecord[];
  latestDiagnostic: {
    completed: boolean;
    score: number;
    attempt_uuid: string | null;
  };
}

export interface AdaptivePracticeQuestion {
  id: number;
  course_id: number;
  topic_id: number;
  topic_title: string;
  sub_concept?: string;
  outcome_id?: number;
  outcome_code?: string;
  difficulty: string;
  question_type: string;
  question_text: string;
  code_snippet?: string | null;
  options: string[];
  explanation?: string;
}

export interface QuestionEvaluationDetail {
  question_id: number;
  topic_id: number;
  topic_title?: string;
  sub_concept?: string;
  difficulty?: string;
  outcome_id?: number;
  outcome_code?: string;
  question_text: string;
  selected_answer: string;
  correct_answer: string;
  is_correct: boolean;
  explanation: string;
}

export interface CodingTestCase {
  call: string;
  expected: string;
  input_desc?: string;
}

export interface CodingChallenge {
  id?: string;
  course_id?: number;
  topic_id?: number;
  topic_title?: string;
  title?: string;
  difficulty?: string;
  outcome_code?: string;
  description?: string;
  starter_code?: string;
  test_cases?: CodingTestCase[];
  has_coding?: boolean;
  message?: string;
}

export interface CodeTestCaseResult {
  test_idx: number;
  call: string;
  input_desc: string;
  expected: string;
  actual: string | null;
  passed: boolean;
  error?: string | null;
}

export interface CodeExecutionResult {
  success: boolean;
  all_passed: boolean;
  passed_count: number;
  total_count: number;
  percentage: number;
  stdout: string;
  stderr: string;
  results: CodeTestCaseResult[];
  execution_time_ms: number;
  self_verified?: boolean;
}

export interface CodingSubmission {
  challenge_id: string;
  title?: string;
  topic_id?: number;
  code: string;
  passed_count: number;
  total_count: number;
  percentage: number;
  all_passed: boolean;
  results: CodeTestCaseResult[];
  execution_time_ms?: number;
  stdout?: string;
  stderr?: string;
  self_verified?: boolean;
}

export interface AssessmentEvaluationResult {
  attempt_uuid: string;
  attempt_type: string;
  score: number;
  max_score: number;
  mcq_score?: number;
  mcq_total?: number;
  percentage: number;
  passed: boolean;
  pass_mark?: number;
  topic_scores: Record<string, number>;
  updated_masteries: Record<string, any>;
  primary_mastery?: {
    topic_id: number;
    topic_title?: string;
    previous_mastery: number;
    new_mastery: number;
    classification: string;
    activity_type: string;
  };
  new_mastery?: number;
  topic_status?: string;
  next_topic?: {
    id: number;
    title: string;
    status: string;
  } | null;
  course_completed?: boolean;
  question_details: QuestionEvaluationDetail[];
  per_question_results?: QuestionEvaluationDetail[];
  coding_result?: CodingSubmission | null;
  state?: CentralStudentState;
  [key: string]: any;
}

export interface ClassInfo {
  id: number;
  faculty_id: number;
  course_id: number;
  course_code?: string;
  course_title?: string;
  name: string;
  class_code: string;
  is_active: boolean;
  max_students?: number | null;
  expires_at?: string | null;
  created_at: string;
  active_students_count: number;
}

export interface ClassStudent {
  id: number;
  name: string;
  email: string;
  joined_at: string | null;
  current_overall_mastery: number;
  completed_topics: string;
  completed_topics_count: number;
  total_topics_count: number;
  baseline_completed_topics: number;
  progress_summary: string;
  improvement_since_join: number;
}

export interface ClassStudentsResponse {
  class_id: number;
  class_name: string;
  course_id: number;
  total_active_students: number;
  students: ClassStudent[];
}

export interface ClassPreviewInfo {
  class_id: number;
  class_name: string;
  class_code: string;
  course_id: number;
  course_title: string;
  course_code: string;
  teacher_name: string;
  consent_text: string;
}

export interface StudentEnrolledClass {
  enrollment_id: number;
  class_id: number;
  name: string;
  class_code: string;
  course_id: number;
  course_title: string;
  course_code: string;
  teacher_name: string;
  joined_at: string | null;
  baseline_completed_topics: number;
}

// ==============================================================================
// STEP 2C: FACULTY DASHBOARD VIEWS TYPES
// ==============================================================================

export interface FacultyThresholds {
  prereq_unlock: number;
  assessment_pass: number;
  topic_mastery: number;
  co_achieved_default: number;
  at_risk_mastery: number;
  inactive_days: number;
}

export interface ClassOverviewOutcome {
  outcome_id: number;
  code: string;
  description: string;
  class_avg_attainment: number;
  target_attainment_pct: number;
  achieved_count: number;
  total_students: number;
  achieved_ratio: string;
}

export interface ClassOverviewTopicMastery {
  topic_id: number;
  code: string;
  title: string;
  order_index: number;
  avg_mastery: number;
  at_risk_count: number;
}

export interface ClassCompletionDistribution {
  completed_topics: number;
  student_count: number;
}

export interface ClassTopLearningGap {
  topic_id: number;
  code: string;
  title: string;
  order_index: number;
  avg_mastery: number;
}

export interface ClassOverview {
  class_id: number;
  class_name: string;
  course: {
    id: number;
    code: string;
    title: string;
    description: string;
  };
  active_students_count: number;
  average_overall_mastery: number;
  at_risk_count: number;
  thresholds: FacultyThresholds;
  outcomes: ClassOverviewOutcome[];
  topic_masteries: ClassOverviewTopicMastery[];
  completion_distribution: ClassCompletionDistribution[];
  top_learning_gaps: ClassTopLearningGap[];
}

export interface OutcomeContributingTopic {
  topic_id: number;
  code: string;
  title: string;
  weight: number;
  class_avg_mastery: number;
}

export interface ConceptMasteryCell {
  topic_id: number;
  code: string;
  title: string;
  mastery_score: number;
}

export interface OutcomeStudentRow {
  student_id: number;
  student_name: string;
  student_email: string;
  co_attainment_pct: number;
  is_achieved: boolean;
  concept_mastery: ConceptMasteryCell[];
}

export interface ClassOutcomeDrilldown {
  class_id: number;
  class_name: string;
  outcome: {
    id: number;
    code: string;
    description: string;
    target_attainment_pct: number;
  };
  class_avg_attainment: number;
  achieved_count: number;
  total_students: number;
  achieved_ratio: string;
  contributing_topics: OutcomeContributingTopic[];
  thresholds: FacultyThresholds;
  student_rows: OutcomeStudentRow[];
}

export interface StudentCOAttainmentItem {
  outcome_id: number;
  code: string;
  description: string;
  attainment_pct: number;
  target_pct: number;
  is_achieved: boolean;
}

export interface ExtendedClassStudent {
  id: number;
  name: string;
  email: string;
  joined_at: string | null;
  current_overall_mastery: number;
  completed_topics: string;
  completed_topics_count: number;
  total_topics_count: number;
  baseline_completed_topics: number;
  progress_summary: string;
  improvement_since_join: number;
  co_attainments: StudentCOAttainmentItem[];
  diagnostic_score: number | null;
  last_activity_date: string | null;
  is_at_risk: boolean;
  at_risk_reasons: string[];
  current_topic?: {
    id: number;
    title: string;
    code: string;
  } | null;
}

export interface ExtendedClassStudentsResponse {
  class_id: number;
  class_name: string;
  course_id: number;
  total_active_students: number;
  thresholds: FacultyThresholds;
  students: ExtendedClassStudent[];
}

export interface StudentTopicProgress {
  topic_id: number;
  code: string;
  title: string;
  order_index: number;
  overall_mastery: number;
  quiz_score: number;
  practice_score: number;
  completion_score: number;
  status: 'completed' | 'current' | 'locked' | 'recommended' | string;
  is_completed: boolean;
}

export interface StudentOutcomeDelta {
  outcome_id: number;
  code: string;
  description: string;
  current_attainment: number;
  baseline_attainment: number;
  delta: number;
  target_pct: number;
  is_achieved: boolean;
}

export interface StudentRecentAttempt {
  id: number;
  topic_id: number | null;
  topic_title: string;
  topic_code: string;
  attempt_type: string;
  score: number;
  max_score: number;
  percentage: number;
  passed: boolean;
  created_at: string | null;
}

export interface StudentPrerequisiteGap {
  topic_id: number;
  topic_title: string;
  prereq_id: number;
  prereq_title: string;
  current_mastery: number;
  required_mastery: number;
  gap: number;
}

export interface ClassStudentDetail {
  student: {
    id: number;
    name: string;
    email: string;
    joined_at: string | null;
    baseline_completed_topics: number;
    progress_summary: string;
    improvement_since_join: number;
  };
  class_id: number;
  class_name: string;
  course_id: number;
  current_overall_mastery: number;
  completed_topics_count: number;
  total_topics_count: number;
  diagnostic_score: number | null;
  last_activity_date: string | null;
  is_at_risk: boolean;
  at_risk_reasons: string[];
  thresholds: FacultyThresholds;
  topics: StudentTopicProgress[];
  completed_topics: StudentTopicProgress[];
  incomplete_topics: StudentTopicProgress[];
  outcomes: StudentOutcomeDelta[];
  recent_attempts: StudentRecentAttempt[];
  prerequisite_gaps: StudentPrerequisiteGap[];
  assessment_summary?: AssessmentSummary;
  weakest_concepts?: WeakestConcept[];
}

export interface AssessmentSummary {
  initial_diagnostic_score: number | null;
  initial_practice_score: number | null;
  latest_score: number | null;
  best_score: number | null;
  reassessment_scores: number[];
  total_attempts: number;
  reassessment_count: number;
  improvement_delta: number | null;
  has_enough_data: boolean;
}

export interface WeakestConcept {
  concept: string;
  accuracy_pct: number;
  total_questions: number;
  correct_count: number;
  is_struggling: boolean;
}

export interface StudentLearningPathItemView {
  id: number;
  sequence_order: number;
  topic_id: number;
  topic_title: string;
  topic_code: string;
  difficulty: string;
  status: string;
  recommendation_reason: string;
  is_remedial: boolean;
  remedial_title: string | null;
  remedial_description: string | null;
}

export interface ClassStudentLearningPath {
  student_id: number;
  class_id: number;
  course_id: number;
  learning_path_id: number | null;
  status: string;
  adaptation_reason: string;
  generated_at: string | null;
  updated_at: string | null;
  items: StudentLearningPathItemView[];
}

// ==============================================================================
// STEP 2D FACULTY INTERFACES (ASSESSMENTS, GAPS, IMPACT)
// ==============================================================================

export interface ClassAssessmentTopicScore {
  topic_id: number;
  topic_code: string;
  topic_title: string;
  first_score: number | null;
  latest_score: number | null;
  best_score: number | null;
  attempts_count: number;
  improvement_delta: number | null;
}

export interface ClassAssessmentStudent {
  student_id: number;
  name: string;
  email: string;
  initial_diagnostic_score: number | null;
  initial_score: number | null;
  latest_score: number | null;
  best_score: number | null;
  improvement_delta: number | null;
  total_attempts_count: number;
  reassessments_count: number;
  reassessment_scores: number[];
  per_topic: ClassAssessmentTopicScore[];
}

export interface ClassAssessmentsResponse {
  class_id: number;
  class_name: string;
  course_id: number;
  total_students: number;
  class_initial_avg: number | null;
  class_latest_avg: number | null;
  class_avg_improvement: number | null;
  students: ClassAssessmentStudent[];
}

export interface ConceptGapItem {
  gap_key: string;
  gap_type: 'concept';
  concept: string;
  topic_id: number | null;
  topic_title: string;
  avg_score: number;
  attempts_count: number;
  students_affected_count: number;
  pct_students_affected: number;
  is_common_gap: boolean;
}

export interface PrerequisiteGapItem {
  gap_key: string;
  gap_type: 'prerequisite';
  prereq_topic_id: number;
  prereq_topic_title: string;
  prereq_topic_code: string;
  dependent_topic_id: number;
  dependent_topic_title: string;
  dependent_topic_code: string;
  required_mastery: number;
  students_affected_count: number;
  pct_students_affected: number;
  is_common_gap: boolean;
}

export type CommonClassGapItem = ConceptGapItem | PrerequisiteGapItem;

export interface ClassGapsResponse {
  class_id: number;
  class_name: string;
  course_id: number;
  total_students: number;
  concept_gaps: ConceptGapItem[];
  prerequisite_gaps: PrerequisiteGapItem[];
  common_class_gaps: CommonClassGapItem[];
  thresholds: {
    ASSESSMENT_PASS: number;
    PREREQ_UNLOCK: number;
    COMMON_GAP_PCT: number;
  };
}

export interface GapAffectedStudent {
  student_id: number;
  name: string;
  email: string;
  score?: number;
  mastery?: number;
  threshold: number;
  gap?: number;
  status: string;
  attempts_count?: number;
}

export interface GapDrilldownResponse {
  class_id: number;
  gap_key: string;
  gap_title: string;
  total_affected: number;
  affected_students: GapAffectedStudent[];
}

export interface ClassImpactStudentSummary {
  student_id: number;
  name: string;
  email: string;
  baseline_co_avg: number;
  current_co_avg: number;
  delta: number;
  status: 'improved' | 'unchanged' | 'declined';
}

export interface ClassImpactSummary {
  class_id: number;
  class_name: string;
  course_id: number;
  total_students: number;
  avg_co_delta_since_joining: number;
  improved_count: number;
  unchanged_count: number;
  declined_count: number;
  has_enough_data: boolean;
  students_summary: ClassImpactStudentSummary[];
}

export interface ImpactTimelinePoint {
  date: string;
  trigger: string;
  outcome_id: number;
  outcome_code: string;
  attainment_pct: number;
}

export interface InterventionEventItem {
  id: number;
  type: 'remedial_inserted' | 'path_adapted' | 'teacher_flag' | 'class_joined' | string;
  topic_id: number | null;
  created_at: string;
  note: string | null;
}

export interface BeforeAfterComparison {
  intervention_id: number;
  type: string;
  date: string;
  note: string | null;
  co_before_avg: number | null;
  co_after_avg: number | null;
  co_delta: number | null;
  mastery_before_avg: number | null;
  mastery_after_avg: number | null;
  mastery_delta: number | null;
}

export interface StudentImpactResponse {
  student_id: number;
  student_name: string;
  class_id: number;
  course_id: number;
  joined_at: string | null;
  baseline_co_avg: number;
  current_co_avg: number;
  overall_co_delta: number;
  has_enough_data: boolean;
  attribution_notice: string;
  timeline: ImpactTimelinePoint[];
  interventions: InterventionEventItem[];
  before_after_comparisons: BeforeAfterComparison[];
}

// ==============================================================================
// CLASS COMMUNICATION FEATURES (Resources, Announcements, Doubts)
// ==============================================================================

export type ClassResourceType = 'video' | 'article' | 'notes' | 'practice' | 'other';

export interface ClassResource {
  id: number;
  class_id: number;
  created_by: number;
  title: string;
  description?: string | null;
  url: string;
  resource_type: ClassResourceType;
  topic_id?: number | null;
  topic_title?: string | null;
  created_at: string;
  is_deleted?: boolean;
}

export interface ClassResourceCreatePayload {
  title: string;
  description?: string;
  url: string;
  resource_type: ClassResourceType;
  topic_id?: number | null;
}

export interface ClassAnnouncement {
  id: number;
  class_id: number;
  created_by: number;
  title: string;
  body: string;
  pinned: boolean;
  created_at: string;
  is_deleted?: boolean;
  is_read?: boolean;
}

export interface ClassAnnouncementCreatePayload {
  title: string;
  body: string;
  pinned?: boolean;
}

export interface ClassDoubtReply {
  id: number;
  doubt_id: number;
  author_id: number;
  author_name: string;
  author_role: string;
  body: string;
  created_at: string;
  is_deleted?: boolean;
}

export interface ClassDoubtReplyCreatePayload {
  body: string;
}

export type DoubtVisibility = 'private' | 'class';
export type DoubtStatus = 'open' | 'answered' | 'closed';

export interface ClassDoubt {
  id: number;
  class_id: number;
  student_id: number;
  title: string;
  body: string;
  visibility: DoubtVisibility;
  status: DoubtStatus;
  topic_id?: number | null;
  topic_title?: string | null;
  created_at: string;
  author_name: string;
  is_my_doubt?: boolean;
  replies: ClassDoubtReply[];
}

export interface ClassDoubtCreatePayload {
  title: string;
  body: string;
  topic_id?: number | null;
  visibility?: DoubtVisibility;
}



