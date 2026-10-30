import React, { useState, useEffect, useRef } from 'react';
import {
  FileCheck2,
  CheckCircle2,
  XCircle,
  ArrowRight,
  ArrowLeft,
  RotateCcw,
  Sparkles,
  Bot,
  AlertTriangle,
  BookOpen,
  Route,
  Award,
  Layers,
  HelpCircle,
  ChevronRight,
  TrendingUp,
  Code2,
  Terminal,
  Check
} from 'lucide-react';
import { api } from '../services/api';
import { AdaptivePracticeQuestion, AssessmentEvaluationResult, CentralStudentState, CodingSubmission } from '../types';
import { useStudentLearning } from '../context/StudentLearningContext';
import { TopicCodingCompiler } from './TopicCodingCompiler';

interface DynamicPracticeAssessmentProps {
  topicId: number;
  topicTitle?: string;
  courseId?: number;
  mode?: 'practice' | 'quiz' | 'reassessment';
  onComplete?: (evalResult: AssessmentEvaluationResult, state: CentralStudentState) => void;
  onClose?: () => void;
  onReviewTopic?: () => void;
  onNavigateToTutor?: (topicId: number) => void;
  onNavigateToTopic?: (topicId: number) => void;
  onNavigateToLearningPath?: () => void;
}

export const DynamicPracticeAssessment: React.FC<DynamicPracticeAssessmentProps> = ({
  topicId,
  topicTitle,
  courseId,
  mode = 'practice',
  onComplete,
  onClose,
  onReviewTopic,
  onNavigateToTutor,
  onNavigateToTopic,
  onNavigateToLearningPath
}) => {
  const {
    activeCourseId,
    studentState,
    submitAssessment,
    refreshStudentState
  } = useStudentLearning();

  const effectiveCourseId = courseId || activeCourseId;
  const userId = studentState?.studentProfile?.user_id || 1;

  const currentTopicMeta = studentState?.topicMastery?.find((t) => t.topic_id === topicId);
  const displayTopicTitle = topicTitle || currentTopicMeta?.title || `Topic ${topicId}`;

  const [questions, setQuestions] = useState<AdaptivePracticeQuestion[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [currentIndex, setCurrentIndex] = useState<number>(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [codingSubmission, setCodingSubmission] = useState<CodingSubmission | null>(null);
  const [studentCode, setStudentCode] = useState<string>('');
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [hasCodingChallenge, setHasCodingChallenge] = useState<boolean>(true);
  const [evalResult, setEvalResult] = useState<AssessmentEvaluationResult | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);

  const loadQuestions = async () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    setLoading(true);
    setErrorMsg(null);
    setQuestions([]);
    setAnswers({});
    setCodingSubmission(null);
    setStudentCode('');
    setEvalResult(null);
    setCurrentIndex(0);

    try {
      // 1. Check if hands-on coding challenge exists for this topic
      try {
        const challenge = await api.getCodingChallenge(effectiveCourseId, topicId, displayTopicTitle, controller.signal);
        if (challenge && challenge.has_coding !== false && challenge.starter_code) {
          setHasCodingChallenge(true);
        } else {
          setHasCodingChallenge(false);
        }
      } catch (err: any) {
        if (err?.name === 'AbortError') throw err;
        setHasCodingChallenge(false);
      }

      // 2. Load 5 conceptual questions
      const q = await api.getAdaptiveQuestions(effectiveCourseId, topicId, 5, mode, userId, controller.signal);
      if (!controller.signal.aborted) {
        if (!q || q.length === 0) {
          setErrorMsg('Unable to load practice questions. Please try again.');
        } else {
          setQuestions(q);
        }
      }
    } catch (err: any) {
      if (err?.name !== 'AbortError') {
        console.error('Failed to load adaptive practice questions', err);
        setErrorMsg('Unable to load practice questions. Please try again.');
      }
    } finally {
      if (!controller.signal.aborted) {
        setLoading(false);
      }
    }
  };

  useEffect(() => {
    loadQuestions();
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [topicId, effectiveCourseId, mode]);

  const handleSelectOption = (questionId: number, optionText: string) => {
    setAnswers((prev) => ({
      ...prev,
      [String(questionId)]: optionText
    }));
  };

  const handleSubmit = async () => {
    if (submitting) return;
    if (questions.length === 0 && !studentCode.trim()) return;
    setSubmitting(true);
    setErrorMsg(null);

    try {
      let finalCodingSub = codingSubmission;
      const codeToEvaluate = studentCode.trim();

      // If code was not compiled yet, or was modified after compilation, evaluate it now (if topic has coding)
      const needsCompile = hasCodingChallenge && (!finalCodingSub || (finalCodingSub.code.trim() !== codeToEvaluate));

      if (hasCodingChallenge) {
        try {
          const challenge = await api.getCodingChallenge(effectiveCourseId, topicId, displayTopicTitle);
          if (challenge && challenge.has_coding !== false && needsCompile) {
            const codeToRun = codeToEvaluate || challenge.starter_code || '';
            const execRes = await api.compileAndRunCode(
              codeToRun,
              challenge.test_cases || [],
              challenge.id,
              4.0
            );
            finalCodingSub = {
              challenge_id: challenge.id || 'custom',
              title: challenge.title || 'Topic Coding Problem',
              topic_id: challenge.topic_id || topicId,
              code: codeToRun,
              passed_count: execRes.passed_count,
              total_count: execRes.total_count,
              percentage: execRes.percentage,
              all_passed: execRes.all_passed,
              results: execRes.results,
              execution_time_ms: execRes.execution_time_ms,
              stdout: execRes.stdout,
              stderr: execRes.stderr
            };
            setCodingSubmission(finalCodingSub);
          }
        } catch (e) {
          console.warn('Auto compile before submission encountered error', e);
        }
      } else {
        finalCodingSub = null;
      }

      const res = await submitAssessment(mode, answers, topicId, finalCodingSub || undefined);
      const evaluation: AssessmentEvaluationResult = res.evaluation || res;
      setEvalResult(evaluation);

      // Force immediate refresh of global student state
      await refreshStudentState();

      if (onComplete && (res.state || (evaluation as any).state)) {
        onComplete(evaluation, res.state || (evaluation as any).state);
      }
    } catch (err: any) {
      console.error('Practice assessment submission failed', err);
      setErrorMsg(err.message || 'Submission failed. Please check your connection and try again.');
    } finally {
      setSubmitting(false);
    }
  };

  // Find next recommended topic dynamically from updated learning path
  const nextRecommendedTopic = React.useMemo(() => {
    if (!studentState?.learningPath?.items) return null;
    const items = studentState.learningPath.items;
    // Find first item that is CURRENT or RECOMMENDED and not current topic
    const nextItem = items.find(
      (item) => item.topic_id !== topicId && (item.status === 'CURRENT' || item.status === 'RECOMMENDED')
    );
    return nextItem;
  }, [studentState, topicId, evalResult]);

  // Loading View
  if (loading) {
    return (
      <div className="bg-white border border-[#E2E8F0] rounded-2xl p-8 sm:p-12 text-center space-y-4 shadow-[0_4px_20px_rgba(15,23,42,0.04)]">
        <div className="w-12 h-12 rounded-2xl bg-orange-50 text-orange-600 flex items-center justify-center mx-auto border border-orange-200">
          <FileCheck2 className="w-6 h-6 animate-pulse" />
        </div>
        <div>
          <h3 className="text-lg font-bold text-slate-900">Loading Practice Assessment</h3>
          <p className="text-xs text-slate-500 mt-1">
            Selecting questions adapted to your cognitive mastery on <strong className="text-slate-700">{displayTopicTitle}</strong>...
          </p>
        </div>
      </div>
    );
  }

  // Error / Empty State
  if (errorMsg && questions.length === 0) {
    return (
      <div className="bg-white border border-rose-200 rounded-2xl p-8 text-center space-y-4 shadow-[0_4px_20px_rgba(15,23,42,0.04)]">
        <div className="w-12 h-12 rounded-2xl bg-rose-50 text-rose-600 flex items-center justify-center mx-auto border border-rose-200">
          <AlertTriangle className="w-6 h-6" />
        </div>
        <div className="max-w-md mx-auto space-y-1">
          <h3 className="text-base font-bold text-slate-900">Assessment Unavailable</h3>
          <p className="text-xs text-rose-700">{errorMsg}</p>
        </div>
        <div className="flex items-center justify-center gap-3 pt-2">
          <button
            onClick={loadQuestions}
            className="px-4 py-2 bg-[#EA580C] hover:bg-[#C2410C] text-white rounded-xl text-xs font-semibold shadow-xs transition-all flex items-center space-x-1.5"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Try Again</span>
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="px-4 py-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-xl text-xs font-semibold transition-all shadow-xs"
            >
              Cancel
            </button>
          )}
        </div>
      </div>
    );
  }

  // --------------------------------------------------------------------------
  // RESULT VIEW (Part 2, 4, 5, 9)
  // --------------------------------------------------------------------------
  if (evalResult) {
    const passMark = typeof evalResult.pass_mark === 'number' ? evalResult.pass_mark : 60.0;
    const isSuccess = Boolean(evalResult.passed !== undefined ? evalResult.passed : (evalResult.percentage >= passMark));
    const answeredCount = evalResult.score;
    const totalCount = evalResult.max_score;
    const masteryChange = evalResult.primary_mastery;
    const nextTopic = evalResult.next_topic || (nextRecommendedTopic ? {
      id: nextRecommendedTopic.topic_id,
      title: nextRecommendedTopic.topic_title,
      status: nextRecommendedTopic.status
    } : null);
    const isCourseFinished = Boolean(
      evalResult.course_completed ||
      studentState?.courseCompleted ||
      (studentState?.learningPath?.items && studentState.learningPath.items.length > 0 &&
       studentState.learningPath.items.every((i: any) => i.status === 'COMPLETED'))
    );

    return (
      <div className="bg-white border border-[#E2E8F0] rounded-2xl p-6 sm:p-8 space-y-6 shadow-[0_4px_20px_rgba(15,23,42,0.04)] animate-fadeIn">
        {/* Header Hero */}
        <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div className="flex items-center space-x-3">
            <div
              className={`p-3 rounded-2xl border ${
                isSuccess
                  ? 'bg-emerald-50 text-emerald-600 border-emerald-200'
                  : 'bg-amber-50 text-amber-600 border-amber-200'
              }`}
            >
              {isSuccess ? <CheckCircle2 className="w-7 h-7" /> : <AlertTriangle className="w-7 h-7" />}
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  {mode.toUpperCase()} RESULT
                </span>
                <span
                  className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                    isSuccess
                      ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                      : 'bg-amber-50 text-amber-700 border-amber-200'
                  }`}
                >
                  {isSuccess ? `PASSED (Pass Mark: ${passMark}%)` : `NEEDS PRACTICE (Required: ${passMark}%)`}
                </span>
              </div>
              <h3 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight mt-0.5">
                {isSuccess ? 'Assessment Passed ✓' : 'Assessment Attempt Recorded'}
              </h3>
              <p className="text-xs text-slate-500">
                {isSuccess
                  ? `Congratulations! You met the pass mark (${passMark}%) for `
                  : `Score was below the pass mark (${passMark}%) for `}
                <strong className="text-slate-800">{displayTopicTitle}</strong>
              </p>
            </div>
          </div>

          {onClose && (
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-slate-700 text-xs px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 transition-colors"
            >
              Close
            </button>
          )}
        </div>

        {/* Score & Mastery Stat Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="p-4 bg-[#F8FAFC] rounded-xl border border-slate-200">
            <div className="text-[10px] uppercase font-bold tracking-wider text-slate-400">Score & Pass Mark</div>
            <div className="text-2xl font-extrabold text-orange-600 font-mono mt-0.5">
              {evalResult.percentage}%
            </div>
            <div className="text-xs text-slate-500 mt-1 flex items-center justify-between">
              <span>{answeredCount} / {totalCount} correct</span>
              <span className="font-semibold text-slate-700">Pass Mark: {passMark}%</span>
            </div>
          </div>

          <div className="p-4 bg-[#F8FAFC] rounded-xl border border-slate-200">
            <div className="text-[10px] uppercase font-bold tracking-wider text-slate-400">Topic Mastery</div>
            <div className="text-lg font-bold text-slate-900 flex items-center space-x-2 mt-0.5">
              {masteryChange ? (
                <>
                  <span className="font-mono text-slate-500 text-sm">{Math.round(masteryChange.previous_mastery)}%</span>
                  <span className="text-slate-400 text-xs">➔</span>
                  <span className="font-mono text-emerald-600 font-extrabold text-xl">{Math.round(masteryChange.new_mastery)}%</span>
                </>
              ) : (
                <span className="font-mono text-emerald-600 font-extrabold text-xl">
                  {typeof evalResult.new_mastery === 'number' ? Math.round(evalResult.new_mastery) : (currentTopicMeta ? Math.round(currentTopicMeta.mastery) : Math.round(evalResult.percentage))}%
                </span>
              )}
            </div>
            <div className="text-xs text-slate-600 mt-1 font-medium capitalize">
              Status: {isSuccess ? 'COMPLETED ✓' : (masteryChange?.classification || currentTopicMeta?.classification || 'IN PROGRESS')}
            </div>
          </div>

          <div className="p-4 bg-[#F8FAFC] rounded-xl border border-slate-200">
            <div className="text-[10px] uppercase font-bold tracking-wider text-slate-400">Learning Status</div>
            <div className="text-sm font-bold text-slate-900 mt-1">
              {isSuccess ? '✓ Topic Completed' : '⚠️ Reinforcement Needed'}
            </div>
            <div className="text-[11px] text-slate-500 mt-1">
              {isSuccess ? 'Prerequisites evaluated & downstream module unlocked.' : 'Topic remains current for targeted practice.'}
            </div>
          </div>
        </div>

        {/* Hands-On Coding Practical Evaluation Result Card */}
        {evalResult.coding_result && (
          <div className="p-4 sm:p-5 bg-[#0B0F19] text-slate-100 rounded-2xl border border-slate-800 space-y-3 shadow-md">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2.5">
                <div className="p-2 bg-[#EA580C] text-white rounded-xl shadow-xs">
                  <Code2 className="w-4 h-4" />
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-[10px] uppercase font-bold tracking-wider text-orange-400">
                      Topic Coding Assessment Evaluated
                    </span>
                    <span className="px-1.5 py-0.5 bg-slate-800 text-emerald-400 border border-emerald-500/30 rounded text-[9px] font-mono">
                      Compiler Sandbox ✓
                    </span>
                  </div>
                  <h4 className="font-bold text-white text-sm">
                    {evalResult.coding_result.title || `${displayTopicTitle} Coding Problem`}
                  </h4>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <span className="text-[11px] font-mono text-slate-400">
                  Runtime: {evalResult.coding_result.execution_time_ms || 24}ms
                </span>
                <span
                  className={`px-2.5 py-1 rounded-full text-xs font-bold font-mono border ${
                    evalResult.coding_result.all_passed
                      ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                      : 'bg-amber-500/20 text-amber-400 border-amber-500/30'
                  }`}
                >
                  {evalResult.coding_result.passed_count} / {evalResult.coding_result.total_count} Test Cases Passed ({evalResult.coding_result.percentage}%)
                </span>
              </div>
            </div>

            {/* Test cases results pill list */}
            {evalResult.coding_result.results && evalResult.coding_result.results.length > 0 && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-mono">
                {evalResult.coding_result.results.map((r: any) => (
                  <div
                    key={r.test_idx}
                    className={`p-2.5 rounded-xl border flex items-center justify-between ${
                      r.passed
                        ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-200'
                        : 'bg-rose-950/20 border-rose-500/30 text-rose-200'
                    }`}
                  >
                    <span className="flex items-center space-x-1.5 font-bold">
                      {r.passed ? (
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                      ) : (
                        <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
                      )}
                      <span>Test Case #{r.test_idx}</span>
                    </span>
                    <span className="text-[10px] text-slate-400 truncate max-w-[140px]">
                      {r.input_desc}
                    </span>
                  </div>
                ))}
              </div>
            )}

            {/* Submitted code snippet */}
            {evalResult.coding_result.code && (
              <div className="pt-1 space-y-1">
                <div className="text-[10px] uppercase font-bold text-slate-400 flex items-center justify-between">
                  <span>Submitted Solution Code in Compiler:</span>
                  <span className="text-[10px] font-mono text-slate-500">Python 3.11</span>
                </div>
                <pre className="p-3 bg-[#080C14] rounded-xl text-xs font-mono text-emerald-300 overflow-x-auto border border-slate-800/80 leading-relaxed max-h-36">
                  <code>{evalResult.coding_result.code}</code>
                </pre>
              </div>
            )}
          </div>
        )}

        {/* Course Completed Celebration Screen (Rule 10) */}
        {isCourseFinished && (
          <div className="p-6 bg-gradient-to-r from-emerald-500/10 via-teal-500/10 to-orange-500/10 border-2 border-emerald-400 rounded-2xl text-center space-y-3 shadow-xs animate-fadeIn">
            <div className="w-12 h-12 mx-auto rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center">
              <Award className="w-6 h-6 stroke-[2.5]" />
            </div>
            <h3 className="text-xl font-bold text-slate-900">🎉 Course Completed!</h3>
            <p className="text-xs sm:text-sm text-slate-600 max-w-lg mx-auto leading-relaxed">
              Outstanding work! You have completed all curriculum topics in this course trajectory and fulfilled the Course Outcome mastery requirements.
            </p>
            {onNavigateToLearningPath && (
              <div className="pt-2">
                <button
                  onClick={onNavigateToLearningPath}
                  className="px-5 py-2.5 bg-[#EA580C] hover:bg-[#C2410C] text-white rounded-xl text-xs sm:text-sm font-bold shadow-xs transition-all inline-flex items-center space-x-2"
                >
                  <Route className="w-4 h-4" />
                  <span>View Learning Path</span>
                </button>
              </div>
            )}
          </div>
        )}

        {/* What You Should Do Next Banner (Part 4 & 5) */}
        <div
          className={`p-5 rounded-2xl border space-y-3 ${
            isSuccess
              ? 'bg-emerald-50/70 border-emerald-200 text-emerald-950'
              : 'bg-amber-50/70 border-amber-200 text-amber-950'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider flex items-center space-x-1.5">
              <Sparkles className="w-4 h-4 text-orange-600" />
              <span>What You Should Do Next</span>
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 bg-white rounded-md border border-slate-200 text-slate-600">
              Adaptive Feedback
            </span>
          </div>

          {isSuccess ? (
            <div className="space-y-3 text-xs">
              <p className="text-slate-700 leading-relaxed">
                Great job! You scored <strong className="text-emerald-700">{evalResult.percentage}%</strong> (Pass Mark: {passMark}%). Topic marked completed and next module unlocked in your learning path.
              </p>
              {nextTopic && !isCourseFinished && (
                <div className="p-3.5 bg-white rounded-xl border border-emerald-200 shadow-2xs flex items-center justify-between">
                  <div>
                    <div className="text-[10px] uppercase font-bold tracking-wider text-slate-400">
                      Next Unlocked Topic
                    </div>
                    <div className="text-sm font-bold text-slate-900 mt-0.5">
                      {nextTopic.title}
                    </div>
                    <div className="text-[11px] text-slate-500">
                      Eligible topic in curriculum trajectory
                    </div>
                  </div>
                  {onNavigateToTopic && (
                    <button
                      onClick={() => onNavigateToTopic(nextTopic.id)}
                      className="px-4 py-2 bg-[#EA580C] hover:bg-[#C2410C] text-white rounded-xl text-xs font-bold shadow-xs transition-all flex items-center space-x-1.5 flex-shrink-0"
                    >
                      <span>Go to Next Topic</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-3 text-xs">
              <p className="text-slate-700 leading-relaxed">
                Your score was <strong className="text-amber-800">{evalResult.percentage}%</strong> ({answeredCount} of {totalCount} correct, Pass Mark: {passMark}%). We recommend reviewing the lesson materials or retrying the assessment before moving forward.
              </p>
            </div>
          )}

          {/* Action Buttons (Requirement 7: "Go to Next Topic" (if passed) / "Retry" / "Review Lesson") */}
          <div className="flex flex-wrap items-center gap-2.5 pt-1">
            {isSuccess && nextTopic && !isCourseFinished && onNavigateToTopic && (
              <button
                onClick={() => onNavigateToTopic(nextTopic.id)}
                className="px-4 py-2 bg-[#EA580C] hover:bg-[#C2410C] text-white rounded-xl text-xs font-bold shadow-xs transition-all flex items-center space-x-1.5"
              >
                <span>Go to Next Topic</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            )}

            <button
              onClick={loadQuestions}
              className="px-4 py-2 bg-white hover:bg-slate-50 text-slate-800 border border-slate-200 rounded-xl text-xs font-semibold shadow-2xs transition-all flex items-center space-x-1.5"
            >
              <RotateCcw className="w-3.5 h-3.5 text-orange-600" />
              <span>Retry</span>
            </button>

            {onReviewTopic && (
              <button
                onClick={onReviewTopic}
                className="px-4 py-2 bg-white hover:bg-slate-50 text-slate-800 border border-slate-200 rounded-xl text-xs font-semibold shadow-2xs transition-all flex items-center space-x-1.5"
              >
                <BookOpen className="w-3.5 h-3.5 text-orange-600" />
                <span>Review Lesson</span>
              </button>
            )}

            {onNavigateToTutor && (
              <button
                onClick={() => onNavigateToTutor(topicId)}
                className="px-4 py-2 bg-orange-50 hover:bg-orange-100 text-orange-700 border border-orange-200 rounded-xl text-xs font-semibold shadow-2xs transition-all flex items-center space-x-1.5"
              >
                <Bot className="w-3.5 h-3.5" />
                <span>Ask AI Tutor</span>
              </button>
            )}

            {onNavigateToLearningPath && (
              <button
                onClick={onNavigateToLearningPath}
                className="px-4 py-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-xl text-xs font-semibold shadow-2xs transition-all flex items-center space-x-1.5"
              >
                <Route className="w-3.5 h-3.5 text-slate-400" />
                <span>View Learning Path</span>
              </button>
            )}
          </div>
        </div>

        {/* Detailed Question Review List */}
        <div className="space-y-4 pt-2">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Question-by-Question Breakdown & Explanations
            </h4>
            <span className="text-[11px] text-slate-400">
              {evalResult.question_details?.length || 0} Questions Evaluated
            </span>
          </div>

          <div className="space-y-4">
            {evalResult.question_details?.map((qd, qIdx) => (
              <div
                key={qd.question_id || qIdx}
                className={`p-5 rounded-2xl border transition-all space-y-3 ${
                  qd.is_correct
                    ? 'bg-white border-emerald-200 shadow-2xs'
                    : 'bg-white border-rose-200 shadow-2xs'
                }`}
              >
                {/* Header row */}
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center space-x-2">
                    <span
                      className={`w-6 h-6 rounded-lg flex items-center justify-center text-xs font-bold ${
                        qd.is_correct
                          ? 'bg-emerald-100 text-emerald-700'
                          : 'bg-rose-100 text-rose-700'
                      }`}
                    >
                      {qIdx + 1}
                    </span>
                    <span className="text-xs font-semibold text-slate-800">
                      {qd.is_correct ? 'Correct' : 'Incorrect'}
                    </span>
                    {qd.sub_concept && (
                      <span className="text-[10px] font-mono px-2 py-0.5 bg-slate-100 text-slate-600 rounded">
                        {qd.sub_concept}
                      </span>
                    )}
                    {qd.outcome_code && (
                      <span className="text-[10px] font-mono px-2 py-0.5 bg-orange-50 text-orange-700 border border-orange-200 rounded">
                        {qd.outcome_code}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center space-x-1.5 text-xs font-bold">
                    {qd.is_correct ? (
                      <span className="text-emerald-600 flex items-center space-x-1">
                        <CheckCircle2 className="w-4 h-4" />
                        <span>+1 Point</span>
                      </span>
                    ) : (
                      <span className="text-rose-600 flex items-center space-x-1">
                        <XCircle className="w-4 h-4" />
                        <span>0 Points</span>
                      </span>
                    )}
                  </div>
                </div>

                {/* Question Text */}
                <p className="text-xs sm:text-sm font-semibold text-slate-900 leading-snug">
                  {qd.question_text}
                </p>

                {/* Answers comparison */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs pt-1">
                  <div
                    className={`p-3 rounded-xl border ${
                      qd.is_correct
                        ? 'bg-emerald-50/60 border-emerald-200 text-emerald-900'
                        : 'bg-rose-50/60 border-rose-200 text-rose-900'
                    }`}
                  >
                    <div className="text-[10px] uppercase font-bold tracking-wider opacity-75">
                      Your Selected Answer:
                    </div>
                    <div className="font-semibold mt-0.5">
                      {qd.selected_answer || '(No answer provided)'}
                    </div>
                  </div>

                  {!qd.is_correct && (
                    <div className="p-3 bg-emerald-50/60 rounded-xl border border-emerald-200 text-emerald-900">
                      <div className="text-[10px] uppercase font-bold tracking-wider opacity-75">
                        Correct Answer:
                      </div>
                      <div className="font-semibold mt-0.5">{qd.correct_answer}</div>
                    </div>
                  )}
                </div>

                {/* Explanation */}
                {qd.explanation && (
                  <div className="p-3 bg-[#F8FAFC] rounded-xl border border-slate-200 text-xs space-y-1">
                    <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-1">
                      <Sparkles className="w-3.5 h-3.5 text-orange-600" />
                      <span>Pedagogical Explanation</span>
                    </div>
                    <p className="text-slate-700 leading-relaxed">{qd.explanation}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // --------------------------------------------------------------------------
  // ACTIVE QUESTION LIST / STEPPER VIEW (Part 1)
  // --------------------------------------------------------------------------
  const totalQuestions = questions.length + (hasCodingChallenge ? 1 : 0);
  const currentQ = currentIndex < questions.length ? questions[currentIndex] : null;
  const answeredCount = Object.keys(answers).length + (codingSubmission ? 1 : 0);

  return (
    <div className="bg-white border border-[#E2E8F0] rounded-2xl p-6 sm:p-8 space-y-6 shadow-[0_4px_20px_rgba(15,23,42,0.04)]">
      {/* Header bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-100">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-[#EA580C] text-white rounded-xl shadow-xs">
            <FileCheck2 className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-mono px-2 py-0.5 bg-orange-50 text-orange-700 border border-orange-200 rounded-md font-bold">
                {mode.toUpperCase()}
              </span>
              <h3 className="text-lg font-bold text-slate-900 tracking-tight">
                {displayTopicTitle}
              </h3>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Targeted adaptive assessment: {questions.length} conceptual questions{hasCodingChallenge ? ' + hands-on topic coding problem' : ' (pure conceptual evaluation)'}
            </p>
          </div>
        </div>

        {onClose && (
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-700 text-xs px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 transition-colors"
          >
            ✕ Exit
          </button>
        )}
      </div>

      {/* Question Stepper Navigation Bar */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs text-slate-500">
          <span>
            Question <strong className="text-slate-900">{currentIndex + 1}</strong> of{' '}
            <strong className="text-slate-900">{totalQuestions}</strong>
          </span>
          <span className="font-mono text-slate-600 font-medium">
            {answeredCount} of {totalQuestions} completed
          </span>
        </div>

        {/* Visual Pill Stepper */}
        <div className="flex flex-wrap items-center gap-1.5">
          {questions.map((q, idx) => {
            const isFilled = Boolean(answers[String(q.id)]);
            const isCur = idx === currentIndex;
            return (
              <button
                key={q.id}
                type="button"
                onClick={() => setCurrentIndex(idx)}
                className={`flex-1 min-w-[28px] h-2.5 rounded-full transition-all ${
                  isCur
                    ? 'bg-[#EA580C] ring-2 ring-orange-200'
                    : isFilled
                    ? 'bg-emerald-500'
                    : 'bg-slate-200 hover:bg-slate-300'
                }`}
                title={`Question ${idx + 1}: ${q.question_text}`}
              />
            );
          })}

          {/* Hands-On Coding Pill (only if topic supports coding) */}
          {hasCodingChallenge && (
            <button
              type="button"
              onClick={() => setCurrentIndex(questions.length)}
              className={`px-3 py-1 rounded-full text-[10px] font-bold transition-all flex items-center space-x-1 ${
                currentIndex === questions.length
                  ? 'bg-[#EA580C] text-white ring-2 ring-orange-200 shadow-xs'
                  : codingSubmission?.all_passed
                  ? 'bg-emerald-500 text-white'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-200'
              }`}
              title="Hands-On Topic Coding Challenge (In-Browser Compiler)"
            >
              <Code2 className="w-3 h-3" />
              <span>Q{totalQuestions}: Code</span>
              {codingSubmission?.all_passed && <Check className="w-2.5 h-2.5" />}
            </button>
          )}
        </div>
      </div>

      {/* Current Question: MCQ (0..4) or Coding Compiler (5) */}
      {currentIndex < questions.length && currentQ ? (
        <div className="p-6 bg-[#F8FAFC] rounded-2xl border border-slate-200 space-y-4">
          {/* Metadata badges */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="px-2.5 py-0.5 bg-white text-slate-600 border border-slate-200 rounded-md text-[10px] font-bold uppercase tracking-wider">
              {currentQ.difficulty || 'Intermediate'}
            </span>
            {currentQ.sub_concept && (
              <span className="px-2.5 py-0.5 bg-orange-50 text-orange-700 border border-orange-200 rounded-md text-[10px] font-semibold">
                {currentQ.sub_concept}
              </span>
            )}
            {currentQ.outcome_code && (
              <span className="px-2.5 py-0.5 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-md text-[10px] font-mono font-bold">
                {currentQ.outcome_code}
              </span>
            )}
          </div>

          {/* Question Text */}
          <div className="text-sm sm:text-base font-bold text-slate-900 leading-snug">
            {currentQ.question_text}
          </div>

          {/* Code snippet if present */}
          {currentQ.code_snippet && (
            <div className="p-4 bg-slate-900 text-slate-100 rounded-xl font-mono text-xs overflow-x-auto border border-slate-800 shadow-inner">
              <pre className="whitespace-pre">{currentQ.code_snippet}</pre>
            </div>
          )}

          {/* Options */}
          <div className="space-y-2 pt-2">
            {currentQ.options?.map((opt, oIdx) => {
              const isSelected = answers[String(currentQ.id)] === opt;
              const optionLetter = String.fromCharCode(65 + oIdx);

              return (
                <button
                  key={oIdx}
                  type="button"
                  onClick={() => handleSelectOption(currentQ.id, opt)}
                  className={`w-full text-left p-3.5 sm:p-4 rounded-xl border text-xs sm:text-sm transition-all flex items-center justify-between ${
                    isSelected
                      ? 'bg-white border-2 border-[#EA580C] text-slate-900 shadow-[0_2px_12px_rgba(234,88,12,0.08)]'
                      : 'bg-white border-slate-200 text-slate-700 hover:border-slate-300 hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <span
                      className={`w-6 h-6 rounded-lg flex items-center justify-center font-mono text-xs font-bold flex-shrink-0 transition-colors ${
                        isSelected
                          ? 'bg-[#EA580C] text-white shadow-xs'
                          : 'bg-slate-100 text-slate-600'
                      }`}
                    >
                      {optionLetter}
                    </span>
                    <span className="font-medium leading-relaxed">{opt}</span>
                  </div>

                  <span
                    className={`w-4 h-4 rounded-full border flex items-center justify-center flex-shrink-0 ${
                      isSelected ? 'border-[#EA580C] bg-[#EA580C]' : 'border-slate-300'
                    }`}
                  >
                    {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-white" />}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      ) : hasCodingChallenge ? (
        /* Hands-On Topic Coding Challenge with In-Browser Compiler */
        <div className="space-y-3">
          <div className="p-4 bg-gradient-to-r from-orange-50 to-amber-50/50 border border-orange-200 rounded-2xl flex flex-wrap items-center justify-between gap-3 text-xs">
            <div className="flex items-center space-x-2.5">
              <div className="p-2 bg-[#EA580C] text-white rounded-xl shadow-xs">
                <Code2 className="w-4 h-4" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-orange-700">
                    Question {totalQuestions} of {totalQuestions} • Topic Coding Question
                  </span>
                  <span className="px-2 py-0.5 bg-white text-slate-700 rounded text-[9px] font-mono border border-slate-200">
                    Compiler Sandbox
                  </span>
                </div>
                <h4 className="font-bold text-slate-900 text-sm mt-0.5">
                  Practical Code Implementation & Compiler Verification
                </h4>
              </div>
            </div>
            <div className="text-[11px] text-slate-600 font-medium">
              Topic: <strong className="text-slate-900">{displayTopicTitle}</strong>
            </div>
          </div>

          <TopicCodingCompiler
            key={`${effectiveCourseId}-${topicId}`}
            courseId={effectiveCourseId}
            topicId={topicId}
            topicTitle={displayTopicTitle}
            initialCode={studentCode}
            onCodeChange={(c) => setStudentCode(c)}
            onCompileResult={(sub) => setCodingSubmission(sub)}
          />
        </div>
      ) : null}

      {/* Submission / Server Error Banner (Rule 9) */}
      {errorMsg && (
        <div className="p-3.5 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-xs flex items-center justify-between shadow-xs">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0" />
            <span className="font-semibold">{errorMsg}</span>
          </div>
          <button
            onClick={() => setErrorMsg(null)}
            className="text-rose-500 hover:text-rose-800 text-xs px-2 py-0.5 rounded hover:bg-rose-100"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Bottom Navigation & Submission Buttons */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-slate-100">
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setCurrentIndex((prev) => Math.max(0, prev - 1))}
            disabled={currentIndex === 0}
            className="px-3.5 py-2 bg-white hover:bg-slate-50 disabled:opacity-40 text-slate-700 border border-slate-200 rounded-xl text-xs font-semibold transition-all shadow-xs flex items-center space-x-1.5"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Previous</span>
          </button>

          {currentIndex < totalQuestions - 1 ? (
            <button
              onClick={() => setCurrentIndex((prev) => Math.min(totalQuestions - 1, prev + 1))}
              className="px-3.5 py-2 bg-[#EA580C] hover:bg-[#C2410C] text-white rounded-xl text-xs font-semibold transition-all shadow-xs flex items-center space-x-1.5"
            >
              <span>
                {currentIndex === questions.length - 1
                  ? 'Next: Topic Coding Challenge 💻'
                  : 'Next'}
              </span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          ) : null}
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleSubmit}
            disabled={submitting || (Object.keys(answers).length === 0 && !studentCode.trim())}
            className="px-6 py-2.5 bg-[#EA580C] hover:bg-[#C2410C] disabled:opacity-50 text-white rounded-xl text-xs sm:text-sm font-bold shadow-xs hover:shadow transition-all flex items-center space-x-2 cursor-pointer"
          >
            <FileCheck2 className="w-4 h-4" />
            <span>{submitting ? 'Evaluating Assessment & Code...' : 'Submit Complete Assessment'}</span>
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
