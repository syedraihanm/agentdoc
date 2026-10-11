from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from backend.app.config import settings
from backend.app.storage.db import init_db
from backend.app.api.documents import router as documents_router, demo_router
from backend.app.api.chat import router as chat_router
from backend.app.api.runs import router as runs_router
from backend.app.api.eval import router as eval_router

# Initialize database schema on startup
init_db()

app = FastAPI(
    title="PageTurner API",
    description="Budgeted Document-Answering Agent",
    version="0.1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Public Config & Health
@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "llm_provider": settings.LLM_PROVIDER,
        "model": settings.LLM_MODEL,
        "budget": settings.TOOL_BUDGET
    }

@app.get("/api/config")
async def public_config():
    return {
        "budget": settings.TOOL_BUDGET,
        "max_upload_mb": settings.MAX_UPLOAD_MB,
        "max_pages": settings.MAX_PAGES,
        "multi_doc_mode": settings.MULTI_DOC_MODE,
        "ocr_enabled": settings.ENABLE_OCR
    }

# Include API routers
app.include_router(documents_router, prefix="/api")
app.include_router(demo_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(runs_router, prefix="/api")
app.include_router(eval_router, prefix="/api")

# Serve frontend build if dist folder exists
frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        # Don't intercept API routes
        if full_path.startswith("api/"):
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
        file_path = frontend_dist / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist / "index.html")