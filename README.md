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

- 🛡️ **100% Air-Gapped Sovereignty**: Operates without internet access, third-party API keys, or cloud telemetry with real-time socket connection auditing (`GET /network-status`).
- 🤖 **Autonomous Stage-4 Agentic Workflow**: Native ReAct tool-calling loop powered by local `qwen3.5:4b`. Autonomously chains tools: search knowledge base -> read document -> run Python code -> compile PDF deliverables.
- 🧠 **Dynamic Multi-Model Routing**: Automatically routes tasks to specialized open-weight models:
  - **General Reasoning & ReAct Agent**: `qwen3.5:4b` (Fast, grounded local reasoning with native function calling)
  - **Code Generation & Debugging**: `qwen2.5-coder:7b` (Industrial scripts & automation)
  - **Vector Embeddings**: `nomic-embed-text:latest` (High-density semantic embeddings)
  - **Document OCR**: `glm-ocr:q8_0` (Scanned inspection sheets & diagrams)
- 📚 **Knowledge Base & Hybrid RAG**: High-accuracy semantic cosine similarity + keyword matching bonus over indexed PDFs, text SOPs, and OCR-extracted images with kerning normalization.
- 🔍 **Interactive Chunk Modal**: Clickable knowledge sources in chat with direct raw chunk inspection and confidence scores.
- 💻 **In-Browser Code Execution Sandbox**: Executes generated Python scripts in an isolated subprocess with stdout/stderr capture and timeout protection.
- 📄 **Automatic Document Deliverables**: Instant one-click generation and download of formatted `.pdf` (ReportLab), `.docx` (python-docx), and `.xlsx` (openpyxl) inspection reports.
- 🗄️ **Persistent Session Memory**: Built-in SQLite database (`data/sovereign.db`) for full conversation history and instant session switching.

---

## 🏗️ System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Sovereign AI Web Client                         │
│ (Dark Glassmorphic UI · Agent Timeline · Chunk Inspector · Air-Gap Pill)│
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / JSON (100% Localhost)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      FastAPI Application Gateway                       │
│ (/chat · /agent · /upload · /network-status · /execute_code · /reports) │
└───────────┬───────────────────────┬───────────────────────┬────────────┘
            │                       │                       │
            ▼                       ▼                       ▼
┌───────────────────────┐ ┌───────────────────┐ ┌────────────────────────┐
│    Local Ollama LLM   │ │ Vector Engine & DB│ │ Code & Document Engine │
│ ├─ qwen3.5:4b (Agent) │ │ ├─ kb_index.json  │ │ ├─ Python Sandbox      │
│ ├─ qwen2.5-coder:7b   │ │ ├─ sovereign.db   │ │ ├─ ReportLab (PDF)     │
│ ├─ nomic-embed-text   │ │ └─ knowledge_base │ │ ├─ python-docx (DOCX)  │
│ └─ glm-ocr:q8_0       │ │                   │ │ └─ openpyxl (XLSX)     │
└───────────────────────┘ └───────────────────┘ └────────────────────────┘
```

---

## 🛠️ Technology Stack

| Layer | Technologies & Models |
|---|---|
| **Frontend UI** | HTML5, CSS3 Glassmorphism, Vanilla JS, Vendored Local Marked.js & Highlight.js |
| **Backend Framework** | FastAPI, Uvicorn, Pydantic, Python 3.10+ |
| **Local LLM Engine** | Ollama (`qwen3.5:4b`, `qwen2.5-coder:7b`) with native Function Calling |
| **OCR & Vision** | GLM-OCR (`glm-ocr:q8_0`), PyPDF with custom kerning normalization |
| **Vector Search** | Nomic Embeddings (`nomic-embed-text`), Hybrid Cosine & Lexical Keyword Search |
| **Agent Layer** | Autonomous ReAct Execution Loop (`agent.py`) |
| **Security & Audit** | Local Network Auditor (`psutil`), Subprocess Isolation Sandbox |
| **Database** | SQLite3 (`data/sovereign.db`) |
| **Report Generation** | ReportLab (`.pdf`), python-docx (`.docx`), openpyxl (`.xlsx`) |
| **Testing** | Pytest, FastAPI TestClient (19/19 Passing Tests · 100% Pass Rate) |

---

## 🚀 Quick Start Guide (Step-by-Step for New Users & Evaluators)

Follow these simple steps to set up and run the Sovereign AI Workbench on any machine:

---

### Step 1: Prerequisites
- **Python 3.10+** installed ([python.org](https://www.python.org/downloads/))
- **Git** installed ([git-scm.com](https://git-scm.com/))
- **Ollama** installed ([ollama.com](https://ollama.com/)) *(Only required for 100% local air-gapped inference; optional if using a remote tunnel endpoint)*

---

### Step 2: Clone the Repository
```bash
git clone https://github.com/200510rj/Sovereign-AI.git
cd Sovereign-AI
```

---

### Step 3: Create & Activate Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**On Linux / macOS (Terminal):**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

### Step 4: Install Dependencies
Install all required packages from `requirements.txt`:
```bash
pip install -r requirements.txt
```

---

### Step 5: Choose Inference Mode

#### Option A: 100% Local / Air-Gapped Mode (Default)
Pull the required open-weight models locally:
```bash
ollama pull qwen3.5:4b
ollama pull qwen2.5-coder:7b
ollama pull nomic-embed-text
ollama pull glm-ocr:q8_0
```

#### Option B: Remote / Cloudflare Tunnel Mode (No local GPU/models needed)
- If running on a low-spec machine without local Ollama, simply start the backend (Step 6) and select or paste your remote Ollama / Cloudflare tunnel URL in the **Target Inference Instance** panel in the UI sidebar.

---

### Step 6: Launch Sovereign AI Backend
```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

---

### Step 7: Open the Application
- Open your browser and go to: **`http://127.0.0.1:8000`**
- Interactive Swagger API Documentation: **`http://127.0.0.1:8000/docs`**

---

### Step 8: Run Automated Verification Tests
Run the comprehensive 19-test suite to verify all tools, agents, report generators, and endpoints:
```bash
python -m pytest tests/ -v
```

---

## 🌐 Inference Modes & Target Endpoint Configuration

The Sovereign AI Workbench supports dual operating modes:

1. **100% Local / Air-Gapped Mode (Default):**
   - Targets `http://127.0.0.1:11434` with strictly local Ollama execution and 0 outbound internet calls.
   - Built-in live network auditor (`GET /network-status`) continuously monitors active sockets.
2. **Remote / Cloudflare Tunnel Mode:**
   - Use the **Target Inference Instance** panel in the left sidebar to enter any remote Ollama or Cloudflare tunnel URL (e.g. `https://your-tunnel.trycloudflare.com`).
   - Click **⚡ Test & Apply** to verify connection and model inventory.
   - Output token limits (`num_predict`) are automatically uncapped for high-throughput remote GPU inference.

---

## 🧪 Test-Driven Development (TDD) Suite

Run the full automated test suite covering all modules:
```powershell
python -m pytest tests/ -v
```

### Test Suite Structure (19 Tests · 100% Pass Rate):
- `tests/test_agent.py`: Validates individual tool execution (`search_knowledge_base`, `execute_python_code`, `generate_report`, `read_uploaded_document`) and `/agent` endpoint.
- `tests/test_ollama_config.py`: Validates runtime Ollama endpoint configuration, Cloudflare tunnel connectivity, and dynamic token uncap logic.
- `tests/test_previous_phases.py`: Validates `/documents`, SQLite session lifecycle (`/sessions`), and sandboxed code execution (`/execute_code`).
- `tests/test_report_generator.py`: Validates `.pdf`, `.docx`, and `.xlsx` document generation and file download endpoints.
- `tests/test_web_search.py`: Validates multi-source web search synthesis (`/search`), fallback mechanisms, and agent tool execution.

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the Sovereign AI Workbench web application |
| `GET` | `/documents` | Lists all indexed knowledge base files and chunk metrics |
| `POST` | `/upload` | Uploads and processes `.pdf`, `.txt`, `.md`, or image files with OCR |
| `POST` | `/chat` | Multi-turn conversational chat with automatic tool/model routing |
| `POST` | `/agent` | Autonomous ReAct agent loop executing multi-step tool calls |
| `POST` | `/search` | Real-time multi-source web search query synthesis |
| `GET` | `/config/ollama` | Gets the active Ollama inference endpoint URL |
| `POST` | `/config/ollama` | Sets the active Ollama inference endpoint URL |
| `POST` | `/config/ollama/test` | Tests connectivity and model inventory of any Ollama endpoint |
| `GET` | `/network-status` | Real-time air-gap connection auditor verifying 0 external network calls |
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

