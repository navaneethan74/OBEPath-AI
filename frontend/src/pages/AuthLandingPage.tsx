import React, { useState } from 'react';
import {
  Mail,
  Lock,
  Eye,
  EyeOff,
  User as UserIcon,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { api } from '../services/api';
import { User } from '../types';
import { AILearningEngineVisual } from '../components/AILearningEngineVisual';
import { GoogleAuthModal } from '../components/GoogleAuthModal';

interface AuthLandingPageProps {
  onAuthSuccess: (user: User, isNewUser?: boolean, onboardingCompleted?: boolean) => void;
  initialMode?: 'login' | 'register';
}

export type AuthRoleTab = 'student' | 'faculty';

export const AuthLandingPage: React.FC<AuthLandingPageProps> = ({
  onAuthSuccess,
  initialMode = 'login'
}) => {
  const [selectedTab, setSelectedTab] = useState<AuthRoleTab>('student');
  const [mode, setMode] = useState<'login' | 'register'>(initialMode);

  // Form Fields
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(true);
  const [consentAgreed, setConsentAgreed] = useState(false);

  // UI State
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const handleNavigateLegal = (path: string) => {
    if (typeof window !== 'undefined') {
      window.history.pushState({}, '', path);
      window.dispatchEvent(new PopStateEvent('popstate'));
    }
  };

  // Google Modal
  const isGoogleConfigured = Boolean(import.meta.env.VITE_GOOGLE_CLIENT_ID);
  const [googleModalOpen, setGoogleModalOpen] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);

  // Forgot Password Toast State
  const [forgotPasswordMsg, setForgotPasswordMsg] = useState<string | null>(null);

  // Explicitly reset all form inputs on mount and whenever mode or tab toggles
  React.useEffect(() => {
    setFullName('');
    setEmail('');
    setPassword('');
    setConfirmPassword('');
    setError(null);
    setFieldErrors({});
  }, [mode, selectedTab]);

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!email.trim()) {
      errors.email = 'Email address is required';
    } else if (!emailRegex.test(email.trim())) {
      errors.email = 'Please enter a valid email address';
    }

    if (!password) {
      errors.password = 'Password is required';
    } else if (password.length < 4) {
      errors.password = 'Password must be at least 4 characters';
    }

    if (mode === 'register') {
      if (!fullName.trim()) {
        errors.fullName = 'Full name is required';
      }
      if (password !== confirmPassword) {
        errors.confirmPassword = 'Passwords do not match';
      }
      if (selectedTab === 'student' && !consentAgreed) {
        errors.consent = 'You must agree to the Terms of Service and Privacy Policy to register.';
      }
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);

    if (!validateForm()) return;

    setLoading(true);

    try {
      if (mode === 'register') {
        const res = await api.register(email.trim().toLowerCase(), password.trim(), fullName.trim(), 'student');
        setSuccessMsg('Account created successfully! Initializing your onboarding experience...');
        setTimeout(() => {
          onAuthSuccess(res.user, true, false);
        }, 750);
      } else {
        const res = await api.login(email.trim().toLowerCase(), password.trim(), selectedTab, selectedTab);

        setSuccessMsg(`Welcome back, ${res.user.full_name}! Loading your workspace...`);
        const isNew = res.is_new_user ?? !res.onboarding_completed;
        const onboardingDone = res.onboarding_completed ?? false;
        setTimeout(() => {
          onAuthSuccess(res.user, isNew, onboardingDone);
        }, 700);
      }
    } catch (err: any) {
      console.error('Auth error', err);
      setError(err.message || 'Authentication failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSuccess = async (credential: string) => {
    setGoogleLoading(true);
    try {
      const res = await api.loginWithGoogle(credential);
      if (res.user.role !== 'student') {
        api.logout();
        setError('This account is not a student account');
        return;
      }
      setGoogleModalOpen(false);
      setSuccessMsg(`Google Authentication successful! Welcome, ${res.user.full_name}.`);
      const isNew = res.is_new_user ?? !res.onboarding_completed;
      const onboardingDone = res.onboarding_completed ?? false;
      setTimeout(() => {
        onAuthSuccess(res.user, isNew, onboardingDone);
      }, 700);
    } catch (err: any) {
      throw err;
    } finally {
      setGoogleLoading(false);
    }
  };

  return (
    <div className="relative w-full min-h-screen bg-[#F8FAFC] flex flex-col justify-between overflow-x-hidden font-sans selection:bg-orange-100 selection:text-orange-900">
      {/* ================================================================= */}
      {/* 1. BACKGROUND WIDE SPLIT CANVAS WITH CURVED BLUE ORGANIC WAVE     */}
      {/* ================================================================= */}
      <div className="absolute inset-0 w-full h-full pointer-events-none overflow-hidden z-0">
        {/* Left Side: Crisp subtle geometric facet gradient */}
        <div
          className="absolute inset-y-0 left-0 w-[55%] bg-gradient-to-br from-white via-[#F8FAFC] to-[#EEF2F6]"
          style={{
            backgroundImage: `radial-gradient(circle at 10% 20%, rgba(224, 231, 255, 0.4) 0%, transparent 40%),
                              linear-gradient(135deg, rgba(255,255,255,0.8) 0%, rgba(241,245,249,0.5) 100%)`
          }}
        />

        {/* Right Side: Deep Obsidian / Cyber Navy Background */}
        <div className="absolute inset-y-0 right-0 w-[60%] bg-gradient-to-br from-[#020512] via-[#050C20] to-[#081232]" />

        {/* Sweeping S-Curve Blue Wave Transition Between Panels */}
        <svg
          className="absolute inset-0 w-full h-full"
          viewBox="0 0 1440 900"
          preserveAspectRatio="none"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <defs>
            <linearGradient id="waveGradDark" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#0B1842" />
              <stop offset="50%" stopColor="#050C20" />
              <stop offset="100%" stopColor="#020512" />
            </linearGradient>

            <linearGradient id="waveBlueRibbon" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#2563EB" stopOpacity="0.95" />
              <stop offset="40%" stopColor="#1D4ED8" stopOpacity="1" />
              <stop offset="80%" stopColor="#4338CA" stopOpacity="0.9" />
              <stop offset="100%" stopColor="#6366F1" stopOpacity="0.85" />
            </linearGradient>

            <linearGradient id="cyanWaveEdge" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#60A5FA" stopOpacity="0.8" />
              <stop offset="50%" stopColor="#00F0FF" stopOpacity="1" />
              <stop offset="100%" stopColor="#38BDF8" stopOpacity="0.9" />
            </linearGradient>

            <filter id="softBlueGlow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="16" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* Deep Navy Background Extension behind wave */}
          <path
            d="M 680,0 C 600,240 500,420 540,650 C 560,780 620,860 680,900 L 1440,900 L 1440,0 Z"
            fill="url(#waveGradDark)"
          />

          {/* Glowing Ambient Cyan / Light Blue Halo along the crest */}
          <path
            d="M 680,0 C 600,240 500,420 540,650 C 560,780 620,860 680,900"
            stroke="url(#cyanWaveEdge)"
            strokeWidth="38"
            strokeOpacity="0.25"
            filter="url(#softBlueGlow)"
            fill="none"
          />

          {/* Vibrant Royal Blue Sweeping Wave Ribbon */}
          <path
            d="M 670,0 C 590,240 490,420 530,650 C 550,780 610,860 670,900 L 730,900 C 660,860 600,780 580,650 C 540,420 640,240 730,0 Z"
            fill="url(#waveBlueRibbon)"
          />

          {/* Crisp Cyan Crest Edge Line */}
          <path
            d="M 670,0 C 590,240 490,420 530,650 C 550,780 610,860 670,900"
            stroke="url(#cyanWaveEdge)"
            strokeWidth="4"
            fill="none"
          />
        </svg>
      </div>

      {/* ================================================================= */}
      {/* 2. TOP HEADER: BRAND LOGO (LEFT) & PLATFORM ONLINE PILL (RIGHT)   */}
      {/* ================================================================= */}
      <header className="relative w-full max-w-[1440px] mx-auto px-6 sm:px-10 lg:px-14 pt-6 sm:pt-8 flex items-center justify-between z-30">
        {/* Top-Left: OBEPath AI Logo (3D Graduation Cap on Stacked Platforms) */}
        <div className="flex items-center space-x-3.5">
          {/* 3D Isometric Logo Icon Exactly as Reference */}
          <div className="w-11 h-11 flex-shrink-0">
            <svg className="w-full h-full" viewBox="0 0 48 48" fill="none">
              {/* Bottom blue platform */}
              <path d="M 6 34 L 24 43 L 42 34 L 24 25 Z" fill="#0066FF" />
              <path d="M 6 34 L 24 43 L 24 46 L 6 37 Z" fill="#0047BA" />
              <path d="M 42 34 L 24 43 L 24 46 L 42 37 Z" fill="#1D4ED8" />

              {/* Middle cyan layered platform */}
              <path d="M 9 27 L 24 35 L 39 27 L 24 19 Z" fill="#00E5FF" />
              <path d="M 9 27 L 24 35 L 24 37.5 L 9 29.5 Z" fill="#00B4D8" />
              <path d="M 39 27 L 24 35 L 24 37.5 L 39 29.5 Z" fill="#0284C7" />

              {/* Top 3D Graduation Cap (Mortarboard) */}
              <path d="M 24 6 L 44 16 L 24 26 L 4 16 Z" fill="url(#logoCapGrad)" />
              <path d="M 4 16 L 24 26 L 24 28.5 L 4 18.5 Z" fill="#1E40AF" />
              <path d="M 44 16 L 24 26 L 24 28.5 L 44 18.5 Z" fill="#312E81" />

              {/* Cap Tassel */}
              <circle cx="24" cy="16" r="2.2" fill="#FFFFFF" />
              <path d="M 24 16 Q 34 18 36 26" stroke="#00F0FF" strokeWidth="2" strokeLinecap="round" fill="none" />
              <circle cx="36" cy="26" r="2" fill="#00F0FF" />

              <defs>
                <linearGradient id="logoCapGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#38BDF8" />
                  <stop offset="45%" stopColor="#2563EB" />
                  <stop offset="100%" stopColor="#6366F1" />
                </linearGradient>
              </defs>
            </svg>
          </div>

          {/* Logo Typography: OBEPath (navy/black) + AI (orange) */}
          <div className="flex items-baseline">
            <span className="text-2xl sm:text-[26px] font-black text-slate-900 tracking-tight leading-none font-sans">
              OBEPath
            </span>
            <span className="text-2xl sm:text-[26px] font-black text-orange-600 tracking-tight leading-none ml-1.5 font-sans">
              AI
            </span>
          </div>
        </div>

        {/* Top-Right: Green "Platform Online" Status Pill (Clean & Steady) */}
        <div className="flex items-center space-x-2 px-3.5 sm:px-4 py-1.5 rounded-full bg-[#071329]/80 border border-slate-700/60 backdrop-blur-md text-white text-xs font-semibold shadow-lg">
          <span className="relative flex h-2 w-2">
            <span className="relative inline-flex rounded-full h-2 w-2 bg-[#10B981] shadow-[0_0_8px_#34D399]"></span>
          </span>
          <span className="tracking-wide text-slate-200 text-xs font-medium">Platform Online</span>
        </div>
      </header>

      {/* ================================================================= */}
      {/* 3. MAIN WORKSPACE: LEFT FLOATING LOGIN CARD / RIGHT AI VISUAL     */}
      {/* ================================================================= */}
      <main className="relative w-full max-w-[1440px] mx-auto px-6 sm:px-10 lg:px-14 py-4 sm:py-6 flex-1 flex flex-col lg:flex-row items-center justify-between z-20">
        
        {/* =============================================================== */}
        {/* LEFT SIDE: FLOATING WHITE LOGIN CARD                            */}
        {/* =============================================================== */}
        <div className="w-full lg:w-[420px] xl:w-[440px] my-auto flex-shrink-0 z-20">
          <div className="w-full bg-white rounded-[28px] sm:rounded-[32px] p-7 sm:p-9 shadow-[0_20px_60px_-15px_rgba(0,0,0,0.09)] border border-slate-100 flex flex-col">
            
            {/* Role Tabs: Student | Faculty */}
            <div className="flex p-1 bg-slate-100 rounded-2xl mb-6 border border-slate-200/60 shadow-xs">
              {(['student', 'faculty'] as const).map((tab) => {
                const isActive = selectedTab === tab;
                return (
                  <button
                    key={tab}
                    type="button"
                    onClick={() => {
                      setSelectedTab(tab);
                      if (tab !== 'student') setMode('login');
                      setError(null);
                      setFieldErrors({});
                      setSuccessMsg(null);
                    }}
                    className={`flex-1 py-2 text-xs font-bold rounded-xl transition-all cursor-pointer ${
                      isActive
                        ? tab === 'faculty'
                          ? 'bg-purple-600 text-white shadow-sm'
                          : 'bg-orange-600 text-white shadow-sm'
                        : 'text-slate-500 hover:text-slate-800'
                    }`}
                  >
                    {tab === 'student' ? 'Student' : 'Faculty'}
                  </button>
                );
              })}
            </div>

            {/* Dynamic Heading & Subtitle */}
            <div className="text-center sm:text-left mb-6">
              {selectedTab === 'student' ? (
                <>
                  <h1 className="text-3xl sm:text-[32px] font-black tracking-tight leading-tight">
                    <span className="text-slate-900">Welcome </span>
                    <span className="text-orange-600">
                      {mode === 'login' ? 'Back!' : 'Aboard!'}
                    </span>
                  </h1>
                  <p className="text-xs sm:text-sm text-slate-500 mt-1 font-normal">
                    {mode === 'login'
                      ? 'Sign in to continue your student learning journey.'
                      : 'Sign up to begin your learning journey.'}
                  </p>
                </>
              ) : (
                <>
                  <h1 className="text-3xl sm:text-[32px] font-black tracking-tight leading-tight">
                    <span className="text-slate-900">Faculty </span>
                    <span className="text-purple-600">Sign In</span>
                  </h1>
                  <p className="text-xs sm:text-sm text-slate-500 mt-1 font-normal">
                    Sign in to access curriculum analytics, syllabus mapping, and cohorts.
                  </p>
                </>
              )}
            </div>

            {/* Error & Success Messages */}
            {error && (
              <div className="mb-4 p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-start space-x-2 animate-fadeIn">
                <AlertCircle className="w-4 h-4 text-rose-500 flex-shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            {successMsg && (
              <div className="mb-4 p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800 flex items-start space-x-2 animate-fadeIn">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
                <span className="font-medium">{successMsg}</span>
              </div>
            )}

            {forgotPasswordMsg && (
              <div className="mb-4 p-2.5 bg-orange-50 border border-orange-200 rounded-xl text-xs text-orange-800 flex items-center justify-between animate-fadeIn">
                <span>{forgotPasswordMsg}</span>
                <button
                  type="button"
                  onClick={() => setForgotPasswordMsg(null)}
                  className="text-orange-500 hover:text-orange-700 font-bold ml-2 text-sm"
                >
                  ×
                </button>
              </div>
            )}

            {/* Large White Google Button: Continue with Google (Student Tab Only) */}
            {selectedTab === 'student' && (
              <>
                <button
                  type="button"
                  onClick={() => {
                    if (!isGoogleConfigured) return;
                    setGoogleModalOpen(true);
                  }}
                  disabled={loading || !isGoogleConfigured}
                  title={!isGoogleConfigured ? "Google login not configured (VITE_GOOGLE_CLIENT_ID missing)" : "Sign in with Google"}
                  className="w-full py-3 px-4 rounded-2xl border border-slate-200 hover:border-slate-300 hover:bg-slate-50 text-slate-700 text-sm font-semibold transition-all shadow-xs flex items-center justify-center space-x-3 group disabled:opacity-50 disabled:cursor-not-allowed active:scale-[0.99] cursor-pointer"
                >
                  <svg className="w-5 h-5 flex-shrink-0" viewBox="0 0 24 24">
                    <path
                      fill="#4285F4"
                      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                    />
                    <path
                      fill="#34A853"
                      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    />
                    <path
                      fill="#FBBC05"
                      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                    />
                    <path
                      fill="#EA4335"
                      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                    />
                  </svg>
                  <span className="tracking-tight text-slate-800">
                    Continue with Google
                    {!isGoogleConfigured && (
                      <span className="text-[11px] text-slate-400 font-normal ml-2">(Unconfigured)</span>
                    )}
                  </span>
                </button>

                {/* Divider: or */}
                <div className="relative my-4 flex items-center justify-center">
                  <div className="w-full border-t border-slate-200" />
                  <span className="bg-white px-3 text-xs text-slate-400 font-medium lowercase absolute">
                    or
                  </span>
                </div>
              </>
            )}

            {/* Email and Password Form */}
            <form key={mode} onSubmit={handleSubmit} className="space-y-3.5" autoComplete="off">
              {/* Full Name for Registration */}
              {mode === 'register' && (
                <div>
                  <label className="block text-xs font-bold text-slate-800 mb-1">
                    Full Name
                  </label>
                  <div className="relative">
                    <UserIcon className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
                    <input
                      type="text"
                      name="registration_fullname_field"
                      autoComplete="off"
                      data-lpignore="true"
                      value={fullName}
                      onChange={(e) => {
                        setFullName(e.target.value);
                        if (fieldErrors.fullName) setFieldErrors({ ...fieldErrors, fullName: '' });
                      }}
                      placeholder="Enter your full name"
                      className={`w-full pl-10 pr-3.5 py-2.5 bg-white border rounded-xl text-xs sm:text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 transition-all ${
                        fieldErrors.fullName
                          ? 'border-rose-300 focus:border-rose-500 focus:ring-rose-100'
                          : 'border-slate-200 focus:border-orange-500 focus:ring-orange-100'
                      }`}
                    />
                  </div>
                  {fieldErrors.fullName && (
                    <p className="text-[11px] text-rose-600 mt-1">{fieldErrors.fullName}</p>
                  )}
                </div>
              )}

              {/* Email Field */}
              <div>
                <label className="block text-xs font-bold text-slate-800 mb-1">Email</label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
                  <input
                    type="email"
                    name="user_email_address_field"
                    autoComplete="new-password"
                    data-lpignore="true"
                    autoCorrect="off"
                    autoCapitalize="none"
                    spellCheck={false}
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value);
                      if (fieldErrors.email) setFieldErrors({ ...fieldErrors, email: '' });
                    }}
                    placeholder="Enter your email address"
                    className={`w-full pl-10 pr-3.5 py-2.5 bg-white border rounded-xl text-xs sm:text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 transition-all ${
                      fieldErrors.email
                        ? 'border-rose-300 focus:border-rose-500 focus:ring-rose-100'
                        : 'border-slate-200 focus:border-orange-500 focus:ring-orange-100'
                    }`}
                  />
                </div>
                {fieldErrors.email && (
                  <p className="text-[11px] text-rose-600 mt-1">{fieldErrors.email}</p>
                )}
              </div>

              {/* Password Field */}
              <div>
                <label className="block text-xs font-bold text-slate-800 mb-1">Password</label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    name="user_security_token_field"
                    autoComplete="new-password"
                    data-lpignore="true"
                    value={password}
                    onChange={(e) => {
                      setPassword(e.target.value);
                      if (fieldErrors.password) setFieldErrors({ ...fieldErrors, password: '' });
                    }}
                    placeholder="Enter your password"
                    className={`w-full pl-10 pr-10 py-2.5 bg-white border rounded-xl text-xs sm:text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 transition-all ${
                      fieldErrors.password
                        ? 'border-rose-300 focus:border-rose-500 focus:ring-rose-100'
                        : 'border-slate-200 focus:border-orange-500 focus:ring-orange-100'
                    }`}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3.5 top-3 text-slate-400 hover:text-slate-600 transition-colors p-0.5 cursor-pointer"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                {fieldErrors.password && (
                  <p className="text-[11px] text-rose-600 mt-1">{fieldErrors.password}</p>
                )}
              </div>

              {/* Confirm Password for Registration */}
              {mode === 'register' && (
                <div>
                  <label className="block text-xs font-bold text-slate-800 mb-1">
                    Confirm Password
                  </label>
                  <div className="relative">
                    <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
                    <input
                      type={showConfirmPassword ? 'text' : 'password'}
                      name="user_security_token_confirm_field"
                      autoComplete="new-password"
                      data-lpignore="true"
                      value={confirmPassword}
                      onChange={(e) => {
                        setConfirmPassword(e.target.value);
                        if (fieldErrors.confirmPassword)
                          setFieldErrors({ ...fieldErrors, confirmPassword: '' });
                      }}
                      placeholder="Confirm password"
                      className={`w-full pl-10 pr-10 py-2.5 bg-white border rounded-xl text-xs sm:text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 transition-all ${
                        fieldErrors.confirmPassword
                          ? 'border-rose-300 focus:border-rose-500 focus:ring-rose-100'
                          : 'border-slate-200 focus:border-orange-500 focus:ring-orange-100'
                      }`}
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="absolute right-3.5 top-3 text-slate-400 hover:text-slate-600 transition-colors p-0.5 cursor-pointer"
                    >
                      {showConfirmPassword ? (
                        <EyeOff className="w-4 h-4" />
                      ) : (
                        <Eye className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                  {fieldErrors.confirmPassword && (
                    <p className="text-[11px] text-rose-600 mt-1">
                      {fieldErrors.confirmPassword}
                    </p>
                  )}
                </div>
              )}

              {/* Remember Me & Forgot Password Row */}
              {mode === 'login' && (
                <div className="flex items-center justify-between text-xs pt-0.5">
                  <label className="flex items-center space-x-2 cursor-pointer text-slate-600 hover:text-slate-900 select-none">
                    <input
                      type="checkbox"
                      checked={rememberMe}
                      onChange={(e) => setRememberMe(e.target.checked)}
                      className="w-4 h-4 rounded border-slate-300 text-orange-600 focus:ring-orange-100 cursor-pointer"
                    />
                    <span>Remember me</span>
                  </label>

                  <button
                    type="button"
                    onClick={() =>
                      setForgotPasswordMsg(
                        'Password reset instructions have been sent to your registered email address.'
                      )
                    }
                    className="text-orange-600 hover:text-orange-700 font-semibold transition-colors cursor-pointer"
                  >
                    Forgot password?
                  </button>
                </div>
              )}

              {/* Required Consent Checkbox on Student Registration */}
              {mode === 'register' && selectedTab === 'student' && (
                <div className="space-y-1 pt-1 text-left">
                  <label className="flex items-start space-x-2 text-xs text-slate-600 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={consentAgreed}
                      onChange={(e) => {
                        setConsentAgreed(e.target.checked);
                        if (fieldErrors.consent) setFieldErrors({ ...fieldErrors, consent: '' });
                      }}
                      className="mt-0.5 w-4 h-4 rounded border-slate-300 text-orange-600 focus:ring-orange-100 cursor-pointer flex-shrink-0"
                    />
                    <span>
                      I agree to the{' '}
                      <button
                        type="button"
                        onClick={() => handleNavigateLegal('/terms')}
                        className="text-orange-600 hover:underline font-semibold cursor-pointer"
                      >
                        Terms of Service
                      </button>{' '}
                      and{' '}
                      <button
                        type="button"
                        onClick={() => handleNavigateLegal('/privacy')}
                        className="text-orange-600 hover:underline font-semibold cursor-pointer"
                      >
                        Privacy Policy
                      </button>
                      , and consent to OBEPath storing my academic progress, assessment scores, and profile data.
                    </span>
                  </label>
                  {fieldErrors.consent && (
                    <p className="text-[11px] text-rose-600 pl-6">{fieldErrors.consent}</p>
                  )}
                </div>
              )}

              {/* Submit Button with Role Adaptation */}
              <button
                type="submit"
                disabled={loading}
                className={`w-full py-3.5 px-6 text-white rounded-2xl text-sm font-bold shadow-lg transition-all duration-200 flex items-center justify-center space-x-2 disabled:opacity-60 active:scale-[0.99] mt-3 cursor-pointer ${
                  selectedTab === 'faculty'
                    ? 'bg-purple-600 hover:bg-purple-700 shadow-purple-500/25'
                    : 'bg-orange-600 hover:bg-orange-700 shadow-orange-500/25'
                }`}
              >
                {loading ? (
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>
                      {mode === 'register'
                        ? 'Creating Account...'
                        : selectedTab === 'faculty'
                        ? 'Signing In to Faculty Portal...'
                        : 'Signing In...'}
                    </span>
                  </div>
                ) : (
                  <span>
                    {mode === 'register'
                      ? 'Sign Up →'
                      : selectedTab === 'faculty'
                      ? 'Faculty Sign In →'
                      : 'Sign In →'}
                  </span>
                )}
              </button>
            </form>

            {/* Bottom: Sign Up / Sign In Toggle (Student Tab Only) */}
            <div className="mt-5 text-center text-xs text-slate-600">
              {selectedTab === 'student' ? (
                mode === 'login' ? (
                  <p>
                    Don't have an account?{' '}
                    <button
                      type="button"
                      onClick={() => {
                        setMode('register');
                        setError(null);
                        setFieldErrors({});
                      }}
                      className="font-bold text-orange-600 hover:text-orange-700 hover:underline transition-colors ml-1 cursor-pointer"
                    >
                      Sign Up
                    </button>
                  </p>
                ) : (
                  <p>
                    Already have an account?{' '}
                    <button
                      type="button"
                      onClick={() => {
                        setMode('login');
                        setError(null);
                        setFieldErrors({});
                      }}
                      className="font-bold text-orange-600 hover:text-orange-700 hover:underline transition-colors ml-1 cursor-pointer"
                    >
                      Sign In
                    </button>
                  </p>
                )
              ) : (
                <p className="text-slate-400 italic">
                  Faculty accounts are provisioned by an institution administrator.
                </p>
              )}
            </div>
          </div>
        </div>

        {/* =============================================================== */}
        {/* RIGHT SIDE: DARK FUTURISTIC AI EDUCATION ENVIRONMENT            */}
        {/* =============================================================== */}
        <div className="w-full lg:w-[680px] xl:w-[740px] h-full flex items-center justify-center relative z-10 py-6">
          <AILearningEngineVisual />
        </div>
      </main>

      {/* Footer copyright & Legal Links */}
      <footer className="relative w-full max-w-[1440px] mx-auto px-6 sm:px-10 lg:px-14 pb-4 flex flex-wrap items-center justify-between gap-3 text-[11px] text-slate-400 z-20">
        <span>© 2026 OBEPath AI • Outcome-Based Education Platform</span>
        <div className="flex items-center space-x-4">
          <button
            type="button"
            onClick={() => handleNavigateLegal('/privacy')}
            className="hover:text-slate-600 underline cursor-pointer"
          >
            Privacy Policy
          </button>
          <button
            type="button"
            onClick={() => handleNavigateLegal('/terms')}
            className="hover:text-slate-600 underline cursor-pointer"
          >
            Terms of Service
          </button>
          <span className="hidden sm:inline">Autonomous Closed-Loop Learning System</span>
        </div>
      </footer>

      {/* Google OAuth Modal */}
      <GoogleAuthModal
        isOpen={googleModalOpen}
        onClose={() => setGoogleModalOpen(false)}
        onGoogleSuccess={handleGoogleSuccess}
        loading={googleLoading}
      />
    </div>
  );
};
