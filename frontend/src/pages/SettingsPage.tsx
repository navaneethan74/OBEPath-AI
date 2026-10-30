import React, { useState, useEffect } from 'react';
import {
  Settings,
  User,
  Bell,
  Sliders,
  Shield,
  Save,
  CheckCircle2,
  Clock,
  Sparkles,
  BookOpen,
  Laptop
} from 'lucide-react';
import { useStudentLearning } from '../context/StudentLearningContext';
import { api } from '../services/api';

export const SettingsPage: React.FC = () => {
  const { studentState, refreshStudentState } = useStudentLearning();
  const profile = studentState?.studentProfile;

  // Active settings tab
  const [activeSubTab, setActiveSubTab] = useState<'general' | 'learning' | 'notifications' | 'security'>('general');

  // Form states
  const [fullName, setFullName] = useState(profile?.full_name || '');
  const [email, setEmail] = useState(profile?.email || '');
  const [studentId, setStudentId] = useState(profile?.student_id || '');
  const [program, setProgram] = useState(profile?.program || 'Computer Science & Engineering');
  const [semester, setSemester] = useState(profile?.semester || 1);
  const [dailyTimeMinutes, setDailyTimeMinutes] = useState(profile?.daily_time_minutes || 60);

  // Sync state when profile or current user loads
  useEffect(() => {
    if (profile) {
      if (profile.full_name) setFullName(profile.full_name);
      if (profile.email) setEmail(profile.email);
      if (profile.student_id) setStudentId(profile.student_id);
      if (profile.program) setProgram(profile.program);
      if (profile.semester) setSemester(profile.semester);
      if (profile.daily_time_minutes) setDailyTimeMinutes(profile.daily_time_minutes);
      if (profile.current_level) setCurrentLevel(profile.current_level);
    } else if (typeof window !== 'undefined') {
      const savedUser = localStorage.getItem('obepath_current_user');
      if (savedUser) {
        try {
          const u = JSON.parse(savedUser);
          if (u.full_name) setFullName((prev) => prev || u.full_name);
          if (u.email) setEmail((prev) => prev || u.email);
        } catch (e) {}
      }
    }
  }, [profile]);

  // Learning preferences
  const [currentLevel, setCurrentLevel] = useState(profile?.current_level || 'Beginner');
  const [tutorTone, setTutorTone] = useState<'socratic' | 'detailed' | 'concise'>('socratic');
  const [autoAdapt, setAutoAdapt] = useState(true);

  // Notifications
  const [emailReminders, setEmailReminders] = useState(true);
  const [progressDigest, setProgressDigest] = useState(true);
  const [tutorPrompts, setTutorPrompts] = useState(true);

  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const handleSave = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setSaving(true);
    setSaveSuccess(false);

    try {
      let targetUserId = profile?.user_id;
      if (!targetUserId && typeof window !== 'undefined') {
        const saved = localStorage.getItem('obepath_current_user');
        if (saved) {
          try {
            targetUserId = JSON.parse(saved).id;
          } catch (e) {}
        }
      }
      if (!targetUserId) {
        throw new Error('User ID not found');
      }
      await api.updateProfile({
        full_name: fullName,
        student_id: studentId,
        program,
        semester: Number(semester),
        current_level: currentLevel,
        daily_time_minutes: Number(dailyTimeMinutes)
      }, targetUserId);
      await refreshStudentState();
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      console.error('Failed to save settings', err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6 max-w-[1400px] mx-auto pb-12">
      {/* Header */}
      <div className="bg-white border border-[#E2E8F0] rounded-2xl p-6 sm:p-7 shadow-[0_2px_12px_rgba(15,23,42,0.03)] flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-semibold text-orange-600 mb-1">
            <Settings className="w-4 h-4" />
            <span className="uppercase tracking-wider">Account & System Configuration</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
            Settings
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Manage your personal profile, study schedule goals, AI learning preferences, and notification alerts.
          </p>
        </div>

        {saveSuccess && (
          <div className="flex items-center space-x-2 px-3.5 py-2 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-xl text-xs font-semibold animate-fadeIn">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <span>Settings saved successfully!</span>
          </div>
        )}
      </div>

      {/* Main Settings Container with Left Tabs and Right Form */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Sub-tabs Navigation */}
        <div className="lg:col-span-3 bg-white border border-[#E2E8F0] rounded-2xl p-2 shadow-xs space-y-1">
          <button
            onClick={() => setActiveSubTab('general')}
            className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
              activeSubTab === 'general'
                ? 'bg-orange-50 text-orange-600'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
            }`}
          >
            <User className="w-4 h-4" />
            <span>General & Profile</span>
          </button>

          <button
            onClick={() => setActiveSubTab('learning')}
            className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
              activeSubTab === 'learning'
                ? 'bg-orange-50 text-orange-600'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
            }`}
          >
            <Sliders className="w-4 h-4" />
            <span>Learning Preferences</span>
          </button>

          <button
            onClick={() => setActiveSubTab('notifications')}
            className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
              activeSubTab === 'notifications'
                ? 'bg-orange-50 text-orange-600'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
            }`}
          >
            <Bell className="w-4 h-4" />
            <span>Notifications</span>
          </button>

          <button
            onClick={() => setActiveSubTab('security')}
            className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
              activeSubTab === 'security'
                ? 'bg-orange-50 text-orange-600'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
            }`}
          >
            <Shield className="w-4 h-4" />
            <span>Account & Security</span>
          </button>
        </div>

        {/* Right Settings Form Area */}
        <div className="lg:col-span-9 bg-white border border-[#E2E8F0] rounded-2xl p-6 sm:p-7 shadow-xs">
          <form onSubmit={handleSave} className="space-y-6">
            {/* SUB-TAB 1: GENERAL & PROFILE */}
            {activeSubTab === 'general' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-base font-bold text-slate-900 tracking-tight">
                    General Student Profile
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Your official student identification details across the Outcome-Based Education system.
                  </p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                      Full Name
                    </label>
                    <input
                      type="text"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      className="w-full px-3.5 py-2 bg-[#F8FAFC] border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-900 focus:outline-none focus:border-orange-500 focus:bg-white transition-all"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                      Email Address
                    </label>
                    <input
                      type="email"
                      value={email}
                      disabled
                      className="w-full px-3.5 py-2 bg-slate-100 border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-500 cursor-not-allowed"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                      Student ID / Roll No.
                    </label>
                    <input
                      type="text"
                      value={studentId}
                      onChange={(e) => setStudentId(e.target.value)}
                      className="w-full px-3.5 py-2 bg-[#F8FAFC] border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-900 focus:outline-none focus:border-orange-500 focus:bg-white transition-all"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                      Semester
                    </label>
                    <select
                      value={semester}
                      onChange={(e) => setSemester(Number(e.target.value))}
                      className="w-full px-3.5 py-2 bg-[#F8FAFC] border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-900 focus:outline-none focus:border-orange-500 focus:bg-white transition-all cursor-pointer"
                    >
                      {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
                        <option key={s} value={s}>
                          Semester {s}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="sm:col-span-2">
                    <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                      Degree / Program
                    </label>
                    <input
                      type="text"
                      value={program}
                      onChange={(e) => setProgram(e.target.value)}
                      className="w-full px-3.5 py-2 bg-[#F8FAFC] border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-900 focus:outline-none focus:border-orange-500 focus:bg-white transition-all"
                    />
                  </div>
                </div>

                <div className="pt-4 border-t border-slate-100">
                  <label className="block text-xs font-semibold text-slate-700 mb-2">
                    Daily Study Target: <span className="text-orange-600 font-bold">{dailyTimeMinutes} minutes/day</span>
                  </label>
                  <div className="grid grid-cols-4 gap-2">
                    {[15, 30, 60, 120].map((mins) => (
                      <button
                        type="button"
                        key={mins}
                        onClick={() => setDailyTimeMinutes(mins)}
                        className={`py-2 text-xs font-semibold rounded-xl border transition-all cursor-pointer ${
                          dailyTimeMinutes === mins
                            ? 'bg-orange-50 text-orange-600 border-orange-200'
                            : 'bg-[#F8FAFC] text-slate-600 border-slate-200 hover:bg-slate-100'
                        }`}
                      >
                        {mins} min
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* SUB-TAB 2: LEARNING PREFERENCES */}
            {activeSubTab === 'learning' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-base font-bold text-slate-900 tracking-tight">
                    Adaptive Learning Preferences
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Customize how the AI diagnostic engine and Gemini AI Tutor calibrate to your pace.
                  </p>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-2">
                      Current Starting Level
                    </label>
                    <div className="grid grid-cols-3 gap-3">
                      {['Beginner', 'Intermediate', 'Advanced'].map((lvl) => (
                        <button
                          type="button"
                          key={lvl}
                          onClick={() => setCurrentLevel(lvl)}
                          className={`p-3 text-xs font-semibold rounded-xl border text-center transition-all cursor-pointer ${
                            currentLevel === lvl
                              ? 'bg-orange-50 text-orange-600 border-orange-200'
                              : 'bg-[#F8FAFC] text-slate-600 border-slate-200 hover:bg-slate-100'
                          }`}
                        >
                          {lvl}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-2">
                      AI Tutor Interaction Style
                    </label>
                    <div className="space-y-2">
                      <label className="flex items-center space-x-3 p-3 bg-[#F8FAFC] rounded-xl border border-slate-200 cursor-pointer">
                        <input
                          type="radio"
                          name="tutorTone"
                          checked={tutorTone === 'socratic'}
                          onChange={() => setTutorTone('socratic')}
                          className="text-orange-600 focus:ring-orange-500"
                        />
                        <div className="text-xs">
                          <span className="font-bold text-slate-900">Socratic Guided Mentorship</span>
                          <p className="text-slate-500 text-[11px]">Guides you through problems with hints, asking probing questions rather than giving immediate code.</p>
                        </div>
                      </label>

                      <label className="flex items-center space-x-3 p-3 bg-[#F8FAFC] rounded-xl border border-slate-200 cursor-pointer">
                        <input
                          type="radio"
                          name="tutorTone"
                          checked={tutorTone === 'detailed'}
                          onChange={() => setTutorTone('detailed')}
                          className="text-orange-600 focus:ring-orange-500"
                        />
                        <div className="text-xs">
                          <span className="font-bold text-slate-900">Step-by-Step Deep Dive</span>
                          <p className="text-slate-500 text-[11px]">Provides thorough conceptual breakdowns with code blocks, analogies, and mathematical proofs.</p>
                        </div>
                      </label>

                      <label className="flex items-center space-x-3 p-3 bg-[#F8FAFC] rounded-xl border border-slate-200 cursor-pointer">
                        <input
                          type="radio"
                          name="tutorTone"
                          checked={tutorTone === 'concise'}
                          onChange={() => setTutorTone('concise')}
                          className="text-orange-600 focus:ring-orange-500"
                        />
                        <div className="text-xs">
                          <span className="font-bold text-slate-900">Concise & Direct</span>
                          <p className="text-slate-500 text-[11px]">Gives quick code snippets and brief definitions for rapid review.</p>
                        </div>
                      </label>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                    <div>
                      <div className="text-xs font-bold text-slate-900">Auto-Adapt Learning Path</div>
                      <div className="text-[11px] text-slate-500">Automatically re-sequence topic items based on quiz scores and prerequisite mastery.</div>
                    </div>
                    <input
                      type="checkbox"
                      checked={autoAdapt}
                      onChange={(e) => setAutoAdapt(e.target.checked)}
                      className="w-4 h-4 text-orange-600 rounded focus:ring-orange-500 cursor-pointer"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* SUB-TAB 3: NOTIFICATIONS */}
            {activeSubTab === 'notifications' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-base font-bold text-slate-900 tracking-tight">
                    Notification Preferences
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Choose which learning reminders and progress alerts you receive.
                  </p>
                </div>

                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3.5 bg-[#F8FAFC] rounded-xl border border-slate-200">
                    <div>
                      <div className="text-xs font-bold text-slate-900">Daily Study Reminders</div>
                      <div className="text-[11px] text-slate-500">Receive gentle nudges to keep your study streak and complete scheduled modules.</div>
                    </div>
                    <input
                      type="checkbox"
                      checked={emailReminders}
                      onChange={(e) => setEmailReminders(e.target.checked)}
                      className="w-4 h-4 text-orange-600 rounded focus:ring-orange-500 cursor-pointer"
                    />
                  </div>

                  <div className="flex items-center justify-between p-3.5 bg-[#F8FAFC] rounded-xl border border-slate-200">
                    <div>
                      <div className="text-xs font-bold text-slate-900">Weekly Progress & Outcome Digest</div>
                      <div className="text-[11px] text-slate-500">Summary of topics mastered, Course Outcomes attained, and weak areas needing practice.</div>
                    </div>
                    <input
                      type="checkbox"
                      checked={progressDigest}
                      onChange={(e) => setProgressDigest(e.target.checked)}
                      className="w-4 h-4 text-orange-600 rounded focus:ring-orange-500 cursor-pointer"
                    />
                  </div>

                  <div className="flex items-center justify-between p-3.5 bg-[#F8FAFC] rounded-xl border border-slate-200">
                    <div>
                      <div className="text-xs font-bold text-slate-900">AI Tutor Challenge Recommendations</div>
                      <div className="text-[11px] text-slate-500">Alerts when your AI Tutor recommends a quick test or concept review.</div>
                    </div>
                    <input
                      type="checkbox"
                      checked={tutorPrompts}
                      onChange={(e) => setTutorPrompts(e.target.checked)}
                      className="w-4 h-4 text-orange-600 rounded focus:ring-orange-500 cursor-pointer"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* SUB-TAB 4: SECURITY */}
            {activeSubTab === 'security' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-base font-bold text-slate-900 tracking-tight">
                    Account & Security
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Manage session security and authenticated devices.
                  </p>
                </div>

                <div className="space-y-4">
                  <div className="p-4 bg-[#F8FAFC] rounded-xl border border-slate-200 flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="p-2 bg-orange-50 text-orange-600 rounded-lg">
                        <Laptop className="w-5 h-5" />
                      </div>
                      <div>
                        <div className="text-xs font-bold text-slate-900">Current Active Session</div>
                        <div className="text-[11px] text-slate-500">Windows • Google Chrome • Verified Local Client</div>
                      </div>
                    </div>
                    <span className="text-[10px] font-bold px-2 py-0.5 bg-emerald-50 text-emerald-700 rounded border border-emerald-200">
                      Active Now
                    </span>
                  </div>

                  <div className="pt-2">
                    <button
                      type="button"
                      onClick={() => alert('Password update form sent to verified student email.')}
                      className="px-4 py-2 bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 rounded-xl text-xs font-semibold shadow-xs transition-all cursor-pointer"
                    >
                      Request Password Reset
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Save Button */}
            <div className="pt-6 border-t border-slate-100 flex items-center justify-end space-x-3">
              <button
                type="submit"
                disabled={saving}
                className="inline-flex items-center space-x-2 px-6 py-2.5 bg-orange-600 hover:bg-orange-700 active:scale-[0.99] text-white rounded-xl text-xs sm:text-sm font-semibold shadow-xs hover:shadow transition-all cursor-pointer disabled:opacity-50"
              >
                <Save className="w-4 h-4" />
                <span>{saving ? 'Saving...' : 'Save Changes'}</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
