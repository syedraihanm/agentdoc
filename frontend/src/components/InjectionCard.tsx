import React from 'react';
import { ShieldAlert } from 'lucide-react';
import { IgnoredInstruction } from '../lib/api';

export const InjectionCard: React.FC<{ item: IgnoredInstruction }> = ({ item }) => {
  return (
    <div className="my-2 p-3 rounded-lg border-2 border-dashed border-amber-400 dark:border-amber-600 bg-amber-50/40 dark:bg-amber-950/20 text-xs">
      <div className="flex items-center gap-1.5 font-semibold text-amber-800 dark:text-amber-300 mb-1">
        <ShieldAlert className="w-4 h-4 text-amber-600 dark:text-amber-400" />
        <span>Ignored Instruction from PDF (p. {item.page})</span>
      </div>
      <div className="text-slate-600 dark:text-slate-400 font-mono text-[11px] bg-white/70 dark:bg-slate-900/60 p-2 rounded border border-amber-200 dark:border-amber-900/40">
        "{item.excerpt}"
      </div>
      <p className="mt-1 text-[11px] text-amber-700 dark:text-amber-400">
        Neutralized by agent sandbox: prompt injection attempts in documents are isolated as data and not executed.
      </p>
    </div>
  );
};