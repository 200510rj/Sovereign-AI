import pytest
from fastapi.testclient import TestClient
from main import app
import agent
import web_search_tool

client = TestClient(app)

def test_web_search_tool_direct_ddgs(monkeypatch):
    """Verify web_search_tool returns structured search results from DDGS."""
    def fake_ddgs_text(query, max_results=5):
        return [
            {"title": "Test Title 1", "body": "Test Snippet 1", "href": "https://example.com/1"},
            {"title": "Test Title 2", "body": "Test Snippet 2", "href": "https://example.com/2"}
        ]

    class FakeDDGS:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            return False
        def text(self, query, max_results=5):
            return fake_ddgs_text(query, max_results=max_results)

    monkeypatch.setattr(web_search_tool, "DDGS", FakeDDGS)

    results = web_search_tool.search_web("Python LangChain", max_results=2)
    assert isinstance(results, list)
    assert len(results) == 2
    assert results[0]["title"] == "Test Title 1"
    assert results[0]["href"] == "https://example.com/1"
    assert results[0]["snippet"] == "Test Snippet 1"

def test_langchain_web_search_tool_decorator():
    """Verify LangChain @tool decorator produces formatted string output."""
    res = web_search_tool.web_search_tool.invoke({"query": "Python"})
    assert isinstance(res, str)
    assert len(res) > 0

def test_web_search_endpoint():
    """Verify POST /search endpoint returns search results."""
    response = client.post('/search', json={'query': 'Python programming', 'top_k': 2})
    assert response.status_code == 200
    data = response.json()
    assert data['query'] == 'Python programming'
    assert isinstance(data['results'], list)

def test_agent_tool_web_search():
    """Verify agent execute_tool delegates to web_search tool correctly."""
    res = agent.execute_tool('web_search', {'query': 'Python programming', 'top_k': 2})
    assert res['tool'] == 'web_search'
    assert 'results' in res
