import sys
import json
from pathlib import Path
from datetime import datetime, timezone

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.config import settings
from backend.app.storage.db import init_db
from backend.app.storage.repo import Repo
from backend.app.ingestion.pdf_loader import ingest_pdf
from backend.app.eval.runner import run_evaluation
from backend.app.api.deps import get_llm_client
from scripts.make_demo_pdf import create_demo_pdf

def main():
    print("=" * 60)
    print("PageTurner Automated Evaluation Benchmark (14 Cases)")
    print("=" * 60)

    init_db()
    repo = Repo()
    llm = get_llm_client()

    data_dir = settings.BASE_DIR / "data"
    p_outline = data_dir / "demo_helix_policy.pdf"
    p_no_outline = data_dir / "demo_helix_policy_no_outline.pdf"

    if not p_outline.exists():
        create_demo_pdf(p_outline, include_outline=True)
    if not p_no_outline.exists():
        create_demo_pdf(p_no_outline, include_outline=False)

    print("\n[1/2] Ingesting Outline Variant...")
    doc_outline = ingest_pdf(p_outline, "demo_helix_policy.pdf", repo)
    print(f"Ingested: {doc_outline['title']} (ID: {doc_outline['doc_id']}, Source: {doc_outline['headings_source']})")

    print("\nRunning Benchmark on Outline Variant...")
    res_outline = run_evaluation(doc_outline["doc_id"], repo, llm)
    print(f"Outline Variant Results: {res_outline['passed']}/{res_outline['total']} passed ({res_outline['pass_rate']}%), Budget Compliance: {res_outline['budget_compliance_rate']}%")

    print("\n[2/2] Ingesting No-Outline (Heuristic) Variant...")
    doc_no_outline = ingest_pdf(p_no_outline, "demo_helix_policy_no_outline.pdf", repo)
    print(f"Ingested: {doc_no_outline['title']} (ID: {doc_no_outline['doc_id']}, Source: {doc_no_outline['headings_source']})")

    print("\nRunning Benchmark on No-Outline Variant...")
    res_no_outline = run_evaluation(doc_no_outline["doc_id"], repo, llm)
    print(f"No-Outline Variant Results: {res_no_outline['passed']}/{res_no_outline['total']} passed ({res_no_outline['pass_rate']}%), Budget Compliance: {res_no_outline['budget_compliance_rate']}%")

    # Generate traces report
    traces_dir = settings.TRACES_DIR
    traces_dir.mkdir(parents=True, exist_ok=True)
    report_file = traces_dir / f"eval_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.md"

    report_lines = [
        "# PageTurner Evaluation Benchmark Report",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        f"Provider: `{settings.LLM_PROVIDER}` | Model: `{settings.LLM_MODEL}` | Hard Budget: 6 calls\n",
        "## Summary",
        f"- **Outline Variant:** {res_outline['passed']}/{res_outline['total']} passed ({res_outline['pass_rate']}%) | Budget Compliance: {res_outline['budget_compliance_rate']}%",
        f"- **No-Outline Variant:** {res_no_outline['passed']}/{res_no_outline['total']} passed ({res_no_outline['pass_rate']}%) | Budget Compliance: {res_no_outline['budget_compliance_rate']}%\n",
        "## Case Details (Outline Variant)",
        "| ID | Question | Expected | Actual | Tool Calls | Result |",
        "|---|---|---|---|---|---|"
    ]

    for c in res_outline["cases"]:
        d = c["details"]
        res_icon = "PASSED" if c["passed"] else "FAILED"
        report_lines.append(f"| {c['case_id']} | {d['question']} | {d.get('expected_status')} | {d.get('actual_status')} | {d.get('tool_calls_used')}/6 | {res_icon} |")

    report_file.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"\nSaved evaluation report to: {report_file}")

if __name__ == "__main__":
    main()