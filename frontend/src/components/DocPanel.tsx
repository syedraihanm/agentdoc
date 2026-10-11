import React, { useRef, useState } from 'react';
import { FileText, Bookmark, Sparkles, AlertTriangle, RefreshCw, Download, ArrowLeft, Plus, Loader2 } from 'lucide-react';
import { DocumentItem } from '../lib/api';

interface DocPanelProps {
  docs?: DocumentItem[];
  doc?: DocumentItem | null;
  sessionId: string;
  onNewSession: () => void;
  onReplaceDoc: () => void;
  onAddDocument?: (file: File) => Promise<void>;
}

export const DocPanel: React.FC<DocPanelProps> = ({
  docs,
  doc,
  sessionId,
  onNewSession,
  onReplaceDoc,
  onAddDocument,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [adding, setAdding] = useState(false);

  const documentList = docs || (doc ? [doc] : []);
  if (documentList.length === 0) return null;

  const handleDownloadSessionTrace = () => {
    window.open(`/api/sessions/${sessionId}/trace.md`, '_blank');
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || !e.target.files[0] || !onAddDocument) return;
    const file = e.target.files[0];
    setAdding(true);
    try {
      await onAddDocument(file);
    } catch (err) {
      console.error(err);
    } finally {
      setAdding(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const getBadge = (d: DocumentItem) => {
    if (d.headings_source === 'outline') {
      return (
        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
          <Bookmark className="w-2.5 h-2.5" />
          Bookmarks
        </span>
      );
    } else if (d.headings_source === 'heuristic') {
      return (
        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
          <Sparkles className="w-2.5 h-2.5" />
          Detected
        </span>
      );
    } else {
      return (
        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
          <AlertTriangle className="w-2.5 h-2.5" />
          Synthetic
        </span>
      );
    }
  };

  return (
    <aside className="w-72 shrink-0 border-r border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-900/40 p-4 flex flex-col justify-between overflow-y-auto">
      <div className="space-y-4">
        {/* Header & Add Doc Button */}
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Documents ({documentList.length})
          </span>
          {onAddDocument && (
            <>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                className="hidden"
                onChange={handleFileChange}
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={adding}
                className="inline-flex items-center gap-1 px-2 py-1 rounded text-[11px] font-medium bg-primary/10 text-primary dark:text-primary-dark hover:bg-primary/20 transition-colors"
                title="Add another PDF to this session"
              >
                {adding ? <Loader2 className="w-3 h-3 animate-spin" /> : <Plus className="w-3 h-3" />}
                <span>Add PDF</span>
              </button>
            </>
          )}
        </div>

        {/* Document Cards List */}
        <div className="space-y-2.5">
          {documentList.map((d) => (
            <div
              key={d.doc_id}
              className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-800/40 space-y-1.5 text-xs shadow-2xs"
            >
              <div className="flex items-center gap-2 text-slate-800 dark:text-slate-100 font-semibold text-xs">
                <FileText className="w-3.5 h-3.5 text-primary shrink-0" />
                <span className="truncate" title={d.title}>{d.title}</span>
              </div>
              <div className="text-[11px] text-slate-500 dark:text-slate-400 space-y-0.5">
                <p className="truncate" title={d.filename}>{d.filename}</p>
                <p>{d.num_pages} pages · {d.headings_count} sections</p>
              </div>
              <div className="pt-1">{getBadge(d)}</div>
            </div>
          ))}
        </div>

        {/* Constraint badges reminder */}
        <div className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-800/40 text-[11px] space-y-2">
          <div className="font-semibold text-slate-700 dark:text-slate-200">Enforced Guardrails</div>
          <ul className="text-slate-500 dark:text-slate-400 space-y-1">
            <li>• Max 6 tool calls / question</li>
            <li>• No RAG / No embeddings</li>
            <li>• Sandboxed prompt-injection</li>
            <li>• Verbatim quote verification</li>
          </ul>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="space-y-2 pt-4 border-t border-slate-200 dark:border-slate-800 text-xs">
        <button
          onClick={onNewSession}
          className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-white dark:hover:bg-slate-800 text-slate-700 dark:text-slate-200 font-medium transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>New Session</span>
        </button>

        <button
          onClick={handleDownloadSessionTrace}
          className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-white dark:hover:bg-slate-800 text-slate-700 dark:text-slate-200 font-medium transition-colors"
        >
          <Download className="w-3.5 h-3.5" />
          <span>Download Session Trace</span>
        </button>

        <button
          onClick={onReplaceDoc}
          className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Change Documents</span>
        </button>
      </div>
    </aside>
  );
};