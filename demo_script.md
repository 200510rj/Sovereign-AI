# Sovereign AI Workbench — 5-Minute SIH Presentation & Live Demo Script

> **Competition:** Smart India Hackathon (SIH 2026)  
> **Problem Statement:** SIH 26117 — Sovereign On-Premise Agentic AI Workbench using Open-Weight Multimodal LLMs for Confidential Industrial Work  
> **Target Organization:** Mangalore Refinery and Petrochemicals Limited (MRPL)  
> **Theme:** Smart Automation / Software  

---

## ⏱️ Quick Timeline (5 Minutes Total)

```
00:00 - 00:45 | Introduction & Problem Statement (Air-Gap Constraint)
00:45 - 01:45 | Live Proof #1: Zero Network Leakage & Local Knowledge RAG
01:45 - 02:45 | Live Proof #2: Autonomous Multi-Step Agentic Workflow
02:45 - 03:45 | Live Proof #3: Sandboxed Code Execution & Dynamic Deliverables
03:45 - 04:30 | Multimodal OCR & SQLite Persistence Architecture
04:30 - 05:00 | Conclusion, Q&A & Commercial Feasibility
```

---

## 🎯 Minute-by-Minute Walkthrough

### 00:00 – 00:45: Introduction & The Core Problem

**Presenter says:**
> *"Respected judges, critical industrial assets like Mangalore Refinery (MRPL) handle proprietary P&ID diagrams, confidential inspection SOPs, and telemetry data that can never leave the refinery premises. Cloud-based APIs like ChatGPT or Claude pose severe compliance and data sovereignty risks.*  
> 
> *We present **Sovereign AI Workbench** — a 100% on-premise, air-gapped agentic AI workstation. It runs entirely on local open-weight models (`qwen3.5:4b`, `qwen2.5-coder:7b`, `nomic-embed-text`, and `glm-ocr`), making zero external network calls."*

**Action on Screen:**
- Show the Workbench UI at `http://127.0.0.1:8000`.
- Point to the **🛡️ 100% Air-Gapped** badge and the **Air-Gap Verified (0 Outbound)** status pill.

---

### 00:45 – 01:45: Live Proof #1 — Air-Gap Audit & Knowledge-Grounded RAG

**Presenter says:**
> *"First, let's verify our air-gap claim. Notice the live network audit badge in the header. Our system audits all OS sockets via `psutil` in real-time, verifying exactly zero outbound connections from our server process.*  
> 
> *Now let's query a confidential refinery standard: 'Summarize the standard operating procedure for centrifugal pump inspection.'*  
> *Notice the Knowledge Base toggle: our hybrid vector-and-keyword search retrieves the exact chunk from `test_sop.txt` (`SOP-PUMP-001`), providing a fully cited, hallucination-free answer with similarity confidence scores."*

**Action on Screen:**
- Click the **Air-Gap pill** to show the real-time audit toast (`PID 12472: 0 Outbound Calls`).
- Send the query: *"Summarize the standard operating procedure for centrifugal pump inspection"*.
- Expand the **📚 Retrieved Knowledge Sources** accordion and click a chunk to show the modal preview.

---

### 01:45 – 02:45: Live Proof #2 — Autonomous Multi-Step Agentic Workflow

**Presenter says:**
> *"Now we move beyond static question-answering to **Stage 4 Agentic Automation**. We enable **Agent Mode**.*  
> 
> *We ask the workbench: 'Search the knowledge base for centrifugal pump inspection, read the SOP, and generate an official PDF inspection checklist.'*  
> 
> *Watch the ReAct agent loop in action: without any hardcoded routing, `qwen3.5:4b` dynamically invokes `search_knowledge_base`, parses the document with `read_uploaded_document`, and chains into `generate_report` to create a real, styled enterprise PDF deliverable."*

**Action on Screen:**
- Toggle **Agent Mode ON** (purple pill activates).
- Click or type: *"Search the knowledge base for pump inspection requirements and generate a PDF report with the findings"*.
- Highlight the **🤖 Autonomous Execution Steps** timeline in the response showing Step 1, Step 2, and Step 3.
- Click the **📥 Download PDF** button to show the styled ReportLab PDF.

---

### 02:45 – 03:45: Live Proof #3 — Code Sandbox & Dynamic Deliverables

**Presenter says:**
> *"Industrial engineers often need computations — calculating pipe friction losses, heat exchanger thermal efficiency, or pressure drops.*  
> 
> *When an engineer asks for a computation: 'Write a Python script to calculate pressure drops in oil pipelines with the Darcy-Weisbach equation,' the router automatically delegates to `qwen2.5-coder:7b`.*  
> 
> *The code block is rendered with syntax highlighting and an interactive **▶ Run Code** button. Clicking it executes the script in an isolated local subprocess with strict timeout guards, displaying stdout directly in an inline terminal console. Furthermore, any response can be exported instantly to Word (.docx), Excel (.xlsx), or PDF."*

**Action on Screen:**
- Ask the Darcy-Weisbach pipeline calculation query.
- Click **▶ Run Code** on the assistant's code block → show green terminal output.
- Click the **📊 XLSX** export button on the message meta header → download the Excel file.

---

### 03:45 – 04:30: Architecture & Multimodal Capabilities

**Presenter says:**
> *"Under the hood, Sovereign AI Workbench is powered by a robust 4-tier local architecture:*  
> 1. *Client Layer: Fast, responsive dark UI using local vendored JavaScript (no CDNs).*  
> 2. *Application Layer: FastAPI asynchronous gateway with SQLite persistence for sessions and messages.*  
> 3. *Vector & Reasoning Engine: Nomic-embed-text with hybrid semantic + keyword scoring and custom PDF normalizers that eliminate letter-spacing kerning artifacts.*  
> 4. *Multimodal OCR: GLM-OCR local engine capable of reading scanned maintenance logs and diagrams directly from images.*  
> 
> *Everything runs on standard commodity enterprise hardware (Intel i7/Xeon or RTX workstation) with zero licensing costs or ongoing cloud tokens."*

---

### 04:30 – 05:00: Summary & Conclusion

**Presenter says:**
> *"In summary, Sovereign AI Workbench provides MRPL with:*  
> - *100% Data Sovereignty & Zero Telemetry.*  
> - *Grounded RAG with anti-hallucination guardrails.*  
> - *Autonomous multi-step agentic workflows.*  
> - *Safe code execution sandbox.*  
> - *Production-ready export to PDF, DOCX, and XLSX.*  
> 
> *Thank you, we are now ready for your questions!"*

---

## 🛠️ Backup Demo Commands (CLI / Fallbacks)

If the UI ever needs a direct API demo during questioning:
```powershell
# 1. Check Air-Gap Network Status
curl http://127.0.0.1:8000/network-status

# 2. Run Test Suite (All 12 Tests Passing)
python -m pytest tests/ -v

# 3. Direct Agent Call
python -c "import json, urllib.request; req = urllib.request.Request('http://127.0.0.1:8000/agent', data=json.dumps({'prompt':'Search knowledge base for pump SOP'}).encode('utf-8'), headers={'Content-Type':'application/json'}); print(urllib.request.urlopen(req).read().decode())"
```
