"""
Unit tests for Laya Gateway (tests/test_laya_gateway.py)
Tests classification, script routing, urgency scoring, and off-topic filtering.
"""

import pytest
import laya_gateway


def test_english_knowledge_intent():
    res = laya_gateway.predict_query("find safety SOP for refinery unit 4")
    assert res["intent"] == "knowledge_search"
    assert res["is_mrpl_relevant"] >= 0.8
    assert res["language"] == "english"


def test_english_offtopic_rejected():
    res = laya_gateway.predict_query("tell me a joke")
    assert res["intent"] == "off_topic"
    assert res["is_mrpl_relevant"] < 0.3


def test_hindi_routes_multilingual():
    res = laya_gateway.predict_query("रिफाइनरी के दस्तावेज़ खोजें")
    assert res["language"] == "multilingual"
    assert res["is_mrpl_relevant"] >= 0.5


def test_report_intent():
    res = laya_gateway.predict_query("generate a PDF report on compliance status")
    assert res["intent"] == "report_generation"
    assert res["is_mrpl_relevant"] >= 0.8


def test_urgency_critical():
    res = laya_gateway.predict_query("URGENT: pipeline pressure alarm triggered")
    assert res["urgency"] == 2
    assert res["urgency_label"] == "critical or blocking"


def test_fallback_on_empty_string():
    res = laya_gateway.predict_query("")
    assert isinstance(res, dict)
    assert "intent" in res
    assert "is_mrpl_relevant" in res


def test_latency_under_100ms():
    res = laya_gateway.predict_query("what are the daily refinery production guidelines?")
    assert res["latency_ms"] < 100.0
