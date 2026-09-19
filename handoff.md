# Sovereign AI Workbench — handoff.md

> Consolidated continuation brief. Generated 2026-09-18 after reading all repo files.
> Replaces/supersedes `sovereign_ai_handoff.md` (which was stale — pre-OCR-integration, pre-sessions, pre-sandbox).

---

## 1. Purpose / Project identity

- **SIH Problem Statement:** SIH26117 / PS 26117
- **Title:** Sovereign On-Premise Agentic AI Workbench using Open-Weight Multimodal LLMs for Confidential Industrial Work
- **Organization:** Mangalore Refinery and Petrochemicals Limited (MRPL)
- **Category:** Software · **Theme:** Smart Automation
- **Goal:** Fully local, air-gapped AI workbench for confidential industrial work. Nothing leaves the machine. Upload docs/images → local RAG → grounded answers, local code gen + sandbox, dynamic report generation (.pdf, .docx, .xlsx), eventually agentic workflows.
- **Sovereign claim:** No API keys, no telemetry, no external calls. Ollama + FastAPI + pure-Python vector search.
- **GitHub Repository:** `https://github.com/200510rj/Sovereign-AI.git` (Tracked on `main` branch, pushed & clean)

---

## 2. User working style (carry over)

- User is learning from scratch, wants **micro-management**: ONE step at a time, exact PowerShell commands, where to run them, wait for output/screenshot before next step.
- Follow **YAGNI** strictly. Minimal changes to working code.
- Always include **TDD test verification steps** after each implementation phase.

- Explain what a step proves before moving on.
- Do NOT restart from scratch. Do NOT ask to reinstall Python/Ollama/models unless broken.

---

## 3. Environment

- **Machine:** Windows
- **Path:** `D:\isha\sovereign-ai`
- **Python:** 3.14.6
- **Venv:** `.venv` (prompt: `(.venv) PS D:\isha\sovereign-ai>`)
- **Backend run:** `uvicorn main:app --reload` → `http://127.0.0.1:8000` (UI), `http://127.0.0.1:8000/docs` (Swagger)
- **Ollama:** must be running locally (`ollama list`, `ollama ps`)

### Models (do NOT replace without concrete reason)

| Model | Role |
|---|---|
| `qwen3.5:4b` | General chat, RAG answering, reasoning. Has built-in vision. Run with thinking OFF for speed. |
| `qwen2.5-coder:7b` | Code generation/debugging (CPU, can be slow — expected). |
| `nomic-embed-text:latest` | Embeddings for KB + queries. |
| `glm-ocr:q8_0` | OCR text extraction from images. |

Pull: `ollama pull qwen3.5:4b`, `ollama pull qwen2.5-coder:7b`, `ollama pull nomic-embed-text`, `ollama pull glm-ocr:q8_0`
Interactive: `ollama run qwen3.5:4b --think=false`, `ollama run qwen2.5-coder:7b --think=false`, `ollama run glm-ocr:q8_0`

---

## 4. Repo map (actual, 2026-09-18)

```
sovereign-ai/
├── main.py                    # FastAPI backend — 1010 lines, all logic (router, RAG, OCR, upload, sessions, sandbox)
├── kb_index.py                # Bulk index data/knowledge_base/*.txt -> data/kb_index.json (TXT-only, legacy chunker)
├── kb_search.py               # CLI semantic search (top_k=3, no min_score)
├── rag_test.py                # E2E RAG test: search top-5 + qwen3.5:4b grounded answer
├── test_embed.py              # Embedding sanity check
├── test_kb.py                 # Dumps data/knowledge_base text files to console
├── test_ocr.py                # Manual OCR test: prompts image path, calls glm-ocr:q8_0 via ollama lib
├── tests/test_previous_phases.py  # pytest: /documents, /sessions CRUD, /execute_code valid+syntax-error
├── frontend/index.html        # Full SPA, 1260 lines, dark theme (see §6)
├── data/
│   ├── knowledge_base/        # test_sop.txt, Panchal Isha Resume.pdf, book (4).pdf, _Secrets...pdf_.pdf, image.png
│   ├── kb_index.json          # Vector index (~4.6 MB at handoff time)
│   └── sovereign.db           # SQLite: sessions, messages, documents (~28 KB)
├── day1_documentation/
│   ├── md/00-09_*.md          # Day-1 Task-1 set (master summary → tech stack)
│   ├── pdf/00-09_*.pdf, docx/00-09_*.docx
│   ├── convert_md_to_pdf.py, convert_md_to_docx.py
├── day1_documentation.zip + Day 1 Task 1.pdf (source brief)
├── ppt/                       # SIH decks: finalSIH 2026 (1).pptx, SIH2026_KAVACH_Visual_Master.{pptx,pdf},
│                              # SIH26117_KAVACH (1).pptx, SIH_PPT_DEMO_1/2 pdfs, SIH2026 PPT Format.pptx (template),
│                              # build_visual_master.py, render_diagrams.py, diagrams/*.html,
│                              # rendered_diagrams/*.png, master_slide_screenshots/*.png, renders/*.mp4|*.m4a
├── videos/sovereign-ai-demo/  # HyperFrames 60s silent showcase: BRIEF.md, index.html, assets/, frames/, renders/
├── sih_prescreening_compliance_diagram.html
├── README.md                  # Full setup/API/roadmap doc (434 lines, accurate)
├── sovereign_ai_handoff.md + sovereign_ai_handoff (1).md  # OLD handoffs, stale (STEP-39 era)
├── image.png                  # OCR test image (study-planner, "DAY 3: KNOWLEDGE REP...")
└── firstmate/ (unrelated supervisor template: VISION.md, .tasks.toml)
```

> Note: `kb_index.py` only handles UTF-8 text files and will crash on PDFs/images in the folder — real uploads go through `main.py:extract_text/ocr_image/index_document`, not this script. Don't "fix" it unless asked.

---

## 5. Backend — `main.py` (source of truth)

### Config

- `INDEX_PATH=data/kb_index.json`, `KB_PATH=data/knowledge_base`, `DB_PATH=data/sovereign.db`
- `GENERAL_MODEL=qwen3.5:4b`, `CODING_MODEL=qwen2.5-coder:7b`, `EMBED_MODEL=nomic-embed-text:latest`, OCR hardcoded `glm-ocr:q8_0`

### Key functions

- `select_route(prompt)` — keyword router: `coding_phrases` (write code, implement, debug/fix code, python/javascript/sql/html/css code…) → `coding`; else `document_phrases` (uploaded, document, pdf, sop, manual, resume, report, knowledge base, according to, inspection…) → `rag` (only used to pick coding vs non-coding; knowledge ON/OFF decides RAG vs general after that); else `general`.
- `get_embedding` — `POST http://127.0.0.1:11434/api/embed` via urllib, timeout 120s.
- `cosine_similarity`, `load_index`, `search_knowledge(query, top_k=5, min_score=0.20)` — filters below 0.20, returns id/source/text/score.
- `ask_ollama` (generate API, num_predict 256, think False) / `ask_ollama_chat` (chat API, num_predict 512, history-aware).
- `clean_ocr_text` — strips only outer wrapping ```` ``` ```` fences; `ocr_image` — `ollama.chat(glm-ocr:q8_0, images=[path])`, returns None on empty/exception.
- `extract_text` — `.txt/.md` direct read; `.pdf` via pypdf; else ValueError.
- `chunk_text(max_chars=1800)` — paragraph packing; `index_document` — embed each chunk, append to `kb_index.json`, return count.

### Endpoints (all verified in code + frontend + tests)

| Method | Path | Notes |
|---|---|---|
| `GET /` | serves `frontend/index.html` |
| `GET /documents` | derives chunk counts from index, lists files in `KB_PATH` with name/size_bytes/chunks/extension |
| `GET /sessions` | list sessions DESC |
| `GET /sessions/{id}/messages` | ordered messages |
| `DELETE /sessions/{id}` | deletes messages + session |
| `POST /upload` | form `file`: `.pdf/.txt/.md/.png/.jpg/.jpeg/.webp`; saves to KB_PATH; images→OCR→index, docs→extract→index; returns `{success, file, chunks, message}` |
| `POST /chat` | body `{prompt\|message, knowledge_enabled, session_id?, history:[{role,content}]}`; saves user+assistant msgs (auto-creates session titled from first 32 chars); coding→CODING_MODEL+history; knowledge ON→top-5 search + strict grounded system prompt + sources `[{id,file,score,snippet}]`; else general. Returns `{session_id, model, route, knowledge_enabled, answer, sources}` |
| `POST /execute_code` | body `{code, timeout=10}`; runs in temp `.py` via `sys.executable`, capture output; returns `{success, stdout, stderr, exit_code}`; timeout→success False |
| `POST /generate_report` | body `{title, content, format: "pdf"\|"docx"\|"xlsx", author}`; generates styled PDF (ReportLab), Word doc (python-docx), or Excel spreadsheet (openpyxl) in `data/reports/`; returns `{success, filename, format, download_url}` |
| `GET /download_report/{filename}` | serves generated report file as downloadable octet-stream attachment |

### DB schema (SQLite, `init_db` on import)

- `sessions(session_id PK, title, created_at)`, `messages(id PK, session_id FK, role, content, route, model, timestamp)`, `documents(...)` table exists but **unused** — doc listing comes from filesystem+index, not this table.

### Proven behaviors

- Knowledge OFF + "What is a refinery?" → general, no sources. Knowledge ON + pump question → grounded from `test_sop.txt` with scores. Knowledge ON + missing info ("emergency shutdown procedure") → "That information is not available in the knowledge base." (anti-hallucination system prompt).
- PDF upload (`Panchal Isha Resume.pdf`) → chunked → "What projects are mentioned?" → CarDekho Price Prediction + Brain Tumor Detection, source cited.
- Image upload → `image.png processed with GLM-OCR…` (STEP-39 goal from old handoff is **DONE** — OCR integration exists in `/upload`).
- Python code generated in chat automatically gets **▶ Run Code** button → `/execute_code` execution in sandbox → live terminal output displayed in console box.
- Assistant responses feature instant **📥 PDF**, **📄 DOCX**, **📊 XLSX** export buttons generating styled downloadable deliverables on-demand.

---

## 6. Frontend — `frontend/index.html`

- Layout: left sidebar (brand, New Conversation, Recent Conversations `#sessionList`, KB Documents `#kbList`, Active Model Routing card, Air-Gapped badge) + main (navbar with Knowledge pill, chat feed, input dock).
- Knowledge pill toggles `knowledgeEnabled` (default OFF). Upload input `accept=".pdf,.txt,.md,.png,.jpg,.jpeg,.webp"`. Suggestions auto-enable knowledge for document queries.
- Chat: `POST /chat` with `{prompt, knowledge_enabled, session_id, history}`; loading bubble; markdown render via `marked`, highlight via `hljs` (CDN, needs net — breaks offline/air-gap claim for full styling, content still works).
- Route badges: `coding`/`rag`/`general`; sources accordion with score + click → chunk modal (`#chunkModal` shows file/score/snippet).
- Code blocks get auto-attached **▶ Run Code** button → `POST /execute_code` → inline console box (green stdout / red stderr).
- Assistant messages get instant **📥 PDF**, **📄 DOCX**, **📊 XLSX** export buttons → `POST /generate_report` → automatic file download.
- Sessions persisted via `/sessions` APIs; `clearChat` resets local state (does NOT delete server session — `DELETE /sessions/{id}` exists but no UI delete button).

---

## 7. KB / data state at handoff

- `data/knowledge_base/`: `test_sop.txt` (SOP-PUMP-001, 7 inspection points — canonical test doc), `Panchal Isha Resume.pdf`, `book (4).pdf`, `_Secrets of the Millionaire Mind….pdf_.pdf`, `image.png`.
- `data/kb_index.json` ~4.6 MB (embeddings for above).
- `data/sovereign.db` has sessions/messages from testing.
- `data/reports/`: generated `.pdf`, `.docx`, `.xlsx` deliverables.
- Root `image.png` = OCR test image (study planner "DAY 3: KNOWLEDGE REP - PART 1").

---

## 8. Tests & scripts (TDD Suite)

- `python test_embed.py` — embedding smoke test.
- `python test_kb.py` — cat KB text files (PDFs will break it — text-only).
- `python test_ocr.py` — prompts `Enter image path:`, prints OCR result.
- `python kb_search.py` — prompts query, top-3, prints score/source/text.
- `python rag_test.py` — prompts query, top-5 + grounded answer + sources.
- `pytest tests/test_previous_phases.py` — covers `/documents`, full session CRUD, `/execute_code` valid + syntax-error.
- `pytest tests/test_report_generator.py` — covers PDF, DOCX, XLSX generation + file download endpoints + invalid format rejection.
- Full suite: `pytest tests/` (7 passed in ~1m45s).

---

## 9. Docs / PPT / video inventory

- **Day-1 docs** (`day1_documentation/md/00–09`): 00 master summary (+mentor alignment matrix), 01 problem understanding (MRPL pain/air-gap), 02 proposed solution (5 pillars, workflow matrix), 03 features (OCR pipeline, cosine RAG), 04 target users (engineers/safety/IT/execs), 05 architecture (4-tier), 06 workflow/user-flow (sequence diagrams), 07 DFD L0/L1/L2, 08 modules (UI gateway, FastAPI router, vector engine, model runtime), 09 tech stack (model matrix, i7/16GB min → Xeon/32-64GB+RTX4090 prod, latency table). Mirrored to `pdf/` + `docx/`.
- **PPT** (`ppt/`): working deck = `finalSIH 2026 (1).pptx` + `SIH2026_KAVACH_Visual_Master.{pptx,pdf}` (built by `build_visual_master.py` from `SIH2026 PPT Format.pptx` template); `render_diagrams.py` → `rendered_diagrams/slide{2,3,5}_*_hd.png` from `diagrams/*.html`; `master_slide_screenshots/` captures; `renders/` has demo videos + narration audio.
- **Video** (`videos/sovereign-ai-demo/`): 60s **silent** showcase for judges (`BRIEF.md`: title→problem→stack→proof1 grounded answer→proof2 OCR pipeline + not-in-KB→close; presenter narrates live). HyperFrames `index.html` + GSAP vendored, `assets/sov-{hero,asked,answered}.png`, `renders/video*.mp4`.
- `sih_prescreening_compliance_diagram.html` — standalone compliance diagram.
- `README.md` — accurate setup/API/roadmap; milestones 1–15 done, 16+ planned.

---

## 10. Milestones (actual)

| # | Item | Status |
|---|---|---|
| 1–6 | Ollama, qwen3.5:4b, qwen2.5-coder:7b, nomic-embed-text, vector index, RAG retrieval | ✅ Done |
| 7–9 | Grounded answers, Knowledge toggle, anti-hallucination | ✅ Done |
| 10–12 | PDF upload→KB→RAG, GLM-OCR test, image upload→OCR→same KB | ✅ Done |
| 13–14 | Dark chat UI upgrade, Multi-turn context & SQLite session persistence | ✅ Done |
| 15 | Local Python Code Sandbox (`/execute_code`) & Run Code buttons | ✅ Done |
| 16 | Automatic Document Generation Engine (`.pdf`, `.docx`, `.xlsx`) | ✅ Done |
| 17 | Stage 4 Dynamic Agentic Tool Routing (Search KB -> Run Code -> Export Report) | 🔜 Next (Phase 7) |
| 18 | Multi-Step End-to-End Agentic Demo Workflow (Upload -> OCR -> RAG -> Reason -> Export) | 🔜 Phase 8 |
| 19 | Network Isolation / Air-Gap Proof Mode (Zero external calls badge) | 🔜 Phase 9 |
| 20 | Final SIH Demo Polish & Presentation Package | 🔜 Phase 10 |

---

## 11. Roadmap / suggested next steps (pick one, YAGNI order)

1. **Harden what exists:** cap `/execute_code` (timeout already; add import/network restrictions), wire UI delete-session, offline fallback for marked/hljs CDN (air-gap story), hide/flag weak sources when all scores < threshold.
2. **Scanned-PDF OCR:** page-render → per-page `ocr_image` → index (currently only digital-text PDFs work).
3. **Stage 4 agent layer:** Needle 2 orchestrator + 4 starter tools, keep everything local.
4. **Deliverables:** `.docx/.xlsx` generation from grounded answers.
5. **Demo polish:** air-gap proof (network-off run), final SIH flow: scanned inspection report → OCR → RAG → reasoning → approval note.

SIH demo target flow stays: upload scanned report → GLM-OCR → KB → RAG → qwen3.5:4b → approval note/report, zero external calls; plus coding task → coder model → sandbox; plus Knowledge OFF general chat.

---

## 12. Commands

```powershell
.venv\Scripts\Activate.ps1
uvicorn main:app --reload
ollama list
ollama ps
ollama run qwen3.5:4b --think=false
ollama run qwen2.5-coder:7b --think=false
ollama run glm-ocr:q8_0
python kb_index.py        # only for text files; NOT needed before every query
python kb_search.py
python rag_test.py
python test_embed.py
python test_kb.py
python test_ocr.py
pytest tests/test_previous_phases.py
```

---

## 13. Principles / gotchas for next agent

- Same KB for everything: OCR text goes through existing chunk→embed→`kb_index.json`; no second DB/vector store/RAG.
- `knowledge_enabled` ON = grounded-only system prompt; missing info → "not available in the knowledge base", never invent (safety-critical).
- Thinking OFF for qwen models (speed); coder 7B on CPU is slow — expected, don't prematurely optimize.
- `documents` DB table is dead code; don't rely on it.
- `marked`/`highlight.js`/Google Fonts are CDN — offline UI still functions, styling/highlight degrades; fix only if air-gap demo demands it.
- First inspect `main.py` + `frontend/index.html` before changing behavior; smallest diff wins.
- `firstmate/` is an unrelated supervisor template — ignore for SIH work.

---

## 14. Resume instruction

Pick up from §11 (harden → scanned-PDF OCR → Needle 2). Verify with: upload `image.png` → chunks message → Knowledge ON question → grounded answer citing `image.png`; Knowledge OFF → general, no sources; `pytest tests/test_previous_phases.py`.
