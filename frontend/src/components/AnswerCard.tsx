import React, { useState } from 'react';
import { FileText, ExternalLink, ShieldCheck, HelpCircle } from 'lucide-react';
import { AnswerObj, RunItem } from '../lib/api';
import { StatusChip } from './StatusChip';
import { BudgetMeter } from './BudgetMeter';
import { ConflictCard } from './ConflictCard';
import { InjectionCard } from './InjectionCard';
import { SourcesDrawer } from './SourcesDrawer';

interface AnswerCardProps {
  run: RunItem;
  onOpenJudge: (runId: string) => void;
}

export const AnswerCard: React.FC<AnswerCardProps> = ({ run, onOpenJudge }) => {
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const answer = run.answer;

  if (!answer) {
    return (
      <div className="p-4 rounded-xl border border-rose-200 dark:border-rose-900 bg-rose-50/50 dark:bg-rose-950/20 text-rose-700 dark:text-rose-300 text-sm">
        Processing error: no structured answer was returned.
      </div>
    );
  }

  // Highlight page citations like (p. 9) in the answer text as clickable buttons
  const renderFormattedAnswer = (text: string) => {
    const parts = text.split(/(\(p\.\s*\d+\))/gi);
    return parts.map((part, i) => {
      const match = part.match(/\(p\.\s*(\d+)\)/i);
      if (match) {
        const pageNum = match[1];
        return (
          <button
            key={i}
            onClick={() => setSourcesOpen(true)}
            className="inline-flex items-center px-1.5 py-0.5 mx-0.5 rounded text-xs font-mono font-semibold bg-primary/10 text-primary dark:text-primary-dark hover:bg-primary/20 transition-colors"
          >
            p.{pageNum}
          </button>
        );
      }
      return part;
    });
  };

  return (
    <div className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 shadow-xs space-y-4">
      {/* Top Header: Status Chip & Confidence */}
      <div className="flex items-center justify-between">
        <StatusChip status={answer.status} />
        <span className="text-xs text-slate-400 capitalize font-medium">
          Confidence: <span className="text-slate-600 dark:text-slate-300 font-semibold">{answer.confidence}</span>
        </span>
      </div>

      {/* Main Answer text */}
      <div className="text-base leading-relaxed text-slate-800 dark:text-slate-100 font-sans">
        {renderFormattedAnswer(answer.answer)}
      </div>

      {/* Conflict Resolution Cards */}
      {answer.conflicts && answer.conflicts.map((conf, idx) => (
        <ConflictCard key={idx} conflict={conf} />
      ))}

      {/* Ignored Document Instructions */}
      {answer.ignored_instructions && answer.ignored_instructions.map((ign, idx) => (
        <InjectionCard key={idx} item={ign} />
      ))}

      {/* Missing or Unanswered Topics */}
      {answer.not_found && answer.not_found.length > 0 && (
        <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700/60 text-xs space-y-1">
          <span className="font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
            <HelpCircle className="w-3.5 h-3.5 text-slate-400" />
            Not found in document:
          </span>
          <ul className="list-disc list-inside text-slate-500 dark:text-slate-400 space-y-0.5 pl-1">
            {answer.not_found.map((nf, i) => (
              <li key={i}>{nf}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Closest related (not an answer) */}
      {answer.closest_related && (
        <div className="p-3 rounded-lg bg-indigo-50/50 dark:bg-indigo-950/20 border border-indigo-100 dark:border-indigo-900/40 text-xs space-y-1">
          <span className="font-semibold text-indigo-800 dark:text-indigo-300">
            Closest Related Information in Document:
          </span>
          <p className="text-slate-600 dark:text-slate-300 italic">
            "{answer.closest_related}"
          </p>
        </div>
      )}

      {/* Footer Meta Row */}
      <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-500">
        <div className="flex items-center gap-4">
          <BudgetMeter used={run.tool_calls_used} maxCalls={6} compact />
          
          <div className="flex items-center gap-1 text-slate-600 dark:text-slate-300">
            <ShieldCheck className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            <span>Quotes verified: {answer.evidence?.length || 0}</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {answer.evidence && answer.evidence.length > 0 && (
            <button
              onClick={() => setSourcesOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-200 font-medium transition-colors"
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Sources ({answer.evidence.length})</span>
            </button>
          )}

          <button
            onClick={() => onOpenJudge(run.run_id)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 font-medium transition-colors"
          >
            <ExternalLink className="w-3.5 h-3.5" />
            <span>View Trace</span>
          </button>
        </div>
      </div>

      {/* Sources Drawer */}
      <SourcesDrawer
        isOpen={sourcesOpen}
        onClose={() => setSourcesOpen(false)}
        evidence={answer.evidence || []}
      />
    </div>
  );
};