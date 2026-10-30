import React, { useState, useRef, useEffect } from 'react';
import {
  ArrowRight,
  BookOpen,
  CheckCircle2,
  Clock,
  Bot,
  Award,
  ChevronRight,
  Target,
  Sparkles,
  Route,
  Network,
  FileCheck2,
  Trophy,
  Layers,
  Repeat,
  GitBranch,
  Binary,
  ChevronDown,
  Check,
  BookMarked,
  Users,
  KeyRound,
  LogOut,
  Shield,
  AlertCircle,
  X,
  RefreshCw,
  Copy
} from 'lucide-react';
import { AgentLog, LearningPath, OutcomeAttainment, User, Course, StudentEnrolledClass, ClassPreviewInfo } from '../types';
import { useStudentLearning } from '../context/StudentLearningContext';
import { api } from '../services/api';

interface StudentDashboardProps {
  currentUser?: User | null;
  onNavigate: (tab: any) => void;
  agentLogs?: AgentLog[];
  onRefreshLogs?: () => void;
  outcomes?: OutcomeAttainment[];
  learningPath?: LearningPath | null;
  overallAttainment?: number;
  onSelectTopic?: (topicId: number) => void;
  courses?: Course[];
}

export const StudentDashboard: React.FC<StudentDashboardProps> = ({
  currentUser,
  onNavigate,
  onSelectTopic,
  courses = []
}) => {
  const {
    studentState,
    activeCourse,
    courses: contextCourses,
    setSelectedTopicForStudy,
    activeCourseId,
    setActiveCourseId
  } = useStudentLearning();

  const [courseDropdownOpen, setCourseDropdownOpen] = useState(false);
  const courseDropdownRef = useRef<HTMLDivElement>(null);

  // Close course dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (courseDropdownRef.current && !courseDropdownRef.current.contains(e.target as Node)) {
        setCourseDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Class Enrollment State (Step 2A Requirement 18)
  const [enrolledClasses, setEnrolledClasses] = useState<StudentEnrolledClass[]>([]);
  const [classesLoading, setClassesLoading] = useState(false);
  const [showJoinModal, setShowJoinModal] = useState(false);
  const [joinCodeInput, setJoinCodeInput] = useState('');
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewData, setPreviewData] = useState<ClassPreviewInfo | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [consentAccepted, setConsentAccepted] = useState(false);
  const [joinSubmitting, setJoinSubmitting] = useState(false);
  const [joinSuccessMsg, setJoinSuccessMsg] = useState<string | null>(null);
  const [classToLeave, setClassToLeave] = useState<StudentEnrolledClass | null>(null);
  const [leaveSubmitting, setLeaveSubmitting] = useState(false);

  const loadStudentClasses = async () => {
    setClassesLoading(true);
    try {
      const res = await api.getStudentClasses();
      setEnrolledClasses(res || []);
    } catch (err) {
      console.error('Failed to load student classes', err);
    } finally {
      setClassesLoading(false);
    }
  };

  useEffect(() => {
    loadStudentClasses();
  }, []);

  const handlePreviewClass = async (e: React.FormEvent) => {
    e.preventDefault();
    const code = joinCodeInput.trim().toUpperCase();
    if (!code) {
      setPreviewError('Please enter a class code.');
      return;
    }
    setPreviewLoading(true);
    setPreviewError(null);
    setPreviewData(null);
    setConsentAccepted(false);
    try {
      const data = await api.previewClass(code);
      setPreviewData(data);
    } catch (err: any) {
      setPreviewError(err.message || 'Invalid or inactive class code');
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleConfirmJoin = async () => {
    if (!consentAccepted || !previewData) return;
    setJoinSubmitting(true);
    setPreviewError(null);
    try {
      const res = await api.joinClass(previewData.class_code, true);
      setJoinSuccessMsg(res.message || 'Successfully joined class!');
      await loadStudentClasses();
      setTimeout(() => {
        setShowJoinModal(false);
        setJoinCodeInput('');
        setPreviewData(null);
        setConsentAccepted(false);
        setJoinSuccessMsg(null);
      }, 1500);
    } catch (err: any) {
      setPreviewError(err.message || 'Failed to join class');
    } finally {
      setJoinSubmitting(false);
    }
  };

  const handleConfirmLeave = async () => {
    if (!classToLeave) return;
    setLeaveSubmitting(true);
    try {
      await api.leaveClass(classToLeave.class_id);
      setClassToLeave(null);
      await loadStudentClasses();
    } catch (err: any) {
      alert(err.message || 'Failed to leave class');
    } finally {
      setLeaveSubmitting(false);
    }
  };

  // 1. Student Name & Greeting
  const studentName =
    studentState?.studentProfile?.full_name || currentUser?.full_name || 'Student';
  const hour = new Date().getHours();
  const timeGreeting =
    hour < 12 ? 'Good Morning' : hour < 18 ? 'Good Afternoon' : 'Good Evening';

  // 2. Course Details from active central state
  const courseTitle = studentState?.enrolledCourse?.title || activeCourse?.title || 'Selected Course';
  const courseCode = studentState?.enrolledCourse?.code || activeCourse?.code || '';
  const currentCourseId = studentState?.enrolledCourse?.id || activeCourseId;

  // Fallback courses list if not passed from parent
  const availableCourses = courses.length > 0 ? courses : (contextCourses.length > 0 ? contextCourses : [
    { id: 1, code: 'CS101', title: 'Python Programming', description: 'Procedural & structured programming' },
    { id: 2, code: 'CS201', title: 'Data Structures', description: 'Linear and non-linear data structures' },
    { id: 3, code: 'AI301', title: 'Machine Learning Fundamentals', description: 'Supervised and unsupervised models' },
    { id: 4, code: 'CS302', title: 'Database Management Systems', description: 'Relational models, SQL, and transactions' }
  ]);

  // 3. Overall Progress & Mastery Metrics
  const overallMastery = studentState
    ? Math.round(studentState.overallMastery)
    : 0;
  const overallProgress = studentState
    ? Math.round(studentState.overallProgress)
    : 0;
  const obeAttainment = studentState
    ? Math.round(studentState.overallOBEAttainment)
    : 0;

  const totalTopics = studentState?.totalTopics || (studentState?.topicMastery?.length ?? 0);
  const masteredCount = studentState?.masteredCount ?? (studentState?.topicMastery?.filter((t) => (t.mastery ?? 0) >= 80).length ?? 0);
  const inProgressCount = (studentState?.topicMastery || []).filter(
    (t) => (t.mastery ?? 0) >= 60 && (t.mastery ?? 0) < 80
  ).length;
  const weakCount = (studentState?.topicMastery || []).filter(
    (t) => (t.mastery ?? 0) < 60
  ).length;

  // 4. Current Target Topic
  const isCourseComplete =
    Boolean(studentState?.courseCompleted) ||
    (masteredCount === totalTopics && totalTopics > 0) ||
    ((studentState?.topicMastery || []).length > 0 &&
      (studentState?.topicMastery || []).every((t) => (t.mastery ?? 0) >= 80 || t.status === 'COMPLETED'));

  const currentTarget = isCourseComplete
    ? null
    : (studentState?.currentTargetTopic &&
       studentState.currentTargetTopic.status !== 'COMPLETED' &&
       (studentState.currentTargetTopic.mastery ?? 0) < 80
        ? studentState.currentTargetTopic
        : (studentState?.topicMastery || []).find((t) => !t.is_locked && (t.mastery ?? 0) < 80 && t.status !== 'COMPLETED') ||
          (studentState?.topicMastery || []).find((t) => (t.mastery ?? 0) < 80 && t.status !== 'COMPLETED') ||
          null);

  // 5. Next Up Topic (from adaptive learning path)
  const learningPathItems = studentState?.learningPath?.items || [];
  let nextUpItem: any = null;

  if (learningPathItems.length > 0 && currentTarget) {
    const currentIdx = learningPathItems.findIndex(
      (i) => i.topic_id === currentTarget.topic_id
    );
    if (currentIdx >= 0 && currentIdx + 1 < learningPathItems.length) {
      nextUpItem = learningPathItems[currentIdx + 1];
    } else {
      nextUpItem =
        learningPathItems.find(
          (i) =>
            i.topic_id !== currentTarget.topic_id &&
            i.status !== 'COMPLETED' &&
            (i.mastery_percentage ?? 0) < 80
        ) || null;
    }
  }

  const nextTopicTitle = nextUpItem?.topic_title || nextUpItem?.title || (isCourseComplete ? 'All Topics Mastered' : 'Next Up Module');
  const nextTopicId = nextUpItem?.topic_id || (currentTarget ? (currentTarget.topic_id === 1 ? 2 : 1) : 1);
  const nextEstMinutes = nextUpItem?.est_minutes || 25;

  // 6. Needs Practice Topics (Filtered strictly from current course's topics)
  const weakTopics = (studentState?.topicMastery || []).filter((t) => {
    const m = t.mastery ?? 0;
    const cls = (t.classification || '').toUpperCase();
    return m < 60 || cls === 'NEEDS PRACTICE' || cls === 'WEAK';
  });

  // Navigation handlers
  const handleContinueLearning = () => {
    if (currentTarget?.topic_id) {
      setSelectedTopicForStudy(currentTarget.topic_id);
      if (onSelectTopic) {
        onSelectTopic(currentTarget.topic_id);
        return;
      }
    }
    onNavigate('learning-path');
  };

  const handleOpenTopic = (topicId: number) => {
    setSelectedTopicForStudy(topicId);
    if (onSelectTopic) {
      onSelectTopic(topicId);
    } else {
      onNavigate('learning-path');
    }
  };

  const handleAskTutor = () => {
    if (currentTarget?.topic_id) {
      setSelectedTopicForStudy(currentTarget.topic_id);
    }
    onNavigate('ai-tutor');
  };

  // 7. Recent Activity formatting
  const formatRelativeTime = (timestamp?: string) => {
    if (!timestamp) return 'Recently';
    try {
      const cleanTs =
        timestamp.includes(' ') && !timestamp.includes('T')
          ? timestamp.replace(' ', 'T')
          : timestamp;
      const date = new Date(cleanTs);
      if (isNaN(date.getTime())) return 'Recently';
      const diffMs = Date.now() - date.getTime();
      const diffSec = Math.floor(diffMs / 1000);
      const diffMin = Math.floor(diffSec / 60);
      const diffHr = Math.floor(diffMin / 60);
      const diffDays = Math.floor(diffHr / 24);

      if (diffSec < 60) return 'Just now';
      if (diffMin < 60) return `${diffMin}m ago`;
      if (diffHr < 24) return `${diffHr} hours ago`;
      if (diffDays === 1) return 'Yesterday';
      if (diffDays < 7) return `${diffDays} days ago`;
      return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    } catch {
      return 'Recently';
    }
  };

  const getTopicTitleById = (tId?: number | null) => {
    if (!tId) return '';
    const match = studentState?.topicMastery?.find((t) => t.topic_id === tId);
    return match?.title || `Topic ${tId}`;
  };

  const realActivities: {
    id: string | number;
    title: string;
    description: string;
    time: string;
    icon: any;
    iconBg: string;
    iconColor: string;
  }[] = [];

  if (studentState?.assessmentResults && studentState.assessmentResults.length > 0) {
    studentState.assessmentResults.slice(0, 4).forEach((record, idx) => {
      const relativeTime = formatRelativeTime(record.created_at);
      const topicName = getTopicTitleById(record.topic_id);
      const typeLower = (record.attempt_type || '').toLowerCase();

      if (typeLower.includes('diagnostic')) {
        realActivities.push({
          id: record.attempt_uuid || idx,
          title: 'You completed an AI Skill Check',
          description: `Diagnostic • ${Math.round(record.percentage)}% score`,
          time: relativeTime,
          icon: CheckCircle2,
          iconBg: 'bg-emerald-50',
          iconColor: 'text-emerald-600'
        });
      } else if (typeLower.includes('tutor') || typeLower.includes('test_me')) {
        realActivities.push({
          id: record.attempt_uuid || idx,
          title: 'You took an AI Tutor challenge',
          description: topicName || 'Adaptive Challenge',
          time: relativeTime,
          icon: Bot,
          iconBg: 'bg-orange-50',
          iconColor: 'text-[#EA580C]'
        });
      } else if (typeLower.includes('reassessment')) {
        realActivities.push({
          id: record.attempt_uuid || idx,
          title: 'You passed a reassessment',
          description: topicName ? `${topicName} • Mastery updated` : 'Mastery updated',
          time: relativeTime,
          icon: Award,
          iconBg: 'bg-amber-50',
          iconColor: 'text-amber-600'
        });
      } else {
        realActivities.push({
          id: record.attempt_uuid || idx,
          title: 'You completed a practice session',
          description: topicName ? `${topicName} • Scored ${Math.round(record.percentage)}%` : 'Practice session',
          time: relativeTime,
          icon: CheckCircle2,
          iconBg: 'bg-orange-50',
          iconColor: 'text-[#EA580C]'
        });
      }
    });
  }

  // Fallbacks if fewer than 4 activities
  if (realActivities.length < 4) {
    realActivities.push({
      id: 'fb-1',
      title: 'Course Learning Path Active',
      description: `${courseTitle} (${courseCode})`,
      time: 'Just now',
      icon: CheckCircle2,
      iconBg: 'bg-orange-50',
      iconColor: 'text-[#EA580C]'
    });
    realActivities.push({
      id: 'fb-2',
      title: 'Curriculum Trajectory Synced',
      description: 'Standard Course Outcomes & Prerequisites',
      time: '1 day ago',
      icon: Award,
      iconBg: 'bg-amber-50',
      iconColor: 'text-amber-600'
    });
  }

  // 8. DYNAMIC TOPIC CARDS: Derived directly from the active course's real topics!
  const bannerThemes = [
    { bg: 'bg-gradient-to-r from-slate-900 via-slate-800 to-orange-950', icon: Layers },
    { bg: 'bg-gradient-to-r from-orange-900 via-amber-900 to-slate-900', icon: Repeat },
    { bg: 'bg-gradient-to-r from-slate-900 via-emerald-950 to-teal-900', icon: GitBranch },
    { bg: 'bg-gradient-to-r from-amber-700 via-orange-600 to-amber-600', icon: Binary },
    { bg: 'bg-gradient-to-r from-emerald-900 via-teal-900 to-slate-900', icon: BookOpen }
  ];

  const currentTopicsList =
    studentState?.topicMastery && studentState.topicMastery.length > 0
      ? studentState.topicMastery.slice(0, 4).map((t, idx) => {
          const theme = bannerThemes[idx % bannerThemes.length];
          const masteryScore = Math.round(t.mastery ?? 0);
          let badge = 'Developing';
          let badgeColor = 'text-orange-800 bg-orange-50 border-orange-200';
          if (masteryScore >= 80 || t.classification === 'MASTERED') {
            badge = 'Mastered';
            badgeColor = 'text-emerald-700 bg-emerald-50 border-emerald-200';
          } else if (masteryScore >= 60 || t.classification === 'DEVELOPING') {
            badge = 'In Progress';
            badgeColor = 'text-orange-700 bg-orange-50 border-orange-200';
          } else if (
            t.classification === 'NEEDS PRACTICE' ||
            (masteryScore >= 40 && masteryScore < 60)
          ) {
            badge = 'Needs Practice';
            badgeColor = 'text-amber-700 bg-amber-50 border-amber-200';
          } else {
            badge = 'Weak';
            badgeColor = 'text-rose-700 bg-rose-50 border-rose-200';
          }

          const outcomesText =
            t.outcomes && t.outcomes.length > 0 ? t.outcomes.join(', ') : 'CO1';

          return {
            id: t.topic_id,
            title: t.title,
            subtitle: `${t.difficulty || 'Core'} • ${outcomesText}`,
            mastery: masteryScore,
            lessons: `${Math.min(Math.round(masteryScore / 20) + 1, 5)} / 5 Objectives`,
            badge,
            badgeColor,
            bannerBg: theme.bg,
            icon: theme.icon
          };
        })
      : [];

  // SVG circular donut progress calculations
  const radius = 38;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (overallProgress / 100) * circumference;

  return (
    <div className="space-y-6 max-w-[1400px] mx-auto pb-12">
      {/* ================================================== */}
      {/* ROW 1: WELCOME BANNER + 3 STAT CARDS (EduSphere Style) */}
      {/* ================================================== */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch">
        {/* Left 8 Cols: Hero Welcome Banner */}
        <div className="lg:col-span-8 bg-gradient-to-r from-[#FFFDF9] via-[#FFF7ED] to-[#FEF3C7]/40 border border-orange-100/90 rounded-2xl p-6 sm:p-7 relative flex flex-col justify-between shadow-xs z-30">
          {/* Isolated illustration container to prevent clipping dropdowns */}
          <div className="absolute inset-0 rounded-2xl overflow-hidden pointer-events-none">
            <div className="hidden sm:block absolute right-3 bottom-0 top-0 w-64 pointer-events-none">
              <svg className="w-full h-full" viewBox="0 0 280 200" fill="none">
                {/* Floating cursive text */}
                <text x="145" y="42" fontFamily="ui-sans-serif, system-ui, sans-serif" fontSize="13" fontStyle="italic" fontWeight="600" fill="#EA580C">
                  Learn
                </text>
                <text x="140" y="58" fontFamily="ui-sans-serif, system-ui, sans-serif" fontSize="13" fontStyle="italic" fontWeight="600" fill="#EA580C">
                  Anytime
                </text>
                <text x="135" y="74" fontFamily="ui-sans-serif, system-ui, sans-serif" fontSize="13" fontStyle="italic" fontWeight="600" fill="#EA580C">
                  Anywhere ♡
                </text>

                {/* Potted Plant */}
                <ellipse cx="60" cy="180" rx="14" ry="4" fill="#E2E8F0" />
                <path d="M52 165 L68 165 L65 180 L55 180 Z" fill="#94A3B8" />
                <path d="M60 165 C55 145 42 148 40 135 C52 135 60 148 60 165 Z" fill="#10B981" />
                <path d="M60 165 C65 145 78 148 80 135 C68 135 60 148 60 165 Z" fill="#059669" />

                {/* Desk Surface */}
                <rect x="75" y="176" width="180" height="6" rx="3" fill="#CBD5E1" />

                {/* Laptop */}
                <rect x="85" y="140" width="55" height="34" rx="3" fill="#1E293B" />
                <rect x="88" y="143" width="49" height="28" rx="2" fill="#EA580C" />
                {/* Laptop glow content */}
                <rect x="94" y="148" width="22" height="3" rx="1" fill="#FFFFFF" opacity="0.8" />
                <rect x="94" y="154" width="36" height="2" rx="1" fill="#FFFFFF" opacity="0.6" />
                <rect x="94" y="159" width="30" height="2" rx="1" fill="#FFFFFF" opacity="0.6" />
                {/* Laptop base */}
                <path d="M80 174 L145 174 L140 177 L85 177 Z" fill="#94A3B8" />

                {/* Student Figure */}
                <path d="M125 155 C125 135 155 135 155 155 L165 180 L115 180 Z" fill="#FBBF24" />
                <circle cx="140" cy="115" r="16" fill="#FCD34D" />
                <path d="M124 115 C124 95 156 95 156 115 C156 122 150 128 140 128 C130 128 124 122 124 115 Z" fill="#1E1B4B" />
                <path d="M126 115 Q140 100 154 115 Q145 110 126 115 Z" fill="#312E81" />
                {/* Headphones */}
                <path d="M124 110 C124 98 156 98 156 110" stroke="#EA580C" strokeWidth="4" strokeLinecap="round" />
                <rect x="122" y="108" width="5" height="12" rx="2" fill="#C2410C" />
                <rect x="153" y="108" width="5" height="12" rx="2" fill="#C2410C" />

                {/* Stacked Books on right of desk */}
                <rect x="180" y="166" width="40" height="8" rx="2" fill="#EA580C" />
                <rect x="182" y="157" width="36" height="8" rx="2" fill="#10B981" />
                <rect x="185" y="148" width="32" height="8" rx="2" fill="#F43F5E" />
              </svg>
            </div>
          </div>

          <div className="relative z-10 max-w-md space-y-2">
            <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <span>{timeGreeting}, {studentName}!</span>
              <span className="text-2xl">☀️</span>
            </h1>

            <p className="text-xs sm:text-sm text-slate-600 font-normal leading-relaxed">
              Keep going! Your hard work today builds a brighter future tomorrow.
            </p>

            {/* Interactive Course Switcher Dropdown */}
            <div className="pt-1.5 relative inline-block text-left z-40" ref={courseDropdownRef}>
              <button
                type="button"
                onClick={() => setCourseDropdownOpen(!courseDropdownOpen)}
                className="inline-flex items-center space-x-2 px-3 py-1.5 bg-white/95 hover:bg-white border border-orange-200/90 rounded-xl text-xs font-semibold text-orange-700 shadow-xs hover:shadow-md transition-all cursor-pointer ring-1 ring-orange-50"
                title="Click to switch active course"
              >
                <span className="w-2 h-2 rounded-full bg-[#EA580C] animate-pulse" />
                <span className="font-bold">{courseTitle}</span>
                <span className="text-orange-400 font-normal">({courseCode})</span>
                <ChevronDown className={`w-3.5 h-3.5 text-orange-500 ml-1 transition-transform duration-200 ${courseDropdownOpen ? 'rotate-180' : ''}`} />
              </button>

              {/* Course Switcher Menu (Opens cleanly in front of everything) */}
              {courseDropdownOpen && (
                <div className="absolute left-0 top-full mt-2 w-80 max-w-[90vw] bg-white border border-slate-200 rounded-2xl shadow-2xl p-2 z-[9999] animate-fadeIn space-y-1 ring-1 ring-black/10">
                  <div className="px-3 py-2 text-[10px] font-bold uppercase tracking-wider text-slate-400 border-b border-slate-100 flex items-center justify-between">
                    <span>Switch Active Course</span>
                    <span className="text-[10px] text-orange-700 font-semibold bg-orange-50 px-2 py-0.5 rounded-full">
                      {availableCourses.length} Courses
                    </span>
                  </div>

                  <div className="space-y-1 pt-1 max-h-64 overflow-y-auto">
                    {availableCourses.map((c) => {
                      const isSelected = c.id === currentCourseId;
                      return (
                        <button
                          key={c.id}
                          onClick={async () => {
                            setCourseDropdownOpen(false);
                            await setActiveCourseId(c.id);
                          }}
                          className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium transition-all text-left cursor-pointer ${
                            isSelected
                              ? 'bg-orange-50 text-orange-700 font-semibold border border-orange-200/60 shadow-xs'
                              : 'text-slate-700 hover:bg-slate-50 border border-transparent'
                          }`}
                        >
                          <div className="min-w-0 pr-2">
                            <div className="font-bold truncate text-slate-900">{c.title}</div>
                            <div className="text-[10px] text-slate-400 flex items-center space-x-1.5 mt-0.5">
                              <span className="font-mono font-semibold text-orange-600 bg-orange-50/80 px-1 rounded">{c.code}</span>
                              <span>•</span>
                              <span className="truncate">{c.description || 'Curriculum Trajectory'}</span>
                            </div>
                          </div>
                          {isSelected && (
                            <div className="w-5 h-5 rounded-full bg-[#EA580C] flex items-center justify-center text-white flex-shrink-0">
                              <Check className="w-3 h-3 stroke-[3]" />
                            </div>
                          )}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>

            <div className="pt-3">
              <button
                id="btn-hero-continue"
                onClick={handleContinueLearning}
                className="inline-flex items-center space-x-2 px-5 py-2.5 bg-[#EA580C] hover:bg-[#C2410C] active:scale-[0.99] text-white rounded-xl text-xs sm:text-sm font-semibold shadow-xs hover:shadow transition-all cursor-pointer"
              >
                <span>{isCourseComplete ? 'Review Learning Path' : 'Continue Learning'}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Right 4 Cols: 3 Clean White Stat Cards in a row */}
        <div className="lg:col-span-4 grid grid-cols-3 gap-3">
          {/* Card 1: Overall Mastery */}
          <div className="bg-white border border-[#E2E8F0] rounded-2xl p-4 shadow-xs flex flex-col justify-between hover:border-orange-200 transition-all">
            <div className="flex items-center justify-between">
              <div className="p-2 bg-orange-50 text-orange-600 rounded-xl">
                <BookOpen className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3">
              <div className="text-[11px] font-semibold text-slate-500 truncate">
                Overall Mastery
              </div>
              <div className="text-xl sm:text-2xl font-bold text-slate-900 mt-0.5">
                {overallMastery}%
              </div>
            </div>
            <button
              onClick={() => onNavigate('learning-path')}
              className="text-[10px] font-semibold text-orange-600 hover:underline flex items-center space-x-0.5 mt-2 cursor-pointer"
            >
              <span>View all</span>
              <ChevronRight className="w-3 h-3" />
            </button>
          </div>

          {/* Card 2: Completed / Mastered Topics */}
          <div className="bg-white border border-[#E2E8F0] rounded-2xl p-4 shadow-xs flex flex-col justify-between hover:border-emerald-200 transition-all">
            <div className="flex items-center justify-between">
              <div className="p-2 bg-emerald-50 text-emerald-600 rounded-xl">
                <CheckCircle2 className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3">
              <div className="text-[11px] font-semibold text-slate-500 truncate">
                Mastered Topics
              </div>
              <div className="text-xl sm:text-2xl font-bold text-slate-900 mt-0.5">
                {masteredCount} / {totalTopics}
              </div>
            </div>
            <button
              onClick={() => onNavigate('learning-path')}
              className="text-[10px] font-semibold text-emerald-600 hover:underline flex items-center space-x-0.5 mt-2 cursor-pointer"
            >
              <span>View all</span>
              <ChevronRight className="w-3 h-3" />
            </button>
          </div>

          {/* Card 3: OBE Attain (Outcome-Based Education Attainment) */}
          <div className="bg-white border border-[#E2E8F0] rounded-2xl p-4 shadow-xs flex flex-col justify-between hover:border-amber-200 transition-all">
            <div className="flex items-center justify-between">
              <div className="p-2 bg-amber-50 text-amber-600 rounded-xl">
                <Award className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3">
              <div className="text-[11px] font-semibold text-slate-500 truncate">
                OBE Attain
              </div>
              <div className="text-xl sm:text-2xl font-bold text-slate-900 mt-0.5">
                {obeAttainment}%
              </div>
            </div>
            <button
              onClick={() => onNavigate('learning-path')}
              className="text-[10px] font-semibold text-amber-600 hover:underline flex items-center space-x-0.5 mt-2 cursor-pointer"
            >
              <span>View all</span>
              <ChevronRight className="w-3 h-3" />
            </button>
          </div>
        </div>
      </div>

      {/* ================================================== */}
      {/* ROW 2: MY CURRENT TOPICS (EduSphere "My Current Courses") */}
      {/* ================================================== */}
      <div className="space-y-3.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <h2 className="text-base sm:text-lg font-bold text-slate-900 tracking-tight">
              My Current Topics
            </h2>
            <span className="text-xs font-semibold px-2.5 py-0.5 bg-slate-100 text-slate-600 rounded-md">
              {courseCode}
            </span>
          </div>

          <button
            onClick={() => onNavigate('learning-path')}
            className="text-xs font-semibold text-orange-600 hover:underline flex items-center space-x-1 cursor-pointer"
          >
            <span>View All</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {currentTopicsList.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {currentTopicsList.map((item) => {
              const Icon = item.icon;
              return (
                <div
                  key={item.id}
                  onClick={() => handleOpenTopic(item.id)}
                  className="bg-white border border-[#E2E8F0] rounded-2xl overflow-hidden shadow-xs hover:shadow-md hover:border-orange-200 transition-all group cursor-pointer flex flex-col justify-between"
                >
                  {/* Top Colored Graphic Banner */}
                  <div className={`h-24 ${item.bannerBg} flex items-center justify-center relative p-4 text-white`}>
                    <div className="w-12 h-12 rounded-xl bg-white/10 backdrop-blur-xs border border-white/20 flex items-center justify-center text-white shadow-inner group-hover:scale-110 transition-transform">
                      <Icon className="w-6 h-6" />
                    </div>
                  </div>

                  {/* Card Content */}
                  <div className="p-4 space-y-3 flex-1 flex flex-col justify-between">
                    <div>
                      <h3 className="font-bold text-slate-900 text-sm tracking-tight truncate group-hover:text-orange-600 transition-colors" title={item.title}>
                        {item.title}
                      </h3>
                      <p className="text-[11px] text-slate-500 mt-0.5 line-clamp-1">
                        {item.subtitle}
                      </p>
                    </div>

                    {/* Progress Bar + Percentage */}
                    <div className="space-y-1.5 pt-1">
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="text-slate-400 font-medium">Mastery</span>
                        <span className="font-bold text-slate-800">{item.mastery}%</span>
                      </div>
                      <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                        <div
                          className="bg-[#EA580C] h-full rounded-full transition-all duration-500"
                          style={{ width: `${item.mastery}%` }}
                        />
                      </div>
                    </div>

                    {/* Bottom Info & Status Badge */}
                    <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px]">
                      <span className="text-slate-500 font-medium">{item.lessons}</span>
                      <span className={`px-2 py-0.5 rounded-md font-semibold text-[10px] border ${item.badgeColor}`}>
                        {item.badge}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="p-8 bg-white border border-[#E2E8F0] rounded-2xl text-center text-slate-500 text-xs">
            No topics loaded yet for this course.
          </div>
        )}
      </div>

      {/* ================================================== */}
      {/* SECTION: MY CLASSES & JOIN CLASS (Step 2A Requirement 18) */}
      {/* ================================================== */}
      <div className="bg-white border border-[#E2E8F0] rounded-2xl p-6 shadow-xs space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-100">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 bg-[#F3F0FF] text-[#635BFF] rounded-xl">
              <Users className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-slate-900 text-sm tracking-tight">
                My Enrolled Classes & Cohorts
              </h3>
              <p className="text-[11px] text-slate-500">
                Join a teacher's class using a 6-character code to share your progress and outcome attainment.
              </p>
            </div>
          </div>

          <button
            onClick={() => {
              setShowJoinModal(true);
              setJoinCodeInput('');
              setPreviewData(null);
              setPreviewError(null);
              setConsentAccepted(false);
            }}
            className="px-4 py-2 bg-[#635BFF] hover:bg-[#5349e0] text-white rounded-xl text-xs font-semibold transition-all flex items-center space-x-1.5 shadow-xs"
          >
            <KeyRound className="w-3.5 h-3.5" />
            <span>Join Class</span>
          </button>
        </div>

        {classesLoading ? (
          <div className="py-6 text-center text-slate-400 text-xs flex items-center justify-center space-x-2">
            <RefreshCw className="w-4 h-4 animate-spin text-[#635BFF]" />
            <span>Loading enrolled classes...</span>
          </div>
        ) : enrolledClasses.length === 0 ? (
          <div className="py-6 px-4 bg-slate-50 border border-dashed border-slate-200 rounded-xl text-center space-y-2">
            <p className="text-xs text-slate-600 font-medium">
              You haven't joined any classes yet.
            </p>
            <p className="text-[11px] text-slate-400 max-w-md mx-auto">
              Your teacher can provide a 6-character class code. You retain full ownership of your data and can leave at any time.
            </p>
            <button
              onClick={() => {
                setShowJoinModal(true);
                setJoinCodeInput('');
                setPreviewData(null);
                setPreviewError(null);
                setConsentAccepted(false);
              }}
              className="mt-1 px-3 py-1.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-semibold rounded-lg shadow-2xs"
            >
              Enter Class Code
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {enrolledClasses.map((cls) => (
              <div
                key={cls.enrollment_id}
                className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-white hover:border-[#635BFF]/30 transition-all flex flex-col justify-between space-y-3"
              >
                <div className="space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-purple-50 text-[#635BFF] border border-purple-100">
                      {cls.course_code || 'COURSE'}
                    </span>
                    <span className="font-mono text-xs font-bold text-slate-700 bg-white px-2 py-0.5 border border-slate-200 rounded">
                      {cls.class_code}
                    </span>
                  </div>
                  <h4 className="font-bold text-slate-900 text-xs pt-1">{cls.name}</h4>
                  <p className="text-[11px] text-slate-500 line-clamp-1">{cls.course_title}</p>
                </div>

                <div className="pt-2 border-t border-slate-200/60 space-y-1 text-[11px] text-slate-600">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Teacher:</span>
                    <span className="font-medium text-slate-800">{cls.teacher_name}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Joined with:</span>
                    <span className="font-semibold text-emerald-700">{cls.baseline_completed_topics} topics done</span>
                  </div>
                  {cls.joined_at && (
                    <div className="flex items-center justify-between">
                      <span className="text-slate-400">Joined on:</span>
                      <span>{new Date(cls.joined_at).toLocaleDateString()}</span>
                    </div>
                  )}
                </div>

                <div className="flex items-center space-x-2 pt-1">
                  <button
                    onClick={() => onNavigate('class-hub')}
                    className="flex-1 py-1.5 px-3 bg-orange-50 hover:bg-orange-100 text-orange-700 border border-orange-200 rounded-lg text-xs font-bold transition-colors flex items-center justify-center space-x-1 cursor-pointer"
                  >
                    <Users className="w-3.5 h-3.5" />
                    <span>Class Hub</span>
                  </button>
                  <button
                    onClick={() => setClassToLeave(cls)}
                    className="py-1.5 px-3 bg-white hover:bg-rose-50 text-slate-500 hover:text-rose-600 border border-slate-200 hover:border-rose-200 rounded-lg text-xs font-semibold transition-colors flex items-center justify-center space-x-1 cursor-pointer"
                    title="Leave Class"
                  >
                    <LogOut className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ================================================== */}
      {/* ROW 3: LEARNING PROGRESS + RECENT ACTIVITY + NEXT UP */}
      {/* ================================================== */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch">
        {/* Col 1 (4 cols): Learning Progress Donut Chart */}
        <div className="lg:col-span-4 bg-white border border-[#E2E8F0] rounded-2xl p-5 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <h3 className="font-bold text-slate-900 text-sm tracking-tight">
              Learning Progress
            </h3>
          </div>

          <div className="py-4 flex items-center justify-around gap-4">
            {/* SVG Donut Chart */}
            <div className="relative w-28 h-28 flex items-center justify-center flex-shrink-0">
              <svg className="w-full h-full -rotate-90 transform" viewBox="0 0 100 100">
                <circle
                  cx="50"
                  cy="50"
                  r={radius}
                  className="stroke-slate-100"
                  strokeWidth="8"
                  fill="transparent"
                />
                <circle
                  cx="50"
                  cy="50"
                  r={radius}
                  className="stroke-[#10B981] transition-all duration-1000 ease-out"
                  strokeWidth="8"
                  strokeDasharray={circumference}
                  strokeDashoffset={strokeDashoffset}
                  strokeLinecap="round"
                  fill="transparent"
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                <span className="text-2xl font-bold text-slate-900 leading-none">
                  {overallProgress}%
                </span>
                <span className="text-[9px] text-slate-400 font-semibold uppercase tracking-wider mt-1">
                  Overall
                </span>
              </div>
            </div>

            {/* Legend */}
            <div className="space-y-2 text-xs">
              <div className="flex items-center justify-between space-x-3">
                <div className="flex items-center space-x-2">
                  <span className="w-2 h-2 rounded-full bg-[#10B981]" />
                  <span className="text-slate-600 font-medium">Completed</span>
                </div>
                <span className="font-bold text-slate-900">{masteredCount}</span>
              </div>

              <div className="flex items-center justify-between space-x-3">
                <div className="flex items-center space-x-2">
                  <span className="w-2 h-2 rounded-full bg-[#EA580C]" />
                  <span className="text-slate-600 font-medium">In Progress</span>
                </div>
                <span className="font-bold text-slate-900">{inProgressCount}</span>
              </div>

              <div className="flex items-center justify-between space-x-3">
                <div className="flex items-center space-x-2">
                  <span className="w-2 h-2 rounded-full bg-[#F59E0B]" />
                  <span className="text-slate-600 font-medium">Needs Practice</span>
                </div>
                <span className="font-bold text-slate-900">{weakCount}</span>
              </div>
            </div>
          </div>

          {/* Bottom Motivation Trophy Pill */}
          <div className="bg-amber-50/70 border border-amber-100 rounded-xl p-3 flex items-center space-x-2.5">
            <div className="text-base">🏆</div>
            <div>
              <div className="text-xs font-bold text-amber-900">You're doing great!</div>
              <div className="text-[10px] text-amber-700">Keep it up! Consistent progress unlocks new skills.</div>
            </div>
          </div>
        </div>

        {/* Col 2 (4 cols): Recent Activity List */}
        <div className="lg:col-span-4 bg-white border border-[#E2E8F0] rounded-2xl p-5 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <h3 className="font-bold text-slate-900 text-sm tracking-tight">
              Recent Activity
            </h3>
            <button
              onClick={() => onNavigate('assessments')}
              className="text-xs font-semibold text-orange-600 hover:underline flex items-center space-x-0.5 cursor-pointer"
            >
              <span>View All</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="divide-y divide-slate-100 my-auto">
            {realActivities.map((act) => {
              const Icon = act.icon;
              return (
                <div key={act.id} className="py-2.5 first:pt-1 last:pb-1 flex items-start space-x-3">
                  <div className={`p-2 rounded-xl ${act.iconBg} ${act.iconColor} flex-shrink-0 mt-0.5`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <div className="text-xs font-semibold text-slate-800 truncate">
                        {act.title}
                      </div>
                      <div className="text-[10px] text-slate-400 font-medium ml-2 flex-shrink-0">
                        {act.time}
                      </div>
                    </div>
                    <div className="text-[11px] text-slate-500 mt-0.5 line-clamp-1">
                      {act.description}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Col 3 (4 cols): Next Up + Needs Practice + Quick Links */}
        <div className="lg:col-span-4 space-y-4">
          {/* Next Up Card */}
          <div className="bg-white border border-[#E2E8F0] rounded-2xl p-4 shadow-xs hover:border-orange-200 transition-all">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                NEXT UP
              </span>
              <div className="flex items-center space-x-1 text-xs text-slate-500">
                <Clock className="w-3 h-3 text-slate-400" />
                <span>{nextEstMinutes} min</span>
              </div>
            </div>

            <div className="mt-2.5 flex items-center justify-between gap-3">
              <div>
                <h4 className="text-sm font-bold text-slate-900 tracking-tight">
                  {nextTopicTitle}
                </h4>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Recommended based on your current progress.
                </p>
              </div>

              <button
                id="btn-next-up-start"
                onClick={() => handleOpenTopic(nextTopicId)}
                className="px-3.5 py-1.5 bg-[#EA580C] hover:bg-[#C2410C] text-white rounded-lg text-xs font-semibold shadow-xs flex-shrink-0 cursor-pointer"
              >
                Start →
              </button>
            </div>
          </div>

          {/* Needs Practice Card */}
          <div className="bg-white border border-[#E2E8F0] rounded-2xl p-4 shadow-xs">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <span className="text-xs font-bold text-slate-900">Needs Practice</span>
              {weakTopics.length > 0 && (
                <span className="text-[10px] px-2 py-0.5 bg-amber-50 text-amber-700 font-bold rounded-md border border-amber-200">
                  {weakTopics.length} topics
                </span>
              )}
            </div>

            <div className="mt-2.5 space-y-2">
              {weakTopics.length > 0 ? (
                weakTopics.slice(0, 2).map((t) => (
                  <button
                    key={t.topic_id}
                    onClick={() => handleOpenTopic(t.topic_id)}
                    className="w-full text-left p-2 rounded-xl bg-[#F8FAFC] hover:bg-slate-100 border border-slate-200/80 transition-all flex items-center justify-between cursor-pointer"
                  >
                    <div className="min-w-0 pr-2">
                      <div className="text-xs font-semibold text-slate-800 truncate">
                        {t.title}
                      </div>
                      <div className="text-[10px] text-slate-400">
                        {Math.round(t.mastery ?? 0)}% mastery
                      </div>
                    </div>
                    <span className="text-[10px] font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                      Practice
                    </span>
                  </button>
                ))
              ) : (
                <div className="text-xs text-slate-500 py-1 text-center font-medium">
                  ✨ No topics currently need extra practice.
                </div>
              )}
            </div>
          </div>

          {/* Quick Links (EduSphere Style) */}
          <div className="bg-white border border-[#E2E8F0] rounded-2xl p-3.5 shadow-xs">
            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-2">
              QUICK LINKS
            </div>
            <div className="grid grid-cols-4 gap-2">
              <button
                onClick={() => onNavigate('learning-path')}
                className="p-2 rounded-xl bg-[#F8FAFC] hover:bg-orange-50 hover:text-orange-600 transition-colors flex flex-col items-center space-y-1 cursor-pointer"
                title="Learning Path"
              >
                <div className="p-1.5 bg-orange-100/70 text-orange-700 rounded-lg">
                  <Route className="w-3.5 h-3.5" />
                </div>
                <span className="text-[9px] font-semibold text-slate-600">Path</span>
              </button>

              <button
                onClick={() => onNavigate('ai-tutor')}
                className="p-2 rounded-xl bg-[#F8FAFC] hover:bg-orange-50 hover:text-orange-600 transition-colors flex flex-col items-center space-y-1 cursor-pointer"
                title="AI Tutor"
              >
                <div className="p-1.5 bg-orange-100/70 text-orange-700 rounded-lg">
                  <Bot className="w-3.5 h-3.5" />
                </div>
                <span className="text-[9px] font-semibold text-slate-600">AI Tutor</span>
              </button>

              <button
                onClick={() => onNavigate('assessments')}
                className="p-2 rounded-xl bg-[#F8FAFC] hover:bg-emerald-50 hover:text-emerald-600 transition-colors flex flex-col items-center space-y-1 cursor-pointer"
                title="Assessments"
              >
                <div className="p-1.5 bg-emerald-100/70 text-emerald-700 rounded-lg">
                  <FileCheck2 className="w-3.5 h-3.5" />
                </div>
                <span className="text-[9px] font-semibold text-slate-600">Tests</span>
              </button>

              <button
                onClick={() => onNavigate('resources')}
                className="p-2 rounded-xl bg-[#F8FAFC] hover:bg-amber-50 hover:text-amber-600 transition-colors flex flex-col items-center space-y-1 cursor-pointer"
                title="Resources"
              >
                <div className="p-1.5 bg-amber-100/70 text-amber-700 rounded-lg">
                  <BookMarked className="w-3.5 h-3.5" />
                </div>
                <span className="text-[9px] font-semibold text-slate-600">Resources</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* ================================================== */}
      {/* ROW 4: BOTTOM BANNER (EduSphere "Achieve Your Goals" / AI Tutor) */}
      {/* ================================================== */}
      <div className="bg-white border border-[#E2E8F0] rounded-2xl p-5 sm:p-6 shadow-xs flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 rounded-full bg-orange-50 border border-orange-100 flex items-center justify-center text-[#EA580C] flex-shrink-0 shadow-xs">
            <Target className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900 tracking-tight">
              Need help with your current topic?
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Ask your AI Tutor about <span className="font-semibold text-slate-800">{currentTarget?.title || 'course concepts'}</span> for instant explanations, practice hints, and concept mastery.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3 flex-shrink-0 w-full sm:w-auto justify-end">
          <button
            id="btn-bottom-ai-tutor"
            onClick={handleAskTutor}
            className="w-full sm:w-auto px-5 py-2.5 bg-[#EA580C] hover:bg-[#C2410C] active:scale-[0.99] text-white rounded-xl text-xs sm:text-sm font-semibold shadow-xs hover:shadow transition-all flex items-center justify-center space-x-2 cursor-pointer"
          >
            <span>Ask AI Tutor</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
      {/* ================================================== */}
      {/* MODAL: JOIN CLASS WITH CONSENT (Step 2A Req 18)   */}
      {/* ================================================== */}
      {showJoinModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4 animate-fadeIn">
          <div className="bg-white rounded-2xl shadow-xl border border-slate-200 max-w-md w-full p-6 space-y-5 animate-scaleUp">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center space-x-2">
                <KeyRound className="w-5 h-5 text-[#635BFF]" />
                <h3 className="text-base font-bold text-slate-900">Join a Class Cohort</h3>
              </div>
              <button
                onClick={() => {
                  setShowJoinModal(false);
                  setPreviewData(null);
                  setPreviewError(null);
                }}
                className="p-1 hover:bg-slate-100 rounded-lg text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {joinSuccessMsg ? (
              <div className="py-6 text-center space-y-2">
                <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto" />
                <h4 className="font-bold text-slate-900 text-sm">{joinSuccessMsg}</h4>
                <p className="text-xs text-slate-500">Your enrollment baseline has been recorded.</p>
              </div>
            ) : !previewData ? (
              /* Step 1: Enter Code */
              <form onSubmit={handlePreviewClass} className="space-y-4 text-xs">
                {previewError && (
                  <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 flex items-start space-x-2">
                    <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                    <span>{previewError}</span>
                  </div>
                )}

                <div className="space-y-1.5">
                  <label className="font-semibold text-slate-700">Enter Class Code</label>
                  <input
                    type="text"
                    required
                    maxLength={12}
                    placeholder="e.g. 7K9M2P"
                    value={joinCodeInput}
                    onChange={(e) => setJoinCodeInput(e.target.value.toUpperCase())}
                    className="w-full px-3 py-2.5 border border-slate-300 rounded-xl font-mono text-center text-lg uppercase tracking-widest text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-[#635BFF]/30"
                  />
                  <p className="text-[11px] text-slate-400 text-center">
                    Ask your teacher for the 6-character class code.
                  </p>
                </div>

                <div className="flex items-center justify-end space-x-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowJoinModal(false)}
                    className="px-4 py-2 border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-xl font-semibold transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={previewLoading || !joinCodeInput.trim()}
                    className="px-4 py-2 bg-[#635BFF] hover:bg-[#5349e0] text-white rounded-xl font-semibold transition-all shadow-xs disabled:opacity-50"
                  >
                    {previewLoading ? 'Verifying...' : 'Next: Preview & Consent'}
                  </button>
                </div>
              </form>
            ) : (
              /* Step 2: Preview & Consent */
              <div className="space-y-4 text-xs">
                {previewError && (
                  <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 flex items-start space-x-2">
                    <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                    <span>{previewError}</span>
                  </div>
                )}

                <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-purple-50 text-[#635BFF] border border-purple-100">
                      {previewData.course_code}
                    </span>
                    <span className="font-mono text-xs font-bold text-slate-700">{previewData.class_code}</span>
                  </div>
                  <h4 className="font-bold text-slate-900 text-sm">{previewData.class_name}</h4>
                  <p className="text-[11px] text-slate-600">{previewData.course_title}</p>
                  <div className="text-[11px] text-slate-500 pt-1 border-t border-slate-200">
                    Instructor: <strong className="text-slate-800">{previewData.teacher_name}</strong>
                  </div>
                </div>

                {/* Consent Section (Design Rules & Step D.13/14) */}
                <div className="p-3.5 bg-amber-50/70 border border-amber-200 rounded-xl space-y-2">
                  <div className="flex items-center space-x-1.5 text-amber-800 font-bold text-xs">
                    <Shield className="w-4 h-4 text-amber-600 flex-shrink-0" />
                    <span>Student Data Consent</span>
                  </div>
                  <p className="text-[11px] text-slate-700 leading-relaxed">
                    {previewData.consent_text}
                  </p>
                </div>

                <label className="flex items-start space-x-2.5 p-2 rounded-lg hover:bg-slate-50 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={consentAccepted}
                    onChange={(e) => setConsentAccepted(e.target.checked)}
                    className="mt-0.5 rounded text-[#635BFF] focus:ring-[#635BFF]"
                  />
                  <span className="text-xs text-slate-800 font-medium select-none leading-snug">
                    I agree to share my learning progress and baseline scores with this instructor.
                  </span>
                </label>

                <div className="flex items-center justify-between pt-2 border-t border-slate-100">
                  <button
                    type="button"
                    onClick={() => {
                      setPreviewData(null);
                      setPreviewError(null);
                      setConsentAccepted(false);
                    }}
                    className="px-3 py-2 text-slate-600 hover:text-slate-900 font-semibold"
                  >
                    Back
                  </button>
                  <div className="flex items-center space-x-2">
                    <button
                      type="button"
                      onClick={() => setShowJoinModal(false)}
                      className="px-3 py-2 border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-xl font-semibold"
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      disabled={!consentAccepted || joinSubmitting}
                      onClick={handleConfirmJoin}
                      className="px-4 py-2 bg-[#635BFF] hover:bg-[#5349e0] text-white rounded-xl font-semibold shadow-xs disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      {joinSubmitting ? 'Joining...' : 'Confirm & Join'}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ================================================== */}
      {/* MODAL: LEAVE CLASS CONFIRMATION (Step 2A Req 18)   */}
      {/* ================================================== */}
      {classToLeave && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4 animate-fadeIn">
          <div className="bg-white rounded-2xl shadow-xl border border-slate-200 max-w-sm w-full p-6 space-y-4 animate-scaleUp">
            <div className="w-10 h-10 rounded-full bg-rose-50 text-rose-600 flex items-center justify-center mx-auto">
              <LogOut className="w-5 h-5" />
            </div>
            <div className="text-center space-y-1.5">
              <h3 className="font-bold text-slate-900 text-sm">Leave Class Cohort?</h3>
              <p className="text-xs text-slate-500">
                Are you sure you want to leave <strong className="text-slate-800">{classToLeave.name}</strong>?
              </p>
              <p className="text-[11px] text-slate-400">
                Your teacher will lose view access immediately. Your student account, mastery scores, and learning path are NOT deleted.
              </p>
            </div>

            <div className="flex items-center justify-end space-x-2 pt-2 border-t border-slate-100 text-xs">
              <button
                type="button"
                onClick={() => setClassToLeave(null)}
                className="w-1/2 py-2 border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-xl font-semibold transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={leaveSubmitting}
                onClick={handleConfirmLeave}
                className="w-1/2 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-xl font-semibold transition-colors shadow-xs disabled:opacity-50"
              >
                {leaveSubmitting ? 'Leaving...' : 'Yes, Leave'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
