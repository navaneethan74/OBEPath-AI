import React from 'react';
import { X, Calculator, CheckCircle2, AlertTriangle, Sparkles } from 'lucide-react';

interface FormulaModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const FormulaModal: React.FC<FormulaModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs animate-fadeIn">
      <div className="relative w-full max-w-xl bg-white border border-[#E2E8F0] rounded-2xl shadow-xl p-6 overflow-hidden">
        <div className="flex items-center justify-between pb-4 border-b border-slate-100">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-orange-50 text-orange-600 rounded-xl border border-orange-100">
              <Calculator className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900">How Topic Mastery is Calculated</h3>
              <p className="text-xs text-slate-500">Transparent Outcome-Based Education (OBE) formula</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="mt-5 space-y-5">
          {/* Formula Card */}
          <div className="p-4 bg-[#FAF8F5] border border-orange-200 rounded-xl shadow-xs">
            <div className="text-xs font-bold uppercase tracking-wider text-orange-600 mb-1.5">Mastery Formula</div>
            <div className="text-sm font-mono font-semibold text-slate-900">
              Mastery = <span className="text-orange-600 font-bold">40%</span> Diagnostic + <span className="text-amber-600 font-bold">30%</span> Latest Quiz + <span className="text-emerald-600 font-bold">20%</span> Practice + <span className="text-slate-600 font-bold">10%</span> Completion
            </div>
          </div>

          {/* Technical Representation G=(V,E) matching User Blueprint */}
          <div className="p-4 bg-[#F8FAFC] border border-slate-200 rounded-xl space-y-2 text-xs font-mono text-slate-800">
            <div className="flex items-center justify-between pb-1 border-b border-slate-200">
              <span className="font-bold text-orange-600">Technical Graph Representation: G = (V, E)</span>
              <span className="text-[10px] text-slate-400">Formal Model</span>
            </div>
            <div className="space-y-1 text-[11px]">
              <div><strong>V</strong> = set of learning concepts</div>
              <div><strong>E</strong> = prerequisite relationships between concepts</div>
              <div><strong>Kt</strong> = learner's knowledge state at time t</div>
              <div><strong>Mt(v)</strong> = mastery score of concept v</div>
              <div className="p-2 bg-amber-50 border border-amber-200 rounded-lg text-amber-900 font-semibold">
                If: <strong>Mt(v) &lt; 60% (Threshold)</strong> ➔ treated as a <strong>learning gap</strong>.
                <br />
                System checks prerequisite concepts (E) and updates learning path.
              </div>
            </div>
          </div>

          {/* Component weights */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
            <div className="p-3 bg-[#FAF8F5] rounded-xl border border-slate-200 text-center">
              <div className="text-xs text-slate-500 font-medium">Diagnostic</div>
              <div className="text-lg font-bold text-orange-600 mt-1">40%</div>
              <div className="text-[10px] text-slate-400">Initial readiness</div>
            </div>
            <div className="p-3 bg-[#FAF8F5] rounded-xl border border-slate-200 text-center">
              <div className="text-xs text-slate-500 font-medium">Latest Quiz</div>
              <div className="text-lg font-bold text-amber-600 mt-1">30%</div>
              <div className="text-[10px] text-slate-400">Recent check</div>
            </div>
            <div className="p-3 bg-[#FAF8F5] rounded-xl border border-slate-200 text-center">
              <div className="text-xs text-slate-500 font-medium">Practice</div>
              <div className="text-lg font-bold text-emerald-600 mt-1">20%</div>
              <div className="text-[10px] text-slate-400">Coding accuracy</div>
            </div>
            <div className="p-3 bg-[#FAF8F5] rounded-xl border border-slate-200 text-center">
              <div className="text-xs text-slate-500 font-medium">Completion</div>
              <div className="text-lg font-bold text-slate-700 mt-1">10%</div>
              <div className="text-[10px] text-slate-400">Lesson finished</div>
            </div>
          </div>

          {/* Classification Tiers */}
          <div>
            <div className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Mastery Classifications</div>
            <div className="space-y-2">
              <div className="flex items-center justify-between p-2.5 bg-emerald-50 border border-emerald-200 rounded-lg text-xs">
                <div className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span className="font-semibold text-emerald-800">Mastered</span>
                </div>
                <span className="font-mono font-bold text-emerald-700">80% – 100%</span>
              </div>
              <div className="flex items-center justify-between p-2.5 bg-orange-50 border border-orange-200 rounded-lg text-xs">
                <div className="flex items-center space-x-2">
                  <Sparkles className="w-4 h-4 text-orange-600" />
                  <span className="font-semibold text-orange-900">Proficient</span>
                </div>
                <span className="font-mono font-bold text-orange-700">60% – 79%</span>
              </div>
              <div className="flex items-center justify-between p-2.5 bg-amber-50 border border-amber-200 rounded-lg text-xs">
                <div className="flex items-center space-x-2">
                  <AlertTriangle className="w-4 h-4 text-amber-600" />
                  <span className="font-semibold text-amber-800">Developing</span>
                </div>
                <span className="font-mono font-bold text-amber-700">40% – 59%</span>
              </div>
              <div className="flex items-center justify-between p-2.5 bg-rose-50 border border-rose-200 rounded-lg text-xs">
                <div className="flex items-center space-x-2">
                  <AlertTriangle className="w-4 h-4 text-rose-600" />
                  <span className="font-semibold text-rose-800">Needs Improvement</span>
                </div>
                <span className="font-mono font-bold text-rose-700">0% – 39%</span>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-6 pt-4 border-t border-slate-100 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg text-xs font-semibold shadow-xs shadow-orange-500/20 transition-colors"
          >
            Got it
          </button>
        </div>
      </div>
    </div>
  );
};
