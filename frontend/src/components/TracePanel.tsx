import React, { useState } from 'react';
import { Activity, ChevronDown, ChevronRight, Terminal, Clock, ShieldCheck } from 'lucide-react';
import { RunItem, RunEvent } from '../lib/api';
import { BudgetMeter } from './BudgetMeter';

interface TracePanelProps {
  run: RunItem | null;
  liveEvents?: RunEvent[];
  onOpenJudge?: () => void;
}

export const TracePanel: React.FC<TracePanelProps> = ({ run, liveEvents = [], onOpenJudge }) => {
  const [expandedSeq, setExpandedSeq] = useState<number | null>(null);

  // Combine run events with live events
  const allEvents = (liveEvents.length > 0 ? liveEvents : run?.events || []);
  const toolCalls = allEvents
    .filter(e => e.type === 'tool_call')
    .map(e => e.payload);

  const used = toolCalls.length > 0 ? toolCalls[toolCalls.length - 1].calls_used : (run?.tool_calls_used || 0);

  return (
    <aside className="w-96 shrink-0 border-l border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/30 flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2 font-semibold text-xs text-slate-800 dark:text-slate-100">
          <Activity className="w-4 h-4 text-primary dark:text-primary-dark" />
          <span>Live Tool Call Trace</span>
        </div>
        <BudgetMeter used={used} maxCalls={6} />
      </div>

      {/* Content / Table */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {toolCalls.length === 0 ? (
          <div className="text-center py-12 text-xs text-slate-400 dark:text-slate-500">
            <Terminal className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>No tool calls executed yet.</p>
            <p className="text-[11px] mt-1 text-slate-400">Ask a question to see real-time tool trace.</p>
          </div>
        ) : (
          toolCalls.map((tc, idx) => {
            const isExpanded = expandedSeq === tc.seq;
            return (
              <div
                key={idx}
                className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-2xs overflow-hidden transition-all text-xs"
              >
                {/* Header row */}
                <button
                  onClick={() => setExpandedSeq(isExpanded ? null : tc.seq)}
                  className="w-full text-left p-2.5 flex items-center justify-between gap-2 hover:bg-slate-50 dark:hover:bg-slate-800/50"
                >
                  <div className="flex items-center gap-2 overflow-hidden">
                    <span className="w-5 h-5 rounded-md font-mono text-[10px] font-bold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 flex items-center justify-center shrink-0">
                      #{idx + 1}
                    </span>
                    <span className="font-mono font-semibold text-slate-800 dark:text-slate-200 truncate">
                      {tc.tool}
                    </span>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <span className="font-mono text-[11px] text-slate-400">
                      {tc.duration_ms}ms
                    </span>
                    {isExpanded ? (
                      <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
                    ) : (
                      <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
                    )}
                  </div>
                </button>

                {/* Purpose and summary snippet */}
                <div className="px-2.5 pb-2 text-[11px] space-y-0.5 border-t border-slate-100 dark:border-slate-800/60 pt-1.5 text-slate-500 dark:text-slate-400">
                  <p><span className="font-medium text-slate-600 dark:text-slate-300">Purpose:</span> {tc.purpose}</p>
                  <p><span className="font-medium text-slate-600 dark:text-slate-300">Result:</span> <span className="font-mono">{tc.result_summary}</span></p>
                </div>

                {/* Expanded Details */}
                {isExpanded && (
                  <div className="p-2.5 bg-slate-50 dark:bg-slate-950/60 border-t border-slate-200 dark:border-slate-800 text-[11px] font-mono space-y-2">
                    <div>
                      <span className="text-slate-400">Args:</span>
                      <pre className="p-1.5 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 overflow-x-auto text-[10px] mt-0.5">
                        {JSON.stringify(tc.args, null, 2)}
                      </pre>
                    </div>

                    <div>
                      <span className="text-slate-400">Full Result:</span>
                      <pre className="p-1.5 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 overflow-x-auto max-h-36 text-[10px] mt-0.5">
                        {typeof tc.result === 'object' ? JSON.stringify(tc.result, null, 2) : String(tc.result)}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Footer */}
      {onOpenJudge && (
        <div className="p-3 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
          <button
            onClick={onOpenJudge}
            className="w-full py-2 px-3 rounded-lg text-xs font-semibold bg-primary/10 text-primary dark:text-primary-dark hover:bg-primary/20 transition-colors flex items-center justify-center gap-1.5"
          >
            <span>Open Judge Mode & Traces</span>
          </button>
        </div>
      )}
    </aside>
  );
};