import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Sparkles,
  Calendar,
  AlertCircle,
  RefreshCw,
  Info
} from 'lucide-react';
import { api } from '../services/api';
import { ClassImpactSummary, StudentImpactResponse } from '../types';

interface FacultyImpactTabProps {
  classId: number;
  onSelectStudent?: (studentId: number) => void;
}

export const FacultyImpactTab: React.FC<FacultyImpactTabProps> = ({
  classId,
  onSelectStudent
}) => {
  const [summaryData, setSummaryData] = useState<ClassImpactSummary | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(true);
  const [summaryError, setSummaryError] = useState<string | null>(null);

  // Selected student drilldown
  const [selectedStudentId, setSelectedStudentId] = useState<number | null>(null);
  const [studentImpact, setStudentImpact] = useState<StudentImpactResponse | null>(null);
  const [studentLoading, setStudentLoading] = useState(false);
  const [studentError, setStudentError] = useState<string | null>(null);

  useEffect(() => {
    if (classId) {
      loadImpactSummary();
    }
  }, [classId]);

  useEffect(() => {
    if (classId && selectedStudentId) {
      loadStudentImpact(selectedStudentId);
    }
  }, [classId, selectedStudentId]);

  const loadImpactSummary = async () => {
    setSummaryLoading(true);
    setSummaryError(null);
    try {
      const res = await api.getClassImpactSummary(classId);
      setSummaryData(res ?? null);
      const summaryList = res?.students_summary ?? [];
      if (summaryList.length > 0 && !selectedStudentId) {
        setSelectedStudentId(summaryList[0].student_id);
      }
    } catch (err: any) {
      setSummaryError(err?.message || 'Failed to load class impact summary.');
    } finally {
      setSummaryLoading(false);
    }
  };

  const loadStudentImpact = async (studentId: number) => {
    setStudentLoading(true);
    setStudentError(null);
    try {
      const res = await api.getClassStudentImpact(classId, studentId);
      setStudentImpact(res ?? null);
    } catch (err: any) {
      setStudentError(err?.message || 'Failed to load student impact metrics.');
    } finally {
      setStudentLoading(false);
    }
  };

  if (summaryLoading) {
    return (
      <div className="py-24 text-center space-y-3 bg-white rounded-2xl border border-slate-200 p-8 shadow-xs">
        <RefreshCw className="w-8 h-8 animate-spin mx-auto text-[#635BFF]" />
        <p className="text-xs text-slate-500 font-medium">Computing Cohort Learning Impact & Before/After Attributions...</p>
      </div>
    );
  }

  if (summaryError) {
    return (
      <div className="p-6 bg-rose-50 border border-rose-200 rounded-2xl text-rose-700 flex items-start space-x-3 shadow-xs">
        <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
        <div className="space-y-1">
          <p className="text-xs font-bold">Failed to load impact analytics</p>
          <p className="text-xs">{summaryError}</p>
          <button
            onClick={loadImpactSummary}
            className="mt-2 px-3 py-1 bg-white border border-rose-300 text-rose-700 rounded-lg text-xs font-semibold hover:bg-rose-100 transition-colors inline-flex items-center space-x-1"
          >
            <RefreshCw className="w-3 h-3" />
            <span>Retry</span>
          </button>
        </div>
      </div>
    );
  }

  const getInterventionBadge = (type: string) => {
    switch (type) {
      case 'remedial_inserted':
        return {
          label: 'Remedial Inserted',
          bg: 'bg-purple-50 text-[#635BFF] border-purple-200'
        };
      case 'path_adapted':
        return {
          label: 'Path Adapted',
          bg: 'bg-blue-50 text-blue-700 border-blue-200'
        };
      case 'teacher_flag':
        return {
          label: 'Teacher Intervention',
          bg: 'bg-amber-50 text-amber-800 border-amber-200'
        };
      case 'class_joined':
        return {
          label: 'Class Joined (Baseline)',
          bg: 'bg-emerald-50 text-emerald-700 border-emerald-200'
        };
      default:
        return {
          label: (type || 'event').replace('_', ' '),
          bg: 'bg-slate-100 text-slate-700 border-slate-200'
        };
    }
  };

  const studentsSummary = summaryData?.students_summary ?? [];
  const timeline = studentImpact?.timeline ?? (studentImpact as any)?.co_timeline ?? [];
  const interventions = studentImpact?.interventions ?? [];
  const comparisons = studentImpact?.before_after_comparisons ?? [];

  const studentName = studentImpact?.student_name ?? (studentImpact as any)?.student?.name ?? 'Student';
  const studentId = studentImpact?.student_id ?? (studentImpact as any)?.student?.id ?? selectedStudentId;
  const joinedAt = studentImpact?.joined_at ?? (studentImpact as any)?.student?.joined_at ?? null;

  const currentStudentSummary = studentsSummary.find((s) => s?.student_id === selectedStudentId);
  const baselineCoAval = studentImpact?.baseline_co_avg ?? currentStudentSummary?.baseline_co_avg ?? (currentStudentSummary as any)?.baseline_avg_co ?? 0.0;
  const currentCoAval = studentImpact?.current_co_avg ?? currentStudentSummary?.current_co_avg ?? (currentStudentSummary as any)?.current_avg_co ?? 0.0;
  const overallDeltaVal = studentImpact?.overall_co_delta ?? currentStudentSummary?.delta ?? 0.0;

  const avgDelta = summaryData?.avg_co_delta_since_joining;
  const isAvgDeltaPositive = avgDelta !== undefined && avgDelta !== null && avgDelta >= 0;

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* 1. Cohort Impact Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="p-5 bg-white border border-[#E2E8F0] rounded-2xl shadow-xs space-y-1">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold">
            <span>Avg CO Delta Since Join</span>
            {isAvgDeltaPositive ? (
              <TrendingUp className="w-4 h-4 text-emerald-600" />
            ) : (
              <TrendingDown className="w-4 h-4 text-rose-500" />
            )}
          </div>
          <div
            className={`text-2xl font-mono font-extrabold ${
              isAvgDeltaPositive ? 'text-emerald-600' : 'text-rose-600'
            }`}
          >
            {avgDelta !== undefined && avgDelta !== null
              ? `${avgDelta > 0 ? '+' : ''}${avgDelta}%`
              : 'N/A'}
          </div>
          <span className="text-[11px] text-slate-400 block">Net outcome attainment improvement</span>
        </div>

        <div className="p-5 bg-white border border-[#E2E8F0] rounded-2xl shadow-xs space-y-1">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold">
            <span>Improved Learners</span>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700">
              Delta &gt; +1%
            </span>
          </div>
          <div className="text-2xl font-mono font-extrabold text-emerald-600">
            {summaryData?.improved_count ?? 0}
          </div>
          <span className="text-[11px] text-slate-400 block">Positive progression since enrollment</span>
        </div>

        <div className="p-5 bg-white border border-[#E2E8F0] rounded-2xl shadow-xs space-y-1">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold">
            <span>Unchanged Learners</span>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-700">
              ±1% Range
            </span>
          </div>
          <div className="text-2xl font-mono font-extrabold text-slate-700">
            {summaryData?.unchanged_count ?? 0}
          </div>
          <span className="text-[11px] text-slate-400 block">Maintained baseline standing</span>
        </div>

        <div className="p-5 bg-white border border-[#E2E8F0] rounded-2xl shadow-xs space-y-1">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold">
            <span>Declined Learners</span>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-50 text-rose-700">
              Delta &lt; -1%
            </span>
          </div>
          <div className="text-2xl font-mono font-extrabold text-rose-600">
            {summaryData?.declined_count ?? 0}
          </div>
          <span className="text-[11px] text-slate-400 block">Needs targeted faculty intervention</span>
        </div>
      </div>

      {/* 2. Attribution Notice Banner */}
      <div className="p-4 bg-purple-50/70 border border-purple-200/80 rounded-2xl flex items-start space-x-3 text-xs text-purple-900">
        <Info className="w-4 h-4 text-[#635BFF] flex-shrink-0 mt-0.5" />
        <div className="space-y-0.5">
          <span className="font-bold">Association, not proof of causation</span>
          <p className="text-[11px] text-purple-800 leading-relaxed">
            Attainment deltas and performance shifts around intervention events (remedial module insertion, adaptive path restructuring, and faculty mentoring flags) represent observational correlation. Multiple external variables, including student study habits and concurrent coursework, also contribute to learning outcomes.
          </p>
        </div>
      </div>

      {/* 3. Student Drilldown Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Student Selector Sidebar */}
        <div className="bg-white border border-[#E2E8F0] rounded-2xl p-4 shadow-xs space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <span className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Enrolled Students
            </span>
            <span className="text-xs font-mono text-slate-400">
              {studentsSummary.length}
            </span>
          </div>

          {studentsSummary.length === 0 ? (
            <div className="py-12 text-center text-slate-400 text-xs">
              No students enrolled in this class yet.
            </div>
          ) : (
            <div className="space-y-1.5 max-h-[500px] overflow-y-auto pr-1">
              {studentsSummary.map((s) => {
                const isSelected = s?.student_id === selectedStudentId;
                const deltaVal = s?.delta ?? 0;
                return (
                  <div
                    key={s?.student_id}
                    onClick={() => setSelectedStudentId(s?.student_id)}
                    className={`p-3 rounded-xl border transition-all cursor-pointer flex items-center justify-between ${
                      isSelected
                        ? 'bg-[#F3F0FF] border-[#635BFF] text-[#635BFF] shadow-xs'
                        : 'bg-white hover:bg-slate-50 border-slate-200/70 text-slate-800'
                    }`}
                  >
                    <div className="space-y-0.5 min-w-0 pr-2">
                      <span className="font-bold text-xs block truncate">{s?.name || 'Student'}</span>
                      <span className="text-[11px] text-slate-400 block truncate">{s?.email || ''}</span>
                    </div>
                    <div className="text-right flex-shrink-0">
                      <span
                        className={`font-mono text-xs font-bold ${
                          deltaVal > 0
                            ? 'text-emerald-600'
                            : deltaVal < 0
                            ? 'text-rose-600'
                            : 'text-slate-500'
                        }`}
                      >
                        {deltaVal > 0 ? '+' : ''}{deltaVal}%
                      </span>
                      <span className="text-[10px] text-slate-400 block capitalize">
                        {s?.status || 'unchanged'}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Selected Student Impact Detail */}
        <div className="lg:col-span-2 space-y-6">
          {studentLoading ? (
            <div className="py-24 text-center space-y-2 bg-white rounded-2xl border border-slate-200 p-8 shadow-xs">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto text-[#635BFF]" />
              <p className="text-xs text-slate-400">Loading student impact history...</p>
            </div>
          ) : studentError ? (
            <div className="p-6 bg-rose-50 border border-rose-200 rounded-2xl text-xs text-rose-700 flex items-start space-x-3 shadow-xs">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <div className="space-y-1">
                <span className="font-bold">Failed to load student impact metrics</span>
                <p>{studentError}</p>
                {selectedStudentId && (
                  <button
                    onClick={() => loadStudentImpact(selectedStudentId)}
                    className="mt-2 px-3 py-1 bg-white border border-rose-300 text-rose-700 rounded-lg text-xs font-semibold hover:bg-rose-100 transition-colors inline-flex items-center space-x-1"
                  >
                    <RefreshCw className="w-3 h-3" />
                    <span>Retry</span>
                  </button>
                )}
              </div>
            </div>
          ) : studentImpact ? (
            <div className="space-y-6">
              {/* Student Header Card */}
              <div className="bg-white border border-[#E2E8F0] rounded-2xl p-5 shadow-xs flex flex-wrap items-center justify-between gap-4">
                <div className="space-y-1">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
                    Student Impact Report
                  </span>
                  <h3 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
                    <span>{studentName}</span>
                    {onSelectStudent && studentId && (
                      <button
                        onClick={() => onSelectStudent(studentId)}
                        className="text-xs text-[#635BFF] hover:underline font-semibold"
                      >
                        (Open Full Profile)
                      </button>
                    )}
                  </h3>
                  <span className="text-xs text-slate-500">
                    Enrolled since: {joinedAt ? new Date(joinedAt).toLocaleDateString() : 'N/A'}
                  </span>
                </div>

                <div className="flex items-center space-x-4">
                  <div className="text-right">
                    <span className="text-[11px] text-slate-400 block">Baseline Avg CO</span>
                    <span className="font-mono text-base font-bold text-slate-700">
                      {baselineCoAval}%
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="text-[11px] text-slate-400 block">Current Avg CO</span>
                    <span className="font-mono text-base font-bold text-[#635BFF]">
                      {currentCoAval}%
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="text-[11px] text-slate-400 block">Net CO Delta</span>
                    <span
                      className={`font-mono text-base font-extrabold ${
                        overallDeltaVal >= 0 ? 'text-emerald-600' : 'text-rose-600'
                      }`}
                    >
                      {overallDeltaVal > 0 ? '+' : ''}{overallDeltaVal}%
                    </span>
                  </div>
                </div>
              </div>

              {/* Data Sufficiency Warning if Applicable */}
              {(!studentImpact.has_enough_data || timeline.length < 2) && (
                <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800 flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span>Not enough data yet (minimum 2 historical evaluations required for before/after comparison)</span>
                </div>
              )}

              {/* CO Attainment Timeline & Intervention Markers */}
              <div className="bg-white border border-[#E2E8F0] rounded-2xl p-5 shadow-xs space-y-4">
                <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                  <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center space-x-2">
                    <Calendar className="w-4 h-4 text-[#635BFF]" />
                    <span>Course Outcome Attainment & Intervention Timeline</span>
                  </h4>
                  <span className="text-xs font-mono text-slate-400">
                    {timeline.length} data points
                  </span>
                </div>

                {timeline.length === 0 ? (
                  <div className="py-8 text-center text-slate-400 text-xs">
                    No timeline history points recorded yet for this student.
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="relative pl-6 border-l-2 border-purple-200 space-y-4">
                      {timeline.map((pt: any, idx: number) => {
                        const ptDateStr = String(pt?.date || (pt as any)?.created_at || '');
                        const matchingIntervention = interventions.find((ev) => {
                          const evDateStr = String(ev?.created_at || (ev as any)?.date || '');
                          if (!evDateStr || !ptDateStr) return false;
                          return evDateStr.slice(0, 10) === ptDateStr.slice(0, 10);
                        });

                        return (
                          <div key={idx} className="relative group">
                            <div className="absolute -left-[31px] top-1.5 w-3.5 h-3.5 rounded-full bg-white border-2 border-[#635BFF]" />
                            <div className="p-3 bg-slate-50/70 hover:bg-slate-50 border border-slate-200/80 rounded-xl flex items-center justify-between transition-colors">
                              <div className="space-y-0.5">
                                <div className="flex items-center space-x-2">
                                  <span className="font-mono text-[11px] font-bold text-slate-700">
                                    {pt?.outcome_code || 'CO'}
                                  </span>
                                  <span className="text-[10px] text-slate-400 font-mono">
                                    {ptDateStr ? new Date(ptDateStr).toLocaleString() : 'N/A'}
                                  </span>
                                  <span className="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-slate-200/70 text-slate-600 uppercase">
                                    {pt?.trigger || 'eval'}
                                  </span>
                                </div>
                                {matchingIntervention && (
                                  <div className="pt-1">
                                    <span
                                      className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                                        getInterventionBadge(matchingIntervention.type).bg
                                      }`}
                                    >
                                      <span>★ {getInterventionBadge(matchingIntervention.type).label}</span>
                                      {matchingIntervention.note && (
                                        <span className="font-normal italic">
                                          — "{matchingIntervention.note}"
                                        </span>
                                      )}
                                    </span>
                                  </div>
                                )}
                              </div>
                              <span className="font-mono text-xs font-extrabold text-[#635BFF]">
                                {pt?.attainment_pct ?? 0}%
                              </span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>

              {/* Before / After Intervention Comparison Cards */}
              <div className="bg-white border border-[#E2E8F0] rounded-2xl p-5 shadow-xs space-y-4">
                <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                  <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center space-x-2">
                    <Sparkles className="w-4 h-4 text-amber-500" />
                    <span>Before vs After Intervention Attribution Analysis</span>
                  </h4>
                  <span className="text-xs font-mono text-slate-400">
                    {comparisons.length} events analyzed
                  </span>
                </div>

                {comparisons.length === 0 ? (
                  <div className="py-8 text-center text-slate-400 text-xs">
                    No intervention events with before/after comparisons recorded yet.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {comparisons.map((c, i) => {
                      const badge = getInterventionBadge(c?.type || '');
                      const coBefore = c?.co_before_avg ?? (c as any)?.co_before ?? null;
                      const coAfter = c?.co_after_avg ?? (c as any)?.co_after ?? null;
                      const coDelta = c?.co_delta ?? null;
                      const mastBefore = c?.mastery_before_avg ?? (c as any)?.mastery_before ?? null;
                      const mastAfter = c?.mastery_after_avg ?? (c as any)?.mastery_after ?? null;
                      const mastDelta = c?.mastery_delta ?? null;

                      return (
                        <div
                          key={i}
                          className="p-4 bg-slate-50/50 border border-slate-200 rounded-xl space-y-3"
                        >
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <div className="flex items-center space-x-2">
                              <span
                                className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${badge.bg}`}
                              >
                                {badge.label}
                              </span>
                              <span className="text-[11px] text-slate-400 font-mono">
                                {c?.date ? new Date(c.date).toLocaleDateString() : 'N/A'}
                              </span>
                            </div>
                            {c?.note && (
                              <span className="text-xs text-slate-600 italic bg-white px-2 py-0.5 rounded border border-slate-200">
                                Note: {c.note}
                              </span>
                            )}
                          </div>

                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                            {/* Outcome Attainment Comparison */}
                            <div className="p-3 bg-white border border-slate-200 rounded-lg space-y-1">
                              <span className="text-[11px] font-semibold text-slate-500 block">
                                Course Outcome Attainment (CO Avg)
                              </span>
                              <div className="flex items-center justify-between font-mono">
                                <span className="text-slate-600">
                                  Before: {coBefore !== null ? `${coBefore}%` : 'N/A'}
                                </span>
                                <span className="text-slate-400">→</span>
                                <span className="font-bold text-slate-900">
                                  After: {coAfter !== null ? `${coAfter}%` : 'N/A'}
                                </span>
                              </div>
                              <div className="text-right">
                                {coDelta !== null ? (
                                  <span
                                    className={`font-mono text-xs font-extrabold ${
                                      coDelta >= 0 ? 'text-emerald-600' : 'text-rose-600'
                                    }`}
                                  >
                                    Delta: {coDelta > 0 ? '+' : ''}{coDelta}%
                                  </span>
                                ) : (
                                  <span className="text-[10px] text-slate-400 italic">
                                    Not enough data
                                  </span>
                                )}
                              </div>
                            </div>

                            {/* Topic Mastery Comparison */}
                            <div className="p-3 bg-white border border-slate-200 rounded-lg space-y-1">
                              <span className="text-[11px] font-semibold text-slate-500 block">
                                Topic Overall Mastery
                              </span>
                              <div className="flex items-center justify-between font-mono">
                                <span className="text-slate-600">
                                  Before: {mastBefore !== null ? `${mastBefore}%` : 'N/A'}
                                </span>
                                <span className="text-slate-400">→</span>
                                <span className="font-bold text-slate-900">
                                  After: {mastAfter !== null ? `${mastAfter}%` : 'N/A'}
                                </span>
                              </div>
                              <div className="text-right">
                                {mastDelta !== null ? (
                                  <span
                                    className={`font-mono text-xs font-extrabold ${
                                      mastDelta >= 0 ? 'text-emerald-600' : 'text-rose-600'
                                    }`}
                                  >
                                    Delta: {mastDelta > 0 ? '+' : ''}{mastDelta}%
                                  </span>
                                ) : (
                                  <span className="text-[10px] text-slate-400 italic">
                                    Not enough data
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="py-24 text-center text-slate-400 text-xs bg-white rounded-2xl border border-slate-200">
              Select a student from the cohort list to inspect their impact and intervention trajectory.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
