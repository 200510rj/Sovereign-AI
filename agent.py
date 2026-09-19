"""
Sovereign AI Workbench - Agent Layer (agent.py)
Dynamic ReAct Agent loop using Ollama native tool/function calling with qwen3.5:4b.
Zero external calls, zero mocks, 100% on-premise execution.
"""

import json
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError

AGENT_MODEL = "qwen3.5:4b"
OLLAMA_CHAT_URL = "http://127.0.0.1:11434/api/chat"

# ============================================================
# TOOL SCHEMAS FOR OLLAMA FUNCTION CALLING
# ============================================================

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Search the local sovereign knowledge base for SOPs, manuals, resumes, and technical documents using hybrid semantic vector and keyword search.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query or keyword phrase to find in documents."
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Maximum number of chunks to retrieve (default 5).",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_python_code",
            "description": "Execute Python code in a safe local sandbox and return stdout, stderr, and exit code. Use this whenever the user asks to run code, perform computations, or test scripts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Valid Python code to execute locally."
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds (default 10).",
                        "default": 10
                    }
                },
                "required": ["code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_report",
            "description": "Generate a downloadable enterprise report deliverable in PDF, DOCX (Word), or XLSX (Excel) format. Use this whenever the user asks to create, export, or generate an official report, checklist, or summary file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Title of the report or document."
                    },
                    "content": {
                        "type": "string",
                        "description": "Body content of the report. For XLSX, provide comma or tab-separated rows."
                    },
                    "format": {
                        "type": "string",
                        "description": "Output format: 'pdf', 'docx', or 'xlsx'.",
                        "enum": ["pdf", "docx", "xlsx"],
                        "default": "pdf"
                    },
                    "author": {
                        "type": "string",
                        "description": "Author name or unit (default 'Sovereign AI Agent').",
                        "default": "Sovereign AI Agent"
                    }
                },
                "required": ["title", "content", "format"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_uploaded_document",
            "description": "Read the extracted text content of a specific uploaded file in the knowledge base by filename.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Exact name of the file in the knowledge base (e.g., 'test_sop.txt', 'Utsav Dhobi Resume.pdf')."
                    }
                },
                "required": ["filename"]
            }
        }
    }
]

# ============================================================
# TOOL EXECUTOR
# ============================================================

def execute_tool(tool_name: str, arguments: dict) -> dict:
    """Executes a requested tool locally using existing production logic."""
    import main  # Lazy import to avoid circular dependency

    start_time = time.time()

    if tool_name == "search_knowledge_base":
        query = arguments.get("query", "")
        top_k = arguments.get("top_k", 5)
        results = main.search_knowledge(query, top_k=top_k)
        
        snippets = []
        for r in results:
            snippets.append({
                "source": r.get("source"),
                "score": round(r.get("score", 0), 3),
                "text": r.get("text", "")[:400] + "..." if len(r.get("text", "")) > 400 else r.get("text", "")
            })

        duration = round(time.time() - start_time, 2)
        return {
            "success": True,
            "tool": tool_name,
            "query": query,
            "count": len(results),
            "results": snippets,
            "raw_results": results,
            "duration_sec": duration
        }

    elif tool_name == "execute_python_code":
        code = arguments.get("code", "")
        timeout = arguments.get("timeout", 10)
        req = main.CodeExecutionRequest(code=code, timeout=timeout)
        res = main.execute_code(req)
        duration = round(time.time() - start_time, 2)
        return {
            "success": res.get("success", False),
            "tool": tool_name,
            "stdout": res.get("stdout", ""),
            "stderr": res.get("stderr", ""),
            "exit_code": res.get("exit_code", 0),
            "duration_sec": duration
        }

    elif tool_name == "generate_report":
        title = arguments.get("title", "Report")
        content = arguments.get("content", "")
        fmt = arguments.get("format", "pdf")
        author = arguments.get("author", "Sovereign AI Agent")
        req = main.ReportRequest(title=title, content=content, format=fmt, author=author)
        res = main.generate_report(req)
        duration = round(time.time() - start_time, 2)
        return {
            "success": res.get("success", False),
            "tool": tool_name,
            "filename": res.get("filename", ""),
            "download_url": res.get("download_url", ""),
            "format": fmt,
            "duration_sec": duration
        }

    elif tool_name == "read_uploaded_document":
        filename = arguments.get("filename", "")
        target = main.KB_PATH / filename
        if not target.exists():
            return {
                "success": False,
                "tool": tool_name,
                "error": f"File '{filename}' not found in knowledge base."
            }
        try:
            text = main.extract_text(target)
            preview = text[:1500] + "\n...[truncated]" if len(text) > 1500 else text
            duration = round(time.time() - start_time, 2)
            return {
                "success": True,
                "tool": tool_name,
                "filename": filename,
                "char_count": len(text),
                "text": preview,
                "duration_sec": duration
            }
        except Exception as e:
            return {
                "success": False,
                "tool": tool_name,
                "error": str(e)
            }

    return {
        "success": False,
        "tool": tool_name,
        "error": f"Unknown tool: '{tool_name}'"
    }

# ============================================================
# REACT AGENT LOOP
# ============================================================

def run_agent(question: str, history: list = None, max_steps: int = 5) -> dict:
    """
    Executes a dynamic ReAct agent loop using local Ollama model qwen3.5:4b.
    Allows multi-step tool calls, reasoning, and synthesis.
    """
    system_prompt = (
        "You are Sovereign Agent, an autonomous enterprise industrial AI assistant operating in a strictly air-gapped on-premise environment.\n"
        "You have access to local tools to search the knowledge base, read documents, execute Python code, and generate official reports.\n"
        "Rules:\n"
        "1. When asked about documents, technical SOPs, or people, call 'search_knowledge_base' or 'read_uploaded_document'.\n"
        "2. When asked to write and run code or verify a computation, use 'execute_python_code'.\n"
        "3. When asked to create, export, or generate documents or checklists, call 'generate_report'.\n"
        "4. You may call multiple tools in sequence if needed.\n"
        "5. Once you have all required tool outputs, provide a clear, professional, and grounded final answer."
    )

    messages = [{"role": "system", "content": system_prompt}]

    if history:
        for item in history:
            role = item.get("role") if item.get("role") in ["user", "assistant"] else "user"
            messages.append({"role": role, "content": item.get("content", "")})

    messages.append({"role": "user", "content": question})

    tool_log = []
    collected_sources = []
    files_created = []

    for step in range(1, max_steps + 1):
        payload = {
            "model": AGENT_MODEL,
            "messages": messages,
            "tools": TOOL_SCHEMAS,
            "stream": False,
            "think": False,
            "options": {
                "num_predict": 512,
                "temperature": 0.2
            }
        }

        req = Request(
            OLLAMA_CHAT_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )

        try:
            with urlopen(req, timeout=180) as resp:
                result = json.loads(resp.read().decode("utf-8"))
        except URLError as err:
            return {
                "answer": f"ERROR: Agent failed to connect to Ollama: {err}",
                "tool_log": tool_log,
                "sources": collected_sources,
                "files_created": files_created
            }

        msg = result.get("message", {})
        tool_calls = msg.get("tool_calls", [])

        # If no tool calls, model gave the final answer
        if not tool_calls:
            content = msg.get("content", "").strip()
            if not content and msg.get("thinking"):
                content = msg.get("thinking").strip()
            return {
                "answer": content or "Task completed.",
                "tool_log": tool_log,
                "sources": collected_sources,
                "files_created": files_created
            }

        # Otherwise, process and execute tool calls
        messages.append(msg)

        for tc in tool_calls:
            func_meta = tc.get("function", {})
            fn_name = func_meta.get("name")
            fn_args = func_meta.get("arguments", {})
            if isinstance(fn_args, str):
                try:
                    fn_args = json.loads(fn_args)
                except Exception:
                    fn_args = {}

            # Execute tool locally
            tool_output = execute_tool(fn_name, fn_args)

            # Record step in tool log
            step_record = {
                "step": step,
                "tool": fn_name,
                "arguments": fn_args,
                "success": tool_output.get("success", False),
                "duration_sec": tool_output.get("duration_sec", 0)
            }

            if fn_name == "search_knowledge_base":
                step_record["summary"] = f"Found {tool_output.get('count', 0)} chunks for '{fn_args.get('query', '')}'"
                for r in tool_output.get("raw_results", []):
                    collected_sources.append({
                        "id": r.get("id", 0),
                        "file": r.get("source"),
                        "score": round(r.get("score", 0), 3),
                        "snippet": r.get("text", "")
                    })
            elif fn_name == "execute_python_code":
                stdout_preview = (tool_output.get("stdout") or "").strip()
                stderr_preview = (tool_output.get("stderr") or "").strip()
                step_record["summary"] = f"Executed (exit {tool_output.get('exit_code', 0)}): {stdout_preview or stderr_preview or 'OK'}"
                step_record["stdout"] = stdout_preview
                step_record["stderr"] = stderr_preview
            elif fn_name == "generate_report":
                step_record["summary"] = f"Generated {tool_output.get('format', '').upper()}: {tool_output.get('filename')}"
                step_record["download_url"] = tool_output.get("download_url")
                if tool_output.get("filename"):
                    files_created.append({
                        "filename": tool_output.get("filename"),
                        "format": tool_output.get("format"),
                        "download_url": tool_output.get("download_url")
                    })
            elif fn_name == "read_uploaded_document":
                step_record["summary"] = f"Read {tool_output.get('char_count', 0)} chars from '{fn_args.get('filename')}'"

            tool_log.append(step_record)

            # Feed result back to Ollama message history
            clean_result_str = json.dumps({k: v for k, v in tool_output.items() if k != "raw_results"})
            messages.append({
                "role": "tool",
                "content": clean_result_str
            })

    # If loop finishes without explicit final answer, prompt for final synthesis
    messages.append({
        "role": "user",
        "content": "Please synthesize all the tool execution results above into a clear final answer."
    })
    final_payload = {
        "model": AGENT_MODEL,
        "messages": messages,
        "stream": False,
        "think": False,
        "options": {"num_predict": 512}
    }
    req = Request(
        OLLAMA_CHAT_URL,
        data=json.dumps(final_payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urlopen(req, timeout=120) as resp:
        res = json.loads(resp.read().decode("utf-8"))
    final_msg = res.get("message", {}).get("content", "Task completed.")

    return {
        "answer": final_msg,
        "tool_log": tool_log,
        "sources": collected_sources,
        "files_created": files_created
    }
