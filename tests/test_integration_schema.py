"""
Integration tests for unified /agent response schema, routing, and Laya/Needle integration.
(tests/test_integration_schema.py)
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_agent_response_has_required_keys():
    res = client.post("/agent", json={"prompt": "tell me a joke"})
    assert res.status_code == 200
    data = res.json()
    for key in ["answer", "tool_log", "sources", "files_created", "laya_meta", "path", "model", "route", "response_time_ms"]:
        assert key in data, f"Missing key '{key}' in response"


def test_path_values_are_valid():
    res = client.post("/agent", json={"prompt": "tell me a joke"})
    assert res.status_code == 200
    data = res.json()
    assert data["path"] in ["needle3", "ollama_react", "laya_rejected", "empty"]


def test_offtopic_query_uses_laya_gate():
    res = client.post("/agent", json={"prompt": "tell me a funny joke or riddle"})
    assert res.status_code == 200
    data = res.json()
    assert data["path"] == "laya_rejected"
    assert data["model"] == "laya-gateway"
    assert data["laya_meta"]["is_mrpl_relevant"] < 0.3


def test_laya_meta_always_present():
    res = client.post("/agent", json={"prompt": "find safety SOP for refinery unit 4"})
    assert res.status_code == 200
    data = res.json()
    assert data["laya_meta"] is not None
    assert "intent" in data["laya_meta"]
    assert "urgency" in data["laya_meta"]
    assert "language" in data["laya_meta"]


def test_classify_endpoint_direct():
    res = client.get("/classify?q=find safety SOP for refinery unit 4")
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "knowledge_search"
    assert "latency_ms" in data


def test_extract_endpoint_direct():
    res = client.post("/extract", json={"filename": "test_sop.txt", "doc_type": "sop"})
    assert res.status_code == 200
    data = res.json()
    assert data["extracted"] is True
    assert "fields" in data
    assert data["filename"] == "test_sop.txt"
