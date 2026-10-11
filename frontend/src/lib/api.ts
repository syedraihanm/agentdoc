export interface DocumentItem {
  doc_id: string;
  title: string;
  filename: string;
  num_pages: number;
  headings_source: string;
  headings_count: number;
  warnings: string[];
  author?: string | null;
  created?: string | null;
  uploaded_at: string;
}

export interface EvidenceItem {
  page: number;
  quote: string;
  supports: string;
  doc_id?: string | null;
}

export interface ConflictChosen {
  page: number;
  quote: string;
  doc_id?: string | null;
}

export interface ConflictItem {
  topic: string;
  chosen: ConflictChosen;
  superseded: ConflictChosen[];
  resolution_rule: string;
}

export interface IgnoredInstruction {
  page: number;
  excerpt: string;
  doc_id?: string | null;
}

export interface AnswerObj {
  status: 'answered' | 'partial' | 'insufficient';
  answer: string;
  evidence: EvidenceItem[];
  conflicts: ConflictItem[];
  calculation?: {
    expression: string;
    result: number;
    operands: { value: number; page: number }[];
  } | null;
  not_found: string[];
  searched_summary?: string | null;
  closest_related?: string | null;
  confidence: 'high' | 'medium' | 'low';
  ignored_instructions: IgnoredInstruction[];
}

export interface ToolCallPayload {
  seq: number;
  tool: string;
  args: Record<string, any>;
  purpose: string;
  status: 'ok' | 'deduped' | 'refused' | 'error';
  result: any;
  result_summary: string;
  duration_ms: number;
  calls_used: number;
  calls_remaining: number;
}

export interface RunEvent {
  run_id: string;
  seq: number;
  ts: string;
  type: string;
  payload: any;
}

export interface RunItem {
  run_id: string;
  session_id: string;
  question: string;
  status: string;
  answer?: AnswerObj | null;
  tool_calls_used: number;
  llm_calls: number;
  started_at: string;
  finished_at?: string | null;
  events?: RunEvent[];
}

export interface SessionData {
  session_id: string;
  doc: DocumentItem | null;
  documents?: DocumentItem[];
  doc_ids?: string[];
  runs: RunItem[];
  active_run_id?: string | null;
}

const API_BASE = '/api';

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

export async function fetchDocuments(): Promise<DocumentItem[]> {
  const res = await fetch(`${API_BASE}/documents`);
  if (!res.ok) throw new Error('Failed to fetch documents');
  return res.json();
}

export async function uploadDocument(file: File): Promise<DocumentItem> {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/documents`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail?.message || 'Upload failed');
  }
  return res.json();
}

export async function loadDemoDocument(): Promise<DocumentItem> {
  const res = await fetch(`${API_BASE}/demo/load`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to load demo document');
  return res.json();
}

export async function deleteDocument(docId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/documents/${docId}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete document');
}

export async function createSession(docIdOrIds: string | string[]): Promise<{ session_id: string; doc_id: string; doc_ids: string[] }> {
  const payload = Array.isArray(docIdOrIds) ? { doc_ids: docIdOrIds } : { doc_id: docIdOrIds };
  const res = await fetch(`${API_BASE}/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to create session');
  return res.json();
}

export async function addDocumentToSession(sessionId: string, docId: string): Promise<{ session_id: string; doc_ids: string[] }> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}/documents`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ doc_id: docId }),
  });
  if (!res.ok) throw new Error('Failed to add document to session');
  return res.json();
}

export async function fetchSession(sessionId: string): Promise<SessionData> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}`);
  if (!res.ok) throw new Error('Failed to fetch session');
  return res.json();
}

export async function askQuestion(sessionId: string, question: string): Promise<{ run_id: string }> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail?.message || 'Failed to submit question');
  }
  return res.json();
}

export async function fetchRun(runId: string): Promise<RunItem> {
  const res = await fetch(`${API_BASE}/runs/${runId}`);
  if (!res.ok) throw new Error('Failed to fetch run');
  return res.json();
}

export async function runEvalSuite(docId?: string): Promise<any> {
  const res = await fetch(`${API_BASE}/eval/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ doc_id: docId }),
  });
  if (!res.ok) throw new Error('Failed to trigger evaluation');
  return res.json();
}

export async function fetchEvalSuite(evalId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/eval/${evalId}`);
  if (!res.ok) throw new Error('Failed to fetch eval results');
  return res.json();
}