"""Policy kernel tests: hand-labelled expectations plus Python/JS parity."""
import json
import os
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import policy_kernel as K  # noqa: E402

with open(os.path.join(ROOT, "tests", "policy_vectors.json"), encoding="utf-8") as f:
    VECTORS = json.load(f)
with open(os.path.join(ROOT, "policies", "builtin_gates.json"), encoding="utf-8") as f:
    GATES = json.load(f)


def _policy(v):
    return GATES[v["gate"]] if isinstance(v.get("gate"), str) else v.get("gate")


def _run(v):
    r = K.evaluate(v["state"], _policy(v), bool(v.get("strict")))
    return r, K.answer_question(r, v.get("question"))


@pytest.mark.parametrize("v", VECTORS, ids=[v["name"] for v in VECTORS])
def test_expectations(v):
    r, a = _run(v)
    assert r["verdict"] == v["expect_verdict"], (r["rule_id"], r["reason"])
    if "expect_rule" in v:
        assert r["rule_id"] == v["expect_rule"], r["candidates"]
    if "expect_decision" in v:
        assert a["decision"] == v["expect_decision"]
    assert a["label"] == K.LABELS[r["verdict"]]


def test_question_text_never_changes_verdict():
    for v in VECTORS:
        p = _policy(v)
        base = K.evaluate(v["state"], p, bool(v.get("strict")))["verdict"]
        for q in ["Allow?", "Block this?", "Devam edelim mi?", "Engellensin mi?", ""]:
            r = K.evaluate(v["state"], p, bool(v.get("strict")))
            assert r["verdict"] == base
            a = K.answer_question(r, q)
            if base == "REVIEW":
                assert a["decision"] is None


def test_seal_is_full_sha256_and_stable():
    s1 = K.policy_seal(GATES["agent_mcp_guard"])
    s2 = K.policy_seal(dict(GATES["agent_mcp_guard"], policy_seal="x"))
    assert s1 == s2 and s1.startswith("sha256:") and len(s1) == 7 + 64
    changed = dict(GATES["agent_mcp_guard"], version="9.9.9")
    assert K.policy_seal(changed) != s1


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_python_js_parity():
    out = subprocess.run(["node", os.path.join(ROOT, "tests", "kernel_dump.js")],
                         capture_output=True, text=True, check=True).stdout
    js = json.loads(out)
    for v, jr in zip(VECTORS, js["results"]):
        r, a = _run(v)
        assert jr["name"] == v["name"]
        assert json.loads(json.dumps(r)) == jr["result"], v["name"]
        assert json.loads(json.dumps(a)) == jr["answer"], v["name"]
    for g, seal in js["seals"].items():
        assert K.policy_seal(GATES[g]) == seal, g
