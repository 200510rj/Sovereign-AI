"""
Sovereign AI Workbench - Agent Layer (agent.py)
Dynamic ReAct Agent loop using LangChain ChatOllama & Tool bindings with qwen3.5:4b.
Zero external calls, zero mocks, 100% on-premise execution.
"""

import json
import re
import time
from pathlib import Path

from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

import web_search_tool

AGENT_MODEL = "qwen3.5:4b"
DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"

# ============================================================
# LANGCHAIN TOOL DEFINITIONS
# ============================================================

@tool("search_knowledge_base")
def search_knowledge_base_tool(query: str, top_k: int = 5) -> str:
    """Search the local sovereign knowledge base for SOPs, manuals, resumes, and technical documents using hybrid semantic vector and keyword search."""
    import main
    results = main.search_knowledge(query, top_k=top_k)
    if not results:
        return f"No relevant documents found in local knowledge base for query: '{query}'."
    parts = []
    for r in results:
        parts.append(f"Source: {r.get('source')}\nScore: {round(r.get('score', 0), 3)}\nContent: {r.get('text')}")
    return "\n\n---\n\n".join(parts)

@tool("execute_python_code")
def execute_python_code_tool(code: str, timeout: int = 10) -> str:
    """Execute Python code in a safe local sandbox and return stdout, stderr, and exit code. Use this whenever the user asks to run code, perform computations, or test scripts."""
    import main
    req = main.CodeExecutionRequest(code=code, timeout=timeout)
    res = main.execute_code(req)
    stdout = res.get("stdout", "").strip()
    stderr = res.get("stderr", "").strip()
    exit_code = res.get("exit_code", 0)
    return f"Exit Code: {exit_code}\nStdout:\n{stdout or '(none)'}\nStderr:\n{stderr or '(none)'}"

@tool("generate_report")
def generate_report_tool(title: str, content: str, format: str = "pdf", author: str = "Sovereign AI Agent") -> str:
    """Generate a downloadable enterprise report deliverable in PDF, DOCX (Word), or XLSX (Excel) format. Use this whenever the user asks to create, export, or generate an official report, checklist, or summary file."""
    import main
    req = main.ReportRequest(title=title, content=content, format=format, author=author)
    res = main.generate_report(req)
    if res.get("success"):
        return f"Report generated successfully: {res.get('filename')} (Download URL: {res.get('download_url')})"
    return f"Failed to generate report: {res.get('error', 'Unknown error')}"

@tool("read_uploaded_document")
def read_uploaded_document_tool(filename: str) -> str:
    """Read the extracted text content of a specific uploaded file in the knowledge base by filename."""
    import main
    target = main.KB_PATH / filename.strip()
    if not target.exists():
        norm_req = re.sub(r'[\s_]+', '', filename.lower())
        matched_file = None
        if main.KB_PATH.exists():
            for f in main.KB_PATH.iterdir():
                if f.is_file():
                    norm_f = re.sub(r'[\s_]+', '', f.name.lower())
                    if norm_req == norm_f or norm_req in norm_f or norm_f in norm_req:
                        matched_file = f
                        break
        if matched_file:
            target = matched_file
        else:
            return f"Error: File '{filename}' not found in knowledge base."
    try:
        text = main.extract_text(target)
        return text[:10000] + "\n...[truncated]" if len(text) > 10000 else (text or "[Empty text extracted]")
    except Exception as e:
        return f"Error reading document '{filename}': {e}"

@tool("web_search")
def web_search_tool_func(query: str, top_k: int = 5) -> str:
    """Search the web for up-to-date real-world information, technical specifications, industrial standards, external documentation, or company facts."""
    return web_search_tool.web_search_tool.invoke({"query": query, "max_results": top_k})

LANGCHAIN_TOOLS = [
    search_knowledge_base_tool,
    execute_python_code_tool,
    generate_report_tool,
    read_uploaded_document_tool,
    web_search_tool_func
]

# Standard Tool Schemas compatibility dictionary for legacy callers
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Search the local sovereign knowledge base for SOPs, manuals, resumes, and technical documents using hybrid semantic vector and keyword search.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query or keyword phrase to find in documents."},
                    "top_k": {"type": "integer", "description": "Maximum number of chunks to retrieve (default 5).", "default": 5}
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
                    "code": {"type": "string", "description": "Valid Python code to execute locally."},
                    "timeout": {"type": "integer", "description": "Timeout in seconds (default 10).", "default": 10}
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
                    "title": {"type": "string", "description": "Title of the report or document."},
                    "content": {"type": "string", "description": "Body content of the report. For XLSX, provide comma or tab-separated rows."},
                    "format": {"type": "string", "description": "Output format: 'pdf', 'docx', or 'xlsx'.", "enum": ["pdf", "docx", "xlsx"], "default": "pdf"},
                    "author": {"type": "string", "description": "Author name or unit (default 'Sovereign AI Agent').", "default": "Sovereign AI Agent"}
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
                    "filename": {"type": "string", "description": "Exact name of the file in the knowledge base (e.g., 'test_sop.txt', 'Utsav Dhobi Resume.pdf')."}
                },
                "required": ["filename"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for up-to-date real-world information, technical specifications, industrial standards, external documentation, or company facts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Keywords or search phrase to query the web for."},
                    "top_k": {"type": "integer", "description": "Maximum number of search results to return (default 5).", "default": 5}
                },
                "required": ["query"]
            }
        }
    }
]

# ============================================================
# WEB SEARCH HELPER
# ============================================================

def perform_web_search(query: str, top_k: int = 5) -> list[dict]:
    """Performs live web search using LangChain & DuckDuckGo Search (DDGS) with KB fallback."""
    import main
    clean_query = (query or "").strip()
    if not clean_query:
        return []

    results = web_search_tool.search_web(clean_query, max_results=top_k)

    if not results:
        try:
            kb_chunks = main.search_knowledge(clean_query, top_k=top_k)
            for c in kb_chunks:
                results.append({
                    "title": f"Local Document: {c.get('source', 'KB')}",
                    "snippet": c.get("text", "")[:300],
                    "url": f"local://knowledge_base/{c.get('source', '')}",
                    "source": "Sovereign Local KB"
                })
        except Exception:
            pass

    return results[:top_k]

# ============================================================
# TOOL EXECUTOR
# ============================================================

def execute_tool(tool_name: str, arguments: dict, base_url: str | None = None) -> dict:
    """Executes a requested tool locally using existing production logic."""
    import main
    start_time = time.time()

    if tool_name == "search_knowledge_base":
        query = arguments.get("query", "")
        top_k = arguments.get("top_k", 5)
        results = main.search_knowledge(query, top_k=top_k, base_url=base_url)
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

    elif tool_name == "web_search":
        query = arguments.get("query", "") or arguments.get("task", "")
        top_k = arguments.get("top_k", 5)
        results = perform_web_search(query, top_k=top_k)
        duration = round(time.time() - start_time, 2)
        return {
            "success": len(results) > 0,
            "tool": tool_name,
            "query": query,
            "count": len(results),
            "results": results,
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
        filename = arguments.get("filename", "").strip()
        target = main.KB_PATH / filename

        if not target.exists():
            norm_req = re.sub(r'[\s_]+', '', filename.lower())
            matched_file = None
            if main.KB_PATH.exists():
                for f in main.KB_PATH.iterdir():
                    if f.is_file():
                        norm_f = re.sub(r'[\s_]+', '', f.name.lower())
                        if norm_req == norm_f or norm_req in norm_f or norm_f in norm_req:
                            matched_file = f
                            break
            if matched_file:
                target = matched_file
            else:
                return {
                    "success": False,
                    "tool": tool_name,
                    "error": f"File '{filename}' not found in knowledge base."
                }
        try:
            text = main.extract_text(target)
            preview = text[:10000] + "\n...[truncated]" if len(text) > 10000 else text
            duration = round(time.time() - start_time, 2)
            return {
                "success": True,
                "tool": tool_name,
                "filename": target.name,
                "char_count": len(text),
                "text": preview or "[Empty text extracted]",
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

# Fallback parser for text tool call tags (<tool_call>, ```json, etc.)
def extract_tool_calls_from_message(msg_content: str) -> list[dict]:
    full_text = (msg_content or "").strip()
    if not full_text:
        return []

    parsed_calls = []

    for match in re.finditer(r"<tool_call>\s*({.*?})\s*</tool_call>", full_text, re.DOTALL):
        try:
            data = json.loads(match.group(1))
            name = data.get("name") or data.get("tool") or data.get("function")
            args = data.get("arguments") or data.get("parameters") or data.get("args") or {}
            if name:
                parsed_calls.append({"name": name, "arguments": args})
        except Exception:
            pass

    if not parsed_calls:
        for match in re.finditer(r"```(?:json)?\s*({[\s\S]*?})\s*```", full_text):
            try:
                data = json.loads(match.group(1))
                name = data.get("name") or data.get("tool")
                args = data.get("arguments") or data.get("parameters") or {}
                if name in ["search_knowledge_base", "web_search", "execute_python_code", "generate_report", "read_uploaded_document"]:
                    parsed_calls.append({"name": name, "arguments": args})
            except Exception:
                pass

    if not parsed_calls:
        for tool_name in ["search_knowledge_base", "web_search", "execute_python_code", "generate_report", "read_uploaded_document"]:
            pattern = rf'\{{\s*"name":\s*"{tool_name}",\s*"arguments":\s*(\{{.*?\}})\s*\}}'
            for match in re.finditer(pattern, full_text, re.DOTALL):
                try:
                    args = json.loads(match.group(1))
                    parsed_calls.append({"name": tool_name, "arguments": args})
                except Exception:
                    pass

    return parsed_calls


# ============================================================
# LANGCHAIN REACT AGENT LOOP
# ============================================================

def run_agent(question: str, history: list = None, max_steps: int = 12, base_url: str | None = None, urgency_prefix: str = "") -> dict:
    """
    Executes a dynamic ReAct agent loop using LangChain ChatOllama & Tool bindings on qwen3.5:4b.
    Provides autonomous multi-step tool calls, reasoning, deliverable generation, and synthesis.
    """
    import main

    target_ollama = (base_url or main.get_ollama_url()).rstrip("/")
    llm = ChatOllama(
        model=AGENT_MODEL,
        base_url=target_ollama,
        temperature=0.1
    )
    llm_with_tools = llm.bind_tools(LANGCHAIN_TOOLS)

    system_instruction = (
        "You are Sovereign Agent, an autonomous enterprise AI assistant operating in a strictly air-gapped on-premise environment.\n"
        "You have access to local tools to search the knowledge base, read documents, execute Python code, search the web, and generate official reports.\n"
        "Instructions:\n"
        "1. For questions requiring knowledge base documents, call 'search_knowledge_base' or 'read_uploaded_document'.\n"
        "2. For live web search questions, call 'web_search'.\n"
        "3. For computations, math, or scripts, call 'execute_python_code'.\n"
        "4. When generating reports (PDF, DOCX, XLSX), ALWAYS dynamically construct title and content based strictly on retrieved context and user task. NEVER use generic or dummy text.\n"
        "5. Chain multiple tools autonomously before synthesizing the final answer."
    )

    if urgency_prefix:
        system_instruction = urgency_prefix.strip() + "\n\n" + system_instruction

    lc_messages = [SystemMessage(content=system_instruction)]

    if history:
        for item in history:
            role = item.get("role", "user")
            content = item.get("content", "")
            if role == "assistant":
                lc_messages.append(AIMessage(content=content))
            else:
                lc_messages.append(HumanMessage(content=content))

    lc_messages.append(HumanMessage(content=question))

    tool_log = []
    collected_sources = []
    files_created = []
    executed_tool_names = set()

    q_lower = question.lower()
    wants_report = any(w in q_lower for w in ["report", "pdf", "docx", "word", "xlsx", "excel", "deliverable", "export", "generate a", "create a"])
    wants_docx = "docx" in q_lower or "word" in q_lower
    wants_xlsx = "xlsx" in q_lower or "excel" in q_lower or "spreadsheet" in q_lower
    target_report_fmt = "xlsx" if wants_xlsx else ("docx" if wants_docx else "pdf")

    final_answer = ""

    for step in range(1, max_steps + 1):
        try:
            response = llm_with_tools.invoke(lc_messages)
        except Exception as err:
            break

        content = (response.content or "").strip()
        lc_messages.append(response)

        raw_tool_calls = getattr(response, "tool_calls", [])
        tool_calls_to_run = []

        if raw_tool_calls:
            for tc in raw_tool_calls:
                tool_calls_to_run.append({
                    "id": tc.get("id"),
                    "name": tc.get("name"),
                    "arguments": tc.get("args", {})
                })
        else:
            fallback_calls = extract_tool_calls_from_message(content)
            for fc in fallback_calls:
                tool_calls_to_run.append({
                    "id": f"call_{int(time.time()*1000)}",
                    "name": fc.get("name"),
                    "arguments": fc.get("arguments", {})
                })

        if not tool_calls_to_run:
            final_answer = content or "Task completed."
            break

        for tc in tool_calls_to_run:
            fn_name = tc.get("name")
            fn_args = tc.get("arguments", {})
            executed_tool_names.add(fn_name)

            tool_output = execute_tool(fn_name, fn_args, base_url=target_ollama)

            step_record = {
                "step": len(tool_log) + 1,
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
            elif fn_name == "web_search":
                step_record["summary"] = f"Searched web: found {tool_output.get('count', 0)} results for '{fn_args.get('query', '')}'"
                for r in tool_output.get("results", []):
                    collected_sources.append({
                        "id": len(collected_sources) + 1,
                        "file": f"🌐 {r.get('title', 'Web Source')} ({r.get('source', 'Web')})",
                        "score": 1.0,
                        "snippet": r.get("snippet", "") + f"\nURL: {r.get('url', '')}"
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

            clean_result_str = json.dumps({k: v for k, v in tool_output.items() if k != "raw_results"})
            lc_messages.append(ToolMessage(
                content=clean_result_str,
                name=fn_name,
                tool_call_id=tc.get("id") or f"call_{len(tool_log)}"
            ))

    # Auto-Fulfillment Planner if user requested deliverable report
    if wants_report and "generate_report" not in executed_tool_names:
        clean_q = re.sub(r'[^a-zA-Z0-9\s]', '', question).strip()
        words = [w for w in clean_q.split() if w.lower() not in ['generate', 'create', 'make', 'a', 'the', 'report', 'pdf', 'docx', 'xlsx', 'and', 'or', 'in', 'to', 'for']]
        dynamic_title = " ".join(words[:5]).title() if words else "Analysis Report"

        content_lines = [f"# {dynamic_title}\n\n## Objective\n{question}\n\n## Summary & Retrieved Findings:"]
        if collected_sources:
            for s in collected_sources:
                content_lines.append(f"### Source: {s.get('file', 'Knowledge Base')}\n{s.get('snippet', '')}\n")
        elif tool_log:
            for t in tool_log:
                content_lines.append(f"- **Step {t.get('step')} ({t.get('tool')})**: {t.get('summary', 'Executed')}")
        else:
            content_lines.append("Analysis conducted based on available system documents and data.")

        report_body = "\n".join(content_lines)
        report_out = execute_tool("generate_report", {
            "title": dynamic_title,
            "content": report_body,
            "format": target_report_fmt,
            "author": "Sovereign AI Autonomous Agent"
        }, base_url=target_ollama)

        executed_tool_names.add("generate_report")
        tool_log.append({
            "step": len(tool_log) + 1,
            "tool": "generate_report",
            "arguments": {"title": dynamic_title, "format": target_report_fmt},
            "summary": f"Generated {target_report_fmt.upper()}: {report_out.get('filename')}",
            "download_url": report_out.get("download_url"),
            "success": report_out.get("success", False),
            "duration_sec": report_out.get("duration_sec", 0)
        })
        if report_out.get("filename"):
            files_created.append({
                "filename": report_out.get("filename"),
                "format": report_out.get("format"),
                "download_url": report_out.get("download_url")
            })

    if not final_answer:
        try:
            lc_messages.append(HumanMessage(content="Synthesize all the tool execution results above into a clear, structured final answer. Highlight any generated documents or key findings."))
            synth_res = llm.invoke(lc_messages)
            final_answer = (synth_res.content or "").strip()
        except Exception:
            pass

    if not final_answer:
        parts = ["### 🤖 Sovereign Agent Multi-Step Execution Summary\n"]
        for step_i in tool_log:
            parts.append(f"- **Step {step_i['step']} ({step_i['tool']})**: {step_i.get('summary', 'Completed')}")
        if files_created:
            parts.append(f"\n✅ **Deliverables Generated**: {', '.join([f['filename'] for f in files_created])}")
        final_answer = "\n".join(parts)

    return {
        "answer": final_answer,
        "tool_log": tool_log,
        "sources": collected_sources,
        "files_created": files_created
    }
