# Flowsome Backend

Privacy-first AI assistant backend for government departments. The assistant runs
local models through Ollama so documents and chat data never leave the machine.

## Requirements

- Python 3.10+
- PostgreSQL
- Ollama with the local models pulled:

```powershell
ollama pull gemma4:e2b
ollama pull qwen2.5-coder:3b
```

## Setup

```powershell
python -m venv flowsome-env
flowsome-env\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file:

```
DATABASE_URL=postgresql://user:password@localhost:5432/flowsome
TAVILY_API_KEY=your_tavily_key
```

`WORKSPACE_ROOT` is optional and limits the file tools to one directory
(defaults to the current user's home directory).

## Run

```powershell
uvicorn main:app --reload
```

- API: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`

The frontend is a separate Electron + Bun + TypeScript project and connects to
this backend over HTTP and Server-Sent Events.

## Layout

```
main.py              FastAPI app, lifespan, CORS, static uploads
config.py            Environment settings
api/routes.py        Chat stream, threads, history, image upload
agent/               Agent factory, models, prompt, middleware, SSE helpers
tools/               File, image, search, Python task, and RAG tools
services/            PDF reading and text splitting
database/            SQLAlchemy session, thread model, Chroma vector store
scripts/             FastMCP math server
```

There is no automated test suite. Verify changes by starting the server and
exercising the affected endpoint or tool.
