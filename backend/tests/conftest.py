"""Shared fixtures for the backend test suite.

`app.py` can't be imported in tests: at import time it builds a real RAGSystem
(ChromaDB + embedding model) and mounts `../frontend`, which only resolves when
the server is started from `backend/`. Instead, `create_test_app` rebuilds the
same API routes against an injected (mocked) RAG system, and serves a stub page
at `/` in place of the static frontend.
"""
from typing import List, Optional
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.testclient import TestClient
from pydantic import BaseModel

# --- Pydantic models (mirror backend/app.py) --------------------------------

class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None


class Source(BaseModel):
    label: str
    url: Optional[str] = None


class QueryResponse(BaseModel):
    answer: str
    sources: List[Source]
    session_id: str


class CourseStats(BaseModel):
    total_courses: int
    course_titles: List[str]


# --- Test app factory --------------------------------------------------------

def create_test_app(rag_system) -> FastAPI:
    """Build an app with the same API routes as backend/app.py, minus static files."""
    app = FastAPI(title="Course Materials RAG System (test)")

    @app.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest):
        try:
            session_id = request.session_id
            if not session_id:
                session_id = rag_system.session_manager.create_session()
            answer, sources = rag_system.query(request.query, session_id)
            return QueryResponse(answer=answer, sources=sources, session_id=session_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/courses", response_model=CourseStats)
    async def get_course_stats():
        try:
            analytics = rag_system.get_course_analytics()
            return CourseStats(
                total_courses=analytics["total_courses"],
                course_titles=analytics["course_titles"],
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.delete("/api/session/{session_id}")
    async def delete_session(session_id: str):
        rag_system.session_manager.delete_session(session_id)
        return {"status": "ok"}

    # Stand-in for the StaticFiles mount of ../frontend
    @app.get("/", response_class=HTMLResponse)
    async def index():
        return "<!doctype html><html><body><h1>Course Materials Assistant</h1></body></html>"

    return app


# --- Test data ---------------------------------------------------------------

@pytest.fixture
def sample_sources():
    return [
        {"label": "Intro to MCP - Lesson 1", "url": "https://example.com/mcp/lesson1"},
        {"label": "Intro to MCP", "url": None},
    ]


@pytest.fixture
def sample_analytics():
    return {
        "total_courses": 2,
        "course_titles": ["Intro to MCP", "Building Towards Computer Use"],
    }


# --- Mocks and clients -------------------------------------------------------

@pytest.fixture
def mock_rag_system(sample_sources, sample_analytics):
    """A RAGSystem stand-in with happy-path defaults; override per test as needed."""
    rag = MagicMock()
    rag.session_manager.create_session.return_value = "session_1"
    rag.session_manager.delete_session.return_value = True
    rag.query.return_value = ("MCP is the Model Context Protocol.", sample_sources)
    rag.get_course_analytics.return_value = sample_analytics
    return rag


@pytest.fixture
def test_app(mock_rag_system):
    return create_test_app(mock_rag_system)


@pytest.fixture
def client(test_app):
    with TestClient(test_app) as c:
        yield c
