import pytest
from fastapi.testclient import TestClient
import main
import agent

client = TestClient(main.app)

def test_tool_execute_python():
    """Verify execute_python_code tool works dynamically in sandbox."""
    res = agent.execute_tool("execute_python_code", {"code": "print('Sovereign Sandbox 42')"})
    assert res["success"] is True
    assert "Sovereign Sandbox 42" in res["stdout"]
    assert res["exit_code"] == 0

def test_tool_search_knowledge():
    """Verify search_knowledge_base tool searches real local index."""
    res = agent.execute_tool("search_knowledge_base", {"query": "centrifugal pump inspection"})
    assert res["success"] is True
    assert res["count"] > 0
    assert any("test_sop.txt" in str(r) for r in res["results"])

def test_tool_generate_report():
    """Verify generate_report tool produces a real downloadable PDF file."""
    res = agent.execute_tool("generate_report", {
        "title": "Agent Test Report",
        "content": "This is an automated test from Sovereign Agent.",
        "format": "pdf",
        "author": "Pytest"
    })
    assert res["success"] is True
    assert res["filename"].endswith(".pdf")
    assert "/download_report/" in res["download_url"]

def test_tool_read_document():
    """Verify read_uploaded_document tool reads actual text from KB file."""
    res = agent.execute_tool("read_uploaded_document", {"filename": "test_sop.txt"})
    assert res["success"] is True
    assert "SOP-PUMP-001" in res["text"]

def test_agent_endpoint_empty():
    """Verify /agent endpoint handles empty prompts gracefully."""
    response = client.post("/agent", json={"prompt": ""})
    assert response.status_code == 200
    data = response.json()
    assert data["route"] == "agent"
    assert "Please enter a request" in data["answer"]
