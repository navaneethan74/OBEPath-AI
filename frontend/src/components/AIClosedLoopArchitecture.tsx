import React from 'react';
import {
  UserCheck,
  Compass,
  Layers,
  Brain,
  Sparkles,
  Route,
  FileCheck2,
  AlertTriangle,
  Wrench,
  RotateCcw,
  ArrowRight,
  Repeat
} from 'lucide-react';

interface AIClosedLoopArchitectureProps {
  currentStage?: number;
  className?: string;
  onNavigateToStage?: (tab: string) => void;
}

export const AIClosedLoopArchitecture: React.FC<AIClosedLoopArchitectureProps> = ({
  className = ''
}) => {
  const steps = [
    {
      id: 1,
      title: 'Learner Input',
      type: 'input',
      desc: 'Academic baseline, learning speed, preferred formats & daily time goals',
      icon: UserCheck,
      color: 'blue'
    },
    {
      id: 2,
      title: 'Learner Profiling',
      type: 'input',
      desc: 'Cognitive state modeling, prerequisite verification & readiness mapping',
      icon: Compass,
      color: 'blue'
    },
    {
      id: 3,
      title: 'Course Outcome & Concept Mapping',
      type: 'mapping',
      desc: 'Accreditation CO1-CO4 syllabus alignment & knowledge graph nodes',
      icon: Layers,
      color: 'indigo'
    },
    {
      id: 4,
      title: 'AI Agent — Planning & Decision',
      type: 'ai-agent',
      desc: 'Autonomous multi-factor pedagogical planning, decision trees, gap analysis & trajectory adaptation',
      icon: Brain,
      color: 'cyan',
      highlight: true,
      roleBadge: 'AI Agent (Planning & Decision)'
    },
    {
      id: 5,
      title: 'Generative AI — Content & Resource Generation',
      type: 'gen-ai',
      desc: 'Real-time synthesis of scaffolded code explanations, interactive hints, targeted examples & question sets',
      icon: Sparkles,
      color: 'orange',
      highlight: true,
      roleBadge: 'Generative AI (Content Generation)'
    },
    {
      id: 6,
      title: 'Personalized Learning Path',
      type: 'path',
      desc: 'Dynamic prerequisite-governed pedagogical roadmap with unlockable milestones',
      icon: Route,
      color: 'indigo'
    },
    {
      id: 7,
      title: 'Assessment',
      type: 'assessment',
      desc: 'Adaptive multi-format evaluation assessing conceptual, algorithmic & tracing mastery',
      icon: FileCheck2,
      color: 'cyan'
    },
    {
      id: 8,
      title: 'Gap Detection',
      type: 'diagnosis',
      desc: 'Pinpointing sub-concept weaknesses and prerequisite regressions',
      icon: AlertTriangle,
      color: 'amber'
    },
    {
      id: 9,
      title: 'Learning Path Repair',
      type: 'repair',
      desc: 'Inserting remediation modules and prerequisite reinforcement steps',
      icon: Wrench,
      color: 'amber'
    },
    {
      id: 10,
      title: 'Progress Monitoring & Path Adaptation',
      type: 'monitor',
      desc: 'Continuous real-time evidence tracking feeding back into the AI Agent Planner',
      icon: RotateCcw,
      color: 'emerald',
      loopsBack: true
    }
  ];

  return (
    <div className={`p-6 sm:p-7 bg-white border border-[#E2E8F0] rounded-2xl shadow-[0_4px_20px_rgba(15,23,42,0.04)] relative overflow-hidden ${className}`}>
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-5 border-b border-slate-100">
        <div>
          <div className="inline-flex items-center space-x-2 px-3 py-1 bg-orange-50 border border-orange-200 rounded-full text-xs font-semibold text-orange-600 mb-2">
            <Repeat className="w-3.5 h-3.5 text-orange-600" />
            <span>Autonomous Pedagogical Closed-Loop Engine</span>
          </div>
          <h3 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
            System Architecture & Adaptive AI Workflow
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Continuous Closed Loop: Progress Monitoring feeds dynamic evidence back to the AI Agent Planner
          </p>
        </div>

        {/* 9-stage lifecycle pill sequence */}
        <div className="flex items-center space-x-1 px-3 py-1.5 bg-[#FAF8F5] border border-slate-200 rounded-xl text-[11px] font-medium text-slate-600">
          <span className="text-orange-600 font-bold">Closed Loop:</span>
          <span>Diagnose</span>
          <span className="text-slate-400">→</span>
          <span>Analyze</span>
          <span className="text-slate-400">→</span>
          <span>Personalize</span>
          <span className="text-slate-400">→</span>
          <span>Learn</span>
          <span className="text-slate-400">→</span>
          <span>Assess</span>
          <span className="text-slate-400">→</span>
          <span>Monitor</span>
          <span className="text-slate-400">→</span>
          <span className="text-emerald-700 font-bold">Adapt Again ⟲</span>
        </div>
      </div>

      {/* Architecture Visual Grid / Loop */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-3 relative">
        {steps.map((step) => {
          const Icon = step.icon;
          const isAgent = step.type === 'ai-agent';
          const isGenAI = step.type === 'gen-ai';
          const isLoopBack = step.loopsBack;

          return (
            <div
              key={step.id}
              className={`p-4 rounded-xl border transition-all relative flex flex-col justify-between ${
                isAgent
                  ? 'bg-amber-50/40 border-amber-300'
                  : isGenAI
                  ? 'bg-orange-50/60 border-orange-300'
                  : isLoopBack
                  ? 'bg-emerald-50/50 border-emerald-300'
                  : 'bg-[#FAF8F5] border-slate-200 hover:border-slate-300'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-white border border-slate-200 text-slate-600">
                    Step {String(step.id).padStart(2, '0')}
                  </span>
                  <div
                    className={`p-1.5 rounded-lg ${
                      isAgent
                        ? 'bg-amber-100 text-amber-700'
                        : isGenAI
                        ? 'bg-orange-100 text-orange-600'
                        : isLoopBack
                        ? 'bg-emerald-100 text-emerald-700'
                        : 'bg-white text-slate-700 border border-slate-200'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                  </div>
                </div>

                {step.roleBadge && (
                  <span
                    className={`inline-block text-[9px] uppercase tracking-wider font-bold px-2 py-0.5 rounded-md mb-2 ${
                      isAgent
                        ? 'bg-amber-100 text-amber-800 border border-amber-200'
                        : 'bg-orange-100 text-orange-800 border border-orange-200'
                    }`}
                  >
                    {step.roleBadge}
                  </span>
                )}

                <h4 className="text-xs font-bold text-slate-900 tracking-tight leading-snug mb-1">
                  {step.title}
                </h4>
                <p className="text-[11px] text-slate-500 leading-relaxed">
                  {step.desc}
                </p>
              </div>

              {/* Next arrow indicator */}
              <div className="mt-3 pt-2 border-t border-slate-200/70 flex items-center justify-between text-[10px] text-slate-500 font-mono">
                {isLoopBack ? (
                  <span className="text-emerald-700 font-bold flex items-center space-x-1">
                    <Repeat className="w-3 h-3" />
                    <span>Loops to Step 04</span>
                  </span>
                ) : (
                  <span className="flex items-center space-x-1 text-slate-400">
                    <span>Next</span>
                    <ArrowRight className="w-3 h-3 text-orange-600" />
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Closed loop visual feedback connector banner */}
      <div className="mt-4 p-3.5 bg-emerald-50/70 border border-emerald-200 rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs text-emerald-900">
        <div className="flex items-center space-x-2">
          <Repeat className="w-4 h-4 text-emerald-600 flex-shrink-0" />
          <span className="font-bold">Closed-Loop Guarantee:</span>
          <span className="text-emerald-800">
            Step 10 (Progress Monitoring & Path Adaptation) evaluates mastery delta and recalculates Course Outcomes, looping dynamic feedback back into Step 04 (AI Agent Planner).
          </span>
        </div>
        <span className="self-start sm:self-auto px-2.5 py-1 bg-white border border-emerald-300 text-emerald-800 rounded-md font-mono text-[10px] font-bold shadow-xs">
          Continuous Adaptation Active
        </span>
      </div>

      {/* Technical Representation G=(V,E) Box (Diagram 1) */}
      <div className="mt-3 p-4 bg-[#FAF8F5] border border-slate-200 rounded-xl space-y-2 text-xs font-mono text-slate-800">
        <div className="flex items-center justify-between pb-1.5 border-b border-slate-200">
          <div className="flex items-center space-x-2">
            <span className="font-bold text-orange-600">Technical Graph Representation</span>
            <span className="text-[10px] text-slate-500 font-sans">Formal Mathematical Engine</span>
          </div>
          <span className="px-2 py-0.5 bg-orange-100 text-orange-700 rounded text-[10px] font-bold">
            G = (V, E)
          </span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1 text-[11px]">
          <div className="space-y-1">
            <div><strong className="text-slate-900">G = (V, E)</strong></div>
            <div className="text-slate-600 pl-2">where:</div>
            <div className="pl-4"><strong>V</strong> = set of learning concepts</div>
            <div className="pl-4"><strong>E</strong> = prerequisite relationships between concepts</div>
          </div>
          <div className="space-y-1">
            <div><strong className="text-slate-900">Kt</strong> = learner's knowledge state at time t</div>
            <div>For a concept <strong>v</strong>, let: <strong>Mt(v)</strong> = mastery score of concept v</div>
            <div className="p-2 bg-amber-50 border border-amber-200 rounded-lg text-amber-900 font-semibold text-[11px] mt-1">
              If: <strong>Mt(v) &lt; threshold</strong> ➔ treated as learning gap.
              <br />
              Checks prerequisite concepts and updates the learning path.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
