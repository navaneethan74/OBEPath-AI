import React, { useState, useEffect, useRef } from 'react';
import {
  DiagnosticQuestion,
  DiagnosticResult,
  DiagnosticAnswer
} from '../types';
import { api } from '../services/api';
import {
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  ArrowLeft,
  Brain,
  Sparkles,
  HelpCircle,
  Award,
  RefreshCw,
  Cpu,
  Route,
  Layers
} from 'lucide-react';
import { useStudentLearning } from '../context/StudentLearningContext';

interface DiagnosticPageProps {
  onPathGenerated: () => void;
}

export const DiagnosticPage: React.FC<DiagnosticPageProps> = ({ onPathGenerated }) => {
  const { activeCourseId, activeCourse, studentState, refreshStudentState } = useStudentLearning();
  const [questions, setQuestions] = useState<DiagnosticQuestion[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<DiagnosticResult | null>(null);
  const [generatedPath, setGeneratedPath] = useState<any | null>(null);

  const enrolledCourse = studentState?.enrolledCourse;
  const courseTitle = enrolledCourse?.title || activeCourse?.title || 'Selected Course';
  const courseCode = enrolledCourse?.code || activeCourse?.code || '';

  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    loadQuestions();
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [activeCourseId]);

  const loadQuestions = async () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    setLoading(true);
    setQuestions([]);
    setAnswers({});
    setResult(null);
    setGeneratedPath(null);
    setCurrentIndex(0);

    try {
      const q = await api.getDiagnosticQuestions(activeCourseId, controller.signal);
      if (!controller.signal.aborted) {
        setQuestions(q);
      }
    } catch (err: any) {
      if (err?.name !== 'AbortError') {
        console.error('Failed to load diagnostic questions', err);
      }
    } finally {
      if (!controller.signal.aborted) {
        setLoading(false);
      }
    }
  };

  const handleSelectAnswer = (qId: number, option: string) => {
    setAnswers((prev) => ({ ...prev, [qId]: option }));
  };

  const handleNext = () => {
    if (currentIndex < questions.length - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  };

  const handlePrev = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      const formattedAnswers: DiagnosticAnswer[] = Object.entries(answers).map(([qid, ans]) => ({
        question_id: parseInt(qid),
        selected_answer: ans
      }));
      const userId = studentState?.studentProfile?.user_id || 1;
      const res = await api.submitDiagnostic(activeCourseId, formattedAnswers, userId);
      setResult(res);
      try {
        const path = await api.generateLearningPath(activeCourseId, userId);
        setGeneratedPath(path);
      } catch (pErr) {
        console.error('Failed to automatically generate path', pErr);
      }
      await refreshStudentState();
    } catch (err) {
      console.error('Failed to submit diagnostic', err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleGeneratePath = async () => {
    setLoading(true);
    try {
      let userId = studentState?.studentProfile?.user_id;
      if (!userId && typeof window !== 'undefined') {
        const saved = localStorage.getItem('obepath_current_user');
        if (saved) {
          try {
            userId = JSON.parse(saved).id;
          } catch (e) {}
        }
      }
      if (!userId) {
        throw new Error('Authenticated user ID not found');
      }
      await api.generateLearningPath(activeCourseId, userId);
      await refreshStudentState();
      onPathGenerated();
    } catch (err) {
      console.error('Failed to generate path', err);
      await refreshStudentState();
      onPathGenerated();
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="py-24 text-center space-y-3 animate-fadeIn">
        <RefreshCw className="w-8 h-8 text-orange-500 animate-spin mx-auto" />
        <p className="text-sm text-slate-400">Loading Diagnostic Assessment questions...</p>
      </div>
    );
  }

  // Result View (Step 5: Learning Gap Identification)
  if (result) {
    return (
      <div className="max-w-4xl mx-auto space-y-8 animate-fadeIn">
        <div className="p-8 bg-white border border-[#E2E8F0] rounded-2xl shadow-[0_4px_20px_rgba(15,23,42,0.06)] text-center space-y-4">
          <div className="inline-flex p-3 bg-orange-50 text-orange-600 rounded-2xl">
            <Award className="w-8 h-8" />
          </div>
          <div>
            <div className="inline-flex items-center space-x-2 px-3 py-1 bg-orange-50 border border-orange-200 text-orange-600 rounded-full text-xs font-semibold">
              <Sparkles className="w-3.5 h-3.5 text-amber-500" />
              <span>OBE Step 5: Learning Gap Identification Complete</span>
            </div>
          </div>
          <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">
            Diagnostic Baseline Evaluated
          </h2>
          <p className="text-sm text-slate-500 max-w-xl mx-auto leading-relaxed">
            The Assessment Agent evaluated your foundational competence in {courseTitle} {courseCode ? `(${courseCode})` : ''} to identify exact learning gaps before generating your personalized trajectory.
          </p>

          <div className="pt-2 flex flex-wrap items-center justify-center gap-4">
            <div className="px-5 py-3 bg-[#FAF8F5] rounded-xl border border-slate-200">
              <span className="text-xs text-slate-500">Diagnostic Score</span>
              <div className="text-2xl font-mono font-extrabold text-orange-600">
                {result.overall_score}%
              </div>
            </div>
            <div className="px-5 py-3 bg-[#FAF8F5] rounded-xl border border-slate-200">
              <span className="text-xs text-slate-500">Correct Answers</span>
              <div className="text-2xl font-mono font-extrabold text-emerald-600">
                {result.correct_answers} / {result.total_questions}
              </div>
            </div>
            <div className="px-5 py-3 bg-[#FAF8F5] rounded-xl border border-slate-200">
              <span className="text-xs text-slate-500">Identified Gaps</span>
              <div className="text-2xl font-mono font-extrabold text-amber-600">
                {result.weaknesses.length} Topics
              </div>
            </div>
          </div>

          <div className="pt-4">
            <button
              onClick={handleGeneratePath}
              className="px-6 py-2.5 bg-orange-600 hover:bg-orange-700 text-white rounded-xl text-sm font-bold shadow-xs shadow-orange-500/20 transition-all flex items-center space-x-2 mx-auto"
            >
              <span>Step 6: Generate My Personalized Learning Path</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Concept Analysis Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Understood Concepts */}
          <div className="p-6 bg-white border border-emerald-200 rounded-2xl space-y-4 shadow-[0_4px_20px_rgba(15,23,42,0.04)]">
            <div className="flex items-center space-x-2 text-emerald-700 text-sm font-bold">
              <CheckCircle2 className="w-5 h-5 text-emerald-600" />
              <span>Understood Topics ({result.strengths.length})</span>
            </div>
            {result.strengths.length === 0 ? (
              <p className="text-xs text-slate-500">No topics met the 60% threshold. Remediation scheduled for all modules.</p>
            ) : (
              <div className="space-y-2">
                {result.strengths.map((s) => (
                  <div key={s.topic_id} className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between text-xs">
                    <div>
                      <span className="font-semibold text-slate-800">{s.title}</span>
                      <p className="text-[11px] text-slate-500">Foundational mechanics validated</p>
                    </div>
                    <span className="font-mono font-bold text-emerald-700 px-2.5 py-1 bg-emerald-50 border border-emerald-200 rounded-lg">{s.score}% ✓</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Weak / Needs Learning Concepts */}
          <div className="p-6 bg-white border border-amber-200 rounded-2xl space-y-4 shadow-[0_4px_20px_rgba(15,23,42,0.04)]">
            <div className="flex items-center space-x-2 text-amber-700 text-sm font-bold">
              <AlertTriangle className="w-5 h-5 text-amber-600" />
              <span>Learning Gaps Identified ({result.weaknesses.length})</span>
            </div>
            {result.weaknesses.length === 0 ? (
              <p className="text-xs text-slate-500">No major prerequisite gaps detected.</p>
            ) : (
              <div className="space-y-2">
                {result.weaknesses.map((w) => (
                  <div key={w.topic_id} className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between text-xs">
                    <div>
                      <span className="font-semibold text-slate-800">{w.title}</span>
                      <p className="text-[11px] text-rose-600 font-medium">Scheduled for priority remediation</p>
                    </div>
                    <span className="font-mono font-bold text-rose-700 px-2.5 py-1 bg-rose-50 border border-rose-200 rounded-lg">{w.score}% ✗</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* TECHNICAL REPRESENTATION & GAP DETECTION ENGINE (USER DIAGRAM 1) */}
        <div className="p-6 bg-white border border-slate-200 rounded-2xl shadow-xs space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-100">
            <div className="flex items-center space-x-2">
              <div className="p-1.5 bg-orange-50 text-orange-600 rounded-lg border border-orange-200">
                <Cpu className="w-4 h-4" />
              </div>
              <h4 className="text-sm font-bold text-slate-900">
                Technical Graph Representation & Gap Detection Engine
              </h4>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 bg-orange-50 text-orange-600 border border-orange-200 rounded-md font-bold">
              Model: G = (V, E)
            </span>
          </div>

          <div className="p-4 bg-[#FAF8F5] border border-slate-200 rounded-xl space-y-2 text-xs font-mono text-slate-800">
            <div className="font-bold text-orange-600">Let:</div>
            <div className="pl-3 space-y-1">
              <div><strong className="text-slate-900">G = (V, E)</strong></div>
              <div className="text-slate-600 pl-2">where:</div>
              <div className="pl-4"><strong>V</strong> = set of learning concepts in syllabus</div>
              <div className="pl-4"><strong>E</strong> = prerequisite relationships between concepts (e.g. Recursion ➔ Tree Traversal)</div>
              <div className="pt-1"><strong className="text-slate-900">Kt</strong> = learner's knowledge state at time t</div>
              <div className="pt-1">For a concept <strong>v ∈ V</strong>:</div>
              <div className="pl-4"><strong>Mt(v)</strong> = mastery score of concept v</div>
              <div className="pt-1.5 p-2 bg-amber-50 border border-amber-200 rounded-lg text-amber-900 font-semibold">
                If: <strong>Mt(v) &lt; 60% (Threshold)</strong> ➔ the concept is treated as a <strong>learning gap</strong>.
                <br />
                The system then checks prerequisite concepts (E) and updates the learning path.
              </div>
            </div>
          </div>
        </div>

        {/* POST-DIAGNOSTIC GENERATED PERSONALIZED LEARNING PATH (CLEARLY SHOWN) */}
        <div className="p-6 bg-white border-2 border-orange-200 rounded-2xl shadow-[0_4px_20px_rgba(234,88,12,0.06)] space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-100">
            <div className="flex items-center space-x-2.5">
              <div className="p-2 bg-orange-50 text-orange-600 rounded-xl border border-orange-200">
                <Route className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <h4 className="text-base font-bold text-slate-900">
                    Generated Personalized Learning Path
                  </h4>
                  <span className="text-[10px] font-mono px-2 py-0.5 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-md font-bold">
                    Generated Live ✓
                  </span>
                </div>
                <p className="text-xs text-slate-500">
                  {generatedPath?.adaptation_reason ||
                    'Roadmap dynamically synthesized: Remedial prerequisite modules scheduled before advanced topics.'}
                </p>
              </div>
            </div>

            <button
              onClick={handleGeneratePath}
              className="px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg text-xs font-bold shadow-xs shadow-orange-500/20 transition-all flex items-center space-x-1.5"
            >
              <span>Begin Module 1 in Path</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>

          {/* Sequential Path Trajectory List */}
          <div className="space-y-2.5">
            {(generatedPath?.items || []).map((item: any, idx: number) => {
              const isRemedial = item.is_remedial || item.topic_title?.toLowerCase().includes('recursion');
              const isMastered = item.mastery_percentage >= 80;
              const isCurrent = item.status === 'CURRENT' || idx === 0;

              return (
                <div
                  key={item.id || idx}
                  className={`p-3.5 rounded-xl border transition-all flex flex-wrap items-center justify-between gap-3 ${
                    isRemedial
                      ? 'bg-amber-50/50 border-amber-200 shadow-2xs'
                      : isCurrent
                      ? 'bg-orange-50/60 border-2 border-orange-500 shadow-xs'
                      : isMastered
                      ? 'bg-emerald-50/40 border-emerald-200'
                      : 'bg-white border-slate-200'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <div
                      className={`w-7 h-7 rounded-lg flex items-center justify-center font-mono font-bold text-xs ${
                        isRemedial
                          ? 'bg-amber-100 text-amber-800'
                          : isCurrent
                          ? 'bg-orange-600 text-white'
                          : isMastered
                          ? 'bg-emerald-100 text-emerald-800'
                          : 'bg-slate-100 text-slate-700'
                      }`}
                    >
                      {item.sequence_order || idx + 1}
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-bold text-slate-900">
                          {item.topic_title}
                        </span>
                        {isRemedial && (
                          <span className="text-[10px] font-bold px-2 py-0.5 bg-amber-100 text-amber-800 border border-amber-200 rounded-md">
                            [REMEDIAL INSERTION]
                          </span>
                        )}
                        {isCurrent && (
                          <span className="text-[10px] font-bold px-2 py-0.5 bg-orange-50 text-orange-600 border border-orange-200 rounded-md">
                            [ACTIVE NOW]
                          </span>
                        )}
                        {isMastered && (
                          <span className="text-[10px] font-bold px-2 py-0.5 bg-emerald-100 text-emerald-800 border border-emerald-200 rounded-md">
                            [MASTERED]
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-slate-500 mt-0.5">
                        {item.recommendation_reason ||
                          (isRemedial
                            ? 'Identified gap in prerequisite recursion: Scheduled priority remediation.'
                            : 'Standard prerequisite sequence.')}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-4 text-xs">
                    <div className="text-right">
                      <span className="text-[10px] text-slate-400 block font-mono">Outcomes</span>
                      <span className="font-semibold text-slate-700">
                        {item.related_outcomes?.join(', ') || 'CO1, CO2'}
                      </span>
                    </div>
                    <div className="text-right">
                      <span className="text-[10px] text-slate-400 block font-mono">Mastery</span>
                      <span className="font-bold text-orange-600">
                        {Math.round(item.mastery_percentage || 0)}%
                      </span>
                    </div>
                    <button
                      onClick={handleGeneratePath}
                      className="px-3 py-1.5 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-lg text-xs font-semibold shadow-2xs transition-colors"
                    >
                      Study Topic
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* 10-STAGE AI CLOSED LOOP STATUS TRACKER */}
        <div className="p-4 bg-[#FAF8F5] border border-slate-200 rounded-xl space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span className="font-bold text-slate-900 flex items-center space-x-1.5">
              <Layers className="w-3.5 h-3.5 text-orange-600" />
              <span>10-Stage Closed Loop Pipeline Active:</span>
            </span>
            <span className="font-mono text-[10px] text-orange-600 font-bold">
              Stage 7 (Assessment) ➔ Stage 8 (Gap Detection) ➔ Stage 9 (Path Repair)
            </span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-[11px]">
            <div className="p-2 bg-white rounded-lg border border-slate-200 text-center">
              <span className="text-slate-400 block text-[10px]">Steps 1–4</span>
              <strong className="text-slate-800">Learner Input</strong>
              <span className="text-[10px] text-emerald-600 block">✓ Completed</span>
            </div>
            <div className="p-2 bg-white rounded-lg border border-slate-200 text-center">
              <span className="text-slate-400 block text-[10px]">Step 5</span>
              <strong className="text-slate-800">Generative AI Content</strong>
              <span className="text-[10px] text-emerald-600 block">✓ Ready</span>
            </div>
            <div className="p-2 bg-white rounded-lg border border-slate-200 text-center">
              <span className="text-slate-400 block text-[10px]">Step 6 & 7</span>
              <strong className="text-slate-800">Path & Assessment</strong>
              <span className="text-[10px] text-emerald-600 block">✓ Evaluated</span>
            </div>
            <div className="p-2 bg-white rounded-lg border-2 border-orange-200 bg-orange-50/40 text-center">
              <span className="text-orange-600 block text-[10px] font-bold">Step 8 & 9</span>
              <strong className="text-orange-600">Gap Detection & Repair</strong>
              <span className="text-[10px] text-orange-600 block font-bold">✓ Path Adapted</span>
            </div>
            <div className="p-2 bg-white rounded-lg border border-slate-200 text-center">
              <span className="text-slate-400 block text-[10px]">Step 10</span>
              <strong className="text-slate-800">Progress Monitoring</strong>
              <span className="text-[10px] text-emerald-600 block">✓ Synchronized</span>
            </div>
          </div>
        </div>

        {/* Question Review Accordion */}
        <div className="p-6 bg-white border border-[#E2E8F0] rounded-2xl shadow-[0_4px_20px_rgba(15,23,42,0.04)] space-y-4">
          <h3 className="text-base font-bold text-slate-900">Diagnostic Question Breakdown</h3>
          <div className="space-y-3">
            {result.question_results.map((qr, idx) => (
              <div
                key={qr.question_id}
                className={`p-4 rounded-xl border text-xs ${
                  qr.is_correct
                    ? 'bg-emerald-50/40 border-emerald-200'
                    : 'bg-rose-50/40 border-rose-200'
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="font-bold text-slate-900">Question {idx + 1}: {qr.topic_title}</span>
                  <span
                    className={`font-semibold px-2 py-0.5 rounded text-[10px] ${
                      qr.is_correct ? 'bg-emerald-100 text-emerald-800 border border-emerald-200' : 'bg-rose-100 text-rose-800 border border-rose-200'
                    }`}
                  >
                    {qr.is_correct ? 'Correct' : 'Incorrect'}
                  </span>
                </div>
                <p className="text-slate-700 mb-2">{qr.question_text}</p>
                <div className="p-2.5 bg-white rounded-lg border border-slate-200 text-[11px] space-y-1">
                  <div>
                    <span className="text-slate-500">Your Answer: </span>
                    <span className={qr.is_correct ? 'text-emerald-700 font-semibold' : 'text-rose-700 font-semibold'}>
                      {qr.selected_answer || 'Skipped'}
                    </span>
                  </div>
                  {!qr.is_correct && (
                    <div>
                      <span className="text-slate-500">Correct Answer: </span>
                      <span className="text-emerald-700 font-semibold">{qr.correct_answer}</span>
                    </div>
                  )}
                  <p className="text-slate-500 pt-1 border-t border-slate-100 text-[10px] italic">
                    {qr.explanation}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Active Assessment Form
  const currentQ = questions[currentIndex];
  const answeredCount = Object.keys(answers).length;

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-200">
        <div>
          <div className="inline-flex items-center space-x-2 px-3 py-1 bg-orange-50 border border-orange-200 rounded-full text-xs font-semibold text-orange-600 mb-1">
            <Brain className="w-3.5 h-3.5 text-orange-600" />
            <span>OBE Step 4: Initial Diagnostic Assessment</span>
          </div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">{courseTitle} ({courseCode}) Diagnostic</h2>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="bg-white border border-[#E2E8F0] rounded-2xl p-4 shadow-xs">
        <div className="flex items-center justify-between text-xs text-slate-500 mb-2">
          <span>Question {currentIndex + 1} of {questions.length}</span>
          <span className="font-mono font-bold text-orange-600">{answeredCount} Answered</span>
        </div>
        <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
          <div
            className="bg-orange-600 h-full rounded-full transition-all duration-300"
            style={{ width: `${((currentIndex + 1) / questions.length) * 100}%` }}
          />
        </div>
      </div>

      {/* Question Card */}
      {currentQ && (
        <div className="bg-white border border-[#E2E8F0] rounded-2xl p-6 sm:p-8 space-y-6 shadow-[0_4px_20px_rgba(15,23,42,0.06)]">
          <div className="flex items-center justify-between text-xs">
            <span className="px-2.5 py-1 bg-orange-50 text-orange-600 border border-orange-200 rounded-lg font-semibold">
              {currentQ.topic_title}
            </span>
            <span className="text-slate-500 capitalize">{currentQ.question_type.replace('_', ' ')}</span>
          </div>

          <h3 className="text-lg font-bold text-slate-900 leading-relaxed">
            {currentQ.question_text}
          </h3>

          {currentQ.code_snippet && (
            <div className="p-4 bg-[#F8FAFC] border border-slate-200 rounded-xl font-mono text-xs text-slate-800 overflow-x-auto whitespace-pre">
              {currentQ.code_snippet}
            </div>
          )}

          {/* Options */}
          <div className="space-y-3">
            {currentQ.options.map((opt, idx) => {
              const isSelected = answers[currentQ.id] === opt;
              return (
                <button
                  key={idx}
                  onClick={() => handleSelectAnswer(currentQ.id, opt)}
                  className={`w-full text-left p-4 rounded-xl text-xs sm:text-sm font-medium transition-all flex items-center justify-between border ${
                    isSelected
                      ? 'bg-orange-50 border-orange-500 text-orange-700 ring-1 ring-orange-500/30'
                      : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50 hover:border-slate-300'
                  }`}
                >
                  <span className="pr-4">{opt}</span>
                  <span
                    className={`w-5 h-5 rounded-full border flex items-center justify-center flex-shrink-0 ${
                      isSelected
                        ? 'border-orange-600 bg-orange-600 text-white'
                        : 'border-slate-300'
                    }`}
                  >
                    {isSelected && <span className="w-2 h-2 rounded-full bg-white" />}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Navigation buttons */}
          <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
            <button
              onClick={handlePrev}
              disabled={currentIndex === 0}
              className="px-4 py-2 bg-slate-100 text-slate-700 hover:bg-slate-200 rounded-xl text-xs font-semibold disabled:opacity-30 disabled:cursor-not-allowed flex items-center space-x-1.5 transition-colors border border-slate-200"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Previous</span>
            </button>

            {currentIndex === questions.length - 1 ? (
              <button
                onClick={handleSubmit}
                disabled={submitting}
                className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold shadow-xs transition-all flex items-center space-x-2"
              >
                <span>{submitting ? 'Evaluating...' : 'Submit Assessment'}</span>
                <CheckCircle2 className="w-4 h-4" />
              </button>
            ) : (
              <button
                onClick={handleNext}
                className="px-5 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-xl text-xs font-semibold shadow-xs shadow-orange-500/20 transition-all flex items-center space-x-1.5"
              >
                <span>Next</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
