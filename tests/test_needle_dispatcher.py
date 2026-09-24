"""
Unit tests for Needle 3 Dispatcher (tests/test_needle_dispatcher.py)
Tests tool wrapping, direct dispatch, confidence gating, and structured extraction.
"""

import pytest
import needle_dispatcher


def test_knowledge_search_dispatched():
    res = needle_dispatcher.dispatch("find safety SOP for refinery unit 4")
    assert isinstance(res, dict)
    assert "fallback" in res
    if not res["fallback"]:
        assert res["path"] == "needle3"
        assert "results" in res
    else:
        assert res["path"] == "needle3_fallback"


def test_no_exception_on_empty():
    res = needle_dispatcher.dispatch("")
    assert isinstance(res, dict)
    assert res["fallback"] is True


def test_offtopic_fallback():
    res = needle_dispatcher.dispatch("   ")
    assert isinstance(res, dict)
    assert res["fallback"] is True


def test_confidence_threshold_logic():
    assert needle_dispatcher.CONFIDENCE_THRESHOLD == 0.40


def test_structured_extraction_sop():
    sample_text = (
        "STANDARD OPERATING PROCEDURE: Pipeline Pressure Monitoring. "
        "Department: Safety & Operations. Version 1.2. Effective date: 2026-02-15. "
        "Scope: High pressure gas pipelines."
    )
    res = needle_dispatcher.extract_document(sample_text, "sop")
    assert res["extracted"] is True
    assert res["doc_type"] == "sop"
    assert "Pipeline Pressure" in res["fields"]["title"]
    assert "Safety & Operations" in res["fields"]["department"]


def test_structured_extraction_unknown_type():
    res = needle_dispatcher.extract_document("some document text", "unknown_schema")
    assert res["extracted"] is False
    assert "unknown_doc_type" in res["reason"]
