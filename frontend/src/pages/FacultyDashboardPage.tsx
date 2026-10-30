import React, { useState, useEffect } from 'react';
import {
  Users,
  TrendingUp,
  AlertTriangle,
  Award,
  BookOpen,
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  RefreshCw,
  Search,
  Plus,
  Copy,
  Check,
  Power,
  RotateCcw,
  UserX,
  Calendar,
  AlertCircle,
  X,
  ChevronDown,
  Layers,
  ArrowRight,
  Filter,
  ArrowUpDown,
  ExternalLink,
  Clock
} from 'lucide-react';
import { api } from '../services/api';
import {
  ClassInfo,
  ClassOverview,
  ExtendedClassStudentsResponse,
  ExtendedClassStudent
} from '../types';
import { CODrilldownModal } from '../components/CODrilldownModal';
import { StudentDetailModal } from '../components/StudentDetailModal';
import { FacultyAssessmentsTab } from '../components/FacultyAssessmentsTab';
import { FacultyLearningGapsTab } from '../components/FacultyLearningGapsTab';
import { FacultyImpactTab } from '../components/FacultyImpactTab';
import { ErrorBoundary } from '../components/ErrorBoundary';

export const FacultyDashboardPage: React.FC = () => {
  // Navigation tab state: 'overview' | 'students' | 'assessments' | 'gaps' | 'impact' | 'management'
  const [activeTab, setActiveTab] = useState<'overview' | 'students' | 'assessments' | 'gaps' | 'impact' | 'management'>('overview');

  // Classes list
  const [classes, setClasses] = useState<ClassInfo[]>([]);
  const [classesLoading, setClassesLoading] = useState(true);
  const [classesError, setClassesError] = useState<string | null>(null);

  // Selected class
  const [selectedClassId, setSelectedClassId] = useState<number | null>(null);

  // Overview data for selected class
  const [overviewData, setOverviewData] = useState<ClassOverview | null>(null);
  const [overviewLoading, setOverviewLoading] = useState(false);
  const [overviewError, setOverviewError] = useState<string | null>(null);

  // Students list for selected class
  const [studentsData, setStudentsData] = useState<ExtendedClassStudentsResponse | null>(null);
  const [studentsLoading, setStudentsLoading] = useState(false);
  const [studentsError, setStudentsError] = useState<string | null>(null);

  // Modals state
  const [drilldownOutcomeId, setDrilldownOutcomeId] = useState<number | null>(null);
  const [selectedStudentDetailId, setSelectedStudentDetailId] = useState<number | null>(null);

  // Students tab search & filter
  const [studentSearch, setStudentSearch] = useState('');
  const [filterAtRiskOnly, setFilterAtRiskOnly] = useState(false);
  const [studentSortBy, setStudentSortBy] = useState<'name' | 'mastery' | 'progress'>('mastery');
  const [studentSortAsc, setStudentSortAsc] = useState(false);

  // Create Class modal state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createCourseId, setCreateCourseId] = useState<number>(1);
  const [createName, setCreateName] = useState('');
  const [createCustomCode, setCreateCustomCode] = useState('');
  const [createMaxStudents, setCreateMaxStudents] = useState('');
  const [createExpiresAt, setCreateExpiresAt] = useState('');
  const [createSubmitting, setCreateSubmitting] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  // Copy code feedback & action loaders
  const [copiedCode, setCopiedCode] = useState<string | null>(null);
  const [actionLoadingId, setActionLoadingId] = useState<number | null>(null);

  useEffect(() => {
    loadClasses();
  }, []);

  useEffect(() => {
    if (selectedClassId) {
      loadClassOverview(selectedClassId);
      loadClassStudents(selectedClassId);
    }
  }, [selectedClassId]);

  const loadClasses = async () => {
    setClassesLoading(true);
    setClassesError(null);
    try {
      const res = await api.getFacultyClasses();
      setClasses(res || []);
      if (res && res.length > 0 && !selectedClassId) {
        setSelectedClassId(res[0].id);
      }
    } catch (err: any) {
      setClassesError(err.message || 'Failed to load class cohorts.');
    } finally {
      setClassesLoading(false);
    }
  };

  const loadClassOverview = async (classId: number) => {
    setOverviewLoading(true);
    setOverviewError(null);
    try {
      const res = await api.getClassOverview(classId);
      setOverviewData(res);
    } catch (err: any) {
      setOverviewError(err.message || 'Failed to load class overview metrics.');
    } finally {
      setOverviewLoading(false);
    }
  };

  const loadClassStudents = async (classId: number) => {
    setStudentsLoading(true);
    setStudentsError(null);
    try {
      const res = await api.getClassStudents(classId);
      setStudentsData(res);
    } catch (err: any) {
      setStudentsError(err.message || 'Failed to load enrolled students roster.');
    } finally {
      setStudentsLoading(false);
    }
  };

  const handleCopyCode = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(code);
    setTimeout(() => {
      setCopiedCode(null);
    }, 2000);
  };

  const handleCreateClass = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createName.trim()) {
      setCreateError('Please provide a class name.');
      return;
    }
    setCreateSubmitting(true);
    setCreateError(null);
    try {
      const payload: any = {
        course_id: createCourseId,
        name: createName.trim()
      };
      if (createCustomCode.trim()) payload.custom_code = createCustomCode.trim();
      if (createMaxStudents.trim()) {
        const parsed = parseInt(createMaxStudents, 10);
        if (!isNaN(parsed) && parsed > 0) payload.max_students = parsed;
      }
      if (createExpiresAt.trim()) {
        payload.expires_at = new Date(createExpiresAt).toISOString();
      }

      const created = await api.createFacultyClass(payload);
      setShowCreateModal(false);
      setCreateName('');
      setCreateCustomCode('');
      setCreateMaxStudents('');
      setCreateExpiresAt('');
      await loadClasses();
      if (created && created.id) {
        setSelectedClassId(created.id);
      }
    } catch (err: any) {
      setCreateError(err.message || 'Failed to create class.');
    } finally {
      setCreateSubmitting(false);
    }
  };

  const handleToggleActive = async (cls: ClassInfo) => {
    setActionLoadingId(cls.id);
    try {
      if (cls.is_active) {
        await api.disableClassCode(cls.id);
      } else {
        await api.enableClassCode(cls.id);
      }
      await loadClasses();
    } catch (err: any) {
      alert(err.message || 'Failed to toggle class status.');
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleRegenerateCode = async (cls: ClassInfo) => {
    if (!confirm(`Are you sure you want to regenerate the code for "${cls.name}"? The previous code will stop working immediately.`)) {
      return;
    }
    setActionLoadingId(cls.id);
    try {
      const res = await api.regenerateClassCode(cls.id);
      alert(res.message);
      await loadClasses();
    } catch (err: any) {
      alert(err.message || 'Failed to regenerate code.');
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleRemoveStudent = async (studentId: number, studentName: string) => {
    if (!selectedClassId) return;
    if (!confirm(`Are you sure you want to remove ${studentName} from this class? Their learning history will remain safe.`)) {
      return;
    }
    try {
      await api.removeStudentFromClass(selectedClassId, studentId);
      await loadClassStudents(selectedClassId);
      await loadClassOverview(selectedClassId);
      await loadClasses();
    } catch (err: any) {
      alert(err.message || 'Failed to remove student.');
    }
  };

  const selectedClass = classes.find((c) => c.id === selectedClassId) || classes[0];

  const thresholds = overviewData?.thresholds || {
    prereq_unlock: 60.0,
    assessment_pass: 60.0,
    topic_mastery: 80.0,
    co_achieved_default: 70.0,
    at_risk_mastery: 50.0,
    inactive_days: 7
  };

  // Filtered and sorted students for the Students Tab
  const filteredStudents: ExtendedClassStudent[] = (studentsData?.students || []).filter((s) => {
    const q = studentSearch.toLowerCase().trim();
    const matchesSearch = !q || s.name.toLowerCase().includes(q) || s.email.toLowerCase().includes(q);
    const matchesAtRisk = !filterAtRiskOnly || s.is_at_risk;
    return matchesSearch && matchesAtRisk;
  });

  filteredStudents.sort((a, b) => {
    if (studentSortBy === 'name') {
      return studentSortAsc ? a.name.localeCompare(b.name) : b.name.localeCompare(a.name);
    }
    if (studentSortBy === 'progress') {
      return studentSortAsc
        ? a.completed_topics_count - b.completed_topics_count
        : b.completed_topics_count - a.completed_topics_count;
    }
    return studentSortAsc
      ? a.current_overall_mastery - b.current_overall_mastery
      : b.current_overall_mastery - a.current_overall_mastery;
  });

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="inline-flex items-center space-x-2 px-3 py-1 bg-[#F3F0FF] border border-purple-100 rounded-full text-xs font-semibold text-[#635BFF] mb-1.5">
            <Users className="w-3.5 h-3.5 text-[#635BFF]" />
            <span>Faculty Institutional Dashboard • Step 2C</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
            Class Cohort Analytics & Outcome Oversight
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Real-Time Course Outcomes • Prerequisite Gap Isolation • Read-Only Cohort Views
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-[#635BFF] hover:bg-[#5349e0] text-white rounded-xl text-xs font-semibold transition-all flex items-center space-x-1.5 shadow-sm"
          >
            <Plus className="w-4 h-4" />
            <span>Create Class</span>
          </button>
          <button
            onClick={() => {
              loadClasses();
              if (selectedClassId) {
                loadClassOverview(selectedClassId);
                loadClassStudents(selectedClassId);
              }
            }}
            className="px-4 py-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-xl text-xs font-semibold transition-colors flex items-center space-x-2 shadow-xs"
          >
            <RefreshCw className="w-3.5 h-3.5 text-[#635BFF]" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Class Selector Bar */}
      <div className="bg-white border border-[#E2E8F0] rounded-2xl p-4 sm:p-5 shadow-[0_4px_20px_rgba(15,23,42,0.03)] flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center space-x-3 flex-1 min-w-[280px]">
          <span className="text-xs font-bold text-slate-600 uppercase tracking-wider whitespace-nowrap">
            Current Class:
          </span>
          {classesLoading ? (
            <div className="flex items-center space-x-2 text-xs text-slate-400">
              <RefreshCw className="w-4 h-4 animate-spin text-[#635BFF]" />
              <span>Loading classes...</span>
            </div>
          ) : classes.length === 0 ? (
            <span className="text-xs text-slate-500 italic">No classes available. Create one to begin.</span>
          ) : (
            <select
              value={selectedClassId || ''}
              onChange={(e) => setSelectedClassId(parseInt(e.target.value, 10))}
              className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-bold text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-[#635BFF]/30 max-w-md w-full"
            >
              {classes.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} ({c.course_code || 'CS'} • Code: {c.class_code}) — {c.active_students_count} students
                </option>
              ))}
            </select>
          )}
        </div>

        {selectedClass && (
          <div className="flex items-center space-x-3 text-xs">
            <span className="px-2.5 py-1 bg-slate-100 text-slate-700 rounded-lg font-mono font-bold">
              Join Code: {selectedClass.class_code}
            </span>
            <button
              onClick={() => handleCopyCode(selectedClass.class_code)}
              className="p-1.5 hover:bg-slate-100 rounded-lg text-slate-500 hover:text-slate-800 transition-colors"
              title="Copy join code"
            >
              {copiedCode === selectedClass.class_code ? (
                <span className="text-emerald-600 font-bold flex items-center space-x-1 text-[11px]">
                  <Check className="w-3.5 h-3.5" />
                  <span>Copied</span>
                </span>
              ) : (
                <Copy className="w-4 h-4" />
              )}
            </button>
            <span
              className={`px-2.5 py-1 rounded-full text-[10px] font-bold border ${
                selectedClass.is_active
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                  : 'bg-slate-100 text-slate-600 border-slate-300'
              }`}
            >
              {selectedClass.is_active ? 'Enrollments Active' : 'Joining Disabled'}
            </span>
          </div>
        )}
      </div>

      {/* Main Tab Navigation */}
      <div className="flex border-b border-slate-200 space-x-2">
        <button
          onClick={() => setActiveTab('overview')}
          className={`py-3 px-5 text-xs font-bold border-b-2 transition-all flex items-center space-x-2 ${
            activeTab === 'overview'
              ? 'border-[#635BFF] text-[#635BFF]'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <TrendingUp className="w-4 h-4" />
          <span>Class Overview</span>
        </button>
        <button
          onClick={() => setActiveTab('students')}
          className={`py-3 px-5 text-xs font-bold border-b-2 transition-all flex items-center space-x-2 ${
            activeTab === 'students'
              ? 'border-[#635BFF] text-[#635BFF]'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Users className="w-4 h-4" />
          <span>Enrolled Students Roster</span>
          {overviewData?.active_students_count !== undefined && (
            <span className="px-2 py-0.5 rounded-full text-[10px] bg-slate-100 text-slate-700">
              {overviewData.active_students_count}
            </span>
          )}
          {overviewData?.at_risk_count !== undefined && overviewData.at_risk_count > 0 && (
            <span className="px-2 py-0.5 rounded-full text-[10px] bg-rose-100 text-rose-700 font-bold">
              {overviewData.at_risk_count} at-risk
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab('assessments')}
          className={`py-3 px-5 text-xs font-bold border-b-2 transition-all flex items-center space-x-2 ${
            activeTab === 'assessments'
              ? 'border-[#635BFF] text-[#635BFF]'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Award className="w-4 h-4" />
          <span>Assessments</span>
        </button>
        <button
          onClick={() => setActiveTab('gaps')}
          className={`py-3 px-5 text-xs font-bold border-b-2 transition-all flex items-center space-x-2 ${
            activeTab === 'gaps'
              ? 'border-[#635BFF] text-[#635BFF]'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <AlertTriangle className="w-4 h-4 text-amber-500" />
          <span>Learning Gaps</span>
        </button>
        <button
          onClick={() => setActiveTab('impact')}
          className={`py-3 px-5 text-xs font-bold border-b-2 transition-all flex items-center space-x-2 ${
            activeTab === 'impact'
              ? 'border-[#635BFF] text-[#635BFF]'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Sparkles className="w-4 h-4 text-purple-600" />
          <span>Impact</span>
        </button>
        <button
          onClick={() => setActiveTab('management')}
          className={`py-3 px-5 text-xs font-bold border-b-2 transition-all flex items-center space-x-2 ${
            activeTab === 'management'
              ? 'border-[#635BFF] text-[#635BFF]'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Layers className="w-4 h-4" />
          <span>My Classes & Join Codes ({classes.length})</span>
        </button>
      </div>

      {/* ================================================== */}
      {/* TAB 1: CLASS OVERVIEW                              */}
      {/* ================================================== */}
      {activeTab === 'overview' && (
        <ErrorBoundary fallbackTitle="Class Overview View Encountered an Error">
        <div className="space-y-8 animate-fadeIn">
          {overviewLoading ? (
            <div className="py-24 text-center space-y-2 text-slate-400">
              <RefreshCw className="w-8 h-8 animate-spin mx-auto text-[#635BFF]" />
              <p className="text-xs">Computing Class Analytics & Outcome Attainment...</p>
            </div>
          ) : overviewError ? (
            <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-center space-x-2">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <span>{overviewError}</span>
            </div>
          ) : !overviewData ? (
            <div className="py-16 text-center text-slate-400 text-xs border border-dashed border-slate-200 rounded-2xl">
              Select or create a class to view cohort analytics.
            </div>
          ) : (
            <>
              {/* Stat Cards Strip */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
                <div className="p-6 bg-white border border-[#E2E8F0] rounded-2xl shadow-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                      Active Enrolled Students
                    </span>
                    <Users className="w-5 h-5 text-blue-500" />
                  </div>
                  <div className="mt-4 text-4xl font-extrabold text-slate-900 font-mono">
                    {overviewData.active_students_count}
                  </div>
                  <span className="text-xs text-slate-400 mt-1 block">
                    Course: {overviewData.course.title} ({overviewData.course.code})
                  </span>
                </div>

                <div className="p-6 bg-white border border-[#E2E8F0] rounded-2xl shadow-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                      Cohort Average Mastery
                    </span>
                    <TrendingUp className="w-5 h-5 text-[#635BFF]" />
                  </div>
                  <div className="mt-4 text-4xl font-extrabold text-[#635BFF] font-mono">
                    {overviewData.average_overall_mastery}%
                  </div>
                  <div className="mt-2 w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-[#635BFF] rounded-full transition-all"
                      style={{ width: `${Math.min(100, overviewData.average_overall_mastery)}%` }}
                    />
                  </div>
                </div>

                <div className="p-6 bg-rose-50/70 border border-rose-200 rounded-2xl shadow-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-rose-800 uppercase tracking-wider">
                      At-Risk Learners
                    </span>
                    <AlertTriangle className="w-5 h-5 text-rose-500" />
                  </div>
                  <div className="mt-4 text-4xl font-extrabold text-rose-600 font-mono">
                    {overviewData.at_risk_count}
                  </div>
                  <span className="text-xs text-rose-600 font-semibold mt-1 block">
                    {overviewData.at_risk_count === 0
                      ? 'All students in healthy progression'
                      : 'Triggered prerequisite gap, low mastery, or inactivity'}
                  </span>
                </div>
              </div>

              {/* CO1-CO4 Cards (Clickable Drill-down) */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-bold text-slate-900">Course Outcome Attainment (CO1 – CO4)</h3>
                    <p className="text-xs text-slate-500">
                      Class average attainment vs target threshold. Click any card to drill down into contributing concepts & student scores.
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {overviewData.outcomes.map((co) => {
                    const isTargetMet = co.class_avg_attainment >= co.target_attainment_pct;
                    return (
                      <div
                        key={co.outcome_id}
                        onClick={() => setDrilldownOutcomeId(co.outcome_id)}
                        className="p-5 bg-white border border-[#E2E8F0] hover:border-[#635BFF] rounded-2xl shadow-xs hover:shadow-md transition-all cursor-pointer flex flex-col justify-between space-y-4 group"
                      >
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="font-mono font-extrabold text-xs px-2.5 py-0.5 rounded-md bg-[#F3F0FF] text-[#635BFF] border border-purple-100">
                              {co.code}
                            </span>
                            <span
                              className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                                isTargetMet
                                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                                  : 'bg-amber-50 text-amber-700 border-amber-200'
                              }`}
                            >
                              {isTargetMet ? 'Target Met' : 'Developing'}
                            </span>
                          </div>
                          <h4 className="font-bold text-slate-900 text-xs line-clamp-2 leading-relaxed">
                            {co.description}
                          </h4>
                        </div>

                        <div className="space-y-2">
                          <div className="flex items-baseline justify-between">
                            <span className="text-2xl font-mono font-extrabold text-slate-900">
                              {co.class_avg_attainment}%
                            </span>
                            <span className="text-xs text-slate-400 font-mono">
                              Target: {co.target_attainment_pct}%
                            </span>
                          </div>

                          <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all ${
                                isTargetMet ? 'bg-emerald-500' : 'bg-[#635BFF]'
                              }`}
                              style={{ width: `${Math.min(100, co.class_avg_attainment)}%` }}
                            />
                          </div>

                          <div className="flex items-center justify-between text-[11px] text-slate-500 pt-2 border-t border-slate-100">
                            <span>Achieved: <strong>{co.achieved_ratio}</strong></span>
                            <span className="text-[#635BFF] font-semibold flex items-center space-x-1 group-hover:translate-x-0.5 transition-transform">
                              <span>Drill-down</span>
                              <ArrowRight className="w-3 h-3" />
                            </span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Topic Mastery Bar Chart & Distribution */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Topic Mastery Bar Chart */}
                <div className="lg:col-span-2 bg-white border border-[#E2E8F0] rounded-2xl p-6 sm:p-7 shadow-[0_4px_20px_rgba(15,23,42,0.03)] space-y-5">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                    <div>
                      <h3 className="text-base font-bold text-slate-900">Topic-Wise Cohort Mastery</h3>
                      <p className="text-xs text-slate-500">Average mastery percentage per curricular module</p>
                    </div>
                    <div className="flex items-center space-x-3 text-[11px] text-slate-500">
                      <span className="flex items-center space-x-1">
                        <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block" />
                        <span>Mastered (≥{thresholds.topic_mastery}%)</span>
                      </span>
                      <span className="flex items-center space-x-1">
                        <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block" />
                        <span>Proficient (≥{thresholds.prereq_unlock}%)</span>
                      </span>
                      <span className="flex items-center space-x-1">
                        <span className="w-2.5 h-2.5 rounded-full bg-rose-500 inline-block" />
                        <span>Gap (&lt;{thresholds.prereq_unlock}%)</span>
                      </span>
                    </div>
                  </div>

                  {overviewData.topic_masteries.length === 0 ? (
                    <div className="py-12 text-center text-slate-400 text-xs">
                      No topics configured for this course.
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {overviewData.topic_masteries.map((tm) => {
                        const barColor =
                          tm.avg_mastery >= thresholds.topic_mastery
                            ? 'bg-emerald-500'
                            : tm.avg_mastery >= thresholds.prereq_unlock
                            ? 'bg-amber-500'
                            : 'bg-rose-500';

                        return (
                          <div key={tm.topic_id} className="space-y-1.5 text-xs">
                            <div className="flex items-center justify-between">
                              <span className="font-semibold text-slate-800">
                                <span className="font-mono text-slate-400 mr-2">#{tm.order_index}</span>
                                {tm.title} ({tm.code})
                              </span>
                              <div className="flex items-center space-x-3">
                                {tm.at_risk_count > 0 && (
                                  <span className="text-[10px] text-rose-600 font-semibold">
                                    {tm.at_risk_count} below prereq
                                  </span>
                                )}
                                <span className="font-mono font-bold text-slate-900 w-12 text-right">
                                  {tm.avg_mastery}%
                                </span>
                              </div>
                            </div>
                            <div className="w-full bg-slate-100 h-3 rounded-full overflow-hidden">
                              <div
                                className={`h-full rounded-full transition-all ${barColor}`}
                                style={{ width: `${Math.min(100, tm.avg_mastery)}%` }}
                              />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>

                {/* Completion Distribution & Top Learning Gaps */}
                <div className="space-y-6">
                  {/* Top Learning Gaps */}
                  <div className="bg-white border border-[#E2E8F0] rounded-2xl p-6 shadow-[0_4px_20px_rgba(15,23,42,0.03)] space-y-4">
                    <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                      <h3 className="text-sm font-bold text-slate-900 flex items-center space-x-1.5">
                        <AlertCircle className="w-4 h-4 text-amber-500" />
                        <span>Top Learning Gaps</span>
                      </h3>
                      <span className="text-[10px] text-slate-400">Lowest mastery topics</span>
                    </div>

                    {overviewData.top_learning_gaps.length === 0 ? (
                      <div className="py-6 text-center text-slate-400 text-xs">
                        No critical learning gaps isolated.
                      </div>
                    ) : (
                      <div className="space-y-2.5">
                        {overviewData.top_learning_gaps.map((gap, i) => (
                          <div
                            key={gap.topic_id}
                            className="p-3 bg-amber-50/50 border border-amber-200 rounded-xl flex items-center justify-between text-xs"
                          >
                            <div className="space-y-0.5">
                              <span className="font-bold text-slate-900 block">{gap.title}</span>
                              <span className="text-[11px] text-slate-500">
                                Module code: <strong className="font-mono">{gap.code}</strong>
                              </span>
                            </div>
                            <span className="font-mono font-bold px-2.5 py-1 bg-white text-rose-600 border border-rose-200 rounded-lg">
                              {gap.avg_mastery}%
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Completion Distribution */}
                  <div className="bg-white border border-[#E2E8F0] rounded-2xl p-6 shadow-[0_4px_20px_rgba(15,23,42,0.03)] space-y-4">
                    <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                      <h3 className="text-sm font-bold text-slate-900 flex items-center space-x-1.5">
                        <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                        <span>Completion Distribution</span>
                      </h3>
                      <span className="text-[10px] text-slate-400">0..N topics complete</span>
                    </div>

                    {overviewData.completion_distribution.length === 0 ? (
                      <div className="py-6 text-center text-slate-400 text-xs">
                        No completion data yet for empty cohort.
                      </div>
                    ) : (
                      <div className="space-y-2">
                        {overviewData.completion_distribution.map((dist) => (
                          <div
                            key={dist.completed_topics}
                            className="flex items-center justify-between text-xs py-1 border-b border-slate-50 last:border-0"
                          >
                            <span className="text-slate-600 font-medium">
                              {dist.completed_topics} topics complete:
                            </span>
                            <span className="font-mono font-bold px-2 py-0.5 bg-slate-100 rounded text-slate-900">
                              {dist.student_count} {dist.student_count === 1 ? 'student' : 'students'}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
        </ErrorBoundary>
      )}

      {/* ================================================== */}
      {/* TAB 2: STUDENTS ROSTER                             */}
      {/* ================================================== */}
      {activeTab === 'students' && (
        <ErrorBoundary fallbackTitle="Enrolled Cohort Students View Encountered an Error">
        <div className="bg-white border border-[#E2E8F0] rounded-2xl p-6 sm:p-7 shadow-[0_4px_20px_rgba(15,23,42,0.03)] space-y-6 animate-fadeIn">
          {/* Header Controls */}
          <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-200">
            <div>
              <h3 className="text-base font-bold text-slate-900">Enrolled Students Progress & Attainment</h3>
              <p className="text-xs text-slate-500">
                Click any student row to view full progress breakdown, baseline delta, and learning path timeline.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              {/* Search */}
              <div className="relative">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  placeholder="Search students..."
                  value={studentSearch}
                  onChange={(e) => setStudentSearch(e.target.value)}
                  className="pl-8 pr-3 py-1.5 border border-slate-200 rounded-xl text-xs text-slate-800 bg-white focus:outline-hidden focus:ring-2 focus:ring-[#635BFF]/30"
                />
              </div>

              {/* At-Risk Only Filter Button */}
              <button
                onClick={() => setFilterAtRiskOnly(!filterAtRiskOnly)}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-colors border ${
                  filterAtRiskOnly
                    ? 'bg-rose-50 text-rose-700 border-rose-200'
                    : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
                }`}
              >
                <Filter className="w-3.5 h-3.5" />
                <span>At-Risk Only</span>
              </button>

              {/* Sort Selector */}
              <select
                value={studentSortBy}
                onChange={(e) => setStudentSortBy(e.target.value as any)}
                className="px-3 py-1.5 border border-slate-200 rounded-xl text-xs text-slate-700 bg-white focus:outline-hidden"
              >
                <option value="mastery">Sort by Mastery %</option>
                <option value="progress">Sort by Completed Topics</option>
                <option value="name">Sort by Name</option>
              </select>
            </div>
          </div>

          {/* Student Table */}
          {studentsLoading ? (
            <div className="py-20 text-center space-y-2 text-slate-400">
              <RefreshCw className="w-8 h-8 animate-spin mx-auto text-[#635BFF]" />
              <p className="text-xs">Loading Enrolled Cohort Students...</p>
            </div>
          ) : studentsError ? (
            <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-center space-x-2">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <span>{studentsError}</span>
            </div>
          ) : filteredStudents.length === 0 ? (
            <div className="py-12 text-center text-slate-400 text-xs border border-dashed border-slate-200 rounded-xl">
              No students found matching current filters.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-500 border-b border-slate-200">
                  <tr>
                    <th className="py-3 px-3 font-semibold">Student</th>
                    <th className="py-3 px-3 font-semibold text-center">Mastery</th>
                    <th className="py-3 px-3 font-semibold text-center">Completed Topics</th>
                    <th className="py-3 px-3 font-semibold text-center">Enrollment Baseline</th>
                    <th className="py-3 px-3 font-semibold text-center">CO Attainments</th>
                    <th className="py-3 px-3 font-semibold text-center">Diagnostic</th>
                    <th className="py-3 px-3 font-semibold">Last Activity</th>
                    <th className="py-3 px-3 font-semibold text-center">At-Risk</th>
                    <th className="py-3 px-3 font-semibold text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredStudents.map((st) => (
                    <tr
                      key={st.id}
                      onClick={() => setSelectedStudentDetailId(st.id)}
                      className="hover:bg-slate-50/80 transition-colors cursor-pointer"
                    >
                      {/* Name & Email */}
                      <td className="py-3.5 px-3">
                        <span className="font-bold text-slate-900 block">{st.name}</span>
                        <span className="text-[11px] text-slate-400">{st.email}</span>
                      </td>

                      {/* Overall Mastery */}
                      <td className="py-3.5 px-3 text-center">
                        <span
                          className={`inline-block font-mono font-bold px-2.5 py-1 rounded-md text-[11px] border ${
                            st.current_overall_mastery >= thresholds.topic_mastery
                              ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                              : st.current_overall_mastery >= thresholds.at_risk_mastery
                              ? 'bg-amber-50 text-amber-800 border-amber-200'
                              : 'bg-rose-50 text-rose-800 border-rose-200'
                          }`}
                        >
                          {st.current_overall_mastery}%
                        </span>
                      </td>

                      {/* Completed Topics */}
                      <td className="py-3.5 px-3 text-center">
                        <span className="font-mono font-bold text-slate-800 text-xs">
                          {st.completed_topics}
                        </span>
                        {st.improvement_since_join > 0 && (
                          <span className="text-[10px] font-bold text-emerald-600 block mt-0.5">
                            +{st.improvement_since_join} since join
                          </span>
                        )}
                      </td>

                      {/* Baseline Progress Notice */}
                      <td className="py-3.5 px-3 text-center text-slate-500 text-[11px]">
                        <span className="px-2 py-0.5 bg-slate-100 rounded text-slate-700 block max-w-fit mx-auto">
                          {st.progress_summary}
                        </span>
                      </td>

                      {/* CO Attainment Badges */}
                      <td className="py-3.5 px-3 text-center">
                        <div className="flex items-center justify-center space-x-1">
                          {st.co_attainments.map((coa) => (
                            <span
                              key={coa.outcome_id}
                              className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded border ${
                                coa.is_achieved
                                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                                  : 'bg-slate-50 text-slate-600 border-slate-200'
                              }`}
                              title={`${coa.code}: ${coa.attainment_pct}% (Target: ${coa.target_pct}%)`}
                            >
                              {coa.code}
                            </span>
                          ))}
                        </div>
                      </td>

                      {/* Diagnostic Score */}
                      <td className="py-3.5 px-3 text-center font-mono text-slate-700 text-xs">
                        {st.diagnostic_score !== null ? (
                          <span className="font-bold text-[#635BFF]">{st.diagnostic_score}%</span>
                        ) : (
                          <span className="text-slate-400 italic text-[11px]">N/A</span>
                        )}
                      </td>

                      {/* Last Activity */}
                      <td className="py-3.5 px-3 text-slate-500 text-[11px]">
                        {st.last_activity_date ? (
                          <span>{new Date(st.last_activity_date).toLocaleDateString()}</span>
                        ) : (
                          <span className="text-slate-400 italic">None</span>
                        )}
                      </td>

                      {/* At-Risk Badge */}
                      <td className="py-3.5 px-3 text-center">
                        {st.is_at_risk ? (
                          <span
                            className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200"
                            title={st.at_risk_reasons.join('; ')}
                          >
                            <AlertTriangle className="w-3 h-3" />
                            <span>At-Risk</span>
                          </span>
                        ) : (
                          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-semibold text-slate-500 bg-slate-50">
                            <span>Healthy</span>
                          </span>
                        )}
                      </td>

                      {/* Action */}
                      <td className="py-3.5 px-3 text-right">
                        <div className="flex items-center justify-end space-x-2" onClick={(e) => e.stopPropagation()}>
                          <button
                            onClick={() => setSelectedStudentDetailId(st.id)}
                            className="px-2.5 py-1 bg-[#F3F0FF] hover:bg-[#E9E4FF] text-[#635BFF] rounded-lg font-semibold text-[11px] transition-colors"
                          >
                            Profile
                          </button>
                          <button
                            onClick={() => handleRemoveStudent(st.id, st.name)}
                            className="px-2 py-1 bg-white hover:bg-rose-50 text-rose-600 border border-rose-200 rounded-lg text-[11px] font-semibold transition-colors"
                            title="Remove from class"
                          >
                            <UserX className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
        </ErrorBoundary>
      )}

      {/* ================================================== */}
      {/* TAB 3: COHORT MANAGEMENT & JOIN CODES              */}
      {/* ================================================== */}
      {activeTab === 'management' && (
        <ErrorBoundary fallbackTitle="Cohort Management View Encountered an Error">
        <div className="bg-white border border-[#E2E8F0] rounded-2xl p-6 sm:p-7 shadow-[0_4px_20px_rgba(15,23,42,0.03)] space-y-6 animate-fadeIn">
          <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-100">
            <div>
              <h3 className="text-lg font-bold text-slate-900">Manage Classes & Join Codes</h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Generate secure join codes, disable class enrollment, or create new class cohorts.
              </p>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-3.5 py-1.5 bg-[#635BFF] hover:bg-[#5349e0] text-white rounded-xl text-xs font-semibold flex items-center space-x-1.5 shadow-xs"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Create New Class</span>
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {classes.map((cls) => (
              <div
                key={cls.id}
                className={`p-5 rounded-2xl border transition-all flex flex-col justify-between space-y-4 ${
                  cls.is_active
                    ? 'bg-white border-[#E2E8F0] shadow-xs hover:border-[#635BFF]/40'
                    : 'bg-slate-50/80 border-slate-200 opacity-80'
                }`}
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-bold px-2 py-0.5 rounded-md bg-[#F3F0FF] text-[#635BFF] border border-purple-100">
                      {cls.course_code || 'COURSE'}
                    </span>
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        cls.is_active
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : 'bg-slate-100 text-slate-600 border border-slate-300'
                      }`}
                    >
                      {cls.is_active ? 'Active' : 'Disabled'}
                    </span>
                  </div>

                  <h4 className="font-bold text-slate-900 text-sm">{cls.name}</h4>
                  <p className="text-[11px] text-slate-500 line-clamp-1">{cls.course_title}</p>
                </div>

                <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl flex items-center justify-between">
                  <div>
                    <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">
                      Join Code
                    </span>
                    <span className="font-mono text-base font-extrabold text-slate-900 tracking-wider">
                      {cls.class_code}
                    </span>
                  </div>
                  <button
                    onClick={() => handleCopyCode(cls.class_code)}
                    className="p-2 hover:bg-white rounded-lg border border-transparent hover:border-slate-200 text-slate-600 transition-all flex items-center space-x-1"
                    title="Copy Join Code"
                  >
                    {copiedCode === cls.class_code ? (
                      <span className="text-[11px] font-bold text-emerald-600 flex items-center space-x-1">
                        <Check className="w-3.5 h-3.5" />
                        <span>Copied</span>
                      </span>
                    ) : (
                      <Copy className="w-4 h-4 text-slate-500 hover:text-slate-800" />
                    )}
                  </button>
                </div>

                <div className="flex items-center justify-between text-xs text-slate-600 pt-1 border-t border-slate-100">
                  <div className="flex items-center space-x-1.5">
                    <Users className="w-3.5 h-3.5 text-slate-400" />
                    <span className="font-semibold text-slate-800">{cls.active_students_count}</span>
                    <span className="text-slate-400">students</span>
                  </div>
                  {cls.expires_at && (
                    <div className="flex items-center space-x-1 text-[11px] text-slate-400">
                      <Calendar className="w-3 h-3" />
                      <span>{new Date(cls.expires_at).toLocaleDateString()}</span>
                    </div>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-2 pt-1 border-t border-slate-100">
                  <button
                    onClick={() => handleToggleActive(cls)}
                    disabled={actionLoadingId === cls.id}
                    className={`py-1.5 px-2 rounded-lg border text-[11px] font-semibold flex items-center justify-center space-x-1 transition-colors ${
                      cls.is_active
                        ? 'border-slate-200 text-slate-700 hover:bg-slate-100'
                        : 'border-emerald-200 bg-emerald-50 text-emerald-700 hover:bg-emerald-100'
                    }`}
                  >
                    <Power className="w-3 h-3" />
                    <span>{cls.is_active ? 'Disable' : 'Enable'}</span>
                  </button>

                  <button
                    onClick={() => handleRegenerateCode(cls)}
                    disabled={actionLoadingId === cls.id}
                    className="py-1.5 px-2 rounded-lg border border-slate-200 text-slate-700 hover:bg-slate-100 text-[11px] font-semibold flex items-center justify-center space-x-1 transition-colors"
                  >
                    <RotateCcw className="w-3 h-3" />
                    <span>Regen</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
        </ErrorBoundary>
      )}

      {/* ================================================== */}
      {/* TAB 3: ASSESSMENTS & REASSESSMENTS (Step 2D)       */}
      {/* ================================================== */}
      {activeTab === 'assessments' && selectedClassId && (
        <ErrorBoundary fallbackTitle="Assessment Performance View Encountered an Error">
          <FacultyAssessmentsTab
            classId={selectedClassId}
            onSelectStudent={(sid) => setSelectedStudentDetailId(sid)}
          />
        </ErrorBoundary>
      )}

      {/* ================================================== */}
      {/* TAB 4: LEARNING GAPS (CONCEPTS & PREREQUISITES)     */}
      {/* ================================================== */}
      {activeTab === 'gaps' && selectedClassId && (
        <ErrorBoundary fallbackTitle="Learning Gaps Analysis View Encountered an Error">
          <FacultyLearningGapsTab
            classId={selectedClassId}
            onSelectStudent={(sid) => setSelectedStudentDetailId(sid)}
          />
        </ErrorBoundary>
      )}

      {/* ================================================== */}
      {/* TAB 5: IMPACT & BEFORE/AFTER INTERVENTIONS         */}
      {/* ================================================== */}
      {activeTab === 'impact' && selectedClassId && (
        <ErrorBoundary fallbackTitle="Cohort Impact & Attribution View Encountered an Error">
          <FacultyImpactTab
            classId={selectedClassId}
            onSelectStudent={(sid) => setSelectedStudentDetailId(sid)}
          />
        </ErrorBoundary>
      )}

      {/* ================================================== */}
      {/* CO DRILL-DOWN MODAL (Step 2C Item 8)               */}
      {/* ================================================== */}
      {drilldownOutcomeId && selectedClassId && (
        <CODrilldownModal
          isOpen={true}
          onClose={() => setDrilldownOutcomeId(null)}
          classId={selectedClassId}
          outcomeId={drilldownOutcomeId}
          className={selectedClass?.name || 'Class'}
        />
      )}

      {/* ================================================== */}
      {/* STUDENT DETAIL PROFILE MODAL (Step 2C Item 9)      */}
      {/* ================================================== */}
      {selectedStudentDetailId && selectedClassId && (
        <StudentDetailModal
          isOpen={true}
          onClose={() => setSelectedStudentDetailId(null)}
          classId={selectedClassId}
          studentId={selectedStudentDetailId}
        />
      )}

      {/* ================================================== */}
      {/* MODAL: CREATE CLASS                                */}
      {/* ================================================== */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4 animate-fadeIn">
          <div className="bg-white rounded-2xl shadow-xl border border-slate-200 max-w-md w-full p-6 space-y-5 animate-scaleUp">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="text-base font-bold text-slate-900">Create New Class Cohort</h3>
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setCreateError(null);
                }}
                className="p-1 hover:bg-slate-100 rounded-lg text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateClass} className="space-y-4 text-xs">
              {createError && (
                <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 flex items-start space-x-2">
                  <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                  <span>{createError}</span>
                </div>
              )}

              <div className="space-y-1">
                <label className="font-semibold text-slate-700">Course</label>
                <select
                  value={createCourseId}
                  onChange={(e) => setCreateCourseId(parseInt(e.target.value, 10))}
                  className="w-full px-3 py-2 border border-slate-300 rounded-xl bg-white text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-[#635BFF]/30"
                >
                  <option value={1}>CS101: Python Programming</option>
                  <option value={2}>CS201: Data Structures</option>
                  <option value={3}>AI301: Machine Learning Fundamentals</option>
                  <option value={4}>CS302: Database Management Systems</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-slate-700">Class Cohort Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Section A - Spring 2026"
                  value={createName}
                  onChange={(e) => setCreateName(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-xl text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-[#635BFF]/30"
                />
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-slate-700">
                  Custom Class Code <span className="text-slate-400 font-normal">(Optional)</span>
                </label>
                <input
                  type="text"
                  maxLength={12}
                  placeholder="Leave empty for auto-generated code"
                  value={createCustomCode}
                  onChange={(e) => setCreateCustomCode(e.target.value.toUpperCase())}
                  className="w-full px-3 py-2 border border-slate-300 rounded-xl font-mono text-slate-900 uppercase focus:outline-hidden focus:ring-2 focus:ring-[#635BFF]/30"
                />
                <p className="text-[10px] text-slate-400">
                  Must be 4-12 characters, uppercase letters & digits.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="font-semibold text-slate-700">Max Students</label>
                  <input
                    type="number"
                    min={1}
                    placeholder="Unlimited"
                    value={createMaxStudents}
                    onChange={(e) => setCreateMaxStudents(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-[#635BFF]/30"
                  />
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-slate-700">Expires At</label>
                  <input
                    type="date"
                    value={createExpiresAt}
                    onChange={(e) => setCreateExpiresAt(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-[#635BFF]/30"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-xl font-semibold transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createSubmitting}
                  className="px-4 py-2 bg-[#635BFF] hover:bg-[#5349e0] text-white rounded-xl font-semibold transition-all shadow-xs disabled:opacity-50"
                >
                  {createSubmitting ? 'Creating...' : 'Create Class'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
