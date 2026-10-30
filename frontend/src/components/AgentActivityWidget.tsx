import React from 'react';
import { Bot, Sparkles, RefreshCw } from 'lucide-react';
import { AgentLog } from '../types';

interface AgentActivityWidgetProps {
  logs: AgentLog[];
  onRefresh?: () => void;
}

export const AgentActivityWidget: React.FC<AgentActivityWidgetProps> = ({ logs, onRefresh }) => {
  const agents = [
    { name: 'Planner Agent', role: 'Sequences learning roadmap', color: 'text-orange-600', bg: 'bg-orange-50 border-orange-200' },
    { name: 'Tutor Agent', role: 'Adaptive instructional dialogue', color: 'text-emerald-700', bg: 'bg-emerald-50 border-emerald-200' },
    { name: 'Assessment Agent', role: 'Evaluates quiz & diagnostic', color: 'text-amber-700', bg: 'bg-amber-50 border-amber-200' },
    { name: 'Resource Agent', role: 'Retrieves approved references', color: 'text-slate-700', bg: 'bg-slate-50 border-slate-200' },
    { name: 'Progress Agent', role: 'Monitors mastery & triggers', color: 'text-emerald-700', bg: 'bg-emerald-50 border-emerald-200' },
  ];

  return (
    <div className="bg-white border border-[#E2E8F0] rounded-2xl p-5 shadow-[0_4px_20px_rgba(15,23,42,0.04)]">
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <div className="flex items-center space-x-2">
          <div className="relative">
            <Bot className="w-5 h-5 text-orange-600" />
            <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-emerald-500 rounded-full" />
          </div>
          <h3 className="text-sm font-bold text-slate-900 tracking-tight">AI Agent Status & Activity</h3>
        </div>
        {onRefresh && (
          <button
            onClick={onRefresh}
            title="Refresh logs"
            className="p-1.5 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* 5 Agent Badges */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 my-3.5">
        {agents.map((ag) => (
          <div key={ag.name} className={`p-2 rounded-xl border ${ag.bg} flex flex-col justify-between`}>
            <div className="flex items-center justify-between">
              <span className={`text-[11px] font-bold ${ag.color}`}>{ag.name.replace(' Agent', '')}</span>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            </div>
            <span className="text-[9px] text-slate-500 mt-1 line-clamp-1">{ag.role}</span>
          </div>
        ))}
      </div>

      {/* Activity Stream */}
      <div className="space-y-2 mt-2 max-h-48 overflow-y-auto pr-1">
        {logs.length === 0 ? (
          <div className="text-xs text-slate-500 py-4 text-center italic">
            AI agents standing by for student activity...
          </div>
        ) : (
          logs.slice(0, 5).map((log) => (
            <div
              key={log.id}
              className="p-2.5 bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl text-xs flex items-start space-x-2.5 transition-all hover:bg-slate-50"
            >
              <div className="mt-0.5 p-1 rounded-md bg-orange-50 text-orange-600 flex-shrink-0">
                <Sparkles className="w-3 h-3" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-900 text-[11px]">{log.agent_name}</span>
                  <span className="text-[10px] text-slate-400 font-mono">{log.created_at}</span>
                </div>
                <p className="text-slate-600 text-[11px] mt-0.5 leading-snug">{log.message}</p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
