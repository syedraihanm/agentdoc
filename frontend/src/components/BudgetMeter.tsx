import React from 'react';

interface BudgetMeterProps {
  used: number;
  maxCalls?: number;
  compact?: boolean;
}

export const BudgetMeter: React.FC<BudgetMeterProps> = ({ used, maxCalls = 6, compact = false }) => {
  const pips = Array.from({ length: maxCalls }, (_, i) => i < used);

  return (
    <div className="flex items-center gap-1.5" title={`Budget: ${used}/${maxCalls} tool calls used`}>
      <div className="flex items-center gap-1">
        {pips.map((filled, idx) => (
          <span
            key={idx}
            className={`transition-all duration-200 rounded-sm ${
              compact ? 'w-2 h-2.5' : 'w-2.5 h-3.5'
            } ${
              filled
                ? 'bg-primary dark:bg-primary-dark shadow-xs'
                : 'bg-slate-200 dark:bg-slate-700 border border-slate-300 dark:border-slate-600'
            }`}
          />
        ))}
      </div>
      <span className="text-xs font-mono font-medium text-slate-500 dark:text-slate-400">
        {used}/{maxCalls}
      </span>
    </div>
  );
};