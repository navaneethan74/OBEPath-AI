import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Search,
  ArrowUpDown,
  RefreshCw,
  AlertCircle,
  Award,
  BookOpen,
  ArrowRight,
  Sparkles
} from 'lucide-react';
import { api } from '../services/api';
import { ClassAssessmentsResponse } from '../types';

interface FacultyAssessmentsTabProps {
  classId: number;
  onSelectStudent?: (studentId: number) => void;
}

export const FacultyAssessmentsTab: React.FC<FacultyAssessmentsTabProps> = ({
  classId,
  onSelectStudent
}) => {
  const [data, setData] = useState<ClassAssessmentsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'name' | 'initial' | 'latest' | 'best' | 'delta' | 'attempts'>('latest');
  const [sortAsc, setSortAsc] = useState(false);

  useEffect(() => {
    if (classId) {
      loadAssessments();
    }
  }, [classId]);

  const loadAssessments = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getClassAssessments(classId);
      setData(res ?? null);
    } catch (err: any) {
      setError(err?.message || 'Failed to load class assessments.');
    } finally {
      setLoading(false);
    }
  };

  const studentsList = data?.students ?? [];
  const initialAvg = data?.class_initial_avg ?? (data as any)?.class_averages?.initial_average ?? null;
  const latestAvg = data?.class_latest_avg ?? (data as any)?.class_averages?.latest_average ?? null;
  const avgImprovement = data?.class_avg_improvement ?? (data as any)?.class_averages?.improvement_average ?? null;
  const totalStudents = data?.total_students ?? studentsList.length;

  const filteredStudents = studentsList.filter((s) => {
    const term = (searchTerm || '').toLowerCase();
    const name = (s?.name || '').toLowerCase();
    const email = (s?.email || '').toLowerCase();
    return name.includes(term) || email.includes(term);
  });

  filteredStudents.sort((a, b) => {
    let diff = 0;
    if (sortBy === 'name') {
      diff = (a?.name || '').localeCompare(b?.name || '');
    } else if (sortBy === 'initial') {
      const aScore = a?.initial_score ?? a?.initial_diagnostic_score ?? -1;
      const bScore = b?.initial_score ?? b?.initial_diagnostic_score ?? -1;
      diff = aScore - bScore;
    } else if (sortBy === 'latest') {
      const aScore = a?.latest_score ?? a?.initial_score ?? a?.initial_diagnostic_score ?? -1;
      const bScore = b?.latest_score ?? b?.initial_score ?? b?.initial_diagnostic_score ?? -1;
      diff = aScore - bScore;
    } else if (sortBy === 'best') {
      const aScore = a?.best_score ?? a?.latest_score ?? a?.initial_score ?? -1;
      const bScore = b?.best_score ?? b?.latest_score ?? b?.initial_score ?? -1;
      diff = aScore - bScore;
    } else if (sortBy === 'delta') {
      const aDelta = a?.improvement_delta ?? -999;
      const bDelta = b?.improvement_delta ?? -999;
      diff = aDelta - bDelta;
    } else if (sortBy === 'attempts') {
      const aAtt = a?.total_attempts_count ?? (a as any)?.total_attempts ?? 0;
      const bAtt = b?.total_attempts_count ?? (b as any)?.total_attempts ?? 0;
      diff = aAtt - bAtt;
    }
    return sortAsc ? diff : -diff;
  });

  if (loading) {
    return (
      <div className="py-24 text-center space-y-3 bg-white rounded-2xl border border-slate-200 p-8 shadow-xs">
        <RefreshCw className="w-8 h-8 animate-spin mx-auto text-[#635BFF]" />
        <p className="text-xs text-slate-500 font-medium">Loading Assessment History & Reassessments...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-rose-50 border border-rose-200 rounded-2xl text-rose-700 flex items-start space-x-3 shadow-xs">
        <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
        <div className="space-y-1">
          <p className="text-xs font-bold">Failed to load class assessment data</p>
          <p className="text-xs">{error}</p>
          <button
            onClick={loadAssessments}
            className="mt-2 px-3 py-1 bg-white border border-rose-300 text-rose-700 rounded-lg text-xs font-semibold hover:bg-rose-100 transition-colors inline-flex items-center space-x-1"
          >
            <RefreshCw className="w-3 h-3" />
            <span>Retry</span>
          </button>
        </div>
      </div>
    );
  }

  const isImprovementPositive = avgImprovement !== null && avgImprovement !== undefined && avgImprovement >= 0;

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Top Class Averages Banner */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="p-5 bg-white border border-[#E2E8F0] rounded-2xl shadow-xs space-y-1">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold">
            <span>Class Initial Average</span>
            <BookOpen className="w-4 h-4 text-slate-400" />
          </div>
          <div className="text-2xl font-mono font-extrabold text-slate-900">
            {initialAvg !== null && initialAvg !== undefined ? `${initialAvg}%` : 'N/A'}
          </div>
          <span className="text-[11px] text-slate-400 block">Baseline diagnostic / first attempt score</span>
        </div>

        <div className="p-5 bg-white border border-[#E2E8F0] rounded-2xl shadow-xs space-y-1">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold">
            <span>Class Latest Average</span>
            <Award className="w-4 h-4 text-[#635BFF]" />
          </div>
          <div className="text-2xl font-mono font-extrabold text-[#635BFF]">
            {latestAvg !== null && latestAvg !== undefined ? `${latestAvg}%` : 'N/A'}
          </div>
          <span className="text-[11px] text-slate-400 block">Most recent evaluation average</span>
        </div>

        <div className="p-5 bg-white border border-[#E2E8F0] rounded-2xl shadow-xs space-y-1">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold">
            <span>Average Improvement</span>
            {isImprovementPositive ? (
              <TrendingUp className="w-4 h-4 text-emerald-600" />
            ) : (
              <TrendingDown className="w-4 h-4 text-rose-500" />
            )}
          </div>
          <div
            className={`text-2xl font-mono font-extrabold ${
              isImprovementPositive ? 'text-emerald-600' : 'text-rose-600'
            }`}
          >
            {avgImprovement !== null && avgImprovement !== undefined
              ? `${avgImprovement > 0 ? '+' : ''}${avgImprovement}%`
              : 'N/A'}
          </div>
          <span className="text-[11px] text-slate-400 block">Class-wide delta from initial to latest</span>
        </div>

        <div className="p-5 bg-white border border-[#E2E8F0] rounded-2xl shadow-xs space-y-1">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold">
            <span>Cohort Students</span>
            <Sparkles className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-2xl font-mono font-extrabold text-slate-900">
            {totalStudents}
          </div>
          <span className="text-[11px] text-slate-400 block">Active enrolled learners</span>
        </div>
      </div>

      {/* Controls Bar */}
      <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-xs flex flex-wrap items-center justify-between gap-4">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search students by name or email..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:outline-hidden focus:ring-2 focus:ring-[#635BFF]/30"
          />
        </div>

        <div className="flex items-center space-x-2 text-xs">
          <span className="text-slate-500 font-semibold">Sort by:</span>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-bold text-slate-800 focus:outline-hidden"
          >
            <option value="latest">Latest Score</option>
            <option value="initial">Initial Score</option>
            <option value="best">Best Score</option>
            <option value="delta">Improvement Delta</option>
            <option value="attempts">Attempt Count</option>
            <option value="name">Student Name</option>
          </select>
          <button
            onClick={() => setSortAsc(!sortAsc)}
            className="p-1.5 bg-slate-100 hover:bg-slate-200 rounded-lg text-slate-600 transition-colors"
            title="Toggle sort direction"
          >
            <ArrowUpDown className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Assessment Table */}
      <div className="bg-white border border-[#E2E8F0] rounded-2xl shadow-xs overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Student Assessment Performance & Reassessment Tracking
            </h3>
            <span className="text-xs text-slate-400 font-mono">({filteredStudents.length} learners)</span>
          </div>
          <span className="text-[11px] text-slate-400">Read-Only Oversight</span>
        </div>

        {filteredStudents.length === 0 ? (
          <div className="py-16 text-center text-slate-400 text-xs">
            {searchTerm
              ? 'No students match your search filter.'
              : 'No assessment attempts recorded yet for this class.'}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 border-b border-slate-200">
                <tr>
                  <th className="py-3 px-4 font-bold">Student</th>
                  <th className="py-3 px-3 font-bold text-center">Diagnostic</th>
                  <th className="py-3 px-3 font-bold text-center">Initial Score</th>
                  <th className="py-3 px-3 font-bold text-center">Latest Score</th>
                  <th className="py-3 px-3 font-bold text-center">Best Score</th>
                  <th className="py-3 px-3 font-bold text-center">Improvement</th>
                  <th className="py-3 px-3 font-bold text-center">Attempts</th>
                  <th className="py-3 px-4 font-bold">Reassessment Scores</th>
                  <th className="py-3 px-4 font-bold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredStudents.map((s) => {
                  const reassessments = s?.reassessment_scores ?? [];
                  const attemptsCount = s?.total_attempts_count ?? (s as any)?.total_attempts ?? 0;
                  const reassessCount = s?.reassessments_count ?? reassessments.length;
                  const delta = s?.improvement_delta;

                  return (
                    <tr key={s?.student_id} className="hover:bg-slate-50/70 transition-colors">
                      <td className="py-3.5 px-4">
                        <div className="font-bold text-slate-900">{s?.name || 'Student'}</div>
                        <div className="text-[11px] text-slate-400">{s?.email || ''}</div>
                      </td>

                      <td className="py-3.5 px-3 text-center font-mono">
                        {s?.initial_diagnostic_score !== null && s?.initial_diagnostic_score !== undefined ? (
                          <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-purple-50 text-[#635BFF]">
                            {s.initial_diagnostic_score}%
                          </span>
                        ) : (
                          <span className="text-slate-400 italic text-[11px]">—</span>
                        )}
                      </td>

                      <td className="py-3.5 px-3 text-center font-mono text-slate-700 font-semibold">
                        {s?.initial_score !== null && s?.initial_score !== undefined ? `${s.initial_score}%` : '—'}
                      </td>

                      <td className="py-3.5 px-3 text-center font-mono font-bold text-slate-900">
                        {s?.latest_score !== null && s?.latest_score !== undefined ? `${s.latest_score}%` : '—'}
                      </td>

                      <td className="py-3.5 px-3 text-center font-mono font-bold text-emerald-700">
                        {s?.best_score !== null && s?.best_score !== undefined ? `${s.best_score}%` : '—'}
                      </td>

                      <td className="py-3.5 px-3 text-center">
                        {delta !== null && delta !== undefined && attemptsCount >= 2 ? (
                          <span
                            className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-bold ${
                              delta > 0
                                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                : delta < 0
                                ? 'bg-rose-50 text-rose-700 border border-rose-200'
                                : 'bg-slate-100 text-slate-600 border border-slate-200'
                            }`}
                          >
                            {delta > 0 ? (
                              <TrendingUp className="w-3 h-3" />
                            ) : delta < 0 ? (
                              <TrendingDown className="w-3 h-3" />
                            ) : null}
                            <span>
                              {delta > 0 ? '+' : ''}
                              {delta}%
                            </span>
                          </span>
                        ) : (
                          <span className="text-slate-400 italic text-[10px]">Not enough data yet</span>
                        )}
                      </td>

                      <td className="py-3.5 px-3 text-center font-mono text-slate-700">
                        <span className="font-bold text-xs">{attemptsCount}</span>
                        {reassessCount > 0 && (
                          <span className="text-[10px] text-slate-400 block font-normal">
                            ({reassessCount} reassess)
                          </span>
                        )}
                      </td>

                      <td className="py-3.5 px-4">
                        {reassessments.length === 0 ? (
                          <span className="text-slate-400 italic text-[11px]">No reassessments</span>
                        ) : (
                          <div className="flex flex-wrap gap-1 max-w-[200px]">
                            {reassessments.map((sc, i) => (
                              <span
                                key={i}
                                className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 text-[10px] font-mono font-semibold"
                              >
                                {sc}%
                              </span>
                            ))}
                          </div>
                        )}
                      </td>

                      <td className="py-3.5 px-4 text-right">
                        {onSelectStudent && (
                          <button
                            onClick={() => onSelectStudent(s?.student_id)}
                            className="px-2.5 py-1 text-xs font-semibold text-[#635BFF] hover:bg-[#F3F0FF] rounded-lg transition-colors inline-flex items-center space-x-1"
                          >
                            <span>Profile</span>
                            <ArrowRight className="w-3 h-3" />
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
