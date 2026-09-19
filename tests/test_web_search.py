import pytest
from fastapi.testclient import TestClient
from main import app
import agent

client = TestClient(app)

def test_web_search_helper():
    results = agent.perform_web_search('Mangalore Refinery', top_k=2)
    assert isinstance(results, list)
    assert len(results) > 0
    assert 'title' in results[0]
    assert 'snippet' in results[0]

def test_web_search_endpoint():
    response = client.post('/search', json={'query': 'Mangalore Refinery', 'top_k': 2})
    assert response.status_code == 200
    data = response.json()
    assert data['query'] == 'Mangalore Refinery'
    assert isinstance(data['results'], list)
    assert len(data['results']) > 0

def test_agent_tool_web_search():
    res = agent.execute_tool('web_search', {'query': 'Mangalore Refinery', 'top_k': 2})
    assert res['success'] is True
    assert res['tool'] == 'web_search'
    assert len(res['results']) > 0
