# Task 1 — Document 06: Workflow & User Flow Diagrams

> **Problem Statement ID:** PS 26117 / SIH26117  
> **Title:** Sovereign On-Premise Agentic AI Workbench using Open-Weight Multimodal LLMs for Confidential Industrial Work  
> **Organization:** Mangalore Refinery and Petrochemicals Limited (MRPL)  
> **Category:** Software | **Theme:** Smart Automation  

---

## 🔀 1. High-Level User Flow Chart

```mermaid
flowchart TD
    Start([User opens Workbench Web UI]) --> ActionChoice{User Action}
    
    %% Document Upload Branch
    ActionChoice -->|Upload File| UploadType{File Format?}
    UploadType -->|.pdf / .txt / .md| PDFProcess[Extract Text via pypdf / File Read]
    UploadType -->|.png / .jpg / .webp| OCRProcess[Send to GLM-OCR via Ollama]
    
    PDFProcess --> Chunking[Chunk Text into 500-char snippets]
    OCRProcess --> Chunking
    Chunking --> Embedding[Generate Vectors via nomic-embed-text]
    Embedding --> UpdateKB[Append to kb_index.json]
    UpdateKB --> NotifySuccess[Show UI Notification: Chunks Indexed]
    
    %% Chat Query Branch
    ActionChoice -->|Enter Prompt| CheckCoding{Coding Keywords Detected?}
    
    CheckCoding -->|Yes| CodeRoute[Route to qwen2.5-coder:7b]
    CodeRoute --> StreamCode[Display Synthesized Code Response]
    
    CheckCoding -->|No| CheckKnowledge{Knowledge Mode ON?}
    
    CheckKnowledge -->|OFF| GeneralRoute[Route to qwen3.5:4b]
    GeneralRoute --> StreamGeneral[Display General AI Answer]
    
    CheckKnowledge -->|ON| RAGRoute[Embed Query via nomic-embed-text]
    RAGRoute --> VectorSearch[Compute Cosine Similarity against kb_index.json]
    VectorSearch --> MatchCheck{Relevant Context Found?}
    
    MatchCheck -->|Yes| GroundedPrompt[Construct Grounded Prompt with Top-5 Chunks]
    GroundedPrompt --> GroundedAnswer[Generate Grounded Answer via qwen3.5:4b]
    GroundedAnswer --> DisplaySources[Render Answer + Source Document Citation Scores]
    
    MatchCheck -->|No| AntiHallucination[Trigger Anti-Hallucination Guardrail]
    AntiHallucination --> DisplayMissing["Display: Information not available in knowledge base"]
```

---

## 🔄 2. Detailed Sequence Diagrams

### Sequence 1: Image Upload & GLM-OCR Ingestion Pipeline

```mermaid
sequenceDiagram
    autonumber
    actor User as Plant Engineer
    participant UI as Web UI (index.html)
    participant API as FastAPI Backend (/upload)
    participant OCR as Ollama (glm-ocr:q8_0)
    participant Embed as Ollama (nomic-embed-text)
    participant Index as Vector Index (kb_index.json)

    User->>UI: Selects & uploads inspection_sheet.png
    UI->>API: POST /upload (File payload)
    API->>API: Detects image file extension (.png)
    API->>OCR: Send image payload for text extraction
    OCR-->>API: Return extracted raw OCR text
    API->>API: Split OCR text into semantic chunks
    loop For each chunk
        API->>Embed: Generate 768-dim vector embedding
        Embed-->>API: Return vector array
    end
    API->>Index: Append chunk text + vector + source filename
    Index-->>API: Save updated index
    API-->>UI: Return JSON success response (file, chunks count)
    UI-->>User: Display notification: "inspection_sheet.png processed with GLM-OCR (3 chunks added)"
```

---

### Sequence 2: Grounded RAG Query Execution (Knowledge ON)

```mermaid
sequenceDiagram
    autonumber
    actor User as Safety Officer
    participant UI as Web UI (index.html)
    participant API as FastAPI Backend (/chat)
    participant Embed as Ollama (nomic-embed-text)
    participant Index as Local KB Index (kb_index.json)
    participant LLM as Ollama (qwen3.5:4b)

    User->>UI: Types query: "What should be checked during pump inspection?" (Knowledge ON)
    UI->>API: POST /chat { message, knowledge_enabled: true }
    API->>Embed: Embed user query string
    Embed-->>API: Return query vector
    API->>Index: Load stored vectors & calculate cosine similarity
    Index-->>API: Return top-5 context chunks (test_sop.txt, score: 0.9421)
    
    alt High Cosine Similarity Matches Found
        API->>LLM: Pass Grounded System Prompt + Top-5 Context + Query
        LLM-->>API: Return factual answer based strictly on context
        API-->>UI: Return JSON { answer, sources: [{ file: "test_sop.txt", score: 0.9421 }] }
        UI-->>User: Render Grounded Answer + Source Pill Badges
    else Low / Zero Similarity Matches Found
        API-->>UI: Return JSON { answer: "That information is not available in the knowledge base.", sources: [] }
        UI-->>User: Render Anti-Hallucination Warning Message
    end
```

---

### Sequence 3: Code Generation Task Routing

```mermaid
sequenceDiagram
    autonumber
    actor User as Automation Engineer
    participant UI as Web UI (index.html)
    participant API as FastAPI Backend (/chat)
    participant Router as Model Router Engine
    participant CoderLLM as Ollama (qwen2.5-coder:7b)

    User->>UI: Types prompt: "Write a python function to parse refinery sensor logs"
    UI->>API: POST /chat { message, knowledge_enabled: false }
    API->>Router: Analyze prompt keywords ("python", "function", "parse")
    Router-->>API: Keyword match triggered -> Route: CODING
    API->>CoderLLM: Send prompt to qwen2.5-coder:7b
    CoderLLM-->>API: Return synthesized Python code snippet
    API-->>UI: Return JSON { route: "coding", model: "qwen2.5-coder:7b", answer: "```python..." }
    UI-->>User: Render syntax-highlighted code block in UI
```
