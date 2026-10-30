import React from 'react';
import { X, HelpCircle, ShieldCheck, Target, Award } from 'lucide-react';

interface WhyRecommendationModalProps {
  isOpen: boolean;
  onClose: () => void;
  data: {
    topic_title: string;
    mastery_score: number;
    prerequisites: string[];
    outcomes: string[];
    explanation: string;
  } | null;
}

export const WhyRecommendationModal: React.FC<WhyRecommendationModalProps> = ({
  isOpen,
  onClose,
  data
}) => {
  if (!isOpen || !data) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/20 backdrop-blur-xs animate-fadeIn">
      <div className="relative w-full max-w-lg bg-white border border-[#E2E8F0] rounded-2xl shadow-xl p-6 overflow-hidden">
        <div className="flex items-center justify-between pb-4 border-b border-slate-100">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-orange-50 text-orange-600 rounded-xl border border-orange-200">
              <HelpCircle className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900">Why Was This Recommended?</h3>
              <p className="text-xs text-slate-500">Explainable AI (XAI) Pedagogical Reasoning</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="mt-5 space-y-4">
          <div className="p-4 bg-[#F8FAFC] border border-slate-200 rounded-xl">
            <div className="text-xs text-slate-500 font-medium">Target Topic</div>
            <div className="text-xl font-bold text-slate-900 mt-0.5">{data.topic_title}</div>
            <div className="flex items-center space-x-3 mt-2">
              <span className="text-xs px-2.5 py-1 bg-white text-slate-700 rounded-md border border-slate-200 shadow-xs">
                Current Mastery: <strong className="text-orange-600 font-mono">{Math.round(data.mastery_score)}%</strong>
              </span>
              <span className="text-xs px-2.5 py-1 bg-orange-50 text-orange-600 rounded-md border border-orange-200">
                Outcome: <strong>{data.outcomes.join(', ') || 'Core'}</strong>
              </span>
            </div>
          </div>

          <div className="p-4 bg-orange-50/70 border border-orange-200 rounded-xl">
            <div className="flex items-center space-x-2 text-xs font-bold text-orange-600 uppercase tracking-wider mb-2">
              <ShieldCheck className="w-4 h-4" />
              <span>Planner Agent Justification</span>
            </div>
            <p className="text-sm text-slate-800 leading-relaxed italic">
              "{data.explanation}"
            </p>
          </div>

          {data.prerequisites && data.prerequisites.length > 0 && (
            <div className="p-3.5 bg-[#F8FAFC] rounded-xl border border-slate-200 text-xs">
              <div className="text-slate-600 font-semibold mb-1 flex items-center space-x-1.5">
                <Target className="w-3.5 h-3.5 text-amber-600" />
                <span>Prerequisites Analyzed</span>
              </div>
              <p className="text-slate-600">
                {data.prerequisites.join(', ')}
              </p>
            </div>
          )}

          <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center space-x-3 text-xs text-emerald-800">
            <Award className="w-4 h-4 text-emerald-600 flex-shrink-0" />
            <span>Mastering this topic directly contributes to attainment of <strong>{data.outcomes.join(', ')}</strong>.</span>
          </div>
        </div>

        <div className="mt-6 pt-4 border-t border-slate-100 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-[#EA580C] hover:bg-[#C2410C] text-white rounded-lg text-xs font-semibold shadow-sm transition-colors"
          >
            Understood
          </button>
        </div>
      </div>
    </div>
  );
};
