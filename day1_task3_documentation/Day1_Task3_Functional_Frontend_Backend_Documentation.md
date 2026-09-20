# Day 1 Task 3 — Functional Frontend & Backend Development
**Sovereign AI Workbench · SIH 2026 (PS 26117) · MRPL · 18 September 2026**

> Objective: overall completion of Frontend Development + core application and server-side logic (screens, REST APIs, auth position, business logic, validation, errors, FE-BE communication), with 15+ pages of evidence.
> Run: `python -m uvicorn main:app --host 127.0.0.1 --port 8000` → app `/`, APIs `/docs`. Rebuild: `python day1_task3_documentation/build_task3_docs.py`. Tests: `pytest tests/` → **7 passed**.

## 1. Scope mapping
| Requirement | Implementation | Evidence |
|---|---|---|
| Major screens | Sidebar, navbar+KB pill, feed, dock, chunk modal, toasts | §4 + ss_01–ss_04 |
| REST APIs | 10 FastAPI JSON endpoints, zero external calls | §6 + ss_06 |
| Auth | Single-user air-gapped model (JWT/RBAC = Day-2) | §7 |
| Business logic | Router, RAG, chunk/embed, sandbox, reports, sessions | §8 |
| Validation | Allow-list, guards, Pydantic, format check | §9 + ss_05 |
| Errors | Envelopes, toasts, Ollama guard, stderr capture | §10 |
| FE-BE link | `fetch()` per action | §5 |
| Responsive | 1920/1366/768/375 captures | §11 + ss_07–ss_09 |

## 2. Architecture
`SPA (frontend/index.html) → FastAPI main.py:8000 → Ollama (qwen3.5:4b, qwen2.5-coder:7b, nomic-embed-text, glm-ocr:q8_0) + kb_index.json + sovereign.db + sandbox/reports`. Tiers: presentation / gateway / RAG-store / models / deliverables.

## 3. Project structure (UI components, pages, services, utilities)
- `main.py` (1156 lines), `frontend/index.html` (1293 lines), `data/knowledge_base/`, `data/kb_index.json` (4.65 MB), `data/sovereign.db`, `data/reports/`, `tests/` (7 tests), `day1_task3_documentation/` (this pack + 9 PNGs).
- Pages: `GET /` SPA · `GET /docs` Swagger · `GET /openapi.json` schema.
- UI: sidebar (`#sessionList,#kbList`), navbar (`#knowledgePill`), feed (route badges + sources), `#emptyState`, dock (`#promptInput,#sendBtn,#fileInput,#statusToast`), `#chunkModal`, per-block Run-Code console, `exportReport(btn,fmt)`.
- FE services → endpoints: `sendMessage→POST /chat`, `uploadFile→POST /upload`, `loadDocuments→GET /documents`, sessions GETs, Run-Code→`POST /execute_code`, `exportReport→POST /generate_report→GET /download_report/{f}`.
- BE regions: config+DB (~24–128), router (~151–223), embeddings/search (~230–344), LLM clients (~352–431), OCR/extract/chunk (~440–629), sessions API (~673–686), sandbox (~694–743), reports (~750–882), upload+chat (~889–1149).
- Utilities: `escapeHtml`, `showToast`, `clean_ocr_text`, `chunk_text(1800)`, `cosine_similarity`; CDN Marked/Highlight with offline fallback.

## 4. Major screens (complete)
Shell + RAG transcript + sandbox console + chunk modal + toasts + Swagger + responsive layouts — see `screenshots/ss_01–ss_04`.

## 5. Frontend-backend communication
Same-origin HTTP/JSON `fetch()`; chat posts `{prompt, knowledge_enabled, session_id, history}` → `{answer, route, model, sources[], session_id}`; uploads multipart; reports resolve via `download_url`.

### 5A. Step sequences
RAG ask: bubble + history snapshot → loading pulse → `POST /chat` (embed → cosine → grounded LLM) → sources accordion + sidebar refresh → modal on click. Coding: router → coder model → highlighted block + Run-Code. Upload: toast → multipart ingest → chunk badge refresh.

## 6. API documentation (10 endpoints)
`GET /` · `GET /documents` · `POST /upload` · `POST /chat` · `GET /sessions` · `GET /sessions/{id}/messages` · `DELETE /sessions/{id}` · `POST /execute_code` · `POST /generate_report` · `GET /download_report/{filename}` — see Swagger `ss_06_swagger_api_docs.png`. Live: `book (4).pdf` 42 chunks; RAG → `{route:rag, model:qwen3.5:4b, sources:[{score:0.8924}]}`; sandbox `TDD Hello World` → `success:true`.

### 6A. Endpoint detail cards
E1 `GET /` shell · E2 `GET /documents` KB+chunks · E3 `POST /upload` ingest/OCR · E4 `POST /chat` router · E5 `GET /sessions` · E6 transcript · E7 delete (idempotent) · E8 sandbox `{stdout,stderr,exit_code}` · E9 report PDF/DOCX/XLSX · E10 download stream. Full per-card requests/responses in DOCX §6A.

## 7. Authentication & authorization (honest status)
Multi-user auth NOT implemented — single-user air-gapped workstation (localhost + OS session = boundary, UUID session isolation). Day-2: JWT login, roles + ownership checks, TLS, containerized sandbox. Safe to ship single-user; gate LAN exposure until auth lands.

## 8. Business logic
Router keyword dispatch → coding/RAG/general; RAG cosine top-5 (min 0.20) + extractive fallback sentence; ingestion txt/md/PDF(pypdf)/images(glm-ocr); 1800-char chunks; sandbox temp+subprocess+timeout+cleanup; reports PDF/DOCX/XLSX timestamped; sessions auto-titled (32 chars) with route/model persisted.

## 9. Validation (V1–V7)
Allow-list `Only PDF, TXT, MD, PNG, JPG, JPEG, and WEBP files are supported.` · empty-text `No readable text was found.` / `GLM-OCR failed…` · empty prompt `Please enter a question.` · bad format `Unsupported format…` · empty code `No code provided.` · title sanitization silent · Pydantic 422. See `ss_05_input_validation_error.png`.

## 10. Error handling
200+`{success:false}` envelopes for domain failures; Ollama-down → persisted ERROR bubble; sandbox stderr inline; timeout message; report `alert()` (toast planned); CDN-offline plaintext fallback. Gap: RAG-embedding outage → 500 (fix planned).

## 11. Responsive UI
1200px + 768px breakpoints; 1920/1366 pass; 768/375 pass with note (sidebar hidden → needs drawer). See `ss_07/08/09`.

### 11A. Per-viewport walkthrough
Desktop: 320px sidebar, 20% gutters, Swagger expanded. Laptop: 10% gutters, no h-scroll. Tablet: sidebar hidden, full-width chat. Mobile: single column, `min(650px,90%)` modal.

## 12. Further-frontend feasibility: HIGH
Drawer+login, drag-drop+progress, reports history (1 endpoint), eval dashboard, streaming (1 SSE endpoint), framework migration — all additive; split `app.js`/`styles.css` first.

## 13. Verification
`pytest tests/ -q` → **7 passed** (documents, session CRUD, sandbox×2, reports×4 incl. invalid format + downloads). Manual 10-min script in DOCX §13 (10-row checklist: KB-ON ask → modal → upload → Run-Code → export → Swagger → responsive → Network same-origin only).

## 14. Mentor review: recommend PASS (auth conditional)
Findings: F1 `closeChunkModal` undefined (Close dead, medium) · F2 duplicate `clearChat` (low) · F3 rejected upload lingers (low) · F4 RAG-embed 500 (medium) · F5 `alert()` + single-user auth (by-design). Sign-off line in DOCX §14.

## 15. Appendix
Paths/sizes: `main.py` 1156 · `index.html` 1293 · 9 PNGs ~1.1 MB · `kb_index.json` ~4.65 MB. Refs: `/openapi.json`, `README.md`, `tests/`, Day-1 Task-1 pack.

### Screenshots index
- `screenshots/ss_01_desktop_workbench.png` — Figure 1
- `screenshots/ss_02_rag_response_sources.png` — Figure 2
- `screenshots/ss_03_code_sandbox_execution.png` — Figure 3
- `screenshots/ss_04_chunk_modal.png` — Figure 4
- `screenshots/ss_05_input_validation_error.png` — Figure 5
- `screenshots/ss_06_swagger_api_docs.png` — Figure 6
- `screenshots/ss_07_responsive_laptop_1366.png` — Figure 7
- `screenshots/ss_08_responsive_tablet_768.png` — Figure 8
- `screenshots/ss_09_responsive_mobile_375.png` — Figure 9
