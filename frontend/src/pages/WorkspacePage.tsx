import React, { useState, useEffect, useRef } from 'react';
import { Sparkles, MessageSquare, Shield, Activity, Menu } from 'lucide-react';
import { DocumentItem, RunItem, RunEvent, createSession, fetchSession, askQuestion, fetchRun, uploadDocument, addDocumentToSession } from '../lib/api';
import { DocPanel } from '../components/DocPanel';
import { TracePanel } from '../components/TracePanel';
import { Composer } from '../components/Composer';
import { AnswerCard } from '../components/AnswerCard';
import { AgentStepper } from '../components/AgentStepper';
import { JudgeView } from '../components/JudgeView';

interface WorkspacePageProps {
  docs?: DocumentItem[];
  doc?: DocumentItem;
  onReplaceDoc: () => void;
  onNavigateToEval: () => void;
}

const SAMPLE_QUESTIONS = [
  "How many days per week can employees work remotely?",
  "What is the domestic and international meal per diem?",
  "Up to what amount can a manager approve without escalation?",
  "What security measures are required for remote work?",
];

export const WorkspacePage: React.FC<WorkspacePageProps> = ({ docs, doc, onReplaceDoc, onNavigateToEval }) => {
  const [docList, setDocList] = useState<DocumentItem[]>(docs || (doc ? [doc] : []));
  const [sessionId, setSessionId] = useState<string>('');
  const [runs, setRuns] = useState<RunItem[]>([]);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [liveEvents, setLiveEvents] = useState<RunEvent[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [judgeRunId, setJudgeRunId] = useState<string | null>(null);
  const [showMobileTrace, setShowMobileTrace] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    initSession();
  }, [docList.map(d => d.doc_id).join(',')]);

  const initSession = async () => {
    try {
      const docIds = docList.map(d => d.doc_id);
      if (docIds.length === 0) return;
      const res = await createSession(docIds);
      setSessionId(res.session_id);
      setRuns([]);
      setActiveRunId(null);
      setLiveEvents([]);
    } catch (e) {
      console.error(e);
    }
  };

  const handleAddDocument = async (file: File) => {
    const uploaded = await uploadDocument(file);
    if (sessionId) {
      await addDocumentToSession(sessionId, uploaded.doc_id);
    }
    setDocList(prev => [...prev, uploaded]);
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [runs, liveEvents]);

  // Handle SSE when activeRunId is set
  useEffect(() => {
    if (!activeRunId) return;

    setLiveEvents([]);
    const eventSource = new EventSource(`/api/runs/${activeRunId}/events`);

    const handleEvent = (type: string, dataStr: string) => {
      try {
        const payload = JSON.parse(dataStr);
        setLiveEvents((prev) => [
          ...prev,
          { run_id: activeRunId, seq: prev.length + 1, ts: new Date().toISOString(), type, payload }
        ]);

        if (type === 'final' || type === 'error') {
          eventSource.close();
          // Fetch updated run details
          fetchRun(activeRunId).then((updated) => {
            setRuns((prev) => prev.map((r) => (r.run_id === activeRunId ? updated : r)));
            setActiveRunId(null);
          });
        }
      } catch (err) {
        console.error('Error parsing SSE event:', err);
      }
    };

    eventSource.addEventListener('tool_call', (e: any) => handleEvent('tool_call', e.data));
    eventSource.addEventListener('decision', (e: any) => handleEvent('decision', e.data));
    eventSource.addEventListener('llm_call', (e: any) => handleEvent('llm_call', e.data));
    eventSource.addEventListener('verification', (e: any) => handleEvent('verification', e.data));
    eventSource.addEventListener('final', (e: any) => handleEvent('final', e.data));
    eventSource.addEventListener('error', (e: any) => handleEvent('error', e.data));

    eventSource.onerror = () => {
      eventSource.close();
      // Polling fallback
      setTimeout(() => {
        fetchRun(activeRunId).then((updated) => {
          if (updated.status !== 'running') {
            setRuns((prev) => prev.map((r) => (r.run_id === activeRunId ? updated : r)));
            setActiveRunId(null);
          }
        });
      }, 2000);
    };

    return () => {
      eventSource.close();
    };
  }, [activeRunId]);

  const handleAsk = async (question: string) => {
    if (!sessionId || activeRunId) return;

    try {
      const res = await askQuestion(sessionId, question);
      const newRunId = res.run_id;
      setActiveRunId(newRunId);
      setSelectedRunId(newRunId);

      // Create placeholder run in thread
      const placeholderRun: RunItem = {
        run_id: newRunId,
        session_id: sessionId,
        question: question,
        status: 'running',
        tool_calls_used: 0,
        llm_calls: 0,
        started_at: new Date().toISOString(),
      };
      setRuns((prev) => [...prev, placeholderRun]);
    } catch (e: any) {
      alert(e.message || 'Failed to submit question');
    }
  };

  const currentRun = runs.find((r) => r.run_id === (selectedRunId || runs[runs.length - 1]?.run_id)) || null;
  const judgeRun = runs.find((r) => r.run_id === judgeRunId) || null;

  return (
    <div className="flex h-screen bg-white dark:bg-slate-950 overflow-hidden font-sans text-slate-800 dark:text-slate-100">
      {/* Left Rail: Document Panel */}
      <DocPanel
        docs={docList}
        sessionId={sessionId}
        onNewSession={initSession}
        onReplaceDoc={onReplaceDoc}
        onAddDocument={handleAddDocument}
      />

      {/* Center: Chat Thread & Composer */}
      <main className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Top Navbar */}
        <header className="h-14 border-b border-slate-200 dark:border-slate-800 px-6 flex items-center justify-between shrink-0 bg-white/80 dark:bg-slate-900/80 backdrop-blur-xs">
          <div className="flex items-center gap-2">
            <span className="font-bold text-sm text-slate-900 dark:text-white">PageTurner</span>
            <span className="text-xs text-slate-400">·</span>
            <span className="text-xs text-slate-500 dark:text-slate-400 font-medium truncate max-w-xs">
              {docList.length === 1 ? docList[0]?.title : `${docList.length} documents loaded`}
            </span>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={onNavigateToEval}
              className="text-xs font-medium text-slate-500 hover:text-primary dark:hover:text-primary-dark transition-colors"
            >
              Eval Dashboard
            </button>
            <button
              onClick={() => setShowMobileTrace(!showMobileTrace)}
              className="lg:hidden p-2 rounded-lg border border-slate-200 dark:border-slate-800 text-slate-600"
            >
              <Activity className="w-4 h-4" />
            </button>
          </div>
        </header>

        {/* Message Thread */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
          {runs.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-6 max-w-lg mx-auto">
              <div className="w-12 h-12 rounded-2xl bg-primary/10 text-primary dark:text-primary-dark flex items-center justify-center">
                <MessageSquare className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <h3 className="font-bold text-slate-800 dark:text-slate-100 text-base">Ready to answer questions</h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Select a suggested question or type your own below. The agent operates under a strict budget of at most 6 document-tool calls.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 w-full text-left">
                {SAMPLE_QUESTIONS.map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleAsk(q)}
                    className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-900/60 hover:border-primary/40 dark:hover:border-primary-dark/40 hover:bg-white dark:hover:bg-slate-900 text-xs text-slate-700 dark:text-slate-300 transition-all font-medium flex items-center justify-between group"
                  >
                    <span>{q}</span>
                    <Sparkles className="w-3.5 h-3.5 text-primary opacity-0 group-hover:opacity-100 transition-opacity shrink-0 ml-1" />
                  </button>
                ))}
              </div>
            </div>
          ) : (
            runs.map((r) => {
              const isCurrentActive = r.run_id === activeRunId;
              return (
                <div key={r.run_id} className="space-y-4 max-w-3xl mx-auto">
                  {/* User Question */}
                  <div className="flex justify-end">
                    <div className="max-w-xl p-3.5 rounded-2xl rounded-tr-xs bg-primary text-white text-sm shadow-xs leading-relaxed">
                      {r.question}
                    </div>
                  </div>

                  {/* Agent Response */}
                  {isCurrentActive ? (
                    <AgentStepper events={liveEvents} />
                  ) : (
                    <AnswerCard run={r} onOpenJudge={(id) => setJudgeRunId(id)} />
                  )}
                </div>
              );
            })
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Composer Footer */}
        <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur-xs max-w-3xl w-full mx-auto">
          <Composer onSend={handleAsk} disabled={Boolean(activeRunId)} />
        </div>
      </main>

      {/* Right Rail: Trace Panel */}
      <div className={`${showMobileTrace ? 'block fixed inset-0 z-40 bg-white dark:bg-slate-950' : 'hidden lg:block'}`}>
        <TracePanel
          run={currentRun}
          liveEvents={activeRunId ? liveEvents : []}
          onOpenJudge={currentRun ? () => setJudgeRunId(currentRun.run_id) : undefined}
        />
      </div>

      {/* Judge Mode Modal */}
      {judgeRun && (
        <JudgeView run={judgeRun} onClose={() => setJudgeRunId(null)} />
      )}
    </div>
  );
};