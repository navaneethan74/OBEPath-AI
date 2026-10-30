import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  ArrowRight,
  ArrowLeft,
  User as UserIcon,
  BookOpen,
  GraduationCap,
  Building,
  Calendar,
  CheckCircle2,
  AlertCircle,
  Brain,
  Check,
  Zap,
  Sprout,
  Rocket
} from 'lucide-react';
import { api } from '../services/api';
import { Course, User } from '../types';

export interface OnboardingData {
  fullName: string;
  department: string;
  year: string;
  selectedCourseId: number;
  selectedCourseTitle?: string;
  selectedCourseCode?: string;
  experienceOption: string;
  currentLevel: 'Beginner' | 'Intermediate' | 'Advanced';
}

interface StudentOnboardingWizardProps {
  currentUser: User;
  onComplete: (data: OnboardingData) => void;
  onSkipToDashboard?: () => void;
}

export const StudentOnboardingWizard: React.FC<StudentOnboardingWizardProps> = ({
  currentUser,
  onComplete
}) => {
  // Load draft from localStorage if available (Handles Case 3: Page refresh during onboarding)
  const savedDraft = (() => {
    try {
      const saved = localStorage.getItem('obepath_onboarding_draft');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  })();

  const [step, setStep] = useState<number>(savedDraft?.step || 1);
  const [courses, setCourses] = useState<Course[]>([]);
  const [loadingCourses, setLoadingCourses] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // STEP 1 Fields: Student Profile
  const [fullName, setFullName] = useState<string>(
    savedDraft?.fullName || currentUser.full_name || ''
  );
  const [department, setDepartment] = useState<string>(
    savedDraft?.department || 'CSE'
  );
  const [year, setYear] = useState<string>(
    savedDraft?.year || '2nd Year'
  );

  // STEP 2 Fields: Learning Experience
  const [experienceOption, setExperienceOption] = useState<string>(
    savedDraft?.experienceOption || ''
  );

  // STEP 3 Fields: Course Selection
  const [selectedCourseId, setSelectedCourseId] = useState<number | null>(
    savedDraft?.selectedCourseId || null
  );

  // Load available courses on mount
  useEffect(() => {
    loadCourses();
  }, []);

  // Save progress draft to localStorage on any change (preserves state on refresh)
  useEffect(() => {
    const draft = {
      step,
      fullName,
      department,
      year,
      experienceOption,
      selectedCourseId
    };
    localStorage.setItem('obepath_onboarding_draft', JSON.stringify(draft));
  }, [step, fullName, department, year, experienceOption, selectedCourseId]);

  const loadCourses = async () => {
    try {
      const data = await api.getCourses();
      setCourses(data);
      // If no course selected yet, default to first active course
      if (!selectedCourseId && data.length > 0) {
        setSelectedCourseId(data[0].id);
      }
    } catch (err) {
      console.error('Failed to load courses', err);
    } finally {
      setLoadingCourses(false);
    }
  };

  // Learning experience options (4 single-select options as specified)
  const experienceOptions = [
    {
      id: "I'm completely new",
      level: 'Beginner' as const,
      title: "I'm completely new",
      desc: 'Starting from scratch. We will build concepts from intuitive fundamentals.',
      badge: 'Beginner',
      icon: Sprout
    },
    {
      id: 'I know the basics',
      level: 'Intermediate' as const,
      title: 'I know the basics',
      desc: 'Familiar with core concepts and syntax. Ready for standard problem solving.',
      badge: 'Intermediate',
      icon: Zap
    },
    {
      id: "I've studied it before",
      level: 'Intermediate' as const,
      title: "I've studied it before",
      desc: 'Covered the syllabus previously. Looking to refresh and fill knowledge gaps.',
      badge: 'Refresher',
      icon: BookOpen
    },
    {
      id: "I'm confident",
      level: 'Advanced' as const,
      title: "I'm confident",
      desc: 'Strong foundation. Ready for complex challenge problems and outcome mastery.',
      badge: 'Advanced',
      icon: Rocket
    }
  ];

  // Quick department choices
  const departmentOptions = ['CSE', 'AI & DS', 'IT', 'ECE', 'EEE', 'Mechanical'];

  // Year choices
  const yearOptions = ['1st Year', '2nd Year', '3rd Year', '4th Year'];

  // Validation for Step 1
  const validateStep1 = (): boolean => {
    if (!fullName.trim()) {
      setErrorMsg('Please enter your name.');
      return false;
    }
    if (!department.trim()) {
      setErrorMsg('Please select your department.');
      return false;
    }
    if (!year.trim()) {
      setErrorMsg('Please select your year.');
      return false;
    }
    setErrorMsg(null);
    return true;
  };

  // Validation for Step 2
  const validateStep2 = (): boolean => {
    if (!experienceOption) {
      setErrorMsg('Please select your current experience level.');
      return false;
    }
    setErrorMsg(null);
    return true;
  };

  // Validation for Step 3
  const validateStep3 = (): boolean => {
    if (!selectedCourseId) {
      setErrorMsg('Please select a course.');
      return false;
    }
    setErrorMsg(null);
    return true;
  };

  const handleNextFromStep1 = () => {
    if (validateStep1()) {
      setStep(2);
    }
  };

  const handleNextFromStep2 = () => {
    if (validateStep2()) {
      setStep(3);
    }
  };

  const handleFinishOnboarding = async () => {
    if (!validateStep3()) return;

    setSaving(true);
    setErrorMsg(null);

    const selectedExp = experienceOptions.find((o) => o.id === experienceOption);
    const mappedLevel = selectedExp ? selectedExp.level : 'Intermediate';
    const selectedCourseObj = courses.find((c) => c.id === selectedCourseId);

    // Map year string to academic semester number (e.g., 2nd Year -> 4)
    let semesterNumber = 4;
    if (year.includes('1st')) semesterNumber = 2;
    else if (year.includes('2nd')) semesterNumber = 4;
    else if (year.includes('3rd')) semesterNumber = 6;
    else if (year.includes('4th')) semesterNumber = 8;

    const finalData: OnboardingData = {
      fullName: fullName.trim(),
      department: department.trim(),
      year: year.trim(),
      selectedCourseId: selectedCourseId as number,
      selectedCourseTitle: selectedCourseObj?.title || courses[0]?.title || 'Selected Course',
      selectedCourseCode: selectedCourseObj?.code || courses[0]?.code || '',
      experienceOption,
      currentLevel: mappedLevel
    };

    try {
      // 1. Persist to existing backend student profile
      await api.updateProfile(
        {
          full_name: finalData.fullName,
          department: finalData.department,
          semester: semesterNumber,
          academic_level: `${finalData.year} Undergraduate`,
          selected_course_id: finalData.selectedCourseId,
          current_level: finalData.currentLevel,
          prior_knowledge: finalData.experienceOption,
          learning_goal: `Master ${finalData.selectedCourseTitle} through Outcome-Based Education`,
          onboarding_completed: true
        },
        currentUser.id
      );

      // 2. Persist in localStorage for session consistency
      localStorage.setItem('obepath_onboarding_completed', 'true');
      localStorage.setItem('obepath_onboarding_data', JSON.stringify(finalData));
      localStorage.removeItem('obepath_onboarding_draft');

      // 3. Navigate to existing AI Skill Check
      onComplete(finalData);
    } catch (err: any) {
      console.error('Failed to update student profile', err);
      // Still allow continuation with local state
      localStorage.setItem('obepath_onboarding_completed', 'true');
      localStorage.setItem('obepath_onboarding_data', JSON.stringify(finalData));
      localStorage.removeItem('obepath_onboarding_draft');
      onComplete(finalData);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#FAF8F5] text-slate-900 flex flex-col justify-between selection:bg-orange-100 selection:text-orange-900 font-sans p-4 sm:p-6 lg:p-8">
      {/* ================================================================= */}
      {/* TOP HEADER: BRAND LOGO                                            */}
      {/* ================================================================= */}
      <header className="max-w-2xl mx-auto w-full flex items-center justify-between pb-4 sm:pb-6 border-b border-slate-200">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-2xl bg-orange-600 flex items-center justify-center text-white shadow-md shadow-orange-500/20">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-extrabold text-slate-900 tracking-tight leading-none">
              OBEPath <span className="text-orange-600">AI</span>
            </h1>
            <p className="text-[11px] text-slate-500 font-medium mt-0.5">
              Personalized Student Onboarding
            </p>
          </div>
        </div>

        {/* Step Indicator: 1 of 3, 2 of 3, 3 of 3 */}
        <div className="flex items-center space-x-2">
          <span className="text-xs font-bold text-slate-700 font-mono bg-white px-3 py-1 rounded-full border border-slate-200 shadow-2xs">
            Step <span className="text-orange-600">{step}</span> of 3
          </span>
        </div>
      </header>

      {/* ================================================================= */}
      {/* MAIN ONBOARDING CARD                                              */}
      {/* ================================================================= */}
      <main className="max-w-2xl mx-auto w-full my-auto py-6 sm:py-8">
        <div className="bg-white rounded-3xl border border-slate-200 shadow-[0_20px_50px_rgba(0,0,0,0.05)] p-6 sm:p-10 space-y-6">
          {/* Progress Bar (3 Equal Segments) */}
          <div className="space-y-1.5">
            <div className="flex space-x-2">
              {[1, 2, 3].map((s) => (
                <div
                  key={s}
                  className={`h-1.5 flex-1 rounded-full transition-all duration-300 ${
                    s <= step
                      ? 'bg-orange-600'
                      : 'bg-slate-100'
                  }`}
                />
              ))}
            </div>
            <div className="flex justify-between text-[11px] font-semibold text-slate-400">
              <span className={step >= 1 ? 'text-orange-600' : ''}>1. Student Profile</span>
              <span className={step >= 2 ? 'text-orange-600' : ''}>2. Experience</span>
              <span className={step >= 3 ? 'text-orange-600' : ''}>3. Course Selection</span>
            </div>
          </div>

          {/* Validation Error Banner */}
          {errorMsg && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-center space-x-2 animate-fadeIn">
              <AlertCircle className="w-4 h-4 text-rose-500 flex-shrink-0" />
              <span className="font-medium">{errorMsg}</span>
            </div>
          )}

          {/* ============================================================= */}
          {/* STEP 1: STUDENT PROFILE                                       */}
          {/* ============================================================= */}
          {step === 1 && (
            <div className="space-y-6 animate-fadeIn">
              <div>
                <div className="inline-flex items-center space-x-1.5 px-3 py-1 bg-orange-50 text-orange-700 rounded-full text-xs font-semibold mb-2">
                  <Sparkles className="w-3.5 h-3.5 text-orange-600" />
                  <span>Step 1 of 3</span>
                </div>
                <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
                  Let's personalize your learning experience
                </h2>
                <p className="text-xs sm:text-sm text-slate-500 mt-1">
                  Tell us a bit about your academic profile to generate outcome-aligned roadmaps.
                </p>
              </div>

              <div className="space-y-4">
                {/* Field 1: Student Name */}
                <div>
                  <label className="block text-xs font-bold text-slate-800 mb-1.5">
                    Student Name <span className="text-rose-500">*</span>
                  </label>
                  <div className="relative">
                    <UserIcon className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
                    <input
                      type="text"
                      value={fullName}
                      onChange={(e) => {
                        setFullName(e.target.value);
                        if (errorMsg) setErrorMsg(null);
                      }}
                      placeholder="Enter your full name"
                      className="w-full pl-10 pr-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-orange-500 focus:ring-2 focus:ring-orange-100 transition-all"
                    />
                  </div>
                </div>

                {/* Field 2: Department */}
                <div>
                  <label className="block text-xs font-bold text-slate-800 mb-1.5">
                    Department <span className="text-rose-500">*</span>
                  </label>
                  <div className="relative">
                    <Building className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
                    <input
                      type="text"
                      value={department}
                      onChange={(e) => {
                        setDepartment(e.target.value);
                        if (errorMsg) setErrorMsg(null);
                      }}
                      placeholder="e.g. CSE"
                      className="w-full pl-10 pr-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-orange-500 focus:ring-2 focus:ring-orange-100 transition-all"
                    />
                  </div>
                  {/* Quick Select Pills for Common Departments */}
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    <span className="text-[11px] text-slate-400 mr-1 self-center">Suggestions:</span>
                    {departmentOptions.map((dept) => (
                      <button
                        key={dept}
                        type="button"
                        onClick={() => {
                          setDepartment(dept);
                          if (errorMsg) setErrorMsg(null);
                        }}
                        className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-colors cursor-pointer ${
                          department === dept
                            ? 'bg-orange-600 text-white shadow-xs'
                            : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                        }`}
                      >
                        {dept}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Field 3: Year */}
                <div>
                  <label className="block text-xs font-bold text-slate-800 mb-1.5">
                    Year <span className="text-rose-500">*</span>
                  </label>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    {yearOptions.map((yr) => (
                      <button
                        key={yr}
                        type="button"
                        onClick={() => {
                          setYear(yr);
                          if (errorMsg) setErrorMsg(null);
                        }}
                        className={`py-2.5 px-3 rounded-xl border text-xs font-semibold transition-all cursor-pointer flex items-center justify-center space-x-1.5 ${
                          year === yr
                            ? 'bg-orange-50 border-orange-600 text-orange-700 shadow-xs ring-1 ring-orange-600'
                            : 'bg-white border-slate-200 text-slate-700 hover:border-slate-300 hover:bg-slate-50'
                        }`}
                      >
                        <Calendar className="w-3.5 h-3.5 text-orange-500" />
                        <span>{yr}</span>
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Action Button: Continue → */}
              <div className="pt-2">
                <button
                  type="button"
                  onClick={handleNextFromStep1}
                  disabled={!fullName.trim() || !department.trim() || !year.trim()}
                  className="w-full py-3.5 px-6 bg-orange-600 hover:bg-orange-700 text-white rounded-xl text-sm font-bold shadow-xs shadow-orange-500/20 hover:shadow transition-all flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
                >
                  <span>Continue →</span>
                </button>
              </div>
            </div>
          )}

          {/* ============================================================= */}
          {/* STEP 2: LEARNING EXPERIENCE                                   */}
          {/* ============================================================= */}
          {step === 2 && (
            <div className="space-y-6 animate-fadeIn">
              <div>
                <div className="inline-flex items-center space-x-1.5 px-3 py-1 bg-orange-50 text-orange-700 rounded-full text-xs font-semibold mb-2">
                  <Sparkles className="w-3.5 h-3.5 text-orange-600" />
                  <span>Step 2 of 3</span>
                </div>
                <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
                  How familiar are you with this subject?
                </h2>
                <p className="text-xs sm:text-sm text-slate-500 mt-1">
                  Select the option that best reflects your current knowledge level.
                </p>
              </div>

              {/* 4 Single-Select Options */}
              <div className="space-y-2.5">
                {experienceOptions.map((opt) => {
                  const Icon = opt.icon;
                  const isSelected = experienceOption === opt.id;
                  return (
                    <button
                      key={opt.id}
                      type="button"
                      onClick={() => {
                        setExperienceOption(opt.id);
                        if (errorMsg) setErrorMsg(null);
                      }}
                      className={`w-full p-4 rounded-2xl border text-left transition-all duration-200 cursor-pointer flex items-center justify-between ${
                        isSelected
                          ? 'border-orange-500 bg-orange-50/70 shadow-xs ring-2 ring-orange-500/30'
                          : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50'
                      }`}
                    >
                      <div className="flex items-center space-x-3.5">
                        <div
                          className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
                            isSelected
                              ? 'bg-orange-600 text-white shadow-xs'
                              : 'bg-slate-100 text-slate-600'
                          }`}
                        >
                          <Icon className="w-5 h-5" />
                        </div>
                        <div>
                          <div className="flex items-center space-x-2">
                            <span className="text-sm font-bold text-slate-900">{opt.title}</span>
                            <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200">
                              {opt.badge}
                            </span>
                          </div>
                          <p className="text-xs text-slate-500 mt-0.5">{opt.desc}</p>
                        </div>
                      </div>

                      {/* Custom Radio Check Circle */}
                      <div
                        className={`w-5 h-5 rounded-full border flex items-center justify-center flex-shrink-0 ml-3 ${
                          isSelected
                            ? 'border-orange-600 bg-orange-600 text-white'
                            : 'border-slate-300 bg-white'
                        }`}
                      >
                        {isSelected && <Check className="w-3 h-3 stroke-[3]" />}
                      </div>
                    </button>
                  );
                })}
              </div>

              {/* Navigation: Back & Continue */}
              <div className="pt-2 flex items-center justify-between space-x-3">
                <button
                  type="button"
                  onClick={() => {
                    setErrorMsg(null);
                    setStep(1);
                  }}
                  className="px-5 py-3 border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-xl text-sm font-semibold transition-colors flex items-center space-x-1.5 cursor-pointer"
                >
                  <ArrowLeft className="w-4 h-4" />
                  <span>Back</span>
                </button>

                <button
                  type="button"
                  onClick={handleNextFromStep2}
                  disabled={!experienceOption}
                  className="flex-1 py-3.5 px-6 bg-orange-600 hover:bg-orange-700 text-white rounded-xl text-sm font-bold shadow-xs shadow-orange-500/20 hover:shadow transition-all flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
                >
                  <span>Continue →</span>
                </button>
              </div>
            </div>
          )}

          {/* ============================================================= */}
          {/* STEP 3: COURSE SELECTION                                      */}
          {/* ============================================================= */}
          {step === 3 && (
            <div className="space-y-6 animate-fadeIn">
              <div>
                <div className="inline-flex items-center space-x-1.5 px-3 py-1 bg-orange-50 text-orange-700 rounded-full text-xs font-semibold mb-2">
                  <Sparkles className="w-3.5 h-3.5 text-orange-600" />
                  <span>Step 3 of 3</span>
                </div>
                <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
                  What would you like to learn?
                </h2>
                <p className="text-xs sm:text-sm text-slate-500 mt-1">
                  Select a course to tailor your outcome-based curriculum and start your skill check.
                </p>
              </div>

              {/* Course Selection Cards */}
              {loadingCourses ? (
                <div className="p-8 text-center text-slate-400 space-y-2">
                  <div className="w-6 h-6 border-2 border-orange-600 border-t-transparent rounded-full animate-spin mx-auto" />
                  <p className="text-xs font-medium">Loading available courses...</p>
                </div>
              ) : (
                <div className="space-y-2.5">
                  {courses.map((c) => {
                    const isSelected = selectedCourseId === c.id;
                    return (
                      <button
                        key={c.id}
                        type="button"
                        onClick={() => {
                          setSelectedCourseId(c.id);
                          if (errorMsg) setErrorMsg(null);
                        }}
                        className={`w-full p-4 rounded-2xl border text-left transition-all duration-200 cursor-pointer flex items-center justify-between ${
                          isSelected
                            ? 'border-orange-500 bg-orange-50/70 shadow-xs ring-2 ring-orange-500/30'
                            : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50'
                        }`}
                      >
                        <div className="flex items-center space-x-3.5">
                          <div
                            className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
                              isSelected
                                ? 'bg-orange-600 text-white shadow-xs'
                                : 'bg-slate-100 text-slate-600'
                            }`}
                          >
                            <BookOpen className="w-5 h-5" />
                          </div>
                          <div>
                            <div className="flex items-center space-x-2">
                              <span className="text-sm font-bold text-slate-900">{c.title}</span>
                              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-md bg-white border border-slate-200 text-orange-600">
                                {c.code}
                              </span>
                            </div>
                            <p className="text-xs text-slate-500 mt-0.5 line-clamp-1">{c.description}</p>
                          </div>
                        </div>

                        {/* Custom Radio Check Circle */}
                        <div
                          className={`w-5 h-5 rounded-full border flex items-center justify-center flex-shrink-0 ml-3 ${
                            isSelected
                              ? 'border-orange-600 bg-orange-600 text-white'
                              : 'border-slate-300 bg-white'
                          }`}
                        >
                          {isSelected && <Check className="w-3 h-3 stroke-[3]" />}
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}

              {/* Navigation: Back & Start AI Skill Check → */}
              <div className="pt-2 flex items-center justify-between space-x-3">
                <button
                  type="button"
                  onClick={() => {
                    setErrorMsg(null);
                    setStep(2);
                  }}
                  disabled={saving}
                  className="px-5 py-3 border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-xl text-sm font-semibold transition-colors flex items-center space-x-1.5 cursor-pointer disabled:opacity-50"
                >
                  <ArrowLeft className="w-4 h-4" />
                  <span>Back</span>
                </button>

                <button
                  type="button"
                  onClick={handleFinishOnboarding}
                  disabled={!selectedCourseId || saving}
                  className="flex-1 py-3.5 px-6 bg-orange-600 hover:bg-orange-700 text-white rounded-xl text-sm font-bold shadow-xs shadow-orange-500/20 hover:shadow transition-all flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
                >
                  {saving ? (
                    <div className="flex items-center space-x-2">
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      <span>Saving Profile...</span>
                    </div>
                  ) : (
                    <>
                      <span>Start AI Skill Check →</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="max-w-2xl mx-auto w-full text-center text-xs text-slate-400 pt-4">
        OBEPath AI • Outcome-Based Education Framework
      </footer>
    </div>
  );
};
