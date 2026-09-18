import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_documents_endpoint():
    response = client.get("/documents")
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert isinstance(data["documents"], list)

def test_sessions_crud():
    # 1. List sessions initially
    res1 = client.get("/sessions")
    assert res1.status_code == 200
    assert "sessions" in res1.json()

    # 2. Send a chat prompt to create a session
    res2 = client.post("/chat", json={"prompt": "Hello test session"})
    assert res2.status_code == 200
    chat_data = res2.json()
    assert "session_id" in chat_data
    session_id = chat_data["session_id"]

    # 3. Retrieve messages for this session
    res3 = client.get(f"/sessions/{session_id}/messages")
    assert res3.status_code == 200
    msg_data = res3.json()
    assert msg_data["session_id"] == session_id
    assert len(msg_data["messages"]) >= 2

    # 4. Delete session
    res4 = client.delete(f"/sessions/{session_id}")
    assert res4.status_code == 200
    assert res4.json()["success"] is True

def test_execute_code_sandbox():
    # Test valid python execution
    valid_res = client.post("/execute_code", json={"code": "print('TDD Hello World')"})
    assert valid_res.status_code == 200
    valid_data = valid_res.json()
    assert valid_data["success"] is True
    assert "TDD Hello World" in valid_data["stdout"]

    # Test syntax error code execution
    error_res = client.post("/execute_code", json={"code": "print('Missing quote)"})
    assert error_res.status_code == 200
    error_data = error_res.json()
    assert error_data["success"] is False
    assert len(error_data["stderr"]) > 0
