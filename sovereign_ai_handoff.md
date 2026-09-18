# Sovereign AI Workbench --- Handoff / Continuation File

## Purpose

This file is a continuation brief for a new ChatGPT conversation.

The project is an MVP for SIH Problem Statement SIH26117 / PS 26117:

**Sovereign On-Premise Agentic AI Workbench using Open-Weight Multimodal
LLMs for Confidential Industrial Work**

Organization: Mangalore Refinery and Petrochemicals Limited (MRPL)
Category: Software Theme: Smart Automation

The goal is a self-hosted, local/air-gapped AI workbench for
confidential industrial knowledge work. Nothing should leave the
machine/network. The final system should support multiple local
open-weight models, local RAG, document/image understanding, coding,
tools, and eventually agentic workflows.

------------------------------------------------------------------------

# USER WORKING STYLE / IMPORTANT INSTRUCTION

The user is learning this from scratch and wants to be
**micro-managed**.

When continuing: - Give ONE step at a time. - Give exact PowerShell
commands. - Tell the user exactly where to run them. - Do not assume
they know Python/FastAPI/Ollama architecture. - After each step, ask
them to show the output/screenshot before moving on. - Follow YAGNI
strictly for the MVP. - Do not dump a huge implementation unless
specifically requested. - Prefer minimal changes to existing working
code. - Explain what a step proves before moving to the next step.

------------------------------------------------------------------------

# CURRENT PROJECT LOCATION

Windows machine.

Project path:

D:`\isha`{=tex}`\sovereign`{=tex}-ai

Python version:

3.14.6

Virtual environment:

.venv

The user has successfully created and activated the virtual environment.

Typical prompt:

(.venv) PS D:`\isha`{=tex}`\sovereign`{=tex}-ai\>

------------------------------------------------------------------------

# CURRENT OLLAMA MODELS

The user has these local Ollama models:

-   qwen3.5:4b
-   qwen2.5-coder:7b
-   nomic-embed-text:latest
-   glm-ocr:q8_0

There are also older/cloud-tagged models visible in Ollama, but they are
not part of the core MVP architecture.

Core roles:

qwen3.5:4b - General local AI - Reasoning - Multimodal/image
understanding - Main RAG answer-generation model

qwen2.5-coder:7b - Coding tasks - Local code generation

nomic-embed-text - Embeddings - Local knowledge-base retrieval

glm-ocr:q8_0 - OCR / document image text extraction - Recently installed
and successfully tested

------------------------------------------------------------------------

# IMPORTANT MODEL DECISION

We decided NOT to add another vision model because qwen3.5:4b already
has vision capability.

We added glm-ocr:q8_0 specifically because it is useful for OCR/document
extraction.

Desired model specialization:

GENERAL: qwen3.5:4b

CODING: qwen2.5-coder:7b

EMBEDDINGS: nomic-embed-text

OCR: glm-ocr:q8_0

Do not replace these without a concrete reason.

------------------------------------------------------------------------

# CURRENT ARCHITECTURE

The MVP currently works approximately like this:

                    Sovereign AI Workbench
                              |
                +-------------+-------------+
                |             |             |
             General       Coding       Knowledge
                |             |             |
          qwen3.5:4b    qwen2.5-coder   Local RAG
                                           |
                                   nomic-embed-text
                                           |
                                      Local KB
                                           |
                                      qwen3.5:4b

Knowledge mode is controlled by a frontend toggle.

------------------------------------------------------------------------

# CURRENT FRONTEND

The frontend is working.

It has: - Sovereign AI Workbench title - Local AI system status - Prompt
textarea - Send button - Upload Document button - Knowledge ON/OFF
toggle - Model label - Answer display - Sources display when Knowledge
is ON

The UI is dark themed and already visually suitable for the MVP.

Do NOT redesign it unless specifically requested.

------------------------------------------------------------------------

# KNOWLEDGE TOGGLE BEHAVIOR

This has been implemented and tested.

## Knowledge OFF

Example:

"What is a refinery?"

Expected/observed: - qwen3.5:4b - "General Local AI" - no KB retrieval -
no Sources section

This test passed.

## Knowledge ON

Example:

"What should be checked during pump inspection?"

Expected/observed: - qwen3.5:4b - "Knowledge Grounded" - answer based on
local knowledge base - Sources shown with similarity scores

This test passed.

------------------------------------------------------------------------

# ANTI-HALLUCINATION / KNOWLEDGE TEST

Knowledge ON:

Question:

"What is the refinery emergency shutdown procedure?"

The local KB did not contain this information.

The system correctly returned:

"That information is not available in the knowledge base."

It did NOT invent a procedure.

This test passed.

Important architecture principle:

Knowledge ON should mean grounded answering from the organization's
local KB, not unrestricted model answering.

There is currently a minor possible UI improvement: - If retrieval
scores are too low, Sources could eventually be hidden or marked as weak
matches. - Do NOT implement this unless needed; current MVP behavior is
acceptable.

------------------------------------------------------------------------

# DOCUMENT UPLOAD / RAG

The user has successfully uploaded:

Panchal Isha Resume.pdf

It was added to the knowledge base and chunked.

A query:

"What projects are mentioned in the uploaded resume?"

returned the correct projects:

1.  CarDekho Price Prediction
2.  Brain Tumor Detection & Classification

The source showed:

Panchal Isha Resume.pdf

This proves:

PDF → extraction → chunking → embeddings → local KB → retrieval →
qwen3.5:4b → grounded answer

This test passed.

------------------------------------------------------------------------

# EXISTING TEST KB

There is also:

data`\knowledge`{=tex}\_base`\test`{=tex}\_sop.txt

It contains pump inspection information.

Queries about pump inspection successfully retrieve it.

Example answer included: - Pump vibration under normal operating
conditions - Unusual or abnormal sounds - Visible leakage from pump and
connected piping - Bearing temperature - Adequacy of lubrication

------------------------------------------------------------------------

# INDEX

The local KB index has been created successfully.

Command used:

python index.py

Result:

Index created successfully! Saved to: data`\kb`{=tex}\_index.json

The directory contains:

data\
knowledge_base\
test_sop.txt Panchal Isha Resume.pdf kb_index.json

Important: Normally, if documents have not changed, rag_test.py can use
the existing index.

If a document is added/changed and the project architecture requires
re-indexing, run:

python index.py

Then test RAG.

Do not blindly rebuild the index before every RAG query.

------------------------------------------------------------------------

# RAG TEST

The existing RAG test script works.

Command:

python rag_test.py

Example:

Ask your knowledge base: What should be checked during pump inspection?

It produced a grounded answer and showed retrieved sources.

The RAG system is working.

------------------------------------------------------------------------

# FASTAPI

The FastAPI backend is working.

The root/local server has been tested at:

http://127.0.0.1:8000

The browser showed:

{"status":"online","message":"Sovereign AI Workbench is running"}

Swagger docs are available at:

http://127.0.0.1:8000/docs

The API has included: GET / POST /chat

There may also be an ask endpoint depending on the current version of
main.py.

IMPORTANT: Before changing backend behavior, inspect the current code
rather than assuming endpoint names.

------------------------------------------------------------------------

# CURRENT PROJECT FILES

Visible project structure included:

.venv\
data\
knowledge_base\
Panchal Isha Resume.pdf test_sop.txt kb_index.json frontend\
index.html index.py kb_search.py main.py rag_test.py test_embed.py
test_kb.py test_ocr.py

There may be additional files not shown here.

Do not delete or rewrite working files unnecessarily.

------------------------------------------------------------------------

# OCR TEST --- PASSED

A new test script was created:

test_ocr.py

The script uses the Ollama Python API with:

model="glm-ocr:q8_0"

and sends an image through the `images` field.

Example:

response = ollama.chat( model="glm-ocr:q8_0", messages=\[ { "role":
"user", "content": "Extract all visible text from this image. Preserve
the structure as much as possible.", "images": \[image_path\], } \], )

The user tested:

D:`\isha`{=tex}`\sovereign`{=tex}-ai`\image`{=tex}.png

GLM-OCR successfully extracted the visible text.

The test image contained a study-planner page beginning:

DAY 3: KNOWLEDGE REP - PART 1 (14 marks LOCKED)

It successfully extracted headings, bullets, and text.

Therefore:

IMAGE → glm-ocr:q8_0 → TEXT

is proven to work locally.

The model sometimes returned an extra Markdown code fence / duplicated
Markdown representation after the OCR text. This is not a blocker. If
integrating, only remove accidental OUTER code fences if they wrap the
complete OCR result; do not aggressively alter OCR text.

------------------------------------------------------------------------

# IMMEDIATE NEXT STEP

The next task is:

## STEP 39 --- Integrate GLM-OCR into the existing upload pipeline

Goal:

Allow the existing Upload Document button to accept images:

.png .jpg .jpeg .webp

Pipeline:

IMAGE ↓ glm-ocr:q8_0 ↓ Extracted text ↓ EXISTING chunking ↓
nomic-embed-text ↓ EXISTING KB/index ↓ Knowledge ON ↓ qwen3.5:4b ↓
Grounded answer + source

Do NOT create: - a second vector database - a second embedding system -
a second RAG implementation - a separate image KB

The OCR-generated text must enter the SAME existing knowledge base.

------------------------------------------------------------------------

# EXACT INTEGRATION REQUIREMENTS

When image is uploaded:

1.  Save it using the existing upload/storage mechanism.
2.  Send the image to local Ollama: glm-ocr:q8_0
3.  Extract OCR text.
4.  Clean only accidental outer Markdown fences if necessary.
5.  Pass OCR text to the existing chunking/indexing code.
6.  Use existing nomic-embed-text embedding code.
7.  Add chunks to existing kb_index.json/index.
8.  Preserve original image filename as source.
9.  Return a success message showing image processed and number of
    chunks.
10. If OCR fails, do not add empty data and return a useful error.

Frontend: Only update the existing file input accept attribute if
needed:

accept=".pdf,.txt,.md,.png,.jpg,.jpeg,.webp"

Do not redesign the UI.

------------------------------------------------------------------------

# NEXT TEST AFTER INTEGRATION

Use:

D:`\isha`{=tex}`\sovereign`{=tex}-ai`\image`{=tex}.png

Upload it through the Workbench.

Expected: "image.png processed with GLM-OCR and added to knowledge base.
X chunks created."

Then:

Knowledge ON

Ask:

"What topics are covered in this document?"

Expected: - Knowledge Grounded - answer based on OCR text - image.png
appears as a source

Then test:

Knowledge OFF

Ask:

"What is a refinery?"

Expected: - General Local AI - qwen3.5:4b - no KB retrieval - no Sources

------------------------------------------------------------------------

# DO NOT IMPLEMENT YET

Future features, but NOT current MVP step:

-   scanned PDF page-by-page OCR
-   handwritten-specialized OCR
-   engineering drawing analysis
-   image RAG
-   multimodal agent
-   automatic model selection
-   OCR model switching
-   document classification
-   multi-agent system
-   tool execution
-   Word/PPT/Excel deliverable generation
-   sandboxed coding execution
-   visible network monitor
-   full agentic planning

Build these only after the simpler MVP path is proven.

------------------------------------------------------------------------

# YAGNI ROADMAP

Recommended order:

1.  General AI --- DONE
2.  Coding model --- DONE
3.  Local embeddings --- DONE
4.  Local KB indexing --- DONE
5.  RAG retrieval --- DONE
6.  Grounded RAG answer --- DONE
7.  Knowledge ON/OFF --- DONE
8.  PDF upload/RAG --- DONE
9.  GLM-OCR direct test --- DONE
10. Image → GLM-OCR → existing KB --- NEXT
11. Test multimodal/visual understanding --- AFTER OCR integration
12. Coding sandbox --- LATER
13. Real file deliverables --- LATER
14. Model auto-selection/router --- LATER
15. Agentic multi-step workflow --- LATER
16. Network isolation/visible proof --- LATER
17. Full SIH demo polish --- FINAL

------------------------------------------------------------------------

# SIH DEMO TARGET

The final MVP demo should eventually show a flow like:

User uploads scanned inspection report ↓ Local OCR ↓ Local knowledge
base ↓ Local RAG ↓ Local reasoning model ↓ Approval note / report ↓ No
external calls

And separately:

User gives coding task ↓ Local coding model ↓ Sandbox
execution/verification ↓ Working result

And:

User asks general question with Knowledge OFF ↓ General local model

The important sovereign claim is:

Everything remains on-premise/local.

------------------------------------------------------------------------

# IMPORTANT COMMANDS

Activate environment if needed:

..venv`\Scripts`{=tex}`\Activate`{=tex}.ps1

Run API (exact command depends on current main.py setup; inspect if
unsure):

uvicorn main:app --reload

Test root:

Open: http://127.0.0.1:8000

Swagger:

http://127.0.0.1:8000/docs

List Ollama models:

ollama list

Check currently running models:

ollama ps

Run Qwen general:

ollama run qwen3.5:4b --think=false

Run coding model:

ollama run qwen2.5-coder:7b --think=false

Run OCR model:

ollama run glm-ocr:q8_0

Build/rebuild KB index:

python index.py

Search KB:

python kb_search.py

Test RAG:

python rag_test.py

Test OCR:

python test_ocr.py

------------------------------------------------------------------------

# THINKING SETTING

The user chose to use:

qwen3.5:4b with thinking OFF

for the initial MVP general/RAG experience because it is faster and more
practical.

Coding model was also tested with:

qwen2.5-coder:7b --think=false

A simple coding request worked, but the 7B coder was running on CPU and
can be relatively slow.

Observed example: qwen2.5-coder:7b 100% CPU context 32768

A simple coding generation took around several seconds in direct CLI
testing, while more complex answers can take longer.

Do not optimize this prematurely.

------------------------------------------------------------------------

# ARCHITECTURAL PRINCIPLE

The project should eventually have a model router, but NOT yet.

Future concept:

User task ↓ Task classification ↓ Choose local specialist: General →
qwen3.5:4b Coding → qwen2.5-coder:7b OCR → glm-ocr:q8_0 Retrieval →
nomic-embed-text ↓ Local execution

But for the current MVP, explicit Knowledge ON/OFF and simple task paths
are preferable to a complicated automatic router.

------------------------------------------------------------------------

# WHAT THE CURRENT MVP HAS PROVEN

The following are already demonstrated successfully:

\[✓\] Local Ollama \[✓\] General local model \[✓\] Local coding model
\[✓\] Local embeddings \[✓\] Local vector index \[✓\] RAG retrieval
\[✓\] Grounded answer \[✓\] Knowledge ON/OFF \[✓\] No-answer behavior
for missing KB information \[✓\] PDF upload \[✓\] Uploaded PDF → KB →
RAG \[✓\] GLM-OCR local image extraction \[ \] Image upload → OCR →
existing KB ← NEXT \[ \] Scanned PDF OCR \[ \] Coding sandbox \[ \]
Deliverable generation \[ \] Agentic workflow \[ \] Automatic model
routing \[ \] Network isolation proof \[ \] Final SIH presentation/demo

------------------------------------------------------------------------

# HANDOFF INSTRUCTION TO NEXT CHAT

Start from:

"STEP 39 --- Integrate GLM-OCR into the existing upload pipeline."

Do NOT restart the project from scratch.

Do NOT ask the user to reinstall Python, Ollama, FastAPI, Qwen,
embeddings, or GLM-OCR.

Do NOT recreate the RAG system.

Do NOT assume code that is not shown.

First inspect the current relevant code if needed, especially: -
main.py - index.py - any upload/indexing helper - frontend/index.html

Then make the smallest change necessary.

The user wants micro-management: give one action, wait for result, then
continue.
