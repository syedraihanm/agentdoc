import React from 'react';
import { GitCompare, ArrowRight } from 'lucide-react';
import { ConflictItem } from '../lib/api';

const RULE_LABELS: Record<string, string> = {
  explicit_supersession: 'Explicit supersession clause overrides base text',
  amendment_or_errata: 'Later amendment / errata notice overrides earlier section',
  later_effective_date: 'Later effective date controls over earlier policy',
  specific_over_general: 'Specific exception controls over general rule',
  unresolved: 'Unresolved conflict detected in document text',
};

export const ConflictCard: React.FC<{ conflict: ConflictItem }> = ({ conflict }) => {
  return (
    <div className="my-3 p-3.5 rounded-lg border border-amber-200 dark:border-amber-900/60 bg-amber-50/50 dark:bg-amber-950/20 text-xs">
      <div className="flex items-center gap-1.5 font-semibold text-amber-800 dark:text-amber-300 mb-2">
        <GitCompare className="w-4 h-4 text-amber-600 dark:text-amber-400" />
        <span>Conflict Resolved: {conflict.topic}</span>
      </div>

      <div className="space-y-1.5 text-slate-700 dark:text-slate-300">
        <div className="flex items-start gap-2">
          <span className="font-semibold text-emerald-700 dark:text-emerald-400 shrink-0">Current (p. {conflict.chosen.page}):</span>
          <span className="italic font-mono text-slate-800 dark:text-slate-200">"{conflict.chosen.quote}"</span>
        </div>

        {conflict.superseded.map((s, idx) => (
          <div key={idx} className="flex items-start gap-2 text-slate-500 dark:text-slate-400">
            <span className="line-through shrink-0">Superseded (p. {s.page}):</span>
            <span className="line-through italic font-mono">"{s.quote}"</span>
          </div>
        ))}

        <div className="pt-1.5 mt-1 border-t border-amber-200/60 dark:border-amber-900/40 text-amber-700 dark:text-amber-400 flex items-center gap-1">
          <ArrowRight className="w-3 h-3" />
          <span>Rule: {RULE_LABELS[conflict.resolution_rule] || conflict.resolution_rule}</span>
        </div>
      </div>
    </div>
  );
};