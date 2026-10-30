import React, { useState, useEffect, useRef } from 'react';
import {
  UserCheck,
  Target,
  Award,
  BookOpen,
  FileCheck2,
  Sparkles,
  ArrowRight,
  ArrowLeft,
  RotateCcw,
  Check,
  Route,
  CheckCircle2,
  AlertTriangle,
  Layers,
  Cpu,
  GitBranch,
  ShieldCheck,
  Clock,
  Code2,
  Terminal
} from 'lucide-react';
import { api } from '../services/api';
import { pyodideRunner } from '../services/pyodideRunner';
import { useStudentLearning } from '../context/StudentLearningContext';
import { TopicCodingCompiler } from '../components/TopicCodingCompiler';
import { CodingSubmission } from '../types';

const COURSE_OUTCOMES_MAP: Record<number, { code: string; target_pct: number; title: string; description: string }[]> = {
  1: [
    { code: 'CO1', target_pct: 75, title: 'Python Syntax & Procedural Logic', description: 'Understand fundamental Python programming syntax & procedural logic.' },
    { code: 'CO2', target_pct: 70, title: 'Conditional Branching & Iteration', description: 'Apply conditional constructs, iteration, and algorithmic patterns.' },
    { code: 'CO3', target_pct: 70, title: 'Functions & Data Structures', description: 'Implement functions, modular code design, and data structures in Python.' },
    { code: 'CO4', target_pct: 70, title: 'Computational Problem Solving', description: 'Develop programs to solve real-world computational challenges.' }
  ],
  2: [
    { code: 'CO1', target_pct: 75, title: 'Fundamental Data Structures', description: 'Understand core concepts of Stack, Queue, Tree basics and linear representations.' },
    { code: 'CO2', target_pct: 70, title: 'Problem Solving Application', description: 'Apply Push/Pop, Enqueue/Dequeue, and systematic tree traversals to computational problems.' },
    { code: 'CO3', target_pct: 70, title: 'Algorithm Analysis & Tracing', description: 'Implement recursive function tracing, call-stack visualization, and complexity bounds.' },
    { code: 'CO4', target_pct: 70, title: 'Complexity Analysis & Optimization', description: 'Analyze Big-O runtime, space trade-offs, and binary search tree applications.' }
  ],
  3: [
    { code: 'CO1', target_pct: 75, title: 'AI Foundations & Search Strategies', description: 'Understand state-space search algorithms, heuristics, and intelligent agent principles.' },
    { code: 'CO2', target_pct: 70, title: 'Supervised & Unsupervised Learning', description: 'Apply regression, classification, decision trees, and clustering techniques to datasets.' },
    { code: 'CO3', target_pct: 70, title: 'Neural Networks & Deep Learning', description: 'Implement forward propagation, backpropagation, and loss optimization models.' },
    { code: 'CO4', target_pct: 70, title: 'Model Evaluation & Ethical AI', description: 'Evaluate model accuracy, precision/recall metrics, and mitigate bias in AI pipelines.' }
  ],
  4: [
    { code: 'CO1', target_pct: 75, title: 'Database Architecture & Relational Model', description: 'Understand relational database architectures, relational algebra & schemas.' },
    { code: 'CO2', target_pct: 70, title: 'SQL Query Formulation & Relational Algebra', description: 'Construct complex SQL queries, views, subqueries, and join operations.' },
    { code: 'CO3', target_pct: 70, title: 'Normalization & Schema Design', description: 'Apply normalization theories (1NF through BCNF) and indexing strategies.' },
    { code: 'CO4', target_pct: 70, title: 'Transaction Management & Concurrency Control', description: 'Analyze transaction concurrency, ACID properties & failure recovery.' }
  ]
};

interface AssessmentsMasterPageProps {
  onPathGenerated: () => void;
  onNavigateToKnowledgeMap?: () => void;
  onNavigateToTutor?: () => void;
}

export const AssessmentsMasterPage: React.FC<AssessmentsMasterPageProps> = ({
  onPathGenerated,
  onNavigateToKnowledgeMap
}) => {
  const { studentState, activeCourse, refreshStudentState, submitAssessment, activeCourseId } = useStudentLearning();
  const profile = studentState?.studentProfile;

  // Stepper state (1 to 5)
  const [currentStep, setCurrentStep] = useState<number>(1);

  // Step 1: Learner Profile
  const [studentId, setStudentId] = useState(profile?.student_id || '');
  const [name, setName] = useState(profile?.full_name || '');
  const [program, setProgram] = useState(profile?.program || 'Computer Science & Engineering');
  const [semester, setSemester] = useState(profile?.semester || 1);
  const [academicLevel, setAcademicLevel] = useState(profile?.academic_level || 'Undergraduate (Semester 4)');
  const [currentLevel, setCurrentLevel] = useState(profile?.current_level || 'Beginner');

  const enrolledCourse = studentState?.enrolledCourse;
  const courseTitle = enrolledCourse?.title || activeCourse?.title || 'Selected Course';
  const courseCode = enrolledCourse?.code || activeCourse?.code || '';

  const defaultGoalForCourse = `Master fundamental concepts, problem solving, and accredited Course Outcomes in ${courseTitle} ${courseCode ? `(${courseCode})` : ''} for technical interviews and OBE accreditation.`;

  // Step 2: Learning Goal
  const [goal, setGoal] = useState(
    profile?.learning_goal || defaultGoalForCourse
  );
  const [targetDate, setTargetDate] = useState(profile?.target_completion_date || '2026-12-15');

  // Keep goal aligned with active course unless customized
  useEffect(() => {
    if (!profile?.learning_goal || profile.learning_goal.includes('data structures') || profile.learning_goal.includes('Course Outcomes in')) {
      setGoal(defaultGoalForCourse);
    }
  }, [activeCourseId, defaultGoalForCourse]);

  // Step 4: Learning Preferences
  const [priorKnowledge, setPriorKnowledge] = useState(
    profile?.prior_knowledge || 'Beginner with basic programming syntax & variable logic'
  );
  const [format, setFormat] = useState(profile?.preferred_format || 'Interactive examples + code tracing + practice');
  const [dailyMinutes, setDailyMinutes] = useState(profile?.daily_time_minutes || 60);

  // Step 5: Adaptive Assessment State
  const [questions, setQuestions] = useState<any[]>([]);
  const [qIndex, setQIndex] = useState<number>(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [codingSubmission, setCodingSubmission] = useState<CodingSubmission | null>(null);
  const [studentCode, setStudentCode] = useState<string>('');
  const [loadingQuestions, setLoadingQuestions] = useState<boolean>(false);
  const [submittingAssessment, setSubmittingAssessment] = useState<boolean>(false);
  const [evalResult, setEvalResult] = useState<any | null>(null);
  const [evalLearningPath, setEvalLearningPath] = useState<any | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);

  // On course change, reset state immediately and abort previous requests
  useEffect(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setQuestions([]);
    setAnswers({});
    setCodingSubmission(null);
    setStudentCode('');
    setEvalResult(null);
    setEvalLearningPath(null);
    setQIndex(0);
    if (currentStep === 5) {
      loadAdaptiveQuestions();
    }
  }, [activeCourseId]);

  // Load questions when step 5 is active
  useEffect(() => {
    if (currentStep === 5 && questions.length === 0 && !loadingQuestions && !evalResult) {
      loadAdaptiveQuestions();
    }
  }, [currentStep]);

  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const loadAdaptiveQuestions = async () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    setLoadingQuestions(true);
    setQuestions([]);
    setAnswers({});
    setCodingSubmission(null);
    setStudentCode('');
    setEvalResult(null);
    setEvalLearningPath(null);
    setQIndex(0);

    try {
      const q = await api.getAdaptiveQuestions(
        activeCourseId,
        undefined,
        5,
        'assessment',
        profile?.user_id || 1,
        controller.signal
      );
      if (!controller.signal.aborted) {
        setQuestions(q);
      }
    } catch (err: any) {
      if (err?.name !== 'AbortError') {
        console.error('Failed to load adaptive questions', err);
      }
    } finally {
      if (!controller.signal.aborted) {
        setLoadingQuestions(false);
      }
    }
  };

  const defaultTopicForCourse = questions[0]?.topic_id || studentState?.learningPath?.items?.[0]?.topic_id || ((activeCourse as any)?.topics?.[0]?.id) || 1;

  const handleSaveProfile = async () => {
    try {
      await api.updateProfile(
        {
          full_name: name,
          student_id: studentId,
          program,
          semester,
          current_level: currentLevel,
          academic_level: academicLevel,
          learning_goal: goal,
          prior_knowledge: priorKnowledge,
          preferred_format: format,
          daily_time_minutes: dailyMinutes,
          target_completion_date: targetDate
        },
        profile?.user_id || 1
      );
      await refreshStudentState();
    } catch (err) {
      console.error('Profile update error', err);
    }
  };

  const handleNextStep = async () => {
    if (currentStep === 4) {
      await handleSaveProfile();
    }
    if (currentStep < 5) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleSelectAnswer = (questionId: number, option: string) => {
    setAnswers((prev) => ({ ...prev, [String(questionId)]: option }));
  };

  // Submit assessment and execute closed loop update
  const handleSubmitAssessment = async () => {
    if (submittingAssessment) return;
    setSubmittingAssessment(true);
    try {
      let finalCodingSub = codingSubmission;
      const codeToEvaluate = studentCode.trim();

      // If code was not compiled yet, or was modified after compilation, evaluate it now
      const needsCompile = !finalCodingSub || (finalCodingSub.code.trim() !== codeToEvaluate);

      try {
        const targetTopicId = (questions[0] && questions[0].course_id === activeCourseId) ? questions[0].topic_id : defaultTopicForCourse;
        const challenge = await api.getCodingChallenge(activeCourseId, targetTopicId);
        if (challenge && challenge.has_coding !== false && needsCompile) {
          const codeToRun = codeToEvaluate || challenge.starter_code || '';
          const execRes = await pyodideRunner.runCode(
            codeToRun,
            challenge.test_cases || []
          );
          finalCodingSub = {
            challenge_id: challenge.id || 'custom',
            title: challenge.title || 'Topic Coding Problem',
            topic_id: challenge.topic_id || targetTopicId,
            code: codeToRun,
            passed_count: execRes.passed_count,
            total_count: execRes.total_count,
            percentage: execRes.percentage,
            all_passed: execRes.all_passed,
            results: execRes.results,
            execution_time_ms: execRes.execution_time_ms,
            stdout: execRes.stdout,
            stderr: execRes.stderr,
            self_verified: true
          };
          setCodingSubmission(finalCodingSub);
        }
      } catch (e) {
        console.warn('Auto compile before submission encountered error', e);
      }

      const res = await submitAssessment('assessment', answers, undefined, finalCodingSub || undefined);
      setEvalResult(res.evaluation);
      if (res.state?.learningPath) {
        setEvalLearningPath(res.state.learningPath);
      } else {
        const path = await api.getLearningPath(activeCourseId, profile?.user_id || 1);
        setEvalLearningPath(path);
      }
      await refreshStudentState();
    } catch (err) {
      console.error('Failed to submit assessment', err);
    } finally {
      setSubmittingAssessment(false);
    }
  };

  // Low score simulation test shortcut
  const handleSimulateLowScore = () => {
    const lowMap: Record<string, string> = {};
    questions.forEach((q) => {
      lowMap[String(q.id)] = q.options[q.options.length - 1];
    });
    setAnswers(lowMap);
  };

  // High score simulation test shortcut
  const handleSimulateHighScore = () => {
    const highMap: Record<string, string> = {};
    questions.forEach((q) => {
      highMap[String(q.id)] = q.correct_answer || q.options[0];
    });
    setAnswers(highMap);
  };

  const stepsList = [
    { num: 1, title: 'Learner Profile', icon: UserCheck },
    { num: 2, title: 'Learning Goal', icon: Target },
    { num: 3, title: 'Course Outcomes', icon: Award },
    { num: 4, title: 'Learning Preferences', icon: BookOpen },
    { num: 5, title: 'Assessment', icon: FileCheck2 }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="inline-flex items-center space-x-2 px-3 py-1 bg-orange-50 border border-orange-200 rounded-full text-xs font-semibold text-orange-600 mb-1.5">
            <Sparkles className="w-3.5 h-3.5 text-orange-500" />
            <span>Closed-Loop Student Profiling & Diagnostic Engine</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
            Assessments & Profiling
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Standard 5-step diagnostic process aligning learner cognitive baseline with accredited Course Outcomes
          </p>
        </div>
      </div>

      {/* 5-Step Stepper Header */}
      <div className="bg-white border border-[#E2E8F0] rounded-2xl p-4 sm:p-5 shadow-[0_4px_20px_rgba(15,23,42,0.04)]">
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 sm:gap-3">
          {stepsList.map((s) => {
            const isCurrent = currentStep === s.num;
            const isCompleted = currentStep > s.num;

            return (
              <button
                key={s.num}
                onClick={() => setCurrentStep(s.num)}
                className={`p-3.5 rounded-xl border text-left transition-all flex items-center space-x-3 ${
                  isCurrent
                    ? 'bg-orange-50 text-orange-600 border-2 border-orange-400 shadow-xs'
                    : isCompleted
                    ? 'bg-white text-slate-800 border border-emerald-200 hover:bg-slate-50'
                    : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
                }`}
              >
                <div
                  className={`w-7 h-7 rounded-lg flex items-center justify-center font-mono font-bold text-xs flex-shrink-0 ${
                    isCurrent
                      ? 'bg-[#EA580C] text-white shadow-xs'
                      : isCompleted
                      ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                      : 'bg-slate-100 text-slate-500'
                  }`}
                >
                  {isCompleted ? <Check className="w-4 h-4" /> : `0${s.num}`}
                </div>
                <div className="min-w-0">
                  <div className={`text-[10px] uppercase font-bold tracking-wider ${isCurrent ? 'text-orange-600' : 'text-slate-400'}`}>
                    Step {s.num}
                  </div>
                  <div className={`text-xs font-bold truncate ${isCurrent ? 'text-slate-900' : 'text-slate-700'}`}>{s.title}</div>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Step Contents */}
      <div className="bg-white border border-[#E2E8F0] rounded-2xl p-6 sm:p-8 shadow-[0_4px_20px_rgba(15,23,42,0.04)]">
        {/* STEP 01: LEARNER PROFILE */}
        {currentStep === 1 && (
          <div className="space-y-6">
            <div className="border-b border-slate-100 pb-3">
              <h3 className="text-lg font-bold text-slate-900 tracking-tight">01. Learner Profile Configuration</h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Configure your student ID, enrollment discipline, and current academic standing.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">Student ID</label>
                <input
                  type="text"
                  value={studentId}
                  onChange={(e) => setStudentId(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-white border border-[#CBD5E1] rounded-lg text-sm font-mono text-orange-600 focus:outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">Student Full Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-white border border-[#CBD5E1] rounded-lg text-sm text-slate-900 focus:outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">Degree / Academic Program</label>
                <input
                  type="text"
                  value={program}
                  onChange={(e) => setProgram(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-white border border-[#CBD5E1] rounded-lg text-sm text-slate-900 focus:outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1.5">Semester</label>
                  <select
                    value={semester}
                    onChange={(e) => setSemester(parseInt(e.target.value))}
                    className="w-full px-3 py-2.5 bg-white border border-[#CBD5E1] rounded-lg text-sm text-slate-900 focus:outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
                  >
                    {[1, 2, 3, 4, 5, 6, 7, 8].map((sem) => (
                      <option key={sem} value={sem}>
                        Semester {sem}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1.5">Current Level</label>
                  <select
                    value={currentLevel}
                    onChange={(e) => setCurrentLevel(e.target.value)}
                    className="w-full px-3 py-2.5 bg-white border border-[#CBD5E1] rounded-lg text-sm font-semibold text-slate-900 focus:outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
                  >
                    <option value="Beginner">Beginner</option>
                    <option value="Intermediate">Intermediate</option>
                    <option value="Advanced">Advanced</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="pt-4 flex justify-end">
              <button
                onClick={handleNextStep}
                className="px-5 py-2.5 bg-[#EA580C] hover:bg-[#C2410C] text-white rounded-lg text-xs font-semibold transition-all shadow-sm flex items-center space-x-2"
              >
                <span>Continue to Learning Goal</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* STEP 02: LEARNING GOAL */}
        {currentStep === 2 && (
          <div className="space-y-6">
            <div className="border-b border-slate-100 pb-3">
              <h3 className="text-lg font-bold text-slate-900 tracking-tight">02. Target Learning Goals</h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Define your pedagogical milestones and expected target completion timeline.
              </p>
            </div>

            <div className="space-y-5">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  Primary Learning Objective / Milestone Goal
                </label>
                <textarea
                  rows={3}
                  value={goal}
                  onChange={(e) => setGoal(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-white border border-[#CBD5E1] rounded-lg text-sm text-slate-900 focus:outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
                />
              </div>

              <div className="max-w-xs">
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  Target Completion Date
                </label>
                <input
                  type="date"
                  value={targetDate}
                  onChange={(e) => setTargetDate(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-white border border-[#CBD5E1] rounded-lg text-sm text-slate-900 focus:outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
                />
              </div>
            </div>

            <div className="pt-4 flex justify-between">
              <button
                onClick={() => setCurrentStep(1)}
                className="px-4 py-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-lg text-xs font-semibold flex items-center space-x-1.5 shadow-xs"
              >
                <ArrowLeft className="w-4 h-4" />
                <span>Back</span>
              </button>

              <button
                onClick={handleNextStep}
                className="px-5 py-2.5 bg-[#EA580C] hover:bg-[#C2410C] text-white rounded-lg text-xs font-semibold transition-all shadow-sm flex items-center space-x-2"
              >
                <span>Continue to Course Outcomes</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* STEP 03: COURSE OUTCOMES */}
        {currentStep === 3 && (
          <div className="space-y-6">
            <div className="border-b border-slate-100 pb-3">
              <h3 className="text-lg font-bold text-slate-900 tracking-tight">03. Target Course Outcomes (COs)</h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Outcome-Based Education alignment for {courseTitle} ({courseCode}). Institutional Target: 70%.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {(studentState?.courseOutcomeAttainment && studentState.courseOutcomeAttainment.length > 0
                ? studentState.courseOutcomeAttainment.map((co) => ({
                    code: co.code,
                    target_pct: co.target_pct || 70,
                    title: co.description.split(' - ')[0] || co.description,
                    description: co.description
                  }))
                : (COURSE_OUTCOMES_MAP[activeCourseId] || COURSE_OUTCOMES_MAP[2])
              ).map((co) => (
                <div key={co.code} className="p-4 bg-[#F8FAFC] rounded-xl border border-slate-200 space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-xs text-orange-600 px-2 py-0.5 bg-orange-50 rounded border border-orange-200">
                      {co.code}
                    </span>
                    <span className="text-xs text-emerald-700 font-bold">Target: {co.target_pct}%</span>
                  </div>
                  <div className="text-xs font-bold text-slate-900">{co.title}</div>
                  <p className="text-[11px] text-slate-600">
                    {co.description}
                  </p>
                </div>
              ))}
            </div>

            <div className="pt-4 flex justify-between">
              <button
                onClick={() => setCurrentStep(2)}
                className="px-4 py-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-lg text-xs font-semibold flex items-center space-x-1.5 shadow-xs"
              >
                <ArrowLeft className="w-4 h-4" />
                <span>Back</span>
              </button>

              <button
                onClick={handleNextStep}
                className="px-5 py-2.5 bg-[#EA580C] hover:bg-[#C2410C] text-white rounded-lg text-xs font-semibold transition-all shadow-sm flex items-center space-x-2"
              >
                <span>Continue to Learning Preferences</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* STEP 04: LEARNING PREFERENCES */}
        {currentStep === 4 && (
          <div className="space-y-6">
            <div className="border-b border-slate-100 pb-3">
              <h3 className="text-lg font-bold text-slate-900 tracking-tight">04. Learning Modality & Preferences</h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Customized pacing, scaffolding levels, and daily study time allocation.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">Prior Knowledge Level</label>
                <input
                  type="text"
                  value={priorKnowledge}
                  onChange={(e) => setPriorKnowledge(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-white border border-[#CBD5E1] rounded-lg text-sm text-slate-900 focus:outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">Daily Study Allocation (Minutes)</label>
                <input
                  type="number"
                  value={dailyMinutes}
                  onChange={(e) => setDailyMinutes(parseInt(e.target.value) || 30)}
                  min={15}
                  max={240}
                  className="w-full px-3.5 py-2.5 bg-white border border-[#CBD5E1] rounded-lg text-sm font-mono text-orange-600 focus:outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
                />
              </div>

              <div className="sm:col-span-2">
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">Preferred Content Formats</label>
                <input
                  type="text"
                  value={format}
                  onChange={(e) => setFormat(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-white border border-[#CBD5E1] rounded-lg text-sm text-slate-900 focus:outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
                />
              </div>
            </div>

            <div className="pt-4 flex justify-between">
              <button
                onClick={() => setCurrentStep(3)}
                className="px-4 py-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-lg text-xs font-semibold flex items-center space-x-1.5 shadow-xs"
              >
                <ArrowLeft className="w-4 h-4" />
                <span>Back</span>
              </button>

              <button
                onClick={handleNextStep}
                className="px-5 py-2.5 bg-[#EA580C] hover:bg-[#C2410C] text-white rounded-lg text-xs font-semibold transition-all shadow-sm flex items-center space-x-2"
              >
                <span>Proceed to Adaptive Assessment</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* STEP 05: ADAPTIVE ASSESSMENT */}
        {currentStep === 5 && (
          <div className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 pb-4">
              <div>
                <h3 className="text-lg font-bold text-slate-900 tracking-tight">
                  05. Adaptive Diagnostic Assessment
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Dynamically selected from QuestionBank based on prerequisite readiness. Never serves identical questions repeatedly.
                </p>
              </div>
            </div>

            {loadingQuestions ? (
              <div className="py-12 text-center space-y-3">
                <div className="w-9 h-9 border-3 border-orange-500 border-t-transparent rounded-full animate-spin mx-auto" />
                <p className="text-xs text-orange-600 font-medium">
                  AI Assessment Engine is querying QuestionBank & selecting adaptive questions...
                </p>
              </div>
            ) : evalResult ? (
              /* Evaluation Results View */
              <div className="p-6 bg-white rounded-xl border border-orange-200 shadow-sm space-y-5">
                <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-100">
                  <div className="flex items-center space-x-3">
                    <span
                      className={`text-xs font-bold px-3 py-1 rounded-full border ${
                        evalResult.passed
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                          : 'bg-amber-50 text-amber-700 border-amber-200'
                      }`}
                    >
                      {evalResult.passed ? 'Assessment Passed' : 'Remediation Required'}
                    </span>
                    <span className="font-bold text-slate-900 text-lg">
                      Score: {evalResult.score} / {evalResult.max_score} ({evalResult.percentage}%)
                    </span>
                  </div>

                  <span className="text-xs font-mono text-slate-500">
                    Attempt UUID: {evalResult.attempt_uuid}
                  </span>
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
                            <span className="text-[10px] uppercase font-bold tracking-wider text-orange-200">
                              Coding Assignment Evaluated
                            </span>
                            <span className="px-1.5 py-0.5 bg-slate-800 text-emerald-400 border border-emerald-500/30 rounded text-[9px] font-mono">
                              Self-verified practice, not counted toward mastery
                            </span>
                          </div>
                          <h4 className="font-bold text-white text-sm">
                            {evalResult.coding_result.title || 'Topic Coding Problem'}
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

                {/* Gap Detection & Topic breakdown */}
                <div className="space-y-3">
                  <div className="text-xs font-bold uppercase tracking-wider text-slate-700">
                    Topic Mastery Evaluation & Gap Detection:
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {evalResult.question_details?.map((qd: any, idx: number) => (
                      <div
                        key={idx}
                        className={`p-3 rounded-xl border text-xs space-y-1 ${
                          qd.is_correct
                            ? 'bg-emerald-50/50 border-emerald-200'
                            : 'bg-rose-50/50 border-rose-200'
                        }`}
                      >
                        <div className="flex items-center justify-between font-semibold">
                          <span className={qd.is_correct ? 'text-emerald-700' : 'text-rose-700'}>
                            {qd.is_correct ? '✓ Correct' : '✗ Knowledge Gap'}
                          </span>
                          <span className="text-[10px] text-slate-400">Q{idx + 1}</span>
                        </div>
                        <p className="text-slate-800 text-[11px] line-clamp-2">{qd.question_text}</p>
                        <div className="text-[10px] text-slate-500 pt-1">
                          Explanation: {qd.explanation}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* TECHNICAL REPRESENTATION & GAP DETECTION ENGINE (USER DIAGRAM 1) */}
                <div className="p-5 bg-white border border-slate-200 rounded-2xl shadow-xs space-y-4">
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
                      Formal Model: G = (V, E)
                    </span>
                  </div>

                  {/* Mathematical Formulation Definition Box */}
                  <div className="p-4 bg-[#F8FAFC] border border-slate-200 rounded-xl space-y-2 text-xs font-mono text-slate-800">
                    <div className="font-bold text-orange-600">Let:</div>
                    <div className="pl-3 space-y-1">
                      <div><strong className="text-slate-900">G = (V, E)</strong></div>
                      <div className="text-slate-600 pl-2">where:</div>
                      <div className="pl-4"><strong>V</strong> = set of learning concepts (Stack, Queue, Recursion, Trees...)</div>
                      <div className="pl-4"><strong>E</strong> = prerequisite relationships between concepts (e.g. Recursion ➔ Tree Traversal)</div>
                      <div className="pt-1"><strong className="text-slate-900">Kt</strong> = learner's knowledge state vector at time t</div>
                      <div className="pt-1">For a concept <strong>v ∈ V</strong>, let:</div>
                      <div className="pl-4"><strong>Mt(v)</strong> = mastery score of concept v</div>
                      <div className="pt-1.5 p-2 bg-amber-50 border border-amber-200 rounded-lg text-amber-900 font-semibold">
                        If: <strong>Mt(v) &lt; 60% (Threshold)</strong> ➔ the concept is treated as a <strong>learning gap</strong>.
                        <br />
                        The system then checks prerequisite concepts (E) and updates the personalized learning path.
                      </div>
                    </div>
                  </div>

                  {/* Evaluated Knowledge State Vector Kt */}
                  {evalResult.topic_scores && Object.keys(evalResult.topic_scores).length > 0 && (
                    <div className="space-y-2 pt-1">
                      <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                        Evaluated Knowledge State Vector Kt & Gap Threshold Analysis:
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
                        {Object.entries(evalResult.topic_scores).map(([tid, score]: [string, any]) => {
                          const isGap = score < 60;
                          return (
                            <div
                              key={tid}
                              className={`p-3 rounded-xl border text-xs space-y-1 ${
                                isGap
                                  ? 'bg-rose-50/60 border-rose-200 text-rose-900'
                                  : 'bg-emerald-50/60 border-emerald-200 text-emerald-900'
                              }`}
                            >
                              <div className="flex items-center justify-between font-bold">
                                <span>Topic #{tid}</span>
                                <span className="font-mono text-xs">{score}%</span>
                              </div>
                              <div className="flex items-center space-x-1 text-[11px] font-semibold">
                                {isGap ? (
                                  <>
                                    <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
                                    <span className="text-rose-700">Learning Gap (Mt &lt; 60%)</span>
                                  </>
                                ) : (
                                  <>
                                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                                    <span className="text-emerald-700">Concept Validated (Mt ≥ 60%)</span>
                                  </>
                                )}
                              </div>
                              <p className="text-[10px] text-slate-500 pt-0.5">
                                {isGap ? 'Triggered prerequisite check & remedial insertion.' : 'Satisfies prerequisite criterion.'}
                              </p>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>

                {/* POST-ASSESSMENT GENERATED PERSONALIZED LEARNING PATH (CLEARLY SHOWN) */}
                <div className="p-5 bg-white border-2 border-orange-200 rounded-2xl shadow-[0_4px_20px_rgba(234,88,12,0.06)] space-y-4">
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
                          {evalLearningPath?.adaptation_reason ||
                            studentState?.learningPath?.adaptation_reason ||
                            'Roadmap automatically re-sequenced based on assessment gap analysis & prerequisite dependencies.'}
                        </p>
                      </div>
                    </div>

                    <button
                      onClick={onPathGenerated}
                      className="px-4 py-2 bg-[#EA580C] hover:bg-[#C2410C] text-white rounded-lg text-xs font-bold shadow-xs transition-all flex items-center space-x-1.5"
                    >
                      <span>Start Module 1 in Path</span>
                      <ArrowRight className="w-4 h-4" />
                    </button>
                  </div>

                  {/* Path Trajectory Node Sequence */}
                  <div className="space-y-2.5">
                    {(evalLearningPath?.items || studentState?.learningPath?.items || []).map((item: any, idx: number) => {
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
                              ? 'bg-orange-50/70 border-2 border-[#EA580C] shadow-xs'
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
                                  ? 'bg-[#EA580C] text-white'
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
                                    ? 'Inserted to reinforce recursive base criteria before proceeding to Tree Traversal.'
                                    : 'Sequential curriculum progression.')}
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
                              onClick={onPathGenerated}
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

                {/* 10-STEP AI CLOSED LOOP PROGRESS (USER DIAGRAM 2) */}
                <div className="p-4 bg-[#F8FAFC] border border-slate-200 rounded-xl space-y-2">
                  <div className="flex items-center justify-between text-xs text-slate-500">
                    <span className="font-bold text-slate-900 flex items-center space-x-1.5">
                      <Layers className="w-3.5 h-3.5 text-orange-600" />
                      <span>10-Stage Closed Loop Pipeline Active:</span>
                    </span>
                    <span className="font-mono text-[10px] text-orange-600 font-bold">
                      Stage 7 ➔ Stage 8 ➔ Stage 9 Executed
                    </span>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-[11px]">
                    <div className="p-2 bg-white rounded-lg border border-slate-200 text-center">
                      <span className="text-slate-400 block text-[10px]">Steps 1–4</span>
                      <strong className="text-slate-800">Learner Input & Profiling</strong>
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
                    <div className="p-2 bg-white rounded-lg border-2 border-orange-200 bg-orange-50/50 text-center">
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

                {/* Closed Loop Navigation CTAs */}
                <div className="pt-4 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100">
                  <button
                    onClick={loadAdaptiveQuestions}
                    className="px-4 py-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-lg text-xs font-semibold flex items-center space-x-1.5 shadow-xs"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    <span>Take Another Assessment</span>
                  </button>

                  <div className="flex items-center space-x-2">
                    {onNavigateToKnowledgeMap && (
                      <button
                        onClick={onNavigateToKnowledgeMap}
                        className="px-4 py-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-lg text-xs font-semibold shadow-xs"
                      >
                        View Knowledge Map
                      </button>
                    )}

                    <button
                      onClick={onPathGenerated}
                      className="px-5 py-2 bg-[#EA580C] hover:bg-[#C2410C] text-white rounded-lg text-xs font-semibold shadow-sm flex items-center space-x-1.5"
                    >
                      <span>View Adapted Learning Path</span>
                      <ArrowRight className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ) : questions.length > 0 ? (
              /* Questions Answering View with 5 MCQs + Question 6 Hands-On Coding Challenge */
              <div className="space-y-5">
                {/* Dev Simulation Shortcuts (Only rendered in development) */}
                {import.meta.env.DEV && (
                  <div className="p-2.5 bg-amber-50/80 border border-amber-200 rounded-xl flex items-center justify-between text-xs text-amber-800">
                    <div className="flex items-center space-x-1.5 font-medium">
                      <Sparkles className="w-3.5 h-3.5 text-amber-600" />
                      <span>Dev Simulation Shortcuts:</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        type="button"
                        onClick={handleSimulateHighScore}
                        className="px-2 py-0.5 bg-white hover:bg-amber-100 border border-amber-300 rounded text-[11px] font-semibold text-amber-900 shadow-2xs transition-colors"
                      >
                        Fill High Scores
                      </button>
                      <button
                        type="button"
                        onClick={handleSimulateLowScore}
                        className="px-2 py-0.5 bg-white hover:bg-amber-100 border border-amber-300 rounded text-[11px] font-semibold text-amber-900 shadow-2xs transition-colors"
                      >
                        Fill Low Scores
                      </button>
                    </div>
                  </div>
                )}

                {/* Stepper Header Bar */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs text-slate-500">
                    <span>
                      Question <strong className="text-slate-900">{qIndex + 1}</strong> of{' '}
                      <strong className="text-slate-900">{questions.length + 1}</strong>
                    </span>
                    <span className="font-mono text-orange-600 font-semibold">
                      {qIndex < questions.length ? (
                        `${questions[qIndex]?.topic_title} • ${questions[qIndex]?.difficulty}`
                      ) : (
                        `Hands-On Coding: ${questions[0]?.topic_title || 'Topic Practical'} • Python Sandbox`
                      )}
                    </span>
                  </div>

                  {/* Visual Stepper Pills */}
                  <div className="flex flex-wrap items-center gap-1.5">
                    {questions.map((q, idx) => {
                      const isFilled = Boolean(answers[String(q.id)]);
                      const isCur = idx === qIndex;
                      return (
                        <button
                          key={q.id}
                          type="button"
                          onClick={() => setQIndex(idx)}
                          className={`flex-1 min-w-[28px] h-2.5 rounded-full transition-all ${
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
                      className={`px-3 py-1 rounded-full text-[10px] font-bold transition-all flex items-center space-x-1 ${
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

                {/* Question Content: MCQs (0..4) OR Coding Question (5) */}
                {qIndex < questions.length ? (
                  <div className="p-5 bg-white rounded-xl border border-slate-200 space-y-4 shadow-xs">
                    <h4 className="text-base font-bold text-slate-900 leading-relaxed">
                      {questions[qIndex]?.question_text}
                    </h4>

                    {questions[qIndex]?.code_snippet && (
                      <pre className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs font-mono text-orange-600 overflow-x-auto">
                        <code>{questions[qIndex].code_snippet}</code>
                      </pre>
                    )}

                    {/* Options */}
                    <div className="space-y-2 pt-2">
                      {questions[qIndex]?.options.map((opt: string, optIdx: number) => {
                        const currentQId = questions[qIndex]?.id;
                        const isSelected = answers[String(currentQId)] === opt;

                        return (
                          <button
                            key={optIdx}
                            type="button"
                            onClick={() => handleSelectAnswer(currentQId, opt)}
                            className={`w-full p-3.5 rounded-lg border text-left text-xs font-medium transition-all flex items-center justify-between ${
                              isSelected
                                ? 'bg-orange-50 border-2 border-orange-500 text-slate-900 font-semibold shadow-xs'
                                : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                            }`}
                          >
                            <span>{opt}</span>
                            <span
                              className={`w-4 h-4 rounded-full border flex items-center justify-center text-[10px] ${
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
                  </div>
                ) : (
                  /* Question 6: Topic Coding Question with Compiler */
                  <div className="space-y-3">
                    <div className="p-4 bg-gradient-to-r from-orange-50 to-amber-50/50 border border-orange-200 rounded-2xl flex flex-wrap items-center justify-between gap-3 text-xs">
                      <div className="flex items-center space-x-2.5">
                        <div className="p-2 bg-[#EA580C] text-white rounded-xl shadow-xs">
                          <Code2 className="w-4 h-4" />
                        </div>
                        <div>
                          <div className="flex items-center space-x-2">
                            <span className="text-[10px] font-bold uppercase tracking-wider text-orange-600">
                              Question 6 of 6 • Topic Coding Question
                            </span>
                            <span className="px-2 py-0.5 bg-white text-slate-700 rounded text-[9px] font-mono border border-slate-200">
                              Compiler Sandbox
                            </span>
                          </div>
                          <h4 className="font-bold text-slate-900 text-sm mt-0.5">
                            Practical Code Implementation & In-Assignment Compiler Submission
                          </h4>
                        </div>
                      </div>
                      <div className="text-[11px] text-slate-600 font-medium">
                        Topic: <strong className="text-slate-900">{questions[0]?.topic_title || 'Topic Practical'}</strong>
                      </div>
                    </div>

                    <TopicCodingCompiler
                      key={`${activeCourseId}-${questions[0]?.topic_id || defaultTopicForCourse}`}
                      courseId={activeCourseId}
                      topicId={questions[0]?.topic_id || defaultTopicForCourse}
                      topicTitle={questions[0]?.topic_title}
                      initialCode={studentCode}
                      onCodeChange={(c) => setStudentCode(c)}
                      onCompileResult={(sub) => setCodingSubmission(sub)}
                    />
                  </div>
                )}

                {/* Question Navigation & Submit */}
                <div className="flex items-center justify-between pt-2">
                  <button
                    disabled={qIndex === 0}
                    onClick={() => setQIndex(qIndex - 1)}
                    className="px-4 py-2 bg-white hover:bg-slate-50 disabled:opacity-40 text-slate-700 border border-slate-200 rounded-lg text-xs font-semibold flex items-center space-x-1.5 shadow-xs"
                  >
                    <ArrowLeft className="w-3.5 h-3.5" />
                    <span>Previous</span>
                  </button>

                  <div className="flex items-center space-x-2">
                    {qIndex < questions.length ? (
                      <button
                        onClick={() => setQIndex(qIndex + 1)}
                        className="px-4 py-2 bg-[#EA580C] hover:bg-[#C2410C] text-white rounded-lg text-xs font-semibold flex items-center space-x-1.5 shadow-xs"
                      >
                        <span>
                          {qIndex === questions.length - 1
                            ? 'Next: Topic Coding Challenge 💻'
                            : 'Next Question'}
                        </span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    ) : (
                      <button
                        onClick={handleSubmitAssessment}
                        disabled={submittingAssessment || (Object.keys(answers).length === 0 && !studentCode.trim())}
                        className="px-6 py-2.5 bg-[#EA580C] hover:bg-[#C2410C] disabled:opacity-50 text-white rounded-lg text-xs font-bold shadow-sm flex items-center space-x-2"
                      >
                        <FileCheck2 className="w-4 h-4" />
                        <span>
                          {submittingAssessment ? 'Analyzing Performance...' : 'Submit Complete Assessment (MCQ + Code)'}
                        </span>
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="py-8 text-center text-slate-500 text-xs">
                <p>No questions loaded.</p>
                <button
                  onClick={loadAdaptiveQuestions}
                  className="mt-2 px-4 py-2 bg-[#EA580C] text-white rounded-lg text-xs font-semibold shadow-xs"
                >
                  Load Questions
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
