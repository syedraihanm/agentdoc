# PageTurner — Budgeted Document-Answering Agent

> **Hackathon Track:** AI/ML — Agentic Systems and Harness Design (2026)  
> **Team:** PageTurner  
> **Core Constraint:** Answers questions about uploaded PDFs using only four metered document tools and a hard budget of **≤ 6 tool calls per question**. No RAG, no embeddings, no vector database.

---

## Key Features

1. **Deterministic Controller & Tool Gateway**: The LLM is a planning policy proposing JSON actions. The Python controller validates, meters, and enforces a hard wall at 6 calls. A 7th call cannot execute.
2. **Headings-First Orientation**: Automatically runs `list_headings` as Call #1 to extract document structure, cross-reference targets, and amendment sections for zero additional calls.
3. **Contradiction & Supersession Reasoning**: Detects amendment sections and unread later hits to resolve superseding terms (e.g. amendments/errata overriding base policies).
4. **Prompt Injection Defense**: Document text is isolated inside `<document_data>` delimiters with per-run boundary tokens. Injection attempts are flagged and stripped from final answers.
5. **Deterministic Verifier**: Verifies every factual claim against verbatim quotes in fetched pages; ungrounded answers are automatically downgraded to `"insufficient information"`.
6. **Live Trace & Judge Mode**: Real-time SSE streaming of tool calls, prompt/response inspection, and one-click JSON/Markdown trace exports.

---

## Quickstart & Setup

### Prerequisites
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- Node.js 18+ and npm

### 1. Install Dependencies
```bash
# Python dependencies via uv
uv sync

# Frontend dependencies
npm --prefix frontend install
npm --prefix frontend run build
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env to set your LLM provider and API key:
# LLM_PROVIDER=gemini (or openai, anthropic, ollama)
# GOOGLE_API_KEY=...
```

### 3. Run the Application
```bash
# Start backend (serves API and built frontend)
uv run uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
Open your browser at: **`http://localhost:8000`**

To run with live Vite HMR during frontend development:
```bash
npm --prefix frontend run dev
```

---

## Running Tests & Verification

### Unit & Compliance Tests
```bash
uv run pytest
```
Runs 26 automated tests covering:
- Exact tool return shapes and contract validation
- Gateway budget enforcement and refusal on 7th call
- Import-boundary AST scans (proves agent cannot touch raw PDF or SQLite pages table)
- Banned dependency scanner (zero embeddings, vector DBs, or agentic frameworks)
- Adversarial FakeLLM attack tests

### Automated Eval Benchmark (14 Cases)
```bash
uv run python scripts/run_eval.py
```
Executes the comprehensive test suite across both outline and no-outline demo variants, measuring:
- Budget compliance (100% ≤ 6 calls)
- Multi-page synthesis
- Contradiction resolution
- Calibrated abstention (unanswerable questions)
- Injection resilience

---

## Project Structure

```
pageturner/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app & static file router
│   │   ├── config.py            # Configuration & flags
│   │   ├── api/                 # REST & SSE endpoints
│   │   ├── storage/             # SQLite DB & repositories
│   │   ├── ingestion/           # PyMuPDF parser, normalizer, headings cascade
│   │   ├── tools/               # Backend, gateway, budget, logging shim
│   │   ├── agent/               # Controller, ledger, signals, verifier, LLM clients
│   │   └── eval/                # Cases schema & runner
│   └── tests/                   # Unit, compliance, and controller tests
├── frontend/
│   ├── src/                     # React 18 + TypeScript + Tailwind CSS UI
│   └── package.json
├── scripts/
│   ├── make_demo_pdf.py         # Generates test PDFs with/without outline
│   └── run_eval.py              # Automated 14-case benchmark runner
├── docs/
│   ├── MEMO.md                  # Hackathon technical memo
│   ├── DEFENSE_NOTES.md         # Judge defense Q&A
│   └── ASSUMPTIONS.md           # Implementation assumptions
└── traces/                      # Generated run & session traces
```