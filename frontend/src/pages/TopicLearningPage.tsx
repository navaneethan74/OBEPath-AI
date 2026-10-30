import React, { useState, useEffect } from 'react';
import {
  BookOpen,
  Code,
  CheckCircle,
  FileCheck2,
  ExternalLink,
  Bot,
  Play,
  ArrowLeft,
  Sparkles,
  AlertTriangle,
  Send,
  HelpCircle,
  Award,
  ChevronRight,
  RefreshCw,
  Layers,
  Wrench,
  TrendingUp,
  CheckCircle2,
  XCircle,
  ShieldCheck,
  Zap,
  Copy,
  Check,
  Globe,
  Video
} from 'lucide-react';
import { api } from '../services/api';
import { useStudentLearning } from '../context/StudentLearningContext';
import { DynamicPracticeAssessment } from '../components/DynamicPracticeAssessment';

interface TopicLearningPageProps {
  topicId: number;
  onBack: () => void;
  onTopicCompleted: () => void;
  onPathAdapted: () => void;
  onNavigateToOBE?: () => void;
  onNavigateToTutor?: (topicId?: number) => void;
  onNavigateToTopic?: (topicId: number) => void;
  onNavigateToLearningPath?: () => void;
}

export const TopicLearningPage: React.FC<TopicLearningPageProps> = ({
  topicId,
  onBack,
  onTopicCompleted,
  onPathAdapted,
  onNavigateToOBE,
  onNavigateToTutor,
  onNavigateToTopic,
  onNavigateToLearningPath
}) => {
  const { activeCourseId, studentState, refreshStudentState, completeTopic } = useStudentLearning();
  const userId = studentState?.studentProfile?.user_id || 1;
  const [activeTab, setActiveTab] = useState<'modalities' | 'quiz' | 'resources'>('modalities');
  const [modalityIndex, setModalityIndex] = useState<number>(0);
  const [topicData, setTopicData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [isCompleting, setIsCompleting] = useState(false);
  const [completionError, setCompletionError] = useState<string | null>(null);
  const [completionSuccess, setCompletionSuccess] = useState<string | null>(null);

  const currentTopicMastery = studentState?.topicMastery?.find((t: any) => t.topic_id === topicId);
  const isTopicLocked = Boolean(currentTopicMastery?.is_locked || (currentTopicMastery?.status === 'LOCKED'));
  const lockExplanation = currentTopicMastery?.unsatisfied_prerequisites?.length
    ? `Prerequisites required: ${currentTopicMastery.unsatisfied_prerequisites.join(', ')}`
    : 'Prerequisite mastery threshold not met. Complete prerequisites first.';
  const isAlreadyCompleted = Boolean(
    currentTopicMastery?.status === 'COMPLETED' ||
    (currentTopicMastery && (currentTopicMastery.mastery ?? 0) >= 100)
  );

  // Practice state
  const [practiceAnswer, setPracticeAnswer] = useState<string | null>(null);
  const [practiceFeedback, setPracticeFeedback] = useState<string | null>(null);

  // AI Tutor in-topic mini chat
  const [tutorChatLog, setTutorChatLog] = useState<{ sender: 'user' | 'bot'; text: string }[]>([]);
  const [tutorLoading, setTutorLoading] = useState(false);

  // Generative AI Teaching Methodology state (Step 5 of closed loop)
  const [generativeData, setGenerativeData] = useState<any>(null);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [userCustomPrompt, setUserCustomPrompt] = useState<string>('');
  const [pedagogicalStyle, setPedagogicalStyle] = useState<string>('Adaptive Intuition');
  const [copiedCode, setCopiedCode] = useState<boolean>(false);

  const modalityKeys = ['explanation', 'analogy', 'worked_example', 'code', 'visual', 'practice'];

  const loadGenerativeModality = async (
    idx = modalityIndex,
    prompt = userCustomPrompt,
    style = pedagogicalStyle
  ) => {
    setIsGenerating(true);
    try {
      const key = modalityKeys[idx] || 'explanation';
      const res = await api.generateTopicModality(topicId, key, prompt, style, userId);
      setGenerativeData(res);
    } catch (err) {
      console.error('Failed to generate modality content', err);
    } finally {
      setIsGenerating(false);
    }
  };

  const loadTopic = async () => {
    setLoading(true);
    try {
      let t: any = null;
      // 1. Direct dedicated topic API call (primary source)
      try {
        t = await api.getTopic(Number(topicId));
      } catch (e) {
        // Fall back to course lookup if direct topic endpoint fails
      }

      // 2. If direct fetch didn't return resources or was null, inspect the current/enrolled course
      if (!t || !t.resources || t.resources.length === 0) {
        const targetCourseId = activeCourseId || studentState?.enrolledCourse?.id;
        if (targetCourseId) {
          try {
            const course = await api.getCourse(targetCourseId);
            const match = course.topics?.find((x: any) => Number(x.id) === Number(topicId));
            if (match) {
              t = { ...match, resources: (match.resources && match.resources.length > 0) ? match.resources : (t?.resources || []) };
            }
          } catch (e) {
            // Fallback search across courses
          }
        }
      }

      // 3. Fallback search across all courses if still not found
      if (!t) {
        const courses = await api.getCourses().catch(() => []);
        for (const c of courses) {
          const fullCourse = await api.getCourse(c.id).catch(() => null);
          const match = fullCourse?.topics?.find((x: any) => Number(x.id) === Number(topicId));
          if (match) {
            t = match;
            break;
          }
        }
      }

      // 4. Ensure resources are populated via getTopicResources if resources array is still empty
      if (t && (!t.resources || t.resources.length === 0)) {
        try {
          const res = await api.getTopicResources(Number(topicId));
          if (res && res.length > 0) {
            t = { ...t, resources: res };
          }
        } catch (e) {
          // ignore
        }
      }

      // 5. Minimal fallback structure if topic not in DB
      if (!t) {
        t = {
          id: Number(topicId),
          title: `Topic ${topicId}`,
          code: `TOPIC-${topicId}`,
          learning_objective: 'Understand and apply outcome-based concepts and problem solving techniques.',
          difficulty: 'Intermediate',
          est_minutes: 45,
          outcomes: ['CO1', 'CO2'],
          resources: []
        };
      }
      setTopicData(t);
    } catch (err) {
      console.error('Failed to load topic details', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTopic();
  }, [topicId]);

  useEffect(() => {
    if (activeTab === 'modalities') {
      loadGenerativeModality(modalityIndex, userCustomPrompt, pedagogicalStyle);
    }
  }, [topicId, modalityIndex, activeTab]);

  const handleTutorQuickAction = async (action: string) => {
    setTutorLoading(true);
    try {
      const res = await api.chatWithTutor(topicId, '', action, activeCourseId || undefined, undefined, userId);
      setTutorChatLog((prev) => [
        ...prev,
        { sender: 'user', text: `Action: ${action.replace('_', ' ')}` },
        { sender: 'bot', text: res.reply }
      ]);
    } catch (err) {
      console.error('Tutor chat failed', err);
    } finally {
      setTutorLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div className="flex items-center space-x-3">
          <button
            onClick={onBack}
            className="p-2 bg-white hover:bg-slate-50 text-slate-700 hover:text-slate-900 border border-slate-200 rounded-lg transition-colors shadow-xs"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-mono px-2 py-0.5 bg-orange-50 text-orange-600 border border-orange-200 rounded-md font-bold">
                {topicData?.code || `TOPIC-${topicId}`}
              </span>
              <h2 className="text-2xl font-bold text-slate-900 tracking-tight">
                {topicData?.title || `Topic ${topicId}`}
              </h2>
            </div>
            <p className="text-xs text-orange-600 mt-1 font-medium">
              Target Outcomes: {topicData?.outcomes?.length ? topicData.outcomes.join(', ') : 'Fundamental Course Outcomes'}
            </p>
          </div>
        </div>

        <div className="flex flex-col items-end space-y-1">
          <div className="flex items-center space-x-3">
            <button
              onClick={async () => {
                if (isCompleting) return;
                setCompletionError(null);
                setCompletionSuccess(null);
                if (isTopicLocked) {
                  setCompletionError(`Topic is locked. ${lockExplanation}`);
                  return;
                }
                try {
                  setIsCompleting(true);
                  const res = await completeTopic(topicId);
                  if (res?.alreadyCompleted) {
                    setCompletionSuccess('Topic is already completed.');
                  } else {
                    setCompletionSuccess('Topic marked completed! Learning path and Course Outcomes updated.');
                  }
                  await refreshStudentState();
                  if (onPathAdapted) {
                    onPathAdapted();
                  }
                } catch (e: any) {
                  const errorMsg = e?.message || 'Failed to complete topic';
                  setCompletionError(errorMsg);
                } finally {
                  setIsCompleting(false);
                }
              }}
              disabled={isCompleting || isTopicLocked || isAlreadyCompleted}
              title={isTopicLocked ? `Locked: ${lockExplanation}` : (isAlreadyCompleted ? 'Topic already completed' : 'Mark Topic Completed')}
              className={`px-4 py-2 text-white rounded-lg text-xs font-semibold shadow-sm transition-all flex items-center space-x-1.5 ${
                isAlreadyCompleted
                  ? 'bg-emerald-700 opacity-90 cursor-default'
                  : isTopicLocked
                  ? 'bg-slate-400 opacity-60 cursor-not-allowed'
                  : 'bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 cursor-pointer'
              }`}
            >
              <CheckCircle className={`w-4 h-4 ${isCompleting ? 'animate-spin' : ''}`} />
              <span>
                {isCompleting
                  ? 'Completing...'
                  : isAlreadyCompleted
                  ? 'Topic Completed ✓'
                  : isTopicLocked
                  ? 'Topic Locked 🔒'
                  : 'Mark Topic Completed'}
              </span>
            </button>
          </div>
          {isTopicLocked && (
            <p className="text-[11px] text-amber-600 font-medium max-w-xs text-right">
              {lockExplanation}
            </p>
          )}
        </div>
      </div>

      {/* Completion Error Banner */}
      {completionError && (
        <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-xl text-xs flex items-center justify-between shadow-xs">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 flex-shrink-0 text-red-600" />
            <span className="font-medium">{completionError}</span>
          </div>
          <button
            onClick={() => setCompletionError(null)}
            className="text-red-500 hover:text-red-800 text-xs font-bold ml-2 cursor-pointer"
          >
            ✕
          </button>
        </div>
      )}

      {/* Completion Success Banner */}
      {completionSuccess && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-700 rounded-xl text-xs flex items-center justify-between shadow-xs">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 flex-shrink-0 text-emerald-600" />
            <span className="font-medium">{completionSuccess}</span>
          </div>
          <button
            onClick={() => setCompletionSuccess(null)}
            className="text-emerald-500 hover:text-emerald-800 text-xs font-bold ml-2 cursor-pointer"
          >
            ✕
          </button>
        </div>
      )}

      {/* Learning Objective Callout */}
      <div className="p-4 bg-white border border-[#E2E8F0] rounded-xl flex items-start space-x-3 shadow-xs">
        <div className="p-2 bg-orange-50 text-orange-600 rounded-lg flex-shrink-0">
          <Award className="w-5 h-5" />
        </div>
        <div>
          <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
            Course Learning Objective (OBE Mapped)
          </div>
          <p className="text-xs sm:text-sm text-slate-800 mt-0.5 font-medium">
            "{topicData?.learning_objective || 'Understand and apply outcome-based concepts and problem solving techniques.'}"
          </p>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-200 space-x-2 overflow-x-auto pb-1">
        <button
          onClick={() => setActiveTab('modalities')}
          className={`flex items-center space-x-2 px-4 py-2 text-xs font-semibold rounded-t-lg transition-all ${
            activeTab === 'modalities'
              ? 'bg-white text-orange-600 border-t-2 border-[#EA580C] border-x border-slate-200'
              : 'text-slate-500 hover:text-slate-900 hover:bg-slate-50'
          }`}
        >
          <BookOpen className="w-4 h-4" />
          <span>Step 7: AI Concept Learning (6 Modalities)</span>
        </button>

        <button
          onClick={() => setActiveTab('quiz')}
          className={`flex items-center space-x-2 px-4 py-2 text-xs font-semibold rounded-t-lg transition-all ${
            activeTab === 'quiz'
              ? 'bg-white text-orange-600 border-t-2 border-[#EA580C] border-x border-slate-200'
              : 'text-slate-500 hover:text-slate-900 hover:bg-slate-50'
          }`}
        >
          <FileCheck2 className="w-4 h-4" />
          <span>Practice & Adaptive Assessment</span>
        </button>

        <button
          onClick={() => setActiveTab('resources')}
          className={`flex items-center space-x-2 px-4 py-2 text-xs font-semibold rounded-t-lg transition-all ${
            activeTab === 'resources'
              ? 'bg-white text-orange-600 border-t-2 border-[#EA580C] border-x border-slate-200'
              : 'text-slate-500 hover:text-slate-900 hover:bg-slate-50'
          }`}
        >
          <BookOpen className="w-4 h-4" />
          <span>Faculty & Curated Resources</span>
        </button>
      </div>

      {/* TAB 1: STEP 5 & 7 GENERATIVE AI CONCEPT LEARNING (6 MODALITIES + CUSTOM REQUESTS) */}
      {activeTab === 'modalities' && (
        <div className="space-y-6">
          {/* Generative AI Teaching Assistant Control Suite */}
          <div className="bg-white border border-[#E2E8F0] rounded-2xl p-5 sm:p-6 space-y-4 shadow-[0_4px_20px_rgba(15,23,42,0.04)]">
            <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-100">
              <div className="flex items-center space-x-2.5">
                <div className="p-2 bg-orange-50 text-orange-600 rounded-xl border border-orange-200">
                  <Sparkles className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <h3 className="text-base font-bold text-slate-900">Generative AI Teaching Assistant</h3>
                    <span className="text-[10px] font-mono font-bold px-2 py-0.5 bg-orange-50 text-orange-600 border border-orange-200 rounded-md">
                      10-Step Loop: Step 5
                    </span>
                  </div>
                  <p className="text-xs text-slate-500">
                    Teaching methodology is dynamic & generative as per your request — not static!
                  </p>
                </div>
              </div>

              {/* Regenerate Button */}
              <button
                onClick={() => loadGenerativeModality(modalityIndex, userCustomPrompt, pedagogicalStyle)}
                disabled={isGenerating}
                className="px-3.5 py-1.5 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-lg text-xs font-semibold flex items-center space-x-1.5 shadow-xs transition-colors disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 text-orange-600 ${isGenerating ? 'animate-spin' : ''}`} />
                <span>{isGenerating ? 'Synthesizing...' : 'Regenerate Content'}</span>
              </button>
            </div>

            {/* User Custom Request Input Bar */}
            <div className="space-y-2">
              <label className="text-[11px] font-bold uppercase tracking-wider text-slate-500 flex items-center justify-between">
                <span>Ask AI to Generate Teaching Content as Per Your Request:</span>
                <span className="text-[10px] text-slate-400 font-normal">Press Enter or click Generate</span>
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={userCustomPrompt}
                  onChange={(e) => setUserCustomPrompt(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      loadGenerativeModality(modalityIndex, userCustomPrompt, pedagogicalStyle);
                    }
                  }}
                  placeholder="E.g., 'Explain using an e-commerce cart analogy', 'Show step-by-step memory stack trace', 'Explain for a beginner in Python'..."
                  className="flex-1 px-4 py-2.5 bg-white border border-slate-200 focus:border-orange-500 focus:ring-2 focus:ring-orange-100 rounded-xl text-xs text-slate-900 placeholder:text-slate-400 transition-all outline-hidden shadow-2xs"
                />
                <button
                  onClick={() => loadGenerativeModality(modalityIndex, userCustomPrompt, pedagogicalStyle)}
                  disabled={isGenerating}
                  className="px-4 py-2.5 bg-[#EA580C] hover:bg-[#C2410C] disabled:opacity-50 text-white rounded-xl text-xs font-bold shadow-xs transition-colors flex items-center space-x-1.5 flex-shrink-0"
                >
                  <Sparkles className={`w-3.5 h-3.5 ${isGenerating ? 'animate-spin' : ''}`} />
                  <span>{isGenerating ? 'Generating...' : 'Generate with AI'}</span>
                </button>
              </div>
            </div>

            {/* Pedagogical Style Quick Selectors */}
            <div className="space-y-1.5 pt-1">
              <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Select Teaching Methodology Style:
              </div>
              <div className="flex flex-wrap gap-1.5">
                {[
                  { label: 'Adaptive Intuition', icon: '💡' },
                  { label: 'Real-World Analogy', icon: '🌐' },
                  { label: 'Step-by-Step Tracing', icon: '📝' },
                  { label: 'Code & Implementation', icon: '💻' },
                  { label: 'Visual Memory Diagram', icon: '📊' },
                  { label: 'Socratic Inquiry', icon: '🔍' },
                  { label: 'Mathematical Rigor', icon: '📐' }
                ].map((s) => (
                  <button
                    key={s.label}
                    onClick={() => {
                      setPedagogicalStyle(s.label);
                      loadGenerativeModality(modalityIndex, userCustomPrompt, s.label);
                    }}
                    className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-all flex items-center space-x-1 ${
                      pedagogicalStyle === s.label
                        ? 'bg-[#EA580C] text-white shadow-xs'
                        : 'bg-[#F8FAFC] text-slate-600 hover:text-slate-900 hover:bg-slate-100 border border-slate-200'
                    }`}
                  >
                    <span>{s.icon}</span>
                    <span>{s.label}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Modality Selector Tabs */}
          <div className="p-2 bg-white border border-[#E2E8F0] rounded-xl flex flex-wrap gap-2 shadow-xs">
            {[
              { label: '1. Simple Explanation', icon: '💡' },
              { label: '2. Real-World Analogy', icon: '🌐' },
              { label: '3. Step-by-Step Example', icon: '📝' },
              { label: '4. Code Implementation', icon: '💻' },
              { label: '5. Visual Explanation', icon: '📊' },
              { label: '6. Practice Questions', icon: '🎯' }
            ].map((m, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setModalityIndex(idx);
                  loadGenerativeModality(idx, userCustomPrompt, pedagogicalStyle);
                }}
                className={`px-3 py-2 rounded-lg text-xs font-semibold transition-all flex items-center space-x-1.5 ${
                  modalityIndex === idx
                    ? 'bg-[#EA580C] text-white shadow-xs'
                    : 'bg-[#F8FAFC] text-slate-600 hover:text-slate-900 hover:bg-slate-100 border border-slate-200'
                }`}
              >
                <span>{m.icon}</span>
                <span>{m.label}</span>
              </button>
            ))}
          </div>

          {/* DYNAMIC GENERATIVE TEACHING CANVAS */}
          {isGenerating ? (
            <div className="bg-white border border-[#E2E8F0] rounded-2xl p-10 text-center space-y-4 shadow-[0_4px_20px_rgba(15,23,42,0.04)] animate-pulse">
              <div className="w-12 h-12 rounded-2xl bg-orange-50 text-orange-600 flex items-center justify-center mx-auto border border-orange-200">
                <Sparkles className="w-6 h-6 animate-spin" />
              </div>
              <div className="space-y-1">
                <h4 className="text-base font-bold text-slate-900">
                  Generative AI is Synthesizing Your Lesson...
                </h4>
                <p className="text-xs text-slate-500 max-w-md mx-auto">
                  Adapting pedagogical methodology for "{topicData?.title || 'Active Topic'}" based on your requested style: <strong>{pedagogicalStyle}</strong>.
                </p>
              </div>
            </div>
          ) : (
            <div className="bg-white border border-[#E2E8F0] rounded-2xl p-6 sm:p-7 space-y-6 shadow-[0_4px_20px_rgba(15,23,42,0.04)]">
              {/* Dynamic Lesson Header */}
              <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-100">
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="inline-flex items-center space-x-1.5 px-3 py-1 bg-orange-50 text-orange-600 border border-orange-200 rounded-full text-xs font-semibold">
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>{generativeData?.pedagogical_style || pedagogicalStyle} Mode</span>
                    </span>
                    <span className="text-xs text-slate-400 font-mono">
                      {topicData?.code || 'TOPIC'} • {generativeData?.modality || modalityKeys[modalityIndex]}
                    </span>
                  </div>
                  <h3 className="text-xl font-bold text-slate-900">
                    {generativeData?.topic_title || topicData?.title || 'Generative Concept Module'}
                  </h3>
                </div>

                <div className="text-right">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                    Target OBE Outcomes
                  </span>
                  <span className="text-xs font-mono font-bold text-orange-600">
                    {topicData?.outcomes?.join(', ') || 'CO1, CO2'}
                  </span>
                </div>
              </div>

              {/* Main Content Markdown Render */}
              <div className="prose prose-sm max-w-none text-slate-700 leading-relaxed space-y-3">
                {generativeData?.content_markdown ? (
                  <div className="space-y-3 text-xs sm:text-sm">
                    {generativeData.content_markdown.split('\n\n').map((paragraph: string, pIdx: number) => {
                      if (paragraph.startsWith('### ')) {
                        return (
                          <h4 key={pIdx} className="text-base font-bold text-slate-900 pt-2 pb-1 border-b border-slate-100">
                            {paragraph.replace('### ', '')}
                          </h4>
                        );
                      } else if (paragraph.startsWith('#### ')) {
                        return (
                          <h5 key={pIdx} className="text-sm font-bold text-orange-600 pt-1">
                            {paragraph.replace('#### ', '')}
                          </h5>
                        );
                      } else if (paragraph.startsWith('> ')) {
                        return (
                          <blockquote key={pIdx} className="p-4 bg-[#F8FAFC] border-l-4 border-[#EA580C] rounded-r-xl text-slate-800 italic my-2">
                            {paragraph.replace('> ', '')}
                          </blockquote>
                        );
                      } else if (paragraph.startsWith('```')) {
                        const lines = paragraph.split('\n');
                        const code = lines.slice(1, lines.length - 1).join('\n');
                        return (
                          <pre key={pIdx} className="p-4 bg-[#F8FAFC] border border-slate-200 rounded-xl font-mono text-xs text-slate-800 overflow-x-auto my-2">
                            <code>{code}</code>
                          </pre>
                        );
                      } else if (paragraph.startsWith('|')) {
                        return (
                          <div key={pIdx} className="overflow-x-auto my-2">
                            <pre className="text-xs font-mono text-slate-700 bg-[#F8FAFC] p-3 rounded-lg border border-slate-200">
                              {paragraph}
                            </pre>
                          </div>
                        );
                      } else {
                        return (
                          <p key={pIdx} className="text-slate-700 leading-relaxed">
                            {paragraph}
                          </p>
                        );
                      }
                    })}
                  </div>
                ) : (
                  <p className="text-sm text-slate-600">
                    {topicData?.learning_objective || 'Exploring fundamental principles and algorithmic mechanics.'}
                  </p>
                )}
              </div>

              {/* Visual ASCII Diagram Display */}
              {generativeData?.visual_ascii && (
                <div className="p-4 bg-[#F8FAFC] border border-slate-200 rounded-xl space-y-2">
                  <div className="flex items-center justify-between text-xs font-bold text-slate-800">
                    <span className="flex items-center space-x-1.5">
                      <span>📊</span>
                      <span>Visual Memory & Structural Diagram</span>
                    </span>
                    <span className="text-[10px] text-slate-400 font-mono">Formal Graph Representation G=(V,E)</span>
                  </div>
                  <pre className="p-4 bg-white border border-slate-200 rounded-lg text-xs font-mono text-orange-600 overflow-x-auto leading-relaxed font-bold">
                    {generativeData.visual_ascii}
                  </pre>
                </div>
              )}

              {/* Code Snippet Box with Copy Button */}
              {generativeData?.code_snippet && (
                <div className="p-4 bg-[#F8FAFC] border border-slate-200 rounded-xl space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-800 flex items-center space-x-1.5">
                      <Code className="w-4 h-4 text-orange-600" />
                      <span>Executable Python Implementation</span>
                    </span>
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(generativeData.code_snippet);
                        setCopiedCode(true);
                        setTimeout(() => setCopiedCode(false), 2000);
                      }}
                      className="px-2.5 py-1 bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 rounded-md text-[11px] font-semibold flex items-center space-x-1 transition-colors shadow-2xs"
                    >
                      {copiedCode ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
                      <span>{copiedCode ? 'Copied!' : 'Copy Code'}</span>
                    </button>
                  </div>
                  <pre className="p-4 bg-white border border-slate-200 rounded-lg text-xs font-mono text-slate-800 overflow-x-auto leading-relaxed">
                    <code>{generativeData.code_snippet}</code>
                  </pre>
                </div>
              )}

              {/* Interactive Practice Question */}
              {generativeData?.practice_question && (
                <div className="p-5 bg-white border border-orange-200 rounded-xl space-y-3 shadow-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-orange-600 flex items-center space-x-1.5 uppercase tracking-wider">
                      <span>🎯</span>
                      <span>Generative Practice Challenge</span>
                    </span>
                    <span className="text-[10px] font-mono text-slate-400">Knowledge State Check Kt</span>
                  </div>
                  <p className="text-xs font-semibold text-slate-900">
                    {generativeData.practice_question.question}
                  </p>
                  <div className="space-y-2 pt-1">
                    {generativeData.practice_question.options?.map((opt: string, optIdx: number) => (
                      <button
                        key={optIdx}
                        onClick={() => {
                          setPracticeAnswer(opt);
                          if (opt === generativeData.practice_question.correct) {
                            setPracticeFeedback(`✓ Correct! ${generativeData.practice_question.explanation}`);
                          } else {
                            setPracticeFeedback(`✗ Incorrect. ${generativeData.practice_question.explanation}`);
                          }
                        }}
                        className={`w-full text-left p-3 rounded-lg border text-xs transition-colors flex items-center justify-between ${
                          practiceAnswer === opt
                            ? 'bg-orange-50 border-2 border-orange-500 text-slate-900 font-semibold shadow-xs'
                            : 'bg-[#F8FAFC] border-slate-200 text-slate-700 hover:bg-slate-100'
                        }`}
                      >
                        <span>{opt}</span>
                        {practiceAnswer === opt && (
                          <span className="text-xs font-bold text-orange-600">Selected</span>
                        )}
                      </button>
                    ))}
                  </div>
                  {practiceFeedback && (
                    <div className="p-3 bg-[#F8FAFC] border border-slate-200 rounded-lg text-xs text-orange-600 font-medium animate-fadeIn">
                      {practiceFeedback}
                    </div>
                  )}
                </div>
              )}

              {/* Key Pedagogical Takeaways Grid */}
              {generativeData?.key_takeaways && generativeData.key_takeaways.length > 0 && (
                <div className="space-y-2">
                  <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                    Key Pedagogical Takeaways:
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                    {generativeData.key_takeaways.map((takeaway: string, tIdx: number) => (
                      <div key={tIdx} className="p-3 bg-[#F8FAFC] border border-slate-200 rounded-xl text-xs space-y-1">
                        <div className="flex items-center space-x-1.5 text-orange-600 font-bold">
                          <CheckCircle2 className="w-3.5 h-3.5 text-orange-600" />
                          <span>Point {tIdx + 1}</span>
                        </div>
                        <p className="text-slate-700 text-[11px] leading-relaxed">
                          {takeaway}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Suggested Follow-up Generative Prompts */}
              {generativeData?.suggested_prompts && generativeData.suggested_prompts.length > 0 && (
                <div className="pt-3 border-t border-slate-100 space-y-2">
                  <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                    Try Asking Generative AI (Click to Generate):
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {generativeData.suggested_prompts.map((suggestedPrompt: string, spIdx: number) => (
                      <button
                        key={spIdx}
                        onClick={() => {
                          setUserCustomPrompt(suggestedPrompt);
                          loadGenerativeModality(modalityIndex, suggestedPrompt, pedagogicalStyle);
                        }}
                        className="px-3 py-1.5 bg-[#F8FAFC] hover:bg-orange-50 text-slate-700 hover:text-orange-600 border border-slate-200 hover:border-orange-200 rounded-lg text-xs transition-colors flex items-center space-x-1.5 shadow-2xs"
                      >
                        <Sparkles className="w-3 h-3 text-orange-600" />
                        <span>"{suggestedPrompt}"</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* In-lesson AI Tutor Assistant */}
          <div className="bg-white border border-[#E2E8F0] rounded-xl p-5 space-y-3 shadow-xs">
            <div className="text-xs font-bold text-slate-900 flex items-center space-x-1.5">
              <Bot className="w-4 h-4 text-orange-600" />
              <span>Ask AI Tutor to Explain Differently:</span>
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => handleTutorQuickAction('explain_simply')}
                disabled={tutorLoading}
                className="px-3 py-1.5 bg-white hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-semibold border border-slate-200 transition-colors shadow-xs"
              >
                💡 Explain Simply
              </button>
              <button
                onClick={() => handleTutorQuickAction('give_analogy')}
                disabled={tutorLoading}
                className="px-3 py-1.5 bg-white hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-semibold border border-slate-200 transition-colors shadow-xs"
              >
                🌐 Give Analogy
              </button>
              <button
                onClick={() => handleTutorQuickAction('trace_stack')}
                disabled={tutorLoading}
                className="px-3 py-1.5 bg-white hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-semibold border border-slate-200 transition-colors shadow-xs"
              >
                📊 Trace Call Stack
              </button>
            </div>

            {tutorChatLog.length > 0 && (
              <div className="mt-3 p-3 bg-[#F8FAFC] rounded-lg border border-slate-200 space-y-2 max-h-48 overflow-y-auto text-xs">
                {tutorChatLog.map((c, i) => (
                  <div
                    key={i}
                    className={`p-2.5 rounded-lg ${
                      c.sender === 'user'
                        ? 'bg-orange-50 text-orange-600 ml-6 font-medium border border-orange-200'
                        : 'bg-white border border-slate-200 text-slate-800 mr-6 shadow-xs'
                    }`}
                  >
                    {c.text}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: DYNAMIC TOPIC PRACTICE & ASSESSMENT */}
      {activeTab === 'quiz' && (
        <div className="space-y-6">
          <DynamicPracticeAssessment
            key={`${activeCourseId}-${topicId}`}
            topicId={topicId}
            topicTitle={topicData?.title}
            courseId={activeCourseId}
            mode="practice"
            onComplete={async () => {
              await refreshStudentState();
              if (onPathAdapted) {
                onPathAdapted();
              }
            }}
            onReviewTopic={() => setActiveTab('modalities')}
            onNavigateToTutor={(tId) => onNavigateToTutor?.(tId)}
            onNavigateToTopic={(tId) => onNavigateToTopic?.(tId)}
            onNavigateToLearningPath={onNavigateToLearningPath}
          />
        </div>
      )}

      {/* TAB 3: TOPIC STUDY RESOURCES & EXTERNAL LINKS */}
      {activeTab === 'resources' && (() => {
        const allResources: any[] = topicData?.resources || [];

        // Categorize resources into three distinct pedagogical groups
        const isVideo = (r: any) => {
          const t = (r.resource_type || r.type || '').toLowerCase();
          const u = (r.url || '').toLowerCase();
          return t.includes('video') || u.includes('youtube.com') || u.includes('youtu.be');
        };

        const isPractice = (r: any) => {
          const t = (r.resource_type || r.type || '').toLowerCase();
          const u = (r.url || '').toLowerCase();
          return (
            t.includes('practice') ||
            t.includes('interactive') ||
            t.includes('visualizer') ||
            t.includes('simulation') ||
            u.includes('leetcode.com') ||
            u.includes('visualgo.net') ||
            u.includes('hackerrank.com') ||
            u.includes('kaggle.com') ||
            u.includes('sqlbolt.com')
          );
        };

        const readingResources = allResources.filter((r) => !isVideo(r) && !isPractice(r));
        const videoResources = allResources.filter(isVideo);
        const practiceResources = allResources.filter((r) => !isVideo(r) && isPractice(r));

        const renderResourceCard = (
          res: any,
          idx: number,
          category: 'reading' | 'video' | 'practice'
        ) => {
          const isFaculty = Boolean(res.approved_by_faculty);
          const relatedTopicTitle = topicData?.title || 'Current Topic';

          const categoryConfig = {
            reading: {
              cardBorder: 'hover:border-indigo-400',
              accentBg: 'bg-indigo-50/50',
              badgeBg: 'bg-indigo-50 text-indigo-700 border-indigo-200',
              btnClass: 'bg-indigo-50 hover:bg-indigo-600 text-indigo-700 hover:text-white border-indigo-200 hover:border-indigo-600',
              btnText: 'Read Material',
              icon: <BookOpen className="w-3.5 h-3.5" />
            },
            video: {
              cardBorder: 'hover:border-rose-400',
              accentBg: 'bg-rose-50/50',
              badgeBg: 'bg-rose-50 text-rose-700 border-rose-200',
              btnClass: 'bg-rose-50 hover:bg-rose-600 text-rose-700 hover:text-white border-rose-200 hover:border-rose-600',
              btnText: 'Watch Video',
              icon: <Video className="w-3.5 h-3.5" />
            },
            practice: {
              cardBorder: 'hover:border-emerald-400',
              accentBg: 'bg-emerald-50/50',
              badgeBg: 'bg-emerald-50 text-emerald-700 border-emerald-200',
              btnClass: 'bg-emerald-50 hover:bg-emerald-600 text-emerald-700 hover:text-white border-emerald-200 hover:border-emerald-600',
              btnText: 'Launch Practice',
              icon: <Code className="w-3.5 h-3.5" />
            }
          }[category];

          return (
            <div
              key={res.id || `${category}-${idx}`}
              className={`p-5 bg-white border border-slate-200 ${categoryConfig.cardBorder} rounded-xl flex flex-col justify-between transition-all duration-200 shadow-xs hover:shadow-md space-y-4`}
            >
              <div className="space-y-3">
                {/* Meta Header: Source & Type & Verification */}
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-[11px] font-semibold text-slate-600 flex items-center space-x-1">
                      <Globe className="w-3.5 h-3.5 text-slate-400" />
                      <span>{res.website_name || 'Educational Resource'}</span>
                    </span>
                    <span className="text-slate-300">•</span>
                    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${categoryConfig.badgeBg} flex items-center space-x-1`}>
                      {categoryConfig.icon}
                      <span>{res.resource_type || res.type || (category === 'video' ? 'Video' : category === 'practice' ? 'Practice' : 'Documentation')}</span>
                    </span>
                  </div>

                  {isFaculty ? (
                    <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                      <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                      <span>Faculty Approved</span>
                    </span>
                  ) : (
                    <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200">
                      <Sparkles className="w-3.5 h-3.5 text-amber-600" />
                      <span>Curated Verified</span>
                    </span>
                  )}
                </div>

                {/* Resource Title & Description */}
                <div>
                  <h4 className="text-sm font-bold text-slate-900 leading-snug group-hover:text-orange-600 transition-colors">
                    {res.title}
                  </h4>
                  {res.description && (
                    <p className="text-xs text-slate-600 mt-1.5 leading-relaxed">
                      {res.description}
                    </p>
                  )}
                </div>

                {/* Related Topic Pill */}
                <div className="flex items-center space-x-1.5 pt-1">
                  <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Related Topic:</span>
                  <span className="text-[11px] font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 px-2 py-0.5 rounded-md border border-slate-200 transition-colors">
                    {relatedTopicTitle}
                  </span>
                </div>
              </div>

              {/* Footer: Difficulty Level and Safe Outbound Link */}
              <div className="flex items-center justify-between pt-3 border-t border-slate-100">
                <span
                  className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
                    (res.difficulty || 'Beginner').toLowerCase() === 'advanced'
                      ? 'bg-rose-50 text-rose-700 border-rose-200'
                      : (res.difficulty || 'Beginner').toLowerCase() === 'intermediate'
                      ? 'bg-amber-50 text-amber-700 border-amber-200'
                      : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                  }`}
                >
                  {res.difficulty || 'Beginner'} Level
                </span>

                <a
                  href={res.url || '#'}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`inline-flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold border transition-all duration-200 shadow-2xs group cursor-pointer ${categoryConfig.btnClass}`}
                >
                  <span>{categoryConfig.btnText}</span>
                  <ExternalLink className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                </a>
              </div>
            </div>
          );
        };

        return (
          <div className="bg-white border border-[#E2E8F0] rounded-2xl p-6 sm:p-8 space-y-8 shadow-[0_4px_20px_rgba(15,23,42,0.04)]">
            {/* Header */}
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-orange-600 flex items-center space-x-1.5">
                <BookOpen className="w-4 h-4" />
                <span>Learning & Study Resources</span>
              </span>
              <h3 className="text-xl font-bold text-slate-900 mt-1">
                {topicData?.title || 'Topic'} Reference & Practice Catalog
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Outcome-aligned learning links organized into Reading Material, Video Lectures, and Hands-on Practice.
              </p>
            </div>

            {/* Overall Empty State */}
            {allResources.length === 0 ? (
              <div className="p-8 bg-slate-50 border border-slate-200 rounded-xl text-center space-y-3 text-xs text-slate-600">
                <div className="w-12 h-12 mx-auto rounded-full bg-orange-100 flex items-center justify-center text-orange-600 mb-2">
                  <BookOpen className="w-6 h-6" />
                </div>
                <h4 className="text-sm font-bold text-slate-800">No Verified Resources Available</h4>
                <p className="max-w-md mx-auto text-slate-500">
                  There are currently no verified external resources cataloged for {topicData?.title || 'this topic'}. Please check back shortly or consult your faculty instructor.
                </p>
                <a
                  href={`https://en.wikipedia.org/wiki/Special:Search?search=${encodeURIComponent(topicData?.title || 'Computer Science')}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center space-x-1.5 px-4 py-2 bg-white text-orange-600 hover:text-orange-700 border border-orange-200 rounded-lg font-semibold shadow-xs hover:bg-orange-50 transition-colors"
                >
                  <span>Search encyclopedic references for {topicData?.title || 'this topic'}</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </div>
            ) : (
              <div className="space-y-8">
                {/* SECTION 1: READING MATERIAL */}
                <div className="space-y-3.5">
                  <div className="flex items-center justify-between pb-2 border-b border-indigo-100">
                    <div className="flex items-center space-x-2">
                      <div className="p-1.5 bg-indigo-100 text-indigo-700 rounded-lg">
                        <BookOpen className="w-4 h-4" />
                      </div>
                      <div>
                        <h4 className="text-sm font-bold text-slate-900">Reading Material</h4>
                        <p className="text-[11px] text-slate-500">Official documentation, specifications, and deep-dive conceptual guides.</p>
                      </div>
                    </div>
                    <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">
                      {readingResources.length} {readingResources.length === 1 ? 'Resource' : 'Resources'}
                    </span>
                  </div>

                  {readingResources.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {readingResources.map((r, i) => renderResourceCard(r, i, 'reading'))}
                    </div>
                  ) : (
                    <div className="p-4 bg-slate-50 border border-dashed border-slate-200 rounded-xl text-center text-xs text-slate-500">
                      No reading materials currently assigned for this topic.
                    </div>
                  )}
                </div>

                {/* SECTION 2: WATCH VIDEO */}
                <div className="space-y-3.5">
                  <div className="flex items-center justify-between pb-2 border-b border-rose-100">
                    <div className="flex items-center space-x-2">
                      <div className="p-1.5 bg-rose-100 text-rose-700 rounded-lg">
                        <Video className="w-4 h-4" />
                      </div>
                      <div>
                        <h4 className="text-sm font-bold text-slate-900">Watch Video</h4>
                        <p className="text-[11px] text-slate-500">Curated lectures, video explanations, and step-by-step walkthroughs.</p>
                      </div>
                    </div>
                    <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200">
                      {videoResources.length} {videoResources.length === 1 ? 'Resource' : 'Resources'}
                    </span>
                  </div>

                  {videoResources.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {videoResources.map((r, i) => renderResourceCard(r, i, 'video'))}
                    </div>
                  ) : (
                    <div className="p-4 bg-slate-50 border border-dashed border-slate-200 rounded-xl text-center text-xs text-slate-500">
                      No video lectures currently assigned for this topic.
                    </div>
                  )}
                </div>

                {/* SECTION 3: PRACTICE & VISUALIZERS */}
                <div className="space-y-3.5">
                  <div className="flex items-center justify-between pb-2 border-b border-emerald-100">
                    <div className="flex items-center space-x-2">
                      <div className="p-1.5 bg-emerald-100 text-emerald-700 rounded-lg">
                        <Code className="w-4 h-4" />
                      </div>
                      <div>
                        <h4 className="text-sm font-bold text-slate-900">Practice & Visualizers</h4>
                        <p className="text-[11px] text-slate-500">Interactive simulations, algorithm visualizers, and coding challenges.</p>
                      </div>
                    </div>
                    <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                      {practiceResources.length} {practiceResources.length === 1 ? 'Resource' : 'Resources'}
                    </span>
                  </div>

                  {practiceResources.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {practiceResources.map((r, i) => renderResourceCard(r, i, 'practice'))}
                    </div>
                  ) : (
                    <div className="p-4 bg-slate-50 border border-dashed border-slate-200 rounded-xl text-center text-xs text-slate-500">
                      No interactive practice visualizers currently assigned for this topic.
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        );
      })()}
    </div>
  );
};
