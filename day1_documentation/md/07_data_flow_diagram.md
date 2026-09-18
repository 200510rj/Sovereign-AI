# Task 1 — Document 07: Data Flow Diagrams (DFD)

> **Problem Statement ID:** PS 26117 / SIH26117  
> **Title:** Sovereign On-Premise Agentic AI Workbench using Open-Weight Multimodal LLMs for Confidential Industrial Work  
> **Organization:** Mangalore Refinery and Petrochemicals Limited (MRPL)  
> **Category:** Software | **Theme:** Smart Automation  

---

## 📊 1. DFD Level 0 — Context Diagram

The Level 0 Context Diagram represents the system boundary of the **Sovereign AI Workbench**, showing external entities (Plant User, Local Disk Storage, Local Model Runtime) and major data inputs/outputs.

```mermaid
graph LR
    User[Plant Engineer / User]
    System(("0.0<br/>Sovereign AI<br/>Workbench<br/>System"))
    Storage[(Local Disk Storage<br/>data/)]
    OllamaRuntime[Local Ollama<br/>Model Runtime]

    %% User Inputs & Outputs
    User -->|Uploaded Files: PDF, PNG, TXT| System
    User -->|Chat Queries & Settings| System
    System -->|Grounded Answers & Code| User
    System -->|Source Citations & Scores| User

    %% Storage Interactivity
    System -->|Store Raw Files & JSON Index| Storage
    Storage -->|Load Vector Index & Chunks| System

    %% Local LLM Execution
    System -->|Prompt & Image Payloads| OllamaRuntime
    OllamaRuntime -->|OCR Text, Embeddings, LLM Answers| System
```

---

## 🔄 2. DFD Level 1 — System Process Overview

Level 1 decomposes the system into four main logical data processes: Document Parsing/OCR, Vector Embedding & Indexing, Task Routing & Retrieval, and Grounded Inference.

```mermaid
graph TD
    User[Plant User]
    
    %% Processes
    P1(("1.0<br/>Multimodal Ingestion<br/>& Parsing"))
    P2(("2.0<br/>Chunking & Embedding<br/>Vector Store"))
    P3(("3.0<br/>Task Routing &<br/>Cosine Retrieval"))
    P4(("4.0<br/>Local Model<br/>Inference"))
    
    %% Data Stores
    D1[("D1: Knowledge Base Files<br/>data/knowledge_base/")]
    D2[("D2: Vector Index Store<br/>data/kb_index.json")]
    
    %% External Runtime
    Ollama[Local Ollama Models]

    %% Data Flow Lines
    User -->|Upload PDF / Image| P1
    P1 -->|Save Raw File| D1
    P1 -->|Image Payload| Ollama
    Ollama -->|Extracted OCR Text| P1
    P1 -->|Clean Document Text| P2

    P2 -->|Text Snippets| Ollama
    Ollama -->|Dense Vector Arrays| P2
    P2 -->|Save Chunks & Vectors| D2

    User -->|Submit User Prompt| P3
    P3 -->|Read Vectors & Chunks| D2
    P3 -->|Top-5 Matching Context| P4

    User -->|Prompt Settings| P4
    P4 -->|Prompt Payload| Ollama
    Ollama -->|Generated LLM Answer| P4
    P4 -->|Final Response + Citations| User
```

---

## 🔬 3. DFD Level 2 — Process 1.0 (Multimodal Document & Image Ingestion Pipeline)

Level 2 zooms into Process 1.0 to depict the exact transformation steps from raw uploaded documents to clean text chunks.

```mermaid
graph TD
    FileInput[Raw Upload File]
    
    FormatCheck{Format Classifier}
    
    PDFHandler["1.1 PDF Parser<br/>(pypdf Reader)"]
    ImageHandler["1.2 OCR Dispatcher<br/>(GLM-OCR)"]
    TextHandler["1.3 Text Reader<br/>(Direct UTF-8 Read)"]
    
    CleanText["1.4 Text Normalizer<br/>(Strip outer code fences)"]
    Chunker["1.5 Semantic Chunker<br/>(500 char window / 50 overlap)"]
    
    DataOutput[Clean Chunk Array to Process 2.0]

    FileInput --> FormatCheck
    FormatCheck -->|.pdf| PDFHandler
    FormatCheck -->|.png, .jpg, .webp| ImageHandler
    FormatCheck -->|.txt, .md| TextHandler

    PDFHandler -->|Extracted Text| CleanText
    ImageHandler -->|Extracted Text| CleanText
    TextHandler -->|Raw Content| CleanText

    CleanText --> Chunker
    Chunker --> DataOutput
```

---

## 📖 4. Data Dictionary

| Data Element | Type | Source | Destination | Description |
|---|---|---|---|---|
| `uploaded_file` | Binary Stream | User UI | Process 1.0 | PDF document or image file uploaded via form payload. |
| `ocr_prompt_payload` | Base64 / Path | Process 1.2 | Ollama (`glm-ocr`) | Image payload sent to local OCR model. |
| `raw_text_stream` | String | Process 1.0 | Process 1.4 | Extracted text before normalization. |
| `chunk_record` | JSON Object | Process 2.0 | `D2: kb_index.json` | Contains `chunk_id`, `text`, `source_file`, and 768-dim `embedding` array. |
| `user_query` | String | User UI | Process 3.0 | Text prompt entered by user in Web UI. |
| `query_vector` | Array[768] | Process 3.0 | Cosine Search Engine | 768-dimensional float embedding of user query. |
| `cosine_match_score` | Float [0.0 - 1.0] | Cosine Search Engine | Process 4.0 | Cosine similarity score between query vector and chunk vector. |
| `grounded_response` | JSON Object | Process 4.0 | User UI | Contains generated LLM answer text, route used, and source document metadata array. |
