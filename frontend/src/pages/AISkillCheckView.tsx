import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  Brain,
  Layers,
  Route,
  Target,
  Cpu,
  Clock,
  Check,
  Code2
} from 'lucide-react';
import { api } from '../services/api';
import { pyodideRunner } from '../services/pyodideRunner';
import { OnboardingData } from './StudentOnboardingWizard';
import { User, CodingSubmission } from '../types';
import { TopicCodingCompiler } from '../components/TopicCodingCompiler';

interface AISkillCheckViewProps {
  currentUser: User;
  onboardingData?: OnboardingData | null;
  onCompleteToDashboard: () => void;
}

export const AISkillCheckView: React.FC<AISkillCheckViewProps> = ({
  currentUser,
  onboardingData,
  onCompleteToDashboard
}) => {
  const [started, setStarted] = useState(false);
  const [questions, setQuestions] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [qIndex, setQIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [codingSubmission, setCodingSubmission] = useState<CodingSubmission | null>(null);
  const [studentCode, setStudentCode] = useState<string>('');
  const [submitting, setSubmitting] = useState(false);
  const [analyzingPhase, setAnalyzingPhase] = useState<'idle' | 'analyzing' | 'done'>('idle');
  const [evalResult, setEvalResult] = useState<any | null>(null);

  const courseId =
    onboardingData?.selectedCourseId ||
    (currentUser as any)?.selected_course_id ||
    (typeof window !== 'undefined' && localStorage.getItem('obepath_active_course_id')
      ? parseInt(localStorage.getItem('obepath_active_course_id')!, 10)
      : 2);
  const initialDifficulty = onboardingData?.currentLevel || 'Intermediate';

  const handleStartSkillCheck = async () => {
    setStarted(true);
    setLoading(true);
    try {
      // Fetch 5 adaptive questions suited to student's initial chosen level
      const q = await api.getAdaptiveQuestions(
        courseId,
        undefined,
        5,
        'assessment',
        currentUser.id
      );
      setQuestions(q);
      setQIndex(0);
      setAnswers({});
    } catch (err) {
      console.error('Failed to load skill check questions', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectAnswer = (qId: number, option: string) => {
    setAnswers((prev) => ({ ...prev, [String(qId)]: option }));
  };

  const handleSubmit = async () => {
    if (submitting) return;
    setSubmitting(true);
    setAnalyzingPhase('analyzing');

    try {
      let finalCodingSub = codingSubmission;
      const codeToEvaluate = studentCode.trim();

      // If code was not compiled yet, or was modified after compilation, evaluate it now
      const needsCompile = !finalCodingSub || (finalCodingSub.code.trim() !== codeToEvaluate);

      try {
        const defaultTopicForCourse = courseId === 1 ? 9 : courseId === 3 ? 17 : courseId === 4 ? 25 : 1;
        const targetTopicId = (questions[0] && questions[0].course_id === courseId) ? questions[0].topic_id : defaultTopicForCourse;
        const challenge = await api.getCodingChallenge(courseId, targetTopicId);
        if (challenge && challenge.has_coding !== false && needsCompile) {
          const codeToRun = codeToEvaluate || challenge.starter_code || '';
          const runRes = await pyodideRunner.runCode(
            codeToRun,
            challenge.test_cases || []
          );
          finalCodingSub = {
            challenge_id: challenge.id || 'custom',
            title: challenge.title || 'Skill Check Topic Coding Challenge',
            topic_id: challenge.topic_id || targetTopicId,
            code: codeToRun,
            all_passed: runRes.all_passed,
            passed_count: runRes.passed_count,
            total_count: runRes.total_count,
            percentage: runRes.percentage,
            results: runRes.results,
            stdout: runRes.stdout,
            stderr: runRes.stderr,
            execution_time_ms: runRes.execution_time_ms,
            self_verified: true
          };
          setCodingSubmission(finalCodingSub);
        }
      } catch (e) {
        console.warn('Auto compile failed:', e);
      }

      // Submit assessment to unified progress engine
      const res = await api.submitAssessmentAttempt(
        {
          course_id: courseId,
          attempt_type: 'assessment',
          answers,
          coding_submission: finalCodingSub || undefined
        },
        currentUser.id
      );

      setEvalResult(res);

      // Smooth 2.2s multi-stage AI analysis animation
      setTimeout(() => {
        setAnalyzingPhase('done');
        setSubmitting(false);
      }, 2200);
    } catch (err) {
      console.error('Skill check submission failed', err);
      setAnalyzingPhase('done');
      setSubmitting(false);
    }
  };

  // 1. WELCOME SCREEN BEFORE STARTING
  if (!started) {
    return (
      <div className="min-h-screen bg-[#FAF8F5] text-slate-900 flex flex-col justify-between selection:bg-orange-100 selection:text-orange-900 font-sans p-4 sm:p-6 lg:p-8">
        <div className="max-w-2xl mx-auto w-full my-auto">
          <div className="bg-white rounded-3xl border border-[#E2E8F0] shadow-[0_8px_30px_rgb(0,0,0,0.04)] p-6 sm:p-10 text-center space-y-6">
            <div className="w-16 h-16 rounded-3xl bg-gradient-to-tr from-orange-600 to-amber-500 text-white flex items-center justify-center mx-auto shadow-md">
              <Brain className="w-8 h-8" />
            </div>

            <div className="space-y-2">
              <div className="inline-flex items-center space-x-1.5 px-3 py-1 bg-orange-50 text-orange-600 rounded-full text-xs font-semibold">
                <Sparkles className="w-3.5 h-3.5" />
                <span>Zero-Pressure Cognitive Baseline</span>
              </div>
              <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
                AI Skill Check
              </h2>
              <p className="text-sm text-slate-600 max-w-lg mx-auto leading-relaxed pt-1 font-medium">
                This isn't an exam. We'll use a few questions to understand your current level and build a learning path that fits you.
              </p>
            </div>

            {/* Baseline Level & Course pill */}
            <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200 text-left max-w-md mx-auto space-y-2 text-xs">
              {(onboardingData?.selectedCourseTitle || currentUser.full_name) && (
                <div className="flex items-center justify-between pb-2 border-b border-slate-200/60">
                  <span className="font-semibold text-slate-700">Course Assessment:</span>
                  <span className="font-bold text-orange-700 bg-orange-50 px-2 py-0.5 rounded border border-orange-200">
                    {onboardingData?.selectedCourseTitle || 'Selected Course'} {onboardingData?.selectedCourseCode ? `(${onboardingData.selectedCourseCode})` : ''}
                  </span>
                </div>
              )}
              <div className="flex items-center justify-between text-slate-700">
                <span className="font-semibold">Starting Difficulty:</span>
                <span className="font-mono font-bold text-orange-600 px-2 py-0.5 bg-white border border-orange-200 rounded-md">
                  {initialDifficulty}
                </span>
              </div>
              <p className="text-slate-500 leading-snug">
                Questions will automatically adapt difficulty up or down as you respond, ensuring your personalized path starts at the optimal point.
              </p>
            </div>

            <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
              <button
                type="button"
                onClick={handleStartSkillCheck}
                className="w-full sm:w-auto px-8 py-3.5 bg-[#EA580C] hover:bg-[#C2410C] text-white rounded-xl text-sm font-bold shadow-md hover:shadow-lg transition-all flex items-center justify-center space-x-2"
              >
                <span>Start Skill Check</span>
                <ArrowRight className="w-4 h-4" />
              </button>

              <button
                type="button"
                onClick={onCompleteToDashboard}
                className="w-full sm:w-auto px-5 py-3.5 text-xs font-semibold text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-xl transition-colors"
              >
                Skip to Dashboard
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 2. ANALYZING & RESULTS PHASE
  if (analyzingPhase === 'analyzing') {
    return (
      <div className="min-h-screen bg-[#FAF8F5] text-slate-900 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-3xl border border-slate-200 shadow-xl p-8 text-center space-y-6 animate-fadeIn">
          <div className="w-16 h-16 border-4 border-orange-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <div className="space-y-2">
            <h3 className="text-xl font-bold text-slate-900">
              Synthesizing Your Learning Path
            </h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Evaluating cognitive baseline • Checking prerequisite dependencies • Generating optimal roadmap...
            </p>
          </div>
          <div className="space-y-2 text-left text-xs bg-slate-50 p-4 rounded-2xl border border-slate-200 font-mono text-slate-600">
            <div className="flex items-center space-x-2 text-emerald-600">
              <Check className="w-4 h-4" />
              <span>Skill Check Evaluated</span>
            </div>
            <div className="flex items-center space-x-2 text-orange-600 animate-pulse">
              <Sparkles className="w-4 h-4" />
              <span>Calibrating Course Outcome Nodes...</span>
            </div>
            <div className="flex items-center space-x-2 text-slate-400">
              <Route className="w-4 h-4" />
              <span>Sequencing Topics (E = Prereq Graph)</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (analyzingPhase === 'done') {
    const score = evalResult?.evaluation?.percentage ?? 60;
    const pathItems = evalResult?.state?.learningPath?.items ?? [];

    return (
      <div className="min-h-screen bg-[#FAF8F5] text-slate-900 flex flex-col justify-between selection:bg-orange-100 selection:text-orange-900 font-sans p-4 sm:p-6 lg:p-8">
        <div className="max-w-3xl mx-auto w-full my-auto space-y-6">
          <div className="bg-white rounded-3xl border border-[#E2E8F0] shadow-[0_8px_30px_rgb(0,0,0,0.04)] p-6 sm:p-10 space-y-6 animate-fadeIn">
            {/* Header */}
            <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-100">
              <div>
                <div className="inline-flex items-center space-x-1.5 px-3 py-1 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-full text-xs font-semibold mb-2">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Skill Check Completed</span>
                </div>
                <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
                  Your Personalized Roadmap is Ready!
                </h2>
                <p className="text-xs sm:text-sm text-slate-500 mt-1">
                  We've organized your syllabus topics according to your baseline mastery and prerequisite needs.
                </p>
              </div>

              <div className="p-4 bg-[#F8FAFC] rounded-2xl border border-slate-200 text-center">
                <span className="text-[10px] uppercase font-bold text-slate-400 block font-mono">
                  Baseline Score
                </span>
                <span className="text-2xl font-bold text-orange-600">{score}%</span>
              </div>
            </div>

            {/* Coding Challenge Results Card */}
            {evalResult?.evaluation?.coding_result && (
              <div className="p-5 bg-[#0B0F19] text-white rounded-2xl border border-slate-800 space-y-3 shadow-lg text-left">
                <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800">
                  <div className="flex items-center space-x-2.5">
                    <div className="p-2 bg-[#EA580C] text-white rounded-xl shadow-xs">
                      <Code2 className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="text-[10px] uppercase font-bold tracking-wider text-orange-200">
                          Coding Assignment Evaluated
                        </span>
                        <span className="px-1.5 py-0.5 bg-slate-800 text-emerald-400 border border-emerald-500/30 rounded text-[9px] font-mono">
                          Self-verified practice, not counted toward mastery
                        </span>
                      </div>
                      <h4 className="font-bold text-white text-sm">
                        {evalResult.evaluation.coding_result.title || 'Topic Coding Problem'}
                      </h4>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <span className="text-[11px] font-mono text-slate-400">
                      Runtime: {evalResult.evaluation.coding_result.execution_time_ms || 24}ms
                    </span>
                    <span
                      className={`px-2.5 py-1 rounded-full text-xs font-bold font-mono border ${
                        evalResult.evaluation.coding_result.all_passed
                          ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                          : 'bg-amber-500/20 text-amber-400 border-amber-500/30'
                      }`}
                    >
                      {evalResult.evaluation.coding_result.passed_count} / {evalResult.evaluation.coding_result.total_count} Test Cases Passed ({evalResult.evaluation.coding_result.percentage}%)
                    </span>
                  </div>
                </div>

                {/* Test cases results pill list */}
                {evalResult.evaluation.coding_result.results && evalResult.evaluation.coding_result.results.length > 0 && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-mono">
                    {evalResult.evaluation.coding_result.results.map((r: any) => (
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
                {evalResult.evaluation.coding_result.code && (
                  <div className="pt-1 space-y-1">
                    <div className="text-[10px] uppercase font-bold text-slate-400 flex items-center justify-between">
                      <span>Submitted Solution Code in Compiler:</span>
                      <span className="text-[10px] font-mono text-slate-500">Python 3.11</span>
                    </div>
                    <pre className="p-3 bg-[#080C14] rounded-xl text-xs font-mono text-emerald-300 overflow-x-auto border border-slate-800/80 leading-relaxed max-h-36">
                      <code>{evalResult.evaluation.coding_result.code}</code>
                    </pre>
                  </div>
                )}
              </div>
            )}

            {/* Generated Path Preview */}
            <div className="space-y-3">
              <div className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center justify-between">
                <span>Personalized Path Sequence:</span>
                <span className="text-[10px] text-slate-400 font-normal">Dynamic Prerequisite Order</span>
              </div>

              <div className="space-y-2">
                {pathItems.slice(0, 4).map((item: any, idx: number) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 flex items-center justify-between text-xs transition-colors"
                  >
                    <div className="flex items-center space-x-3">
                      <div className="w-6 h-6 rounded-lg bg-orange-50 text-orange-600 font-mono font-bold flex items-center justify-center text-xs">
                        {item.sequence_order || idx + 1}
                      </div>
                      <div>
                        <span className="font-bold text-slate-900">{item.topic_title}</span>
                        <p className="text-[10px] text-slate-500 mt-0.5">
                          {item.recommendation_reason || 'Foundational syllabus module'}
                        </p>
                      </div>
                    </div>

                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-slate-100 text-slate-600">
                      {item.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="pt-4 border-t border-slate-100 flex justify-end">
              <button
                type="button"
                onClick={onCompleteToDashboard}
                className="px-8 py-3 bg-[#EA580C] hover:bg-[#C2410C] text-white rounded-xl text-xs font-bold shadow-md transition-all flex items-center space-x-2"
              >
                <span>Enter Student Dashboard</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 3. QUESTIONS ANSWERING INTERFACE
  const totalQ = questions.length + 1;
  const isCodingQuestion = qIndex === questions.length;
  const currentQ = isCodingQuestion ? null : questions[qIndex];

  return (
    <div className="min-h-screen bg-[#FAF8F5] text-slate-900 flex flex-col justify-between selection:bg-orange-100 selection:text-orange-900 font-sans p-4 sm:p-6 lg:p-8">
      {/* Header & Stepper */}
      <div className="max-w-3xl mx-auto w-full pb-4 border-b border-slate-200 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="w-7 h-7 rounded-xl bg-[#EA580C] text-white flex items-center justify-center text-xs font-bold shadow-xs">
              <Brain className="w-3.5 h-3.5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">AI Skill Check</h3>
              <p className="text-[11px] text-slate-500">Adaptive Baseline Diagnostic</p>
            </div>
          </div>

          <div className="text-right">
            <span className="text-xs font-mono font-bold text-orange-600">
              Question {qIndex + 1} of {totalQ}
            </span>
            <span className="block text-[10px] text-slate-400">
              {isCodingQuestion
                ? `Hands-On Coding: ${questions[0]?.topic_title || 'Topic Practical'}`
                : (currentQ?.topic_title || 'General')}
            </span>
          </div>
        </div>

        {/* Stepper Pills */}
        <div className="flex flex-wrap items-center gap-1.5 pt-1">
          {questions.map((q, idx) => {
            const isFilled = Boolean(answers[String(q.id)]);
            const isCur = idx === qIndex;
            return (
              <button
                key={q.id}
                type="button"
                onClick={() => setQIndex(idx)}
                className={`flex-1 min-w-[28px] h-2 rounded-full transition-all ${
                  isCur
                    ? 'bg-[#EA580C] ring-2 ring-orange-200'
                    : isFilled
                    ? 'bg-emerald-500'
                    : 'bg-slate-200 hover:bg-slate-300'
                }`}
                title={`Question ${idx + 1}: ${q.topic_title}`}
              />
            );
          })}
          {/* Question 6: Topic Coding Pill */}
          <button
            type="button"
            onClick={() => setQIndex(questions.length)}
            className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold transition-all flex items-center space-x-1 ${
              qIndex === questions.length
                ? 'bg-[#EA580C] text-white ring-2 ring-orange-200 shadow-xs'
                : codingSubmission?.all_passed
                ? 'bg-emerald-500 text-white'
                : 'bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-200'
            }`}
            title="Question 6: Hands-On Topic Coding Challenge (In-Browser Compiler)"
          >
            <Code2 className="w-3 h-3" />
            <span>Q6: Code Compiler</span>
            {codingSubmission?.all_passed && <Check className="w-2.5 h-2.5" />}
          </button>
        </div>
      </div>

      {/* Main Question Card */}
      <div className="max-w-3xl mx-auto w-full my-auto py-6">
        {loading ? (
          <div className="p-12 text-center text-xs text-orange-600 space-y-3">
            <div className="w-8 h-8 border-3 border-orange-500 border-t-transparent rounded-full animate-spin mx-auto" />
            <p>Querying QuestionBank for adaptive questions...</p>
          </div>
        ) : isCodingQuestion ? (
          <div className="bg-white rounded-3xl border border-[#E2E8F0] shadow-[0_8px_30px_rgb(0,0,0,0.04)] p-6 sm:p-8 space-y-5">
            <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-100">
              <div className="flex items-center space-x-2.5">
                <div className="p-2 bg-[#EA580C] text-white rounded-xl shadow-xs">
                  <Code2 className="w-4 h-4" />
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-orange-600">
                      Question 6 of 6 • Topic Coding Question
                    </span>
                    <span className="px-2 py-0.5 bg-slate-100 text-slate-700 rounded text-[9px] font-mono border border-slate-200">
                      Compiler Sandbox
                    </span>
                  </div>
                  <h4 className="font-bold text-slate-900 text-sm mt-0.5">
                    Practical Code Implementation & Compiler Submission
                  </h4>
                </div>
              </div>
              <div className="text-[11px] text-slate-600 font-medium">
                Topic: <strong className="text-slate-900">{questions[0]?.topic_title || 'Topic Practical'}</strong>
              </div>
            </div>

            <TopicCodingCompiler
              courseId={courseId}
              topicId={questions[0]?.topic_id || (courseId === 1 ? 9 : courseId === 3 ? 17 : courseId === 4 ? 25 : 1)}
              topicTitle={questions[0]?.topic_title}
              initialCode={studentCode}
              onCodeChange={(c) => setStudentCode(c)}
              onCompileResult={(sub) => setCodingSubmission(sub)}
            />

            {/* Navigation buttons */}
            <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
              <button
                type="button"
                onClick={() => setQIndex(qIndex - 1)}
                className="px-4 py-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-colors"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Previous Question</span>
              </button>

              <button
                type="button"
                onClick={handleSubmit}
                disabled={submitting || (Object.keys(answers).length === 0 && !studentCode.trim())}
                className="px-6 py-2.5 bg-[#EA580C] hover:bg-[#C2410C] disabled:opacity-50 text-white rounded-xl text-xs font-bold shadow-md transition-all flex items-center space-x-2"
              >
                <Sparkles className="w-4 h-4" />
                <span>{submitting ? 'Analyzing Responses & Code...' : 'Complete & Generate Path (MCQ + Code)'}</span>
              </button>
            </div>
          </div>
        ) : currentQ ? (
          <div className="bg-white rounded-3xl border border-[#E2E8F0] shadow-[0_8px_30px_rgb(0,0,0,0.04)] p-6 sm:p-10 space-y-6">
            <div className="flex items-center justify-between text-xs pb-3 border-b border-slate-100">
              <span className="px-2.5 py-1 bg-slate-100 text-slate-700 rounded-lg font-mono font-bold text-[11px]">
                {currentQ.difficulty || 'Beginner'}
              </span>
              <span className="text-slate-400 font-medium text-[11px]">
                Skill Check Question {qIndex + 1}
              </span>
            </div>

            <div className="space-y-3">
              <h4 className="text-base sm:text-lg font-bold text-slate-900 leading-relaxed">
                {currentQ.question_text}
              </h4>

              {currentQ.code_snippet && (
                <pre className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 text-xs font-mono text-orange-600 overflow-x-auto">
                  <code>{currentQ.code_snippet}</code>
                </pre>
              )}
            </div>

            {/* Options */}
            <div className="space-y-2.5 pt-2">
              {currentQ.options?.map((opt: string, optIdx: number) => {
                const isSelected = answers[String(currentQ.id)] === opt;
                return (
                  <button
                    key={optIdx}
                    type="button"
                    onClick={() => handleSelectAnswer(currentQ.id, opt)}
                    className={`w-full p-4 rounded-xl border text-left text-xs sm:text-sm font-medium transition-all flex items-center justify-between ${
                      isSelected
                        ? 'bg-orange-50 border-2 border-orange-500 text-slate-900 font-semibold shadow-xs'
                        : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                    }`}
                  >
                    <span>{opt}</span>
                    <span
                      className={`w-5 h-5 rounded-full border flex items-center justify-center text-xs flex-shrink-0 ml-3 ${
                        isSelected
                          ? 'border-orange-500 bg-[#EA580C] text-white'
                          : 'border-slate-300'
                      }`}
                    >
                      {isSelected ? '✓' : ''}
                    </span>
                  </button>
                );
              })}
            </div>

            {/* Navigation buttons */}
            <div className="pt-6 border-t border-slate-100 flex items-center justify-between">
              <button
                type="button"
                disabled={qIndex === 0}
                onClick={() => setQIndex(qIndex - 1)}
                className="px-4 py-2 bg-white hover:bg-slate-50 disabled:opacity-40 text-slate-700 border border-slate-200 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-colors"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Previous</span>
              </button>

              <button
                type="button"
                onClick={() => setQIndex(qIndex + 1)}
                className="px-6 py-2.5 bg-[#EA580C] hover:bg-[#C2410C] text-white rounded-xl text-xs font-bold shadow-sm transition-all flex items-center space-x-1.5"
              >
                <span>
                  {qIndex === questions.length - 1
                    ? 'Next: Topic Coding Challenge 💻'
                    : 'Next Question'}
                </span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
};
