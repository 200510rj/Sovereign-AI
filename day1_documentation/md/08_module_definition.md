# Task 1 — Document 08: Module Definition Specification

> **Problem Statement ID:** PS 26117 / SIH26117  
> **Title:** Sovereign On-Premise Agentic AI Workbench using Open-Weight Multimodal LLMs for Confidential Industrial Work  
> **Organization:** Mangalore Refinery and Petrochemicals Limited (MRPL)  
> **Category:** Software | **Theme:** Smart Automation  

---

## 🧩 Software Module Architecture

The **Sovereign AI Workbench** codebase is structured into six decoupled, highly cohesive software modules. Each module maintains clean API boundaries to allow independent maintenance and future extensibility.

```
sovereign-ai/
├── frontend/
│   └── index.html               # [Module 1] Web Interface Module
├── main.py                      # [Module 2 & 6] FastAPI Backend Gateway & Guardrails
├── kb_index.py                  # [Module 3 & 4] Document/OCR Ingestion & Vector Indexer
├── kb_search.py                 # [Module 4] Cosine Vector Search Engine
├── rag_test.py                  # [Module 5 & 6] End-to-End RAG Verification Module
└── data/                        # [Module 4] Storage Module
    ├── knowledge_base/          # Source Files & Images
    └── kb_index.json            # Vector Index Storage
```

---

## 📦 Module Specifications

### Module 1: Web Interface Module (`frontend/index.html`)
- **Responsibility**: Provides the responsive, dark-themed Single Page Application (SPA) user interface.
- **Key Components**:
  - `Chat Window`: Renders user messages and formatted markdown AI responses.
  - `Document Uploader`: Form payload handler for drag-and-drop file uploads.
  - `Knowledge Toggle`: Interactive UI switch modifying payload state (`knowledge_enabled: true/false`).
  - `Source Badges`: Renders document pill badges showing source file names and cosine similarity scores.
- **Input**: User clicks, file selections, keyboard inputs.
- **Output**: REST HTTP calls to FastAPI backend; DOM updates.

---

### Module 2: FastAPI Gateway & Task Router Module (`main.py`)
- **Responsibility**: Serves as the central API gateway, managing request endpoints and dynamic prompt routing.
- **Endpoints**:
  - `GET /`: Serves the static single-page Web UI.
  - `POST /upload`: Ingests document/image upload streams, routes to parser, appends vectors to KB index.
  - `POST /chat`: Receives chat messages, dispatches to Model Router or RAG Engine, returns JSON answers.
- **Router Logic**:
  - Coding keyword match → `route: coding` → `qwen2.5-coder:7b`.
  - `knowledge_enabled == true` → `route: rag` → Vector Search → Grounded `qwen3.5:4b`.
  - Default → `route: general` → Direct `qwen3.5:4b`.

---

### Module 3: Multimodal Document & Image Parsing Engine
- **Responsibility**: Handles file decoding and text extraction across heterogeneous file types.
- **Supported File Adapters**:
  - `PDF Adapter`: Uses `pypdf.PdfReader` to extract text from multi-page PDFs.
  - `Text/Markdown Adapter`: Native UTF-8 string file decoding.
  - `OCR Adapter`: Encodes `.png`, `.jpg`, `.jpeg`, `.webp` into Ollama chat payload, calls `glm-ocr:q8_0` for visual text extraction.
- **Input**: File streams saved to `data/knowledge_base/`.
- **Output**: Cleaned normalized text string.

---

### Module 4: Vector Indexing & Cosine Search Engine (`kb_index.py` & `kb_search.py`)
- **Responsibility**: Generates text embeddings, maintains vector store state, and executes high-speed similarity search.
- **Core Operations**:
  - `Chunking`: Splits normalized text into 500-character windows with 50-character overlap.
  - `Embedding Generation`: Calls local `nomic-embed-text` via Ollama Python client to generate 768-dimensional float arrays.
  - `Index Persistence`: Writes JSON structure to `data/kb_index.json`.
  - `Cosine Search`: Performs dot-product cosine similarity vector math between query vector and index vectors to return Top-K matching snippets.

---

### Module 5: Local LLM Runtime Manager (Ollama Interface)
- **Responsibility**: Manages IPC communications with local Ollama daemon.
- **Hosted Models**:
  - `qwen3.5:4b`: General reasoning & RAG synthesis.
  - `qwen2.5-coder:7b`: Code generation.
  - `glm-ocr:q8_0`: OCR text extraction.
  - `nomic-embed-text`: Text embedding generation.
- **Settings**: Thinking mode turned OFF (`--think=false`) for low latency inference.

---

### Module 6: Grounding & Anti-Hallucination Guardrail Module
- **Responsibility**: Enforces truthfulness and strict context boundaries during RAG generation.
- **Guardrail Rule**:
  - System prompt enforces: *"Answer ONLY based on the provided context. If the answer cannot be found in the context, explicitly state 'That information is not available in the knowledge base.'"*
  - Rejects speculative answers when retrieval score is below threshold.
