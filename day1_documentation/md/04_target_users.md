# Task 1 — Document 04: Target Users & Industrial Personas

> **Problem Statement ID:** PS 26117 / SIH26117  
> **Title:** Sovereign On-Premise Agentic AI Workbench using Open-Weight Multimodal LLMs for Confidential Industrial Work  
> **Organization:** Mangalore Refinery and Petrochemicals Limited (MRPL)  
> **Category:** Software | **Theme:** Smart Automation  

---

## 👥 Overview of Target User Groups

The **Sovereign AI Workbench** is tailored for multidisciplinary teams operating within confidential industrial refining facilities. Below are the primary user personas, their operational pain points, and specific workbench use cases.

| Persona Group | Primary Focus & Tasks | Primary Workbench Solution |
|---|---|---|
| **⚙️ 1. Plant Maintenance & Equipment Engineers** | Pump inspection verification, compressor SOP step retrieval, maintenance logs. | Grounded RAG search over equipment SOP manuals & OCR scanned inspection sheets. |
| **🛡️ 2. Health, Safety & Environment (HSE) Officers** | Emergency shutdown procedures, hazardous chemical handling, compliance audits. | Grounded safety manual retrieval with strict anti-hallucination fallback. |
| **💻 3. Industrial IT & Automation Engineers** | Writing automation scripts, PLC data parsing, API development, local debugging. | Local code synthesis via `qwen2.5-coder:7b` without cloud code exposure. |
| **👔 4. Plant Management & Executive Leadership** | Decision support, executive shift report summaries, milestone tracking. | Instant AI summarization of daily shift reports and plant progress logs. |

---

## 🛠️ Detailed Persona Profiles

### Persona 1: Plant Maintenance & Equipment Engineers
- **Role**: Field Engineers responsible for maintaining mechanical equipment (pumps, turbines, heat exchangers, valves) across MRPL refinery units.
- **Pain Point**: Finding specific torque values, vibration limits, or inspection checklists buried in 500-page vendor manuals or handwritten paper logs.
- **Workbench Solution**:
  - Uploads equipment manual PDFs and photos of handwritten inspection sheets.
  - Queries: *"What is the acceptable pump vibration threshold during normal operation according to the SOP?"*
  - Receives grounded answers with direct citations (`test_sop.txt`).

---

### Persona 2: Health, Safety & Environment (HSE) Officers
- **Role**: Officers ensuring strict adherence to environmental regulations, personal protective equipment (PPE) guidelines, and emergency shutdown protocols.
- **Pain Point**: Cross-referencing multiple safety regulations during live plant safety audits or incident investigations.
- **Workbench Solution**:
  - Indexes all plant safety manuals into the local Knowledge Base.
  - Queries: *"What are the mandated safety protocols for hydrogen sulfide (H2S) leak containment?"*
  - Relies on anti-hallucination guardrails: if an H2S manual hasn't been uploaded, system responds with missing data warning rather than inventing safety steps.

---

### Persona 3: Industrial IT & Automation Engineers
- **Role**: Control system engineers and software developers writing internal automation scripts, PLC data parsers, and monitoring tools.
- **Pain Point**: Needing AI coding assistance for Python/FastAPI automation without leaking internal code snippets to commercial cloud LLMs.
- **Workbench Solution**:
  - Uses the workbench for code generation and debugging.
  - Automatic model router routes coding prompts to `qwen2.5-coder:7b`.
  - Generates clean Python code, regex parsers, or SQL queries locally.

---

### Persona 4: Plant Management & Executive Leadership
- **Role**: Refinery Operations Managers, Unit Heads, and General Managers.
- **Pain Point**: Requiring immediate operational insights from daily plant shift logs and high-level reports without waiting for manual summary compilation.
- **Workbench Solution**:
  - Uploads daily shift reports and milestone progress documents.
  - Asks high-level summary questions: *"Summarize key maintenance activities completed during Shift A in Unit 2."*
  - Fast, grounded decision support with zero data privacy risks.

---

## 📊 Business Impact & Benefit Matrix

| Persona | Primary Metric Improved | Before Workbench | With Sovereign Workbench |
|---|---|---|---|
| **Maintenance Engineer** | SOP Retrieval Time | 45-60 minutes manual search | **< 5 seconds** grounded answer |
| **HSE Officer** | Audit Accuracy & Safety Compliance | Manual cross-referencing paper binders | **100% Grounded RAG** with source citations |
| **Automation Engineer** | Code Generation Speed | 2-3 hours writing scripts from scratch | **Instant local code synthesis** via Qwen Coder |
| **Plant Manager** | Decision Support Velocity | Hours waiting for compiled shift reports | **Instant AI summarization** of local shift logs |
| **Cybersecurity Team** | Data Leakage Prevention | Risk of sensitive data sent to Cloud APIs | **100% Air-Gapped**, 0 outbound calls |
