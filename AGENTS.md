# AGENTS.md

Guidance for AI coding assistants working on Flowsome.

## What this project is

Flowsome is a final-year research project: a **privacy-first AI assistant for government departments**. Government staff can chat with an AI assistant to read and classify files, generate letters and PDFs, query/update databases, and work with documents — without sending sensitive data to cloud AI providers.

The research gap: cloud LLMs (ChatGPT, Claude, etc.) are unsuitable for government data because of privacy, confidentiality, and data-sovereignty concerns. Flowsome runs open models **locally through Ollama** instead.

- **This repository (`flowsome-backend`)** — Python FastAPI backend, LangChain/LangGraph agent, tools, RAG, persistence.
- **Frontend (separate folder/repo: `flowsome-frontend`)** — desktop client built with **Bun + TypeScript**, packaged with **Electron** (Next.js renderer). It is NOT in this repository. The two communicate over HTTP and Server-Sent Events (SSE).

Do not assume frontend files exist here. When a task spans both, ask for the frontend path or work against the API contract described below.

## Core capabilities

- **Streaming chatbot** with tool calling and conversation memory per thread.
- **File tools** — read, write, edit, list files/folders (sandboxed to `WORKSPACE_ROOT`, default: user home).
- **System information** — RAM, GPU/VRAM, graphics card brand, CPU, and system brand/model are obtained through `execute_python_task` (the agent generates a Python/PowerShell query); there is no dedicated hardware tool.
- **Image understanding** — vision via local `gemma4:e2b` (attached images are base64-encoded; local paths can be read with `read_image`).
- **RAG over PDFs** — per-document ChromaDB collections, PDF read from local path or URL, chunking, local embeddings (`all-MiniLM-L6-v2`), retrieval, then answer generation with Gemma.
- **Python task execution** — a LangGraph sub-agent writes a Python script, executes it with `subprocess`, retries on failure, and returns stdout. This is the intended path for PDF/letter generation and arbitrary system/database tasks.
- **Internet search** — Tavily (cloud; use only when the query is not sensitive).
- **MCP tools** — `langchain-mcp-adapters` + FastMCP (math server in `scripts/math_server.py`).
- **Human-in-the-loop** — LangGraph interrupts resumed with `Command(resume=...)` via `interruptResponse` in the request body.
- **Thread persistence** — LangGraph `AsyncPostgresSaver` checkpoints plus a SQLAlchemy `threads` table for sidebar metadata.
- **Middleware** — chat title generation and summarization/trimming.

## Architecture and request flow

1. Electron client calls `POST /api/stream` with:
   ```json
   {
     "input": {
       "threadId": "...",
       "messages": [{ "content": "text" }, { "content": "https://.../image.png" }],
       "interruptResponse": { "decisions": [] }
     }
   }
   ```
   The second message, if present, is treated as an attachment URL.
2. `api/routes.py` builds a `HumanMessage` (text-only or text + `image_url`) or a resume `Command`, then calls `agent.astream(...)`.
3. The agent streams with modes `updates`, `messages`, `values`, `tools`, `custom`. Each chunk is cleaned by `agent/serialization.py` and emitted as SSE:
   ```
   event: <mode>
   data: <json>

   ```
   Errors are emitted as `event: error`.
4. `AsyncPostgresSaver` checkpoints messages by `thread_id`; `Thread` rows (Postgres) back the thread list.
5. History is read from the checkpointer state, not from the `threads` table (`GET /api/threads/history/{thread}`).

## Stack

| Layer | Technology |
|---|---|
| API | FastAPI, Uvicorn, Pydantic Settings |
| Agent | LangChain `create_agent` (v1 API), LangGraph `StateGraph`, `langgraph-checkpoint-postgres` |
| Local models | Ollama — `gemma4:e2b` (chat/vision/RAG), `qwen2.5-coder:3b` (titles, summarization) |
| Embeddings / vector store | ChromaDB (persistent, `./chroma_db`) + SentenceTransformers `all-MiniLM-L6-v2` |
| Relational DB | PostgreSQL via SQLAlchemy (threads) and LangGraph checkpointer |
| Tools | MCP (`langchain-mcp-adapters`, FastMCP), Tavily, pypdf, `RecursiveCharacterTextSplitter` |
| Frontend | Separate project: Bun + TypeScript + Electron + Next.js |

All models are local Ollama models. Do not switch the default to a cloud model without explicit approval — local-only inference is the project's core premise.

## Repository layout

```
main.py                         FastAPI app, lifespan, checkpointer, CORS, static /uploads
config.py                       Pydantic Settings loaded from .env
api/routes.py                   /api/stream (SSE), thread CRUD, history, image upload
agent/factory.py                Agent factory and tool registration
agent/models.py                 Shared Ollama model instances
agent/prompt.py                 System prompt
agent/middleware.py             Chat title generation middleware
agent/serialization.py          SSE-safe serialization and image encoding
database/session.py             SQLAlchemy engine, SessionLocal, Base, get_db
database/models.py              Thread table (thread_id, thread_name)
database/vector_store.py        Chroma client, per-document collections, embedding function
services/documents.py           PDF reading and text splitting
tools/files.py                  read_file, write_file, edit_file, list_files
tools/image.py                  read_image
tools/search.py                 internet_search
tools/python_task.py            execute_python_task subgraph (script generation + execution)
tools/rag.py                    rag_tool subgraph (index check, read, split, embed, retrieve)
scripts/math_server.py          FastMCP math server (stdio)
```

## Running the backend

Windows-first setup:

```powershell
flowsome-env\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Prerequisites:

- Ollama running locally with the models pulled:
  ```powershell
  ollama pull gemma4:e2b
  ollama pull qwen2.5-coder:3b
  ```
- PostgreSQL reachable at `DATABASE_URL`.
- Swagger UI: `http://127.0.0.1:8000/docs`.

Environment variables (`.env`, never commit real values):

```
DATABASE_URL
TAVILY_API_KEY
WORKSPACE_ROOT   # optional, defaults to the user's home directory
```

`DATABASE_URL` is used by both SQLAlchemy and the LangGraph Postgres checkpointer.

## Conventions for extending the agent

- **New tools**: define with `@tool` under `tools/`, then register in `build_agent` (`agent/factory.py`). Return JSON strings (`{"status": "success"|"error", ...}`) for file-style tools.
- **Fresh tool results**: the system prompt requires the agent to re-run tools for each new request (including hardware/system questions via `execute_python_task`) and never answer from earlier tool output. Preserve that rule when editing `agent/prompt.py`.
- **Progress events**: call `get_stream_writer()` (or `ToolRuntime.stream_writer`) and emit `{"message": ...}` or `{"status": ...}`. The UI renders these `custom` events as tool progress.
- **Multi-step tools**: implement as a compiled LangGraph subgraph and stream `updates` + `custom` (pattern: `tools/python_task.py`, `tools/rag.py`).
- **Middleware**: use `@before_model`, `@wrap_model_call`, or `AgentMiddleware` in `agent/middleware.py`. `generate_chat_title` and `SummarizationMiddleware` are active.
- **Models**: keep inference local. Prefer the shared instances/constants in `agent/models.py` instead of constructing new clients.
- **Persistence**: add new tables in `database/models.py` and import them before `Base.metadata.create_all` runs in `main.py`. Use the `get_db` dependency in routes.
- **API/SSE contract**: the Electron client depends on exact event names and payload shapes. Do not rename fields (`threadId`, `interruptResponse`, `decisions`, etc.) without updating the frontend.
- **Paths**: use `pathlib` and `WORKSPACE_ROOT`; avoid hardcoded absolute paths.
- **Style**: match existing code (type hints, docstrings, small helper functions). Do not add comments unless they explain non-obvious logic. Add any new dependency to `requirements.txt`.

## Known issues and gotchas

- `execute_python_task` runs model-generated code with `subprocess` (30s timeout, 5 attempts). The file tools restrict paths to `WORKSPACE_ROOT`, but generated Python code is not sandboxed. Treat it as a privileged capability.
- `internet_search` sends queries to Tavily (cloud). Avoid it for confidential government data.
- `/api/upload` stores images locally under `uploads/` and returns a local URL; Cloudinary uploads are handled by the client, which then passes the URL in `messages[1].content`.
- No authentication/authorization exists yet. Assume a trusted local environment.
- No pytest suite or CI. Verify changes by running the server and exercising `/docs` or `/api/stream`.
- The SSE stream uses `recursion_limit: 25`; deep tool chains will raise a recursion error.
- `clean_for_stream` drops non-JSON-serializable values (and `shell_session_resources`); keep tool return values JSON-safe.
- `internet_search` and `rag_tool` are plain functions passed to `create_agent`, while the file/image tools use `@tool`. Preserve their signatures when editing.

## Guidance for AI assistants

- Read the relevant files before editing; follow the patterns above rather than introducing new frameworks.
- Keep the privacy premise intact: no cloud LLM calls for user data, no logging of document contents, PII, credentials, or `.env` values.
- Prefer small, scoped changes. Do not rename public API fields or SSE event names.
- When adding government-domain features (letter templates, PDF generation, document classification, database updates), implement them as tools/subgraphs, emit progress via the stream writer, and document the tool in the system prompt in `agent/prompt.py`.
- There is no automated test command. Run `uvicorn main:app --reload`, check startup errors, and manually verify the affected endpoint/tool. If you add tests, use pytest and document the command here.
