"""
Sovereign AI Workbench - Web Search Module (web_search_tool.py)
Rebuilt Web Search feature powered by Python, LangChain APIs, and DuckDuckGo Search (DDGS).
"""

import logging
import re
from typing import List, Dict, Any
from duckduckgo_search import DDGS
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchResults, DuckDuckGoSearchRun

logger = logging.getLogger(__name__)

def search_web(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Executes a web search query using DuckDuckGo Search (DDGS) and LangChain APIs.
    Returns a list of structured result dicts with keys: title, snippet, href.
    """
    clean_query = (query or "").strip()
    if not clean_query:
        return []

    results = []

    # 1. Primary Engine: DDGS text search
    try:
        with DDGS() as ddgs:
            raw_results = list(ddgs.text(clean_query, max_results=max_results))
        
        for item in raw_results:
            results.append({
                "title": item.get("title", ""),
                "snippet": item.get("body", ""),
                "href": item.get("href", ""),
                "url": item.get("href", "")
            })
    except Exception as e:
        logger.warning(f"DDGS search failed: {e}. Falling back to LangChain DuckDuckGoSearchResults.")

    # 2. Secondary Engine: LangChain DuckDuckGoSearchResults fallback
    if not results:
        try:
            lc_tool = DuckDuckGoSearchResults(num_results=max_results)
            output = lc_tool.invoke(clean_query)
            
            # Parse LangChain formatted output: snippet: ..., title: ..., link: ...
            matches = re.findall(r'snippet:\s*(.*?),\s*title:\s*(.*?),\s*link:\s*(https?://[^\s,]+)', str(output))
            for snip, title, link in matches:
                results.append({
                    "title": title.strip(),
                    "snippet": snip.strip(),
                    "href": link.strip(),
                    "url": link.strip()
                })
        except Exception as e:
            logger.error(f"LangChain search fallback failed: {e}")

    return results[:max_results]

@tool("web_search")
def web_search_tool(query: str, max_results: int = 5) -> str:
    """Search the web for up-to-date real-time information, news, facts, and specs using DuckDuckGo Search."""
    results = search_web(query, max_results=max_results)
    if not results:
        return f"No search results found for query: '{query}'."
    
    formatted_parts = []
    for idx, r in enumerate(results, 1):
        formatted_parts.append(
            f"[{idx}] {r.get('title', 'No Title')}\n"
            f"URL: {r.get('href', '')}\n"
            f"Snippet: {r.get('snippet', '')}"
        )
    return "\n\n".join(formatted_parts)

def get_langchain_web_search_tool():
    """Returns the LangChain tool instance for agent integration."""
    return web_search_tool

if __name__ == "__main__":
    test_query = "latest Python release features"
    res = search_web(test_query, max_results=3)
    print(f"Search results for '{test_query}':", res)

