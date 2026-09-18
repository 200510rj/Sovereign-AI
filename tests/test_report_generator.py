import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from main import app

client = TestClient(app)

def test_generate_pdf_report():
    payload = {
        "title": "Refinery Inspection Summary",
        "content": "All pressure safety valves and pump seals passed standard baseline checks.",
        "format": "pdf",
        "author": "MRPL Safety Team"
    }
    response = client.post("/generate_report", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "filename" in data
    assert data["filename"].endswith(".pdf")
    assert "download_url" in data
    
    # Verify download endpoint
    dl_response = client.get(data["download_url"])
    assert dl_response.status_code == 200
    assert len(dl_response.content) > 0

def test_generate_docx_report():
    payload = {
        "title": "Monthly Pump Maintenance Log",
        "content": "SOP-PUMP-001 executed on Centrifugal Pump CP-101. Vibration levels normal.",
        "format": "docx",
        "author": "Maintenance Unit"
    }
    response = client.post("/generate_report", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["filename"].endswith(".docx")
    
    # Verify download
    dl_response = client.get(data["download_url"])
    assert dl_response.status_code == 200
    assert len(dl_response.content) > 0

def test_generate_xlsx_report():
    payload = {
        "title": "Inspection Metrics Table",
        "content": "Metric, Baseline, Measured, Status\nPressure (bar), 12.5, 12.4, PASS\nTemperature (C), 65.0, 64.8, PASS\nVibration (mm/s), 2.0, 1.8, PASS",
        "format": "xlsx",
        "author": "Process Engineer"
    }
    response = client.post("/generate_report", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["filename"].endswith(".xlsx")
    
    # Verify download
    dl_response = client.get(data["download_url"])
    assert dl_response.status_code == 200
    assert len(dl_response.content) > 0

def test_generate_report_invalid_format():
    payload = {
        "title": "Bad Request Report",
        "content": "Test content",
        "format": "invalid_format"
    }
    response = client.post("/generate_report", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "Unsupported format" in data["error"]
