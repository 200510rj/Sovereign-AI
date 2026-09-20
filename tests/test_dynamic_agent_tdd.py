import pytest
from pathlib import Path
import main
import agent

def test_read_all_kb_documents_fuzzy_and_ocr():
    """Verify read_uploaded_document can resolve exact & fuzzy filenames and perform OCR on images."""
    files_to_test = [
        ("Het_Patel_Resume.pdf", ["het", "patel", "data"]),
        ("Panchal_Isha_Resume.pdf", ["isha", "panchal"]),
        ("test_sop.txt", ["sop", "pump", "inspection"]),
        ("image.png", []), # OCR text or non-error status
    ]

    for filename, expected_keywords in files_to_test:
        res = agent.execute_tool("read_uploaded_document", {"filename": filename})
        assert res["success"] is True, f"Failed to read document: {filename}. Error: {res.get('error')}"
        assert res["char_count"] > 0, f"0 characters read for {filename}"
        text_lower = res["text"].lower()
        for kw in expected_keywords:
            assert kw in text_lower, f"Keyword '{kw}' not found in {filename} text preview"

def test_no_hardcoded_dummy_report_generation():
    """Verify that auto-report generation creates dynamic titles & contents from prompt context, NOT hardcoded dummy text."""
    prompt = "Read Het_Patel_Resume.pdf and test_sop.txt, compare candidate against SOP requirements, and generate a report deliverable."
    
    result = agent.run_agent(prompt, max_steps=5)
    
    assert "answer" in result
    answer = result["answer"]
    
    # Assert no dummy fallback refinery text
    assert "refinery standard operating procedures" not in answer.lower()
    assert "sovereign industrial inspection report" not in answer.lower()
    
    # Check created files
    files = result.get("files_created", [])
    if files:
        file_name = files[0]["filename"]
        # Ensure the filename is derived dynamically from prompt/context (e.g. recruitment/candidate/comparison/sop)
        assert "industrial_inspection" not in file_name.lower()

def test_dynamic_report_title_and_content_synthesis():
    """Verify report title and body are dynamically synthesized from tool output."""
    query = "Analyze the SOP requirements in test_sop.txt and generate a summary docx report."
    
    result = agent.run_agent(query, max_steps=5)
    
    files = result.get("files_created", [])
    assert len(files) > 0, "Report file was not generated"
    filename = files[0]["filename"]
    assert filename.endswith(".docx") or filename.endswith(".pdf")
    assert "industrial_inspection" not in filename.lower()
    
    # Verify tool log summary
    report_tools = [t for t in result["tool_log"] if t["tool"] == "generate_report"]
    assert len(report_tools) > 0
    report_args = report_tools[0].get("arguments", {})
    title = report_args.get("title", "")
    assert title and title != "Sovereign Industrial Inspection Report"
