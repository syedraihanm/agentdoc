CREATE TABLE IF NOT EXISTS documents (
  doc_id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  filename TEXT NOT NULL,
  sha256 TEXT NOT NULL,
  num_pages INTEGER NOT NULL,
  headings_source TEXT NOT NULL,
  headings_count INTEGER NOT NULL,
  author TEXT,
  created TEXT,
  warnings_json TEXT NOT NULL DEFAULT '[]',
  uploaded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pages (
  doc_id TEXT NOT NULL,
  page_number INTEGER NOT NULL,
  text TEXT NOT NULL,
  norm TEXT NOT NULL,
  norm_numeric TEXT NOT NULL,
  PRIMARY KEY (doc_id, page_number)
);

CREATE TABLE IF NOT EXISTS headings (
  doc_id TEXT NOT NULL,
  idx INTEGER NOT NULL,
  title TEXT NOT NULL,
  level INTEGER NOT NULL,
  page INTEGER NOT NULL,
  PRIMARY KEY (doc_id, idx)
);

CREATE TABLE IF NOT EXISTS sessions (
  session_id TEXT PRIMARY KEY,
  doc_id TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS session_documents (
  session_id TEXT NOT NULL,
  doc_id TEXT NOT NULL,
  added_at TEXT NOT NULL,
  PRIMARY KEY (session_id, doc_id)
);

CREATE TABLE IF NOT EXISTS runs (
  run_id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  question TEXT NOT NULL,
  status TEXT NOT NULL,
  answer_json TEXT,
  tool_calls_used INTEGER DEFAULT 0,
  llm_calls INTEGER DEFAULT 0,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  latency_ms INTEGER
);

CREATE TABLE IF NOT EXISTS events (
  run_id TEXT NOT NULL,
  seq INTEGER NOT NULL,
  ts TEXT NOT NULL,
  type TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  PRIMARY KEY (run_id, seq)
);

CREATE TABLE IF NOT EXISTS eval_results (
  eval_id TEXT NOT NULL,
  case_id TEXT NOT NULL,
  passed INTEGER NOT NULL,
  details_json TEXT NOT NULL,
  PRIMARY KEY (eval_id, case_id)
);
