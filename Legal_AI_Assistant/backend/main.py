from pathlib import Path
import os

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from backend import pipeline

from urllib.parse import urlparse, unquote
import pg8000

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"
HTML_DIR = FRONTEND_DIR / "html"
CSS_DIR = FRONTEND_DIR / "css"
JS_DIR = FRONTEND_DIR / "js"
app = FastAPI(title="Legal AI Contract Chatbot")


class AskRequest(BaseModel):
    question: str
    history: list[dict] = []


@app.get("/")
def home():
    return FileResponse(HTML_DIR / "index.html")


@app.get("/css/{filename}")
def css_file(filename: str):
    return FileResponse(CSS_DIR / filename)


@app.get("/js/{filename}")
def js_file(filename: str):
    return FileResponse(JS_DIR / filename)


def save_pdf_to_postgres(filename: str, pdf_bytes: bytes):
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        return False

    try:
        url = urlparse(database_url)

        with pg8000.connect(
            user=unquote(url.username),
            password=unquote(url.password),
            host=url.hostname,
            port=url.port or 5432,
            database=url.path.lstrip("/")
        ) as conn:

            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS uploaded_documents (
                    id SERIAL PRIMARY KEY,
                    filename TEXT NOT NULL,
                    file_data BYTEA NOT NULL,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute(
                "INSERT INTO uploaded_documents (filename, file_data) VALUES (%s, %s)",
                (filename, pdf_bytes),
            )

            conn.commit()
            cursor.close()

        return True

    except Exception as exc:
        raise RuntimeError(f"PostgreSQL file save failed: {exc}") from exc


@app.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        chunks = pipeline.index_pdf(pdf_bytes)
        postgres_saved = save_pdf_to_postgres(file.filename, pdf_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return {
        "message": "PDF indexed successfully",
        "filename": file.filename,
        "chunks": chunks,
        "postgres_saved": postgres_saved,
        "postgres_message": "Saved to PostgreSQL." if postgres_saved else "PostgreSQL not configured; PDF indexed in ChromaDB only."
    }


@app.post("/api/ask")
def ask(body: AskRequest):
    if not body.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    try:
        answer, chunks = pipeline.answer_question(body.question, body.history)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Question answering failed: {exc}")
    return {"answer": answer, "chunks": chunks}
