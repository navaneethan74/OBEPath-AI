import React from 'react';
import { Shield, FileText, ArrowLeft, CheckCircle2, Lock, Eye, Trash2, AlertTriangle } from 'lucide-react';

interface LegalPageProps {
  type: 'privacy' | 'terms';
  onNavigateHome: () => void;
  onSwitchType: (type: 'privacy' | 'terms') => void;
}

export const LegalPage: React.FC<LegalPageProps> = ({
  type,
  onNavigateHome,
  onSwitchType
}) => {
  const isPrivacy = type === 'privacy';

  return (
    <div className="min-h-screen bg-[#FAF8F5] text-slate-900 py-10 px-4 sm:px-6 lg:px-8 selection:bg-orange-100 selection:text-orange-900">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Navigation & Tab Toggle */}
        <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-200">
          <button
            onClick={onNavigateHome}
            className="inline-flex items-center space-x-2 text-xs font-semibold text-slate-600 hover:text-slate-900 bg-white border border-slate-200 px-3 py-1.5 rounded-xl shadow-xs transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Return to Home</span>
          </button>

          <div className="flex items-center space-x-2 bg-slate-100 p-1 rounded-xl text-xs font-semibold">
            <button
              onClick={() => onSwitchType('privacy')}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                isPrivacy
                  ? 'bg-white text-slate-900 shadow-xs'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              Privacy Policy
            </button>
            <button
              onClick={() => onSwitchType('terms')}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                !isPrivacy
                  ? 'bg-white text-slate-900 shadow-xs'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              Terms of Service
            </button>
          </div>
        </div>

        {/* Institutional Template Notice */}
        <div className="p-4 bg-amber-50 border border-amber-200 rounded-2xl flex items-start space-x-3 text-xs text-amber-900">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 text-amber-600 mt-0.5" />
          <div className="space-y-1">
            <p className="font-bold">Institutional Review Notice (Template Document)</p>
            <p className="text-amber-800 leading-relaxed">
              This document represents an operational baseline for OBEPath AI. Each deploying educational institution
              should review, customize, and ratify these terms with their respective legal, academic registry,
              and data protection governance authorities before campus-wide production rollout.
            </p>
          </div>
        </div>

        {/* Main Content Card */}
        <div className="bg-white border border-[#E2E8F0] rounded-2xl p-6 sm:p-10 shadow-[0_4px_20px_rgba(15,23,42,0.04)] space-y-8">
          {/* Header */}
          <div className="space-y-2 pb-6 border-b border-slate-100">
            <div className="inline-flex items-center space-x-2 px-3 py-1 bg-orange-50 border border-orange-200 rounded-full text-xs font-semibold text-orange-600">
              {isPrivacy ? <Shield className="w-3.5 h-3.5" /> : <FileText className="w-3.5 h-3.5" />}
              <span>{isPrivacy ? 'Student Data Governance' : 'Academic Platform Rules'}</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              {isPrivacy ? 'OBEPath AI Privacy Policy' : 'OBEPath AI Terms of Service'}
            </h1>
            <p className="text-xs text-slate-500 font-mono">
              Last Updated: October 2026 • Platform Version 1.0.0 (Production)
            </p>
          </div>

          {isPrivacy ? (
            /* PRIVACY POLICY CONTENT */
            <div className="space-y-6 text-sm text-slate-700 leading-relaxed">
              <section className="space-y-2">
                <h2 className="text-base font-bold text-slate-900 flex items-center space-x-2">
                  <span className="w-1.5 h-4 bg-orange-500 rounded-full" />
                  <span>1. What Data We Collect & Store</span>
                </h2>
                <p>
                  To provide an autonomous closed-loop learning trajectory, OBEPath stores minimal academic and platform interaction data:
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 text-xs">
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-1">
                    <span className="font-bold text-slate-900 block">Personal Profile</span>
                    <p className="text-slate-600">Full name, academic email address, department, semester, and self-reported learning goals.</p>
                  </div>
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-1">
                    <span className="font-bold text-slate-900 block">Academic Progress</span>
                    <p className="text-slate-600">Topic mastery percentages, prerequisite unlock states, and Course Outcome (CO1–CO4) attainment vectors.</p>
                  </div>
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-1">
                    <span className="font-bold text-slate-900 block">Assessment Evidence</span>
                    <p className="text-slate-600">Diagnostic attempts, practice quiz answers, and in-browser coding test execution results.</p>
                  </div>
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-1">
                    <span className="font-bold text-slate-900 block">AI Tutor Logs</span>
                    <p className="text-slate-600">Interaction queries with the pedagogical tutor to identify persistent knowledge gaps and adapt explanations.</p>
                  </div>
                </div>
              </section>

              <section className="space-y-2">
                <h2 className="text-base font-bold text-slate-900 flex items-center space-x-2">
                  <span className="w-1.5 h-4 bg-orange-500 rounded-full" />
                  <span>2. Who Can See Your Data</span>
                </h2>
                <div className="p-4 bg-emerald-50/70 border border-emerald-200 rounded-xl space-y-2 text-xs text-emerald-950">
                  <div className="flex items-center space-x-2 font-bold text-emerald-900">
                    <Eye className="w-4 h-4 text-emerald-600" />
                    <span>Strict Academic Oversight Isolation</span>
                  </div>
                  <p>
                    <strong>Your progress is private by default.</strong> Other students can never view your scores, mastery, or submissions.
                  </p>
                  <p>
                    When you explicitly enter a <strong>Class Code</strong> and provide consent to join an instructor's cohort, that specific verified teacher gains read-only access to view your course progress, attainment delta, and gap analytics to provide pedagogical support.
                  </p>
                  <p>
                    If you choose to leave a class, the teacher's view access is revoked immediately.
                  </p>
                </div>
              </section>

              <section className="space-y-2">
                <h2 className="text-base font-bold text-slate-900 flex items-center space-x-2">
                  <span className="w-1.5 h-4 bg-orange-500 rounded-full" />
                  <span>3. In-Browser Code Execution Safety</span>
                </h2>
                <p className="text-xs">
                  Hands-on Python coding exercises execute entirely client-side inside a sandboxed WebAssembly (Pyodide) Web Worker in your local browser.
                  No untrusted code is executed on central application servers.
                </p>
              </section>

              <section className="space-y-2">
                <h2 className="text-base font-bold text-slate-900 flex items-center space-x-2">
                  <span className="w-1.5 h-4 bg-orange-500 rounded-full" />
                  <span>4. Account Deletion & Right to Erasure</span>
                </h2>
                <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2 text-xs text-slate-800">
                  <div className="flex items-center space-x-2 font-bold text-slate-900">
                    <Trash2 className="w-4 h-4 text-rose-600" />
                    <span>How to Request Account & Data Deletion</span>
                  </div>
                  <p>
                    Students may request permanent deletion of their account, personal profile, and learning history at any time.
                  </p>
                  <p>
                    To submit a formal deletion request, authenticated students can make an account deletion request via student settings or by submitting an authenticated request to <code>POST /api/student/account-deletion-request</code>. The request will be reviewed and completed by the system administrator in accordance with institutional records retention schedules.
                  </p>
                </div>
              </section>
            </div>
          ) : (
            /* TERMS OF SERVICE CONTENT */
            <div className="space-y-6 text-sm text-slate-700 leading-relaxed">
              <section className="space-y-2">
                <h2 className="text-base font-bold text-slate-900 flex items-center space-x-2">
                  <span className="w-1.5 h-4 bg-orange-500 rounded-full" />
                  <span>1. Academic Integrity & Honor Code</span>
                </h2>
                <p>
                  OBEPath AI is an Outcome-Based Education tool designed for learning reinforcement, conceptual mastery, and prerequisite remediation.
                  Users agree to:
                </p>
                <ul className="list-disc pl-5 space-y-1 text-xs text-slate-600">
                  <li>Complete diagnostic and practice assessments independently to reflect authentic cognitive readiness.</li>
                  <li>Refrain from automated scripting, reverse engineering of test case parameters, or submitting malicious payloads to code compilers.</li>
                  <li>Use the AI Tutor for conceptual guidance and problem formulation rather than unauthorized examination assistance.</li>
                </ul>
              </section>

              <section className="space-y-2">
                <h2 className="text-base font-bold text-slate-900 flex items-center space-x-2">
                  <span className="w-1.5 h-4 bg-orange-500 rounded-full" />
                  <span>2. Role-Based Access & Account Security</span>
                </h2>
                <p className="text-xs">
                  Student accounts are provisioned exclusively for individual academic use. Faculty and administrator accounts are restricted to institutional staff. Users are responsible for safeguarding their login credentials and must immediately report any suspected unauthorized access.
                </p>
              </section>

              <section className="space-y-2">
                <h2 className="text-base font-bold text-slate-900 flex items-center space-x-2">
                  <span className="w-1.5 h-4 bg-orange-500 rounded-full" />
                  <span>3. Disclaimer of Warranty</span>
                </h2>
                <p className="text-xs">
                  While OBEPath AI employs rigorous pedagogical heuristics (Bloom's Taxonomy, prerequisite DAG mapping, and adaptive testing), automated recommendations do not supersede direct faculty instruction or formal institutional degree requirements.
                </p>
              </section>
            </div>
          )}

          {/* Footer CTA */}
          <div className="pt-6 border-t border-slate-100 flex items-center justify-between text-xs">
            <span className="text-slate-400">Questions? Contact your institution's OBEPath administrator.</span>
            <button
              onClick={onNavigateHome}
              className="px-4 py-2 bg-[#EA580C] hover:bg-[#C2410C] text-white rounded-xl font-semibold shadow-xs transition-colors"
            >
              Back to Sign In
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
