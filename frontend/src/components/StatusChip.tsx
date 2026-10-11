import React from 'react';
import { CheckCircle2, AlertCircle, HelpCircle } from 'lucide-react';

interface StatusChipProps {
  status: 'answered' | 'partial' | 'insufficient' | string;
}

export const StatusChip: React.FC<StatusChipProps> = ({ status }) => {
  if (status === 'answered') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
        Answered
      </span>
    );
  } else if (status === 'partial') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-400 border border-amber-200 dark:border-amber-800">
        <AlertCircle className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />
        Partial Information
      </span>
    );
  } else {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
        <HelpCircle className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400" />
        Insufficient Information
      </span>
    );
  }
};