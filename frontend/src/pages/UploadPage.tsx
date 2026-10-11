import React, { useState, useEffect, useRef } from 'react';
import { Upload, FileText, Sparkles, AlertCircle, Loader2, ArrowRight, ShieldCheck } from 'lucide-react';
import { DocumentItem, fetchDocuments, uploadDocument, loadDemoDocument, deleteDocument } from '../lib/api';

interface UploadPageProps {
  onDocumentsSelected: (docs: DocumentItem[]) => void;
  onNavigateToEval: () => void;
}

export const UploadPage: React.FC<UploadPageProps> = ({ onDocumentsSelected, onNavigateToEval }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [recentDocs, setRecentDocs] = useState<DocumentItem[]>([]);
  const [selectedDocIds, setSelectedDocIds] = useState<Set<string>>(new Set());
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadRecent();
  }, []);

  const loadRecent = async () => {
    try {
      const docs = await fetchDocuments();
      setRecentDocs(docs);
    } catch {
      // ignore
    }
  };

  const handleFiles = async (files: FileList | File[]) => {
    const fileList = Array.from(files);
    const pdfFiles = fileList.filter(f => f.name.toLowerCase().endsWith('.pdf'));
    if (pdfFiles.length === 0) {
      setError('Please upload at least one PDF document (.pdf).');
      return;
    }
    setError(null);
    setLoading(true);

    const uploaded: DocumentItem[] = [];
    try {
      for (let i = 0; i < pdfFiles.length; i++) {
        const file = pdfFiles[i];
        setStatusMessage(`Ingesting (${i + 1}/${pdfFiles.length}): ${file.name}...`);
        const doc = await uploadDocument(file);
        uploaded.push(doc);
      }
      onDocumentsSelected(uploaded);
    } catch (err: any) {
      setError(err.message || 'Ingestion failed. Please check the PDF.');
    } finally {
      setLoading(false);
      setStatusMessage('');
    }
  };

  const handleDemoLoad = async () => {
    setError(null);
    setLoading(true);
    setStatusMessage('Loading demo document: Helix Robotics Policy (11 pages)...');
    try {
      const doc = await loadDemoDocument();
      onDocumentsSelected([doc]);
    } catch (err: any) {
      setError(err.message || 'Failed to load demo document.');
    } finally {
      setLoading(false);
      setStatusMessage('');
    }
  };

  const toggleSelectDoc = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const next = new Set(selectedDocIds);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelectedDocIds(next);
  };

  const handleStartWithSelected = () => {
    const selected = recentDocs.filter(d => selectedDocIds.has(d.doc_id));
    if (selected.length > 0) {
      onDocumentsSelected(selected);
    }
  };

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const onDragLeave = () => {
    setIsDragging(false);
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col items-center justify-center p-6 text-slate-800 dark:text-slate-100">
      <div className="w-full max-w-2xl space-y-8">
        {/* Header */}
        <div className="text-center space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-primary/10 text-primary dark:text-primary-dark">
            <ShieldCheck className="w-4 h-4" />
            <span>Budgeted Document QA · Hackathon 2026</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-900 dark:text-white">
            PageTurner
          </h1>
          <p className="text-sm sm:text-base text-slate-600 dark:text-slate-400 max-w-lg mx-auto">
            Ask your PDF. Under budget. Fully traced. Reasoning directly over raw documents without vector databases or RAG.
          </p>
        </div>

        {/* Constraint Chips */}
        <div className="flex flex-wrap items-center justify-center gap-2.5 text-xs font-medium">
          <span className="px-3 py-1 rounded-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-300 shadow-2xs">
            🚫 No RAG · No embeddings
          </span>
          <span className="px-3 py-1 rounded-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-300 shadow-2xs">
            ⏱️ ≤ 6 tool calls / question
          </span>
          <span className="px-3 py-1 rounded-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-300 shadow-2xs">
            🔍 100% Transparent trace
          </span>
        </div>

        {/* Upload Dropzone */}
        <div
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onDrop={onDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`p-10 rounded-2xl border-2 border-dashed transition-all cursor-pointer text-center bg-white dark:bg-slate-900 shadow-sm ${
            isDragging
              ? 'border-primary dark:border-primary-dark bg-primary/5 dark:bg-primary-dark/10 scale-[1.01]'
              : 'border-slate-300 dark:border-slate-700 hover:border-slate-400 dark:hover:border-slate-600'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            multiple
            className="hidden"
            onChange={(e) => e.target.files && handleFiles(e.target.files)}
          />

          {loading ? (
            <div className="py-6 space-y-3">
              <Loader2 className="w-10 h-10 text-primary dark:text-primary-dark animate-spin mx-auto" />
              <p className="text-sm font-medium text-slate-700 dark:text-slate-200">{statusMessage}</p>
              <p className="text-xs text-slate-400">Targeting &lt; 5 seconds per 100 pages</p>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="w-12 h-12 rounded-2xl bg-primary/10 text-primary dark:text-primary-dark flex items-center justify-center mx-auto">
                <Upload className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                  Drop one or more PDFs here, or <span className="text-primary dark:text-primary-dark underline">browse files</span>
                </p>
                <p className="text-xs text-slate-400">Single or multiple PDFs up to 50MB (max 1,000 pages)</p>
              </div>
            </div>
          )}
        </div>

        {/* Error notification */}
        {error && (
          <div className="p-3.5 rounded-xl border border-rose-200 dark:rose-900 bg-rose-50 dark:bg-rose-950/40 text-xs text-rose-700 dark:text-rose-300 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Demo button & Eval link */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2">
          <button
            onClick={handleDemoLoad}
            disabled={loading}
            className="w-full sm:w-auto flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800 text-sm font-semibold text-slate-700 dark:text-slate-200 transition-colors shadow-2xs"
          >
            <Sparkles className="w-4 h-4 text-amber-500" />
            <span>Try the Demo Document</span>
          </button>

          <button
            onClick={onNavigateToEval}
            className="text-xs text-slate-500 dark:text-slate-400 hover:text-primary dark:hover:text-primary-dark flex items-center gap-1 font-medium transition-colors"
          >
            <span>Open Automated Eval Dashboard</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Recent Documents & Multi-Doc Selection */}
        {recentDocs.length > 0 && (
          <div className="pt-6 border-t border-slate-200 dark:border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Recent Documents (Select 1 or more)</h3>
              {selectedDocIds.size > 0 && (
                <button
                  onClick={handleStartWithSelected}
                  className="px-3 py-1 rounded-lg text-xs font-semibold bg-primary text-white hover:bg-primary/90 transition-colors"
                >
                  Start Session with {selectedDocIds.size} Doc{selectedDocIds.size > 1 ? 's' : ''} →
                </button>
              )}
            </div>
            <div className="space-y-2">
              {recentDocs.slice(0, 6).map((d) => {
                const isSelected = selectedDocIds.has(d.doc_id);
                return (
                  <div
                    key={d.doc_id}
                    onClick={() => onDocumentsSelected([d])}
                    className={`p-3 rounded-xl border transition-all cursor-pointer flex items-center justify-between text-xs ${
                      isSelected
                        ? 'border-primary bg-primary/5 dark:bg-primary/10'
                        : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-primary/50'
                    }`}
                  >
                    <div className="flex items-center gap-2.5 overflow-hidden">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={(e) => toggleSelectDoc(d.doc_id, e as any)}
                        onClick={(e) => e.stopPropagation()}
                        className="rounded border-slate-300 text-primary focus:ring-primary w-4 h-4 cursor-pointer"
                      />
                      <FileText className="w-4 h-4 text-primary shrink-0" />
                      <span className="font-semibold text-slate-800 dark:text-slate-200 truncate">{d.title}</span>
                      <span className="text-slate-400 shrink-0">({d.num_pages} pages)</span>
                    </div>
                    <span className="text-primary dark:text-primary-dark font-medium shrink-0">Open →</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};