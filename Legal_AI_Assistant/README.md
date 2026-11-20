# Legal AI Assistant - Contract Chat (Functionality 1)

Simple project structure:
- `frontend/`: HTML, CSS, JavaScript
- `backend/main.py`: FastAPI API and PostgreSQL PDF storage
- `backend/pipeline.py`: PDF extraction, chunking, ChromaDB retrieval, Groq response, and last 5 chat exchanges as context
- `backend/database/chroma_db/`: persistent ChromaDB files

## Setup
1. Create/activate your Python environment.
2. From the project root install: `python -m pip install -r backend/requirements.txt`
3. Copy `backend/.env.example` to `backend/.env`, then set your Groq API key and PostgreSQL URL.
4. Ensure PostgreSQL is running and the database named `legal_ai` exists (create it once in PostgreSQL).
5. Start from the project root: `uvicorn backend.main:app --reload`
6. Open http://127.0.0.1:8000

PostgreSQL stores uploaded PDF file bytes and filename. ChromaDB stores extracted chunks for RAG. Chat context sends the last 5 exchanges (10 messages) with the question. If PostgreSQL isn't configured, PDF indexing still works and the upload response tells you it wasn't saved in PostgreSQL.
