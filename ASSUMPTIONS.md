# Assumptions and Interpretations Log

The following interpretations of the problem constraints were made and implemented in PageTurner. Each is configurable via `config.py` / `.env`.

| # | Ambiguity / Question | Default Implemented | Config Flag |
|---|---|---|---|
| **A1** | Does the "6 tool calls" count only document tools, or also planner LLM calls? | Only executed document tools (`list_documents`, `list_headings`, `get_page`, `search_keyword`) count toward the 6. Planner decide calls are hard-capped at ≤4 rounds and logged. | `MAX_DECIDE_ROUNDS=4` |
| **A2** | Does `list_documents` count toward the budget? | Yes, if invoked. In single-document chat mode, `doc_id` is supplied on session creation, so `list_documents` is not needed. In multi-doc mode it is call #1. | `MULTI_DOC_MODE=false` |
| **A3** | Does `list_headings` count? | Yes, counting as call #1 for almost every question. | — |
| **A4** | Do duplicate calls count? | Identical `(tool, args)` within the same run are returned from run cache and marked `deduped` without spending budget. | — |
| **A5** | Do invalid or refused calls count? | Calls rejected by the gateway prior to execution (e.g. unknown tool or bad types) are logged as `refused` and do not consume budget. | — |
| **A6** | Does `list_headings` return page numbers? | Yes: returns `[{title, level, page}]`. | — |
| **A7** | How is keyword matching performed? | Case/accent/hyphenation-insensitive lexical substring search returning only sorted unique page numbers. | — |
| **A8** | Page numbering convention | 1-based physical PDF page indexes. | — |
| **A9** | Follow-up conversation history | Previous user questions and answers (text only, no raw page text) are passed to resolve pronouns. | `HISTORY_TURNS=3` |
| **A10** | Organizers' logging wrapper | Default logging wrapper implements `logging_shim.py` writing to `traces/tool_calls.jsonl`. Can be adapted cleanly. | — |