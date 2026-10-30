import {
  User, StudentProfile, Course, Topic, TopicResource, DiagnosticQuestion, DiagnosticResult,
  MasteryScore, LearningPath, QuizQuestion, QuizSubmissionResponse,
  AgentLog, OutcomeAttainment, KnowledgeGraphData, CentralStudentState,
  CodingChallenge, CodeExecutionResult, FacultyAccount,
  ClassInfo, ClassStudentsResponse, ClassPreviewInfo, StudentEnrolledClass,
  ClassOverview, ClassOutcomeDrilldown, ClassStudentDetail,
  ClassStudentLearningPath, ExtendedClassStudentsResponse,
  ClassAssessmentsResponse, ClassGapsResponse, GapDrilldownResponse,
  ClassImpactSummary, StudentImpactResponse,
  ClassResource, ClassResourceCreatePayload, ClassAnnouncement, ClassAnnouncementCreatePayload,
  ClassDoubt, ClassDoubtCreatePayload, ClassDoubtReply, ClassDoubtReplyCreatePayload
} from '../types';

// Single canonical environment variable for backend API endpoint: VITE_API_URL
// Safely handles '/api', 'https://host', 'https://host/api', with or without trailing slash
export const resolveApiBase = (): string => {
  const raw = (import.meta.env.VITE_API_URL || '/api').trim().replace(/\/+$/, '');
  if (!raw) return '/api';
  if (raw === '/api' || raw.endsWith('/api')) {
    return raw;
  }
  return `${raw}/api`;
};

const API_BASE = resolveApiBase();

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  try {
    const authHeader: Record<string, string> = {};
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('obepath_token');
      if (token) {
        authHeader['Authorization'] = `Bearer ${token}`;
      }
    }

    const res = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...authHeader,
        ...(options?.headers || {})
      }
    });

    if (res.status === 401) {
      const err = await res.json().catch(() => ({ detail: 'Unauthorized session' }));
      if (typeof window !== 'undefined') {
        localStorage.removeItem('obepath_token');
        localStorage.removeItem('obepath_current_user');
        window.dispatchEvent(new CustomEvent('obepath_unauthorized', { detail: err.detail }));
      }
      throw new Error(err.detail || 'Unauthorized session');
    }

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Request failed');
    }
    return await res.json();
  } catch (err: any) {
    if (err?.name === 'AbortError') {
      throw err;
    }
    console.error(`API Error on ${url}:`, err);
    throw err;
  }
}

export const api = {
  // Auth
  getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('obepath_token');
  },

  logout(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('obepath_token');
      localStorage.removeItem('obepath_current_user');
      window.dispatchEvent(new CustomEvent('obepath_unauthorized'));
    }
  },

  async login(email: string, password: string, role = 'student', expectedRole?: string): Promise<{ user: User; token: string; is_new_user?: boolean; onboarding_completed?: boolean }> {
    const res = await fetchJson<{ user: User; token: string; is_new_user?: boolean; onboarding_completed?: boolean }>(`${API_BASE}/auth/login`, {
      method: 'POST',
      body: JSON.stringify({ email, password, role, expected_role: expectedRole || role })
    });
    if (res?.token && typeof window !== 'undefined') {
      localStorage.setItem('obepath_token', res.token);
    }
    return res;
  },

  async register(email: string, password: string, fullName: string, role = 'student'): Promise<{ user: User; token: string; is_new_user?: boolean; onboarding_completed?: boolean }> {
    const res = await fetchJson<{ user: User; token: string; is_new_user?: boolean; onboarding_completed?: boolean }>(`${API_BASE}/auth/register`, {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name: fullName, role })
    });
    if (res?.token && typeof window !== 'undefined') {
      localStorage.setItem('obepath_token', res.token);
    }
    return res;
  },

  async loginWithGoogle(credential: string): Promise<{ user: User; token: string; is_new_user?: boolean; onboarding_completed?: boolean }> {
    const res = await fetchJson<{ user: User; token: string; is_new_user?: boolean; onboarding_completed?: boolean }>(`${API_BASE}/auth/google`, {
      method: 'POST',
      body: JSON.stringify({ credential })
    });
    if (res?.token && typeof window !== 'undefined') {
      localStorage.setItem('obepath_token', res.token);
    }
    return res;
  },

  async getAuthMe(): Promise<{ user: User; onboarding_completed: boolean; must_change_password?: boolean }> {
    const raw = await fetchJson<any>(`${API_BASE}/auth/me`);
    const user: User = {
      id: raw.id,
      email: raw.email,
      full_name: raw.name || raw.full_name || '',
      role: raw.role,
      must_change_password: Boolean(raw.must_change_password)
    };
    return {
      user,
      onboarding_completed: Boolean(raw.onboarding_completed),
      must_change_password: Boolean(raw.must_change_password)
    };
  },

  async changePassword(oldPassword: string, newPassword: string): Promise<{ status: string; message: string; must_change_password: boolean }> {
    return fetchJson(`${API_BASE}/auth/change-password`, {
      method: 'POST',
      body: JSON.stringify({
        old_password: oldPassword,
        new_password: newPassword
      })
    });
  },

  // Courses
  async getCourses(): Promise<Course[]> {
    return fetchJson(`${API_BASE}/courses`);
  },

  async getCourse(courseId: number): Promise<Course> {
    return fetchJson(`${API_BASE}/courses/${courseId}`);
  },

  async getTopic(topicId: number | string): Promise<Topic> {
    return fetchJson(`${API_BASE}/topics/${topicId}`);
  },

  async getTopicResources(topicId: number | string): Promise<TopicResource[]> {
    return fetchJson(`${API_BASE}/topics/${topicId}/resources`);
  },

  // Profile
  async getProfile(userId = 1): Promise<StudentProfile> {
    return fetchJson(`${API_BASE}/profile?user_id=${userId}`);
  },

  async updateProfile(profile: Partial<StudentProfile>, userId = 1): Promise<StudentProfile> {
    return fetchJson(`${API_BASE}/profile?user_id=${userId}`, {
      method: 'PUT',
      body: JSON.stringify(profile)
    });
  },

  // Diagnostic
  async getDiagnosticQuestions(courseId: number, signal?: AbortSignal): Promise<DiagnosticQuestion[]> {
    return fetchJson(`${API_BASE}/diagnostic/${courseId}`, { signal });
  },

  async submitDiagnostic(courseId: number, answers: { question_id: number; selected_answer: string }[], userId = 1): Promise<DiagnosticResult> {
    return fetchJson(`${API_BASE}/diagnostic/submit?user_id=${userId}`, {
      method: 'POST',
      body: JSON.stringify({ course_id: courseId, answers })
    });
  },

  // Learning Path
  async getLearningPath(courseId = 1, userId = 1): Promise<LearningPath> {
    return fetchJson(`${API_BASE}/learning-path?course_id=${courseId}&user_id=${userId}`);
  },

  async generateLearningPath(courseId = 1, userId = 1): Promise<LearningPath> {
    return fetchJson(`${API_BASE}/learning-path/generate?course_id=${courseId}&user_id=${userId}`, {
      method: 'POST'
    });
  },

  async reviseLearningPath(failedTopicId = 5, courseId = 1, userId = 1): Promise<LearningPath> {
    return fetchJson(`${API_BASE}/learning-path/revise?failed_topic_id=${failedTopicId}&course_id=${courseId}&user_id=${userId}`, {
      method: 'POST'
    });
  },

  async repairLearningPath(courseId = 1, userId = 1): Promise<LearningPath> {
    return fetchJson(`${API_BASE}/learning-path/repair?course_id=${courseId}&user_id=${userId}`, {
      method: 'POST'
    });
  },

  async getWhyRecommendation(topicId: number, userId = 1): Promise<{
    topic_id: number;
    topic_title: string;
    mastery_score: number;
    prerequisites: string[];
    outcomes: string[];
    explanation: string;
  }> {
    return fetchJson(`${API_BASE}/learning-path/why/${topicId}?user_id=${userId}`);
  },

  // AI Tutor (Gemini Powered)
  async chatWithTutor(
    topicId: number,
    message: string,
    action?: string,
    courseId?: number,
    history?: { role: string; content: string }[],
    userId = 1
  ): Promise<{
    reply: string;
    action_taken: string;
    adapted_for_level: string;
    suggested_followups: string[];
    model_used?: string;
    error?: string;
  }> {
    return fetchJson(`${API_BASE}/ai-tutor/chat?user_id=${userId}`, {
      method: 'POST',
      body: JSON.stringify({
        topic_id: topicId,
        message,
        action,
        course_id: courseId,
        history
      })
    });
  },

  async getTutorStatus(): Promise<{
    status: string;
    gemini_configured: boolean;
    model?: string;
  }> {
    return fetchJson(`${API_BASE}/ai-tutor/status`);
  },

  async generateTopicModality(
    topicId: number,
    modality: string,
    userPrompt?: string,
    pedagogicalStyle?: string,
    userId = 1
  ): Promise<{
    topic_id: number;
    topic_title: string;
    modality: string;
    pedagogical_style: string;
    content_markdown: string;
    key_takeaways: string[];
    code_snippet?: string;
    visual_ascii?: string;
    practice_question?: {
      question: string;
      options: string[];
      correct: string;
      explanation: string;
    };
    suggested_prompts: string[];
  }> {
    return fetchJson(`${API_BASE}/ai-tutor/generate-modality?user_id=${userId}`, {
      method: 'POST',
      body: JSON.stringify({
        topic_id: topicId,
        modality,
        user_prompt: userPrompt,
        pedagogical_style: pedagogicalStyle
      })
    });
  },

  // Assessments & Quiz
  async getTopicQuiz(topicId: number): Promise<QuizQuestion[]> {
    return fetchJson(`${API_BASE}/assessment/quiz/${topicId}`);
  },

  async submitQuiz(topicId: number, score: number, answers?: Record<string, string>, userId = 1): Promise<QuizSubmissionResponse> {
    return fetchJson(`${API_BASE}/assessment/quiz/submit?user_id=${userId}`, {
      method: 'POST',
      body: JSON.stringify({ topic_id: topicId, score, answers })
    });
  },

  async submitPractice(topicId: number, score: number, userId = 1): Promise<any> {
    return fetchJson(`${API_BASE}/assessment/practice/submit?user_id=${userId}`, {
      method: 'POST',
      body: JSON.stringify({ topic_id: topicId, score })
    });
  },

  async completeTopic(topicId: number): Promise<any> {
    return fetchJson(`${API_BASE}/assessment/topic/complete/${topicId}`, {
      method: 'POST'
    });
  },

  async completeRemediation(topicId = 5, userId = 1): Promise<any> {
    return fetchJson(`${API_BASE}/assessment/remediation/complete?topic_id=${topicId}&user_id=${userId}`, {
      method: 'POST'
    });
  },

  // Step 8: Tree Traversal Quiz
  async getTreeTraversalQuiz(): Promise<QuizQuestion[]> {
    return fetchJson(`${API_BASE}/assessment/tree-traversal-quiz`);
  },

  // Step 9: Analyze Tree Traversal Errors
  async analyzeTreeTraversalErrors(answers: Record<string, string>, userId = 1): Promise<{
    basic_traversal_score: number;
    recursive_traversal_score: number;
    diagnosis: string;
    pinpointed_issue: string;
    recommendation: string;
  }> {
    return fetchJson(`${API_BASE}/assessment/tree-traversal/analyze-errors?user_id=${userId}`, {
      method: 'POST',
      body: JSON.stringify({ answers })
    });
  },

  // Step 10: Prerequisite Verification Quiz
  async getPrerequisiteRecursionQuiz(): Promise<QuizQuestion[]> {
    return fetchJson(`${API_BASE}/assessment/prerequisite/recursion`);
  },

  // Step 10: Verify Prerequisite
  async verifyPrerequisite(answers: Record<string, string>, userId = 1): Promise<{
    prerequisite: string;
    score_pct: number;
    gap_confirmed: boolean;
    evidence_summary: string;
    recommended_action: string;
  }> {
    return fetchJson(`${API_BASE}/assessment/prerequisite/verify?user_id=${userId}`, {
      method: 'POST',
      body: JSON.stringify({ answers })
    });
  },

  // Step 13 & 14: Complete Reassessment & check CO2 attainment
  async completeReassessment(courseId = 1, userId = 1): Promise<any> {
    return fetchJson(`${API_BASE}/assessment/reassessment/complete?course_id=${courseId}&user_id=${userId}`, {
      method: 'POST'
    });
  },

  // Mastery & Outcomes
  async getStudentMastery(userId = 1, courseId = 1): Promise<{
    topics: MasteryScore[];
    average_mastery: number;
    topics_mastered: string;
    mastered_count: number;
    total_topics: number;
  }> {
    return fetchJson(`${API_BASE}/mastery/student?user_id=${userId}&course_id=${courseId}`);
  },

  async getOutcomesAttainment(userId = 1, courseId = 1): Promise<{
    outcomes: OutcomeAttainment[];
    overall_attainment: number;
  }> {
    return fetchJson(`${API_BASE}/mastery/outcomes?user_id=${userId}&course_id=${courseId}`);
  },

  async getKnowledgeMap(userId = 1, courseId = 1): Promise<KnowledgeGraphData> {
    return fetchJson(`${API_BASE}/mastery/knowledge-map?user_id=${userId}&course_id=${courseId}`);
  },

  async getAgentLogs(userId = 1, limit = 15): Promise<AgentLog[]> {
    return fetchJson(`${API_BASE}/mastery/agent-logs?user_id=${userId}&limit=${limit}`);
  },

  // Faculty
  async getFacultyDashboard(courseId = 1): Promise<any> {
    return fetchJson(`${API_BASE}/faculty/dashboard?course_id=${courseId}`);
  },

  async getFacultyTopicAnalytics(courseId = 1): Promise<any> {
    return fetchJson(`${API_BASE}/faculty/topic-analytics?course_id=${courseId}`);
  },

  async getFacultyClasses(): Promise<ClassInfo[]> {
    return fetchJson(`${API_BASE}/faculty/classes`);
  },

  async createFacultyClass(payload: {
    course_id: number;
    name: string;
    custom_code?: string;
    max_students?: number;
    expires_at?: string;
  }): Promise<ClassInfo> {
    return fetchJson(`${API_BASE}/faculty/classes`, {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  async regenerateClassCode(classId: number): Promise<{ id: number; class_code: string; message: string }> {
    return fetchJson(`${API_BASE}/faculty/classes/${classId}/regenerate-code`, {
      method: 'POST'
    });
  },

  async disableClassCode(classId: number): Promise<{ id: number; is_active: boolean; message: string }> {
    return fetchJson(`${API_BASE}/faculty/classes/${classId}/disable-code`, {
      method: 'POST'
    });
  },

  async enableClassCode(classId: number): Promise<{ id: number; is_active: boolean; message: string }> {
    return fetchJson(`${API_BASE}/faculty/classes/${classId}/enable-code`, {
      method: 'POST'
    });
  },

  async getClassStudents(classId: number): Promise<ExtendedClassStudentsResponse> {
    return fetchJson(`${API_BASE}/faculty/classes/${classId}/students`);
  },

  async getClassOverview(classId: number): Promise<ClassOverview> {
    return fetchJson(`${API_BASE}/faculty/classes/${classId}/overview`);
  },

  async getClassOutcomeDrilldown(classId: number, outcomeId: number): Promise<ClassOutcomeDrilldown> {
    return fetchJson(`${API_BASE}/faculty/classes/${classId}/outcomes/${outcomeId}`);
  },

  async getClassStudentDetail(classId: number, studentId: number): Promise<ClassStudentDetail> {
    return fetchJson(`${API_BASE}/faculty/classes/${classId}/students/${studentId}`);
  },

  async getClassStudentLearningPath(classId: number, studentId: number): Promise<ClassStudentLearningPath> {
    return fetchJson(`${API_BASE}/faculty/classes/${classId}/students/${studentId}/learning-path`);
  },

  async removeStudentFromClass(classId: number, studentId: number): Promise<{ message: string; student_id: number; class_id: number }> {
    return fetchJson(`${API_BASE}/faculty/classes/${classId}/students/${studentId}`, {
      method: 'DELETE'
    });
  },

  // Step 2D: Assessments, Gaps, and Impact
  async getClassAssessments(classId: number): Promise<ClassAssessmentsResponse> {
    return fetchJson(`${API_BASE}/faculty/classes/${classId}/assessments`);
  },

  async getClassGaps(classId: number): Promise<ClassGapsResponse> {
    return fetchJson(`${API_BASE}/faculty/classes/${classId}/gaps`);
  },

  async getClassGapDrilldown(classId: number, gapKey: string): Promise<GapDrilldownResponse> {
    return fetchJson(`${API_BASE}/faculty/classes/${classId}/gaps/${encodeURIComponent(gapKey)}`);
  },

  async getClassImpactSummary(classId: number): Promise<ClassImpactSummary> {
    return fetchJson(`${API_BASE}/faculty/classes/${classId}/impact-summary`);
  },

  async getClassStudentImpact(classId: number, studentId: number): Promise<StudentImpactResponse> {
    return fetchJson(`${API_BASE}/faculty/classes/${classId}/students/${studentId}/impact`);
  },

  async flagStudentIntervention(classId: number, studentId: number, note: string): Promise<{ success: boolean; event: any }> {
    return fetchJson(`${API_BASE}/faculty/classes/${classId}/students/${studentId}/flag`, {
      method: 'POST',
      body: JSON.stringify({ note })
    });
  },

  // Student Classes
  async previewClass(classCode: string): Promise<ClassPreviewInfo> {
    return fetchJson(`${API_BASE}/student/classes/preview`, {
      method: 'POST',
      body: JSON.stringify({ class_code: classCode })
    });
  },

  async joinClass(classCode: string, acceptConsent = true): Promise<any> {
    return fetchJson(`${API_BASE}/student/classes/join`, {
      method: 'POST',
      body: JSON.stringify({ class_code: classCode, accept_consent: acceptConsent })
    });
  },

  async getStudentClasses(): Promise<StudentEnrolledClass[]> {
    return fetchJson(`${API_BASE}/student/classes`);
  },

  async leaveClass(classId: number): Promise<{ message: string; class_id: number }> {
    return fetchJson(`${API_BASE}/student/classes/${classId}/leave`, {
      method: 'POST'
    });
  },

  // Admin
  async getAdminMetrics(): Promise<any> {
    return fetchJson(`${API_BASE}/admin/metrics`);
  },

  async getAdminLogs(limit = 30): Promise<any> {
    return fetchJson(`${API_BASE}/admin/logs?limit=${limit}`);
  },

  async createFaculty(data: { name: string; email: string; temporary_password: string }): Promise<FacultyAccount> {
    return fetchJson(`${API_BASE}/admin/users`, {
      method: 'POST',
      body: JSON.stringify({
        full_name: data.name,
        email: data.email,
        temporary_password: data.temporary_password
      })
    });
  },

  async getFacultyList(): Promise<FacultyAccount[]> {
    return fetchJson(`${API_BASE}/admin/users?role=faculty`);
  },

  // Central Student State & Progress Engine
  async getStudentState(userId?: number, courseId?: number): Promise<CentralStudentState> {
    const params = new URLSearchParams();
    if (userId) params.append('user_id', String(userId));
    if (courseId) params.append('course_id', String(courseId));
    const q = params.toString() ? `?${params.toString()}` : '';
    return fetchJson(`${API_BASE}/progress/state${q}`);
  },

  async getAdaptiveQuestions(
    courseId: number,
    topicId?: number,
    count = 5,
    attemptType = 'assessment',
    userId?: number,
    signal?: AbortSignal
  ): Promise<any[]> {
    const params = new URLSearchParams();
    params.append('course_id', String(courseId));
    params.append('count', String(count));
    params.append('attempt_type', attemptType);
    if (userId) params.append('user_id', String(userId));
    if (topicId) params.append('topic_id', String(topicId));
    params.append('_t', String(Date.now()));
    return fetchJson(`${API_BASE}/progress/questions?${params.toString()}`, { signal });
  },

  async submitAssessmentAttempt(payload: {
    course_id: number;
    attempt_type: string;
    answers: Record<string, string>;
    topic_id?: number;
    coding_submission?: any;
  }, userId?: number): Promise<{
    evaluation: any;
    state: CentralStudentState;
    score?: number;
    passed?: boolean;
    pass_mark?: number;
    per_question_results?: any[];
    new_mastery?: number;
    topic_status?: string;
    next_topic?: any;
    course_completed?: boolean;
    [key: string]: any;
  }> {
    const url = userId
      ? `${API_BASE}/progress/submit-assessment?user_id=${userId}`
      : `${API_BASE}/progress/submit-assessment`;
    return fetchJson(url, {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  // In-Assessment Coding Challenge & Sandbox Compiler
  async getCodingChallenge(courseId: number, topicId?: number, topicTitle?: string, signal?: AbortSignal): Promise<CodingChallenge> {
    let url = `${API_BASE}/assessment/coding-challenge?course_id=${courseId}`;
    if (topicId) url += `&topic_id=${topicId}`;
    if (topicTitle) url += `&topic_title=${encodeURIComponent(topicTitle)}`;
    return fetchJson(url, { signal });
  },

  async compileAndRunCode(code: string, testCases?: any[], challengeId?: string, timeoutSec = 4.0): Promise<CodeExecutionResult> {
    return fetchJson(`${API_BASE}/assessment/compile-code`, {
      method: 'POST',
      body: JSON.stringify({
        code,
        test_cases: testCases,
        challenge_id: challengeId,
        timeout_sec: timeoutSec
      })
    });
  },

  async simulateActivity(payload: {
    topic_id: number;
    score: number;
    activity_type: string;
    reason?: string;
  }, userId = 1): Promise<{ mastery_update: any; state: CentralStudentState }> {
    return fetchJson(`${API_BASE}/progress/simulate-activity?user_id=${userId}`, {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  async seedDemoJourney(courseId = 2, userId = 1): Promise<CentralStudentState> {
    return fetchJson(`${API_BASE}/progress/seed-demo-journey?user_id=${userId}`, {
      method: 'POST',
      body: JSON.stringify({ course_id: courseId })
    });
  },

  // ==============================================================================
  // CLASS COMMUNICATION API (Resources, Announcements, Doubts)
  // ==============================================================================

  // Faculty Class Resources
  async getFacultyClassResources(classId: number): Promise<ClassResource[]> {
    return fetchJson(`${API_BASE}/faculty/classes/${classId}/resources`);
  },

  async createFacultyClassResource(classId: number, payload: ClassResourceCreatePayload): Promise<ClassResource> {
    return fetchJson(`${API_BASE}/faculty/classes/${classId}/resources`, {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  async deleteFacultyClassResource(classId: number, resourceId: number): Promise<{ message: string }> {
    return fetchJson(`${API_BASE}/faculty/classes/${classId}/resources/${resourceId}`, {
      method: 'DELETE'
    });
  },

  // Faculty Class Announcements
  async getFacultyClassAnnouncements(classId: number): Promise<ClassAnnouncement[]> {
    return fetchJson(`${API_BASE}/faculty/classes/${classId}/announcements`);
  },

  async createFacultyClassAnnouncement(classId: number, payload: ClassAnnouncementCreatePayload): Promise<ClassAnnouncement> {
    return fetchJson(`${API_BASE}/faculty/classes/${classId}/announcements`, {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  async deleteFacultyClassAnnouncement(classId: number, announcementId: number): Promise<{ message: string }> {
    return fetchJson(`${API_BASE}/faculty/classes/${classId}/announcements/${announcementId}`, {
      method: 'DELETE'
    });
  },

  async togglePinClassAnnouncement(classId: number, announcementId: number): Promise<ClassAnnouncement> {
    return fetchJson(`${API_BASE}/faculty/classes/${classId}/announcements/${announcementId}/pin`, {
      method: 'PATCH'
    });
  },

  // Faculty Class Doubts & Replies
  async getFacultyClassDoubts(classId: number, status?: string, topicId?: number): Promise<ClassDoubt[]> {
    const params = new URLSearchParams();
    if (status && status !== 'all') params.append('status', status);
    if (topicId !== undefined && topicId !== null) params.append('topic_id', String(topicId));
    const query = params.toString() ? `?${params.toString()}` : '';
    return fetchJson(`${API_BASE}/faculty/classes/${classId}/doubts${query}`);
  },

  async replyToFacultyClassDoubt(classId: number, doubtId: number, body: string): Promise<ClassDoubtReply> {
    return fetchJson(`${API_BASE}/faculty/classes/${classId}/doubts/${doubtId}/replies`, {
      method: 'POST',
      body: JSON.stringify({ body })
    });
  },

  async closeFacultyClassDoubt(classId: number, doubtId: number): Promise<ClassDoubt> {
    return fetchJson(`${API_BASE}/faculty/classes/${classId}/doubts/${doubtId}/close`, {
      method: 'PATCH'
    });
  },

  async deleteFacultyClassDoubtReply(classId: number, doubtId: number, replyId: number): Promise<{ message: string }> {
    return fetchJson(`${API_BASE}/faculty/classes/${classId}/doubts/${doubtId}/replies/${replyId}`, {
      method: 'DELETE'
    });
  },

  // Student Class Resources
  async getStudentClassResources(classId: number): Promise<ClassResource[]> {
    return fetchJson(`${API_BASE}/student/classes/${classId}/resources`);
  },

  // Student Class Announcements
  async getStudentClassAnnouncements(classId: number): Promise<ClassAnnouncement[]> {
    return fetchJson(`${API_BASE}/student/classes/${classId}/announcements`);
  },

  async markStudentAnnouncementRead(classId: number, announcementId: number): Promise<{ message: string; announcement_id: number }> {
    return fetchJson(`${API_BASE}/student/classes/${classId}/announcements/${announcementId}/read`, {
      method: 'POST'
    });
  },

  async getStudentUnreadAnnouncementsCount(classId: number): Promise<{ class_id: number; unread_count: number }> {
    return fetchJson(`${API_BASE}/student/classes/${classId}/announcements/unread-count`);
  },

  // Student Class Doubts
  async askStudentClassDoubt(classId: number, payload: ClassDoubtCreatePayload): Promise<ClassDoubt> {
    return fetchJson(`${API_BASE}/student/classes/${classId}/doubts`, {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  async getStudentClassDoubts(classId: number): Promise<ClassDoubt[]> {
    return fetchJson(`${API_BASE}/student/classes/${classId}/doubts`);
  }
};
