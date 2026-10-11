import React, { useState } from 'react';
import { X, Download, Copy, Check, Terminal, Cpu, ShieldCheck, Code } from 'lucide-react';
import { RunItem } from '../lib/api';
import { StatusChip } from './StatusChip';
import { BudgetMeter } from './BudgetMeter';

interface JudgeViewProps {
  run: RunItem;
  onClose: () => void;
}

export const JudgeView: React.FC<JudgeViewProps> = ({ run, onClose }) => {
  const [activeTab, setActiveTab] = useState<'tools' | 'llm' | 'verification' | 'raw'>('tools');
  const [copied, setCopied] = useState(false);

  const events = run.events || [];
  const toolCalls = events.filter(e => e.type === 'tool_call').map(e => e.payload);
  const llmCalls = events.filter(e => e.type === 'llm_call').map(e => e.payload);
  const verifications = events.filter(e => e.type === 'verification').map(e => e.payload);

  const handleCopyRaw = () => {
    navigator.clipboard.writeText(JSON.stringify({ run, events }, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadMarkdown = () => {
    window.open(`/api/runs/${run.run_id}/trace.md`, '_blank');
  };

  const handleDownloadJSON = () => {
    window.open(`/api/runs/${run.run_id}/trace.json`, '_blank');
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-black/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="w-full max-w-5xl h-[85vh] bg-white dark:bg-slate-900 rounded-2xl shadow-2xl flex flex-col border border-slate-200 dark:border-slate-800 overflow-hidden">
        {/* Header */}
        <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50 dark:bg-slate-900/50">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold text-primary dark:text-primary-dark">JUDGE MODE</span>
              <span className="text-xs text-slate-400">· Run ID: {run.run_id}</span>
              <StatusChip status={run.status} />
            </div>
            <h2 className="text-sm font-semibold text-slate-800 dark:text-slate-100 truncate max-w-2xl">
              {run.question}
            </h2>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleDownloadMarkdown}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-white dark:hover:bg-slate-800 text-xs font-medium text-slate-700 dark:text-slate-200 transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Trace (.md)</span>
            </button>

            <button
              onClick={handleDownloadJSON}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-white dark:hover:bg-slate-800 text-xs font-medium text-slate-700 dark:text-slate-200 transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Trace (.json)</span>
            </button>

            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-1 px-4 border-b border-slate-200 dark:border-slate-800 text-xs font-medium bg-slate-50/50 dark:bg-slate-900/30">
          <button
            onClick={() => setActiveTab('tools')}
            className={`py-2.5 px-3 border-b-2 flex items-center gap-1.5 transition-colors ${
              activeTab === 'tools'
                ? 'border-primary text-primary dark:text-primary-dark font-semibold'
                : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
            }`}
          >
            <Terminal className="w-3.5 h-3.5" />
            <span>Tool Calls ({toolCalls.length}/6)</span>
          </button>

          <button
            onClick={() => setActiveTab('llm')}
            className={`py-2.5 px-3 border-b-2 flex items-center gap-1.5 transition-colors ${
              activeTab === 'llm'
                ? 'border-primary text-primary dark:text-primary-dark font-semibold'
                : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
            }`}
          >
            <Cpu className="w-3.5 h-3.5" />
            <span>LLM Decisions & Prompts ({llmCalls.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('verification')}
            className={`py-2.5 px-3 border-b-2 flex items-center gap-1.5 transition-colors ${
              activeTab === 'verification'
                ? 'border-primary text-primary dark:text-primary-dark font-semibold'
                : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Verification Details</span>
          </button>

          <button
            onClick={() => setActiveTab('raw')}
            className={`py-2.5 px-3 border-b-2 flex items-center gap-1.5 transition-colors ${
              activeTab === 'raw'
                ? 'border-primary text-primary dark:text-primary-dark font-semibold'
                : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
            }`}
          >
            <Code className="w-3.5 h-3.5" />
            <span>Raw JSON</span>
          </button>
        </div>

        {/* Tab Body */}
        <div className="p-4 overflow-y-auto flex-1 font-sans text-xs">
          {activeTab === 'tools' && (
            <div className="space-y-3">
              <table className="w-full text-left border-collapse border border-slate-200 dark:border-slate-800">
                <thead>
                  <tr className="bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-semibold font-mono text-[11px]">
                    <th className="p-2.5 border border-slate-200 dark:border-slate-800">#</th>
                    <th className="p-2.5 border border-slate-200 dark:border-slate-800">Tool</th>
                    <th className="p-2.5 border border-slate-200 dark:border-slate-800">Arguments</th>
                    <th className="p-2.5 border border-slate-200 dark:border-slate-800">Result</th>
                    <th className="p-2.5 border border-slate-200 dark:border-slate-800">Purpose</th>
                    <th className="p-2.5 border border-slate-200 dark:border-slate-800">Budget</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-800 font-mono text-[11px]">
                  {toolCalls.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="p-4 text-center text-slate-400 italic font-sans">
                        No tool calls executed (canned response or direct lookup).
                      </td>
                    </tr>
                  ) : (
                    toolCalls.map((tc, idx) => (
                      <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                        <td className="p-2.5 border border-slate-200 dark:border-slate-800 font-bold">{idx + 1}</td>
                        <td className="p-2.5 border border-slate-200 dark:border-slate-800 font-semibold text-primary dark:text-primary-dark">
                          {tc.tool}
                        </td>
                        <td className="p-2.5 border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-300">
                          {JSON.stringify(tc.args)}
                        </td>
                        <td className="p-2.5 border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-200">
                          {tc.result_summary}
                        </td>
                        <td className="p-2.5 border border-slate-200 dark:border-slate-800 font-sans text-slate-500">
                          {tc.purpose}
                        </td>
                        <td className="p-2.5 border border-slate-200 dark:border-slate-800 text-emerald-600 dark:text-emerald-400 font-bold">
                          {tc.calls_used}/6
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === 'llm' && (
            <div className="space-y-4">
              {llmCalls.map((llm, idx) => (
                <div key={idx} className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/40 space-y-2">
                  <div className="flex items-center justify-between font-semibold">
                    <span className="font-mono text-primary dark:text-primary-dark">LLM Call #{idx + 1}: {llm.purpose}</span>
                    <span className="text-slate-400 text-[11px] font-mono">
                      {llm.usage?.duration_ms}ms · {llm.usage?.model}
                    </span>
                  </div>
                  <pre className="p-2.5 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 font-mono text-[11px] overflow-x-auto max-h-48 text-slate-800 dark:text-slate-200">
                    {llm.raw_output}
                  </pre>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'verification' && (
            <div className="space-y-3 font-mono">
              <pre className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-[11px] overflow-x-auto text-slate-800 dark:text-slate-200">
                {JSON.stringify(verifications, null, 2)}
              </pre>
            </div>
          )}

          {activeTab === 'raw' && (
            <div className="space-y-2">
              <div className="flex justify-end">
                <button
                  onClick={handleCopyRaw}
                  className="flex items-center gap-1 px-2.5 py-1 rounded bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-xs font-sans transition-colors"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copied ? 'Copied' : 'Copy JSON'}</span>
                </button>
              </div>
              <pre className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 font-mono text-[11px] overflow-x-auto max-h-[55vh] text-slate-800 dark:text-slate-200">
                {JSON.stringify({ run, events }, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};