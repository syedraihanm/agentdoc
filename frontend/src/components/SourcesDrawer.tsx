import React from 'react';
import { X, Copy, Check, FileText } from 'lucide-react';
import { EvidenceItem } from '../lib/api';

interface SourcesDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  evidence: EvidenceItem[];
}

export const SourcesDrawer: React.FC<SourcesDrawerProps> = ({ isOpen, onClose, evidence }) => {
  const [copiedIdx, setCopiedIdx] = React.useState<number | null>(null);

  if (!isOpen) return null;

  const handleCopy = (quote: string, idx: number) => {
    navigator.clipboard.writeText(quote);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-black/40 backdrop-blur-xs flex justify-end animate-in fade-in duration-200">
      <div className="w-full max-w-md bg-white dark:bg-slate-900 h-full shadow-2xl flex flex-col border-l border-slate-200 dark:border-slate-800">
        <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2 font-semibold text-slate-800 dark:text-slate-100">
            <FileText className="w-5 h-5 text-primary dark:text-primary-dark" />
            <span>Verified Sources & Evidence ({evidence.length})</span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-4 overflow-y-auto flex-1 space-y-4">
          {evidence.length === 0 ? (
            <p className="text-sm text-slate-500 italic">No quotes were cited for this response.</p>
          ) : (
            evidence.map((item, idx) => (
              <div
                key={idx}
                className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/40 space-y-2 text-xs"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    {item.doc_id && (
                      <span className="px-1.5 py-0.5 rounded font-mono text-[10px] font-semibold bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20">
                        {item.doc_id}
                      </span>
                    )}
                    <span className="inline-block px-2 py-0.5 rounded font-mono font-semibold bg-primary/10 text-primary dark:text-primary-dark">
                      Page {item.page}
                    </span>
                  </div>
                  <button
                    onClick={() => handleCopy(item.quote, idx)}
                    className="flex items-center gap-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
                  >
                    {copiedIdx === idx ? (
                      <>
                        <Check className="w-3.5 h-3.5 text-emerald-500" />
                        <span className="text-[11px] text-emerald-500">Copied</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3.5 h-3.5" />
                        <span className="text-[11px]">Copy quote</span>
                      </>
                    )}
                  </button>
                </div>

                <div className="p-2.5 rounded bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 font-mono text-slate-800 dark:text-slate-200 leading-relaxed text-[11px]">
                  "{item.quote}"
                </div>

                {item.supports && (
                  <p className="text-slate-500 dark:text-slate-400 text-[11px]">
                    <span className="font-medium text-slate-700 dark:text-slate-300">Supports:</span> {item.supports}
                  </p>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};