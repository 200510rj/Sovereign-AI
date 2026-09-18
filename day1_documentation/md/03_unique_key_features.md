# Task 1 — Document 03: Unique Key Features

> **Problem Statement ID:** PS 26117 / SIH26117  
> **Title:** Sovereign On-Premise Agentic AI Workbench using Open-Weight Multimodal LLMs for Confidential Industrial Work  
> **Organization:** Mangalore Refinery and Petrochemicals Limited (MRPL)  
> **Category:** Software | **Theme:** Smart Automation  

---

## 💡 Overview of Innovations & Key Features

The **Sovereign AI Workbench** stands out from traditional cloud AI services and generic chatbot templates through several specialized architectural innovations designed specifically for confidential industrial operations.

| Key Feature | Technical Innovation | Operational Benefit |
|---|---|---|
| **🛡️ 1. Air-Gapped Sovereignty** | 100% On-Premise Ollama Local Runtime | Zero data exfiltration; complete network air-gap compliance. |
| **🖼️ 2. Integrated Multimodal OCR** | Local `glm-ocr:q8_0` Extraction | Scanned handwritten logs & inspection photos directly searchable. |
| **🧠 3. Task Specialist Routing** | Model Router (`qwen3.5:4b` / `qwen2.5-coder:7b`) | Optimal model dispatch for coding vs. grounded reasoning tasks. |
| **⚡ 4. Zero-DB Vector Store** | Pure Python Cosine Similarity Engine | High-speed dot-product vector search without heavy vector DB setup. |
| **🎯 5. Anti-Hallucination Guardrail** | Grounded System Prompting & Threshold Rejection | Rejects ungrounded queries ("Information not available in KB"). |
| **🎛️ 6. Single-Toggle UI Control** | Dynamic Knowledge ON/OFF Switch | Seamless transition between general conversation and strict RAG Q&A. |

---

## 📄 Feature 1: 100% Air-Gapped Data Sovereignty

- **Zero Cloud API Dependency**: Does not rely on OpenAI, Anthropic, Google, or any cloud API endpoints.
- **Air-Gap Certified Execution**: Runs completely offline after initial deployment. Suitable for installation on isolated industrial control system (ICS) networks or air-gapped refinery workstations.
- **Privacy Assurance**: Sensitive operational SOPs, plant blueprints, and maintenance logs never leave the local hardware.

---

## 🖼️ Feature 2: Multimodal Image OCR Pipeline (`glm-ocr:q8_0`)

- **Unified Ingestion**: Handles both standard digital documents (`.pdf`, `.txt`, `.md`) and image files (`.png`, `.jpg`, `.jpeg`, `.webp`).
- **High-Precision OCR Model**: Employs `glm-ocr:q8_0`, a specialized quantized vision-language OCR model running via Ollama.
- **Seamless Vector Indexing**: OCR output text is automatically passed to the chunking engine, embedded via `nomic-embed-text`, and integrated into the primary Knowledge Base without creating fragmented data silos.

---

## 🧠 Feature 3: Specialized Task Routing Engine

- **Model Specialization over One-Size-Fits-All**: Rather than relying on a single monolithic model, the workbench dynamically dispatches prompts to specialized models:
  - **General Reasoning & Grounded RAG**: Powered by `qwen3.5:4b`.
  - **Code Synthesis & Scripting**: Automatically routed to `qwen2.5-coder:7b`.
  - **OCR Text Extraction**: Dispatched to `glm-ocr:q8_0`.
- **Latency & Resource Optimization**: Using smaller, quantized, high-efficiency models allows high performance on standard workstation hardware.

---

## ⚡ Feature 4: In-Memory Cosine Vector Engine (Zero Heavy DB Overhead)

- **No Heavy Vector Database Needed**: Traditional RAG systems require setting up heavy databases (Milvus, Qdrant, Pinecone), increasing infrastructure complexity.
- **Pure Python Cosine Similarity Engine**: Computes high-speed dot-product and cosine similarity vectors directly in memory, serializing state to a clean JSON index file (`kb_index.json`).
- **Instant Deployment**: Simplifies deployment to a single command (`python main.py` / `uvicorn main:app`).

---

## 🎯 Feature 5: Grounded RAG & Strict Anti-Hallucination Guardrails

- **Context-Bound Prompt Engineering**: Grounded queries strictly instruct the model to base answers solely on retrieved top-K context chunks.
- **Honest Fallback Guardrail**: When queried about non-indexed topics (e.g., *"What is the refinery emergency shutdown procedure?"* when no shutdown SOP is uploaded), the system explicitly responds:
  > *"That information is not available in the knowledge base."*
- **Source Transparency**: Every grounded answer includes source document names and exact cosine similarity matching scores (e.g., `test_sop.txt — Score: 0.9421`).

---

## 🎛️ Feature 6: Responsive Dark-Themed Single-Page Web UI

- **User-Centric Design**: Clean, modern dark-themed web interface built using Vanilla HTML5, CSS3, and JavaScript.
- **Knowledge Toggle (`Knowledge ON/OFF`)**: Allows users to seamlessly switch between general conversation mode and grounded document Q&A mode with a single click.
- **Real-Time Drag & Drop File Upload**: Simple interface for uploading PDFs, text files, and inspection images with instant status feedback.
