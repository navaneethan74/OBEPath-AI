import React, { useState } from 'react';
import { User, StudentProfile } from '../types';
import { UserCheck, Clock, BookOpen, Target, Sparkles, ArrowRight, CheckCircle2 } from 'lucide-react';
import { api } from '../services/api';
import { useStudentLearning } from '../context/StudentLearningContext';

interface ProfileWizardPageProps {
  profile: StudentProfile | null;
  onSaveAndContinue: () => void;
}

export const ProfileWizardPage: React.FC<ProfileWizardPageProps> = ({
  profile,
  onSaveAndContinue
}) => {
  const { studentState, activeCourse } = useStudentLearning();
  const courseTitle = studentState?.enrolledCourse?.title || activeCourse?.title || 'Selected Course';
  const courseCode = studentState?.enrolledCourse?.code || activeCourse?.code || '';

  const [studentId, setStudentId] = useState(profile?.student_id || '');
  const [name, setName] = useState(profile?.full_name || '');
  const [program, setProgram] = useState(profile?.program || 'Computer Science & Engineering');
  const [semester, setSemester] = useState(profile?.semester || 1);
  const [currentLevel, setCurrentLevel] = useState(profile?.current_level || 'Beginner');
  const [academicLevel, setAcademicLevel] = useState(profile?.academic_level || 'Undergraduate (Semester 4)');
  const [goal, setGoal] = useState(
    profile?.learning_goal || `Master fundamental concepts and Course Outcomes in ${courseTitle}.`
  );
  const [priorKnowledge, setPriorKnowledge] = useState(
    profile?.prior_knowledge || 'Beginner with basic programming logic'
  );
  const [format, setFormat] = useState(profile?.preferred_format || 'Interactive examples + practice');
  const [dailyMinutes, setDailyMinutes] = useState(profile?.daily_time_minutes || 60);
  const [targetDate, setTargetDate] = useState(profile?.target_completion_date || '2026-12-15');
  const [saving, setSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.updateProfile({
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
      });
      setSavedSuccess(true);
      setTimeout(() => {
        onSaveAndContinue();
      }, 500);
    } catch (err) {
      console.error('Failed to update profile', err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fadeIn">
      <div className="pb-4 border-b border-slate-200">
        <div className="inline-flex items-center space-x-2 px-3 py-1 bg-orange-50 border border-orange-200 rounded-full text-xs font-semibold text-orange-600 mb-2">
          <Sparkles className="w-3.5 h-3.5 text-orange-500" />
          <span>OBE Steps 1 & 2: Student Registration & Profile Setup</span>
        </div>
        <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Student Profile Setup</h2>
        <p className="text-xs text-slate-500 mt-1">
          The Planner Agent will initialize your cognitive state and map prerequisites against target Course Outcomes.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="bg-white border border-[#E2E8F0] rounded-2xl p-6 sm:p-8 space-y-6 shadow-[0_4px_20px_rgba(15,23,42,0.06)]">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          {/* Student ID */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Student ID (Step 1)</label>
            <input
              type="text"
              value={studentId}
              onChange={(e) => setStudentId(e.target.value)}
              placeholder="e.g. S101"
              className="w-full px-3.5 py-2.5 bg-white border border-[#CBD5E1] rounded-xl text-sm font-mono text-orange-600 focus:outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
            />
          </div>

          {/* Student Name */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Student Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-white border border-[#CBD5E1] rounded-xl text-sm text-slate-900 focus:outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          {/* Program */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Course / Program (Step 1)</label>
            <input
              type="text"
              value={program}
              onChange={(e) => setProgram(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-white border border-[#CBD5E1] rounded-xl text-sm text-slate-900 focus:outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
            />
          </div>

          {/* Semester & Level */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Semester (Step 1)</label>
              <select
                value={semester}
                onChange={(e) => setSemester(parseInt(e.target.value))}
                className="w-full px-3 py-2.5 bg-white border border-[#CBD5E1] rounded-xl text-sm text-slate-900 focus:outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
              >
                <option value={1}>Semester 1</option>
                <option value={2}>Semester 2</option>
                <option value={3}>Semester 3</option>
                <option value={4}>Semester 4</option>
                <option value={5}>Semester 5</option>
                <option value={6}>Semester 6</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Current Level (Step 2)</label>
              <select
                value={currentLevel}
                onChange={(e) => setCurrentLevel(e.target.value)}
                className="w-full px-3 py-2.5 bg-white border border-[#CBD5E1] rounded-xl text-sm font-semibold text-emerald-600 focus:outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
              >
                <option value="Beginner">Beginner</option>
                <option value="Intermediate">Intermediate</option>
                <option value="Advanced">Advanced</option>
              </select>
            </div>
          </div>
        </div>

        {/* Selected Subject */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">Selected Subject (Step 1)</label>
          <input
            type="text"
            readOnly
            value={`${courseTitle} ${courseCode ? `(${courseCode})` : ''}`}
            className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-semibold text-orange-600 cursor-not-allowed"
          />
        </div>

        {/* Course Outcomes Preview (Step 3) */}
        <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-500 font-semibold">
            <span>Step 3: Target Course Outcomes (COs)</span>
            <span className="text-orange-600 font-mono">{courseCode} {courseTitle}</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-xs">
            {(studentState?.courseOutcomeAttainment && studentState.courseOutcomeAttainment.length > 0
              ? studentState.courseOutcomeAttainment.slice(0, 3)
              : [
                  { code: 'CO1', description: 'Foundational concepts and principles' },
                  { code: 'CO2', description: 'Applied problem solving and procedural logic' },
                  { code: 'CO3', description: 'Analysis, efficiency, and real-world evaluation' }
                ]
            ).map((co: any, idx: number) => (
              <div key={co.code || idx} className="p-2.5 bg-white border border-slate-200 rounded-xl shadow-xs">
                <span className="px-1.5 py-0.5 bg-orange-50 text-orange-600 border border-orange-200 text-[10px] font-bold rounded">{co.code}</span>
                <p className="mt-1 text-slate-700 font-medium leading-snug line-clamp-2">{co.description || co.title}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Learning Goal */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">Learning Goal (Step 2)</label>
          <textarea
            rows={2}
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            className="w-full px-3.5 py-2.5 bg-white border border-[#CBD5E1] rounded-xl text-sm text-slate-900 focus:outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          {/* Prior Knowledge */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Prior Knowledge</label>
            <select
              value={priorKnowledge}
              onChange={(e) => setPriorKnowledge(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-white border border-[#CBD5E1] rounded-xl text-sm text-slate-900 focus:outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
            >
              <option>Beginner with basic concepts</option>
              <option>Zero prior programming background</option>
              <option>Familiar with syntax in other languages (C/Java)</option>
              <option>Intermediate looking to refresh concepts</option>
            </select>
          </div>

          {/* Preferred Format */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Preferred Content Format</label>
            <select
              value={format}
              onChange={(e) => setFormat(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-white border border-[#CBD5E1] rounded-xl text-sm text-slate-900 focus:outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
            >
              <option>Interactive examples + practice</option>
              <option>Conceptual deep dives + reading</option>
              <option>Rapid challenge-based problem sets</option>
              <option>Visual walkthroughs with execution traces</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          {/* Available Study Time */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Available Study Time (Daily)
            </label>
            <div className="flex items-center space-x-3">
              <input
                type="range"
                min="30"
                max="180"
                step="15"
                value={dailyMinutes}
                onChange={(e) => setDailyMinutes(parseInt(e.target.value))}
                className="flex-1 accent-[#EA580C]"
              />
              <span className="text-xs font-mono font-bold text-orange-600 min-w-[70px]">
                {Math.floor(dailyMinutes / 60)}h {dailyMinutes % 60 ? `${dailyMinutes % 60}m` : ''} / day
              </span>
            </div>
          </div>

          {/* Target Completion Date */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Target Completion Date</label>
            <input
              type="date"
              value={targetDate}
              onChange={(e) => setTargetDate(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-white border border-[#CBD5E1] rounded-xl text-sm text-slate-900 focus:outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
            />
          </div>
        </div>

        <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
          <div className="text-xs text-slate-500 flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
            <span>Profile stored with SQLite persistence</span>
          </div>

          <button
            type="submit"
            disabled={saving}
            className="px-6 py-2.5 bg-[#EA580C] hover:bg-[#C2410C] text-white rounded-xl text-xs font-semibold shadow-xs transition-all flex items-center space-x-2 disabled:opacity-50"
          >
            <span>{saving ? 'Saving...' : 'Continue to Diagnostic Assessment'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  );
};
