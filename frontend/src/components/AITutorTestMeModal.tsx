import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  Bot,
  CheckCircle2,
  XCircle,
  ArrowRight,
  RotateCcw,
  Check,
  AlertTriangle,
  Award,
  Layers,
  HelpCircle
} from 'lucide-react';
import { api } from '../services/api';
import { AdaptivePracticeQuestion, AssessmentEvaluationResult } from '../types';
import { useStudentLearning } from '../context/StudentLearningContext';

interface AITutorTestMeModalProps {
  topicId: number;
  topicTitle: string;
  courseId?: number;
  onClose: () => void;
  onSessionComplete: (summary: {
    score: number;
    maxScore: number;
    percentage: number;
    prevMastery: number;
    newMastery: number;
    classification: string;
  }) => void;
}

export const AITutorTestMeModal: React.FC<AITutorTestMeModalProps> = ({
  topicId,
  topicTitle,
  courseId,
  onClose,
  onSessionComplete
}) => {
  const { activeCourseId, studentState, submitAssessment, refreshStudentState } = useStudentLearning();
  const effectiveCourseId = courseId || activeCourseId;
  const userId = studentState?.studentProfile?.user_id || 1;

  const [questions, setQuestions] = useState<AdaptivePracticeQuestion[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [currentIndex, setCurrentIndex] = useState<number>(0);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [checked, setChecked] = useState<boolean>(false);
  const [sessionAnswers, setSessionAnswers] = useState<Record<string, string>>({});

  const [submittingSession, setSubmittingSession] = useState<boolean>(false);
  const [finishedSummary, setFinishedSummary] = useState<any | null>(null);

  const loadQuestions = async () => {
    setLoading(true);
    setErrorMsg(null);
    setSelectedOption(null);
    setChecked(false);
    setSessionAnswers({});
    setCurrentIndex(0);
    setFinishedSummary(null);

    try {
      const q = await api.getAdaptiveQuestions(effectiveCourseId, topicId, 3, 'practice', userId);
      if (!q || q.length === 0) {
        setErrorMsg('Unable to load test questions for this topic. Please try again.');
      } else {
        setQuestions(q);
      }
    } catch (err: any) {
      console.error('Failed to load Test Me questions', err);
      setErrorMsg('Unable to load practice questions. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQuestions();
  }, [topicId, effectiveCourseId]);

  const currentQ = questions[currentIndex];
  const isLastQuestion = currentIndex === questions.length - 1;

  const handleCheckAnswer = () => {
    if (!selectedOption || !currentQ) return;
    setChecked(true);
    setSessionAnswers((prev) => ({
      ...prev,
      [String(currentQ.id)]: selectedOption
    }));
  };

  const handleNextOrFinish = async () => {
    if (!isLastQuestion) {
      setCurrentIndex((prev) => prev + 1);
      setSelectedOption(null);
      setChecked(false);
    } else {
      // All questions evaluated -> submit to central assessment engine
      setSubmittingSession(true);
      try {
        const finalAnswers = {
          ...sessionAnswers,
          ...(currentQ && selectedOption ? { [String(currentQ.id)]: selectedOption } : {})
        };

        const res = await submitAssessment('practice', finalAnswers, topicId);
        const evaluation: AssessmentEvaluationResult = res.evaluation;
        await refreshStudentState();

        const currentMeta = res.state?.topicMastery?.find((t: any) => t.topic_id === topicId);
        const prevM = evaluation.primary_mastery ? evaluation.primary_mastery.previous_mastery : (currentMeta?.mastery || 50);
        const newM = evaluation.primary_mastery ? evaluation.primary_mastery.new_mastery : (currentMeta?.mastery || 60);
        const cls = evaluation.primary_mastery ? evaluation.primary_mastery.classification : (currentMeta?.classification || 'DEVELOPING');

        const summary = {
          score: evaluation.score,
          maxScore: evaluation.max_score,
          percentage: evaluation.percentage,
          prevMastery: Math.round(prevM),
          newMastery: Math.round(newM),
          classification: cls
        };

        setFinishedSummary(summary);
        onSessionComplete(summary);
      } catch (err: any) {
        console.error('Failed to finalize Test Me session', err);
      } finally {
        setSubmittingSession(false);
      }
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-fadeIn">
      <div className="bg-white border border-[#E2E8F0] rounded-2xl max-w-xl w-full p-6 sm:p-7 shadow-[0_20px_50px_rgba(15,23,42,0.18)] space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between pb-3.5 border-b border-slate-100">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 bg-[#EA580C] text-white rounded-xl shadow-xs">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-bold text-slate-900">AI Tutor: Test Me</span>
                <span className="text-[10px] font-bold px-2 py-0.5 bg-orange-50 text-orange-600 border border-orange-200 rounded-md">
                  Interactive Check
                </span>
              </div>
              <p className="text-xs text-slate-500">{topicTitle}</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-700 text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 transition-colors"
          >
            ✕ Close
          </button>
        </div>

        {/* Loading state */}
        {loading && (
          <div className="py-12 text-center space-y-3">
            <Bot className="w-8 h-8 text-[#EA580C] animate-spin mx-auto" />
            <p className="text-xs text-slate-600 font-medium">
              Generating dynamic practice questions for <strong>{topicTitle}</strong>...
            </p>
          </div>
        )}

        {/* Error state */}
        {errorMsg && !loading && (
          <div className="py-8 text-center space-y-4">
            <div className="p-3 bg-rose-50 text-rose-600 rounded-xl inline-flex border border-rose-200">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <p className="text-xs text-rose-700">{errorMsg}</p>
            <button
              onClick={loadQuestions}
              className="px-4 py-2 bg-[#EA580C] hover:bg-[#C2410C] text-white rounded-xl text-xs font-semibold shadow-xs"
            >
              Try Again
            </button>
          </div>
        )}

        {/* Finished Summary State */}
        {finishedSummary && !loading && (
          <div className="py-4 space-y-5 animate-fadeIn text-center">
            <div className="w-14 h-14 rounded-2xl bg-emerald-50 text-emerald-600 border border-emerald-200 flex items-center justify-center mx-auto">
              <Award className="w-7 h-7" />
            </div>

            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                TEST ME COMPLETED
              </span>
              <h4 className="text-2xl font-extrabold text-slate-900 mt-0.5">
                {finishedSummary.percentage}%
              </h4>
              <p className="text-xs text-slate-500 mt-1">
                You answered <strong>{finishedSummary.score}</strong> of <strong>{finishedSummary.maxScore}</strong> questions correctly on <strong>{topicTitle}</strong>.
              </p>
            </div>

            <div className="p-4 bg-[#F8FAFC] rounded-xl border border-slate-200 flex items-center justify-around text-xs">
              <div>
                <div className="text-[10px] uppercase font-bold text-slate-400">Topic Mastery</div>
                <div className="font-bold text-slate-900 mt-0.5 flex items-center justify-center space-x-1.5">
                  <span className="text-slate-500 font-mono">{finishedSummary.prevMastery}%</span>
                  <span className="text-slate-400">➔</span>
                  <span className="text-emerald-600 font-mono font-extrabold">{finishedSummary.newMastery}%</span>
                </div>
              </div>
              <div className="h-8 w-px bg-slate-200" />
              <div>
                <div className="text-[10px] uppercase font-bold text-slate-400">Classification</div>
                <div className="font-bold text-orange-600 mt-0.5 uppercase">
                  {finishedSummary.classification}
                </div>
              </div>
            </div>

            <div className="flex items-center justify-center gap-3 pt-2">
              <button
                onClick={loadQuestions}
                className="px-4 py-2.5 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-xl text-xs font-semibold shadow-2xs transition-all flex items-center space-x-1.5"
              >
                <RotateCcw className="w-3.5 h-3.5 text-orange-600" />
                <span>Test Me Again</span>
              </button>

              <button
                onClick={onClose}
                className="px-5 py-2.5 bg-[#EA580C] hover:bg-[#C2410C] text-white rounded-xl text-xs font-bold shadow-xs transition-all flex items-center space-x-1.5"
              >
                <span>Back to AI Tutor</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}

        {/* Active Question Flow */}
        {!finishedSummary && !loading && currentQ && (
          <div className="space-y-4">
            {/* Question Stepper Indicator */}
            <div className="flex items-center justify-between text-xs text-slate-500">
              <span className="font-medium">
                Question <strong className="text-slate-900">{currentIndex + 1}</strong> of{' '}
                <strong className="text-slate-900">{questions.length}</strong>
              </span>
              <div className="flex items-center space-x-1.5">
                <span className="px-2 py-0.5 bg-slate-100 text-slate-600 rounded text-[10px] font-bold uppercase">
                  {currentQ.difficulty || 'Intermediate'}
                </span>
                {currentQ.sub_concept && (
                  <span className="px-2 py-0.5 bg-orange-50 text-orange-700 rounded text-[10px] font-semibold">
                    {currentQ.sub_concept}
                  </span>
                )}
              </div>
            </div>

            {/* Question Box */}
            <div className="p-4 bg-[#F8FAFC] rounded-xl border border-slate-200 space-y-2">
              <div className="text-sm font-bold text-slate-900 leading-snug">
                {currentQ.question_text}
              </div>

              {currentQ.code_snippet && (
                <div className="p-3 bg-slate-900 text-slate-100 rounded-lg font-mono text-xs overflow-x-auto">
                  <pre className="whitespace-pre">{currentQ.code_snippet}</pre>
                </div>
              )}
            </div>

            {/* Options */}
            <div className="space-y-2">
              {currentQ.options?.map((opt, oIdx) => {
                const isSelected = selectedOption === opt;
                const letter = String.fromCharCode(65 + oIdx);

                return (
                  <button
                    key={oIdx}
                    type="button"
                    disabled={checked}
                    onClick={() => setSelectedOption(opt)}
                    className={`w-full text-left p-3 rounded-xl border text-xs sm:text-sm transition-all flex items-center justify-between ${
                      isSelected
                        ? 'bg-white border-2 border-[#EA580C] text-slate-900 shadow-2xs font-semibold'
                        : 'bg-white border-slate-200 text-slate-700 hover:border-slate-300 hover:bg-slate-50'
                    } ${checked ? 'cursor-default' : ''}`}
                  >
                    <div className="flex items-center space-x-3">
                      <span
                        className={`w-6 h-6 rounded-lg flex items-center justify-center font-mono text-xs font-bold flex-shrink-0 ${
                          isSelected ? 'bg-[#EA580C] text-white' : 'bg-slate-100 text-slate-600'
                        }`}
                      >
                        {letter}
                      </span>
                      <span>{opt}</span>
                    </div>

                    <span
                      className={`w-4 h-4 rounded-full border flex items-center justify-center ${
                        isSelected ? 'border-[#EA580C] bg-[#EA580C]' : 'border-slate-300'
                      }`}
                    >
                      {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-white" />}
                    </span>
                  </button>
                );
              })}
            </div>

            {/* Immediate Pedagogical Feedback after Checking */}
            {checked && (
              <div className="p-3.5 bg-emerald-50/70 border border-emerald-200 rounded-xl space-y-1.5 text-xs animate-fadeIn">
                <div className="flex items-center space-x-1.5 text-emerald-800 font-bold">
                  <Sparkles className="w-4 h-4 text-emerald-600" />
                  <span>AI Tutor Explanation:</span>
                </div>
                <p className="text-slate-700 leading-relaxed">
                  {currentQ.explanation || 'Great check! Review the fundamental definition to reinforce this concept.'}
                </p>
              </div>
            )}

            {/* Buttons */}
            <div className="pt-2 flex items-center justify-between border-t border-slate-100">
              <span className="text-[11px] text-slate-400">
                {checked ? 'Review explanation, then continue.' : 'Pick an answer and check.'}
              </span>

              {!checked ? (
                <button
                  onClick={handleCheckAnswer}
                  disabled={!selectedOption}
                  className="px-5 py-2.5 bg-[#EA580C] hover:bg-[#C2410C] disabled:opacity-50 text-white rounded-xl text-xs font-bold shadow-xs transition-all flex items-center space-x-1.5"
                >
                  <Check className="w-3.5 h-3.5" />
                  <span>Check Answer</span>
                </button>
              ) : (
                <button
                  onClick={handleNextOrFinish}
                  disabled={submittingSession}
                  className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold shadow-xs transition-all flex items-center space-x-1.5"
                >
                  <span>
                    {submittingSession
                      ? 'Synchronizing Progress...'
                      : isLastQuestion
                      ? 'Finish & Update Progress'
                      : 'Next Question'}
                  </span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
