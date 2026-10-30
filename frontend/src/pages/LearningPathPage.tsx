import React, { useState } from 'react';
import {
  LearningPath,
  LearningPathItem,
  PrerequisiteDetail
} from '../types';
import {
  CheckCircle2,
  Lock,
  ArrowRight,
  RotateCcw,
  Sparkles,
  ChevronDown
} from 'lucide-react';
import { useStudentLearning } from '../context/StudentLearningContext';

interface LearningPathPageProps {
  learningPath?: LearningPath | null;
  onSelectTopic: (topicId: number) => void;
  onRefreshPath: () => void;
  onNavigateToTutor?: (topicId?: number) => void;
}

interface JourneyTopic {
  topic_id: number;
  title: string;
  order_index: number;
  mastery: number;
  status: string;
  est_minutes: number;
  difficulty: string;
  is_remedial: boolean;
  recommendation_reason: string;
  prerequisites: string[];
  unsatisfied_prerequisites: string[];
  prerequisite_details?: PrerequisiteDetail[];
  is_locked: boolean;
  // Student-facing computed state
  stateCategory: 'COMPLETED' | 'CURRENT' | 'UP_NEXT' | 'LOCKED';
}

export const LearningPathPage: React.FC<LearningPathPageProps> = ({
  learningPath: propLearningPath,
  onSelectTopic,
  onRefreshPath
}) => {
  const { studentState, activeCourse, refreshStudentState, setSelectedTopicForStudy } = useStudentLearning();
  const [refreshing, setRefreshing] = useState(false);

  // Dynamic Course Header (Not Hardcoded)
  const courseTitle = studentState?.enrolledCourse?.title || activeCourse?.title || 'Selected Course';
  const courseCode = studentState?.enrolledCourse?.code || activeCourse?.code || '';

  // Real backend learning path and topic mastery records
  const activeLearningPath = studentState?.learningPath || propLearningPath;
  const rawPathItems = activeLearningPath?.items || [];
  const topicMasteryList = studentState?.topicMastery || [];

  // Assemble unified real topic list
  const sourceTopics = topicMasteryList.length > 0 ? topicMasteryList : rawPathItems;

  // Build journey topics enriched with adaptive recommendation & prerequisite information
  const enrichedTopics: JourneyTopic[] = sourceTopics.map((item: any, idx: number) => {
    const topicId = item.topic_id;
    const pathItem = rawPathItems.find((p: LearningPathItem) => p.topic_id === topicId);
    const masteryObj = topicMasteryList.find((m: any) => m.topic_id === topicId);

    const mastery = Math.round(
      typeof pathItem?.mastery_percentage === 'number'
        ? pathItem.mastery_percentage
        : typeof masteryObj?.mastery === 'number'
        ? masteryObj.mastery
        : item.mastery_percentage || item.mastery || 0
    );

    const isLockedRaw = Boolean(
      masteryObj?.is_locked ||
      pathItem?.status === 'LOCKED' ||
      item.is_locked ||
      item.status === 'LOCKED'
    );

    const isRemedial = Boolean(pathItem?.is_remedial || item.is_remedial);

    const title =
      (isRemedial && pathItem?.remedial_title) ||
      pathItem?.topic_title ||
      masteryObj?.title ||
      item.title ||
      item.topic_title ||
      `Topic ${idx + 1}`;

    return {
      topic_id: topicId,
      title,
      order_index: item.order_index || pathItem?.sequence_order || idx + 1,
      mastery,
      status: pathItem?.status || item.status || 'RECOMMENDED',
      est_minutes: item.est_minutes || pathItem?.est_minutes || 45,
      difficulty: item.difficulty || pathItem?.difficulty || 'Beginner',
      is_remedial: isRemedial,
      recommendation_reason: pathItem?.recommendation_reason || item.recommendation_reason || '',
      prerequisites: item.prerequisites || pathItem?.prerequisites || [],
      unsatisfied_prerequisites: item.unsatisfied_prerequisites || masteryObj?.unsatisfied_prerequisites || [],
      prerequisite_details: item.prerequisite_details || masteryObj?.prerequisite_details || [],
      is_locked: isLockedRaw,
      stateCategory: 'LOCKED' // Will be computed below
    };
  });

  // Determine student-facing states: ONLY 'COMPLETED', 'CURRENT', 'UP_NEXT', 'LOCKED'
  // Identify the single active current topic (highest priority uncompleted topic)
  let currentTopicId: number | null = null;

  // Check if backend designated a CURRENT target that is uncompleted and unlocked
  const explicitCurrent = enrichedTopics.find(
    (t) => (t.status === 'CURRENT' || t.topic_id === studentState?.currentTargetTopic?.topic_id) &&
           t.status !== 'COMPLETED' &&
           t.mastery < 80 &&
           !t.is_locked
  );

  if (explicitCurrent) {
    currentTopicId = explicitCurrent.topic_id;
  } else {
    // First non-completed, non-locked topic
    const firstEligible = enrichedTopics.find((t) => t.mastery < 80 && t.status !== 'COMPLETED' && !t.is_locked);
    if (firstEligible) {
      currentTopicId = firstEligible.topic_id;
    } else {
      // First non-completed topic
      const firstUncompleted = enrichedTopics.find((t) => t.mastery < 80 && t.status !== 'COMPLETED');
      if (firstUncompleted) {
        currentTopicId = firstUncompleted.topic_id;
      }
    }
  }

  // Categorize every topic strictly into: COMPLETED, CURRENT, UP_NEXT, or LOCKED
  const categorizedTopics = enrichedTopics.map((t) => {
    if (t.mastery >= 80 || t.status === 'COMPLETED') {
      return { ...t, stateCategory: 'COMPLETED' as const };
    }
    if (t.topic_id === currentTopicId) {
      return { ...t, stateCategory: 'CURRENT' as const };
    }
    if (t.is_locked || t.status === 'LOCKED' || t.unsatisfied_prerequisites.length > 0) {
      return { ...t, stateCategory: 'LOCKED' as const };
    }
    // Unlocked and uncompleted, following current
    return { ...t, stateCategory: 'UP_NEXT' as const };
  });

  // Separate topics into the personalized vertical journey structure:
  // 1. Completed topics
  // 2. Current topic (prominent active target)
  // 3. Up Next / Locked topics
  const completedTopics = categorizedTopics.filter((t) => t.stateCategory === 'COMPLETED');
  const currentTopic = categorizedTopics.find((t) => t.stateCategory === 'CURRENT');
  const upcomingTopics = categorizedTopics.filter(
    (t) => t.stateCategory !== 'COMPLETED' && t.stateCategory !== 'CURRENT'
  );

  // Ordered journey timeline items
  const journeyItems: JourneyTopic[] = [
    ...completedTopics,
    ...(currentTopic ? [currentTopic] : []),
    ...upcomingTopics
  ];

  // Top summary metrics
  const totalTopicsCount = categorizedTopics.length;
  const completedCount = completedTopics.length;
  const isCourseComplete = (completedCount === totalTopicsCount && totalTopicsCount > 0) || Boolean(studentState?.courseCompleted);
  const currentTopicTitle = currentTopic?.title || (isCourseComplete ? 'All Topics Mastered 🎉' : 'Course Curriculum Complete');

  const handleStartTopic = (topicId: number) => {
    setSelectedTopicForStudy(topicId);
    onSelectTopic(topicId);
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await onRefreshPath();
      await refreshStudentState();
    } catch (e) {
      console.error('Failed to refresh learning path', e);
    } finally {
      setRefreshing(false);
    }
  };

  // Student-friendly "Why you're learning this" helper using existing backend state
  const getWhyLearningThis = (topic: JourneyTopic): string => {
    if (topic.is_remedial || topic.mastery < 40) {
      return "This topic needs more practice before you move ahead. Strengthening these fundamentals will make upcoming concepts much clearer.";
    }
    if (topic.mastery < 60) {
      return "Recommended based on your recent performance. Reach 60%+ mastery to unlock dependent topics.";
    }
    if (topic.prerequisites && topic.prerequisites.length > 0) {
      return "Your previous topic is strong enough to continue. Complete this topic to progress further along your journey.";
    }
    if (topic.recommendation_reason && !topic.recommendation_reason.includes('G = (V, E)')) {
      return topic.recommendation_reason;
    }
    return "Recommended based on your recent performance.";
  };

  // Student-friendly unlock requirement helper (No technical IDs, no math notation)
  const getUnlockRequirement = (topic: JourneyTopic, previousTopic?: JourneyTopic): string => {
    if (topic.unsatisfied_prerequisites && topic.unsatisfied_prerequisites.length > 0) {
      // E.g. "Recursion Fundamentals (40% < 60%)" -> clean to "Complete Recursion Fundamentals first."
      const cleanName = topic.unsatisfied_prerequisites[0].split('(')[0].trim();
      return `Complete ${cleanName} first.`;
    }
    if (topic.prerequisites && topic.prerequisites.length > 0) {
      return `Complete ${topic.prerequisites.join(' and ')} first.`;
    }
    if (previousTopic) {
      return `Complete ${previousTopic.title} first.`;
    }
    return "Complete the required prerequisites first.";
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-12">
      {/* 1. PAGE HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <div className="flex items-center space-x-2 text-xs font-semibold text-orange-700 mb-1">
            <span className="px-2.5 py-0.5 rounded-full bg-orange-50 border border-orange-200 font-medium">
              {courseTitle} • {courseCode}
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
            My Learning Path
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Your personalized learning journey
          </p>
        </div>

        <button
          type="button"
          onClick={handleRefresh}
          disabled={refreshing}
          className="inline-flex items-center space-x-1.5 px-3.5 py-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-xl text-xs font-semibold shadow-2xs transition-colors self-start sm:self-auto cursor-pointer"
          title="Refresh learning path state"
        >
          <RotateCcw className={`w-3.5 h-3.5 text-orange-600 ${refreshing ? 'animate-spin' : ''}`} />
          <span>Refresh Journey</span>
        </button>
      </div>

      {/* 2. TOP SUMMARY (COMPACT & FOCUSED ON THE JOURNEY) */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {/* Course */}
        <div className="p-3.5 bg-white rounded-xl border border-slate-200 shadow-2xs">
          <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">
            Course
          </span>
          <span className="text-sm font-bold text-slate-900 truncate block mt-0.5" title={courseTitle}>
            {courseTitle}
          </span>
        </div>

        {/* Total Topics */}
        <div className="p-3.5 bg-white rounded-xl border border-slate-200 shadow-2xs">
          <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">
            Topics
          </span>
          <span className="text-sm font-bold text-slate-900 mt-0.5 block">
            {totalTopicsCount}
          </span>
        </div>

        {/* Completed */}
        <div className="p-3.5 bg-white rounded-xl border border-slate-200 shadow-2xs">
          <span className="text-[10px] uppercase font-bold text-emerald-600 block tracking-wider flex items-center space-x-1">
            <CheckCircle2 className="w-3 h-3 text-emerald-500" />
            <span>Completed</span>
          </span>
          <span className="text-sm font-bold text-slate-900 mt-0.5 block">
            {completedCount} of {totalTopicsCount}
          </span>
        </div>

        {/* Current Topic */}
        <div className="p-3.5 bg-white rounded-xl border border-orange-200 bg-orange-50/40 shadow-2xs">
          <span className="text-[10px] uppercase font-bold text-orange-700 block tracking-wider flex items-center space-x-1">
            <Sparkles className="w-3 h-3 text-orange-600" />
            <span>Current Topic</span>
          </span>
          <span className="text-sm font-bold text-slate-900 truncate block mt-0.5" title={currentTopicTitle}>
            {currentTopicTitle}
          </span>
        </div>
      </div>

      {/* 3. MAIN LEARNING JOURNEY (VERTICAL TIMELINE) */}
      <div className="pt-2">
        <div className="relative pl-6 sm:pl-8 space-y-6 before:absolute before:left-3 sm:before:left-4 before:top-4 before:bottom-4 before:w-0.5 before:bg-slate-200">
          {journeyItems.map((topic, index) => {
            const isCompleted = topic.stateCategory === 'COMPLETED';
            const isCurrent = topic.stateCategory === 'CURRENT';
            const isUpNext = topic.stateCategory === 'UP_NEXT';
            const isLocked = topic.stateCategory === 'LOCKED';

            // Find preceding topic for friendly unlock requirement
            const previousTopic = index > 0 ? journeyItems[index - 1] : undefined;

            return (
              <div key={topic.topic_id || index} className="relative group">
                {/* Timeline Node Icon Indicator */}
                <div
                  className={`absolute -left-6 sm:-left-8 top-5 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold transition-all z-10 ${
                    isCompleted
                      ? 'bg-emerald-500 text-white ring-4 ring-emerald-50'
                      : isCurrent
                      ? 'bg-[#EA580C] text-white ring-4 ring-orange-100 shadow-sm scale-110'
                      : isUpNext
                      ? 'bg-white border-2 border-[#EA580C] text-[#EA580C] ring-4 ring-slate-50'
                      : 'bg-slate-200 text-slate-500 ring-4 ring-slate-50'
                  }`}
                >
                  {isCompleted ? (
                    <CheckCircle2 className="w-3.5 h-3.5" />
                  ) : isCurrent ? (
                    <ArrowRight className="w-3.5 h-3.5" />
                  ) : isLocked ? (
                    <Lock className="w-3 h-3" />
                  ) : (
                    <span className="text-[10px]">{index + 1}</span>
                  )}
                </div>

                {/* --- A. COMPLETED TOPIC CARD --- */}
                {isCompleted && (
                  <div className="p-5 sm:p-6 bg-white rounded-2xl border border-emerald-200/80 shadow-2xs hover:border-emerald-300 transition-all">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                      <div className="space-y-1.5 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                            <span>✓ Completed</span>
                          </span>
                          <span className="text-xs text-slate-400 font-medium">
                            {topic.difficulty} • ~{topic.est_minutes} mins
                          </span>
                        </div>

                        <h3 className="text-base sm:text-lg font-bold text-slate-900">
                          {topic.title}
                        </h3>

                        {/* Mastery Percentage & Progress Bar */}
                        <div className="pt-1 space-y-1 max-w-sm">
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-slate-500 font-medium">Mastery</span>
                            <span className="font-bold text-emerald-600">
                              {topic.mastery}%
                            </span>
                          </div>
                          <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                            <div
                              className="bg-emerald-500 h-full rounded-full transition-all duration-500"
                              style={{ width: `${Math.min(topic.mastery, 100)}%` }}
                            />
                          </div>
                        </div>
                      </div>

                      {/* Review Button */}
                      <button
                        type="button"
                        onClick={() => handleStartTopic(topic.topic_id)}
                        className="px-4 py-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-xl text-xs font-semibold shadow-2xs hover:border-slate-300 transition-colors flex items-center justify-center space-x-1.5 self-start sm:self-center cursor-pointer"
                      >
                        <span>Review</span>
                        <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
                      </button>
                    </div>
                  </div>
                )}

                {/* --- B. CURRENT TOPIC CARD (MOST VISUALLY PROMINENT) --- */}
                {isCurrent && (
                  <div className="p-6 sm:p-7 bg-white rounded-2xl border-2 border-[#EA580C] shadow-[0_8px_30px_rgba(234,88,12,0.08)] ring-4 ring-orange-500/10 relative overflow-hidden transition-all">
                    {/* Top Accent Line */}
                    <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-amber-500 via-orange-500 to-orange-600" />

                    <div className="space-y-4">
                      {/* Header with Status Pill */}
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold bg-orange-50 text-orange-700 border border-orange-200">
                          <Sparkles className="w-3.5 h-3.5 text-orange-600" />
                          <span>→ Current</span>
                        </span>
                        <span className="text-xs font-medium text-slate-500">
                          {courseTitle} • ~{topic.est_minutes} mins • {topic.difficulty}
                        </span>
                      </div>

                      {/* Topic Title */}
                      <div>
                        <h2 className="text-lg sm:text-xl font-bold text-slate-900 tracking-tight">
                          {topic.title}
                        </h2>
                      </div>

                      {/* Current Mastery & Prominent Progress Bar */}
                      <div className="space-y-1.5 max-w-md">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-slate-600 font-semibold">Current Mastery</span>
                          <span className="font-bold text-orange-600 text-sm">
                            {topic.mastery}%
                          </span>
                        </div>
                        <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden">
                          <div
                            className="bg-[#EA580C] h-full rounded-full transition-all duration-500"
                            style={{ width: `${Math.min(topic.mastery, 100)}%` }}
                          />
                        </div>
                      </div>

                      {/* "Why you're learning this" Section */}
                      <div className="p-4 rounded-xl bg-[#F8FAFC] border border-slate-200 space-y-1 text-left">
                        <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">
                          Why you're learning this
                        </span>
                        <p className="text-xs sm:text-sm text-slate-700 leading-relaxed font-medium">
                          {getWhyLearningThis(topic)}
                        </p>
                      </div>

                      {/* Primary CTA: Continue Learning */}
                      <div className="pt-2">
                        <button
                          type="button"
                          onClick={() => handleStartTopic(topic.topic_id)}
                          className="w-full sm:w-auto px-7 py-3 bg-[#EA580C] hover:bg-[#C2410C] text-white rounded-xl text-sm font-bold shadow-sm hover:shadow-md transition-all flex items-center justify-center space-x-2 cursor-pointer"
                        >
                          <span>Continue Learning</span>
                          <ArrowRight className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {/* --- C. UP NEXT TOPIC CARD (UNLOCKED UPCOMING) --- */}
                {isUpNext && (
                  <div className="p-5 sm:p-6 bg-white rounded-2xl border border-slate-200 shadow-2xs hover:border-orange-200 transition-all">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                      <div className="space-y-1.5 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-orange-50 text-orange-700 border border-orange-200">
                            <span>→ Up Next</span>
                          </span>
                          <span className="text-xs text-slate-400 font-medium">
                            {topic.difficulty} • ~{topic.est_minutes} mins
                          </span>
                        </div>

                        <h3 className="text-base sm:text-lg font-bold text-slate-900">
                          {topic.title}
                        </h3>

                        {/* Mastery Percentage & Progress Bar */}
                        <div className="pt-1 space-y-1 max-w-sm">
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-slate-500 font-medium">Mastery</span>
                            <span className="font-semibold text-slate-700">
                              {topic.mastery}%
                            </span>
                          </div>
                          <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                            <div
                              className="bg-slate-300 h-full rounded-full transition-all duration-500"
                              style={{ width: `${Math.min(topic.mastery, 100)}%` }}
                            />
                          </div>
                        </div>
                      </div>

                      {/* Start Learning Button */}
                      <button
                        type="button"
                        onClick={() => handleStartTopic(topic.topic_id)}
                        className="px-4 py-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-xl text-xs font-semibold shadow-2xs hover:border-[#EA580C] hover:text-[#EA580C] transition-colors flex items-center justify-center space-x-1.5 self-start sm:self-center cursor-pointer"
                      >
                        <span>Start Learning</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                )}

                {/* --- D. LOCKED TOPIC CARD --- */}
                {isLocked && (() => {
                  const firstUnsatisfiedPrereq = topic.prerequisite_details?.find((p) => !p.is_satisfied);
                  const prereqMasteryText = firstUnsatisfiedPrereq
                    ? `${firstUnsatisfiedPrereq.current_mastery}%`
                    : `${topic.mastery}%`;
                  const prereqNameText = firstUnsatisfiedPrereq?.title || 'Prerequisite topic';
                  const requiredMasteryVal = firstUnsatisfiedPrereq?.required_mastery || 60;

                  return (
                    <div className="p-5 sm:p-6 bg-[#F8FAFC]/90 rounded-2xl border border-slate-200 shadow-2xs transition-all text-slate-600">
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                        <div className="space-y-2 flex-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-600 border border-slate-200">
                              <Lock className="w-3 h-3 text-slate-500" />
                              <span>🔒 Locked</span>
                            </span>
                            <span className="text-xs text-slate-400 font-medium">
                              {topic.difficulty} • ~{topic.est_minutes} mins
                            </span>
                          </div>

                          <h3 className="text-base sm:text-lg font-semibold text-slate-700">
                            {topic.title}
                          </h3>

                          {/* Student-Friendly Unlock Requirement & Prerequisite Mastery Target */}
                          <div className="space-y-1.5 text-xs pt-0.5">
                            <p className="text-amber-800 font-medium flex items-center space-x-1.5 bg-amber-50/70 p-2 rounded-lg border border-amber-200/50">
                              <Lock className="w-3.5 h-3.5 text-amber-600 flex-shrink-0" />
                              <span>
                                {firstUnsatisfiedPrereq
                                  ? `Prerequisite Required: Complete ${prereqNameText} to reach ${requiredMasteryVal}% mastery.`
                                  : getUnlockRequirement(topic, previousTopic)}
                              </span>
                            </p>
                            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-slate-500 px-0.5">
                              <span>Prerequisite: <strong className="text-slate-700">{prereqNameText}</strong></span>
                              <span>•</span>
                              <span>Required mastery: <strong className="text-slate-700">{requiredMasteryVal}%</strong></span>
                              <span>•</span>
                              <span>Current prerequisite mastery: <strong className="text-orange-600 font-bold">{prereqMasteryText}</strong></span>
                            </div>
                          </div>
                        </div>

                        {/* Action buttons */}
                        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 self-start sm:self-center">
                          <span className="px-3.5 py-2 bg-slate-100 text-slate-400 border border-slate-200 rounded-xl text-xs font-semibold flex items-center justify-center space-x-1.5 opacity-80 cursor-not-allowed">
                            <Lock className="w-3.5 h-3.5" />
                            <span>Locked</span>
                          </span>
                          {firstUnsatisfiedPrereq && (
                            <button
                              type="button"
                              onClick={() => handleStartTopic(firstUnsatisfiedPrereq.topic_id)}
                              className="px-4 py-2 bg-[#EA580C] hover:bg-[#C2410C] text-white rounded-xl text-xs font-bold shadow-xs hover:shadow-md transition-all flex items-center justify-center space-x-1.5 cursor-pointer whitespace-nowrap"
                              title={`Study ${firstUnsatisfiedPrereq.title} to unlock this topic`}
                            >
                              <span>Unlock: Study Prerequisite</span>
                              <ArrowRight className="w-3.5 h-3.5" />
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })()}

                {/* Sub-node Timeline Arrow Indicator */}
                {index < journeyItems.length - 1 && (
                  <div className="flex items-center justify-center py-1 -my-2 text-slate-300">
                    <ChevronDown className="w-4 h-4 text-slate-300" />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
