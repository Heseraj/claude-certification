# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Dependencies are managed with `uv` (Python 3.13+). Requires `ANTHROPIC_API_KEY` in a root `.env` (see `.env.example`).

**Always use `uv` for everything — never `pip`, `pip install`, or `python -m pip`**:
- Run the server and any Python with `uv run`.
- Add/remove dependencies with `uv add <pkg>` / `uv remove <pkg>` (dev-only: `uv add --dev <pkg>`); don't hand-edit the dependency list in `pyproject.toml`.
- Install/refresh the environment with `uv sync`; `uv.lock` is committed and updated by these commands.

```bash
uv sync                                              # install dependencies
./run.sh                                             # start server (Git Bash on Windows)
cd backend && uv run uvicorn app:app --reload --port 8000   # manual start
```

- The server **must be started from `backend/`**: `app.py` uses relative paths `../docs`, `../frontend`, and `./chroma_db`.
- UI at http://localhost:8000, Swagger at http://localhost:8000/docs.
- There are no tests, linter, or build step configured. `main.py` at the root is an unused placeholder.

## Architecture

A FastAPI backend (`backend/`) serving a static vanilla-JS chat UI (`frontend/`, mounted at `/`) that answers questions about course transcripts in `docs/` using Claude with tool-based retrieval over ChromaDB.

**Query path** (`POST /api/query`): `app.py` → `RAGSystem.query` (`rag_system.py`, the orchestrator that wires all components) → `AIGenerator.generate_response` → Claude decides via `tool_choice: auto` whether to call `search_course_content` → `ToolManager` → `CourseSearchTool` → `VectorStore.search`.

- **Single search round**: if Claude returns `tool_use`, `_handle_tool_execution` runs the tools and makes one follow-up call *without tools*. Multi-step tool use requires changing `ai_generator.py`. The system prompt also enforces "one search per query".
- **Sources travel out-of-band**: `CourseSearchTool` stores UI source labels in `self.last_sources`; `RAGSystem.query` reads them via `ToolManager.get_last_sources()` then resets them. This is shared state on a singleton tool instance.
- **Conversation history** (`session_manager.py`) is in-memory only, capped at `MAX_HISTORY` exchanges, and injected as plain text into the *system prompt*, not the `messages` array.
- New tools: subclass `Tool` in `search_tools.py` (implement `get_tool_definition` returning an Anthropic tool schema, and `execute`), then register it in `RAGSystem.__init__`.

**Vector store** (`vector_store.py`) uses two ChromaDB collections with `all-MiniLM-L6-v2` embeddings:
- `course_catalog`: one doc per course (the title, also used as ID); lessons stored as a JSON string in `lessons_json` metadata. Used to fuzzy-resolve a partial `course_name` to an exact title via top-1 semantic match.
- `course_content`: text chunks with `course_title` / `lesson_number` / `chunk_index` metadata, filtered with a Chroma `where` clause built in `_build_filter`.

**Ingestion** runs on server startup (`app.py` startup event → `RAGSystem.add_course_folder("../docs")`). Courses whose title already exists in Chroma are skipped, so **edited documents are not re-indexed** — delete `backend/chroma_db/` (or pass `clear_existing=True`) to rebuild.

`document_processor.py` expects this file format:
```
Course Title: <title>
Course Link: <url>
Course Instructor: <name>

Lesson <N>: <lesson title>
Lesson Link: <url>        (optional, must be the line right after the marker)
<content...>
```
Lesson text is split into sentences and packed into ~`CHUNK_SIZE` (800) char chunks with `CHUNK_OVERLAP` (100) chars of whole-sentence overlap. `.pdf`/`.docx` pass the extension filter but are read as plain UTF-8 text (no real parsing).

All tunables (model ID, chunk sizes, `MAX_RESULTS`, `MAX_HISTORY`, Chroma path) live in the `Config` dataclass in `backend/config.py`.
