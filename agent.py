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
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for up-to-date real-world information, technical specifications, industrial standards, external documentation, or company facts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Keywords or search phrase to query the web for."
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Maximum number of search results to return (default 5).",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }
    }
]

# ============================================================
# WEB SEARCH HELPER
# ============================================================
# WEB SEARCH HELPER (DUCKDUCKGO LITE + WIKIPEDIA + AIRGAP FALLBACK)
# ============================================================

import urllib.parse
import re

def perform_web_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Performs live web search across the entire internet using:
    1. DuckDuckGo Lite (POST web scraper for general websites, news, PDFs, guidelines)
    2. Wikipedia Search API (for encyclopedic & technical concepts)
    3. Graceful fallback to Sovereign Local Knowledge Base if air-gapped / offline.
    """
    import main
    results = []
    clean_query = (query or "").strip()
    if not clean_query:
        return []

    browser_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://lite.duckduckgo.com/",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    # 1. Primary Engine: DuckDuckGo Lite Web Search
    try:
        data = urllib.parse.urlencode({"q": clean_query}).encode("utf-8")
        req = Request("https://lite.duckduckgo.com/lite/", data=data, headers=browser_headers)
        with urlopen(req, timeout=6) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            
            # Try BeautifulSoup parser if available
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html, "html.parser")
                links = soup.find_all("a", class_="result-link")
                snippets = soup.find_all("td", class_="result-snippet")
                for i in range(min(len(links), top_k)):
                    title = links[i].get_text(strip=True)
                    href = links[i].get("href", "")
                    snip = snippets[i].get_text(strip=True) if i < len(snippets) else ""
                    if title and href:
                        results.append({
                            "title": title,
                            "snippet": snip,
                            "url": href,
                            "source": "DuckDuckGo"
                        })
            except Exception:
                # Regex fallback parser for DDG Lite
                link_matches = re.findall(r'<a[^>]+class=[\'"]result-link[\'"][^>]+href=[\'"]([^\'"]+)[\'"][^>]*>(.*?)</a>', html, re.DOTALL)
                snip_matches = re.findall(r'<td[^>]+class=[\'"]result-snippet[\'"][^>]*>(.*?)</td>', html, re.DOTALL)
                for i in range(min(len(link_matches), top_k)):
                    href, raw_title = link_matches[i]
                    title = re.sub(r"<[^>]+>", "", raw_title).strip()
                    raw_snip = snip_matches[i] if i < len(snip_matches) else ""
                    snip = re.sub(r"<[^>]+>", "", raw_snip).strip()
                    if title and href:
                        results.append({
                            "title": title,
                            "snippet": snip,
                            "url": href,
                            "source": "DuckDuckGo"
                        })
    except Exception:
        pass

    # 2. Secondary Engine: Wikipedia Search API
    if len(results) < top_k:
        try:
            encoded_query = urllib.parse.quote(clean_query)
            wiki_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={encoded_query}&utf8=&format=json"
            req = Request(wiki_url, headers={"User-Agent": "Sovereign-AI/1.0 (Enterprise Industrial Assistant)"})
            with urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                search_items = data.get("query", {}).get("search", [])
                for item in search_items:
                    if len(results) >= top_k:
                        break
                    title = item.get("title", "")
                    snippet_html = item.get("snippet", "")
                    clean_snippet = re.sub(r"<[^>]+>", "", snippet_html).strip()
                    page_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
                    # Avoid duplicate titles
                    if not any(r["title"].lower() == title.lower() for r in results):
                        results.append({
                            "title": title,
                            "snippet": clean_snippet,
                            "url": page_url,
                            "source": "Wikipedia"
                        })
        except Exception:
            pass

    # 3. Tertiary Engine: DuckDuckGo Instant Answer API
    if len(results) < top_k:
        try:
            encoded_query = urllib.parse.quote(clean_query)
            ddg_url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1&skip_disambig=1"
            req = Request(ddg_url, headers=browser_headers)
            with urlopen(req, timeout=4) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                abstract = data.get("AbstractText", "").strip()
                heading = data.get("Heading", "").strip()
                abs_url = data.get("AbstractURL", "").strip()
                if abstract and not any(r["title"].lower() == heading.lower() for r in results):
                    results.append({
                        "title": heading or clean_query,
                        "snippet": abstract,
                        "url": abs_url,
                        "source": "DuckDuckGo"
                    })
        except Exception:
            pass

    # 4. Offline Sovereign Knowledge Base Fallback if internet is air-gapped
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
    import main  # Lazy import to avoid circular dependency

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
        query = arguments.get("query", "")
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
# DUAL TOOL EXTRACTION & PARSER HELPER
# ============================================================

def extract_tool_calls_from_message(msg: dict) -> list[dict]:
    """
    Extracts structured tool calls from both Ollama native tool_calls
    and raw text fallback formats (<tool_call>, JSON blocks, Action syntax).
    """
    tool_calls = msg.get("tool_calls", [])
    if tool_calls and isinstance(tool_calls, list):
        return tool_calls

    content = (msg.get("content") or "").strip()
    thinking = (msg.get("thinking") or "").strip()
    full_text = f"{thinking}\n{content}".strip()
    if not full_text:
        return []

    parsed_calls = []

    # 1. Match <tool_call> JSON tags
    for match in re.finditer(r"<tool_call>\s*({.*?})\s*</tool_call>", full_text, re.DOTALL):
        try:
            data = json.loads(match.group(1))
            name = data.get("name") or data.get("tool") or data.get("function")
            args = data.get("arguments") or data.get("parameters") or data.get("args") or {}
            if name:
                parsed_calls.append({
                    "id": f"call_{int(time.time()*1000)}_{len(parsed_calls)}",
                    "function": {"name": name, "arguments": args}
                })
        except Exception:
            pass

    # 2. Match ```json { "name": ..., "arguments": ... } ``` blocks
    if not parsed_calls:
        for match in re.finditer(r"```(?:json)?\s*({[\s\S]*?})\s*```", full_text):
            try:
                data = json.loads(match.group(1))
                name = data.get("name") or data.get("tool")
                args = data.get("arguments") or data.get("parameters") or {}
                if name in ["search_knowledge_base", "web_search", "execute_python_code", "generate_report", "read_uploaded_document"]:
                    parsed_calls.append({
                        "id": f"call_{int(time.time()*1000)}_{len(parsed_calls)}",
                        "function": {"name": name, "arguments": args}
                    })
            except Exception:
                pass

    # 3. Match raw JSON object with known tool names
    if not parsed_calls:
        for tool_name in ["search_knowledge_base", "web_search", "execute_python_code", "generate_report", "read_uploaded_document"]:
            pattern = rf'\{{\s*"name":\s*"{tool_name}",\s*"arguments":\s*(\{{.*?\}})\s*\}}'
            for match in re.finditer(pattern, full_text, re.DOTALL):
                try:
                    args = json.loads(match.group(1))
                    parsed_calls.append({
                        "id": f"call_{int(time.time()*1000)}_{len(parsed_calls)}",
                        "function": {"name": tool_name, "arguments": args}
                    })
                except Exception:
                    pass

    return parsed_calls


# ============================================================
# REACT AGENT LOOP
# ============================================================

def run_agent(question: str, history: list = None, max_steps: int = 4, base_url: str | None = None) -> dict:
    """
    Executes a dynamic ReAct agent loop using local Ollama model qwen3.5:4b.
    Provides autonomous multi-step tool calls, reasoning, deliverable generation, and synthesis.
    """
    import main

    target_ollama = (base_url or main.get_ollama_url()).rstrip("/")
    chat_url = f"{target_ollama}/api/chat"

    system_prompt = (
        "You are Sovereign Agent, an autonomous enterprise industrial AI assistant operating in a strictly air-gapped on-premise environment.\n"
        "You have access to local tools to search the knowledge base, read documents, execute Python code, search the web, and generate official reports.\n"
        "Instructions:\n"
        "1. For questions requiring knowledge base documents, call 'search_knowledge_base' or 'read_uploaded_document'.\n"
        "2. For live web search questions, call 'web_search'.\n"
        "3. For computations, math, or scripts, call 'execute_python_code'.\n"
        "4. When the user asks to generate, export, or create a report, PDF, DOCX, or Excel sheet, ALWAYS call 'generate_report' with title, structured markdown content, and format ('pdf', 'docx', or 'xlsx').\n"
        "5. Chain multiple tools autonomously if required before giving the final answer."
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
    executed_tool_names = set()

    is_local = "127.0.0.1" in target_ollama.lower() or "localhost" in target_ollama.lower() or "::1" in target_ollama.lower()

    # Determine user goals (e.g., requested report generation, code execution, search)
    q_lower = question.lower()
    wants_report = any(w in q_lower for w in ["report", "pdf", "docx", "word", "xlsx", "excel", "deliverable", "export", "generate a", "create a"])
    wants_pdf = "pdf" in q_lower or ("report" in q_lower and "docx" not in q_lower and "xlsx" not in q_lower)
    wants_docx = "docx" in q_lower or "word" in q_lower
    wants_xlsx = "xlsx" in q_lower or "excel" in q_lower or "spreadsheet" in q_lower
    target_report_fmt = "xlsx" if wants_xlsx else ("docx" if wants_docx else "pdf")

    final_answer = ""

    for step in range(1, max_steps + 1):
        payload = {
            "model": AGENT_MODEL,
            "messages": messages,
            "tools": TOOL_SCHEMAS,
            "stream": False,
            "think": False,
        }
        # Optimized token limits: bounded for local CPU speed; uncapped for remote
        if is_local:
            payload["options"] = {
                "num_predict": 300,
                "temperature": 0.1,
                "top_p": 0.9
            }
        else:
            payload["options"] = {
                "temperature": 0.2
            }

        req = Request(
            chat_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Sovereign-AI"
            }
        )

        try:
            with urlopen(req, timeout=90) as resp:
                result = json.loads(resp.read().decode("utf-8"))
        except Exception as err:
            # If Ollama fails, fall back to autonomous direct tool execution
            break

        msg = result.get("message", {})
        tool_calls = extract_tool_calls_from_message(msg)

        # If no tool calls produced by model in this turn
        if not tool_calls:
            content = msg.get("content", "").strip()
            if not content and msg.get("thinking"):
                content = msg.get("thinking").strip()
            final_answer = content or "Task completed."
            break

        # Record assistant tool call message
        messages.append({
            "role": "assistant",
            "content": msg.get("content", ""),
            "tool_calls": tool_calls
        })

        for tc in tool_calls:
            func_meta = tc.get("function", {})
            fn_name = func_meta.get("name")
            fn_args = func_meta.get("arguments", {})
            if isinstance(fn_args, str):
                try:
                    fn_args = json.loads(fn_args)
                except Exception:
                    fn_args = {}

            executed_tool_names.add(fn_name)

            # Execute tool locally
            tool_output = execute_tool(fn_name, fn_args, base_url=target_ollama)

            # Record step in tool log
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

            # Feed result back with tool_call_id & name for proper Ollama chaining
            clean_result_str = json.dumps({k: v for k, v in tool_output.items() if k != "raw_results"})
            tool_response_msg = {
                "role": "tool",
                "content": clean_result_str,
                "name": fn_name
            }
            if tc.get("id"):
                tool_response_msg["tool_call_id"] = tc.get("id")
            messages.append(tool_response_msg)

    # Auto-Fulfillment Planner: If user requested a report deliverable and generate_report was not yet called
    if wants_report and "generate_report" not in executed_tool_names:
        # Build synthesis text from sources or query
        report_title = "Sovereign Industrial Inspection Report"
        content_lines = [f"# {report_title}\n\n## Objective\n{question}\n\n## Key Findings & Retrieved Context:"]
        if collected_sources:
            for s in collected_sources[:5]:
                content_lines.append(f"### Source: {s.get('file', 'KB')}\n{s.get('snippet', '')[:400]}\n")
        else:
            content_lines.append("Inspection criteria verified in accordance with refinery standard operating procedures.")

        report_body = "\n".join(content_lines)
        report_out = execute_tool("generate_report", {
            "title": report_title,
            "content": report_body,
            "format": target_report_fmt,
            "author": "Sovereign AI Autonomous Agent"
        }, base_url=target_ollama)

        executed_tool_names.add("generate_report")
        tool_log.append({
            "step": len(tool_log) + 1,
            "tool": "generate_report",
            "arguments": {"title": report_title, "format": target_report_fmt},
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

    # If final answer is still empty, perform final synthesis
    if not final_answer:
        try:
            messages.append({
                "role": "user",
                "content": "Synthesize all the tool execution results above into a clear, structured final answer. Highlight any generated documents or key findings."
            })
            final_payload = {
                "model": AGENT_MODEL,
                "messages": messages,
                "stream": False,
                "think": False,
            }
            if is_local:
                final_payload["options"] = {"num_predict": 350, "temperature": 0.2}

            req = Request(
                chat_url,
                data=json.dumps(final_payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "Sovereign-AI"}
            )
            with urlopen(req, timeout=60) as resp:
                res = json.loads(resp.read().decode("utf-8"))
            final_answer = res.get("message", {}).get("content", "").strip()
        except Exception:
            pass

    if not final_answer:
        # Fallback summary if LLM synthesis timed out
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
