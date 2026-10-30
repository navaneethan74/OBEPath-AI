import React, { useState } from 'react';
import {
  ShieldAlert,
  Lock,
  Mail,
  Eye,
  EyeOff,
  AlertCircle,
  CheckCircle2,
  ArrowLeft
} from 'lucide-react';
import { api } from '../services/api';
import { User } from '../types';

interface AdminLoginPageProps {
  onAuthSuccess: (user: User, isNewUser?: boolean, onboardingCompleted?: boolean) => void;
  onNavigateHome?: () => void;
}

export const AdminLoginPage: React.FC<AdminLoginPageProps> = ({
  onAuthSuccess,
  onNavigateHome
}) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);

    const emailClean = email.trim().toLowerCase();
    const passClean = password.trim();

    if (!emailClean || !passClean) {
      setError('Please provide both administrator email and password.');
      return;
    }

    setLoading(true);

    try {
      // Sends expected_role: 'admin' to enforce server-side role gating
      const res = await api.login(emailClean, passClean, 'admin', 'admin');

      // Double-check role; if not admin, clear token and reject
      if (res.user.role !== 'admin') {
        api.logout();
        setError('These credentials are not valid for this portal');
        setPassword('');
        return;
      }

      setSuccessMsg(`Administrator credentials verified. Access granted to ${res.user.full_name}.`);
      setTimeout(() => {
        onAuthSuccess(res.user, false, true);
        if (typeof window !== 'undefined' && window.history) {
          window.history.replaceState({}, '', '/');
        }
      }, 700);
    } catch (err: any) {
      console.error('Admin authentication error:', err);
      // Uniform generic error message for role mismatch or authentication failure
      setError(err.message || 'These credentials are not valid for this portal');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen bg-[#070B19] text-slate-100 flex items-center justify-center p-4 sm:p-6 overflow-hidden selection:bg-rose-500/30 selection:text-rose-200">
      {/* Background ambient security perimeter glow */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-[25%] -left-[10%] w-[500px] h-[500px] rounded-full bg-rose-950/20 blur-[120px]" />
        <div className="absolute -bottom-[20%] -right-[10%] w-[600px] h-[600px] rounded-full bg-indigo-950/25 blur-[140px]" />
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: `radial-gradient(circle at 1px 1px, #ffffff 1px, transparent 0)`,
            backgroundSize: '24px 24px'
          }}
        />
      </div>

      <div className="relative w-full max-w-[440px] z-10">
        {/* Security Card */}
        <div className="bg-[#0D1527]/90 backdrop-blur-xl rounded-3xl p-7 sm:p-9 border border-rose-900/30 shadow-[0_25px_70px_-15px_rgba(0,0,0,0.7)] flex flex-col">
          {/* Header Icon & Title */}
          <div className="flex flex-col items-center text-center mb-7">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-rose-600 to-rose-900 p-0.5 shadow-lg shadow-rose-900/40 mb-4 flex items-center justify-center">
              <div className="w-full h-full bg-[#0E172C] rounded-2xl flex items-center justify-center">
                <ShieldAlert className="w-7 h-7 text-rose-400" />
              </div>
            </div>

            <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-rose-950/60 border border-rose-800/40 text-[11px] font-semibold text-rose-300 tracking-wider uppercase mb-2">
              <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse" />
              <span>Restricted Security Zone</span>
            </div>

            <h1 className="text-2xl sm:text-2xl font-bold tracking-tight text-white mt-1">
              Admin Portal
            </h1>
            <p className="text-xs text-slate-400 mt-1.5 max-w-xs leading-relaxed">
              Institutional administrative access only. All authorization attempts are monitored and rate-limited.
            </p>
          </div>

          {/* Feedback Messages */}
          {error && (
            <div
              id="admin-login-error"
              className="mb-5 p-3.5 bg-rose-950/50 border border-rose-800/60 rounded-xl text-xs text-rose-200 flex items-start space-x-2.5 animate-fadeIn"
            >
              <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
              <span className="leading-snug">{error}</span>
            </div>
          )}

          {successMsg && (
            <div
              id="admin-login-success"
              className="mb-5 p-3.5 bg-emerald-950/50 border border-emerald-800/60 rounded-xl text-xs text-emerald-200 flex items-start space-x-2.5 animate-fadeIn"
            >
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
              <span className="leading-snug font-medium">{successMsg}</span>
            </div>
          )}

          {/* Strict Admin Form: Email + Password Only (No Signup, No Google) */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label
                htmlFor="admin-email"
                className="block text-xs font-semibold text-slate-300 mb-1.5 tracking-wide"
              >
                Administrator Email
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                  <Mail className="w-4 h-4" />
                </div>
                <input
                  id="admin-email"
                  type="email"
                  autoComplete="username"
                  required
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    if (error) setError(null);
                  }}
                  placeholder="admin@institution.edu"
                  className="w-full pl-10 pr-4 py-3 bg-[#0A1020] border border-slate-700/80 rounded-xl text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-rose-500/40 focus:border-rose-500 transition-all"
                />
              </div>
            </div>

            <div>
              <label
                htmlFor="admin-password"
                className="block text-xs font-semibold text-slate-300 mb-1.5 tracking-wide"
              >
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  id="admin-password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    if (error) setError(null);
                  }}
                  placeholder="••••••••••••"
                  className="w-full pl-10 pr-11 py-3 bg-[#0A1020] border border-slate-700/80 rounded-xl text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-rose-500/40 focus:border-rose-500 transition-all font-mono"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-500 hover:text-slate-300 transition-colors cursor-pointer"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <div className="pt-2">
              <button
                id="admin-submit-btn"
                type="submit"
                disabled={loading}
                className="w-full py-3.5 px-4 bg-gradient-to-r from-rose-600 to-rose-700 hover:from-rose-500 hover:to-rose-600 text-white text-sm font-bold rounded-xl shadow-lg shadow-rose-900/30 hover:shadow-rose-900/50 active:scale-[0.99] transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2 cursor-pointer"
              >
                {loading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                    <span>Verifying Credentials...</span>
                  </>
                ) : (
                  <span>Authenticate Administrator</span>
                )}
              </button>
            </div>
          </form>

          {/* Footer note & subtle return */}
          <div className="mt-6 pt-5 border-t border-slate-800/80 text-center">
            <p className="text-[11px] text-slate-500">
              OBEPath Central Security Subsystem • v2.6.4
            </p>
            {onNavigateHome && (
              <button
                type="button"
                onClick={onNavigateHome}
                className="mt-3 inline-flex items-center text-xs text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
              >
                <ArrowLeft className="w-3.5 h-3.5 mr-1" />
                Return to public portal
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
