import React from 'react';
import {
  Brain,
  Award,
  ArrowRight,
  Compass,
  Repeat,
  UserCheck,
  Layers,
  Sparkles,
  Route,
  FileCheck2,
  AlertTriangle,
  RotateCcw,
  CheckCircle2
} from 'lucide-react';

interface LandingPageProps {
  onGetStarted: () => void;
  onLogin: () => void;
  onCreateAccount: () => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({
  onGetStarted,
  onLogin,
  onCreateAccount
}) => {
  const lifecycleSteps = [
    { num: '01', label: 'Diagnose', color: 'bg-cream-100 text-orange-800 border-orange-200' },
    { num: '02', label: 'Analyze', color: 'bg-orange-50 text-orange-700 border-orange-200' },
    { num: '03', label: 'Personalize', color: 'bg-orange-50 text-orange-700 border-orange-200' },
    { num: '04', label: 'Learn', color: 'bg-mint-50 text-emerald-700 border-emerald-200' },
    { num: '05', label: 'Assess', color: 'bg-amber-50 text-amber-700 border-amber-200' },
    { num: '06', label: 'Monitor', color: 'bg-slate-50 text-slate-700 border-slate-200' },
    { num: '07', label: 'Adapt', color: 'bg-orange-50 text-orange-700 border-orange-200' },
    { num: '08', label: 'Measure Outcomes', color: 'bg-emerald-50 text-emerald-700 border-emerald-200' }
  ];

  const pipelineStages = [
    {
      title: 'Learner Profile',
      desc: 'Baseline diagnostics & cognitive pace modeling',
      icon: UserCheck,
      badge: 'Step 1',
      color: 'text-slate-700 bg-slate-50 border-slate-200',
      active: true
    },
    {
      title: 'Course Outcomes',
      desc: 'Accreditation CO1–CO4 syllabus node mapping',
      icon: Layers,
      badge: 'Step 2',
      color: 'text-orange-700 bg-orange-50 border-orange-200',
      active: true
    },
    {
      title: 'AI Agent',
      desc: 'Autonomous multi-factor planning & pedagogical decisions',
      icon: Brain,
      badge: 'Core Engine',
      color: 'text-orange-700 bg-orange-50 border-orange-200',
      highlight: true,
      active: true
    },
    {
      title: 'Personalized Learning Path',
      desc: 'Dynamically sequenced prerequisite trajectory',
      icon: Route,
      badge: 'Step 4',
      color: 'text-emerald-700 bg-emerald-50 border-emerald-200',
      active: true
    },
    {
      title: 'Assessment',
      desc: 'Formative verification & real-time mastery calculation',
      icon: FileCheck2,
      badge: 'Step 5',
      color: 'text-pink-600 bg-pink-50 border-pink-200',
      active: true
    },
    {
      title: 'Gap Detection',
      desc: 'Prerequisite error analysis & misconception tracing',
      icon: AlertTriangle,
      badge: 'Step 6',
      color: 'text-amber-600 bg-amber-50 border-amber-200',
      active: true
    },
    {
      title: 'Path Adaptation',
      desc: 'Remediation insertion & closed-loop trajectory re-routing',
      icon: RotateCcw,
      badge: 'Step 7',
      color: 'text-emerald-600 bg-emerald-50 border-emerald-200',
      active: true
    }
  ];

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-slate-900 flex flex-col justify-between selection:bg-orange-100 selection:text-orange-900 font-sans">
      {/* Subtle background glow */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1100px] h-[350px] bg-gradient-to-b from-orange-100/30 via-amber-50/15 to-transparent blur-3xl" />
      </div>

      {/* Header */}
      <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-[#E2E8F0] shadow-[0_1px_3px_0_rgba(15,23,42,0.03)]">
        <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 h-[68px] flex items-center justify-between">
          {/* Logo & Identity */}
          <div className="flex items-center space-x-3.5">
            <div className="p-2.5 bg-orange-600 rounded-xl text-white shadow-xs flex items-center justify-center">
              <Brain className="w-5 h-5" />
            </div>
            <div>
              <div className="text-base sm:text-lg font-bold tracking-tight text-slate-900 flex items-center space-x-2">
                <span>AI Learning Path Generator</span>
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 bg-orange-50 text-orange-700 border border-orange-200 rounded-md">
                  OBE
                </span>
              </div>
              <p className="text-xs text-slate-500 font-normal">Personalized Learning System</p>
            </div>
          </div>

          {/* Header Action Buttons */}
          <div className="flex items-center space-x-3">
            <button
              onClick={onLogin}
              className="px-4 py-2 text-sm font-semibold text-slate-700 hover:text-slate-900 hover:bg-slate-100 rounded-xl transition-colors cursor-pointer"
            >
              Sign In
            </button>

            <button
              onClick={onGetStarted}
              className="px-4 sm:px-5 py-2 sm:py-2.5 text-sm font-semibold bg-orange-600 hover:bg-orange-700 text-white rounded-xl shadow-xs hover:shadow transition-all flex items-center space-x-1.5 cursor-pointer"
            >
              <span>Get Started</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      {/* Hero Section: 2-Column Responsive Layout */}
      <main className="flex-1 max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-10 sm:py-14 relative z-10 w-full space-y-12">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-12 items-center">
          {/* LEFT COLUMN: Badge, Headline, Description, CTAs */}
          <div className="lg:col-span-7 space-y-6 text-left">
            {/* Small badge */}
            <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 bg-orange-50 border border-orange-200 rounded-full text-xs font-semibold text-orange-700">
              <span className="w-2 h-2 rounded-full bg-orange-500" />
              <span>A Generative AI and AI-Agent-Based Personalized Learning System</span>
            </div>

            {/* Main Hero Headline (42-48px desktop scale) */}
            <h1 className="text-[32px] sm:text-[38px] lg:text-[46px] font-extrabold text-slate-900 tracking-tight leading-[1.12]">
              AI Learning Path Generator for{' '}
              <span className="text-orange-600">
                Outcome-Based Education
              </span>
            </h1>

            {/* Subtitle */}
            <p className="text-base sm:text-[17px] text-slate-600 leading-relaxed max-w-2xl font-normal">
              Transform course outcomes into personalized, measurable learning journeys powered by multi-agent pedagogical intelligence.
            </p>

            {/* Primary Action Buttons */}
            <div className="pt-2 flex flex-wrap items-center gap-3.5">
              <button
                onClick={onCreateAccount}
                className="px-6 py-3.5 bg-orange-600 hover:bg-orange-700 text-white rounded-xl text-sm sm:text-base font-semibold shadow-xs hover:shadow transition-all flex items-center space-x-2 cursor-pointer"
              >
                <span>Create Free Account</span>
                <ArrowRight className="w-4 h-4" />
              </button>

              <button
                onClick={onLogin}
                className="px-6 py-3.5 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 hover:border-slate-300 rounded-xl text-sm sm:text-base font-semibold shadow-xs transition-all flex items-center space-x-2 cursor-pointer"
              >
                <span>Sign In to Dashboard</span>
              </button>
            </div>
          </div>

          {/* RIGHT COLUMN: Connected 7-Stage AI Learning-Path Preview Card */}
          <div className="lg:col-span-5 relative">
            {/* Subtle Floating AI Badge */}
            <div className="absolute -top-3.5 -right-2 sm:right-3 z-20 px-3.5 py-1.5 bg-white border border-orange-200 rounded-full shadow-sm flex items-center space-x-2 text-xs font-bold text-orange-700">
              <Sparkles className="w-3.5 h-3.5 text-orange-600" />
              <span>Autonomous AI Pipeline</span>
            </div>

            {/* White Preview Card */}
            <div className="bg-white border border-[#E2E8F0] rounded-2xl p-5 sm:p-6 shadow-[0_4px_24px_rgba(15,23,42,0.06)] relative overflow-hidden">
              <div className="flex items-center justify-between pb-3.5 mb-4 border-b border-slate-100">
                <div className="flex items-center space-x-2">
                  <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                    Closed-Loop Adaptive Pipeline
                  </span>
                </div>
                <span className="text-[11px] font-semibold text-slate-400">
                  OBE Engine v2.0
                </span>
              </div>

              {/* 7 Connected Stages */}
              <div className="space-y-1.5">
                {pipelineStages.map((stage, idx) => {
                  const Icon = stage.icon;
                  return (
                    <React.Fragment key={stage.title}>
                      <div
                        className={`p-2.5 rounded-xl border transition-all flex items-center justify-between ${
                          stage.highlight
                            ? 'bg-[#F8FAFC] border-orange-300 shadow-xs'
                            : 'bg-white border-slate-200 hover:border-slate-300'
                        }`}
                      >
                        <div className="flex items-center space-x-3">
                          <div className={`p-1.5 rounded-lg border flex-shrink-0 ${stage.color}`}>
                            <Icon className="w-3.5 h-3.5" />
                          </div>
                          <div>
                            <div className="text-xs font-bold text-slate-900 leading-tight flex items-center space-x-1.5">
                              <span>{stage.title}</span>
                              {stage.highlight && (
                                <span className="text-[9px] px-1.5 py-0.2 bg-orange-50 text-orange-700 font-bold rounded">
                                  Planner
                                </span>
                              )}
                            </div>
                            <div className="text-[11px] text-slate-500 leading-tight">
                              {stage.desc}
                            </div>
                          </div>
                        </div>

                        <div className="flex-shrink-0 pl-2">
                          <span className="text-[10px] font-mono font-semibold text-slate-400 px-2 py-0.5 bg-slate-50 border border-slate-100 rounded-md">
                            {stage.badge}
                          </span>
                        </div>
                      </div>

                      {/* Thin connector line between stages */}
                      {idx < pipelineStages.length - 1 && (
                        <div className="flex justify-center py-0.5">
                          <div className="w-0.5 h-2 bg-orange-200" />
                        </div>
                      )}
                    </React.Fragment>
                  );
                })}
              </div>
            </div>
          </div>
        </div>

        {/* Process Timeline */}
        <div className="pt-4">
          <div className="p-5 sm:p-6 bg-white border border-[#E2E8F0] rounded-2xl max-w-5xl mx-auto shadow-[0_2px_12px_rgba(15,23,42,0.03)]">
            <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-100">
              <div className="flex items-center space-x-2">
                <Repeat className="w-4 h-4 text-orange-600" />
                <span className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  Continuous OBE Closed-Loop Adaptation Lifecycle
                </span>
              </div>
              <span className="text-xs text-slate-500 font-medium hidden sm:inline-block">
                Automated Pedagogical Feedback Loop
              </span>
            </div>

            {/* Seamless horizontal grid of 8 lifecycle stages */}
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2">
              {lifecycleSteps.map((step) => (
                <div
                  key={step.label}
                  className={`px-2.5 py-2.5 rounded-xl border ${step.color} flex flex-col items-center justify-center text-center transition-all hover:scale-[1.02] bg-white`}
                >
                  <span className="text-[10px] font-mono font-bold opacity-75">{step.num}</span>
                  <span className="text-xs font-semibold leading-tight mt-0.5">{step.label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>


        {/* 3 Core Architecture Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-16">
          {/* Card 1 */}
          <div className="p-7 bg-white border border-[#E2E8F0] rounded-2xl shadow-[0_4px_20px_rgba(15,23,42,0.04)] hover:shadow-md transition-all">
            <div className="w-11 h-11 rounded-xl bg-orange-50 text-orange-600 flex items-center justify-center mb-5 border border-orange-100">
              <Compass className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 mb-2">Dynamic Learning Paths</h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              Every student receives a personalized learning path dynamically sequenced by an autonomous Planner Agent based on baseline diagnostics and prerequisite graphs.
            </p>
          </div>

          {/* Card 2 */}
          <div className="p-7 bg-white border border-[#E2E8F0] rounded-2xl shadow-[0_4px_20px_rgba(15,23,42,0.04)] hover:shadow-md transition-all">
            <div className="w-11 h-11 rounded-xl bg-mint-50 text-emerald-600 flex items-center justify-center mb-5 border border-emerald-100">
              <Brain className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 mb-2">AI Pedagogical Tutor</h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              Generative AI and specialized monitoring agents provide scaffolded code explanations, interactive hints, targeted practice, and instant remediation.
            </p>
          </div>

          {/* Card 3 */}
          <div className="p-7 bg-white border border-[#E2E8F0] rounded-2xl shadow-[0_4px_20px_rgba(15,23,42,0.04)] hover:shadow-md transition-all">
            <div className="w-11 h-11 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center mb-5 border border-amber-100">
              <Award className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 mb-2">Outcome-Based Education</h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              Track student progress against measurable Course Outcomes (CO1–CO4) with transparent mathematical mastery formulas and syllabus evidence attribution.
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-[#E2E8F0] py-8 bg-white">
        <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 text-center text-xs text-slate-500 space-y-2">
          <p className="font-semibold text-slate-700">
            AI Learning Path Generator for Outcome-Based Education (OBE) • College Engineering Prototype
          </p>
          <p className="text-slate-500 max-w-2xl mx-auto leading-relaxed">
            Educational support system adhering to ethical AI safety guidelines: clearly labeled AI-generated learning support with human-in-the-loop faculty review.
          </p>
        </div>
      </footer>
    </div>
  );
};
