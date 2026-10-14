"""API endpoint tests: request validation, response shape, and error handling."""
import pytest


@pytest.mark.api
class TestQueryEndpoint:
    def test_query_creates_session_when_missing(self, client, mock_rag_system):
        resp = client.post("/api/query", json={"query": "What is MCP?"})

        assert resp.status_code == 200
        data = resp.json()
        assert data["answer"] == "MCP is the Model Context Protocol."
        assert data["session_id"] == "session_1"
        mock_rag_system.session_manager.create_session.assert_called_once()
        mock_rag_system.query.assert_called_once_with("What is MCP?", "session_1")

    def test_query_reuses_given_session(self, client, mock_rag_system):
        resp = client.post("/api/query", json={"query": "And lesson 2?", "session_id": "abc"})

        assert resp.status_code == 200
        assert resp.json()["session_id"] == "abc"
        mock_rag_system.session_manager.create_session.assert_not_called()
        mock_rag_system.query.assert_called_once_with("And lesson 2?", "abc")

    def test_query_returns_sources_with_optional_urls(self, client, sample_sources):
        resp = client.post("/api/query", json={"query": "What is MCP?"})

        assert resp.json()["sources"] == sample_sources

    def test_query_with_no_sources(self, client, mock_rag_system):
        mock_rag_system.query.return_value = ("Hello!", [])

        resp = client.post("/api/query", json={"query": "hi"})

        assert resp.status_code == 200
        assert resp.json()["sources"] == []

    def test_query_missing_query_field_is_422(self, client, mock_rag_system):
        resp = client.post("/api/query", json={"session_id": "abc"})

        assert resp.status_code == 422
        mock_rag_system.query.assert_not_called()

    def test_query_wrong_type_is_422(self, client):
        resp = client.post("/api/query", json={"query": ["not", "a", "string"]})

        assert resp.status_code == 422

    def test_query_backend_error_is_500_with_detail(self, client, mock_rag_system):
        mock_rag_system.query.side_effect = RuntimeError("Anthropic API unavailable")

        resp = client.post("/api/query", json={"query": "What is MCP?"})

        assert resp.status_code == 500
        assert resp.json()["detail"] == "Anthropic API unavailable"

    def test_query_get_method_not_allowed(self, client):
        assert client.get("/api/query").status_code == 405


@pytest.mark.api
class TestCoursesEndpoint:
    def test_courses_returns_stats(self, client, sample_analytics):
        resp = client.get("/api/courses")

        assert resp.status_code == 200
        assert resp.json() == sample_analytics

    def test_courses_empty_catalog(self, client, mock_rag_system):
        mock_rag_system.get_course_analytics.return_value = {"total_courses": 0, "course_titles": []}

        resp = client.get("/api/courses")

        assert resp.status_code == 200
        assert resp.json() == {"total_courses": 0, "course_titles": []}

    def test_courses_backend_error_is_500(self, client, mock_rag_system):
        mock_rag_system.get_course_analytics.side_effect = Exception("chroma down")

        resp = client.get("/api/courses")

        assert resp.status_code == 500
        assert resp.json()["detail"] == "chroma down"

    def test_courses_malformed_analytics_is_500(self, client, mock_rag_system):
        mock_rag_system.get_course_analytics.return_value = {"total_courses": 1}

        resp = client.get("/api/courses")

        assert resp.status_code == 500


@pytest.mark.api
class TestSessionEndpoint:
    def test_delete_session(self, client, mock_rag_system):
        resp = client.delete("/api/session/abc")

        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
        mock_rag_system.session_manager.delete_session.assert_called_once_with("abc")

    def test_delete_unknown_session_still_ok(self, client, mock_rag_system):
        mock_rag_system.session_manager.delete_session.return_value = False

        assert client.delete("/api/session/missing").status_code == 200


@pytest.mark.api
class TestRoot:
    def test_root_serves_html(self, client):
        resp = client.get("/")

        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/html")

    def test_unknown_route_is_404(self, client):
        assert client.get("/api/does-not-exist").status_code == 404
