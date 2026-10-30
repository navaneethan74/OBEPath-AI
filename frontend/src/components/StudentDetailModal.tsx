import React, { useState, useEffect } from 'react';
import {
  X,
  User,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Award,
  BookOpen,
  Calendar,
  CheckCircle2,
  Clock,
  RefreshCw,
  AlertCircle,
  FileText,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Check,
  ChevronRight,
  GitBranch,
  Send,
  MessageSquare
} from 'lucide-react';
import { api } from '../services/api';
import { ClassStudentDetail, ClassStudentLearningPath, StudentImpactResponse } from '../types';

interface StudentDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  classId: number;
  studentId: number;
}

export const StudentDetailModal: React.FC<StudentDetailModalProps> = ({
  isOpen,
  onClose,
  classId,
  studentId
}) => {
  const [activeTab, setActiveTab] = useState<'progress' | 'outcomes' | 'scores' | 'path' | 'impact'>('progress');
  const [detail, setDetail] = useState<ClassStudentDetail | null>(null);
  const [learningPath, setLearningPath] = useState<ClassStudentLearningPath | null>(null);
  const [impactData, setImpactData] = useState<StudentImpactResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Teacher intervention form state
  const [flagNote, setFlagNote] = useState('');
  const [flagSubmitting, setFlagSubmitting] = useState(false);
  const [flagSuccess, setFlagSuccess] = useState(false);
  const [flagError, setFlagError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && classId && studentId) {
      loadStudentData();
    }
  }, [isOpen, classId, studentId]);

  const loadStudentData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [detailRes, lpRes, impactRes] = await Promise.all([
        api.getClassStudentDetail(classId, studentId),
        api.getClassStudentLearningPath(classId, studentId),
        api.getClassStudentImpact(classId, studentId).catch(() => null)
      ]);
      setDetail(detailRes);
      setLearningPath(lpRes);
      setImpactData(impactRes);
    } catch (err: any) {
      setError(err.message || 'Failed to load student profile.');
    } finally {
      setLoading(false);
    }
  };

  const handleFlagIntervention = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!flagNote.trim()) return;
    setFlagSubmitting(true);
    setFlagError(null);
    setFlagSuccess(false);
    try {
      await api.flagStudentIntervention(classId, studentId, flagNote.trim());
      setFlagSuccess(true);
      setFlagNote('');
      // Reload impact and detail
      const [detailRes, impactRes] = await Promise.all([
        api.getClassStudentDetail(classId, studentId),
        api.getClassStudentImpact(classId, studentId)
      ]);
      setDetail(detailRes);
      setImpactData(impactRes);
      setTimeout(() => setFlagSuccess(false), 3000);
    } catch (err: any) {
      setFlagError(err.message || 'Failed to record intervention note.');
    } finally {
      setFlagSubmitting(false);
    }
  };

  if (!isOpen) return null;

  const thresholds = detail?.thresholds || {
    prereq_unlock: 60.0,
    assessment_pass: 60.0,
    topic_mastery: 80.0,
    co_achieved_default: 70.0,
    at_risk_mastery: 50.0,
    inactive_days: 7
  };

  const getStatusBadge = (status: string) => {
    const s = status.toLowerCase();
    switch (s) {
      case 'completed':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="w-3 h-3" />
            <span>Completed</span>
          </span>
        );
      case 'current':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#F3F0FF] text-[#635BFF] border border-purple-200 animate-pulse">
            <Clock className="w-3 h-3" />
            <span>Current Study</span>
          </span>
        );
      case 'locked':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-600 border border-slate-200">
            <span>Locked</span>
          </span>
        );
      case 'recommended':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-200">
            <span>Recommended</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-700">
            <span>{status}</span>
          </span>
        );
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4 sm:p-6 animate-fadeIn">
      <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-5xl w-full max-h-[92vh] flex flex-col overflow-hidden animate-scaleUp">
        {/* Header */}
        <div className="p-6 border-b border-slate-200 bg-slate-50/60 flex items-start justify-between">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-200 text-slate-700">
                Student Profile • Read-Only
              </span>
              {detail?.is_at_risk && (
                <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200">
                  <AlertTriangle className="w-3 h-3" />
                  <span>At-Risk Learner</span>
                </span>
              )}
            </div>
            <h3 className="text-xl font-bold text-slate-900 flex items-center space-x-2">
              <span>{detail?.student.name || 'Student Profile'}</span>
            </h3>
            <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500">
              <span>{detail?.student.email}</span>
              <span>•</span>
              <span className="text-[#635BFF] font-semibold bg-[#F3F0FF] px-2 py-0.5 rounded">
                {detail?.student.progress_summary}
              </span>
              {detail?.student.improvement_since_join !== undefined && detail.student.improvement_since_join > 0 && (
                <span className="text-emerald-700 font-semibold bg-emerald-50 px-2 py-0.5 rounded">
                  +{detail.student.improvement_since_join} topics mastered since joining
                </span>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-200 rounded-xl text-slate-400 hover:text-slate-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* At-Risk Banner if Applicable */}
        {detail?.is_at_risk && (
          <div className="px-6 py-3 bg-rose-50 border-b border-rose-200 flex items-start space-x-3 text-xs text-rose-800">
            <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
            <div className="space-y-0.5">
              <span className="font-bold">At-Risk Criteria Triggered:</span>
              <ul className="list-disc pl-4 space-y-0.5 text-[11px] text-rose-700">
                {detail.at_risk_reasons.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* Tabs Bar */}
        <div className="px-6 border-b border-slate-200 bg-white flex space-x-1">
          <button
            onClick={() => setActiveTab('progress')}
            className={`py-3 px-4 text-xs font-semibold border-b-2 transition-all flex items-center space-x-2 ${
              activeTab === 'progress'
                ? 'border-[#635BFF] text-[#635BFF]'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <BookOpen className="w-4 h-4" />
            <span>Progress & Mastery</span>
          </button>
          <button
            onClick={() => setActiveTab('outcomes')}
            className={`py-3 px-4 text-xs font-semibold border-b-2 transition-all flex items-center space-x-2 ${
              activeTab === 'outcomes'
                ? 'border-[#635BFF] text-[#635BFF]'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Award className="w-4 h-4" />
            <span>Outcomes (Baseline vs Delta)</span>
          </button>
          <button
            onClick={() => setActiveTab('scores')}
            className={`py-3 px-4 text-xs font-semibold border-b-2 transition-all flex items-center space-x-2 ${
              activeTab === 'scores'
                ? 'border-[#635BFF] text-[#635BFF]'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <TrendingUp className="w-4 h-4" />
            <span>Diagnostic & Assessment Attempts</span>
          </button>
          <button
            onClick={() => setActiveTab('path')}
            className={`py-3 px-4 text-xs font-semibold border-b-2 transition-all flex items-center space-x-2 ${
              activeTab === 'path'
                ? 'border-[#635BFF] text-[#635BFF]'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <GitBranch className="w-4 h-4" />
            <span>Learning Path & Prerequisite Gaps</span>
          </button>
          <button
            onClick={() => setActiveTab('impact')}
            className={`py-3 px-4 text-xs font-semibold border-b-2 transition-all flex items-center space-x-2 ${
              activeTab === 'impact'
                ? 'border-[#635BFF] text-[#635BFF]'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Sparkles className="w-4 h-4 text-amber-500" />
            <span>Impact & Interventions</span>
          </button>
        </div>

        {/* Tab Content Area */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1 bg-slate-50/30">
          {loading ? (
            <div className="py-24 text-center space-y-2 text-slate-400">
              <RefreshCw className="w-8 h-8 animate-spin mx-auto text-[#635BFF]" />
              <p className="text-xs">Loading Student Progress Records...</p>
            </div>
          ) : error ? (
            <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          ) : detail ? (
            <>
              {/* TAB 1: PROGRESS & MASTERY */}
              {activeTab === 'progress' && (
                <div className="space-y-6 animate-fadeIn">
                  {/* Summary Metric Strip */}
                  <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
                    <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs">
                      <span className="text-[11px] font-medium text-slate-500 block">Overall Mastery</span>
                      <span className="text-2xl font-mono font-extrabold text-slate-900 mt-1 block">
                        {detail.current_overall_mastery}%
                      </span>
                    </div>
                    <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs">
                      <span className="text-[11px] font-medium text-slate-500 block">Completed Topics</span>
                      <span className="text-2xl font-mono font-extrabold text-emerald-600 mt-1 block">
                        {detail.completed_topics_count} / {detail.total_topics_count}
                      </span>
                    </div>
                    <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs">
                      <span className="text-[11px] font-medium text-slate-500 block">Joined Baseline</span>
                      <span className="text-2xl font-mono font-extrabold text-[#635BFF] mt-1 block">
                        {detail.student.baseline_completed_topics} Topics
                      </span>
                    </div>
                    <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs">
                      <span className="text-[11px] font-medium text-slate-500 block">Improvement Delta</span>
                      <span className="text-2xl font-mono font-extrabold text-emerald-600 mt-1 block">
                        +{detail.student.improvement_since_join} Topics
                      </span>
                    </div>
                  </div>

                  {/* Topic Progress Table */}
                  <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
                    <div className="p-4 border-b border-slate-100 flex items-center justify-between">
                      <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                        Curriculum Topic Mastery Details
                      </h4>
                      <span className="text-[11px] text-slate-400">
                        Threshold for Mastery: ≥ {thresholds.topic_mastery}%
                      </span>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-slate-50 text-slate-500 border-b border-slate-200">
                          <tr>
                            <th className="py-2.5 px-3 font-semibold">Code</th>
                            <th className="py-2.5 px-3 font-semibold">Topic Title</th>
                            <th className="py-2.5 px-3 font-semibold">Status</th>
                            <th className="py-2.5 px-3 font-semibold text-center">Quiz</th>
                            <th className="py-2.5 px-3 font-semibold text-center">Practice</th>
                            <th className="py-2.5 px-3 font-semibold text-center">Completion</th>
                            <th className="py-2.5 px-3 font-semibold text-center">Overall Mastery</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {detail.topics.map((t) => (
                            <tr key={t.topic_id} className="hover:bg-slate-50/70 transition-colors">
                              <td className="py-3 px-3 font-mono font-bold text-slate-800">{t.code}</td>
                              <td className="py-3 px-3 font-medium text-slate-900">{t.title}</td>
                              <td className="py-3 px-3">{getStatusBadge(t.status)}</td>
                              <td className="py-3 px-3 text-center font-mono text-slate-600">{t.quiz_score}%</td>
                              <td className="py-3 px-3 text-center font-mono text-slate-600">{t.practice_score}%</td>
                              <td className="py-3 px-3 text-center font-mono text-slate-600">{t.completion_score}%</td>
                              <td className="py-3 px-3 text-center">
                                <span
                                  className={`inline-block font-mono font-bold px-2 py-0.5 rounded text-[11px] border ${
                                    t.overall_mastery >= thresholds.topic_mastery
                                      ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                                      : t.overall_mastery >= thresholds.prereq_unlock
                                      ? 'bg-amber-50 text-amber-800 border-amber-200'
                                      : 'bg-rose-50 text-rose-800 border-rose-200'
                                  }`}
                                >
                                  {t.overall_mastery}%
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 2: OUTCOMES (BASELINE VS DELTA) */}
              {activeTab === 'outcomes' && (
                <div className="space-y-6 animate-fadeIn">
                  <div className="p-4 bg-white border border-slate-200 rounded-xl space-y-1">
                    <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                      Course Outcome Attainment Growth
                    </h4>
                    <p className="text-xs text-slate-500">
                      Comparing outcome attainment percentage captured at class enrollment baseline against current progress.
                    </p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {detail.outcomes.map((co) => (
                      <div
                        key={co.outcome_id}
                        className="p-5 bg-white border border-slate-200 rounded-xl shadow-xs space-y-4"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-mono font-bold text-xs px-2 py-0.5 bg-[#F3F0FF] text-[#635BFF] border border-purple-100 rounded">
                            {co.code}
                          </span>
                          <span
                            className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full border ${
                              co.is_achieved
                                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                                : 'bg-amber-50 text-amber-700 border-amber-200'
                            }`}
                          >
                            {co.is_achieved ? 'Target Achieved' : 'In Progress'}
                          </span>
                        </div>

                        <div>
                          <h5 className="text-xs font-bold text-slate-900">{co.description}</h5>
                          <span className="text-[11px] text-slate-400">Target: {co.target_pct}%</span>
                        </div>

                        {/* Baseline vs Current Delta Visual */}
                        <div className="grid grid-cols-3 gap-2 p-3 bg-slate-50 border border-slate-200 rounded-lg text-center">
                          <div>
                            <span className="text-[10px] text-slate-400 block uppercase font-bold">Join Baseline</span>
                            <span className="text-sm font-mono font-bold text-slate-600">
                              {co.baseline_attainment}%
                            </span>
                          </div>
                          <div>
                            <span className="text-[10px] text-slate-400 block uppercase font-bold">Current</span>
                            <span className="text-sm font-mono font-bold text-slate-900">
                              {co.current_attainment}%
                            </span>
                          </div>
                          <div>
                            <span className="text-[10px] text-slate-400 block uppercase font-bold">Net Delta</span>
                            <span
                              className={`text-sm font-mono font-extrabold ${
                                co.delta >= 0 ? 'text-emerald-600' : 'text-rose-600'
                              }`}
                            >
                              {co.delta >= 0 ? `+${co.delta}%` : `${co.delta}%`}
                            </span>
                          </div>
                        </div>

                        {/* Progress Bar */}
                        <div className="space-y-1">
                          <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all ${
                                co.is_achieved ? 'bg-emerald-500' : 'bg-[#635BFF]'
                              }`}
                              style={{ width: `${Math.min(100, co.current_attainment)}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* TAB 3: SCORES & ATTEMPTS */}
              {activeTab === 'scores' && (
                <div className="space-y-6 animate-fadeIn">
                  {/* Step 2D: Initial vs Reassessment Summary Card */}
                  {detail.assessment_summary && (
                    <div className="p-5 bg-white border border-slate-200 rounded-xl shadow-xs space-y-4">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="space-y-0.5">
                          <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                            Assessment & Reassessment Analytics
                          </h4>
                          <p className="text-[11px] text-slate-500">
                            Comparison between baseline initial performance, continuous reassessments, and peak score.
                          </p>
                        </div>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                          {detail.assessment_summary.total_attempts} total attempts ({detail.assessment_summary.reassessment_count} reassessments)
                        </span>
                      </div>

                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                        <div className="p-3 bg-slate-50 rounded-lg">
                          <span className="text-[10px] font-semibold text-slate-500 block">Initial / Diagnostic</span>
                          <span className="text-lg font-mono font-bold text-slate-900">
                            {detail.assessment_summary.initial_diagnostic_score !== null
                              ? `${detail.assessment_summary.initial_diagnostic_score}%`
                              : detail.assessment_summary.initial_practice_score !== null
                              ? `${detail.assessment_summary.initial_practice_score}%`
                              : 'N/A'}
                          </span>
                        </div>
                        <div className="p-3 bg-slate-50 rounded-lg">
                          <span className="text-[10px] font-semibold text-slate-500 block">Latest Attempt</span>
                          <span className="text-lg font-mono font-bold text-[#635BFF]">
                            {detail.assessment_summary.latest_score !== null ? `${detail.assessment_summary.latest_score}%` : 'N/A'}
                          </span>
                        </div>
                        <div className="p-3 bg-slate-50 rounded-lg">
                          <span className="text-[10px] font-semibold text-slate-500 block">Best Score</span>
                          <span className="text-lg font-mono font-bold text-emerald-700">
                            {detail.assessment_summary.best_score !== null ? `${detail.assessment_summary.best_score}%` : 'N/A'}
                          </span>
                        </div>
                        <div className="p-3 bg-slate-50 rounded-lg">
                          <span className="text-[10px] font-semibold text-slate-500 block">Improvement Delta</span>
                          <span className="text-lg font-mono font-bold">
                            {detail.assessment_summary.improvement_delta !== null ? (
                              <span className={detail.assessment_summary.improvement_delta >= 0 ? 'text-emerald-600' : 'text-rose-600'}>
                                {detail.assessment_summary.improvement_delta > 0 ? '+' : ''}
                                {detail.assessment_summary.improvement_delta}%
                              </span>
                            ) : (
                              <span className="text-xs text-slate-400 italic">Not enough data yet</span>
                            )}
                          </span>
                        </div>
                      </div>

                      {/* Reassessment Scores Pills */}
                      {detail.assessment_summary.reassessment_scores.length > 0 && (
                        <div className="pt-2 border-t border-slate-100 flex items-center space-x-2 text-xs">
                          <span className="text-slate-500 font-semibold text-[11px]">Reassessments:</span>
                          <div className="flex flex-wrap gap-1.5">
                            {detail.assessment_summary.reassessment_scores.map((sc, i) => (
                              <span key={i} className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#F3F0FF] text-[#635BFF]">
                                {sc}%
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Step 2D: Weakest Concepts Card */}
                  {detail.weakest_concepts && detail.weakest_concepts.length > 0 && (
                    <div className="p-5 bg-white border border-slate-200 rounded-xl shadow-xs space-y-3">
                      <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                        <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center space-x-1.5">
                          <AlertTriangle className="w-4 h-4 text-amber-500" />
                          <span>Weakest Evaluated Concepts</span>
                        </h4>
                        <span className="text-[10px] text-slate-400">Pass Mark: {thresholds.assessment_pass}%</span>
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                        {detail.weakest_concepts.map((wc, i) => (
                          <div
                            key={i}
                            className={`p-3 rounded-lg border flex items-center justify-between ${
                              wc.is_struggling
                                ? 'bg-rose-50/50 border-rose-200 text-rose-900'
                                : 'bg-slate-50 border-slate-200 text-slate-800'
                            }`}
                          >
                            <div>
                              <span className="text-xs font-bold block">{wc.concept}</span>
                              <span className="text-[10px] text-slate-500">
                                {wc.correct_count} of {wc.total_questions} questions correct
                              </span>
                            </div>
                            <div className="text-right">
                              <span className={`font-mono text-xs font-bold ${wc.is_struggling ? 'text-rose-600' : 'text-slate-700'}`}>
                                {wc.accuracy_pct}%
                              </span>
                              {wc.is_struggling && (
                                <span className="block text-[9px] font-bold text-rose-500">Below Pass</span>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Diagnostic Card */}
                  <div className="p-5 bg-white border border-slate-200 rounded-xl shadow-xs flex flex-wrap items-center justify-between gap-4">
                    <div className="space-y-1">
                      <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
                        Diagnostic Assessment Score
                      </span>
                      <h4 className="text-sm font-bold text-slate-900">Initial Course Onboarding Baseline</h4>
                      <p className="text-xs text-slate-500">
                        Initial diagnostic evaluation used to synthesize initial personalized path and isolated gaps.
                      </p>
                    </div>
                    <div className="text-right">
                      {detail.diagnostic_score !== null ? (
                        <div className="text-3xl font-mono font-extrabold text-[#635BFF]">
                          {detail.diagnostic_score}%
                        </div>
                      ) : (
                        <span className="text-xs text-slate-400 italic">Diagnostic not completed</span>
                      )}
                    </div>
                  </div>

                  {/* Recent Assessment Attempts Table */}
                  <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
                    <div className="p-4 border-b border-slate-100">
                      <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                        Recent Assessment Attempts (Audit History)
                      </h4>
                    </div>
                    {detail.recent_attempts.length === 0 ? (
                      <div className="py-8 text-center text-slate-400 text-xs">
                        No recent assessment attempts recorded yet for this student.
                      </div>
                    ) : (
                      <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs">
                          <thead className="bg-slate-50 text-slate-500 border-b border-slate-200">
                            <tr>
                              <th className="py-2.5 px-3 font-semibold">Date & Time</th>
                              <th className="py-2.5 px-3 font-semibold">Type</th>
                              <th className="py-2.5 px-3 font-semibold">Topic / Target</th>
                              <th className="py-2.5 px-3 font-semibold text-center">Score</th>
                              <th className="py-2.5 px-3 font-semibold text-center">Percentage</th>
                              <th className="py-2.5 px-3 font-semibold text-center">Result</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-100">
                            {detail.recent_attempts.map((att) => (
                              <tr key={att.id} className="hover:bg-slate-50/70 transition-colors">
                                <td className="py-3 px-3 text-slate-500 text-[11px] font-mono">
                                  {att.created_at || 'N/A'}
                                </td>
                                <td className="py-3 px-3">
                                  <span className="capitalize font-semibold px-2 py-0.5 rounded text-[10px] bg-slate-100 text-slate-700">
                                    {att.attempt_type}
                                  </span>
                                </td>
                                <td className="py-3 px-3 font-medium text-slate-900">{att.topic_title}</td>
                                <td className="py-3 px-3 text-center font-mono text-slate-700">
                                  {att.score} / {att.max_score}
                                </td>
                                <td className="py-3 px-3 text-center font-mono font-bold text-slate-900">
                                  {att.percentage}%
                                </td>
                                <td className="py-3 px-3 text-center">
                                  <span
                                    className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                                      att.passed
                                        ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                                        : 'bg-rose-50 text-rose-700 border-rose-200'
                                    }`}
                                  >
                                    {att.passed ? 'Passed' : 'Needs Review'}
                                  </span>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* TAB 4: LEARNING PATH & PREREQUISITE GAPS */}
              {activeTab === 'path' && (
                <div className="space-y-6 animate-fadeIn">
                  {/* Prerequisite Gaps Alert */}
                  {detail.prerequisite_gaps.length > 0 && (
                    <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl space-y-2">
                      <div className="flex items-center space-x-2 text-xs font-bold text-amber-800">
                        <AlertTriangle className="w-4 h-4 text-amber-600" />
                        <span>Identified Prerequisite Gaps</span>
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                        {detail.prerequisite_gaps.map((gap, i) => (
                          <div
                            key={i}
                            className="p-3 bg-white/80 border border-amber-200 rounded-lg flex items-center justify-between"
                          >
                            <div>
                              <span className="font-bold text-slate-900 block">{gap.prereq_title}</span>
                              <span className="text-[11px] text-slate-500">Prerequisite for: {gap.topic_title}</span>
                            </div>
                            <div className="text-right">
                              <span className="font-mono font-bold text-rose-600 text-xs block">
                                {gap.current_mastery}% / {gap.required_mastery}%
                              </span>
                              <span className="text-[10px] text-rose-500 font-semibold">Deficit: -{gap.gap}%</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Learning Path Timeline */}
                  <div className="bg-white border border-slate-200 rounded-xl p-5 space-y-4 shadow-xs">
                    <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-100">
                      <div>
                        <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                          Personalized Learning Path Timeline (Read-Only)
                        </h4>
                        <p className="text-[11px] text-slate-500">
                          {learningPath?.adaptation_reason || 'Adaptive sequence generated by Progress Monitoring Agent.'}
                        </p>
                      </div>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                        Status: {learningPath?.status || 'ACTIVE'}
                      </span>
                    </div>

                    {!learningPath?.items || learningPath.items.length === 0 ? (
                      <div className="py-8 text-center text-slate-400 text-xs">
                        No learning path items available for this student.
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {learningPath.items.map((it, idx) => (
                          <div
                            key={it.id}
                            className={`p-4 rounded-xl border flex flex-col sm:flex-row sm:items-start justify-between gap-3 transition-colors ${
                              it.status === 'CURRENT'
                                ? 'bg-purple-50/50 border-purple-200'
                                : it.status === 'COMPLETED'
                                ? 'bg-emerald-50/30 border-emerald-100'
                                : 'bg-slate-50 border-slate-200'
                            }`}
                          >
                            <div className="flex items-start space-x-3">
                              <span className="font-mono text-xs font-bold w-6 h-6 rounded-full bg-slate-200 text-slate-700 flex items-center justify-center flex-shrink-0 mt-0.5">
                                {it.sequence_order}
                              </span>
                              <div className="space-y-1">
                                <div className="flex items-center space-x-2">
                                  <span className="font-bold text-slate-900 text-xs">{it.topic_title}</span>
                                  <span className="text-[10px] font-mono px-1.5 py-0.5 bg-white text-slate-600 border border-slate-200 rounded">
                                    {it.topic_code}
                                  </span>
                                  {it.is_remedial && (
                                    <span className="text-[10px] font-bold px-2 py-0.5 bg-amber-100 text-amber-800 border border-amber-200 rounded">
                                      Remedial Module
                                    </span>
                                  )}
                                </div>
                                <p className="text-[11px] text-slate-600 leading-relaxed">
                                  {it.recommendation_reason}
                                </p>
                                {it.is_remedial && it.remedial_title && (
                                  <div className="mt-1 p-2 bg-amber-50/80 border border-amber-200 rounded text-[11px] text-amber-900">
                                    <strong>Remedial Intervention:</strong> {it.remedial_title}
                                    {it.remedial_description && ` — ${it.remedial_description}`}
                                  </div>
                                )}
                              </div>
                            </div>

                            <div className="sm:self-center flex-shrink-0">
                              {getStatusBadge(it.status)}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* TAB 5: IMPACT & INTERVENTIONS */}
              {activeTab === 'impact' && (
                <div className="space-y-6 animate-fadeIn">
                  {/* Summary Metric Strip */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs">
                      <span className="text-[11px] font-medium text-slate-500 block">Baseline CO at Enrollment</span>
                      <span className="text-2xl font-mono font-extrabold text-slate-700 mt-1 block">
                        {impactData?.baseline_co_avg !== undefined ? `${impactData.baseline_co_avg}%` : 'N/A'}
                      </span>
                    </div>
                    <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs">
                      <span className="text-[11px] font-medium text-slate-500 block">Current Outcome Attainment</span>
                      <span className="text-2xl font-mono font-extrabold text-[#635BFF] mt-1 block">
                        {impactData?.current_co_avg !== undefined ? `${impactData.current_co_avg}%` : 'N/A'}
                      </span>
                    </div>
                    <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs">
                      <span className="text-[11px] font-medium text-slate-500 block">Net Improvement Delta</span>
                      <span
                        className={`text-2xl font-mono font-extrabold mt-1 block ${
                          (impactData?.overall_co_delta ?? 0) >= 0 ? 'text-emerald-600' : 'text-rose-600'
                        }`}
                      >
                        {impactData?.overall_co_delta !== undefined
                          ? `${impactData.overall_co_delta > 0 ? '+' : ''}${impactData.overall_co_delta}%`
                          : 'N/A'}
                      </span>
                    </div>
                  </div>

                  {/* Attribution Notice */}
                  <div className="p-4 bg-purple-50/70 border border-purple-200/80 rounded-xl text-xs text-purple-900 space-y-1">
                    <span className="font-bold flex items-center space-x-1">
                      <Sparkles className="w-3.5 h-3.5 text-[#635BFF]" />
                      <span>Association, not proof of causation</span>
                    </span>
                    <p className="text-[11px] text-purple-800">
                      Performance shifts around intervention events represent observational correlation. Multiple external variables, including student study habits and concurrent coursework, also contribute to learning outcomes.
                    </p>
                  </div>

                  {/* Sufficiency Check */}
                  {impactData && !impactData.has_enough_data && (
                    <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800 flex items-center space-x-2">
                      <AlertCircle className="w-4 h-4 flex-shrink-0" />
                      <span>Not enough data yet (minimum 2 historical evaluations required for before/after comparison).</span>
                    </div>
                  )}

                  {/* Flag Teacher Intervention Form */}
                  <div className="p-5 bg-white border border-slate-200 rounded-xl shadow-xs space-y-3">
                    <div className="flex items-center space-x-2">
                      <span className="p-1.5 bg-amber-100 rounded-lg text-amber-700">
                        <MessageSquare className="w-4 h-4" />
                      </span>
                      <div>
                        <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                          Record Faculty Intervention
                        </h4>
                        <p className="text-[11px] text-slate-500">
                          Log 1-on-1 mentoring, office hour discussions, or tailored remedial instructions.
                        </p>
                      </div>
                    </div>

                    <form onSubmit={handleFlagIntervention} className="space-y-3">
                      <textarea
                        rows={2}
                        value={flagNote}
                        onChange={(e) => setFlagNote(e.target.value)}
                        placeholder="e.g. Conducted 1-on-1 code walkthrough on recursion call stack and base cases."
                        className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-[#635BFF]/30 resize-none"
                      />

                      {flagError && (
                        <div className="text-xs text-rose-600 font-semibold">{flagError}</div>
                      )}

                      {flagSuccess && (
                        <div className="text-xs text-emerald-600 font-semibold flex items-center space-x-1">
                          <Check className="w-3.5 h-3.5" />
                          <span>Intervention logged successfully!</span>
                        </div>
                      )}

                      <div className="flex justify-end">
                        <button
                          type="submit"
                          disabled={flagSubmitting || !flagNote.trim()}
                          className="px-4 py-2 bg-[#635BFF] hover:bg-[#5349e0] disabled:bg-slate-300 text-white rounded-xl text-xs font-semibold transition-all flex items-center space-x-1.5 shadow-xs"
                        >
                          {flagSubmitting ? (
                            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <Send className="w-3.5 h-3.5" />
                          )}
                          <span>Record Intervention</span>
                        </button>
                      </div>
                    </form>
                  </div>

                  {/* Before vs After Intervention Attribution Analysis */}
                  {(() => {
                    const comps = impactData?.before_after_comparisons ?? [];
                    if (comps.length === 0) return null;
                    return (
                      <div className="p-5 bg-white border border-slate-200 rounded-xl shadow-xs space-y-3">
                        <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider pb-2 border-b border-slate-100">
                          Before vs After Intervention Trajectory
                        </h4>
                        <div className="space-y-3">
                          {comps.map((c, i) => {
                            const coBefore = c?.co_before_avg ?? (c as any)?.co_before ?? null;
                            const coAfter = c?.co_after_avg ?? (c as any)?.co_after ?? null;
                            const coDelta = c?.co_delta ?? null;
                            const mastBefore = c?.mastery_before_avg ?? (c as any)?.mastery_before ?? null;
                            const mastAfter = c?.mastery_after_avg ?? (c as any)?.mastery_after ?? null;
                            const mastDelta = c?.mastery_delta ?? null;

                            return (
                              <div key={i} className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl space-y-2 text-xs">
                                <div className="flex items-center justify-between">
                                  <span className="font-bold capitalize px-2 py-0.5 rounded bg-purple-100 text-[#635BFF] text-[10px]">
                                    {(c?.type || 'event').replace('_', ' ')}
                                  </span>
                                  <span className="text-[10px] text-slate-400 font-mono">
                                    {c?.date ? new Date(c.date).toLocaleDateString() : 'N/A'}
                                  </span>
                                </div>
                                {c?.note && (
                                  <p className="text-[11px] text-slate-600 italic">Note: "{c.note}"</p>
                                )}
                                <div className="grid grid-cols-2 gap-2 pt-1 font-mono text-[11px]">
                                  <div className="p-2 bg-white rounded border border-slate-200">
                                    <span className="text-slate-400 block text-[10px]">Course Outcome Delta</span>
                                    <span className={`font-bold ${coDelta !== null && coDelta >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                                      {coDelta !== null ? `${coDelta > 0 ? '+' : ''}${coDelta}%` : 'N/A'}
                                    </span>
                                  </div>
                                  <div className="p-2 bg-white rounded border border-slate-200">
                                    <span className="text-slate-400 block text-[10px]">Topic Mastery Delta</span>
                                    <span className={`font-bold ${mastDelta !== null && mastDelta >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                                      {mastDelta !== null ? `${mastDelta > 0 ? '+' : ''}${mastDelta}%` : 'N/A'}
                                    </span>
                                  </div>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    );
                  })()}

                  {/* Chronological Timeline */}
                  {(() => {
                    const timelinePts = impactData?.timeline ?? (impactData as any)?.co_timeline ?? [];
                    if (timelinePts.length === 0) return null;
                    return (
                      <div className="p-5 bg-white border border-slate-200 rounded-xl shadow-xs space-y-3">
                        <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider pb-2 border-b border-slate-100">
                          Course Outcome Timeline Audit
                        </h4>
                        <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                          {timelinePts.map((pt: any, i: number) => {
                            const dateVal = pt?.date || (pt as any)?.created_at;
                            return (
                              <div key={i} className="p-2.5 bg-slate-50 border border-slate-200/80 rounded-lg flex items-center justify-between text-xs">
                                <div className="space-y-0.5">
                                  <span className="font-bold text-slate-800">{pt?.outcome_code || 'CO'}</span>
                                  <span className="text-[10px] text-slate-400 block font-mono">
                                    {dateVal ? new Date(dateVal).toLocaleString() : 'N/A'} • Trigger: {pt?.trigger || 'eval'}
                                  </span>
                                </div>
                                <span className="font-mono font-bold text-[#635BFF]">{pt?.attainment_pct ?? 0}%</span>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    );
                  })()}
                </div>
              )}
            </>
          ) : null}
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-slate-200 bg-slate-50 flex items-center justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-200 hover:bg-slate-300 text-slate-800 rounded-xl font-semibold text-xs transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
