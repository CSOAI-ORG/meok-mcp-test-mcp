"""Unit tests for meok-mcp-test-mcp."""
from __future__ import annotations

import os
import sys
import pathlib

os.environ.setdefault("MEOK_HMAC_SECRET", "test-only-secret")

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from server import (  # noqa: E402
    run_golden_diff,
    validate_tool_schema,
    validate_server_json,
    diff_server_json,
    check_idempotency_static,
    generate_test_template,
    run_test_suite,
    sign_test_report,
)


# ---------- golden diff ----------

def test_golden_diff_matches():
    out = run_golden_diff({"a": 1}, {"a": 1})
    assert out["matches"] is True
    assert out["diff"] == ""


def test_golden_diff_detects_change():
    out = run_golden_diff({"a": 1}, {"a": 2})
    assert out["matches"] is False
    assert '"a": 1' in out["diff"]
    assert '"a": 2' in out["diff"]


# ---------- tool schema ----------

def test_valid_tool():
    out = validate_tool_schema({"name": "my_tool", "description": "Does a thing nicely."})
    assert out["valid"] is True
    assert out["issues"] == []


def test_missing_name():
    out = validate_tool_schema({"description": "x" * 10})
    assert out["valid"] is False
    assert any("name" in i for i in out["issues"])


def test_bad_name_chars():
    out = validate_tool_schema({"name": "my tool!", "description": "x" * 10})
    assert out["valid"] is False


def test_description_too_short():
    out = validate_tool_schema({"name": "ok", "description": "hi"})
    assert out["valid"] is False
    assert any("too short" in i for i in out["issues"])


def test_description_too_long():
    out = validate_tool_schema({"name": "ok", "description": "x" * 2000})
    assert out["valid"] is False
    assert any("too long" in i for i in out["issues"])


def test_invalid_input_schema_type():
    out = validate_tool_schema({
        "name": "ok", "description": "x" * 10,
        "inputSchema": {"type": "not-a-real-type"},
    })
    assert out["valid"] is False


# ---------- server.json ----------

def test_valid_server_json():
    sj = {
        "name": "io.github.X/Y",
        "version": "1.0.0",
        "description": "test",
        "tools": [{"name": "do_thing", "description": "Does a thing well."}],
    }
    out = validate_server_json(sj)
    assert out["valid"] is True


def test_missing_required_fields():
    out = validate_server_json({"name": "x"})
    assert out["valid"] is False
    assert len(out["issues"]) >= 2  # version + description missing


def test_invalid_tool_inside():
    sj = {
        "name": "x", "version": "1.0.0", "description": "y",
        "tools": [{"description": "no name here"}],
    }
    out = validate_server_json(sj)
    assert out["valid"] is False
    assert out["tools"][0]["valid"] is False


# ---------- schema drift ----------

def test_no_drift_same_doc():
    sj = {"name": "x", "version": "1"}
    d = diff_server_json(sj, sj)
    assert d["breaking"] is False
    assert d["added"] == []
    assert d["removed"] == []


def test_added_field_non_breaking():
    old = {"name": "x"}
    new = {"name": "x", "homepage": "https://example.com"}
    d = diff_server_json(old, new)
    assert d["breaking"] is False
    assert "$.homepage" in d["added"]


def test_removed_field_breaking():
    old = {"name": "x", "version": "1.0.0"}
    new = {"name": "x"}
    d = diff_server_json(old, new)
    assert d["breaking"] is True
    assert "$.version" in d["removed"]


def test_type_change_breaking():
    old = {"version": "1.0.0"}
    new = {"version": 1}
    d = diff_server_json(old, new)
    assert d["breaking"] is True


# ---------- idempotency ----------

def test_idempotent_identical_samples():
    out = check_idempotency_static([{"a": 1}, {"a": 1}, {"a": 1}])
    assert out["idempotent"] is True
    assert out["distinct_results"] == 1


def test_non_idempotent_diverging_samples():
    out = check_idempotency_static([{"a": 1}, {"a": 2}])
    assert out["idempotent"] is False
    assert out["distinct_results"] == 2


def test_needs_two_samples():
    out = check_idempotency_static([{"a": 1}])
    assert out["idempotent"] is False


# ---------- template + run_test_suite + sign ----------

def test_template_generated():
    out = generate_test_template()
    assert "filename" in out and out["filename"].endswith(".py")
    assert "def test_" in out["content"]


def test_run_suite_passes_clean_server():
    sj = {
        "name": "x", "version": "1.0.0", "description": "y",
        "tools": [{"name": "ok_tool", "description": "Does it well."}],
    }
    out = run_test_suite(sj)
    assert out["grade"] in ("A", "B")
    assert out["passed"] >= 2


def test_run_suite_with_drift_flags_breaking():
    new_sj = {"name": "x", "version": "1.0.0", "description": "y"}
    baseline = {**new_sj, "homepage": "https://a"}  # baseline had homepage, new removed it
    out = run_test_suite(new_sj, schema_drift_baseline=baseline)
    drift_result = [r for r in out["results"] if r["name"] == "schema_drift"][0]
    assert drift_result["passed"] is False


def test_sign_test_report_returns_signature_and_badge():
    raw = run_test_suite({"name": "x", "version": "1", "description": "y"})
    sealed = sign_test_report(raw)
    assert sealed["signature"] != "unsigned-no-key-configured"
    assert "shields.io" in sealed["badge_url"]
    assert sealed["issuer"] == "meok-mcp-test-mcp"
