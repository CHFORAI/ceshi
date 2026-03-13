# Backend (FastAPI + LangChain + SQLite + Qwen)

## Run

Create a virtualenv, then:

```bash
pip install -r requirements.txt
set DASHSCOPE_API_KEY=your_key
set SQLITE_PATH=c:\path\to\data.db
uvicorn app.main:app --reload --port 8000
```

## Endpoints

- `GET /api/health`
- `GET /api/sessions`
- `POST /api/sessions`
- `PATCH /api/sessions/{id}`
- `DELETE /api/sessions/{id}`
- `POST /api/chat/{sessionId}/stream` (SSE)

