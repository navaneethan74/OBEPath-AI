import React, { useState } from 'react';
import { Award, CheckCircle2, AlertTriangle, Layers, ChevronRight } from 'lucide-react';
import { OutcomeAttainment } from '../types';
import { useStudentLearning } from '../context/StudentLearningContext';

interface OBEDashboardPageProps {
  outcomes?: OutcomeAttainment[];
  overallAttainment?: number;
}

export const OBEDashboardPage: React.FC<OBEDashboardPageProps> = ({
  outcomes: propOutcomes,
  overallAttainment: propOverall
}) => {
  const { studentState, activeCourse } = useStudentLearning();
  const courseTitle = studentState?.enrolledCourse?.title || activeCourse?.title || 'Selected Course';
  const courseCode = studentState?.enrolledCourse?.code || activeCourse?.code || '';

  // Prefer central persistent student state
  const rawOutcomes = studentState?.courseOutcomeAttainment || propOutcomes || [];
  const overallAttainment = studentState ? Math.round(studentState.overallOBEAttainment) : (propOverall ?? 53);

  // Normalize outcomes for rendering
  const outcomes = rawOutcomes.map((co: any) => ({
    outcome_id: co.outcome_id || co.id,
    code: co.code,
    description: co.description,
    target_pct: co.target_pct || 70,
    attainment_percentage: Math.round(co.attainment_percentage || 0),
    status: co.status || (co.attainment_percentage >= (co.target_pct || 70) ? 'Achieved' : 'In Progress'),
    contributing_topics: co.contributing_topics || [],
    weak_areas: co.weak_areas || [],
    remediation:
      co.remediation ||
      (co.attainment_percentage >= (co.target_pct || 70)
        ? 'Outcome threshold achieved. Continuous progression active.'
        : 'Review foundational prerequisite modules to satisfy accreditation target.'),
    evidence: co.evidence || {
      contributing_topics_count: (co.contributing_topics || []).length || 3,
      average_topic_mastery: Math.round(co.attainment_percentage || 0),
      target_threshold_met: (co.attainment_percentage || 0) >= (co.target_pct || 70)
    }
  }));

  const [selectedOutcome, setSelectedOutcome] = useState<any>(
    outcomes.find((o: any) => o.code === 'CO2') || outcomes[0] || null
  );

  const activeSelected = selectedOutcome
    ? (outcomes.find((o: any) => o.code === selectedOutcome.code) || selectedOutcome)
    : (outcomes[0] || null);

  const getStatusBadge = (status: string, attainment: number, target: number) => {
    if (attainment >= target) {
      return (
        <span className="text-[11px] font-semibold px-2.5 py-0.5 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-full">
          Mastered
        </span>
      );
    }
    if (attainment >= 50) {
      return (
        <span className="text-[11px] font-semibold px-2.5 py-0.5 bg-orange-50 text-orange-600 border border-orange-200 rounded-full">
          Developing
        </span>
      );
    }
    return (
      <span className="text-[11px] font-semibold px-2.5 py-0.5 bg-amber-50 text-amber-700 border border-amber-200 rounded-full">
        Needs Improvement
      </span>
    );
  };

  const targetMet = overallAttainment >= 70;

  return (
    <div className="space-y-6">
      {/* 1. Header & OVERALL OBE ATTAINMENT */}
      <div className="bg-white border border-[#E2E8F0] rounded-2xl p-6 shadow-[0_4px_20px_rgba(15,23,42,0.04)] space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div>
            <div className="inline-flex items-center space-x-2 px-3 py-1 bg-orange-50 border border-orange-200 rounded-full text-xs font-semibold text-orange-600 mb-1.5">
              <Award className="w-3.5 h-3.5 text-orange-600" />
              <span>Accreditation & Curriculum Outcome Assessment</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
              Outcome Attainment Dashboard
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Real-time aggregation of student evidence across Course Outcomes in {courseTitle} {courseCode ? `(${courseCode})` : ''}
            </p>
          </div>

          <div className="p-4 bg-[#F8FAFC] rounded-xl border border-slate-200 flex items-center space-x-5 shadow-xs">
            <div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                OVERALL OBE ATTAINMENT
              </div>
              <div className="text-2xl sm:text-3xl font-bold text-orange-600 mt-0.5">
                {overallAttainment}%
              </div>
            </div>

            <div className="pl-4 border-l border-slate-200 space-y-1">
              <div className="text-xs font-bold text-slate-900">
                Institutional Target: <span className="text-orange-600">70%</span>
              </div>
              <div className="flex items-center space-x-1.5 text-xs">
                {targetMet ? (
                  <span className="text-emerald-700 font-semibold flex items-center space-x-1">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    <span>Target Satisfied</span>
                  </span>
                ) : (
                  <span className="text-amber-700 font-semibold flex items-center space-x-1">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                    <span>Gap: {70 - overallAttainment}% below target</span>
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Visual Target Attainment Progress */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs text-slate-500 font-medium">
            <span>Overall Attainment Progress against Institutional Target (70%)</span>
            <span className="font-bold text-slate-900">{overallAttainment}% / 100%</span>
          </div>
          <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden relative">
            {/* 70% threshold marker */}
            <div
              className="absolute top-0 bottom-0 w-0.5 bg-slate-400 z-10"
              style={{ left: '70%' }}
              title="Institutional Target 70%"
            />
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                targetMet ? 'bg-emerald-500' : 'bg-orange-500'
              }`}
              style={{ width: `${Math.min(overallAttainment, 100)}%` }}
            />
          </div>
        </div>
      </div>

      {/* 2. Grid of 4 Course Outcomes (CO1, CO2, CO3, CO4) */}
      <div>
        <div className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3 flex items-center space-x-2">
          <Layers className="w-4 h-4 text-orange-600" />
          <span>Course Outcomes Attainment Matrix (CO1 - CO4)</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {outcomes.map((co: any) => {
            const isSelected = activeSelected?.code === co.code;
            const isMet = co.attainment_percentage >= co.target_pct;

            return (
              <div
                key={co.code}
                onClick={() => setSelectedOutcome(co)}
                className={`p-5 rounded-2xl border cursor-pointer transition-all flex flex-col justify-between ${
                  isSelected
                    ? 'bg-white border-2 border-orange-500 shadow-[0_4px_20px_rgba(234,88,12,0.08)]'
                    : 'bg-white border border-[#E2E8F0] shadow-xs hover:border-slate-300'
                }`}
              >
                <div>
                  {/* Code & Status */}
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-mono font-bold px-2 py-0.5 bg-orange-50 text-orange-600 rounded-md border border-orange-200">
                      {co.code}
                    </span>
                    {getStatusBadge(co.status, co.attainment_percentage, co.target_pct)}
                  </div>

                  {/* Description */}
                  <div className="text-xs text-slate-700 font-medium line-clamp-3 mb-3 leading-relaxed">
                    {co.description}
                  </div>
                </div>

                {/* Current % vs Target % and Progress Bar */}
                <div className="pt-3 border-t border-slate-100 space-y-2">
                  <div className="flex items-baseline justify-between text-xs">
                    <span className="text-slate-500 text-[11px]">
                      Target: <strong className="text-slate-800 font-mono">{co.target_pct}%</strong>
                    </span>
                    <span className="font-bold text-lg text-slate-900">
                      {co.attainment_percentage}%
                    </span>
                  </div>

                  {/* Thin modern progress bar */}
                  <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        isMet
                          ? 'bg-emerald-500'
                          : co.attainment_percentage >= 50
                          ? 'bg-orange-500'
                          : 'bg-amber-500'
                      }`}
                      style={{ width: `${Math.min(co.attainment_percentage, 100)}%` }}
                    />
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1">
                    <span>{co.contributing_topics?.length || 3} Modules</span>
                    <div className="flex items-center space-x-1 text-orange-600 font-semibold">
                      <span>Inspect Evidence</span>
                      <ChevronRight className="w-3 h-3" />
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 3. Detailed Evidence Tracking Section */}
      {activeSelected && (
        <div className="bg-white border border-[#E2E8F0] rounded-2xl p-6 sm:p-7 space-y-6 shadow-[0_4px_20px_rgba(15,23,42,0.04)]">
          <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-100">
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-mono font-bold px-2.5 py-1 bg-orange-50 text-orange-600 rounded-md border border-orange-200">
                  {activeSelected.code}
                </span>
                <h3 className="text-lg sm:text-xl font-bold text-slate-900 tracking-tight">
                  Detailed Attainment Evidence & Topic Matrix
                </h3>
              </div>
              <p className="text-xs text-slate-600 mt-1 max-w-2xl leading-relaxed">
                {activeSelected.description}
              </p>
            </div>

            <div className="flex items-center space-x-4 p-3 bg-[#F8FAFC] rounded-xl border border-slate-200">
              {getStatusBadge(activeSelected.status, activeSelected.attainment_percentage, activeSelected.target_pct)}
              <div className="text-right">
                <div className="text-[10px] text-slate-400 uppercase font-bold">Attainment</div>
                <div className="text-xl font-bold text-orange-600">
                  {activeSelected.attainment_percentage}%
                </div>
              </div>
            </div>
          </div>

          {/* Contributing Topics Matrix */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3 flex items-center space-x-1.5">
              <Layers className="w-4 h-4 text-orange-600" />
              <span>Contributing Syllabus Modules to {activeSelected.code}</span>
            </h4>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {(activeSelected.contributing_topics || []).map((t: any) => (
                <div
                  key={t.topic_id}
                  className="p-4 bg-[#F8FAFC] rounded-xl border border-slate-200 space-y-1.5"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono px-1.5 py-0.5 bg-white text-slate-600 rounded border border-slate-200">
                      {t.code || `TOPIC-${t.topic_id}`}
                    </span>
                    <span className="text-xs font-bold text-orange-600">
                      {Math.round(t.mastery)}%
                    </span>
                  </div>
                  <div className="font-semibold text-slate-900 text-xs truncate">{t.title}</div>
                  <div className="text-[10px] text-slate-500 capitalize">
                    Mastery Tier: {t.status || 'Assessed'}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Audit Trail & Pedagogical Remediation */}
          <div className="p-5 bg-[#F8FAFC] rounded-xl border border-slate-200 space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Accreditation Evidence Audit Trail & Remediation Strategy
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
              <div className="p-3.5 bg-white rounded-xl border border-slate-200">
                <div className="text-slate-500 font-medium">Mapped Contributing Modules</div>
                <div className="text-base font-bold text-slate-900 mt-1">
                  {activeSelected.evidence?.contributing_topics_count || (activeSelected.contributing_topics || []).length} Topics
                </div>
                <p className="text-[10px] text-slate-400 mt-0.5">Syllabus-to-Outcome matrix</p>
              </div>

              <div className="p-3.5 bg-white rounded-xl border border-slate-200">
                <div className="text-slate-500 font-medium">Identified Weak Areas</div>
                <div className="text-sm font-bold text-amber-600 mt-1 truncate">
                  {activeSelected.weak_areas?.length > 0 ? activeSelected.weak_areas.join(', ') : 'None (Threshold Satisfied)'}
                </div>
                <p className="text-[10px] text-slate-400 mt-0.5">Scored below target threshold</p>
              </div>

              <div className="p-3.5 bg-white rounded-xl border border-slate-200">
                <div className="text-slate-500 font-medium">AI Pedagogical Remediation</div>
                <div className="text-xs font-semibold text-slate-800 mt-1 leading-snug">
                  {activeSelected.remediation}
                </div>
                <p className="text-[10px] text-slate-400 mt-0.5">
                  Institutional Target: {activeSelected.target_pct}%
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
