# Task 1 — Document 02: Proposed Solution

> **Problem Statement ID:** PS 26117 / SIH26117  
> **Title:** Sovereign On-Premise Agentic AI Workbench using Open-Weight Multimodal LLMs for Confidential Industrial Work  
> **Organization:** Mangalore Refinery and Petrochemicals Limited (MRPL)  
> **Category:** Software | **Theme:** Smart Automation  

---

## 1. Solution Overview

The **Sovereign AI Workbench** is a specialized, air-gapped, on-premise artificial intelligence workstation designed to serve as an intelligent digital assistant for MRPL industrial engineers. 

By unifying open-weight large language models (LLMs), local visual text extraction (OCR), and dense vector similarity retrieval into a cohesive single-node FastAPI backend, the solution guarantees **complete data sovereignty**: zero bytes of data, prompts, embeddings, or inspection images ever cross the local network boundary.

### High-Level Architecture Component Mapping

| Core Component | Technical Subsystem | Primary Function |
|---|---|---|
| **Local Multimodal OCR Pipeline** | `glm-ocr:q8_0` | Extracts text from scanned images, nameplates, and maintenance logs. |
| **Local RAG Vector Engine** | `nomic-embed-text` + Cosine Store | Ingests PDFs/TXTs, generates 768-dim embeddings, performs similarity search. |
| **Specialized Model Task Router** | Router Engine in `main.py` | Routes prompts to `qwen3.5:4b` (RAG/General) or `qwen2.5-coder:7b` (Coding). |

---

## 2. Core Architectural Pillars

### Pillar 1: Total Data Sovereignty & Offline Execution
- Built on top of **Ollama**, an open-source model execution runtime that hosts and executes GGUF/quantized models directly on local GPU/CPU hardware.
- Fully air-gap friendly. No outbound HTTP/HTTPS connections required after initial model deployment.

### Pillar 2: Dense Retrieval-Augmented Generation (Local RAG)
- Incoming confidential documents (PDFs, TXT, Markdown) are automatically split into semantic text chunks.
- High-dimensional vector embeddings are generated using `nomic-embed-text` locally.
- Chunks and embedding vectors are stored in a lightweight, local JSON index (`kb_index.json`).
- Semantic search computes cosine similarity between user queries and stored chunk embeddings to retrieve the top 5 most relevant context snippets in milliseconds.

### Pillar 3: Grounded Answering & Strict Anti-Hallucination Guardrails
- When **Knowledge Mode** is enabled (`knowledge_enabled: true`), the LLM (`qwen3.5:4b`) is strictly instructed via system prompt engineering to answer **only** using the retrieved chunk context.
- If the semantic similarity score of retrieved context falls below threshold, or if the relevant information is absent from the Knowledge Base, the system responds:
  > *"That information is not available in the knowledge base."*
- Prevents dangerous speculative hallucinations during critical refinery equipment queries.

### Pillar 4: Multimodal Inspection Image Parsing (GLM-OCR Integration)
- Plant engineers frequently capture physical equipment inspection logs, nameplates, or printed reports.
- Using `glm-ocr:q8_0`, the workbench automatically extracts structured text from `.png`, `.jpg`, `.jpeg`, and `.webp` images.
- Extracted OCR text is instantly chunked, embedded, and appended to the local knowledge base, making scanned reports instantly searchable alongside standard PDFs.

### Pillar 5: Intelligent Task Routing & Dedicated Specialist Models
- Queries containing coding keywords (`python`, `code`, `fastapi`, `script`, `function`, `algorithm`, `sql`) are routed to `qwen2.5-coder:7b` for precise code synthesis.
- General operational or grounded document queries are handled by `qwen3.5:4b`.

---

## 3. Operational Workflow Matrix

| User Input Type | Processing Pipeline | Model / Tool Used | Expected Output |
|---|---|---|---|
| **PDF Document Upload** | Text Extraction → Chunking → Local Vector Embeddings | `pypdf` + `nomic-embed-text` | Grounded KB Index Entry |
| **Image / Scanned Log Upload** | Image Extraction → Local OCR → Text Chunking → Embeddings | `glm-ocr:q8_0` + `nomic-embed-text` | Grounded KB Index Entry |
| **Grounded Question (Knowledge ON)** | Vector Cosine Search → Top-K Retrieval → Grounded Prompt | `nomic-embed-text` + `qwen3.5:4b` | Factual Answer + Source Citations |
| **General Query (Knowledge OFF)** | Direct Inference | `qwen3.5:4b` | General AI Response |
| **Coding / Scripting Request** | Keyword Task Router → Code Prompt Generation | `qwen2.5-coder:7b` | Executable Code / Script |

---

## 4. Alignment with MRPL Industrial Safety & SOP Requirements

1. **Refinery SOP Verification**: Allows maintenance crews to quickly verify exact step-by-step pump/compressor maintenance procedures directly from indexed MRPL manuals.
2. **HSE (Health, Safety & Environment) Audit Readiness**: Instantly retrieves safety guidelines, hazardous material handling steps, and emergency shutdown procedures.
3. **Equipment History Indexing**: Historical inspection reports (scanned or digital) can be uploaded in bulk, building an institutional memory accessible to all plant engineers.
