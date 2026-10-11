import os
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from backend.app.config import settings
from backend.app.storage.repo import Repo
from backend.app.api.deps import get_repo
from backend.app.ingestion.pdf_loader import ingest_pdf, IngestionError
from scripts.make_demo_pdf import create_demo_pdf

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("", status_code=201)
async def upload_document(file: UploadFile = File(...), repo: Repo = Depends(get_repo)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail={"code": "not_pdf", "message": "Uploaded file must be a PDF."})

    upload_dir = settings.UPLOADS_DIR
    upload_dir.mkdir(parents=True, exist_ok=True)
    temp_path = upload_dir / f"upload_{file.filename}"

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        doc = ingest_pdf(temp_path, file.filename, repo)
        return doc
    except IngestionError as ie:
        raise HTTPException(status_code=400, detail={"code": ie.code, "message": ie.message, "details": ie.details})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"code": "internal_error", "message": str(e)})
    finally:
        if not settings.KEEP_UPLOADS and temp_path.exists():
            temp_path.unlink()

@router.get("")
async def list_documents(repo: Repo = Depends(get_repo)):
    return repo.list_documents()

@router.delete("/{doc_id}", status_code=204)
async def delete_document(doc_id: str, repo: Repo = Depends(get_repo)):
    deleted = repo.delete_document(doc_id)
    if not deleted:
        raise HTTPException(status_code=404, detail={"code": "doc_not_found", "message": "Document not found"})
    return None

demo_router = APIRouter(prefix="/demo", tags=["demo"])

@demo_router.post("/load", status_code=201)
async def load_demo_document(repo: Repo = Depends(get_repo)):
    demo_pdf_path = settings.BASE_DIR / "data" / "demo_helix_policy.pdf"
    if not demo_pdf_path.exists():
        create_demo_pdf(demo_pdf_path, include_outline=True)
    
    doc = ingest_pdf(demo_pdf_path, "demo_helix_policy.pdf", repo)
    return doc