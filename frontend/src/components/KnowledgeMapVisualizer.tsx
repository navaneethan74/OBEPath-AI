import React, { useState, useEffect, useMemo } from 'react';
import {
  CheckCircle2,
  Lock,
  ArrowRight,
  Circle,
  Sparkles,
  BookOpen,
  Layers,
  ArrowDown,
  HelpCircle,
  Bot,
  ChevronRight,
  X,
  Code2,
  Play,
  RotateCcw,
  AlertCircle,
  Compass,
  GitBranch,
  Network
} from 'lucide-react';
import { useStudentLearning } from '../context/StudentLearningContext';
import { api } from '../services/api';
import { CentralStudentTopic, KnowledgeEdge, KnowledgeNode } from '../types';

interface KnowledgeMapVisualizerProps {
  nodes?: KnowledgeNode[];
  edges?: KnowledgeEdge[];
  onSelectTopic?: (topicId: number) => void;
  onNavigateToTutor?: (topicId?: number) => void;
  onNavigateToPractice?: (topicId: number) => void;
}

type StatusKey = 'mastered' | 'current' | 'available' | 'locked';

interface TopicStatusInfo {
  key: StatusKey;
  label: string;
  symbol: string;
  color: string;
  badgeBg: string;
  textColor: string;
  borderClass: string;
  ringClass: string;
}

export const KnowledgeMapVisualizer: React.FC<KnowledgeMapVisualizerProps> = ({
  onSelectTopic,
  onNavigateToTutor
}) => {
  const { studentState, activeCourse, setSelectedTopicForStudy, activeCourseId } = useStudentLearning();

  // State
  const [selectedTopic, setSelectedTopic] = useState<CentralStudentTopic | null>(null);
  const [activeFilter, setActiveFilter] = useState<'all' | 'current' | 'available' | 'mastered' | 'locked'>('all');
  const [viewMode, setViewMode] = useState<'flow' | 'chain'>('chain');
  const [edges, setEdges] = useState<KnowledgeEdge[]>([]);

  const userId = studentState?.studentProfile?.user_id || 1;
  const courseId = studentState?.enrolledCourse?.id || activeCourseId;
  const courseTitle = studentState?.enrolledCourse?.title || activeCourse?.title || 'Selected Course';
  const courseCode = studentState?.enrolledCourse?.code || activeCourse?.code || '';

  // Load backend prerequisite edges
  useEffect(() => {
    let isMounted = true;
    api.getKnowledgeMap(userId, courseId)
      .then((data) => {
        if (isMounted && data?.edges) {
          setEdges(data.edges);
        }
      })
      .catch((err) => {
        console.warn('Could not fetch knowledge map edges:', err);
      });
    return () => {
      isMounted = false;
    };
  }, [userId, courseId]);

  // Real course topics from central student state
  const topics: CentralStudentTopic[] = useMemo(() => {
    return studentState?.topicMastery || [];
  }, [studentState?.topicMastery]);

  // Current target topic identified by the adaptive learning engine
  const currentTargetId = studentState?.currentTargetTopic?.topic_id;

  // Student-friendly status resolver using strictly backend state
  const getStatusInfo = (topic: CentralStudentTopic): TopicStatusInfo => {
    const isMastered = topic.mastery >= 80 || topic.status === 'COMPLETED';
    const isCurrent = (topic.status === 'CURRENT' || topic.topic_id === currentTargetId) && !isMastered;
    const isLocked = topic.is_locked;

    if (isMastered) {
      return {
        key: 'mastered',
        label: 'Mastered',
        symbol: '✓',
        color: '#10B981',
        badgeBg: 'bg-emerald-50 text-emerald-700 border-emerald-200',
        textColor: 'text-emerald-700',
        borderClass: 'border-emerald-200 bg-white hover:border-emerald-300',
        ringClass: 'hover:shadow-md'
      };
    }

    if (isCurrent) {
      return {
        key: 'current',
        label: 'Current',
        symbol: '→',
        color: '#EA580C',
        badgeBg: 'bg-orange-50 text-orange-700 border-orange-200',
        textColor: 'text-orange-700',
        borderClass: 'border-orange-500 bg-orange-50/25 shadow-md ring-2 ring-orange-200/80',
        ringClass: 'shadow-lg'
      };
    }

    if (isLocked) {
      return {
        key: 'locked',
        label: 'Locked',
        symbol: '🔒',
        color: '#94A3B8',
        badgeBg: 'bg-slate-100 text-slate-500 border-slate-200',
        textColor: 'text-slate-500',
        borderClass: 'border-slate-200 bg-slate-50/70 opacity-80 hover:opacity-100',
        ringClass: 'hover:shadow-xs'
      };
    }

    // Default: Available
    return {
      key: 'available',
      label: 'Available',
      symbol: '○',
      color: '#0284C7',
      badgeBg: 'bg-sky-50 text-sky-700 border-sky-200',
      textColor: 'text-sky-700',
      borderClass: 'border-slate-200 bg-white hover:border-orange-300',
      ringClass: 'hover:shadow-md'
    };
  };

  // Find the prominent active learning topic
  const currentLearningTopic = useMemo(() => {
    if (studentState?.currentTargetTopic) {
      const match = topics.find((t) => t.topic_id === studentState.currentTargetTopic?.topic_id);
      if (match && match.mastery < 80) return match;
    }
    return topics.find((t) => t.status === 'CURRENT' && t.mastery < 80) || null;
  }, [studentState?.currentTargetTopic, topics]);

  // Helper to find prerequisite topics for a given topic
  const getPrerequisitesForTopic = (t: CentralStudentTopic): CentralStudentTopic[] => {
    const directPrereqTitles = t.prerequisites || [];
    return topics.filter((other) => {
      if (other.topic_id === t.topic_id) return false;
      if (directPrereqTitles.includes(other.title)) return true;
      return edges.some((e) => e.to === String(t.topic_id) && e.from === String(other.topic_id));
    });
  };

  // Helper to find subsequent topics that depend on this topic
  const getNextTopicsForTopic = (t: CentralStudentTopic): CentralStudentTopic[] => {
    return topics.filter((other) => {
      if (other.topic_id === t.topic_id) return false;
      if (other.prerequisites?.includes(t.title)) return true;
      return edges.some((e) => e.from === String(t.topic_id) && e.to === String(other.topic_id));
    });
  };

  // Calculate dependency tier/depth dynamically from real prerequisite links
  const tieredTopics = useMemo(() => {
    const depths: Record<number, number> = {};

    const computeDepth = (t: CentralStudentTopic, visited: Set<number> = new Set()): number => {
      if (depths[t.topic_id] !== undefined) return depths[t.topic_id];
      if (visited.has(t.topic_id)) return 0; // Prevent cyclic loops
      visited.add(t.topic_id);

      const prereqs = getPrerequisitesForTopic(t);
      if (prereqs.length === 0) {
        depths[t.topic_id] = 0;
        return 0;
      }
      const maxPrereqDepth = Math.max(...prereqs.map((p) => computeDepth(p, new Set(visited))));
      const result = maxPrereqDepth + 1;
      depths[t.topic_id] = result;
      return result;
    };

    topics.forEach((t) => computeDepth(t));

    // Group into levels
    const levels: Record<number, CentralStudentTopic[]> = {};
    topics.forEach((t) => {
      const d = depths[t.topic_id] || 0;
      if (!levels[d]) levels[d] = [];
      levels[d].push(t);
    });

    const levelTitles = [
      'Foundational Topics (Start Here)',
      'Core Dependent Concepts',
      'Advanced Problem Solving',
      'Complex Applied Mastery'
    ];

    return Object.keys(levels)
      .map(Number)
      .sort((a, b) => a - b)
      .map((depth) => ({
        depth,
        title: levelTitles[depth] || `Level ${depth + 1} Topics`,
        topics: levels[depth].sort((a, b) => a.order_index - b.order_index)
      }));
  }, [topics, edges]);

  // Topic filter counts
  const filterCounts = useMemo(() => {
    return {
      all: topics.length,
      current: topics.filter((t) => getStatusInfo(t).key === 'current').length,
      available: topics.filter((t) => getStatusInfo(t).key === 'available').length,
      mastered: topics.filter((t) => getStatusInfo(t).key === 'mastered').length,
      locked: topics.filter((t) => getStatusInfo(t).key === 'locked').length
    };
  }, [topics]);

  // Filtered topics list for chain view
  const filteredTopics = useMemo(() => {
    if (activeFilter === 'all') return topics;
    return topics.filter((t) => getStatusInfo(t).key === activeFilter);
  }, [topics, activeFilter]);

  // Navigation handlers
  const handleStudy = (topicId: number) => {
    setSelectedTopicForStudy(topicId);
    if (onSelectTopic) {
      onSelectTopic(topicId);
    }
  };

  const handleAskTutor = (topicId: number) => {
    setSelectedTopicForStudy(topicId);
    if (onNavigateToTutor) {
      onNavigateToTutor(topicId);
    }
  };

  return (
    <div className="space-y-6 max-w-[1400px] mx-auto pb-12">
      {/* 1. PAGE HEADER */}
      <div className="bg-white border border-[#E2E8F0] rounded-2xl p-6 sm:p-7 shadow-[0_2px_12px_rgba(15,23,42,0.03)] flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-semibold text-orange-600 mb-1">
            <Network className="w-4 h-4 text-orange-600" />
            <span className="uppercase tracking-wider">Concept & Prerequisite Map</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
            Topic Map
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            See how your course topics connect and build on each other.
          </p>
        </div>

        {/* Dynamic Enrolled Course Badge */}
        <div className="flex items-center space-x-2.5 px-4 py-2.5 bg-orange-50/70 border border-orange-200/80 rounded-xl self-start md:self-auto shadow-xs">
          <span className="w-2 h-2 rounded-full bg-orange-500 animate-pulse" />
          <span className="text-xs sm:text-sm font-bold text-slate-900 tracking-tight">
            {courseTitle}
          </span>
          <span className="text-slate-400">•</span>
          <span className="text-xs font-semibold text-orange-700 font-mono">
            {courseCode}
          </span>
        </div>
      </div>

      {/* 2. PROMINENT CURRENT LEARNING BANNER */}
      {currentLearningTopic && (
        <div className="bg-gradient-to-r from-orange-50/90 via-white to-amber-50/50 border-2 border-orange-200 rounded-2xl p-5 sm:p-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <span className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 bg-orange-600 text-white rounded-md text-[10px] font-bold uppercase tracking-wider shadow-xs">
                <span className="w-1.5 h-1.5 rounded-full bg-white animate-ping" />
                <span>You're learning this now</span>
              </span>
              <span className="px-2 py-0.5 bg-orange-100 text-orange-800 rounded-md text-[10px] font-bold">
                → Current
              </span>
            </div>

            <div>
              <h2 className="text-lg sm:text-xl font-bold text-slate-900">
                {currentLearningTopic.title}
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                {currentLearningTopic.prerequisites && currentLearningTopic.prerequisites.length > 0
                  ? `Builds upon: ${currentLearningTopic.prerequisites.join(', ')}`
                  : 'Foundational topic • Ready for study and practice.'}
              </p>
            </div>

            {/* Mastery Progress Bar */}
            <div className="flex items-center space-x-3 pt-1 max-w-md">
              <div className="flex-1 bg-slate-100 h-2 rounded-full overflow-hidden">
                <div
                  className="bg-orange-600 h-full rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(currentLearningTopic.mastery, 100)}%` }}
                />
              </div>
              <span className="text-xs font-bold text-orange-700">
                {Math.round(currentLearningTopic.mastery)}% Mastery
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-2 self-start md:self-auto">
            <button
              onClick={() => handleAskTutor(currentLearningTopic.topic_id)}
              className="px-3.5 py-2.5 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-xl text-xs font-semibold shadow-xs transition-all flex items-center space-x-1.5 cursor-pointer"
            >
              <Bot className="w-4 h-4 text-orange-600" />
              <span>Ask AI Tutor</span>
            </button>

            <button
              onClick={() => handleStudy(currentLearningTopic.topic_id)}
              className="px-5 py-2.5 bg-orange-600 hover:bg-orange-700 active:scale-[0.99] text-white rounded-xl text-xs sm:text-sm font-bold shadow-xs hover:shadow transition-all flex items-center space-x-2 cursor-pointer"
            >
              <span>Continue Learning</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* 3. CONTROLS: COMPACT LEGEND & FILTER TABS */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white border border-[#E2E8F0] rounded-2xl p-4 shadow-xs">
        {/* Compact Legend */}
        <div className="flex flex-wrap items-center gap-2 sm:gap-3 text-xs">
          <span className="text-slate-400 font-semibold uppercase text-[10px] tracking-wider mr-1">
            Legend:
          </span>
          <div className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-700 border border-emerald-200 font-semibold text-[11px]">
            <span>✓</span>
            <span>Mastered</span>
          </div>
          <div className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-orange-50 text-orange-700 border border-orange-200 font-semibold text-[11px]">
            <span>→</span>
            <span>Current</span>
          </div>
          <div className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-sky-50 text-sky-700 border border-sky-200 font-semibold text-[11px]">
            <span>○</span>
            <span>Available</span>
          </div>
          <div className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-slate-100 text-slate-500 border border-slate-200 font-semibold text-[11px]">
            <span>🔒</span>
            <span>Locked</span>
          </div>
        </div>

        {/* View Mode Toggle: Chain vs Flow */}
        <div className="flex items-center space-x-1 bg-slate-100 p-1 rounded-xl self-start sm:self-auto">
          <button
            onClick={() => setViewMode('chain')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              viewMode === 'chain'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Step-by-Step Chain
          </button>
          <button
            onClick={() => setViewMode('flow')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              viewMode === 'flow'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Concept Hierarchy
          </button>
        </div>
      </div>

      {/* Filter Pills */}
      <div className="flex flex-wrap items-center gap-1.5">
        <button
          onClick={() => setActiveFilter('all')}
          className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
            activeFilter === 'all'
              ? 'bg-orange-600 text-white shadow-xs'
              : 'bg-white text-slate-600 hover:text-slate-900 hover:bg-slate-50 border border-slate-200'
          }`}
        >
          All Topics ({filterCounts.all})
        </button>
        {filterCounts.current > 0 && (
          <button
            onClick={() => setActiveFilter('current')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
              activeFilter === 'current'
                ? 'bg-orange-600 text-white shadow-xs'
                : 'bg-white text-slate-600 hover:text-slate-900 hover:bg-slate-50 border border-slate-200'
            }`}
          >
            → Current ({filterCounts.current})
          </button>
        )}
        <button
          onClick={() => setActiveFilter('available')}
          className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
            activeFilter === 'available'
              ? 'bg-orange-600 text-white shadow-xs'
              : 'bg-white text-slate-600 hover:text-slate-900 hover:bg-slate-50 border border-slate-200'
          }`}
        >
          ○ Available ({filterCounts.available})
        </button>
        <button
          onClick={() => setActiveFilter('mastered')}
          className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
            activeFilter === 'mastered'
              ? 'bg-orange-600 text-white shadow-xs'
              : 'bg-white text-slate-600 hover:text-slate-900 hover:bg-slate-50 border border-slate-200'
          }`}
        >
          ✓ Mastered ({filterCounts.mastered})
        </button>
        <button
          onClick={() => setActiveFilter('locked')}
          className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
            activeFilter === 'locked'
              ? 'bg-orange-600 text-white shadow-xs'
              : 'bg-white text-slate-600 hover:text-slate-900 hover:bg-slate-50 border border-slate-200'
          }`}
        >
          🔒 Locked ({filterCounts.locked})
        </button>
      </div>

      {/* 4. VISUAL TOPIC MAP CONTAINER */}
      <div className="bg-white border border-[#E2E8F0] rounded-2xl p-6 sm:p-8 shadow-[0_2px_12px_rgba(15,23,42,0.03)]">
        {/* VIEW MODE 1: STEP-BY-STEP VERTICAL CHAIN */}
        {viewMode === 'chain' && (
          <div className="max-w-2xl mx-auto space-y-4">
            {filteredTopics.map((topic, index) => {
              const status = getStatusInfo(topic);
              const prereqs = getPrerequisitesForTopic(topic);
              const nextTopics = getNextTopicsForTopic(topic);
              const isLast = index === filteredTopics.length - 1;

              return (
                <div key={topic.topic_id} className="relative">
                  {/* Topic Node Card */}
                  <div
                    onClick={() => setSelectedTopic(topic)}
                    className={`rounded-2xl border p-5 transition-all cursor-pointer ${status.borderClass} ${status.ringClass} ${
                      selectedTopic?.topic_id === topic.topic_id ? 'ring-2 ring-orange-500' : ''
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-start space-x-3.5">
                        {/* Status Icon Indicator */}
                        <div
                          className={`w-10 h-10 rounded-xl flex items-center justify-center text-sm font-bold flex-shrink-0 border ${status.badgeBg}`}
                        >
                          {status.symbol}
                        </div>

                        {/* Topic Title & Prerequisites */}
                        <div className="space-y-1">
                          <div className="flex items-center space-x-2">
                            <h3 className="text-base font-bold text-slate-900 leading-snug">
                              {topic.title}
                            </h3>
                          </div>

                          {/* Human-readable Prerequisite Notes */}
                          {topic.is_locked ? (
                            <p className="text-xs text-amber-700 flex items-center space-x-1.5 font-medium">
                              <Lock className="w-3.5 h-3.5 text-amber-600 flex-shrink-0" />
                              <span>
                                {topic.unsatisfied_prerequisites && topic.unsatisfied_prerequisites.length > 0
                                  ? `Complete ${topic.unsatisfied_prerequisites.join(' and ')} first.`
                                  : 'Locked: Prerequisite mastery required.'}
                              </span>
                            </p>
                          ) : prereqs.length > 0 ? (
                            <p className="text-xs text-slate-500">
                              Prerequisite: {prereqs.map((p) => p.title).join(', ')}
                            </p>
                          ) : (
                            <p className="text-xs text-emerald-600 font-medium">
                              Foundational concept • No prerequisites required
                            </p>
                          )}
                        </div>
                      </div>

                      {/* Right Status Badge & Mastery */}
                      <div className="flex flex-col items-end space-y-1.5 flex-shrink-0">
                        <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full border ${status.badgeBg}`}>
                          {status.symbol} {status.label}
                        </span>
                        {!topic.is_locked ? (
                          <span className="text-xs font-bold text-slate-700">
                            Mastery: {Math.round(topic.mastery)}%
                          </span>
                        ) : (
                          <span className="text-xs font-medium text-slate-400">
                            Locked
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Progress Bar for unlocked topics */}
                    {!topic.is_locked && (
                      <div className="mt-3.5 pt-3 border-t border-slate-100 flex items-center justify-between">
                        <div className="flex-1 max-w-xs bg-slate-100 h-1.5 rounded-full overflow-hidden mr-4">
                          <div
                            className="h-full rounded-full transition-all duration-500"
                            style={{
                              width: `${Math.min(topic.mastery, 100)}%`,
                              backgroundColor: status.color
                            }}
                          />
                        </div>

                        <span className="text-xs text-orange-600 font-semibold hover:underline">
                          View Details & Connected Topics →
                        </span>
                      </div>
                    )}

                    {topic.is_locked && (
                      <div className="mt-3.5 pt-3 border-t border-slate-100 flex items-center justify-between">
                        <span className="text-xs text-slate-400">
                          Click to see unlock requirements
                        </span>
                        <span className="text-xs text-orange-600 font-semibold hover:underline">
                          Why is this locked? →
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Clean Visual Relationship Connector Arrow (as specified in prompt) */}
                  {!isLast && (
                    <div className="flex flex-col items-center justify-center my-1.5">
                      <div className="w-0.5 h-3 bg-slate-300" />
                      <div className="w-5 h-5 rounded-full bg-white border border-slate-300 flex items-center justify-center text-slate-500 shadow-2xs">
                        <ArrowDown className="w-3 h-3 text-orange-600" />
                      </div>
                      <div className="w-0.5 h-3 bg-slate-300" />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* VIEW MODE 2: CONCEPT HIERARCHY WITH TIERS & CONNECTIONS */}
        {viewMode === 'flow' && (
          <div className="space-y-8">
            {tieredTopics.map((tier, tIdx) => (
              <div key={tier.depth} className="space-y-3">
                {/* Level Title Header */}
                <div className="flex items-center space-x-3">
                  <span className="text-xs font-bold uppercase tracking-wider text-orange-700 px-3 py-1 bg-orange-50 rounded-lg border border-orange-200">
                    {tier.title}
                  </span>
                  <div className="flex-1 h-px bg-slate-200" />
                </div>

                {/* Topic Cards Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {tier.topics.map((topic) => {
                    const status = getStatusInfo(topic);
                    const prereqs = getPrerequisitesForTopic(topic);
                    const nextTopics = getNextTopicsForTopic(topic);
                    const isSelected = selectedTopic?.topic_id === topic.topic_id;

                    return (
                      <div
                        key={topic.topic_id}
                        onClick={() => setSelectedTopic(topic)}
                        className={`rounded-2xl border p-5 transition-all cursor-pointer flex flex-col justify-between ${status.borderClass} ${status.ringClass} ${
                          isSelected ? 'ring-2 ring-orange-500' : ''
                        }`}
                      >
                        <div className="space-y-3">
                          {/* Top: Status Badge + Mastery */}
                          <div className="flex items-center justify-between">
                            <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full border ${status.badgeBg}`}>
                              {status.symbol} {status.label}
                            </span>
                            {!topic.is_locked ? (
                              <span className="text-xs font-bold" style={{ color: status.color }}>
                                {Math.round(topic.mastery)}%
                              </span>
                            ) : (
                              <span className="text-xs text-slate-400 font-medium">Locked</span>
                            )}
                          </div>

                          {/* Title */}
                          <h3 className="text-base font-bold text-slate-900 leading-snug">
                            {topic.title}
                          </h3>

                          {/* Prerequisites Pill List */}
                          {topic.is_locked ? (
                            <div className="p-2.5 bg-amber-50 rounded-xl border border-amber-200 text-xs text-amber-800 space-y-1">
                              <div className="font-bold flex items-center space-x-1 text-[11px]">
                                <Lock className="w-3 h-3 text-amber-600" />
                                <span>Prerequisites Needed:</span>
                              </div>
                              <p className="text-[11px] leading-tight">
                                {topic.unsatisfied_prerequisites && topic.unsatisfied_prerequisites.length > 0
                                  ? topic.unsatisfied_prerequisites.join(', ')
                                  : 'Complete prior modules first'}
                              </p>
                            </div>
                          ) : prereqs.length > 0 ? (
                            <div className="text-xs text-slate-500">
                              <span className="font-semibold text-slate-700">Depends on:</span>{' '}
                              {prereqs.map((p) => p.title).join(', ')}
                            </div>
                          ) : (
                            <div className="text-xs text-emerald-600 font-medium">
                              Foundational concept
                            </div>
                          )}
                        </div>

                        {/* Card Footer: Progress Bar and Next Links */}
                        <div className="mt-4 pt-3 border-t border-slate-100 space-y-2">
                          {!topic.is_locked && (
                            <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                              <div
                                className="h-full rounded-full transition-all duration-500"
                                style={{
                                  width: `${Math.min(topic.mastery, 100)}%`,
                                  backgroundColor: status.color
                                }}
                              />
                            </div>
                          )}

                          {nextTopics.length > 0 && (
                            <p className="text-[11px] text-slate-400 truncate">
                              Unlocks: <span className="text-slate-600 font-medium">{nextTopics.map((n) => n.title).join(', ')}</span>
                            </p>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Downward connector between tiers */}
                {tIdx < tieredTopics.length - 1 && (
                  <div className="flex items-center justify-center py-2">
                    <div className="w-6 h-6 rounded-full bg-white border border-slate-200 flex items-center justify-center text-orange-600 shadow-2xs">
                      <ArrowDown className="w-3.5 h-3.5" />
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 5. TOPIC DETAILS / LOCKED EXPLANATION MODAL */}
      {selectedTopic && (() => {
        const status = getStatusInfo(selectedTopic);
        const prereqs = getPrerequisitesForTopic(selectedTopic);
        const nextTopics = getNextTopicsForTopic(selectedTopic);
        const isLocked = selectedTopic.is_locked;

        return (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs animate-fadeIn">
            <div className="relative w-full max-w-lg bg-white rounded-2xl shadow-xl border border-slate-200 overflow-hidden">
              {/* Modal Header */}
              <div className="p-6 pb-4 border-b border-slate-100 flex items-start justify-between">
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full border ${status.badgeBg}`}>
                      {status.symbol} {status.label}
                    </span>
                    <span className="text-xs text-slate-400 font-medium">
                      Est. Time: {selectedTopic.est_minutes || 45} mins
                    </span>
                  </div>
                  <h3 className="text-xl font-bold text-slate-900 tracking-tight">
                    {selectedTopic.title}
                  </h3>
                </div>

                <button
                  onClick={() => setSelectedTopic(null)}
                  className="p-1.5 text-slate-400 hover:text-slate-700 rounded-xl hover:bg-slate-100 transition-colors cursor-pointer"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Modal Content */}
              <div className="p-6 space-y-5 max-h-[75vh] overflow-y-auto">
                {/* A. If Locked: Human-readable unlock explanation */}
                {isLocked ? (
                  <div className="space-y-4">
                    <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl space-y-2">
                      <div className="flex items-center space-x-2 text-amber-900 font-bold text-sm">
                        <Lock className="w-4 h-4 text-amber-600" />
                        <span>Why is this topic locked?</span>
                      </div>
                      <p className="text-xs text-amber-800 leading-relaxed">
                        {selectedTopic.unsatisfied_prerequisites && selectedTopic.unsatisfied_prerequisites.length > 0
                          ? `Complete ${selectedTopic.unsatisfied_prerequisites.join(' and ')} first with ≥60% mastery to unlock this topic.`
                          : 'You must satisfy the required prerequisite concepts before beginning this module.'}
                      </p>
                    </div>

                    {/* Prerequisite Breakdown */}
                    <div className="space-y-2">
                      <div className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                        Required Prerequisite Concepts
                      </div>
                      <div className="space-y-2">
                        {prereqs.map((prereq) => {
                          const prereqStatus = getStatusInfo(prereq);
                          const isSatisfied = prereq.mastery >= 60;

                          return (
                            <div
                              key={prereq.topic_id}
                              className="p-3.5 rounded-xl border border-slate-200 bg-white flex items-center justify-between"
                            >
                              <div className="space-y-0.5">
                                <span className="text-xs font-bold text-slate-900">
                                  {prereq.title}
                                </span>
                                <div className="text-[11px] text-slate-500">
                                  Required mastery: <span className="font-semibold text-slate-700">60%</span> • Current mastery:{' '}
                                  <span className={`font-semibold ${isSatisfied ? 'text-emerald-600' : 'text-amber-700'}`}>
                                    {Math.round(prereq.mastery)}%
                                  </span>
                                </div>
                              </div>

                              <div className="flex items-center space-x-2">
                                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md border ${prereqStatus.badgeBg}`}>
                                  {isSatisfied ? '✓ Ready' : 'Needs Practice'}
                                </span>
                                <button
                                  onClick={() => {
                                    setSelectedTopic(null);
                                    handleStudy(prereq.topic_id);
                                  }}
                                  className="px-2.5 py-1 text-xs font-semibold bg-orange-50 hover:bg-orange-100 text-orange-700 rounded-lg border border-orange-200 transition-colors cursor-pointer"
                                >
                                  Study →
                                </button>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                ) : (
                  /* B. If Unlocked (Current / Available / Mastered): Topic Overview */
                  <div className="space-y-4">
                    {/* Mastery Level */}
                    <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-bold text-slate-700">Your Current Mastery</span>
                        <span className="font-bold text-sm" style={{ color: status.color }}>
                          {Math.round(selectedTopic.mastery)}%
                        </span>
                      </div>
                      <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all duration-500"
                          style={{
                            width: `${Math.min(selectedTopic.mastery, 100)}%`,
                            backgroundColor: status.color
                          }}
                        />
                      </div>
                    </div>

                    {/* Prerequisite Topics */}
                    <div className="space-y-1.5">
                      <div className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                        Prerequisite Topics
                      </div>
                      {prereqs.length > 0 ? (
                        <div className="space-y-1.5">
                          {prereqs.map((prereq) => (
                            <div
                              key={prereq.topic_id}
                              className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs flex items-center justify-between"
                            >
                              <span className="font-medium text-slate-800">{prereq.title}</span>
                              <span className="text-[11px] font-bold text-emerald-600">✓ Completed ({Math.round(prereq.mastery)}%)</span>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-xs text-slate-500">
                          None. This is a foundational topic.
                        </p>
                      )}
                    </div>

                    {/* Next Connected Topics */}
                    <div className="space-y-1.5">
                      <div className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                        Next Connected Topics
                      </div>
                      {nextTopics.length > 0 ? (
                        <div className="space-y-1.5">
                          {nextTopics.map((next) => {
                            const nextStatus = getStatusInfo(next);
                            return (
                              <div
                                key={next.topic_id}
                                className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs flex items-center justify-between"
                              >
                                <span className="font-medium text-slate-800">{next.title}</span>
                                <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${nextStatus.badgeBg}`}>
                                  {nextStatus.symbol} {nextStatus.label}
                                </span>
                              </div>
                            );
                          })}
                        </div>
                      ) : (
                        <p className="text-xs text-slate-500">
                          Final topic in this concept branch.
                        </p>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Modal Footer Actions */}
              <div className="p-4 sm:p-6 pt-3 border-t border-slate-100 bg-slate-50 flex items-center justify-between gap-3">
                <button
                  onClick={() => setSelectedTopic(null)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-900 rounded-xl transition-colors cursor-pointer"
                >
                  Close
                </button>

                <div className="flex items-center space-x-2">
                  {!isLocked && (
                    <button
                      onClick={() => {
                        const tId = selectedTopic.topic_id;
                        setSelectedTopic(null);
                        handleAskTutor(tId);
                      }}
                      className="px-3.5 py-2 bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 rounded-xl text-xs font-semibold shadow-xs transition-colors flex items-center space-x-1.5 cursor-pointer"
                    >
                      <Bot className="w-4 h-4 text-orange-600" />
                      <span>Ask AI Tutor</span>
                    </button>
                  )}

                  {isLocked ? (
                    <button
                      disabled
                      className="px-4 py-2 bg-slate-200 text-slate-400 rounded-xl text-xs font-semibold cursor-not-allowed flex items-center space-x-1.5"
                    >
                      <Lock className="w-3.5 h-3.5" />
                      <span>Locked Topic</span>
                    </button>
                  ) : status.key === 'current' ? (
                    <button
                      onClick={() => {
                        const tId = selectedTopic.topic_id;
                        setSelectedTopic(null);
                        handleStudy(tId);
                      }}
                      className="px-5 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-xl text-xs sm:text-sm font-bold shadow-xs hover:shadow transition-all flex items-center space-x-1.5 cursor-pointer"
                    >
                      <span>Continue Learning</span>
                      <ArrowRight className="w-4 h-4" />
                    </button>
                  ) : status.key === 'mastered' ? (
                    <button
                      onClick={() => {
                        const tId = selectedTopic.topic_id;
                        setSelectedTopic(null);
                        handleStudy(tId);
                      }}
                      className="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs sm:text-sm font-bold shadow-xs hover:shadow transition-all flex items-center space-x-1.5 cursor-pointer"
                    >
                      <RotateCcw className="w-4 h-4" />
                      <span>Review Topic</span>
                    </button>
                  ) : (
                    <button
                      onClick={() => {
                        const tId = selectedTopic.topic_id;
                        setSelectedTopic(null);
                        handleStudy(tId);
                      }}
                      className="px-5 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-xl text-xs sm:text-sm font-bold shadow-xs hover:shadow transition-all flex items-center space-x-1.5 cursor-pointer"
                    >
                      <span>Start Learning</span>
                      <ArrowRight className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        );
      })()}
    </div>
  );
};
