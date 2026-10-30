import React, { useState, useEffect } from 'react';
import {
  AlertTriangle,
  Layers,
  Users,
  RefreshCw,
  AlertCircle,
  Sparkles,
  ChevronRight,
  ShieldAlert,
  ArrowRight
} from 'lucide-react';
import { api } from '../services/api';
import {
  ClassGapsResponse,
  ConceptGapItem,
  PrerequisiteGapItem,
  CommonClassGapItem
} from '../types';
import { GapDrilldownModal } from './GapDrilldownModal';

interface FacultyLearningGapsTabProps {
  classId: number;
  onSelectStudent?: (studentId: number) => void;
}

export const FacultyLearningGapsTab: React.FC<FacultyLearningGapsTabProps> = ({
  classId,
  onSelectStudent
}) => {
  const [data, setData] = useState<ClassGapsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Drilldown modal state
  const [activeDrilldownKey, setActiveDrilldownKey] = useState<string | null>(null);
  const [activeDrilldownTitle, setActiveDrilldownTitle] = useState<string | undefined>(undefined);

  useEffect(() => {
    if (classId) {
      loadGaps();
    }
  }, [classId]);

  const loadGaps = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getClassGaps(classId);
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to load class learning gaps.');
    } finally {
      setLoading(false);
    }
  };

  const openDrilldown = (gapKey: string, title: string) => {
    setActiveDrilldownKey(gapKey);
    setActiveDrilldownTitle(title);
  };

  if (loading) {
    return (
      <div className="py-24 text-center space-y-3 bg-white rounded-2xl border border-slate-200 p-8 shadow-xs">
        <RefreshCw className="w-8 h-8 animate-spin mx-auto text-[#635BFF]" />
        <p className="text-xs text-slate-500 font-medium">Analyzing Class Concept & Prerequisite Gaps...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-rose-50 border border-rose-200 rounded-2xl text-rose-700 flex items-start space-x-3">
        <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
        <div className="space-y-1">
          <p className="text-xs font-bold">Failed to load learning gaps analysis</p>
          <p className="text-xs">{error}</p>
          <button
            onClick={loadGaps}
            className="mt-2 text-xs font-semibold underline hover:text-rose-900"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const commonGaps = data?.common_class_gaps || [];
  const conceptGaps = data?.concept_gaps || [];
  const prereqGaps = data?.prerequisite_gaps || [];
  const thresholds = data?.thresholds || {
    ASSESSMENT_PASS: 60.0,
    PREREQ_UNLOCK: 60.0,
    COMMON_GAP_PCT: 25.0
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* 1. Highlighted "Common Class Gaps" Card */}
      <div className="p-6 bg-gradient-to-br from-amber-50/70 via-white to-purple-50/40 border border-amber-200/80 rounded-2xl shadow-xs space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center space-x-2">
            <span className="p-2 bg-amber-100 rounded-xl text-amber-700">
              <ShieldAlert className="w-5 h-5" />
            </span>
            <div>
              <h3 className="text-sm font-bold text-slate-900 flex items-center space-x-2">
                <span>Common Class Gaps (Cohort Priority)</span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800">
                  Affecting ≥ {thresholds.COMMON_GAP_PCT}% of class
                </span>
              </h3>
              <p className="text-xs text-slate-500">
                Pervasive learning hurdles requiring targeted faculty lecture review or remedial workshop sessions.
              </p>
            </div>
          </div>
          <span className="text-xs font-mono font-bold text-amber-800 bg-amber-100/70 px-3 py-1 rounded-lg">
            {commonGaps.length} Pervasive {commonGaps.length === 1 ? 'Gap' : 'Gaps'}
          </span>
        </div>

        {commonGaps.length === 0 ? (
          <div className="p-6 bg-white/80 border border-emerald-100 rounded-xl text-center space-y-1">
            <span className="text-xs font-bold text-emerald-800 block">
              No Common Gaps Exceeding {thresholds.COMMON_GAP_PCT}% of Class
            </span>
            <span className="text-[11px] text-slate-500">
              The cohort has no widespread conceptual bottlenecks or blocked prerequisites above the threshold.
            </span>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {commonGaps.map((gap, i) => {
              const isConcept = gap.gap_type === 'concept';
              const title = isConcept
                ? (gap as ConceptGapItem).concept
                : `${(gap as PrerequisiteGapItem).prereq_topic_title} → ${(gap as PrerequisiteGapItem).dependent_topic_title}`;
              return (
                <div
                  key={i}
                  onClick={() => openDrilldown(gap.gap_key, title)}
                  className="p-4 bg-white border border-amber-200/80 hover:border-[#635BFF] rounded-xl shadow-xs transition-all cursor-pointer group hover:shadow-md space-y-2"
                >
                  <div className="flex items-start justify-between">
                    <span
                      className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md ${
                        isConcept ? 'bg-purple-100 text-[#635BFF]' : 'bg-rose-100 text-rose-700'
                      }`}
                    >
                      {isConcept ? 'Concept Gap' : 'Prereq Block'}
                    </span>
                    <span className="font-mono text-xs font-extrabold text-rose-600">
                      {gap.pct_students_affected}% affected
                    </span>
                  </div>
                  <h4 className="text-xs font-bold text-slate-900 group-hover:text-[#635BFF] transition-colors line-clamp-2">
                    {title}
                  </h4>
                  <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1 border-t border-slate-100">
                    <span>{gap.students_affected_count} of {data?.total_students} students</span>
                    <span className="text-[#635BFF] font-semibold flex items-center space-x-0.5">
                      <span>View Roster</span>
                      <ChevronRight className="w-3.5 h-3.5" />
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* 2. Concept-Level Gaps (Ranked with struggle bars) */}
      <div className="bg-white border border-[#E2E8F0] rounded-2xl shadow-xs overflow-hidden">
        <div className="p-5 border-b border-slate-100 flex flex-wrap items-center justify-between gap-2">
          <div className="space-y-0.5">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center space-x-2">
              <Layers className="w-4 h-4 text-[#635BFF]" />
              <span>Ranked Concept Gaps (Accuracy Below {thresholds.ASSESSMENT_PASS}%)</span>
            </h3>
            <p className="text-xs text-slate-500">
              Evaluated from granular question-level sub-concept accuracy histories across all assessment attempts.
            </p>
          </div>
          <span className="text-xs font-mono text-slate-400">
            {conceptGaps.length} concepts evaluated
          </span>
        </div>

        {conceptGaps.length === 0 ? (
          <div className="py-12 text-center text-slate-400 text-xs">
            No concept gaps identified. All concept accuracies exceed {thresholds.ASSESSMENT_PASS}%.
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {conceptGaps.map((cg) => (
              <div
                key={cg.gap_key}
                onClick={() => openDrilldown(cg.gap_key, `Concept: ${cg.concept}`)}
                className="p-4 hover:bg-slate-50/80 transition-colors cursor-pointer group flex flex-wrap items-center justify-between gap-4"
              >
                <div className="space-y-1 max-w-md w-full">
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-xs text-slate-900 group-hover:text-[#635BFF] transition-colors">
                      {cg.concept}
                    </span>
                    {cg.is_common_gap && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800">
                        Common Gap
                      </span>
                    )}
                  </div>
                  <span className="text-[11px] text-slate-500 block">
                    Target Topic: {cg.topic_title} • {cg.attempts_count} question responses
                  </span>

                  {/* Struggle Bar */}
                  <div className="space-y-1 pt-1">
                    <div className="flex items-center justify-between text-[10px] font-mono text-slate-400">
                      <span>Struggle Share ({cg.pct_students_affected}% of class)</span>
                      <span>Avg Score: {cg.avg_score}%</span>
                    </div>
                    <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${
                          cg.pct_students_affected >= thresholds.COMMON_GAP_PCT
                            ? 'bg-rose-500'
                            : 'bg-amber-500'
                        }`}
                        style={{ width: `${Math.min(100, cg.pct_students_affected)}%` }}
                      />
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-4">
                  <div className="text-right">
                    <span className="font-mono text-xs font-bold text-slate-900 block">
                      {cg.students_affected_count} Students
                    </span>
                    <span className="text-[11px] text-rose-600 font-semibold block">
                      Below {thresholds.ASSESSMENT_PASS}% Pass
                    </span>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      openDrilldown(cg.gap_key, `Concept: ${cg.concept}`);
                    }}
                    className="p-2 hover:bg-slate-200/70 rounded-xl text-slate-400 group-hover:text-[#635BFF] transition-colors"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 3. Prerequisite Gaps (Prerequisite -> Dependent Blocked) */}
      <div className="bg-white border border-[#E2E8F0] rounded-2xl shadow-xs overflow-hidden">
        <div className="p-5 border-b border-slate-100 flex flex-wrap items-center justify-between gap-2">
          <div className="space-y-0.5">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-amber-500" />
              <span>Prerequisite Deficits (Blocked Dependent Topics)</span>
            </h3>
            <p className="text-xs text-slate-500">
              Students whose prerequisite topic mastery is under {thresholds.PREREQ_UNLOCK}% and are therefore blocked from advancing.
            </p>
          </div>
          <span className="text-xs font-mono text-slate-400">
            {prereqGaps.length} dependency paths
          </span>
        </div>

        {prereqGaps.length === 0 ? (
          <div className="py-12 text-center text-slate-400 text-xs">
            No prerequisite gaps found. Enrolled students satisfy all prerequisite unlocks.
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {prereqGaps.map((pg) => (
              <div
                key={pg.gap_key}
                onClick={() => openDrilldown(pg.gap_key, `${pg.prereq_topic_title} → ${pg.dependent_topic_title}`)}
                className="p-4 hover:bg-slate-50/80 transition-colors cursor-pointer group flex flex-wrap items-center justify-between gap-4"
              >
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200 font-mono">
                      {pg.prereq_topic_code}
                    </span>
                    <span className="font-bold text-xs text-slate-900 group-hover:text-[#635BFF] transition-colors">
                      {pg.prereq_topic_title}
                    </span>
                    <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700 font-mono">
                      {pg.dependent_topic_code}
                    </span>
                    <span className="text-xs text-slate-600 font-medium">
                      Blocks: {pg.dependent_topic_title}
                    </span>
                    {pg.is_common_gap && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800">
                        Common Gap
                      </span>
                    )}
                  </div>
                  <span className="text-[11px] text-slate-500 block">
                    Unlock Threshold: {pg.required_mastery}% prerequisite mastery required
                  </span>
                </div>

                <div className="flex items-center space-x-4">
                  <div className="text-right">
                    <span className="font-mono text-xs font-bold text-rose-600 block">
                      {pg.students_affected_count} Blocked ({pg.pct_students_affected}%)
                    </span>
                    <span className="text-[10px] text-slate-400 block font-mono">
                      &lt; {pg.required_mastery}% mastery
                    </span>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      openDrilldown(pg.gap_key, `${pg.prereq_topic_title} → ${pg.dependent_topic_title}`);
                    }}
                    className="p-2 hover:bg-slate-200/70 rounded-xl text-slate-400 group-hover:text-[#635BFF] transition-colors"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Drilldown Modal */}
      {activeDrilldownKey && (
        <GapDrilldownModal
          isOpen={true}
          onClose={() => {
            setActiveDrilldownKey(null);
            setActiveDrilldownTitle(undefined);
          }}
          classId={classId}
          gapKey={activeDrilldownKey}
          gapTitle={activeDrilldownTitle}
          onSelectStudent={onSelectStudent}
        />
      )}
    </div>
  );
};
