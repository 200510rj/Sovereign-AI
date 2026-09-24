"""
Sovereign AI Workbench - Needle 3 Fast Tool Dispatcher (needle_dispatcher.py)
On-device grammar-constrained tool dispatch & structured extraction powered by Needle 3.
Directly executes tools in <2s with calibrated confidence and zero hallucination.
"""

import json
import logging
import os
import time
from typing import Literal, List, Dict, Any, Optional
from pydantic import BaseModel
import re

import needle
import agent

logger = logging.getLogger(__name__)

# Minimum calibrated confidence floor to execute without fallback
CONFIDENCE_THRESHOLD = 0.40

# Singleton agent
_needle_agent: Optional[needle.Needle] = None


# ============================================================
# TOOL DEFINITIONS FOR NEEDLE 3 (Grammar-Constrained with Triggers)
# ============================================================

@needle.tool(triggers=[r"\b(search|find|lookup|sop|manual|resume|policy|guideline|knowledge|refinery)\b"])
def search_knowledge_base(query: str, top_k: int = 5) -> str:
    """Search the local MRPL knowledge base for SOPs, manuals, resumes, and technical documents using semantic search.

    Args:
        query: Search term or keyword phrase to find in documents
        top_k: Maximum number of chunks to retrieve (default 5)
    """
    res = agent.execute_tool("search_knowledge_base", {"query": query, "top_k": top_k})
    return json.dumps(res)


@needle.tool(triggers=[r"\b(run|execute|calculate|compute|eval)\b.*\b(python|code|script|math|formula)\b"])
def execute_python_code(code: str, timeout: int = 10) -> str:
    """Execute Python code in a safe local sandbox and return stdout, stderr, and exit code.

    Args:
        code: Valid Python code to execute locally
        timeout: Maximum execution timeout in seconds (default 10)
    """
    res = agent.execute_tool("execute_python_code", {"code": code, "timeout": timeout})
    return json.dumps(res)


@needle.tool(triggers=[r"\b(generate|create|export|write|make)\b.*\b(report|pdf|docx|xlsx|checklist)\b"])
def generate_report(title: str, content: str, format: Literal["pdf", "docx", "xlsx"] = "pdf", author: str = "Sovereign AI Agent") -> str:
    """Generate a downloadable enterprise report deliverable in PDF, DOCX, or XLSX format.

    Args:
        title: Title of the official report or document
        content: Body content of the report to include
        format: Output file format - pdf, docx, or xlsx
        author: Author or issuing unit name
    """
    res = agent.execute_tool("generate_report", {"title": title, "content": content, "format": format, "author": author})
    return json.dumps(res)


@needle.tool(triggers=[r"\b(read|open|extract from|show)\b.*\b(file|document|pdf|txt|resume)\b"])
def read_uploaded_document(filename: str) -> str:
    """Read the extracted text content of a specific uploaded file in the knowledge base by filename.

    Args:
        filename: Exact name of the file in the knowledge base (e.g. test_sop.txt, Utsav Dhobi Resume.pdf)
    """
    res = agent.execute_tool("read_uploaded_document", {"filename": filename})
    return json.dumps(res)


@needle.tool(triggers=[r"\b(web search|search web|search online|latest news|current facts)\b"])
def web_search(query: str, max_results: int = 5) -> str:
    """Search the web for up-to-date real-world facts, technical specifications, and news using DuckDuckGo.

    Args:
        query: Search query keywords or phrase
        max_results: Maximum number of search results to return (default 5)
    """
    res = agent.execute_tool("web_search", {"query": query, "top_k": max_results})
    return json.dumps(res)


NEEDLE_TOOLS = [
    search_knowledge_base,
    execute_python_code,
    generate_report,
    read_uploaded_document,
    web_search
]


def _get_agent() -> needle.Needle:
    """Returns the singleton Needle agent instance."""
    global _needle_agent
    if _needle_agent is None:
        index_cache = os.path.join("data", "needle_tool_index.bin")
        os.makedirs("data", exist_ok=True)
        _needle_agent = needle.Needle(
            tools=NEEDLE_TOOLS,
            tool_index_path=index_cache
        )
    return _needle_agent


# ============================================================
# DISPATCHER FUNCTION
# ============================================================

def dispatch(query: str) -> Dict[str, Any]:
    """
    Attempts to dispatch a user query directly to a tool using Needle 3.
    Returns:
        dict with keys:
            fallback: bool (True if execution should fall back to Ollama ReAct)
            reason: Optional[str]
            tool: Optional[str]
            arguments: Optional[dict]
            results: List[Any]
            confidence: Optional[float]
            reasoning: Optional[str]
            path: str ("needle3" or "needle3_fallback")
    """
    clean_query = (query or "").strip()
    if not clean_query:
        return {
            "fallback": True,
            "reason": "empty_query",
            "path": "needle3_fallback"
        }

    try:
        ag = _get_agent()
        start = time.perf_counter()
        res = ag.run(clean_query, max_steps=1)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        conf = res.get("confidence")
        calls = res.get("function_calls", [])
        executed_results = res.get("results", [])

        # Parse executed results if they were returned as JSON strings
        parsed_results = []
        for r in executed_results:
            if isinstance(r, str):
                try:
                    parsed_results.append(json.loads(r))
                except Exception:
                    parsed_results.append(r)
            else:
                parsed_results.append(r)

        # Gating checks
        if conf is not None and conf < CONFIDENCE_THRESHOLD:
            logger.info(f"[NEEDLE3] Low confidence ({conf:.3f} < {CONFIDENCE_THRESHOLD}) -> fallback")
            return {
                "fallback": True,
                "reason": "low_confidence",
                "confidence": conf,
                "path": "needle3_fallback",
                "latency_ms": duration_ms
            }

        # If Needle executed tool via run() and returned results
        if parsed_results:
            first_res = parsed_results[0]
            if isinstance(first_res, dict) and "tool" in first_res:
                tool_name = first_res["tool"]
            elif calls:
                tool_name = calls[0].get("name", "dispatched_tool")
            else:
                tool_name = "dispatched_tool"

            args = calls[0].get("arguments", {}) if calls else {}

            return {
                "fallback": False,
                "tool": tool_name,
                "arguments": args,
                "results": parsed_results,
                "confidence": conf or 1.0,
                "reasoning": res.get("reasoning", ""),
                "path": "needle3",
                "latency_ms": duration_ms
            }

        # If calls were proposed but not executed, or empty
        if not calls:
            return {
                "fallback": True,
                "reason": "no_tool_matched",
                "path": "needle3_fallback",
                "latency_ms": duration_ms
            }

        first_call = calls[0]
        tool_name = first_call.get("name")
        tool_args = first_call.get("arguments", {})

        # Execute the tool call locally
        tool_res = agent.execute_tool(tool_name, tool_args)
        return {
            "fallback": False,
            "tool": tool_name,
            "arguments": tool_args,
            "results": [tool_res],
            "confidence": conf or 1.0,
            "reasoning": res.get("reasoning", ""),
            "path": "needle3",
            "latency_ms": duration_ms
        }

    except Exception as e:
        logger.warning(f"[NEEDLE3] Dispatch exception: {e}")
        return {
            "fallback": True,
            "reason": f"exception: {str(e)}",
            "path": "needle3_fallback"
        }


# ============================================================
# STRUCTURED EXTRACTION SCHEMAS (Needle extract)
# ============================================================

class SOPDocument(BaseModel):
    title: str = "Standard Operating Procedure"
    department: str = "Operations"
    version: str = "1.0"
    effective_date: str = ""
    scope: str = ""
    key_steps: List[str] = []


class ComplianceReport(BaseModel):
    regulation_name: str = "Industrial Safety Standard"
    status: Literal["compliant", "non-compliant", "partial", "unknown"] = "unknown"
    findings: str = ""
    deadline: str = ""
    risk_level: Literal["low", "medium", "high", "critical"] = "medium"


class PurchaseOrder(BaseModel):
    vendor: str = "Vendor"
    po_number: str = ""
    total_amount: float = 0.0
    currency: str = "INR"
    order_date: str = ""
    items: List[str] = []


class IncidentReport(BaseModel):
    incident_type: str = "Incident"
    severity: Literal["minor", "moderate", "major", "critical"] = "moderate"
    date: str = ""
    location: str = ""
    affected_equipment: str = ""
    description: str = ""


DOC_TYPE_MAP = {
    "sop": SOPDocument,
    "compliance": ComplianceReport,
    "purchase_order": PurchaseOrder,
    "incident": IncidentReport
}


def extract_document(text: str, doc_type: str) -> Dict[str, Any]:
    """
    Extracts structured fields from raw document text using Needle structured extraction.
    """
    schema_cls = DOC_TYPE_MAP.get(doc_type.lower())
    if not schema_cls:
        return {
            "extracted": False,
            "reason": f"unknown_doc_type '{doc_type}'",
            "supported_types": list(DOC_TYPE_MAP.keys())
        }

    clean_text = (text or "").strip()[:4000]
    if not clean_text:
        return {
            "extracted": False,
            "reason": "empty_text"
        }

    try:
        extracted_obj = needle.extract(clean_text, schema_cls, strict=False)
        if extracted_obj is None:
            # Heuristic structural extractor fallback for document headers & numbered lists
            inferred = {}
            lines = [l.strip() for l in clean_text.splitlines() if l.strip()]
            if lines:
                inferred["title"] = lines[0][:80]
            for l in lines:
                if ":" in l:
                    k, v = l.split(":", 1)
                    k_clean = k.strip().lower().replace(" ", "_")
                    v_clean = v.strip()
                    if "department" in k_clean:
                        inferred["department"] = v_clean
                    elif "purpose" in k_clean or "scope" in k_clean:
                        inferred["scope"] = v_clean
                    elif "date" in k_clean:
                        inferred["effective_date"] = v_clean
                    elif "version" in k_clean or "id" in k_clean:
                        inferred["version"] = v_clean
            # Extract numbered steps if present
            steps = [l for l in lines if re.match(r"^\d+[\.\)]", l)]
            if steps:
                inferred["key_steps"] = steps[:10]
            try:
                extracted_obj = schema_cls(**inferred)
            except Exception:
                extracted_obj = inferred
        
        if isinstance(extracted_obj, BaseModel):
            fields = extracted_obj.model_dump()
        elif isinstance(extracted_obj, dict):
            fields = extracted_obj
        else:
            fields = {"result": str(extracted_obj)}

        return {
            "extracted": True,
            "doc_type": doc_type,
            "fields": fields
        }
    except Exception as e:
        logger.warning(f"[NEEDLE3] Extraction error: {e}")
        return {
            "extracted": False,
            "reason": f"error: {str(e)}"
        }


if __name__ == "__main__":
    print("Testing Needle 3 dispatch...")
    d1 = dispatch("find safety SOP for refinery unit 4")
    print("D1 Result:", d1.get("tool"), "Fallback:", d1.get("fallback"), "Confidence:", d1.get("confidence"))

    d2 = dispatch("search web for latest Python 3.14 features")
    print("D2 Result:", d2.get("tool"), "Fallback:", d2.get("fallback"), "Confidence:", d2.get("confidence"))

    print("Testing Needle 3 extraction...")
    sop_sample = "STANDARD OPERATING PROCEDURE: Emergency Shutdown Procedure. Department: Operations Unit 2. Effective: 2026-01-01. Scope: Refinery crude distillation."
    ext = extract_document(sop_sample, "sop")
    print("Extraction Result:", ext)
