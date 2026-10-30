import React, { useState, useEffect } from 'react';
import {
  X,
  AlertTriangle,
  Search,
  CheckCircle2,
  RefreshCw,
  Users,
  AlertCircle
} from 'lucide-react';
import { api } from '../services/api';
import { GapDrilldownResponse, GapAffectedStudent } from '../types';

interface GapDrilldownModalProps {
  isOpen: boolean;
  onClose: () => void;
  classId: number;
  gapKey: string;
  gapTitle?: string;
  onSelectStudent?: (studentId: number) => void;
}

export const GapDrilldownModal: React.FC<GapDrilldownModalProps> = ({
  isOpen,
  onClose,
  classId,
  gapKey,
  gapTitle,
  onSelectStudent
}) => {
  const [data, setData] = useState<GapDrilldownResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    if (isOpen && classId && gapKey) {
      loadDrilldown();
    }
  }, [isOpen, classId, gapKey]);

  const loadDrilldown = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getClassGapDrilldown(classId, gapKey);
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to load gap drilldown details.');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const filteredStudents = (data?.affected_students || []).filter((s) => {
    const term = searchTerm.toLowerCase();
    return s.name.toLowerCase().includes(term) || s.email.toLowerCase().includes(term);
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4 sm:p-6 animate-fadeIn">
      <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-2xl w-full max-h-[85vh] flex flex-col overflow-hidden animate-scaleUp">
        {/* Header */}
        <div className="p-6 border-b border-slate-200 bg-slate-50/60 flex items-start justify-between">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <span className="text-xs font-semibold px-2 py-0.5 rounded bg-amber-100 text-amber-800 flex items-center space-x-1">
                <AlertTriangle className="w-3 h-3 text-amber-600" />
                <span>Learning Gap Drill-Down</span>
              </span>
              <span className="text-xs text-slate-500 font-mono">
                {data ? `${data.total_affected} students affected` : 'Loading...'}
              </span>
            </div>
            <h3 className="text-lg font-bold text-slate-900">
              {data?.gap_title || gapTitle || gapKey}
            </h3>
            <p className="text-xs text-slate-500">
              Roster of enrolled students performing below mastery threshold for this learning component.
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-200 rounded-xl text-slate-400 hover:text-slate-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Search */}
        <div className="p-4 border-b border-slate-100 bg-white flex items-center justify-between gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search affected students by name or email..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs focus:outline-hidden focus:ring-2 focus:ring-[#635BFF]/30"
            />
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-4 flex-1 bg-slate-50/30">
          {loading ? (
            <div className="py-16 text-center space-y-2 text-slate-400">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto text-[#635BFF]" />
              <p className="text-xs">Loading affected students...</p>
            </div>
          ) : error ? (
            <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          ) : filteredStudents.length === 0 ? (
            <div className="py-12 text-center text-slate-400 text-xs">
              {searchTerm ? 'No affected students match your search.' : 'No students currently struggling with this gap.'}
            </div>
          ) : (
            <div className="divide-y divide-slate-100 bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
              {filteredStudents.map((s) => (
                <div
                  key={s.student_id}
                  className="p-3.5 flex items-center justify-between hover:bg-slate-50/80 transition-colors"
                >
                  <div className="space-y-0.5">
                    <div className="flex items-center space-x-2">
                      <span className="font-bold text-xs text-slate-900">{s.name}</span>
                      {onSelectStudent && (
                        <button
                          onClick={() => {
                            onClose();
                            onSelectStudent(s.student_id);
                          }}
                          className="text-[10px] text-[#635BFF] hover:underline font-semibold"
                        >
                          View Profile
                        </button>
                      )}
                    </div>
                    <span className="text-[11px] text-slate-500">{s.email}</span>
                  </div>
                  <div className="text-right space-y-0.5">
                    <div className="flex items-center justify-end space-x-2">
                      <span className="font-mono text-xs font-bold text-rose-600">
                        {s.score !== undefined ? `${s.score}% accuracy` : `${s.mastery}% mastery`}
                      </span>
                      <span className="text-[10px] text-slate-400 font-mono">
                        (target: {s.threshold}%)
                      </span>
                    </div>
                    {s.gap !== undefined && (
                      <span className="text-[10px] text-rose-500 font-semibold block">
                        Deficit: -{s.gap}%
                      </span>
                    )}
                    {s.attempts_count !== undefined && (
                      <span className="text-[10px] text-slate-400 block">
                        {s.attempts_count} question attempts
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-200 bg-white flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-xl transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
