"""
Performance benchmark tests for Laya Gateway and Needle 3 Dispatcher.
(tests/test_performance.py)
"""

import pytest
import time
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def warmup_module():
    # Warm up client, imports, and database connections
    client.get("/classify?q=warmup")
    client.post("/agent", json={"prompt": "warmup"})


def test_classify_endpoint_under_100ms():
    start = time.perf_counter()
    res = client.get("/classify?q=what is the emergency shutoff procedure for pump 1")
    duration_ms = (time.perf_counter() - start) * 1000
    assert res.status_code == 200
    # Also verify internal latency_ms reported by Laya
    assert res.json()["latency_ms"] < 50.0
    assert duration_ms < 500.0, f"Classify took {duration_ms}ms"


def test_laya_gate_under_500ms():
    start = time.perf_counter()
    res = client.post("/agent", json={"prompt": "tell me a funny joke about cats"})
    duration_ms = (time.perf_counter() - start) * 1000
    assert res.status_code == 200
    data = res.json()
    assert data["path"] == "laya_rejected"
    assert duration_ms < 500.0, f"Laya gate rejection took {duration_ms}ms"


def test_extract_endpoint_under_30s():
    start = time.perf_counter()
    res = client.post("/extract", json={"filename": "test_sop.txt", "doc_type": "sop"})
    duration_ms = (time.perf_counter() - start) * 1000
    assert res.status_code == 200
    assert duration_ms < 30000.0, f"Extract took {duration_ms}ms (expected < 30000ms)"
