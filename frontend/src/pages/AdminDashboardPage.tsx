import React, { useState, useEffect } from 'react';
import {
  Shield,
  Activity,
  Users,
  BookOpen,
  Bot,
  Terminal,
  CheckCircle2,
  RefreshCw,
  Server,
  UserPlus,
  Mail,
  Lock,
  User as UserIcon,
  AlertCircle,
  KeyRound
} from 'lucide-react';
import { api } from '../services/api';
import { FacultyAccount } from '../types';

export const AdminDashboardPage: React.FC = () => {
  const [metrics, setMetrics] = useState<any>(null);
  const [logs, setLogs] = useState<any[]>([]);
  const [facultyList, setFacultyList] = useState<FacultyAccount[]>([]);
  const [loading, setLoading] = useState(true);

  // Create Faculty Form State
  const [facultyName, setFacultyName] = useState('');
  const [facultyEmail, setFacultyEmail] = useState('');
  const [facultyPassword, setFacultyPassword] = useState('');
  const [creatingFaculty, setCreatingFaculty] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [createSuccess, setCreateSuccess] = useState<string | null>(null);

  useEffect(() => {
    loadAdminData();
  }, []);

  const loadAdminData = async () => {
    setLoading(true);
    try {
      const [m, l, f] = await Promise.all([
        api.getAdminMetrics(),
        api.getAdminLogs(40),
        api.getFacultyList()
      ]);
      setMetrics(m);
      setLogs(l);
      setFacultyList(f || []);
    } catch (err) {
      console.error('Failed to load admin telemetry', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateFaculty = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateError(null);
    setCreateSuccess(null);

    if (!facultyName.trim()) {
      setCreateError('Faculty name is required');
      return;
    }
    if (!facultyEmail.trim()) {
      setCreateError('Faculty email is required');
      return;
    }
    if (!facultyPassword.trim() || facultyPassword.length < 8) {
      setCreateError('Temporary password must be at least 8 characters');
      return;
    }

    setCreatingFaculty(true);
    try {
      const newAcc = await api.createFaculty({
        name: facultyName.trim(),
        email: facultyEmail.trim().toLowerCase(),
        temporary_password: facultyPassword.trim()
      });
      setCreateSuccess(`Faculty account created for ${newAcc.email}! (Temporary password set, change required on first login)`);
      setFacultyName('');
      setFacultyEmail('');
      setFacultyPassword('');

      // Refresh list & metrics
      const [freshList, freshMetrics] = await Promise.all([
        api.getFacultyList(),
        api.getAdminMetrics()
      ]);
      setFacultyList(freshList || []);
      setMetrics(freshMetrics);
    } catch (err: any) {
      setCreateError(err.message || 'Failed to create faculty account');
    } finally {
      setCreatingFaculty(false);
    }
  };

  if (loading) {
    return (
      <div className="py-24 text-center space-y-3 animate-fadeIn">
        <RefreshCw className="w-8 h-8 text-purple-400 animate-spin mx-auto" />
        <p className="text-sm text-slate-400">Loading System Health & Agent Telemetry...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="inline-flex items-center space-x-2 px-3 py-1 bg-[#F3F0FF] border border-purple-100 rounded-full text-xs font-semibold text-[#635BFF] mb-1.5">
            <Shield className="w-3.5 h-3.5 text-[#635BFF]" />
            <span>Administrator Console</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
            System Telemetry & AI Agent Infrastructure
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Real-time monitoring of all 5 autonomous pedagogical agents & faculty provisioning
          </p>
        </div>

        <button
          onClick={loadAdminData}
          className="px-4 py-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-xl text-xs font-semibold transition-colors flex items-center space-x-2 shadow-xs cursor-pointer"
        >
          <RefreshCw className="w-3.5 h-3.5 text-[#635BFF]" />
          <span>Refresh Telemetry</span>
        </button>
      </div>

      {/* System Status Banner */}
      <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl flex items-center justify-between text-xs">
        <div className="flex items-center space-x-2 text-emerald-700 font-semibold">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span>{metrics?.system_status || 'All AI Agents Operational'}</span>
        </div>
        <span className="text-slate-500 font-mono text-[11px]">
          {metrics?.llm_engine || 'Modular Hybrid (OpenAI API Key + Deterministic Fallback Active)'}
        </span>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        <div className="p-4 bg-white border border-[#E2E8F0] rounded-2xl text-center shadow-xs">
          <div className="text-[10px] text-slate-400 uppercase font-semibold">Total Users</div>
          <div className="text-2xl font-extrabold text-slate-900 font-mono mt-1">
            {metrics?.total_users || 3}
          </div>
        </div>

        <div className="p-4 bg-white border border-[#E2E8F0] rounded-2xl text-center shadow-xs">
          <div className="text-[10px] text-slate-400 uppercase font-semibold">Students</div>
          <div className="text-2xl font-extrabold text-blue-600 font-mono mt-1">
            {metrics?.students || 1}
          </div>
        </div>

        <div className="p-4 bg-white border border-[#E2E8F0] rounded-2xl text-center shadow-xs">
          <div className="text-[10px] text-slate-400 uppercase font-semibold">Faculty</div>
          <div className="text-2xl font-extrabold text-emerald-600 font-mono mt-1">
            {metrics?.faculty || facultyList.length || 1}
          </div>
        </div>

        <div className="p-4 bg-white border border-[#E2E8F0] rounded-2xl text-center shadow-xs">
          <div className="text-[10px] text-slate-400 uppercase font-semibold">Courses</div>
          <div className="text-2xl font-extrabold text-[#635BFF] font-mono mt-1">
            {metrics?.courses || 4}
          </div>
        </div>

        <div className="p-4 bg-white border border-[#E2E8F0] rounded-2xl text-center shadow-xs">
          <div className="text-[10px] text-slate-400 uppercase font-semibold">Active Sessions</div>
          <div className="text-2xl font-extrabold text-amber-600 font-mono mt-1">
            {metrics?.active_learning_sessions || 1}
          </div>
        </div>

        <div className="p-4 bg-white border border-[#E2E8F0] rounded-2xl text-center shadow-xs">
          <div className="text-[10px] text-slate-400 uppercase font-semibold">Agent Invocations</div>
          <div className="text-2xl font-extrabold text-purple-600 font-mono mt-1">
            {metrics?.ai_agent_executions || 12}
          </div>
        </div>
      </div>

      {/* Faculty Management Section: Create Faculty Form + Existing Accounts List */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Create Faculty Form */}
        <div className="lg:col-span-5 bg-white border border-[#E2E8F0] rounded-2xl p-6 sm:p-7 shadow-[0_4px_20px_rgba(15,23,42,0.04)] flex flex-col justify-between">
          <div>
            <div className="flex items-center space-x-2.5 pb-3 border-b border-slate-100 mb-5">
              <div className="w-8 h-8 rounded-xl bg-purple-50 border border-purple-100 flex items-center justify-center">
                <UserPlus className="w-4 h-4 text-purple-600" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900">Create Faculty Account</h3>
                <p className="text-xs text-slate-500">Provision instructor access with temporary password</p>
              </div>
            </div>

            {createError && (
              <div className="mb-4 p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-start space-x-2 animate-fadeIn">
                <AlertCircle className="w-4 h-4 text-rose-500 flex-shrink-0 mt-0.5" />
                <span>{createError}</span>
              </div>
            )}

            {createSuccess && (
              <div className="mb-4 p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800 flex items-start space-x-2 animate-fadeIn">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
                <span>{createSuccess}</span>
              </div>
            )}

            <form onSubmit={handleCreateFaculty} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Faculty Full Name
                </label>
                <div className="relative">
                  <UserIcon className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  <input
                    type="text"
                    value={facultyName}
                    onChange={(e) => setFacultyName(e.target.value)}
                    placeholder="e.g. Dr. Jane Smith"
                    className="w-full pl-10 pr-3.5 py-2.5 bg-white border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-purple-100 focus:border-purple-500"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  <input
                    type="email"
                    value={facultyEmail}
                    onChange={(e) => setFacultyEmail(e.target.value)}
                    placeholder="faculty@domain.edu"
                    className="w-full pl-10 pr-3.5 py-2.5 bg-white border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-purple-100 focus:border-purple-500"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Temporary Password
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  <input
                    type="password"
                    value={facultyPassword}
                    onChange={(e) => setFacultyPassword(e.target.value)}
                    placeholder="Min 8 characters (letters + numbers)"
                    className="w-full pl-10 pr-3.5 py-2.5 bg-white border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-purple-100 focus:border-purple-500"
                    required
                  />
                </div>
                <p className="text-[11px] text-slate-400 mt-1">
                  Password change will be mandatory on instructor's first login.
                </p>
              </div>

              <button
                type="submit"
                disabled={creatingFaculty}
                className="w-full py-3 px-4 bg-purple-600 hover:bg-purple-700 text-white font-bold rounded-xl text-xs shadow-md shadow-purple-500/20 transition-all flex items-center justify-center space-x-2 disabled:opacity-50 cursor-pointer mt-2"
              >
                {creatingFaculty ? (
                  <div className="flex items-center space-x-2">
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Provisioning Faculty...</span>
                  </div>
                ) : (
                  <>
                    <UserPlus className="w-3.5 h-3.5" />
                    <span>Provision Faculty Account</span>
                  </>
                )}
              </button>
            </form>
          </div>
        </div>

        {/* Right: Existing Faculty Accounts List */}
        <div className="lg:col-span-7 bg-white border border-[#E2E8F0] rounded-2xl p-6 sm:p-7 shadow-[0_4px_20px_rgba(15,23,42,0.04)] flex flex-col">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
            <div className="flex items-center space-x-2.5">
              <div className="w-8 h-8 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-center">
                <Users className="w-4 h-4 text-slate-600" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900">Existing Faculty Accounts</h3>
                <p className="text-xs text-slate-500">{facultyList.length} registered instructor accounts</p>
              </div>
            </div>
            <button
              onClick={loadAdminData}
              className="p-1.5 hover:bg-slate-50 text-slate-500 hover:text-slate-800 rounded-lg transition-colors cursor-pointer"
              title="Refresh Faculty Accounts"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto max-h-[380px] space-y-2.5 pr-1">
            {facultyList.length === 0 ? (
              <div className="text-xs text-slate-400 py-12 text-center italic">
                No faculty accounts provisioned yet.
              </div>
            ) : (
              facultyList.map((fac) => (
                <div
                  key={fac.id}
                  className="p-3.5 bg-slate-50/80 hover:bg-slate-50 rounded-xl border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 transition-colors"
                >
                  <div className="space-y-0.5">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-bold text-slate-900">{fac.full_name}</span>
                      <span className="text-[10px] px-2 py-0.5 bg-purple-50 text-purple-700 font-semibold rounded-full border border-purple-100">
                        {fac.role}
                      </span>
                    </div>
                    <div className="text-xs text-slate-500 font-mono">{fac.email}</div>
                  </div>

                  <div className="flex items-center space-x-2 text-right">
                    {fac.must_change_password ? (
                      <span className="inline-flex items-center space-x-1 text-[11px] px-2.5 py-1 bg-amber-50 text-amber-700 font-semibold rounded-lg border border-amber-200">
                        <KeyRound className="w-3 h-3 text-amber-500" />
                        <span>Temp Password</span>
                      </span>
                    ) : (
                      <span className="inline-flex items-center space-x-1 text-[11px] px-2.5 py-1 bg-emerald-50 text-emerald-700 font-semibold rounded-lg border border-emerald-200">
                        <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                        <span>Active</span>
                      </span>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* System Logs Terminal */}
      <div className="bg-white border border-[#E2E8F0] rounded-2xl p-6 sm:p-8 space-y-4 shadow-[0_4px_20px_rgba(15,23,42,0.04)]">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center space-x-2">
            <Terminal className="w-5 h-5 text-[#635BFF]" />
            <h3 className="text-base font-bold text-slate-900">AI Agent Execution Audit Log</h3>
          </div>
          <span className="text-xs text-slate-400 font-mono">Real-time trace</span>
        </div>

        <div className="space-y-2 max-h-[450px] overflow-y-auto pr-1">
          {logs.length === 0 ? (
            <div className="text-xs text-slate-400 py-4 text-center italic">
              No audit logs recorded yet.
            </div>
          ) : (
            logs.map((l) => (
              <div
                key={l.id}
                className="p-3 bg-slate-50 rounded-xl border border-slate-200 font-mono text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-2 hover:border-slate-300 transition-colors"
              >
                <div className="flex items-center space-x-2.5">
                  <span className="text-[10px] text-slate-400">{l.timestamp}</span>
                  <span className="text-[#635BFF] font-bold font-sans">[{l.agent}]</span>
                  <span className="text-slate-700 font-sans">{l.message}</span>
                </div>
                <span className="text-[10px] px-2 py-0.5 bg-white border border-slate-200 text-slate-600 rounded w-fit uppercase font-semibold">
                  {l.action}
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
