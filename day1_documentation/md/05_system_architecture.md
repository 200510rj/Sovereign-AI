# Task 1 — Document 05: System Architecture

> **Problem Statement ID:** PS 26117 / SIH26117  
> **Title:** Sovereign On-Premise Agentic AI Workbench using Open-Weight Multimodal LLMs for Confidential Industrial Work  
> **Organization:** Mangalore Refinery and Petrochemicals Limited (MRPL)  
> **Category:** Software | **Theme:** Smart Automation  

---

## 🏗️ Architectural Overview

The **Sovereign AI Workbench** is structured around a 4-tier modular, air-gapped architecture. Designed for single-node workstation or edge server deployment, the system decouples user interface, backend routing, vector search processing, and local LLM runtime execution.

```mermaid
graph TD
    %% Styling
    classDef ui fill:#1e293b,stroke:#38bdf8,stroke-width:2px,color:#fff;
    classDef api fill:#0f172a,stroke:#818cf8,stroke-width:2px,color:#fff;
    classDef rag fill:#1e1b4b,stroke:#c084fc,stroke-width:2px,color:#fff;
    classDef model fill:#064e3b,stroke:#34d399,stroke-width:2px,color:#fff;
    classDef store fill:#451a03,stroke:#fb923c,stroke-width:2px,color:#fff;

    subgraph Tier1["1. Presentation Layer (Browser UI)"]
        UI["Dark-Themed Single Page App<br/>(Vanilla HTML5 / CSS3 / JS)"]:::ui
        Toggle["Knowledge Mode Toggle<br/>(ON / OFF)"]:::ui
        UploadBtn["Multimodal File Upload<br/>(PDF, TXT, PNG, JPG, WEBP)"]:::ui
    end

    subgraph Tier2["2. Application Gateway & Router Layer (FastAPI Backend)"]
        API["FastAPI Server (main.py)<br/>Port: 8000"]:::api
        Router{"Task Router Engine"}:::api
    end

    subgraph Tier3["3. Document Processing & Local RAG Vector Engine"]
        PDFParser["PDF Parser (pypdf)"]:::rag
        OCRParser["Local OCR Engine<br/>(GLM-OCR:q8_0)"]:::rag
        Chunker["Semantic Text Chunker<br/>(500 char chunks / overlap)"]:::rag
        Embedder["Embeddings Model<br/>(nomic-embed-text)"]:::rag
        CosineSearch["In-Memory Cosine Similarity<br/>Search Engine"]:::rag
    end

    subgraph Tier4["4. Local Open-Weight Model Runtime (Ollama)"]
        OllamaRuntime["Local Ollama Service Runtime"]:::model
        GeneralLLM["qwen3.5:4b<br/>(General & Grounded RAG)"]:::model
        CoderLLM["qwen2.5-coder:7b<br/>(Dedicated Coding)"]:::model
        OCRLModel["glm-ocr:q8_0<br/>(Vision OCR Extraction)"]:::model
    end

    subgraph Tier5["5. Storage Layer (Local Disk)"]
        FileStore["data/knowledge_base/<br/>(Source Documents & Images)"]:::store
        VectorIndex["data/kb_index.json<br/>(Serialized Vector Index)"]:::store
    end

    %% Flow Connections
    UI -->|HTTP Requests| API
    UploadBtn -->|POST /upload| API
    Toggle -->|Chat Config| API
    API --> Router

    Router -->|Image File| OCRParser
    Router -->|PDF / Text File| PDFParser
    Router -->|Coding Keywords| CoderLLM
    Router -->|Knowledge ON| CosineSearch
    Router -->|Knowledge OFF / General| GeneralLLM

    OCRParser -->|Extract Text| OllamaRuntime
    OllamaRuntime -->|Return OCR Text| Chunker
    PDFParser -->|Extract Text| Chunker

    Chunker -->|Text Chunks| Embedder
    Embedder -->|Generate Vectors via Ollama| OllamaRuntime
    Embedder -->|Save Chunks & Vectors| VectorIndex
    PDFParser -->|Save Raw File| FileStore

    CosineSearch -->|Query Vector| Embedder
    CosineSearch -->|Load Index| VectorIndex
    CosineSearch -->|Top-5 Context Chunks| GeneralLLM

    GeneralLLM -->|Generate Grounded Response| API
    CoderLLM -->|Generate Code Response| API
    API -->|JSON Response + Sources| UI
```

---

## 🧩 Architectural Layer Details

### 1. Presentation Layer (Web UI)
- **Technology**: Single-page application using HTML5, CSS3 (Flexbox/Grid, Dark Modern Palette), and asynchronous JavaScript (`fetch` API).
- **Functionality**:
  - Chat window rendering user prompts and AI responses with markdown support.
  - Interactive file uploader with real-time status notifications.
  - Knowledge ON/OFF toggle controlling RAG augmentation.
  - Real-time display of retrieved source documents and cosine similarity scores.

### 2. Application Gateway Layer (`main.py`)
- **Technology**: Python FastAPI with Uvicorn ASGI server.
- **Functionality**:
  - Serves static UI assets (`frontend/index.html`).
  - Endpoints: `POST /upload` for file processing, `POST /chat` for conversational Q&A.
  - **Task Router**: Inspects prompt text and parameters to select the execution path (Coding Model vs. RAG Grounded Model vs. General LLM).

### 3. Document Processing & Local Vector RAG Engine
- **Text Parser**: `pypdf` extracts clean text streams from multi-page PDFs.
- **OCR Extractor**: Invokes `glm-ocr:q8_0` via local Ollama API to transcribe scanned images.
- **Chunking Module**: Splits documents into overlapping semantic chunks (500 characters) to preserve contextual boundaries.
- **Embedding Pipeline**: Transmits text chunks to local `nomic-embed-text` model via Ollama to generate 768-dimensional dense vector representations.
- **Vector Storage & Search**: Saves chunk metadata and vectors into `data/kb_index.json`. Executes fast in-memory dot-product cosine similarity search to retrieve top-K matching contexts.

### 4. Local Model Execution Layer (Ollama)
- **Runtime**: Ollama daemon running on localhost (`http://127.0.0.1:11434`).
- **Model Palette**:
  - `qwen3.5:4b`: Primary general-purpose LLM for conversational chat and grounded RAG synthesis.
  - `qwen2.5-coder:7b`: Code generation specialist.
  - `glm-ocr:q8_0`: Document image OCR specialist.
  - `nomic-embed-text`: High-speed text embedding generator.

### 5. Storage Layer
- **Physical Disk Storage**: All files reside in local workstation directory `d:\isha\sovereign-ai\data\`.
- **Air-Gap Security**: Zero external network connections; completely self-contained.
