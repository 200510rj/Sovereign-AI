from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from urllib.request import Request, urlopen
from urllib.error import URLError
from pathlib import Path
import json
import math
import shutil
import sqlite3
import uuid
from datetime import datetime

from pypdf import PdfReader
import ollama


app = FastAPI()


# ============================================================
# CONFIGURATION
# ============================================================

INDEX_PATH = Path("data/kb_index.json")
KB_PATH = Path("data/knowledge_base")
DB_PATH = Path("data/sovereign.db")

GENERAL_MODEL = "qwen3.5:4b"
CODING_MODEL = "qwen2.5-coder:7b"
EMBED_MODEL = "nomic-embed-text:latest"


# ============================================================
# STARTUP & DATABASE INIT
# ============================================================

KB_PATH.mkdir(
    parents=True,
    exist_ok=True
)

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        title TEXT,
        created_at TEXT
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        role TEXT,
        content TEXT,
        route TEXT,
        model TEXT,
        timestamp TEXT,
        FOREIGN KEY(session_id) REFERENCES sessions(session_id)
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT UNIQUE,
        file_type TEXT,
        chunk_count INTEGER,
        size_bytes INTEGER,
        uploaded_at TEXT
    )
    """)
    
    conn.commit()
    conn.close()

init_db()

def save_chat_message(session_id: str, role: str, content: str, route: str = None, model: str = None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT session_id FROM sessions WHERE session_id = ?", (session_id,))
    if not cursor.fetchone():
        clean_title = content.replace("\n", " ").strip()
        title = clean_title[:32] + "..." if len(clean_title) > 32 else clean_title
        if not title:
            title = "New Conversation"
        cursor.execute("INSERT INTO sessions (session_id, title, created_at) VALUES (?, ?, ?)",
                       (session_id, title, datetime.now().isoformat()))
    
    cursor.execute(
        "INSERT INTO messages (session_id, role, content, route, model, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
        (session_id, role, content, route, model, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def get_all_sessions():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT session_id, title, created_at FROM sessions ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [{"session_id": r[0], "title": r[1], "created_at": r[2]} for r in rows]

def get_session_messages(session_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT role, content, route, model, timestamp FROM messages WHERE session_id = ? ORDER BY id ASC", (session_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1], "route": r[2], "model": r[3], "timestamp": r[4]} for r in rows]

def delete_session(session_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()


# ============================================================
# REQUEST FORMAT
# ============================================================

class MessageItem(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    prompt: str | None = None
    message: str | None = None
    knowledge_enabled: bool = False
    session_id: str | None = None
    history: list[MessageItem] = []



# ============================================================
# MODEL ROUTER
# ============================================================

def select_route(prompt: str):

    prompt_lower = prompt.lower().strip()

    # ========================================================
    # CODING REQUEST
    # ========================================================

    coding_phrases = [
        "write code",
        "write a python",
        "write python",
        "write a python function",
        "write a program",
        "create a function",
        "write a function",
        "implement",
        "debug this code",
        "debug the code",
        "fix this code",
        "fix the code",
        "code for",
        "python code",
        "javascript code",
        "sql query",
        "html code",
        "css code",
        "programming task"
    ]

    if any(
        phrase in prompt_lower
        for phrase in coding_phrases
    ):
        return "coding"

    # ========================================================
    # RAG / DOCUMENT REQUEST
    # ========================================================

    document_phrases = [
        "uploaded",
        "document",
        "pdf",
        "sop",
        "manual",
        "procedure",
        "resume",
        "report",
        "knowledge base",
        "knowledge-base",
        "according to",
        "mentioned in",
        "what does the document say",
        "what does the",
        "what is mentioned",
        "what should be checked",
        "inspection",
        "in the file",
        "in this document"
    ]

    if any(
        phrase in prompt_lower
        for phrase in document_phrases
    ):
        return "rag"

    # ========================================================
    # GENERAL
    # ========================================================

    return "general"


# ============================================================
# OLLAMA EMBEDDING
# ============================================================

def get_embedding(text: str):

    data = json.dumps({
        "model": EMBED_MODEL,
        "input": text
    }).encode("utf-8")

    request = Request(
        "http://127.0.0.1:11434/api/embed",
        data=data,
        headers={
            "Content-Type": "application/json"
        }
    )

    with urlopen(
        request,
        timeout=120
    ) as response:

        result = json.loads(
            response.read().decode("utf-8")
        )

    return result["embeddings"][0]


# ============================================================
# COSINE SIMILARITY
# ============================================================

def cosine_similarity(a, b):

    dot_product = sum(
        x * y
        for x, y in zip(a, b)
    )

    magnitude_a = math.sqrt(
        sum(x * x for x in a)
    )

    magnitude_b = math.sqrt(
        sum(x * x for x in b)
    )

    if (
        magnitude_a == 0
        or magnitude_b == 0
    ):
        return 0

    return dot_product / (
        magnitude_a * magnitude_b
    )


# ============================================================
# LOAD INDEX
# ============================================================

def load_index():

    if not INDEX_PATH.exists():
        return []

    return json.loads(
        INDEX_PATH.read_text(
            encoding="utf-8"
        )
    )


# ============================================================
# SEARCH KNOWLEDGE BASE
# ============================================================

def search_knowledge(
    query,
    top_k=5,
    min_score=0.20
):

    chunks = load_index()

    if not chunks:
        return []

    query_embedding = get_embedding(
        query
    )

    results = []

    for idx, chunk in enumerate(chunks):

        score = cosine_similarity(
            query_embedding,
            chunk["embedding"]
        )

        if score >= min_score:
            results.append({
                "id": idx,
                "source": chunk["source"],
                "text": chunk["text"],
                "score": score
            })

    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return results[:top_k]



# ============================================================
# ASK OLLAMA
# ============================================================

def ask_ollama(
    model: str,
    prompt: str
):

    data = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "think": False,
        "options": {
            "num_predict": 256
        }
    }).encode("utf-8")

    request = Request(
        "http://127.0.0.1:11434/api/generate",
        data=data,
        headers={
            "Content-Type": "application/json"
        }
    )

    try:

        with urlopen(
            request,
            timeout=180
        ) as response:

            result = json.loads(
                response.read().decode("utf-8")
            )

        return result["response"]

    except URLError:

        return "ERROR: Ollama is not running."


def ask_ollama_chat(
    model: str,
    messages: list[dict]
):

    data = json.dumps({
        "model": model,
        "messages": messages,
        "stream": False,
        "think": False,
        "options": {
            "num_predict": 512
        }
    }).encode("utf-8")

    request = Request(
        "http://127.0.0.1:11434/api/chat",
        data=data,
        headers={
            "Content-Type": "application/json"
        }
    )

    try:
        with urlopen(
            request,
            timeout=180
        ) as response:
            result = json.loads(
                response.read().decode("utf-8")
            )
        msg = result.get("message", {})
        content = msg.get("content", "")
        # Fallback if content is empty but thinking was generated
        if not content and msg.get("thinking"):
            content = msg.get("thinking")
        return content or "No response generated."
    except URLError:
        return "ERROR: Ollama is not running."



# ============================================================
# OCR IMAGE PROCESSING
# ============================================================


def clean_ocr_text(text: str):

    cleaned = (text or "").strip()

    if not cleaned:
        return ""

    if cleaned.startswith("```"):

        first_line, separator, rest = cleaned.partition("\n")

        if first_line.strip().startswith("```"):
            cleaned = rest

        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("```", 1)[0]

    return cleaned.strip()


def ocr_image(file_path: Path):

    try:

        response = ollama.chat(
            model="glm-ocr:q8_0",
            messages=[
                {
                    "role": "user",
                    "content": "Extract all visible text from this image. Preserve the structure as much as possible.",
                    "images": [str(file_path)],
                }
            ],
        )

        content = response.get("message", {}).get("content", "")
        cleaned_text = clean_ocr_text(content)

        if not cleaned_text:
            return None

        return cleaned_text

    except Exception:
        return None


# ============================================================
# DOCUMENT EXTRACTION
# ============================================================

def extract_text(file_path: Path):

    extension = file_path.suffix.lower()

    # -------------------------
    # TXT
    # -------------------------

    if extension in [".txt", ".md"]:

        return file_path.read_text(
            encoding="utf-8"
        )


    # -------------------------
    # PDF
    # -------------------------

    if extension == ".pdf":

        reader = PdfReader(
            str(file_path)
        )

        pages = []

        for page in reader.pages:

            text = page.extract_text()

            if text:
                pages.append(text)

        return "\n\n".join(pages)


    raise ValueError(
        "Only TXT, MD, and PDF files are supported."
    )


# ============================================================
# CHUNK DOCUMENT
# ============================================================

def chunk_text(
    text,
    max_chars=1800
):

    paragraphs = [
        p.strip()
        for p in text.split("\n\n")
        if p.strip()
    ]

    chunks = []

    current = ""

    for paragraph in paragraphs:

        if not current:

            current = paragraph

        elif len(current) + len(paragraph) + 2 <= max_chars:

            current += "\n\n" + paragraph

        else:

            chunks.append(
                current
            )

            current = paragraph

    if current:
        chunks.append(
            current
        )

    return chunks


# ============================================================
# ADD DOCUMENT TO INDEX
# ============================================================

def index_document(
    file_name,
    text
):

    chunks = chunk_text(text)

    existing_index = load_index()

    new_entries = []

    for chunk in chunks:

        print(
            f"Embedding: {file_name}"
        )

        embedding = get_embedding(
            chunk
        )

        new_entries.append({
            "source": file_name,
            "text": chunk,
            "embedding": embedding
        })


    existing_index.extend(
        new_entries
    )


    INDEX_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    INDEX_PATH.write_text(
        json.dumps(
            existing_index,
            indent=2
        ),
        encoding="utf-8"
    )


    return len(new_entries)


# ============================================================
# WEB UI
# ============================================================

@app.get("/")
def home():

    return FileResponse(
        "frontend/index.html"
    )


# ============================================================
# LIST DOCUMENTS
# ============================================================

@app.get("/documents")
def list_documents():
    index_entries = load_index()
    doc_stats = {}
    for entry in index_entries:
        src = entry.get("source", "Unknown")
        doc_stats[src] = doc_stats.get(src, 0) + 1

    docs = []
    if KB_PATH.exists():
        for file_path in KB_PATH.iterdir():
            if file_path.is_file():
                docs.append({
                    "name": file_path.name,
                    "size_bytes": file_path.stat().st_size,
                    "chunks": doc_stats.get(file_path.name, 0),
                    "extension": file_path.suffix.lower()
                })
    return {"documents": docs}


# ============================================================
# SESSION MANAGEMENT API
# ============================================================

@app.get("/sessions")
def list_sessions():
    return {"sessions": get_all_sessions()}


@app.get("/sessions/{session_id}/messages")
def list_session_messages(session_id: str):
    return {"session_id": session_id, "messages": get_session_messages(session_id)}


@app.delete("/sessions/{session_id}")
def remove_session(session_id: str):
    delete_session(session_id)
    return {"success": True, "message": f"Session {session_id} deleted."}



# ============================================================
# CODE EXECUTION SANDBOX
# ============================================================

import sys
import subprocess
import tempfile

class CodeExecutionRequest(BaseModel):
    code: str
    timeout: int = 10

@app.post("/execute_code")
def execute_code(request: CodeExecutionRequest):
    code = request.code.strip()
    if not code:
        return {"success": False, "stdout": "", "stderr": "No code provided.", "exit_code": -1}
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as temp_file:
        temp_file.write(code)
        temp_file_path = temp_file.name
    
    try:
        result = subprocess.run(
            [sys.executable, temp_file_path],
            capture_output=True,
            text=True,
            timeout=request.timeout
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Execution timed out after {request.timeout} seconds.",
            "exit_code": -1
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "exit_code": -1
        }
    finally:
        try:
            Path(temp_file_path).unlink(missing_ok=True)
        except Exception:
            pass


# ============================================================
# AUTOMATIC DOCUMENT GENERATION ENGINE (PDF, DOCX, XLSX)
# ============================================================

REPORTS_PATH = Path("data/reports")
REPORTS_PATH.mkdir(parents=True, exist_ok=True)

class ReportRequest(BaseModel):
    title: str
    content: str
    format: str = "pdf"
    author: str = "Sovereign AI Workbench"

@app.post("/generate_report")
def generate_report(request: ReportRequest):
    fmt = request.format.lower().strip()
    if fmt not in ["pdf", "docx", "xlsx"]:
        return {
            "success": False,
            "error": f"Unsupported format '{fmt}'. Supported formats: pdf, docx, xlsx"
        }
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_title = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in request.title).strip().replace(" ", "_")
    if not clean_title:
        clean_title = "Report"
    filename = f"{clean_title}_{timestamp}.{fmt}"
    output_path = REPORTS_PATH / filename

    try:
        if fmt == "pdf":
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors

            doc = SimpleDocTemplate(str(output_path), pagesize=letter)
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle(
                'DocTitle',
                parent=styles['Heading1'],
                fontSize=18,
                leading=22,
                textColor=colors.HexColor('#1e3a8a'),
                spaceAfter=10
            )
            meta_style = ParagraphStyle(
                'DocMeta',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.HexColor('#64748b'),
                spaceAfter=14
            )
            body_style = ParagraphStyle(
                'DocBody',
                parent=styles['Normal'],
                fontSize=10,
                leading=14,
                textColor=colors.HexColor('#1f2937'),
                spaceAfter=8
            )

            story = [
                Paragraph(request.title, title_style),
                Paragraph(f"<b>Author:</b> {request.author} | <b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", meta_style),
                Spacer(1, 8)
            ]

            for para in request.content.split("\n\n"):
                if para.strip():
                    clean_para = para.replace("\n", "<br/>")
                    story.append(Paragraph(clean_para, body_style))
                    story.append(Spacer(1, 4))

            doc.build(story)

        elif fmt == "docx":
            import docx

            doc = docx.Document()
            doc.add_heading(request.title, level=1)
            doc.add_paragraph(f"Author: {request.author} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            for para in request.content.split("\n\n"):
                if para.strip():
                    doc.add_paragraph(para.strip())
            
            doc.save(str(output_path))

        elif fmt == "xlsx":
            import openpyxl
            from openpyxl.styles import Font

            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Report"

            ws.append([request.title])
            ws.append([f"Author: {request.author}", f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
            ws.append([])

            for line in request.content.strip().split("\n"):
                if "," in line:
                    row_data = [col.strip() for col in line.split(",")]
                elif "\t" in line:
                    row_data = [col.strip() for col in line.split("\t")]
                else:
                    row_data = [line.strip()]
                ws.append(row_data)

            ws["A1"].font = Font(size=14, bold=True, color="1E3A8A")
            wb.save(str(output_path))

        return {
            "success": True,
            "filename": filename,
            "format": fmt,
            "download_url": f"/download_report/{filename}"
        }

    except Exception as err:
        return {
            "success": False,
            "error": f"Failed to generate {fmt} report: {str(err)}"
        }

@app.get("/download_report/{filename}")
def download_report(filename: str):
    file_path = REPORTS_PATH / filename
    if not file_path.exists():
        return {"error": "Report not found"}
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream"
    )


# ============================================================
# DOCUMENT UPLOAD
# ============================================================

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...)
):

    filename = Path(
        file.filename
    ).name

    extension = Path(
        filename
    ).suffix.lower()


    if extension not in [
        ".txt",
        ".md",
        ".pdf",
        ".png",
        ".jpg",
        ".jpeg",
        ".webp"
    ]:

        return {
            "success": False,
            "message":
                "Only PDF, TXT, MD, PNG, JPG, JPEG, and WEBP files are supported."
        }


    destination = (
        KB_PATH / filename
    )


    with destination.open("wb") as buffer:

        shutil.copyfileobj(
            file.file,
            buffer
        )


    try:

        if extension in [
            ".png",
            ".jpg",
            ".jpeg",
            ".webp"
        ]:

            text = ocr_image(destination)

            if not text or not text.strip():

                return {
                    "success": False,
                    "message":
                        "GLM-OCR failed to process this image."
                }

            chunk_count = index_document(
                filename,
                text
            )

            return {
                "success": True,
                "file": filename,
                "chunks": chunk_count,
                "message":
                    f"{filename} processed with GLM-OCR and added to knowledge base. {chunk_count} chunks created."
            }

        text = extract_text(
            destination
        )

        if not text.strip():

            return {
                "success": False,
                "message":
                    "No readable text was found."
            }


        chunk_count = index_document(
            filename,
            text
        )


        return {
            "success": True,
            "file": filename,
            "chunks": chunk_count,
            "message":
                f"{filename} added to knowledge base. {chunk_count} chunks created."
        }

    except Exception as error:

        return {
            "success": False,
            "message":
                f"Failed to process document: {error}"
        }

# ============================================================
# CHAT
# ============================================================

@app.post("/chat")
def chat(
    request: ChatRequest
):

    question = (
        request.prompt or request.message or ""
    ).strip()

    knowledge_enabled = bool(
        request.knowledge_enabled
    )

    if not question:

        return {
            "model": GENERAL_MODEL,
            "route": "general",
            "knowledge_enabled": knowledge_enabled,
            "answer": "Please enter a question.",
            "sources": []
        }


    session_id = request.session_id or str(uuid.uuid4())
    save_chat_message(session_id, "user", question)

    # Format past history into chat message list
    formatted_messages = []
    for item in request.history:
        role = item.role if item.role in ["user", "assistant", "system"] else "user"
        formatted_messages.append({"role": role, "content": item.content})

    # ========================================================
    # CODING TASK
    # ========================================================

    route = select_route(
        question
    )

    if route == "coding":

        messages = list(formatted_messages)
        messages.append({"role": "user", "content": question})

        answer = ask_ollama_chat(
            CODING_MODEL,
            messages
        )

        save_chat_message(session_id, "assistant", answer, route="coding", model=CODING_MODEL)

        return {
            "session_id": session_id,
            "model": CODING_MODEL,
            "route": "coding",
            "knowledge_enabled": knowledge_enabled,
            "answer": answer,
            "sources": []
        }

    if knowledge_enabled:

        results = search_knowledge(
            question,
            top_k=5
        )

        context_parts = []

        for result in results:

            context_parts.append(
                f"[Source: {result['source']}]\n"
                f"{result['text']}"
            )

        context = "\n\n".join(
            context_parts
        ) if context_parts else (
            "No relevant knowledge base entries were found."
        )

        system_instruction = f"""You are a local enterprise AI assistant.
Answer the user's question using ONLY the provided knowledge-base context.
Do not invent procedures, measurements, requirements, policies, or facts.
If the context does not contain enough information, say: "That information is not available in the knowledge base."

KNOWLEDGE BASE:
{context}"""

        messages = [{"role": "system", "content": system_instruction}] + formatted_messages + [{"role": "user", "content": question}]

        answer = ask_ollama_chat(
            GENERAL_MODEL,
            messages
        )

        sources = []

        for result in results:

            sources.append({
                "id": result.get("id", 0),
                "file": result["source"],
                "score": round(
                    result["score"],
                    4
                ),
                "snippet": result["text"]
            })

        save_chat_message(session_id, "assistant", answer, route="rag", model=GENERAL_MODEL)

        return {
            "session_id": session_id,
            "model": GENERAL_MODEL,
            "route": "rag",
            "knowledge_enabled": True,
            "answer": answer,
            "sources": sources
        }

    # ========================================================
    # GENERAL
    # ========================================================

    messages = list(formatted_messages)
    messages.append({"role": "user", "content": question})

    answer = ask_ollama_chat(
        GENERAL_MODEL,
        messages
    )

    save_chat_message(session_id, "assistant", answer, route="general", model=GENERAL_MODEL)

    return {
        "session_id": session_id,
        "model": GENERAL_MODEL,
        "route": "general",
        "knowledge_enabled": False,
        "answer": answer,
        "sources": []
    }




if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
