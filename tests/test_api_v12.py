"""API tests for v1.2.0: gate auth, persistence, inline policy, compiler, IP trust."""
import importlib
import json
import os
import sys
import tempfile

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY_A = "a" * 32
KEY_B = "b" * 32


@pytest.fixture()
def client(monkeypatch):
    tmp = tempfile.mkdtemp()
    monkeypatch.setenv("ANSWERR_API_KEYS", "acme:{},globex:{}".format(KEY_A, KEY_B))
    monkeypatch.setenv("ANSWERR_GATES_PATH", os.path.join(tmp, "gates.json"))
    monkeypatch.setenv("ANSWERR_RATELIMIT_DB", os.path.join(tmp, "rl.sqlite"))
    monkeypatch.setenv("ANSWERR_WERR_PATH", os.environ.get("ANSWERR_WERR_PATH", os.path.join(ROOT, "..", "werr")))
    monkeypatch.delenv("RECAPTCHA_SECRET", raising=False)
    sys.path.insert(0, ROOT)
    import api_server
    api_server = importlib.reload(api_server)
    from fastapi.testclient import TestClient
    with TestClient(api_server.app) as c:
        c.mod = api_server
        c.tmp = tmp
        yield c


def q(text="Should this tool call be permitted?"):
    return {"allow": {"type": "noul", "text": text}}


def test_agent_gate_denies_destructive_snake_case(client):
    r = client.post("/v1/decide", json={"gate_id": "agent_mcp_guard", "strict_policy": True,
                                         "state": {"tool_name": "bulk_delete_users", "user_role": "admin", "auth_status": True},
                                         "questions": q()})
    b = r.json()
    assert r.status_code == 200
    assert b["verdict"] == "DENY" and b["answers"]["allow"]["decision"] is False
    assert b["trace"]["rule_id"] == "tool_class:destructive"
    assert b["trace"]["policy_seal"].startswith("sha256:") and len(b["trace"]["policy_seal"]) == 71
    assert r.headers["X-Answerr-Verdict"] == "DENY"


@pytest.mark.parametrize("tool,verdict", [("send_payment", "REVIEW"), ("deploy_to_production", "REVIEW"),
                                          ("update_customer_records", "REVIEW"), ("read_invoice_summary", "ALLOW")])
def test_agent_gate_tool_classes(client, tool, verdict):
    b = client.post("/v1/gates/agent_mcp_guard/decide", json={
        "state": {"tool_name": tool, "user_role": "admin", "auth_status": True}, "questions": q()}).json()
    assert b["verdict"] == verdict, b["trace"]["candidates"]


def test_partial_ood_goes_to_review(client):
    b = client.post("/v1/decide", json={"strict_policy": True, "state": {"user_role": "admin", "coffee_temp": 90},
                                        "questions": q("Allow?")}).json()
    assert b["verdict"] == "REVIEW" and b["label"] == "ABSTAIN_REVIEW"
    assert b["trace"]["unrecognized_fields"] == ["coffee_temp"]


def test_question_wording_does_not_flip_verdict(client):
    pol = {"gate_id": "t", "fields": ["amount_usd"], "hard_rules": [{"id": "big", "field": "amount_usd", "op": ">", "value": 10000, "effect": "DENY"}]}
    a = client.post("/v1/decide", json={"policy": pol, "state": {"amount_usd": 50000}, "questions": q("Allow this payment?")}).json()
    b = client.post("/v1/decide", json={"policy": pol, "state": {"amount_usd": 50000}, "questions": q("Block this payment?")}).json()
    assert a["verdict"] == b["verdict"] == "DENY"
    assert a["answers"]["allow"]["decision"] is False and b["answers"]["allow"]["decision"] is True
    assert a["label"] == b["label"] == "DENIED"


def test_register_requires_key_and_owner(client):
    gate = {"gate_id": "acme_payments", "title": "x", "fields": ["amount_usd"],
            "hard_rules": [{"id": "big", "field": "amount_usd", "op": ">", "value": 100, "effect": "REVIEW"}]}
    assert client.post("/v1/gates", json=gate).status_code == 401
    r = client.post("/v1/gates", json=gate, headers={"X-API-Key": KEY_A})
    assert r.status_code == 200 and r.json()["policy_seal"].startswith("sha256:")
    # another tenant cannot overwrite or use it
    assert client.post("/v1/gates", json=gate, headers={"X-API-Key": KEY_B}).status_code == 403
    assert client.post("/v1/gates/acme_payments/decide", json={"state": {"amount_usd": 500}}).status_code == 401
    assert client.post("/v1/gates/acme_payments/decide", json={"state": {"amount_usd": 500}},
                       headers={"X-API-Key": KEY_B}).status_code == 403
    ok = client.post("/v1/gates/acme_payments/decide", json={"state": {"amount_usd": 500}, "questions": q()},
                     headers={"X-API-Key": KEY_A}).json()
    assert ok["verdict"] == "REVIEW"
    # built-ins are protected
    bi = dict(gate, gate_id="agent_mcp_guard")
    assert client.post("/v1/gates", json=bi, headers={"X-API-Key": KEY_A}).status_code == 409
    # persisted to disk
    with open(os.path.join(client.tmp, "gates.json")) as f:
        assert "acme_payments" in json.load(f)
    # listing shows own gates only
    assert any(g["gate_id"] == "acme_payments" for g in client.get("/v1/gates", headers={"X-API-Key": KEY_A}).json()["gates"])
    assert not any(g["gate_id"] == "acme_payments" for g in client.get("/v1/gates").json()["gates"])
    assert client.delete("/v1/gates/acme_payments", headers={"X-API-Key": KEY_B}).status_code == 403
    assert client.delete("/v1/gates/acme_payments", headers={"X-API-Key": KEY_A}).status_code == 200


def test_compile_does_not_register_and_matches_schema(client):
    prompt = ("Otonom AI ajanı veritabanında drop, delete veya truncate aracı çağırmak isterse reddet. "
              "İşlem tutarı 5000 dolar üzerinde ise insana gönder. Hatalı deneme sayısı 3 üstündeyse engelle.")
    sample = {"tool_name": "delete_customer_ledger", "amount_usd": 7200, "failed_attempts": 1, "auth_status": True}
    b = client.post("/v1/policies/compile", json={"prompt": prompt, "gate_id": "studio_draft", "sample_state": sample}).json()
    fields = {r["field"] for r in b["policy_spec"]["hard_rules"]}
    assert {"tool_name", "amount_usd", "failed_attempts"} <= fields
    assert b["registered"] is False and b["tests_passed"] == b["tests_total"]
    assert all(c["passed"] for c in b["checks"])
    assert "studio_draft" not in client.mod.GATE_STORE.gates
    d = client.post("/v1/decide", json={"policy": b["policy_spec"], "state": sample, "questions": q()}).json()
    assert d["verdict"] == "DENY"


def test_forwarded_for_spoofing_is_ignored(client):
    def req(peer, xff=None, real=None):
        r = type("R", (), {})()
        r.client = type("C", (), {"host": peer})()
        r.headers = {k: v for k, v in (("x-forwarded-for", xff), ("x-real-ip", real)) if v}
        return r
    ip = client.mod.client_ip
    # direct peer that is not a proxy: headers ignored
    assert ip(req("203.0.113.9", "1.2.3.4", "1.2.3.4")) == "203.0.113.9"
    # real chain observed on mechsrv: IIS appends client:port, Apache appends 10.0.2.2
    assert ip(req("127.0.0.1", "160.79.106.133:49152, 10.0.2.2")) == "160.79.106.133"
    # client-written XFF on the left is never used
    assert ip(req("127.0.0.1", "203.0.113.77, 160.79.106.143:49152, 10.0.2.2")) == "160.79.106.143"
    assert ip(req("127.0.0.1", "[2001:db8::5]:443, 10.0.2.2")) == "2001:db8::5"


def test_recaptcha_not_marked_active_without_verification(client):
    b = client.post("/v1/decide", json={"state": {"user_role": "member"}, "questions": q()},
                    headers={"X-Recaptcha-Token": "garbage"}).json()
    assert b["security"]["recaptcha"] in ("not_configured", "failed")
    assert b["security"]["rate_tier"] == "anonymous"


def test_invalid_policy_rejected(client):
    bad = {"hard_rules": [{"id": "x", "field": "a", "op": "regex", "value": ".*", "effect": "DENY"}]}
    assert client.post("/v1/decide", json={"policy": bad, "state": {"a": 1}}).status_code == 400


def test_legacy_preset_still_answers(client):
    b = client.post("/v1/decide", json={"domain": "robotics_industrial"}).json()
    assert b["status"] in ("success", "abstain_review")
    assert "continue_operation" in b["answers"]


def test_gate_store_shared_between_workers(client):
    path = os.path.join(client.tmp, "shared.json")
    w1, w2 = client.mod.GateStore(path), client.mod.GateStore(path)
    g = {"gate_id": "shared_gate", "tenant": "acme", "hard_rules": []}
    w1.put(g, "acme")
    assert w2.get("shared_gate") is not None
    assert w2.delete("shared_gate", "acme") is True
    assert w1.get("shared_gate") is None


def test_access_request(client, monkeypatch):
    sent = []
    monkeypatch.setenv("SMTP_PASSWORD", "x")
    monkeypatch.setenv("ANSWERR_ACCESS_LOG", os.path.join(client.tmp, "access.jsonl"))
    monkeypatch.setattr(client.mod.access_mailer, "_send", lambda msgs: sent.extend(msgs))
    assert client.post("/v1/access-request", json={"email": "not-an-email"}).status_code == 400
    r = client.post("/v1/access-request", json={"email": "ali@ornek.com.tr", "company": "Örnek A.Ş.", "lang": "tr"})
    assert r.status_code == 200 and r.json()["mailed"] is True
    assert sent[0]["To"] == "ask@answerr.me" and sent[0]["Reply-To"] == "ali@ornek.com.tr"
    assert sent[1]["To"] == "ali@ornek.com.tr" and "answerr" in sent[1]["From"]
    assert "\n" not in sent[0]["Subject"]
    # honeypot: accepted silently, nothing sent
    n = len(sent)
    assert client.post("/v1/access-request", json={"email": "bot@spam.io", "website": "x"}).status_code == 200
    assert len(sent) == n
    # per-IP limit (5 per hour)
    codes = [client.post("/v1/access-request", json={"email": "a@b.co"}).status_code for _ in range(3)]
    assert 429 in codes
    with open(os.path.join(client.tmp, "access.jsonl"), encoding="utf-8") as f:
        assert "ali@ornek.com.tr" in f.read()


def test_gate_store_rapid_alternation(client):
    path = os.path.join(client.tmp, "rapid.json")
    w1, w2 = client.mod.GateStore(path), client.mod.GateStore(path)
    for i in range(50):
        a, b = (w1, w2) if i % 2 else (w2, w1)
        a.put({"gate_id": "g%d" % i, "tenant": "acme", "hard_rules": []}, "acme")
        assert b.get("g%d" % i) is not None
        b.delete("g%d" % i, "acme")
        assert a.get("g%d" % i) is None


def test_rate_limit_shared_between_workers(client):
    w1 = client.mod.SlidingWindowLimiter(name="t")
    w2 = client.mod.SlidingWindowLimiter(name="t")
    assert w1.shared and w2.shared
    seen = []
    for i in range(6):
        ok, lim, rem, _ = (w1 if i % 2 else w2).check("ip:192.0.2.50", "verified")
        seen.append(rem)
    assert seen == [119, 118, 117, 116, 115, 114]   # one bucket across both "workers"
    ok, _, rem, _ = w1.check("ip:192.0.2.51", "verified")
    assert rem == 119
