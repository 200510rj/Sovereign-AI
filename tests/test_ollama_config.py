import pytest
from fastapi.testclient import TestClient
from main import app, get_ollama_url, set_ollama_url, DEFAULT_OLLAMA_URL

client = TestClient(app)

def test_get_ollama_config():
    response = client.get("/config/ollama")
    assert response.status_code == 200
    data = response.json()
    assert "current_url" in data
    assert "default_url" in data
    assert data["default_url"] == DEFAULT_OLLAMA_URL

def test_set_ollama_config():
    test_url = "https://universe-hosts-spot-wizard.trycloudflare.com"
    response = client.post("/config/ollama", json={"url": test_url})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "updated"
    assert data["current_url"] == test_url
    assert get_ollama_url() == test_url

    # Reset back to default
    set_ollama_url(DEFAULT_OLLAMA_URL)
    assert get_ollama_url() == DEFAULT_OLLAMA_URL

def test_test_ollama_connection_remote_tunnel():
    tunnel_url = "https://universe-hosts-spot-wizard.trycloudflare.com"
    response = client.post("/config/ollama/test", json={"url": tunnel_url})
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert data["url"] == tunnel_url
    if data["success"]:
        assert isinstance(data["models"], list)
        assert data["model_count"] > 0

def test_is_local_instance_token_uncap_logic():
    from main import is_local_instance
    assert is_local_instance("http://127.0.0.1:11434") is True
    assert is_local_instance("http://localhost:11434") is True
    assert is_local_instance("https://universe-hosts-spot-wizard.trycloudflare.com") is False
    assert is_local_instance("https://solution-bloomberg-leaf-tradition.trycloudflare.com") is False
    assert is_local_instance("https://custom-gpu-instance.internal") is False
