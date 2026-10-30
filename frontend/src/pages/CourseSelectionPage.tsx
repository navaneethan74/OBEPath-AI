import React, { useState, useEffect } from 'react';
import {
  CheckCircle2,
  ArrowRight,
  Layers,
  Sparkles,
  Lock,
  Play,
  AlertTriangle,
  Clock,
  BookOpen,
  ChevronDown,
  GraduationCap
} from 'lucide-react';
import { Course } from '../types';
import { useStudentLearning } from '../context/StudentLearningContext';
import { api } from '../services/api';

interface CourseSelectionPageProps {
  courses: Course[];
  activeCourseId?: number;
  onSelectCourse: (course: Course) => void;
  onNavigateProfile?: () => void;
  onSelectTopic?: (topicId: number) => void;
}

export const CourseSelectionPage: React.FC<CourseSelectionPageProps> = ({
  courses,
  activeCourseId: propActiveCourseId,
  onSelectCourse,
  onSelectTopic
}) => {
  const { studentState, setSelectedTopicForStudy, setActiveCourseId } = useStudentLearning();
  const [detailedCourse, setDetailedCourse] = useState<Course | null>(null);
  const [showCourseDropdown, setShowCourseDropdown] = useState(false);

  // Active enrolled course resolution
  const activeCourseId = propActiveCourseId || studentState?.enrolledCourse?.id || (courses.length > 0 ? courses[0].id : 1);
  const matchedCourse = courses.find((c) => c.id === activeCourseId) || courses[0] || studentState?.enrolledCourse;
  const currentCourse: Course = matchedCourse || {
    id: activeCourseId,
    code: 'CURR',
    title: 'Curriculum Course',
    description: 'Outcome-based education curriculum course and competencies.',
    category: 'Computer Science',
    level: 'Undergraduate',
    is_active: true,
    topic_count: 8,
    outcome_count: 4
  };

  // Fetch detailed course topics with rich descriptions and learning objectives from backend
  useEffect(() => {
    let isMounted = true;
    api
      .getCourse(activeCourseId)
      .then((res) => {
        if (isMounted) setDetailedCourse(res);
      })
      .catch((err) => console.error('Failed to load detailed course info', err));
    return () => {
      isMounted = false;
    };
  }, [activeCourseId]);

  // Open topic handler opening the existing topic-learning flow
  const handleOpenTopic = (topicId: number) => {
    setSelectedTopicForStudy(topicId);
    if (onSelectTopic) {
      onSelectTopic(topicId);
    }
  };

  // Course Outcomes resolution (student-friendly language)
  const getCourseSkills = () => {
    // 1. From detailed backend course outcomes if available
    if (detailedCourse?.outcomes && detailedCourse.outcomes.length > 0) {
      return detailedCourse.outcomes.map((co) => ({
        code: co.code,
        description: co.description,
        status:
          studentState?.courseOutcomeAttainment?.find((o) => o.code === co.code)?.status ||
          'In Progress'
      }));
    }
    // 2. From student state attainment if available
    if (studentState?.courseOutcomeAttainment && studentState.courseOutcomeAttainment.length > 0) {
      return studentState.courseOutcomeAttainment.map((co) => ({
        code: co.code,
        description: co.description,
        status: co.status || 'In Progress'
      }));
    }
    // 3. Fallback to standard syllabus competencies
    switch (currentCourse.code) {
      case 'CS201':
        return [
          {
            code: 'CO1',
            description: 'Understand fundamental linear and non-linear data structures.',
            status: 'In Progress'
          },
          {
            code: 'CO2',
            description: 'Apply data structures to solve computational problems.',
            status: 'In Progress'
          },
          {
            code: 'CO3',
            description: 'Analyze algorithm efficiency using time and space complexity.',
            status: 'In Progress'
          },
          {
            code: 'CO4',
            description:
              'Design data-structure-based solutions for real-world computational problems.',
            status: 'In Progress'
          }
        ];
      case 'CS101':
        return [
          {
            code: 'CO1',
            description: 'Understand Python syntax, control structures, and procedural execution.',
            status: 'In Progress'
          },
          {
            code: 'CO2',
            description: 'Implement modular functions and data structures (lists, dictionaries).',
            status: 'In Progress'
          },
          {
            code: 'CO3',
            description: 'Build robust programs with file I/O and exception handling.',
            status: 'In Progress'
          },
          {
            code: 'CO4',
            description: 'Apply object-oriented programming principles to solve problems.',
            status: 'In Progress'
          }
        ];
      case 'AI301':
        return [
          {
            code: 'CO1',
            description: 'Understand foundations of statistical learning and features.',
            status: 'In Progress'
          },
          {
            code: 'CO2',
            description: 'Implement supervised learning regression and classification models.',
            status: 'In Progress'
          },
          {
            code: 'CO3',
            description: 'Apply unsupervised clustering and dimensionality reduction.',
            status: 'In Progress'
          },
          {
            code: 'CO4',
            description: 'Evaluate model accuracy, validation metrics, and neural architectures.',
            status: 'In Progress'
          }
        ];
      case 'CS302':
      default:
        return [
          {
            code: 'CO1',
            description: 'Understand relational data models and relational algebra.',
            status: 'In Progress'
          },
          {
            code: 'CO2',
            description: 'Write complex SQL queries, views, subqueries, and aggregation.',
            status: 'In Progress'
          },
          {
            code: 'CO3',
            description: 'Apply database normalization (1NF–BCNF) and indexing.',
            status: 'In Progress'
          },
          {
            code: 'CO4',
            description: 'Understand transaction ACID properties and concurrency control.',
            status: 'In Progress'
          }
        ];
    }
  };

  const courseSkills = getCourseSkills();

  // Unified Topic List: combining detailedCourse topics and studentState topicMastery
  const enrolledCourseId = studentState?.enrolledCourse?.id || studentState?.studentProfile?.selected_course_id;
  const isEnrolledCourse = detailedCourse?.id === enrolledCourseId;
  const masteryByTopicId = new Map(
    (studentState?.topicMastery || []).map((tm) => [tm.topic_id, tm])
  );

  const topicsList =
    detailedCourse?.topics && detailedCourse.topics.length > 0
      ? detailedCourse.topics.map((t) => {
          const tm = isEnrolledCourse ? masteryByTopicId.get(t.id) : null;
          return {
            topic_id: t.id,
            title: t.title,
            order_index: t.order_index,
            description: t.description || t.learning_objective || '',
            mastery: tm ? Math.round(tm.mastery || 0) : 0,
            difficulty: tm?.difficulty || t.difficulty || 'Beginner',
            est_minutes: tm?.est_minutes || t.est_minutes || 40,
            is_locked: tm ? Boolean(tm.is_locked || tm.status === 'LOCKED') : false,
            status: tm ? tm.status : 'RECOMMENDED',
            unsatisfied_prerequisites: tm?.unsatisfied_prerequisites || [],
            prerequisite_details: tm?.prerequisite_details || []
          };
        })
      : (studentState?.topicMastery || []).map((tm) => ({
          topic_id: tm.topic_id,
          title: tm.title,
          order_index: tm.order_index,
          description: '',
          mastery: Math.round(tm.mastery || 0),
          difficulty: tm.difficulty || 'Beginner',
          est_minutes: tm.est_minutes || 40,
          is_locked: tm.is_locked,
          status: tm.status,
          unsatisfied_prerequisites: tm.unsatisfied_prerequisites || [],
          prerequisite_details: tm.prerequisite_details || []
        }));


  // Current Focus Topic Resolution (from real adaptive state)
  const isCourseComplete =
    Boolean(studentState?.courseCompleted) ||
    (topicsList.length > 0 && topicsList.every((t) => t.status === 'COMPLETED' || t.mastery >= 80));

  const currentFocusTopic = isCourseComplete
    ? null
    : (studentState?.currentTargetTopic &&
       studentState.currentTargetTopic.status !== 'COMPLETED' &&
       studentState.currentTargetTopic.mastery < 80
        ? studentState.currentTargetTopic
        : topicsList.find((t) => !t.is_locked && t.status !== 'COMPLETED' && t.mastery < 80) ||
          topicsList.find((t) => t.status !== 'COMPLETED' && t.mastery < 80) ||
          null);

  const getFocusWhyText = () => {
    if (!currentFocusTopic) return 'Focus on foundational concepts in this curriculum.';
    if (currentFocusTopic.mastery < 40) {
      return 'Strengthen foundational concepts in this topic before moving ahead to dependent modules.';
    }
    if (currentFocusTopic.mastery < 60) {
      return 'Build your topic mastery above 60% to unlock advanced tree and algorithm topics.';
    }
    return 'Practice key algorithmic mechanics to reach complete concept mastery.';
  };

  // Topic status resolver
  const getTopicStatusInfo = (topic: {
    mastery: number;
    is_locked: boolean;
    status: string;
  }) => {
    if (topic.is_locked) {
      return {
        label: '🔒 Locked',
        badgeClass: 'bg-slate-100 text-slate-500 border-slate-200',
        progressClass: 'bg-slate-300',
        actionLabel: 'Locked',
        isLocked: true
      };
    }
    if (topic.mastery >= 80 || topic.status === 'COMPLETED') {
      return {
        label: topic.mastery >= 80 ? '✓ Mastered' : '✓ Completed',
        badgeClass: 'bg-emerald-50 text-emerald-700 border-emerald-200',
        progressClass: 'bg-emerald-500',
        actionLabel: 'Review',
        isLocked: false
      };
    }
    if (topic.mastery >= 60) {
      return {
        label: '→ In Progress',
        badgeClass: 'bg-orange-50 text-orange-700 border-orange-200',
        progressClass: 'bg-[#EA580C]',
        actionLabel: 'Continue Learning',
        isLocked: false
      };
    }
    return {
      label: '⚠ Needs Practice',
      badgeClass: 'bg-amber-50 text-amber-700 border-amber-200',
      progressClass: 'bg-amber-500',
      actionLabel: 'Continue Learning',
      isLocked: false
    };
  };

  const totalTopicsCount = topicsList.length || currentCourse.topic_count || 8;
  const masteredTopicsCount = topicsList.filter((t) => t.mastery >= 80 || t.status === 'COMPLETED').length;

  return (
    <div className="max-w-5xl mx-auto space-y-7 pb-12">
      {/* 1. PAGE HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-5 border-b border-slate-200">
        <div>
          <div className="flex items-center space-x-2 text-xs font-semibold text-orange-700 mb-1">
            <span className="px-2.5 py-0.5 rounded-full bg-orange-50 border border-orange-200 font-medium">
              {currentCourse.title} • {currentCourse.code}
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
            My Course
          </h1>
          <p className="text-sm text-slate-500 mt-1 max-w-2xl leading-relaxed">
            {currentCourse.description ||
              'Build a strong foundation in core computer science concepts, master problem-solving techniques, and track your syllabus progress.'}
          </p>
        </div>

        {/* Course Switcher Menu (Optional View Other Enrolled Syllabi) */}
        {courses.length > 1 && (
          <div className="relative self-start sm:self-center">
            <button
              type="button"
              onClick={() => setShowCourseDropdown(!showCourseDropdown)}
              className="inline-flex items-center space-x-2 px-3.5 py-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-xl text-xs font-semibold shadow-2xs transition-all cursor-pointer"
            >
              <BookOpen className="w-3.5 h-3.5 text-orange-600" />
              <span>Switch Course</span>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
            </button>

            {showCourseDropdown && (
              <div className="absolute right-0 mt-2 w-64 bg-white rounded-2xl border border-slate-200 shadow-xl py-2 z-30 animate-fadeIn">
                <div className="px-3.5 py-1.5 text-[10px] uppercase font-bold text-slate-400 tracking-wider">
                  Select Enrolled Course
                </div>
                {courses.map((c) => (
                  <button
                    key={c.id}
                    type="button"
                    onClick={async () => {
                      await setActiveCourseId(c.id);
                      onSelectCourse(c);
                      setShowCourseDropdown(false);
                    }}
                    className={`w-full px-3.5 py-2.5 text-left text-xs flex items-center justify-between hover:bg-slate-50 transition-colors ${
                      c.id === activeCourseId ? 'font-bold text-orange-700 bg-orange-50' : 'text-slate-700'
                    }`}
                  >
                    <div>
                      <span className="block font-semibold">{c.title}</span>
                      <span className="text-[10px] text-slate-400">{c.code}</span>
                    </div>
                    {c.id === activeCourseId && <CheckCircle2 className="w-4 h-4 text-orange-600" />}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Course Selection Tabs / Pills */}
      {courses.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 pt-1 pb-1">
          {courses.map((c) => {
            const isActive = c.id === activeCourseId;
            return (
              <button
                key={c.id}
                type="button"
                onClick={async () => {
                  if (c.id !== activeCourseId) {
                    await setActiveCourseId(c.id);
                    onSelectCourse(c);
                  }
                }}
                className={`px-4 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center space-x-2 border cursor-pointer ${
                  isActive
                    ? 'bg-[#EA580C] text-white border-orange-600 shadow-xs'
                    : 'bg-white hover:bg-slate-50 text-slate-700 border-slate-200'
                }`}
              >
                <span>{c.title}</span>
                <span
                  className={`px-1.5 py-0.5 rounded text-[10px] font-mono ${
                    isActive ? 'bg-orange-800 text-white' : 'bg-slate-100 text-slate-500'
                  }`}
                >
                  {c.code}
                </span>
                {isActive && <CheckCircle2 className="w-3.5 h-3.5 text-white" />}
              </button>
            );
          })}
        </div>
      )}

      {/* 2. COURSE OVERVIEW CARD */}
      <div className="p-6 sm:p-7 bg-white rounded-2xl border border-slate-200 shadow-2xs relative overflow-hidden space-y-5">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-lg bg-orange-50 text-orange-700 border border-orange-200 font-mono font-bold text-xs">
                {currentCourse.code}
              </span>
              <span className="px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-semibold">
                Active Enrolled Course
              </span>
            </div>
            <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight mt-1">
              {currentCourse.title}
            </h2>
            <p className="text-xs sm:text-sm text-slate-600 max-w-3xl leading-relaxed pt-1">
              {currentCourse.description}
            </p>
          </div>

          <div className="flex flex-row md:flex-col items-start md:items-end justify-between gap-2 pt-2 md:pt-0 border-t md:border-t-0 border-slate-100 flex-shrink-0">
            <div className="text-left md:text-right">
              <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">
                Overall Progress
              </span>
              <span className="text-2xl font-bold text-[#EA580C]">
                {Math.round(studentState?.overallProgress || 0)}%
              </span>
            </div>
            <span className="text-xs font-medium text-slate-500">
              {masteredTopicsCount} of {totalTopicsCount} Topics Mastered
            </span>
          </div>
        </div>

        {/* Quick Attribute Pills */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4 border-t border-slate-100 text-xs">
          <div className="p-3 bg-[#F8FAFC] rounded-xl border border-slate-200 space-y-0.5">
            <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">
              Department
            </span>
            <span className="font-bold text-slate-900 truncate block">
              {currentCourse.category || 'Computer Science'}
            </span>
          </div>
          <div className="p-3 bg-[#F8FAFC] rounded-xl border border-slate-200 space-y-0.5">
            <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">
              Total Topics
            </span>
            <span className="font-bold text-slate-900 block">
              {totalTopicsCount} Modules
            </span>
          </div>
          <div className="p-3 bg-[#F8FAFC] rounded-xl border border-slate-200 space-y-0.5">
            <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">
              Course Level
            </span>
            <span className="font-bold text-slate-900 block">
              {currentCourse.level || 'Intermediate'}
            </span>
          </div>
          <div className="p-3 bg-[#F8FAFC] rounded-xl border border-slate-200 space-y-0.5">
            <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">
              Average Mastery
            </span>
            <span className="font-bold text-orange-600 block">
              {Math.round(studentState?.overallMastery || 0)}%
            </span>
          </div>
        </div>
      </div>

      {/* 3. YOUR CURRENT FOCUS CARD OR COURSE COMPLETED BANNER */}
      {isCourseComplete ? (
        <div className="p-6 sm:p-7 bg-gradient-to-r from-emerald-50 via-teal-50 to-white rounded-2xl border-2 border-emerald-400 shadow-sm space-y-4">
          <div className="flex items-center space-x-2">
            <div className="p-2 bg-emerald-100 text-emerald-700 rounded-xl">
              <CheckCircle2 className="w-5 h-5 text-emerald-600" />
            </div>
            <div>
              <div className="text-xs font-bold text-emerald-800 uppercase tracking-wider">
                Curriculum Milestone Achieved
              </div>
              <h3 className="text-lg sm:text-xl font-bold text-slate-900">
                🎉 Course Completed! All Topics Mastered
              </h3>
            </div>
          </div>
          <p className="text-xs sm:text-sm text-slate-600">
            Congratulations! You have satisfied all prerequisite requirements and achieved 100% learning outcome criteria for this curriculum. You can review any topic at any time.
          </p>
          <div className="pt-2">
            <button
              type="button"
              onClick={() => handleOpenTopic(topicsList[0]?.topic_id || 1)}
              className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs sm:text-sm font-bold shadow-sm transition-all inline-flex items-center space-x-2 cursor-pointer"
            >
              <span>Review Topics</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      ) : currentFocusTopic ? (
        <div className="p-6 sm:p-7 bg-white rounded-2xl border-2 border-[#EA580C] shadow-[0_8px_30px_rgba(234,88,12,0.08)] ring-4 ring-orange-500/10 relative overflow-hidden space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold bg-orange-50 text-orange-700 border border-orange-200">
              <Sparkles className="w-3.5 h-3.5 text-orange-600" />
              <span>Your Current Focus</span>
            </div>
            <div className="flex items-center space-x-2 text-xs text-slate-500 font-medium">
              <Clock className="w-3.5 h-3.5 text-slate-400" />
              <span>~{currentFocusTopic.est_minutes || 40} mins</span>
              <span>•</span>
              <span className="capitalize">{currentFocusTopic.difficulty || 'Beginner'}</span>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <h3 className="text-lg sm:text-xl font-bold text-slate-900 tracking-tight">
                {currentFocusTopic.title}
              </h3>
              <p className="text-xs sm:text-sm text-slate-600 max-w-2xl leading-relaxed">
                {getFocusWhyText()}
              </p>
            </div>

            <div className="text-left sm:text-right flex-shrink-0">
              <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">
                Current Mastery
              </span>
              <span className="text-xl sm:text-2xl font-bold text-orange-600">
                {Math.round(currentFocusTopic.mastery || 0)}%
              </span>
            </div>
          </div>

          <div className="pt-2 flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-t border-slate-100">
            <div className="w-full sm:max-w-xs space-y-1">
              <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                <div
                  className="bg-[#EA580C] h-full rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(currentFocusTopic.mastery || 0, 100)}%` }}
                />
              </div>
            </div>

            <button
              type="button"
              onClick={() => handleOpenTopic(currentFocusTopic.topic_id)}
              className="px-6 py-2.5 bg-[#EA580C] hover:bg-[#C2410C] text-white rounded-xl text-xs sm:text-sm font-bold shadow-sm hover:shadow-md transition-all flex items-center justify-center space-x-2 cursor-pointer self-start sm:self-auto"
            >
              <span>Continue Learning</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      ) : null}

      {/* 4. COURSE OUTCOMES / SKILLS ("Course Skills") */}
      <div className="space-y-3.5">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base sm:text-lg font-bold text-slate-900 tracking-tight">
              Course Skills
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Core competencies and capabilities you master throughout this syllabus
            </p>
          </div>
          <span className="text-xs font-semibold px-2.5 py-1 bg-slate-100 text-slate-600 rounded-lg border border-slate-200">
            {courseSkills.length} Skills
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {courseSkills.map((skill) => (
            <div
              key={skill.code}
              className="p-4 bg-white rounded-xl border border-slate-200 shadow-2xs hover:border-orange-200 transition-all space-y-2 flex flex-col justify-between"
            >
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-xs px-2.5 py-0.5 rounded-lg bg-orange-50 text-orange-700 border border-orange-200">
                    {skill.code}
                  </span>
                  <span className="text-[10px] font-semibold text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full">
                    {skill.status}
                  </span>
                </div>
                <p className="text-xs sm:text-sm font-medium text-slate-800 leading-snug">
                  {skill.description}
                </p>
              </div>

              <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
                <span className="flex items-center space-x-1">
                  <GraduationCap className="w-3.5 h-3.5 text-slate-400" />
                  <span>Curriculum Outcome</span>
                </span>
                <span className="font-semibold text-slate-600">Standardized Skill</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 5. "WHAT YOU'LL LEARN" / COURSE TOPIC GRID */}
      <div className="space-y-3.5 pt-2">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1">
          <div>
            <h3 className="text-base sm:text-lg font-bold text-slate-900 tracking-tight">
              What You'll Learn
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Comprehensive curriculum topics, learning objectives, and current mastery levels
            </p>
          </div>
          <span className="text-xs font-semibold text-slate-500 self-start sm:self-auto">
            {totalTopicsCount} Topics in Curriculum
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {topicsList.map((topic, idx) => {
            const statusInfo = getTopicStatusInfo(topic);

            return (
              <div
                key={topic.topic_id || idx}
                className={`p-5 rounded-2xl border transition-all flex flex-col justify-between space-y-4 ${
                  statusInfo.isLocked
                    ? 'bg-[#F8FAFC]/80 border-slate-200 text-slate-500'
                    : 'bg-white border-slate-200 hover:border-orange-200 hover:shadow-xs'
                }`}
              >
                <div className="space-y-2.5">
                  {/* Top Bar: Sequence + Status Badge */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div className="w-6 h-6 rounded-lg bg-slate-100 text-slate-600 text-xs font-mono font-bold flex items-center justify-center">
                        {topic.order_index || idx + 1}
                      </div>
                      <span className="text-[11px] font-medium text-slate-400">
                        Topic {topic.order_index || idx + 1}
                      </span>
                    </div>

                    <span
                      className={`inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${statusInfo.badgeClass}`}
                    >
                      <span>{statusInfo.label}</span>
                    </span>
                  </div>

                  {/* Topic Title */}
                  <h4 className="text-base font-bold text-slate-900 leading-snug">
                    {topic.title}
                  </h4>

                  {/* Short Description */}
                  {topic.description && (
                    <p className="text-xs text-slate-600 leading-relaxed line-clamp-2">
                      {topic.description}
                    </p>
                  )}
                </div>

                {/* Bottom Bar: Mastery Progress + Action */}
                <div className="pt-3 border-t border-slate-100 space-y-3">
                  <div className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-500 font-medium">Mastery</span>
                      <span className="font-bold text-slate-800">{topic.mastery}%</span>
                    </div>
                    <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${statusInfo.progressClass}`}
                        style={{ width: `${Math.min(topic.mastery, 100)}%` }}
                      />
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-1">
                    <div className="flex items-center space-x-2 text-[11px] text-slate-400">
                      <span className="flex items-center space-x-1">
                        <Clock className="w-3 h-3 text-slate-400" />
                        <span>{topic.est_minutes}m</span>
                      </span>
                      <span>•</span>
                      <span className="capitalize">{topic.difficulty}</span>
                    </div>

                    {statusInfo.isLocked ? (() => {
                      const firstUnsatisfiedPrereq = (topic as any).prerequisite_details?.find((p: any) => !p.is_satisfied);
                      const prereqSummary = firstUnsatisfiedPrereq
                        ? `Requires: ${firstUnsatisfiedPrereq.title} (${firstUnsatisfiedPrereq.current_mastery}% / ${firstUnsatisfiedPrereq.required_mastery}% required)`
                        : (topic.unsatisfied_prerequisites && topic.unsatisfied_prerequisites.length > 0
                            ? `Requires: ${topic.unsatisfied_prerequisites[0]}`
                            : 'Prerequisite mastery needed');

                      return (
                        <div className="flex flex-col items-end space-y-1.5">
                          <div className="flex items-center space-x-2">
                            <span className="px-2.5 py-1 bg-slate-100 text-slate-500 border border-slate-200 rounded-lg text-xs font-semibold flex items-center space-x-1 opacity-90">
                              <Lock className="w-3 h-3 text-slate-400" />
                              <span>Locked</span>
                            </span>
                            {firstUnsatisfiedPrereq && (
                              <button
                                type="button"
                                onClick={() => handleOpenTopic(firstUnsatisfiedPrereq.topic_id)}
                                className="px-2.5 py-1 bg-orange-50 hover:bg-orange-100 text-[#EA580C] border border-orange-200 rounded-lg text-xs font-bold transition-all flex items-center space-x-1 cursor-pointer shadow-2xs"
                                title={`Open prerequisite ${firstUnsatisfiedPrereq.title}`}
                              >
                                <span>Study Prereq</span>
                                <ArrowRight className="w-3 h-3 text-orange-600" />
                              </button>
                            )}
                          </div>
                          <span
                            className="text-[10px] text-amber-700 font-medium text-right max-w-[260px] truncate"
                            title={prereqSummary}
                          >
                            {prereqSummary}
                          </span>
                        </div>
                      );
                    })() : (
                      <button
                        type="button"
                        onClick={() => handleOpenTopic(topic.topic_id)}
                        className="px-3.5 py-1.5 bg-white hover:bg-slate-50 text-slate-700 hover:text-[#EA580C] border border-slate-200 hover:border-orange-200 rounded-xl text-xs font-semibold shadow-2xs transition-all flex items-center space-x-1 cursor-pointer"
                      >
                        <span>{statusInfo.actionLabel}</span>
                        <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
