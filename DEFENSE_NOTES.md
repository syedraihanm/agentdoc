# Defense Notes & Judge Q&A: PageTurner

### Q1: Why not let the LLM call tools freely in a standard function-calling loop?
**Answer:** A free-form function calling loop delegates trust to the model. In an adversarial or resource-constrained environment:
1. The model can loop indefinitely or exceed budget.
2. Injected prompt instructions within document text can hijack arguments, invent tools, or switch documents.
3. The model will frequently answer from parametric memory when a document page doesn't quite answer the question.
By making the LLM a *policy* that proposes actions and our controller the *executor*, we guarantee safety, budget enforcement, and grounding.

### Q2: How do you guarantee the agent never exceeds 6 tool calls?
**Answer:** The `ToolGateway` wraps execution with a thread-safe `Budget(max_calls=6)` object. When `budget.used >= 6`, the gateway physically refuses execution, logs a `refused` event, and raises an internal exception. The 7th call cannot execute. We prove this via `test_gateway_budget.py` and `test_controller_adversarial_llm_cannot_break_budget`.

### Q3: How do you know the final answer is not hallucinated?
**Answer:** Every claim in the final answer requires a verbatim evidence quote. In `verifier.py`, our deterministic post-processor checks every quote against the exact pages fetched during that question. If quotes are absent, fabricated, or numbers are untraceable, the status is automatically downgraded to `"insufficient"` or `"partial"`.

### Q4: How do you handle cases where a later amendment supersedes an earlier rule?
**Answer:** We employ three complementary strategies:
1. **Signal detection:** The controller scans heading titles for terms like `Amendment`, `Appendix`, `Errata`, or `Revision` and exposes these to the planner.
2. **Bracketing:** The prompt instructs the model to inspect both earliest and latest relevant pages for a topic.
3. **Hierarchy of authority:** The answer prompt applies explicit rules: explicit supersession clauses beat base text; errata beat original statements; later effective dates beat earlier dates.

### Q5: What stops prompt injection (e.g., "Ignore previous instructions") inside the PDF?
**Answer:** A five-layer defense in depth:
1. **Channel separation:** Page text is placed strictly inside `<document_data>` delimiters with per-run random boundary tokens.
2. **Sanitization:** Brackets (`<`/`>`) are escaped before entering prompts.
3. **Capability bounds:** Document text cannot register new tools or change `doc_id`.
4. **Detector:** A multi-pattern regex detector scans read pages, flagging injections to the LLM and logging them.
5. **Verifier rejection:** Verifier check V5 strips any injection echoes from the proposed answer.

### Q6: Is `search_keyword` secretly semantic search or BM25?
**Answer:** No. It is pure lexical substring matching over normalized text (NFKC, lowercase, de-hyphenation, and whitespace collapse). It returns only a sorted list of integer page numbers, never text snippets, scores, or counts.

### Q7: Why use synthetic headings when bookmarks are missing?
**Answer:** Real-world documents often lack PDF outlines. Our cascade first checks outline bookmarks, falls back to typographic heuristics (font size, bold, numbering), and if still sparse, creates synthetic single-page entries from the first substantive line of each page. The UI displays an explicit quality badge (`Outline: Bookmarks / Detected / Synthetic`) so judges know the outline source.

### Q8: Where is the cache stored across questions?
**Answer:** Nowhere. Each question starts with a fresh, empty run state and budget. Caching pages across questions would violate the spirit of the 6-call constraint. We enforce this via `test_no_cross_question_cache.py`.