from typing import Any
from backend.app.storage.repo import Repo
from backend.app.tools.schemas import ToolError
from backend.app.ingestion.normalize import normalize_text, normalize_numeric_variant, validate_keyword

class ToolBackend:
    """The ONLY module permitted to access raw document page text and headings tables."""
    def __init__(self, repo: Repo):
        self.repo = repo

    def list_documents(self, doc_ids: list[str] | None = None) -> list[dict[str, Any]]:
        docs = self.repo.list_documents(doc_ids=doc_ids)
        results = []
        for d in docs:
            results.append({
                "doc_id": d["doc_id"],
                "title": d["title"],
                "metadata": {
                    "filename": d["filename"],
                    "num_pages": d["num_pages"],
                    "created": d.get("created"),
                    "author": d.get("author")
                }
            })
        return results

    def list_headings(self, doc_id: str) -> list[dict[str, Any]]:
        doc = self.repo.get_document(doc_id)
        if not doc:
            raise ToolError("unknown_document", f"Document '{doc_id}' not found.")
        headings = self.repo.get_headings(doc_id)
        return [{"title": h["title"], "level": h["level"], "page": h["page"]} for h in headings]

    def get_page(self, doc_id: str, page_number: int) -> dict[str, Any]:
        if not isinstance(page_number, int) or isinstance(page_number, bool):
            raise ToolError("invalid_args", "page_number must be an integer.")
        doc = self.repo.get_document(doc_id)
        if not doc:
            raise ToolError("unknown_document", f"Document '{doc_id}' not found.")
        if page_number < 1 or page_number > doc["num_pages"]:
            raise ToolError("page_out_of_range", f"Page {page_number} is out of range [1, {doc['num_pages']}].")
        
        page = self.repo.get_page(doc_id, page_number)
        if not page:
            raise ToolError("page_not_found", f"Page {page_number} could not be retrieved.")
        return {
            "page_number": page["page_number"],
            "text": page["text"]
        }

    def search_keyword(self, doc_id: str, keyword: str) -> list[int]:
        if not isinstance(keyword, str):
            raise ToolError("invalid_args", "keyword must be a string.")
        doc = self.repo.get_document(doc_id)
        if not doc:
            raise ToolError("unknown_document", f"Document '{doc_id}' not found.")
        
        valid, msg = validate_keyword(keyword)
        if not valid:
            raise ToolError("invalid_keyword", msg)
        
        norm_kw = normalize_text(keyword)
        pages = self.repo.search_pages_keyword(doc_id, norm_kw)
        return pages
