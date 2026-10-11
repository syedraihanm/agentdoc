import json
import sqlite3
from typing import Any
from backend.app.storage.db import get_db

class Repo:
    def __init__(self, db_path=None):
        self.db_path = db_path

    # Documents
    def save_document(self, doc_id: str, title: str, filename: str, sha256: str,
                      num_pages: int, headings_source: str, headings_count: int,
                      author: str | None, created: str | None, warnings: list[str], uploaded_at: str):
        with get_db(self.db_path) as db:
            db.execute('''
                INSERT INTO documents (doc_id, title, filename, sha256, num_pages,
                                       headings_source, headings_count, author, created,
                                       warnings_json, uploaded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (doc_id, title, filename, sha256, num_pages, headings_source,
                  headings_count, author, created, json.dumps(warnings), uploaded_at))

    def get_document(self, doc_id: str) -> dict[str, Any] | None:
        with get_db(self.db_path) as db:
            row = db.execute('SELECT * FROM documents WHERE doc_id = ?', (doc_id,)).fetchone()
            if not row:
                return None
            d = dict(row)
            d['warnings'] = json.loads(d.pop('warnings_json', '[]'))
            return d

    def get_document_by_sha256(self, sha256: str) -> dict[str, Any] | None:
        with get_db(self.db_path) as db:
            row = db.execute('SELECT * FROM documents WHERE sha256 = ?', (sha256,)).fetchone()
            if not row:
                return None
            d = dict(row)
            d['warnings'] = json.loads(d.pop('warnings_json', '[]'))
            return d

    def list_documents(self, doc_ids: list[str] | None = None) -> list[dict[str, Any]]:
        with get_db(self.db_path) as db:
            if doc_ids is not None:
                if not doc_ids:
                    return []
                placeholders = ', '.join(['?'] * len(doc_ids))
                rows = db.execute(f'SELECT * FROM documents WHERE doc_id IN ({placeholders}) ORDER BY uploaded_at DESC', tuple(doc_ids)).fetchall()
            else:
                rows = db.execute('SELECT * FROM documents ORDER BY uploaded_at DESC').fetchall()
            result = []
            for row in rows:
                d = dict(row)
                d['warnings'] = json.loads(d.pop('warnings_json', '[]'))
                result.append(d)
            return result

    def delete_document(self, doc_id: str) -> bool:
        with get_db(self.db_path) as db:
            cur = db.execute('DELETE FROM documents WHERE doc_id = ?', (doc_id,))
            db.execute('DELETE FROM pages WHERE doc_id = ?', (doc_id,))
            db.execute('DELETE FROM headings WHERE doc_id = ?', (doc_id,))
            return cur.rowcount > 0

    # Pages (Only to be called by ingestion and tools/backend.py)
    def save_pages(self, doc_id: str, pages: list[dict[str, Any]]):
        with get_db(self.db_path) as db:
            db.executemany('''
                INSERT INTO pages (doc_id, page_number, text, norm, norm_numeric)
                VALUES (?, ?, ?, ?, ?)
            ''', [(doc_id, p['page_number'], p['text'], p['norm'], p['norm_numeric']) for p in pages])

    def get_page(self, doc_id: str, page_number: int) -> dict[str, Any] | None:
        with get_db(self.db_path) as db:
            row = db.execute('''
                SELECT page_number, text FROM pages
                WHERE doc_id = ? AND page_number = ?
            ''', (doc_id, page_number)).fetchone()
            return dict(row) if row else None

    def search_pages_keyword(self, doc_id: str, norm_keyword: str) -> list[int]:
        # Fast lexical substring match over pre-normalized text
        with get_db(self.db_path) as db:
            rows = db.execute('''
                SELECT page_number, norm, norm_numeric FROM pages
                WHERE doc_id = ?
                ORDER BY page_number ASC
            ''', (doc_id,)).fetchall()
            matching_pages = []
            for row in rows:
                if norm_keyword in row['norm'] or norm_keyword in row['norm_numeric']:
                    matching_pages.append(row['page_number'])
            return sorted(list(set(matching_pages)))

    # Headings (Only to be called by ingestion and tools/backend.py)
    def save_headings(self, doc_id: str, headings: list[dict[str, Any]]):
        with get_db(self.db_path) as db:
            db.executemany('''
                INSERT INTO headings (doc_id, idx, title, level, page)
                VALUES (?, ?, ?, ?, ?)
            ''', [(doc_id, i, h['title'], h['level'], h['page']) for i, h in enumerate(headings)])

    def get_headings(self, doc_id: str) -> list[dict[str, Any]]:
        with get_db(self.db_path) as db:
            rows = db.execute('''
                SELECT title, level, page FROM headings
                WHERE doc_id = ?
                ORDER BY idx ASC
            ''', (doc_id,)).fetchall()
            return [dict(r) for r in rows]

    # Sessions
    def create_session(self, session_id: str, doc_id: str | list[str], created_at: str):
        with get_db(self.db_path) as db:
            primary_doc_id = doc_id[0] if isinstance(doc_id, list) else doc_id
            db.execute('INSERT INTO sessions (session_id, doc_id, created_at) VALUES (?, ?, ?)',
                       (session_id, primary_doc_id, created_at))
            doc_list = doc_id if isinstance(doc_id, list) else [doc_id]
            for did in doc_list:
                db.execute('INSERT OR IGNORE INTO session_documents (session_id, doc_id, added_at) VALUES (?, ?, ?)',
                           (session_id, did, created_at))

    def add_document_to_session(self, session_id: str, doc_id: str, added_at: str):
        with get_db(self.db_path) as db:
            db.execute('INSERT OR IGNORE INTO session_documents (session_id, doc_id, added_at) VALUES (?, ?, ?)',
                       (session_id, doc_id, added_at))

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        with get_db(self.db_path) as db:
            row = db.execute('SELECT * FROM sessions WHERE session_id = ?', (session_id,)).fetchone()
            if not row:
                return None
            sess = dict(row)
            # Fetch all associated documents
            doc_rows = db.execute('''
                SELECT d.* FROM documents d
                JOIN session_documents sd ON d.doc_id = sd.doc_id
                WHERE sd.session_id = ?
                ORDER BY sd.added_at ASC
            ''', (session_id,)).fetchall()
            docs = []
            for dr in doc_rows:
                d = dict(dr)
                d['warnings'] = json.loads(d.pop('warnings_json', '[]'))
                docs.append(d)
            if not docs and sess.get("doc_id"):
                primary = self.get_document(sess["doc_id"])
                if primary:
                    docs.append(primary)
            sess["documents"] = docs
            sess["doc_ids"] = [d["doc_id"] for d in docs]
            return sess

    def get_session_doc_ids(self, session_id: str) -> list[str]:
        sess = self.get_session(session_id)
        if not sess:
            return []
        return sess.get("doc_ids", [sess["doc_id"]])

    # Runs
    def create_run(self, run_id: str, session_id: str, question: str, status: str, started_at: str):
        with get_db(self.db_path) as db:
            db.execute('''
                INSERT INTO runs (run_id, session_id, question, status, started_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (run_id, session_id, question, status, started_at))

    def update_run(self, run_id: str, status: str, answer_json: str | None,
                   tool_calls_used: int, llm_calls: int, finished_at: str, latency_ms: int):
        with get_db(self.db_path) as db:
            db.execute('''
                UPDATE runs
                SET status = ?, answer_json = ?, tool_calls_used = ?, llm_calls = ?,
                    finished_at = ?, latency_ms = ?
                WHERE run_id = ?
            ''', (status, answer_json, tool_calls_used, llm_calls, finished_at, latency_ms, run_id))

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        with get_db(self.db_path) as db:
            row = db.execute('SELECT * FROM runs WHERE run_id = ?', (run_id,)).fetchone()
            if not row:
                return None
            d = dict(row)
            if d.get('answer_json'):
                try:
                    d['answer'] = json.loads(d['answer_json'])
                except Exception:
                    d['answer'] = None
            else:
                d['answer'] = None
            return d

    def list_runs_for_session(self, session_id: str) -> list[dict[str, Any]]:
        with get_db(self.db_path) as db:
            rows = db.execute('SELECT * FROM runs WHERE session_id = ? ORDER BY started_at ASC', (session_id,)).fetchall()
            res = []
            for r in rows:
                d = dict(r)
                if d.get('answer_json'):
                    try:
                        d['answer'] = json.loads(d['answer_json'])
                    except Exception:
                        d['answer'] = None
                res.append(d)
            return res

    # Events
    def save_event(self, run_id: str, seq: int, ts: str, event_type: str, payload: dict[str, Any]):
        with get_db(self.db_path) as db:
            db.execute('''
                INSERT INTO events (run_id, seq, ts, type, payload_json)
                VALUES (?, ?, ?, ?, ?)
            ''', (run_id, seq, ts, event_type, json.dumps(payload)))

    def get_events(self, run_id: str) -> list[dict[str, Any]]:
        with get_db(self.db_path) as db:
            rows = db.execute('SELECT * FROM events WHERE run_id = ? ORDER BY seq ASC', (run_id,)).fetchall()
            events = []
            for r in rows:
                events.append({
                    'run_id': r['run_id'],
                    'seq': r['seq'],
                    'ts': r['ts'],
                    'type': r['type'],
                    'payload': json.loads(r['payload_json'])
                })
            return events

    # Eval
    def save_eval_result(self, eval_id: str, case_id: str, passed: bool, details: dict[str, Any]):
        with get_db(self.db_path) as db:
            db.execute('''
                INSERT OR REPLACE INTO eval_results (eval_id, case_id, passed, details_json)
                VALUES (?, ?, ?, ?)
            ''', (eval_id, case_id, 1 if passed else 0, json.dumps(details)))

    def get_eval_results(self, eval_id: str) -> list[dict[str, Any]]:
        with get_db(self.db_path) as db:
            rows = db.execute('SELECT * FROM eval_results WHERE eval_id = ?', (eval_id,)).fetchall()
            return [{'case_id': r['case_id'], 'passed': bool(r['passed']), 'details': json.loads(r['details_json'])} for r in rows]
