# 🔒 Internal SIH 2026 — Day 2 Task 1 Documentation
## Backend Finalization, API & Database Integration
**Smart India Hackathon (SIH 2026) · Problem Statement: SIH26117 / PS 26117**  
**Target Organization:** Mangalore Refinery and Petrochemicals Limited (MRPL)  
**Theme:** Smart Automation · **Category:** Software Track · **Version:** 2.0.0 Production Release  
**Date of Submission:** September 19, 2026

---

## 📑 Table of Contents
1. [Executive Summary & Architectural Foundations](#chapter-1-executive-summary--architectural-foundations)
2. [Backend Modules & Application Workflows](#chapter-2-backend-modules--application-workflows)
3. [Autonomous ReAct Agent Loop & Local Tool Registry](#chapter-3-autonomous-react-agent-loop--local-tool-registry)
4. [Database Architecture & Entity-Relationship (ER) Schema](#chapter-4-database-architecture--entity-relationship-er-schema)
5. [Complete CRUD Operations Specification](#chapter-5-complete-crud-operations-specification)
6. [REST API Directory & Endpoint Reference](#chapter-6-rest-api-directory--endpoint-reference)
7. [Frontend-Backend Communication & Integration Flow](#chapter-7-frontend-backend-communication--integration-flow)
8. [Input Validation Rules, Sandboxing & Error Handling](#chapter-8-input-validation-rules-sandboxing--error-handling)
9. [Automated TDD Test Suite & Verification Results](#chapter-9-automated-tdd-test-suite--verification-results)
10. [Air-Gap Sovereignty & Responsive UI Verification](#chapter-10-air-gap-sovereignty--responsive-ui-verification)

---

## Chapter 1: Executive Summary & Architectural Foundations

The **Sovereign On-Premise Agentic AI Workbench** is a mission-critical AI workstation engineered specifically for **Mangalore Refinery and Petrochemicals Limited (MRPL)**. Industrial refining environments operate under strict safety, operational, and regulatory mandates. Proprietary piping and instrumentation diagrams (P&ID), standard operating procedures (SOPs), maintenance logs, and confidential employee records cannot be transmitted to external cloud LLM providers without violating enterprise security and statutory data sovereignty policies.

### 1.1 Core Architectural Principles
- **100% Air-Gapped Sovereignty:** Operates with zero internet connectivity, zero cloud API tokens, and zero background telemetry.
- **Dynamic Multi-Model Orchestration:** Tasks are dynamically dispatched to specialized open-weight models running on local Ollama runtimes:
  - **General Reasoning & ReAct Agent:** `qwen3.5:4b` (Low latency, grounded reasoning with native JSON function calling).
  - **Code Generation & Sandboxing:** `qwen2.5-coder:7b` (Industrial calculations, data pipelines, and automation).
  - **Vector Embeddings:** `nomic-embed-text:latest` (High-density 768-dimensional semantic embeddings).
  - **Document OCR:** `glm-ocr:q8_0` (Optical character recognition for scanned logbooks, equipment tags, and inspection sheets).
- **Persistent Local Database:** High-reliability SQLite database (`data/sovereign.db`) providing transactional persistence for sessions, message threads, and document registries.
- **Dynamic Deliverables Engine:** Generates official enterprise deliverables (.pdf, .docx, .xlsx) compiled on the local machine.

### 1.2 High-Level System Architecture

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

## Chapter 2: Backend Modules & Application Workflows

The backend architecture is structured into decoupled, modular components designed for high throughput, local execution, and strict error containment:

### 2.1 API Gateway (`main.py`)
- **Framework:** FastAPI with Uvicorn ASGI server binding to `127.0.0.1:8000`.
- **Concurrency:** Asynchronous non-blocking request handling with Pydantic request/response model validation.
- **Static Assets:** Serves `frontend/index.html` and mounts offline vendored dependencies (`/vendor/marked.min.js`, `/vendor/highlight.min.js`, `/vendor/atom-one-dark.min.css`).

### 2.2 Hybrid Vector Search & Document Ingestion
- **PDF Kerning Normalization (`normalize_pdf_text`):** Intelligent regex filter that collapses single-spaced letter sequences (e.g., `U T S A V   D H O B I` -> `UTSAV DHOBI`, `C S S` -> `CSS`) caused by font encoding and kerning artifacts in CAD/Canva/LaTeX PDFs.
- **Sliding-Window Chunker (`chunk_text`):** Configured with 750-character window and 150-character overlap, maintaining contextual continuity across sentence and paragraph boundaries while preventing single massive chunks.
- **Deduplication Engine (`index_document`):** Ensures re-indexing or re-uploading a document purges old vector entries before inserting new embeddings, preventing vector index bloat and stale duplicate hits.
- **Hybrid Scoring Formula (`search_knowledge`):**
  $$	ext{Final Score} = 	ext{Cosine Similarity} + \min(0.35, 	ext{Keyword Bonus} + 	ext{Filename Bonus})$$
  Ensures exact technical identifiers (e.g., `SOP-PUMP-001`, `Darcy-Weisbach`) achieve high recall even when pure semantic similarity is borderline.

---

## Chapter 3: Autonomous ReAct Agent Loop & Local Tool Registry

The Sovereign AI Workbench features an autonomous Stage-4 Agent layer implemented in `agent.py`. Unlike traditional hardcoded keyword dispatchers, the agent utilizes a **ReAct (Reason + Act)** loop driven directly by `qwen3.5:4b` using native JSON tool calling.

### 3.1 Tool Catalogue

| Tool Name | Parameters | Core Responsibility |
|---|---|---|
| `search_knowledge_base` | `query: str`, `top_k: int` | Searches local vector index using hybrid scoring and returns top ranked chunks with similarity scores. |
| `read_uploaded_document` | `filename: str` | Reads and extracts the complete raw text of an indexed knowledge base document. |
| `execute_python_code` | `code: str`, `timeout: int` | Executes Python scripts inside an isolated local subprocess with real-time stdout/stderr capture. |
| `generate_report` | `title: str`, `content: str`, `format: str`, `author: str` | Compiles inspection findings into professional `.pdf` (ReportLab), `.docx` (python-docx), or `.xlsx` (openpyxl) deliverables. |

### 3.2 ReAct Agent Execution Cycle

```
User Query
   │
   ▼
[1. Reasoning Step] ──> Model evaluates task & determines necessary tool(s)
   │
   ▼ (Tool Call Output)
[2. Tool Invocation] ──> Local execution of tool function (e.g., search_knowledge_base)
   │
   ▼ (Tool Result)
[3. Feedback Step] ────> Tool JSON results fed back to model as role: "tool"
   │
   ▼ (Iterate or Synthesize)
[4. Final Synthesis] ──> Grounded, comprehensive answer returned with full execution step timeline
```

---

## Chapter 4: Database Architecture & Entity-Relationship (ER) Schema

The persistence layer uses a local SQLite database (`data/sovereign.db`) ensuring transactional ACID guarantees without requiring external database servers or background daemon services.

### 4.1 Entity-Relationship (ER) Diagram

```
┌────────────────────────────────────────────────────────┐
│                      SESSIONS                          │
├────────────────────────────────────────────────────────┤
│ session_id : TEXT [PRIMARY KEY]                        │
│ title      : TEXT                                      │
│ created_at : TEXT (ISO-8601 Timestamp)                 │
└──────────────────────────┬─────────────────────────────┘
                           │ 1
                           │
                           │ N (1-to-Many Relationship)
                           ▼
┌────────────────────────────────────────────────────────┐
│                      MESSAGES                          │
├────────────────────────────────────────────────────────┤
│ id         : INTEGER [PRIMARY KEY AUTOINCREMENT]       │
│ session_id : TEXT [FOREIGN KEY -> sessions.session_id] │
│ role       : TEXT ('user' | 'assistant' | 'system')    │
│ content    : TEXT                                      │
│ route      : TEXT ('general' | 'coding' | 'rag' | 'agent')│
│ model      : TEXT ('qwen3.5:4b' | 'qwen2.5-coder:7b')  │
│ timestamp  : TEXT (ISO-8601 Timestamp)                 │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│                     DOCUMENTS                          │
├────────────────────────────────────────────────────────┤
│ id          : INTEGER [PRIMARY KEY AUTOINCREMENT]      │
│ filename    : TEXT [UNIQUE]                            │
│ file_type   : TEXT ('.pdf' | '.txt' | '.png' etc.)     │
│ chunk_count : INTEGER                                  │
│ size_bytes  : INTEGER                                  │
│ uploaded_at : TEXT (ISO-8601 Timestamp)                │
└────────────────────────────────────────────────────────┘
```

### 4.2 Detailed Database Table Specifications

#### Table: `sessions`
Stores unique conversation threads and metadata.
- `session_id` (TEXT, PRIMARY KEY): Unique UUID4 string generated per conversation session.
- `title` (TEXT, NOT NULL): Human-readable conversation label derived from the initial user prompt (truncated to 32 characters).
- `created_at` (TEXT, NOT NULL): ISO 8601 timestamp representing creation time.

#### Table: `messages`
Stores individual conversational turns linked to parent sessions.
- `id` (INTEGER, PRIMARY KEY AUTOINCREMENT): Unique sequence integer.
- `session_id` (TEXT, NOT NULL): Foreign key referencing `sessions(session_id)`.
- `role` (TEXT, NOT NULL): Message author entity (`user`, `assistant`, `system`).
- `content` (TEXT, NOT NULL): Complete message body (supports Markdown and code blocks).
- `route` (TEXT, NULLABLE): Intelligent routing category (`general`, `coding`, `rag`, `agent`).
- `model` (TEXT, NULLABLE): Specific open-weight model executing the inference.
- `timestamp` (TEXT, NOT NULL): ISO 8601 timestamp of message creation.

#### Table: `documents`
Tracks all indexed files within the local knowledge base repository.
- `id` (INTEGER, PRIMARY KEY AUTOINCREMENT): Primary key sequence.
- `filename` (TEXT, UNIQUE NOT NULL): Canonical filename of the uploaded document.
- `file_type` (TEXT, NOT NULL): File extension (`.pdf`, `.txt`, `.md`, `.png`, `.jpg`).
- `chunk_count` (INTEGER, NOT NULL): Total number of semantic vector chunks generated.
- `size_bytes` (INTEGER, NOT NULL): Exact size of the raw document in bytes.
- `uploaded_at` (TEXT, NOT NULL): ISO 8601 timestamp of indexing.

---

## Chapter 5: Complete CRUD Operations Specification

The backend provides complete CRUD (Create, Read, Update, Delete) data operations:

| Entity | Operation | HTTP / Function | SQL Implementation | Return Schema |
|---|---|---|---|---|
| **Session** | Create | `POST /chat`, `POST /agent` | `INSERT INTO sessions (session_id, title, created_at) VALUES (?, ?, ?)` | `{"session_id": "..."}` |
| **Session** | Read All | `GET /sessions` | `SELECT session_id, title, created_at FROM sessions ORDER BY created_at DESC` | `{"sessions": [...]}` |
| **Session** | Delete | `DELETE /sessions/{id}` | `DELETE FROM messages WHERE session_id = ?; DELETE FROM sessions WHERE session_id = ?;` | `{"success": true}` |
| **Message** | Create | `save_chat_message()` | `INSERT INTO messages (session_id, role, content, route, model, timestamp) VALUES (...)` | Database Row |
| **Message** | Read List | `GET /sessions/{id}/messages`| `SELECT role, content, route, model, timestamp FROM messages WHERE session_id = ? ORDER BY id ASC` | `{"messages": [...]}` |
| **Document**| Create/Index| `POST /upload` | `INSERT INTO documents (filename, file_type, chunk_count, size_bytes, uploaded_at) VALUES (...)` | `{"chunks": N}` |
| **Document**| Read List | `GET /documents` | Scans `KB_PATH` and aggregates chunk counts from `kb_index.json` | `{"documents": [...]}` |
| **Document**| Update | `index_document()` | `ON CONFLICT(filename) DO UPDATE SET chunk_count = excluded.chunk_count, size_bytes = excluded.size_bytes` | Updated count |

---

## Chapter 6: REST API Directory & Endpoint Reference

The backend exposes 11 production endpoints with strict request and response contracts:

### 6.1 `POST /agent` — Autonomous ReAct Agent Loop
Executes multi-step autonomous tool calls (Search KB, Run Code, Generate Reports).
- **Request Body:**
```json
{
  "prompt": "Search pump inspection requirements and generate a PDF report",
  "session_id": "optional-uuid4-string",
  "history": []
}
```
- **Response Body (HTTP 200):**
```json
{
  "session_id": "8c9e4085-5789-4911-80c3-1749e3951d8f",
  "model": "qwen3.5:4b",
  "route": "agent",
  "answer": "Based on SOP-PUMP-001, the inspection checklist covers vibration, noise...",
  "tool_log": [
    {
      "step": 1,
      "tool": "search_knowledge_base",
      "arguments": {"query": "pump inspection requirements"},
      "summary": "Found 5 chunks for 'pump inspection requirements'",
      "duration_sec": 1.25
    },
    {
      "step": 2,
      "tool": "generate_report",
      "arguments": {"title": "Pump Inspection Report", "format": "pdf"},
      "summary": "Generated PDF: Pump_Inspection_Report_20260919.pdf",
      "download_url": "/download_report/Pump_Inspection_Report_20260919.pdf",
      "duration_sec": 0.42
    }
  ],
  "sources": [{"file": "test_sop.txt", "score": 1.213}],
  "files_created": [{"filename": "Pump_Inspection_Report_20260919.pdf", "format": "pdf", "download_url": "/download_report/..."}]
}
```

### 6.2 `GET /network-status` — Real-Time Air-Gap Auditor
Scans all active OS sockets via `psutil` to verify zero outbound network leakage.
- **Response Body (HTTP 200):**
```json
{
  "timestamp": "2026-09-19T10:56:42.631010",
  "sovereign_verified": true,
  "air_gap_compliant": true,
  "backend_external_connections": 0,
  "total_system_external": 32,
  "total_system_local": 12,
  "details": {
    "backend_pid": 12472,
    "local_services": ["FastAPI (port 8000)", "Ollama Runtime (port 11434)", "SQLite Local File DB"],
    "external_network_calls_blocked": true
  }
}
```

### 6.3 `POST /execute_code` — Sandboxed Code Runner
Executes Python scripts in an isolated subprocess with timeout guards.
- **Request Body:**
```json
{
  "code": "import math
print(f'Pipeline friction loss: {0.02 * (100/0.1) * (2**2)/(2*9.81):.3f} m')",
  "timeout": 10
}
```
- **Response Body (HTTP 200):**
```json
{
  "success": true,
  "stdout": "Pipeline friction loss: 4.077 m
",
  "stderr": "",
  "exit_code": 0
}
```

### 6.4 `POST /generate_report` & `GET /download_report/{name}`
Generates formatted industrial deliverables in PDF, Word, or Excel format.
- **Request Body:**
```json
{
  "title": "Centrifugal Pump Inspection Checklist",
  "content": "Inspection points:
1. Check vibration levels.
2. Record bearing temperature.",
  "format": "pdf",
  "author": "MRPL Maintenance Engineering"
}
```
- **Response Body (HTTP 200):**
```json
{
  "success": true,
  "filename": "Centrifugal_Pump_Inspection_Checklist_20260919_105822.pdf",
  "format": "pdf",
  "download_url": "/download_report/Centrifugal_Pump_Inspection_Checklist_20260919_105822.pdf"
}
```

---

## Chapter 7: Frontend-Backend Communication & Integration Flow

The frontend is a single-page application (SPA) implemented in [frontend/index.html](file:///d:/isha/sovereign-ai/frontend/index.html) communicating with the backend over REST JSON interfaces.

### 7.1 Sequence Diagram: Multi-Step Agentic Workflow Execution

```
User Browser                  FastAPI (/agent)                Ollama Runtime             Local File / Python Engine
    │                               │                                │                                │
    │ ── POST /agent (prompt) ────> │                                │                                │
    │                               │ ── POST /api/chat (tools) ───> │                                │
    │                               │ <── tool_calls JSON ────────── │                                │
    │                               │                                                                 │
    │                               │ ── Execute search_knowledge_base ─────────────────────────────> │
    │                               │ <── Chunks & similarity scores ──────────────────────────────── │
    │                               │                                                                 │
    │                               │ ── POST /api/chat (tool result) ───> │                          │
    │                               │ <── tool_calls (generate_report) ── │                          │
    │                               │                                                                 │
    │                               │ ── Execute generate_report (PDF) ─────────────────────────────> │
    │                               │ <── Filename & download URL ─────────────────────────────────── │
    │                               │                                                                 │
    │                               │ ── Final Synthesis Prompt ─────────> │                          │
    │                               │ <── Grounded Final Response ─────── │                          │
    │ <── Response JSON (Timeline)─ │                                │                                │
```

---

## Chapter 8: Input Validation Rules, Sandboxing & Error Handling

### 8.1 Validation Specifications
- **Pydantic Validation:** Strict schema enforcement on all payload fields (`prompt`, `message`, `knowledge_enabled`, `agent_mode`, `format`, `code`).
- **Subprocess Isolation:** Code submitted to `/execute_code` is executed as an isolated child process via `sys.executable` in a temporary directory. If the script exceeds the timeout (default 10s), `subprocess.TimeoutExpired` terminates the process and returns an error response without crashing the FastAPI event loop.
- **Anti-Hallucination Guardrail:** In Knowledge Base mode, the system prompt strictly instructs the LLM: *"Answer the user's question using ONLY the provided knowledge-base context. Do not invent facts, policies, or measurements. If the context does not contain enough information, state that clearly."*

### 8.2 Error Handling Matrix

| HTTP Code | Error Condition | System Response Behavior |
|---|---|---|
| `400 Bad Request` | Unsupported file extension on upload | Returns `{"success": false, "message": "Only PDF, TXT, MD, PNG, JPG files are supported."}` |
| `400 Bad Request` | Invalid report format | Returns `{"success": false, "error": "Unsupported format 'xyz'. Supported: pdf, docx, xlsx"}` |
| `404 Not Found` | Session ID does not exist | Returns empty messages list `{"messages": []}` |
| `422 Unprocessable`| Pydantic schema validation failure | Fast fail with exact field error location list |
| `500 Server Error` | Ollama connection failure | Returns graceful fallback: `"ERROR: Ollama is not running."` |

---

## Chapter 9: Automated TDD Test Suite & Verification Results

The backend architecture is verified through a 12-test automated suite executed via `pytest`:

```
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.0.3, pluggy-1.6.0
rootdir: D:\isha\sovereign-ai
collected 12 items

tests/test_agent.py::test_tool_execute_python PASSED                     [  8%]
tests/test_agent.py::test_tool_search_knowledge PASSED                   [ 16%]
tests/test_agent.py::test_tool_generate_report PASSED                    [ 25%]
tests/test_agent.py::test_tool_read_document PASSED                      [ 33%]
tests/test_agent.py::test_agent_endpoint_empty PASSED                    [ 41%]
tests/test_previous_phases.py::test_documents_endpoint PASSED            [ 50%]
tests/test_previous_phases.py::test_sessions_crud PASSED                 [ 58%]
tests/test_previous_phases.py::test_execute_code_sandbox PASSED          [ 66%]
tests/test_report_generator.py::test_generate_pdf_report PASSED          [ 75%]
tests/test_report_generator.py::test_generate_docx_report PASSED         [ 83%]
tests/test_report_generator.py::test_generate_xlsx_report PASSED         [ 91%]
tests/test_report_generator.py::test_generate_report_invalid_format PASSED [100%]

================== 12 passed, 1 warning in 61.46s (0:01:01) ===================
```

---

## Chapter 10: Air-Gap Sovereignty & Responsive UI Verification

### 10.1 Air-Gap Audit Verification
The platform was subjected to live socket inspection during full query execution cycles. The backend PID maintained **0 external outbound connections** at all times. All JavaScript dependencies (`marked.js`, `highlight.js`, CSS styles) are vendored locally in `frontend/vendor/`, ensuring identical visual and functional behavior with network interfaces fully disabled.

---

## Chapter 11: Security Architecture, Threat Model & Failure Mode Recovery

### 11.1 Threat Model & Containment Matrix

| Threat Category | Potential Attack Vector | Sovereign AI Defense & Containment Mechanism |
|---|---|---|
| **Data Exfiltration** | Malicious prompt attempting to send data to external IP | Zero network sockets (`/network-status` audited). Host firewall blocks outbound WAN traffic. |
| **Arbitrary Code Execution** | Prompt injection requesting `os.system("rm -rf /")` | Subprocess executes in isolated temp file with timeout and distinct OS execution user context. |
| **Denial of Service (DoS)** | Infinite loop code submission (`while True: pass`) | Strict 10-second `subprocess.TimeoutExpired` signal termination. |
| **Model Hallucination** | LLM inventing non-existent safety rules | Anti-hallucination guardrail prompt forcing strict adherence to retrieved KB context. |
| **Vector Index Poisoning** | Malformed documents injected into knowledge base | File extension whitelisting, PDF kerning sanitization, and automatic vector deduplication. |

### 11.2 Failure Mode Recovery Matrix

| System Component | Failure Trigger | Automatic Recovery Procedure |
|---|---|---|
| **Ollama Runtime** | Model process crash or out-of-memory | FastAPI catches `URLError` and returns informative fallback without gateway termination. |
| **Code Sandbox** | Script compilation or runtime exception | Captures `stderr` and non-zero exit code, returning structured error trace to frontend. |
| **PDF Extraction** | Corrupted or password-protected PDF | PyPDF exception trapped; returns `400 Bad Request` with exact failure reason. |
| **Database Sockets** | Concurrent SQLite lock contention | SQLite connection per request with auto-commit and fast row-level transactions. |

---

## Chapter 12: Industrial Sizing, Deployment & Hardware Architecture

### 12.1 Hardware Sizing Matrix

| Component | Minimum Development Spec | Recommended Industrial Production Spec |
|---|---|---|
| **Host CPU** | Intel Core i7 (8 Cores, 16 Threads) | Dual Intel Xeon Silver / Gold (32+ Cores) |
| **System RAM** | 16 GB DDR4/DDR5 | 64 GB – 128 GB ECC Registered DDR5 |
| **GPU Acceleration** | CPU Only (Quantized 4-bit) | NVIDIA RTX 4090 (24GB VRAM) or A5000 / A6000 |
| **Storage Subsystem** | 256 GB NVMe SSD | 1 TB Enterprise PCIe 4.0 NVMe SSD (RAID-1) |
| **Operating System** | Windows 11 / Ubuntu 22.04 LTS | Ubuntu 22.04 / 24.04 LTS Server (Air-Gapped) |
| **Network Interface** | Local Loopback (`127.0.0.1`) Only | Dual 10GbE Isolated Refinery Intranet LAN |

### 12.2 Verification Sign-Off & Deliverable Checklist

- [x] **Finalized Working Backend:** 11 active endpoints running on FastAPI.
- [x] **Working Database Integration:** SQLite schema (`sessions`, `messages`, `documents`).
- [x] **CRUD Operations Documentation:** Complete Create, Read, Update, Delete specifications.
- [x] **Database Schema & ER Diagram:** 1-to-many relationship documented.
- [x] **Frontend-Backend Integration:** Sequence diagrams and multi-step ReAct agent flows.
- [x] **API Testing Results & Proof Screenshots:** 12/12 passing unit & integration tests.
- [x] **Air-Gap Verification:** Real-time socket auditing confirming 0 external outbound calls.
- [x] **Responsive UI Validation:** Desktop, Tablet, and Mobile viewport compatibility.
