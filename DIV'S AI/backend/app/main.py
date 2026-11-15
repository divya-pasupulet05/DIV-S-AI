from pathlib import Path
from uuid import uuid4
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from .config import FRONTEND_ORIGIN, UPLOAD_DIR
from .rag_service import ask, ingest

app = FastAPI(title="DIV'S AI RAG API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=[FRONTEND_ORIGIN],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class AskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=4000)

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "DIV'S AI RAG API"}

@app.post("/api/documents/upload")
async def upload(file: UploadFile = File(...)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".pdf", ".txt", ".md"}:
        raise HTTPException(400, "Upload a PDF, TXT or MD file.")
    if not file.filename:
        raise HTTPException(400, "Filename is missing.")
    destination = UPLOAD_DIR / f"{uuid4().hex}_{Path(file.filename).name}"
    try:
        data = await file.read()
        if not data:
            raise HTTPException(400, "The uploaded file is empty.")
        if len(data) > 15 * 1024 * 1024:
            raise HTTPException(413, "Maximum upload size is 15 MB.")
        destination.write_bytes(data)
        result = ingest(destination)
        result["original_filename"] = file.filename
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, str(exc))
    finally:
        await file.close()

@app.post("/api/chat")
def chat(request: AskRequest):
    try:
        return ask(request.question)
    except Exception as exc:
        raise HTTPException(502, str(exc))
