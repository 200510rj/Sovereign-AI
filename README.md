# 🔒 Sovereign AI Workbench
### On-Premise Agentic AI Workbench for Confidential Industrial Work
**Smart India Hackathon (SIH 2026) · Problem Statement: SIH26117 / PS 26117**  
**Organization:** Mangalore Refinery and Petrochemicals Limited (MRPL)  
**Category:** Software · **Theme:** Smart Automation

---

## 📌 Executive Summary

Industrial refining, petrochemical, and critical infrastructure facilities deal with highly sensitive data—process piping schematics, proprietary Standard Operating Procedures (SOPs), safety logs, and inspection reports. Transmitting this data to public cloud LLMs violates strict enterprise data sovereignty and security policies.

**Sovereign AI** is an air-gapped, on-premise, agentic AI workbench running entirely on local enterprise hardware. It delivers end-to-end multimodal document ingestion, optical character recognition (OCR), semantic Retrieval-Augmented Generation (RAG), sandboxed code execution, and formal document reporting with **zero external network calls**.

---

## 🌟 Key Capabilities

- 🛡️ **100% Air-Gapped Sovereignty**: Operates without internet access, third-party API keys, or cloud telemetry.
- 🧠 **Dynamic Multi-Model Routing**: Automatically routes tasks to specialized open-weight models:
  - **General Reasoning & RAG**: `qwen3.5:4b` (Fast, grounded local reasoning)
  - **Code Generation & Debugging**: `qwen2.5-coder:7b` (Industrial scripts & automation)
  - **Vector Embeddings**: `nomic-embed-text:latest` (High-density semantic embeddings)
  - **Document OCR**: `glm-ocr:q8_0` (Scanned inspection sheets & diagrams)
- 📚 **Knowledge Base & Cosine Similarity RAG**: Fast pure-Python vector search over indexed PDFs, text SOPs, and OCR-extracted text with relevance thresholding.
- 🔍 **Interactive Chunk Modal**: Clickable knowledge sources in chat with direct raw chunk inspection.
- 💻 **In-Browser Code Execution Sandbox**: Executes generated Python scripts in an isolated subprocess with stdout/stderr capture and timeout protection.
- 📄 **Automatic Document Deliverables**: Instant one-click generation and download of formatted `.pdf` (ReportLab), `.docx` (python-docx), and `.xlsx` (openpyxl) inspection reports.
- 🗄️ **Persistent Session Memory**: Built-in SQLite database (`data/sovereign.db`) for full conversation history and instant session switching.

---

## 🏗️ System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Sovereign AI Web Client                         │
│   (Dark Glassmorphic UI · Multi-Turn Chat · Chunk Inspector · Console)  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / JSON
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      FastAPI Application Gateway                       │
│    (/chat · /upload · /execute_code · /generate_report · /sessions)    │
└───────────┬───────────────────────┬───────────────────────┬────────────┘
            │                       │                       │
            ▼                       ▼                       ▼
┌───────────────────────┐ ┌───────────────────┐ ┌────────────────────────┐
│    Local Ollama LLM   │ │ Vector Engine & DB│ │ Code & Document Engine │
│ ├─ qwen3.5:4b         │ │ ├─ kb_index.json  │ │ ├─ Python Sandbox      │
│ ├─ qwen2.5-coder:7b   │ │ ├─ sovereign.db   │ │ ├─ ReportLab (PDF)     │
│ ├─ nomic-embed-text   │ │ └─ knowledge_base │ │ ├─ python-docx (DOCX)  │
│ └─ glm-ocr:q8_0       │ │                   │ │ └─ openpyxl (XLSX)     │
└───────────────────────┘ └───────────────────┘ └────────────────────────┘
```

---

## 🛠️ Technology Stack

| Layer | Technologies & Models |
|---|---|
| **Frontend UI** | HTML5, CSS3 Glassmorphism, Vanilla JS, Marked.js, Highlight.js |
| **Backend Framework** | FastAPI, Uvicorn, Pydantic, Python 3.10+ |
| **Local LLM Engine** | Ollama (`qwen3.5:4b`, `qwen2.5-coder:7b`) |
| **OCR & Vision** | GLM-OCR (`glm-ocr:q8_0`), PyPDF |
| **Vector Search** | Nomic Embeddings (`nomic-embed-text`), NumPy / Pure-Python Cosine Similarity |
| **Database** | SQLite3 (`data/sovereign.db`) |
| **Report Generation** | ReportLab (`.pdf`), python-docx (`.docx`), openpyxl (`.xlsx`) |
| **Testing** | Pytest, FastAPI TestClient (TDD Architecture) |

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Python 3.10+**
- **Ollama** installed and running locally

### 2. Pull Required Open-Weight Models
```powershell
ollama pull qwen3.5:4b
ollama pull qwen2.5-coder:7b
ollama pull nomic-embed-text
ollama pull glm-ocr:q8_0
```

### 3. Clone Repository & Setup Environment
```powershell
git clone https://github.com/200510rj/Sovereign-AI.git
cd Sovereign-AI

python -m venv .venv
.venv\Scripts\Activate.ps1
pip install fastapi uvicorn pydantic pypdf ollama reportlab python-docx openpyxl pytest httpx
```

### 4. Launch Sovereign AI Backend
```powershell
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Open your browser and navigate to: **`http://127.0.0.1:8000`**

---

## 🧪 Test-Driven Development (TDD) Suite

Run the full automated test suite covering all modules:
```powershell
pytest tests/
```

### Test Suite Structure:
- `tests/test_previous_phases.py`: Validates `/documents`, SQLite session lifecycle (`/sessions`), and sandboxed code execution (`/execute_code`).
- `tests/test_report_generator.py`: Validates `.pdf`, `.docx`, and `.xlsx` document generation and file download endpoints.

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the Sovereign AI Workbench web application |
| `GET` | `/documents` | Lists all indexed knowledge base files and chunk metrics |
| `POST` | `/upload` | Uploads and processes `.pdf`, `.txt`, `.md`, or image files with OCR |
| `POST` | `/chat` | Multi-turn conversational chat with automatic tool/model routing |
| `GET` | `/sessions` | Lists all stored chat conversation sessions |
| `GET` | `/sessions/{id}/messages` | Fetches historical messages for a given session |
| `DELETE` | `/sessions/{id}` | Deletes a conversation session |
| `POST` | `/execute_code` | Runs Python code inside the local sandbox environment |
| `POST` | `/generate_report` | Compiles inspection findings into `.pdf`, `.docx`, or `.xlsx` |
| `GET` | `/download_report/{name}`| Downloads generated report deliverables |

---

## 👥 Team & Attribution
- **Developed for:** Smart India Hackathon (SIH 2026)
- **Problem Statement ID:** PS 26117
- **Target Organization:** Mangalore Refinery and Petrochemicals Limited (MRPL)
- **License:** MIT License
