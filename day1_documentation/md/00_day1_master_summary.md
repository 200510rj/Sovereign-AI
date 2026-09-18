# SIH 2026 — Day 1 Task 1: Master Summary Document
> **Problem Statement ID:** PS 26117 / SIH26117  
> **Title:** Sovereign On-Premise Agentic AI Workbench using Open-Weight Multimodal LLMs for Confidential Industrial Work  
> **Organization:** Mangalore Refinery and Petrochemicals Limited (MRPL)  
> **Category:** Software | **Theme:** Smart Automation  

---

## 📌 Executive Summary

This documentation repository contains the complete **Day 1 Task 1: Problem Understanding, Solution Planning & System Design** package for SIH 2026. 

The **Sovereign AI Workbench** is a 100% local, air-gapped, privacy-first AI platform engineered specifically for heavy industrial confidential environments like **MRPL refineries**. It eliminates external cloud telemetry and data leakage by running quantized open-weight LLMs (`qwen3.5:4b`, `qwen2.5-coder:7b`, `glm-ocr:q8_0`, `nomic-embed-text`) entirely on local edge hardware via Ollama and FastAPI.

---

## 📁 Day 1 Documentation Index

| # | Document | Target Section / Focus Area |
|---|---|---|
| **01** | [`01_problem_statement_understanding.md`](01_problem_statement_understanding.md) | MRPL Context, Industrial Pain Points, Air-Gap Constraints & Scope |
| **02** | [`02_proposed_solution.md`](02_proposed_solution.md) | Solution Core, Operational Capabilities & Anti-Hallucination Guardrails |
| **03** | [`03_unique_key_features.md`](03_unique_key_features.md) | Key Innovations, Multimodal OCR Pipeline, In-Memory Cosine RAG Engine |
| **04** | [`04_target_users.md`](04_target_users.md) | Industrial User Personas (Plant Engineers, Safety Officers, IT, Executives) |
| **05** | [`05_system_architecture.md`](05_system_architecture.md) | High-Level Architecture Diagram, Layer Breakdown & Component Specs |
| **06** | [`06_workflow_user_flow_diagram.md`](06_workflow_user_flow_diagram.md) | Interactive Sequence Diagrams (OCR Ingestion, RAG Grounding, Code Generation) |
| **07** | [`07_data_flow_diagram.md`](07_data_flow_diagram.md) | DFD Level 0 (Context Diagram), Level 1 (System Processes), Level 2 (OCR/RAG) |
| **08** | [`08_module_definition.md`](08_module_definition.md) | Software Modules (UI Gateway, FastAPI Router, Vector Engine, Model Runtime) |
| **09** | [`09_technology_stack.md`](09_technology_stack.md) | Open-Weight Models Matrix, Tech Justification & Hardware Specs |

---

## 🎯 Mentor Review Alignment Matrix

| Mentor Evaluation Metric | Addressed In Document | Key Highlights |
|---|---|---|
| **Problem–Solution Alignment** | `01_problem_statement_understanding.md`, `02_proposed_solution.md` | Tailored specifically for MRPL refinery SOPs, plant safety, and confidential blueprints. |
| **Technical Feasibility** | `09_technology_stack.md`, `05_system_architecture.md` | 100% working local stack with Ollama, FastAPI, and quantized models on consumer hardware. |
| **System Architecture** | `05_system_architecture.md` | Modular 4-tier design: Frontend, FastAPI Gateway, Cosine Vector Engine, Local Model Runtime. |
| **Workflow / User Flow** | `06_workflow_user_flow_diagram.md` | Clear flowcharts and sequence diagrams for Document Upload, RAG Querying, and OCR processing. |
| **Data Flow Diagram (DFD)** | `07_data_flow_diagram.md` | Complete DFD Level 0, Level 1, and Level 2 pipeline mappings. |
| **Scalability & Security** | `03_unique_key_features.md`, `09_technology_stack.md` | Air-gapped network isolation with zero telemetry; scalable through modular tool definitions. |
| **Module Clarity** | `08_module_definition.md` | Clean separation of concerns between web frontend, backend routing, OCR, RAG, and LLMs. |
| **Innovation & Uniqueness** | `03_unique_key_features.md` | Local GLM-OCR multimodal pipeline + lightweight in-memory cosine vector store with zero DB overhead. |

---

## 🚀 Quick Verification & Demo Status

- ✅ **Local Model Execution**: `qwen3.5:4b` (General/RAG), `qwen2.5-coder:7b` (Code), `glm-ocr:q8_0` (OCR), `nomic-embed-text` (Embeddings) running locally via Ollama.
- ✅ **Local RAG Pipeline**: Grounded vector search over uploaded PDFs and text files with strict fallback when info is missing.
- ✅ **Local OCR Ingestion**: Scanned image text extraction via GLM-OCR feeding into the same unified vector knowledge index.
- ✅ **FastAPI Backend + Web UI**: Functional web interface served directly from local Python backend.
