import React, { useState, useEffect } from 'react';
import {
  X,
  Award,
  Search,
  BookOpen,
  ArrowUpDown,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  TrendingUp,
  Layers
} from 'lucide-react';
import { api } from '../services/api';
import { ClassOutcomeDrilldown, OutcomeStudentRow } from '../types';

interface CODrilldownModalProps {
  isOpen: boolean;
  onClose: () => void;
  classId: number;
  outcomeId: number;
  className: string;
}

export const CODrilldownModal: React.FC<CODrilldownModalProps> = ({
  isOpen,
  onClose,
  classId,
  outcomeId,
  className
}) => {
  const [data, setData] = useState<ClassOutcomeDrilldown | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState<'name' | 'attainment'>('name');
  const [sortAsc, setSortAsc] = useState(true);

  useEffect(() => {
    if (isOpen && classId && outcomeId) {
      loadDrilldown();
    }
  }, [isOpen, classId, outcomeId]);

  const loadDrilldown = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getClassOutcomeDrilldown(classId, outcomeId);
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to load outcome drill-down.');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const thresholds = data?.thresholds || {
    prereq_unlock: 60.0,
    assessment_pass: 60.0,
    topic_mastery: 80.0,
    co_achieved_default: 70.0,
    at_risk_mastery: 50.0,
    inactive_days: 7
  };

  // Helper to color-code mastery using API thresholds
  const getMasteryColorClass = (score: number) => {
    if (score >= thresholds.topic_mastery) {
      return 'bg-emerald-50 text-emerald-800 border-emerald-200';
    }
    if (score >= thresholds.prereq_unlock) {
      return 'bg-amber-50 text-amber-800 border-amber-200';
    }
    return 'bg-rose-50 text-rose-800 border-rose-200';
  };

  // Filter and sort students
  const filteredStudents: OutcomeStudentRow[] = (data?.student_rows || []).filter((s) => {
    const q = searchTerm.toLowerCase().trim();
    return s.student_name.toLowerCase().includes(q) || s.student_email.toLowerCase().includes(q);
  });

  filteredStudents.sort((a, b) => {
    if (sortField === 'name') {
      return sortAsc
        ? a.student_name.localeCompare(b.student_name)
        : b.student_name.localeCompare(a.student_name);
    }
    return sortAsc
      ? a.co_attainment_pct - b.co_attainment_pct
      : b.co_attainment_pct - a.co_attainment_pct;
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4 sm:p-6 animate-fadeIn">
      <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-5xl w-full max-h-[90vh] flex flex-col overflow-hidden animate-scaleUp">
        {/* Modal Header */}
        <div className="p-6 border-b border-slate-200 flex items-start justify-between bg-slate-50/50">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <span className="px-2.5 py-0.5 rounded-md text-xs font-bold bg-[#F3F0FF] text-[#635BFF] border border-purple-100">
                {data?.outcome.code || 'CO'}
              </span>
              <span className="text-xs text-slate-500 font-medium">Class: {className}</span>
            </div>
            <h3 className="text-xl font-bold text-slate-900">
              {data?.outcome.code}: {data?.outcome.description}
            </h3>
            <p className="text-xs text-slate-500">
              Outcome Attainment Drill-down • Contributing Topics Weighted Evaluation • Concept Mastery
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-200 rounded-xl text-slate-400 hover:text-slate-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {loading ? (
            <div className="py-20 text-center space-y-2 text-slate-400">
              <RefreshCw className="w-8 h-8 animate-spin mx-auto text-[#635BFF]" />
              <p className="text-xs">Loading Outcome Attainment Drill-down...</p>
            </div>
          ) : error ? (
            <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-center space-x-2">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          ) : data ? (
            <>
              {/* Outcome Metrics Summary Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs">
                  <span className="text-xs font-medium text-slate-500 block">Class Average Attainment</span>
                  <div className="mt-2 text-2xl font-extrabold text-slate-900 font-mono">
                    {data.class_avg_attainment}%
                  </div>
                  <span className="text-[11px] text-slate-400">Target: {data.outcome.target_attainment_pct}%</span>
                </div>

                <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs">
                  <span className="text-xs font-medium text-slate-500 block">Students Achieved</span>
                  <div className="mt-2 text-2xl font-extrabold text-emerald-600 font-mono">
                    {data.achieved_ratio}
                  </div>
                  <span className="text-[11px] text-emerald-600 font-medium">
                    {data.total_students > 0
                      ? `${Math.round((data.achieved_count / data.total_students) * 100)}% of cohort`
                      : '0%'}
                  </span>
                </div>

                <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs">
                  <span className="text-xs font-medium text-slate-500 block">Contributing Topics</span>
                  <div className="mt-2 text-2xl font-extrabold text-[#635BFF] font-mono">
                    {data.contributing_topics.length}
                  </div>
                  <span className="text-[11px] text-slate-400">Weighted curriculum concepts</span>
                </div>
              </div>

              {/* Contributing Topics Weights & Average Mastery */}
              <div className="p-5 bg-slate-50/70 border border-slate-200 rounded-xl space-y-3">
                <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center space-x-1.5">
                  <Layers className="w-3.5 h-3.5 text-[#635BFF]" />
                  <span>Curricular Contributing Topics (Weights & Cohort Performance)</span>
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {data.contributing_topics.map((t) => (
                    <div
                      key={t.topic_id}
                      className="p-3 bg-white border border-slate-200 rounded-lg shadow-xs flex flex-col justify-between space-y-2"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-bold px-1.5 py-0.5 bg-slate-100 text-slate-700 rounded font-mono">
                          {t.code}
                        </span>
                        <span className="text-[10px] font-semibold text-slate-500">
                          Weight: <strong className="text-slate-800">{t.weight}x</strong>
                        </span>
                      </div>
                      <span className="text-xs font-bold text-slate-900 line-clamp-1">{t.title}</span>
                      <div className="flex items-center justify-between text-xs pt-1 border-t border-slate-100">
                        <span className="text-slate-500 text-[11px]">Class Avg:</span>
                        <span
                          className={`font-mono font-bold px-2 py-0.5 rounded text-[11px] border ${getMasteryColorClass(
                            t.class_avg_mastery
                          )}`}
                        >
                          {t.class_avg_mastery}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Student Performance Rows Table */}
              <div className="space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h4 className="text-sm font-bold text-slate-900">Student Attainment & Concept Breakdown</h4>
                    <p className="text-xs text-slate-500">
                      Sort and search individual student attainment and concept-level mastery.
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="relative">
                      <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
                      <input
                        type="text"
                        placeholder="Search student..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="pl-8 pr-3 py-1.5 border border-slate-200 rounded-lg text-xs text-slate-800 bg-white focus:outline-hidden focus:ring-2 focus:ring-[#635BFF]/20"
                      />
                    </div>
                    <button
                      onClick={() => {
                        if (sortField === 'attainment') {
                          setSortAsc(!sortAsc);
                        } else {
                          setSortField('attainment');
                          setSortAsc(false);
                        }
                      }}
                      className="px-3 py-1.5 border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-semibold flex items-center space-x-1 shadow-xs"
                    >
                      <ArrowUpDown className="w-3 h-3" />
                      <span>Attainment %</span>
                    </button>
                  </div>
                </div>

                {filteredStudents.length === 0 ? (
                  <div className="py-10 text-center text-slate-400 text-xs border border-dashed border-slate-200 rounded-xl">
                    No enrolled students match your search query.
                  </div>
                ) : (
                  <div className="overflow-x-auto border border-slate-200 rounded-xl">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-slate-50 border-b border-slate-200 text-slate-600">
                        <tr>
                          <th className="py-3 px-3 font-semibold">Student</th>
                          <th className="py-3 px-3 font-semibold text-center">Outcome Attainment</th>
                          <th className="py-3 px-3 font-semibold text-center">Status</th>
                          {data.contributing_topics.map((t) => (
                            <th key={t.topic_id} className="py-3 px-3 font-semibold text-center">
                              {t.code} Mastery
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 bg-white">
                        {filteredStudents.map((st) => (
                          <tr key={st.student_id} className="hover:bg-slate-50/70 transition-colors">
                            <td className="py-3 px-3">
                              <span className="font-bold text-slate-900 block">{st.student_name}</span>
                              <span className="text-[11px] text-slate-400">{st.student_email}</span>
                            </td>
                            <td className="py-3 px-3 text-center">
                              <span className="font-mono font-bold text-slate-900 text-sm">
                                {st.co_attainment_pct}%
                              </span>
                            </td>
                            <td className="py-3 px-3 text-center">
                              <span
                                className={`inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${
                                  st.is_achieved
                                    ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                                    : 'bg-amber-50 text-amber-700 border-amber-200'
                                }`}
                              >
                                {st.is_achieved ? (
                                  <>
                                    <CheckCircle2 className="w-3 h-3" />
                                    <span>Achieved</span>
                                  </>
                                ) : (
                                  <>
                                    <AlertCircle className="w-3 h-3" />
                                    <span>In Progress</span>
                                  </>
                                )}
                              </span>
                            </td>
                            {st.concept_mastery.map((cm) => (
                              <td key={cm.topic_id} className="py-3 px-3 text-center">
                                <span
                                  className={`inline-block font-mono font-bold px-2.5 py-1 rounded-md text-[11px] border ${getMasteryColorClass(
                                    cm.mastery_score
                                  )}`}
                                >
                                  {cm.mastery_score}%
                                </span>
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </>
          ) : null}
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-slate-200 bg-slate-50 flex items-center justify-between text-xs text-slate-500">
          <div className="flex items-center space-x-4">
            <span className="flex items-center space-x-1">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block" />
              <span>≥ {thresholds.topic_mastery}% Mastered</span>
            </span>
            <span className="flex items-center space-x-1">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block" />
              <span>≥ {thresholds.prereq_unlock}% Developing</span>
            </span>
            <span className="flex items-center space-x-1">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500 inline-block" />
              <span>&lt; {thresholds.prereq_unlock}% Gap</span>
            </span>
          </div>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-200 hover:bg-slate-300 text-slate-800 rounded-xl font-semibold transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
