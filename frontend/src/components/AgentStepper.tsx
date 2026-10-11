import React from 'react';
import { Loader2, Compass, Search, BookOpen, CheckCircle } from 'lucide-react';
import { RunEvent } from '../lib/api';

interface AgentStepperProps {
  events: RunEvent[];
  currentStepMessage?: string;
}

export const AgentStepper: React.FC<AgentStepperProps> = ({ events, currentStepMessage }) => {
  // Extract actions from tool_call and decision events
  const actions = events
    .filter(e => e.type === 'tool_call')
    .map(e => e.payload);

  return (
    <div className="p-4 my-2 rounded-xl border border-primary/20 dark:border-primary-dark/20 bg-primary/5 dark:bg-primary-dark/5 space-y-3">
      <div className="flex items-center gap-2 text-xs font-semibold text-primary dark:text-primary-dark">
        <Loader2 className="w-4 h-4 animate-spin" />
        <span>Agent Planning & Reading (Hard budget ≤ 6 calls)...</span>
      </div>

      <div className="space-y-1.5">
        {actions.map((act, idx) => {
          let Icon = BookOpen;
          if (act.tool === 'list_headings') Icon = Compass;
          if (act.tool === 'search_keyword') Icon = Search;

          return (
            <div key={idx} className="flex items-center gap-2 text-xs text-slate-700 dark:text-slate-300 font-mono">
              <span className="w-4 h-4 rounded-full bg-emerald-100 dark:bg-emerald-950 flex items-center justify-center shrink-0">
                <CheckCircle className="w-3 h-3 text-emerald-600 dark:text-emerald-400" />
              </span>
              <Icon className="w-3.5 h-3.5 text-slate-400" />
              <span className="font-medium text-slate-800 dark:text-slate-200">
                {act.tool}
              </span>
              <span className="text-slate-500 truncate max-w-xs">
                ({Object.entries(act.args || {})
                  .filter(([k]) => k !== 'doc_id')
                  .map(([k, v]) => `${k}=${v}`)
                  .join(', ')})
              </span>
              <span className="text-[11px] text-slate-400 ml-auto font-sans italic">
                {act.result_summary}
              </span>
            </div>
          );
        })}

        {currentStepMessage && (
          <div className="flex items-center gap-2 text-xs text-primary dark:text-primary-dark animate-pulse">
            <span className="w-2 h-2 rounded-full bg-primary animate-ping" />
            <span>{currentStepMessage}</span>
          </div>
        )}
      </div>
    </div>
  );
};