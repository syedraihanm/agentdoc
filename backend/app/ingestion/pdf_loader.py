import os
import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
import pymupdf

from backend.app.config import settings
from backend.app.storage.repo import Repo
from backend.app.ingestion.normalize import normalize_text, normalize_numeric_variant
from backend.app.ingestion.headings import extract_headings
from backend.app.ingestion.tables import extract_tables_as_markdown
from backend.app.ingestion.ocr import perform_ocr

class IngestionError(Exception):
    def __init__(self, code: str, message: str, details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}

def ingest_pdf(file_path: Path | str, original_filename: str, repo: Repo) -> dict:
    path = Path(file_path)
    if not path.exists():
        raise IngestionError("not_found", "Uploaded file not found.")

    # 1. File size check
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_MB:
        raise IngestionError("too_large", f"File exceeds maximum size of {settings.MAX_UPLOAD_MB}MB.")

    # Magic byte check
    with open(path, "rb") as f:
        header = f.read(5)
        if header != b"%PDF-":
            raise IngestionError("not_pdf", "File is not a valid PDF (invalid magic bytes).")
        f.seek(0)
        sha256 = hashlib.sha256(f.read()).hexdigest()

    # Deduplication check
    existing = repo.get_document_by_sha256(sha256)
    if existing:
        return existing

    # 2. Open with PyMuPDF
    try:
        doc = pymupdf.open(str(path))
    except Exception as e:
        raise IngestionError("corrupt_pdf", f"Could not read PDF: {str(e)}")

    if doc.needs_pass:
        doc.close()
        raise IngestionError("encrypted_pdf", "PDF is password protected. Please provide an unencrypted document.")

    num_pages = len(doc)
    if num_pages == 0:
        doc.close()
        raise IngestionError("corrupt_pdf", "PDF contains 0 pages.")

    if num_pages > settings.MAX_PAGES:
        doc.close()
        raise IngestionError("too_large", f"PDF has {num_pages} pages, which exceeds the limit of {settings.MAX_PAGES}.")

    warnings = []
    scanned_pages = []
    truncated_pages = []
    total_chars = 0
    pages_data = []

    for p_idx in range(num_pages):
        p_num = p_idx + 1
        page = doc[p_idx]
        
        # Sort=True for natural reading order
        try:
            text = page.get_text("text", sort=True)
        except Exception:
            text = ""

        # Markdown tables (P1)
        tables_md = extract_tables_as_markdown(page)
        if tables_md:
            text += tables_md

        # Check for text layer
        if not text.strip():
            ocr_text = perform_ocr(page)
            if ocr_text.strip():
                text = ocr_text
            else:
                text = "[NO TEXT LAYER ON THIS PAGE]"
                scanned_pages.append(p_num)

        # Cap length
        if len(text) > settings.PAGE_TEXT_CHAR_CAP:
            text = text[:settings.PAGE_TEXT_CHAR_CAP] + "\n[TRUNCATED]"
            truncated_pages.append(p_num)

        total_chars += len(text)
        norm = normalize_text(text)
        norm_num = normalize_numeric_variant(norm)

        pages_data.append({
            "page_number": p_num,
            "text": text,
            "norm": norm,
            "norm_numeric": norm_num
        })

    # Warnings & validations
    if scanned_pages:
        warnings.append(f"Scanned/empty text layer on pages: {scanned_pages[:10]}")
    if truncated_pages:
        warnings.append(f"Pages truncated due to length: {truncated_pages[:10]}")

    if len(scanned_pages) > int(num_pages * 0.80):
        doc.close()
        raise IngestionError("no_text", "Over 80% of pages have no text layer. Document appears to be a scanned image.")

    avg_chars = total_chars / num_pages if num_pages > 0 else 0
    if avg_chars < 50:
        warnings.append("Low text density detected (<50 characters per page).")

    # Headings extraction
    headings, headings_source = extract_headings(doc)
    if headings_source == "synthetic_first_line":
        warnings.append("Document lacks bookmarks or clear headers; using synthetic outline.")

    # Determine Title
    meta = doc.metadata or {}
    meta_title = meta.get("title", "").strip()
    title = ""
    if meta_title and len(meta_title) > 2 and not meta_title.lower().endswith(".pdf"):
        title = meta_title
    elif headings:
        title = headings[0]["title"]
    else:
        title = Path(original_filename).stem.replace("_", " ").title()

    doc.close()

    doc_id = str(uuid.uuid4())[:8]
    uploaded_at = datetime.now(timezone.utc).isoformat()

    # Save to storage
    repo.save_document(
        doc_id=doc_id,
        title=title,
        filename=original_filename,
        sha256=sha256,
        num_pages=num_pages,
        headings_source=headings_source,
        headings_count=len(headings),
        author=meta.get("author") or None,
        created=meta.get("creationDate") or None,
        warnings=warnings,
        uploaded_at=uploaded_at
    )
    repo.save_pages(doc_id, pages_data)
    repo.save_headings(doc_id, headings)

    return repo.get_document(doc_id)
