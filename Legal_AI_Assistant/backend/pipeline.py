import io
import os
import uuid
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_text_splitters import RecursiveCharacterTextSplitter
from PyPDF2 import PdfReader

# Load API key from backend/.env
load_dotenv(Path(__file__).resolve().parent / ".env")

MODEL_NAME = "openai/gpt-oss-120b"
client = chromadb.PersistentClient(
    path=str(Path(__file__).resolve().parent / "database" / "chroma_db")
)
collection = None
llm = None


def get_llm():
    global llm
    if llm is None:
        if not os.getenv("GROQ_API_KEY"):
            raise RuntimeError("GROQ_API_KEY is missing from backend/.env")
        llm = ChatGroq(model=MODEL_NAME, temperature=0)
    return llm


def index_pdf(pdf_bytes: bytes):
    """Read uploaded PDF, split into chunks, and store in ChromaDB."""
    global collection
    if not pdf_bytes:
        raise ValueError("The uploaded PDF is empty.")

    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""

    if not text.strip():
        raise ValueError("No readable text found. Scanned PDFs need OCR.")

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_text(text)

    # Start a clean collection for this uploaded document.
    collection_name = "legal_contract_current"
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass

    collection = client.create_collection(collection_name)
    collection.add(documents=chunks, ids=["c" + str(i) for i in range(len(chunks))])
    return len(chunks)


def answer_question(question: str, history=None):
    """Answer using PDF context and the last 5 conversation exchanges."""
    if collection is None:
        return "Please upload a PDF first.", []

    if not question.strip():
        return "Please enter a question.", []

    count = collection.count()
    if count == 0:
        return "No text was indexed from this PDF.", []

    result = collection.query(query_texts=[question], n_results=min(3, count))
    context = result["documents"][0] if result.get("documents") else []

    past_chat = (history or [])[-10:]  # last 5 user/assistant exchanges
    chat_text = "\\n".join(
        f"{item.get('role', 'user')}: {item.get('content', '')}"
        for item in past_chat
        if item.get("role") in ("user", "assistant")
    )

    prompt = f"""
You are a contract assistant. Answer the current question using the PDF context.
Use the past conversation only to understand follow-up questions and references.
Do not treat conversation history as evidence about the contract.
Do not invent legal facts. If the PDF context does not contain the answer,
reply exactly: "Answer Not found in given context."
Keep the answer concise, around 2 to 6 lines.

Past conversation (for context only):
{chat_text}

Question:
{question}

PDF context:
{context}
"""
    response = get_llm().invoke(prompt)
    return response.content, context
