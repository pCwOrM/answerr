"""Commercial layer (API 1.3.0): accounts, keys, metering, quotas, reviews, shadow mode, backtest,
members, plan requests, statements, admin, webhooks, retention and docs."""
import importlib
import json
import os
import re
import sys
import tempfile
import time

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADMIN = "adm_" + "z" * 30
H_ADMIN = {"X-Admin-Key": ADMIN}


@pytest.fixture()
def client(monkeypatch):
    tmp = tempfile.mkdtemp()
    monkeypatch.setenv("ANSWERR_API_KEYS", "itouch:" + "i" * 32)
    monkeypatch.setenv("ANSWERR_GATES_PATH", os.path.join(tmp, "gates.json"))
    monkeypatch.setenv("ANSWERR_RATELIMIT_DB", os.path.join(tmp, "rl.sqlite"))
    monkeypatch.setenv("ANSWERR_COMMERCE_DB", os.path.join(tmp, "commerce.sqlite"))
    monkeypatch.setenv("ANSWERR_ADMIN_KEY", ADMIN)
    monkeypatch.setenv("ANSWERR_WERR_PATH", os.environ.get("ANSWERR_WERR_PATH", os.path.join(ROOT, "..", "werr")))
    monkeypatch.delenv("RECAPTCHA_SECRET", raising=False)
    monkeypatch.delenv("SMTP_PASSWORD", raising=False)
    sys.path.insert(0, ROOT)
    import api_server
    api_server = importlib.reload(api_server)
    from commerce import mail, store
    store._key_cache.clear()
    mail.OUTBOX.clear()
    from fastapi.testclient import TestClient
    with TestClient(api_server.app) as c:
        c.mod, c.store, c.mail = api_server, store, mail
        yield c


def last_token(c):
    body = c.mail.OUTBOX[-1].get_content()
    return re.search(r"#login=(ans_link_[A-Za-z0-9_\-]+)", body).group(1)


def signup(c, email="founder@example.com", company="Örnek A.Ş."):
    r = c.post("/v1/auth/signup", json={"email": email, "company": company, "accept_terms": True, "kvkk_ack": True})
    assert r.status_code == 200, r.text
    v = c.post("/v1/auth/verify", json={"token": last_token(c)})
    assert v.status_code == 200, v.text
    b = v.json()
    return b["session"], b.get("api_key"), b["account_id"]


def auth(t):
    return {"Authorization": "Bearer " + t}


def decide(c, key, tool="read_invoice_summary", **extra):
    body = {"gate_id": "agent_mcp_guard", "state": {"tool_name": tool, "user_role": "member", "auth_status": True},
            "questions": {"allow": {"type": "noul", "text": "Allow?"}}}
    body.update(extra)
    return c.post("/v1/decide", json=body, headers=auth(key) if key else {})


def set_plan(c, acc, plan, **kw):
    r = c.post("/v1/admin/accounts/{}/plan".format(acc), json={"plan": plan, **kw}, headers=H_ADMIN)
    assert r.status_code == 200, r.text
    return r.json()["account"]


# ----------------------------------------------------------------------------- docs & catalog
def test_docs_live_under_v1(client):
    assert client.get("/v1/docs").status_code == 200
    spec = client.get("/v1/openapi.json").json()
    assert spec["info"]["version"] == "1.3.1"
    assert "/v1/account" in spec["paths"] and "/v1/backtest" in spec["paths"]
    assert client.get("/").json()["docs_url"] == "/v1/docs"


def test_plan_catalog_matches_pricing_page(client):
    plans = client.get("/v1/plans").json()["plans"]
    assert list(plans) == ["kesif", "gelistirici", "pro", "kurumsal"]
    html = open(os.path.join(ROOT, "pro", "pricing.html"), encoding="utf-8").read()
    for pid in ("gelistirici", "pro"):
        p = plans[pid]
        assert 'data-price-m="${}" data-price-y="${}"'.format(p["price_monthly"], p["price_yearly_per_month"]) in html
    assert "10.000 karar" in html and "250.000 karar" in html and "1.000.000 karar" in html
    assert "$0,15" in html and "$0,10" in html


# ----------------------------------------------------------------------------- sign-up / login
def test_signup_requires_consent_and_creates_owner_with_key(client):
    r = client.post("/v1/auth/signup", json={"email": "x@example.com", "accept_terms": True, "kvkk_ack": False})
    assert r.status_code == 400 and r.json()["error"] == "consent_required"
    sess, key, acc = signup(client)
    assert sess.startswith("ans_sess_") and key.startswith("ans_live_") and acc.startswith("acc_")
    me = client.get("/v1/account", headers=auth(sess)).json()["account"]
    assert me["plan"] == "kesif" and me["me"]["role"] == "owner" and me["usage"]["quota"] == 10000
    assert client.get("/v1/account", headers=auth(key)).json()["account"]["me"]["via"] == "api_key"


def test_link_is_single_use_and_login_does_not_enumerate(client):
    client.post("/v1/auth/signup", json={"email": "a@example.com", "accept_terms": True, "kvkk_ack": True})
    tok = last_token(client)
    assert client.post("/v1/auth/verify", json={"token": tok}).status_code == 200
    assert client.post("/v1/auth/verify", json={"token": tok}).json()["error"] == "invalid_link"
    n = len(client.mail.OUTBOX)
    r1 = client.post("/v1/auth/login", json={"email": "nobody@example.com"})
    r2 = client.post("/v1/auth/login", json={"email": "a@example.com"})
    assert r1.json() == r2.json() and len(client.mail.OUTBOX) == n + 2   # unknown address gets a sign-up hint, only in its own mailbox
    sess = client.post("/v1/auth/verify", json={"token": last_token(client)}).json()["session"]
    assert client.post("/v1/auth/logout", headers=auth(sess)).status_code == 200
    assert client.get("/v1/account", headers=auth(sess)).status_code == 401


# ----------------------------------------------------------------------------- metering & quota
def test_decisions_are_metered_and_logged(client):
    sess, key, acc = signup(client)
    r = decide(client, key, "send_payment", external_id="order-42")
    b = r.json()
    assert r.status_code == 200 and b["verdict"] == "REVIEW" and b["decision_id"].startswith("dec_")
    assert b["usage"]["decisions"] == 1 and r.headers["X-Answerr-Quota-Remaining"] == "9999"
    assert "review" not in b                                 # Keşif has no review queue
    decide(client, None)                                     # anonymous demo calls are not metered
    log = client.get("/v1/account/decisions", headers=auth(sess)).json()["decisions"]
    assert len(log) == 1 and log[0]["external_id"] == "order-42" and log[0]["state_fields"] == ["auth_status", "tool_name", "user_role"]
    series = client.get("/v1/account/usage?days=7", headers=auth(key)).json()
    assert series["usage"]["decisions"] == 1 and series["series"][-1]["review"] == 1


def test_quota_exceeded_returns_429_and_overage_rules(client, monkeypatch):
    from commerce import plans
    monkeypatch.setitem(plans.PLANS["kesif"], "quota", 2)
    sess, key, acc = signup(client)
    assert decide(client, key).status_code == 200
    assert decide(client, key).status_code == 200
    r = decide(client, key)
    assert r.status_code == 429 and r.json()["error"] == "quota_exceeded" and r.headers["Retry-After"]
    assert client.patch("/v1/account", json={"overage_enabled": True}, headers=auth(sess)).json()["error"] == "no_overage"
    monkeypatch.setitem(plans.PLANS["gelistirici"], "quota", 2)
    set_plan(client, acc, "gelistirici")
    assert decide(client, key).status_code == 429
    assert client.patch("/v1/account", json={"overage_enabled": True}, headers=auth(sess)).status_code == 200
    assert decide(client, key).status_code == 200


def test_quota_warning_mail_at_80_percent(client, monkeypatch):
    from commerce import plans
    monkeypatch.setitem(plans.PLANS["kesif"], "quota", 5)
    sess, key, acc = signup(client)
    for _ in range(4):
        decide(client, key)
    assert any("%80" in (m["Subject"] or "") for m in client.mail.OUTBOX)


# ----------------------------------------------------------------------------- reviews, shadow, backtest
def test_review_queue_and_resolution_on_pro(client):
    sess, key, acc = signup(client)
    set_plan(client, acc, "pro")
    b = decide(client, key, "send_payment", external_id="pay-7").json()
    rid = b["review"]["id"]
    q = client.get("/v1/reviews", headers=auth(sess)).json()["reviews"]
    assert q[0]["id"] == rid and q[0]["state"]["tool_name"] == "send_payment" and q[0]["external_id"] == "pay-7"
    r = client.post("/v1/reviews/{}/resolve".format(rid), json={"action": "approve", "note": "known customer"}, headers=auth(key))
    assert r.json()["review"]["status"] == "approved"
    assert client.post("/v1/reviews/{}/resolve".format(rid), json={"action": "reject"}, headers=auth(key)).status_code == 409
    assert client.get("/v1/reviews/" + rid, headers=auth(key)).json()["review"]["status"] == "approved"
    log = client.get("/v1/account/decisions", headers=auth(sess)).json()["decisions"]
    assert log[0]["observed"] == "ALLOW"
    assert "review" not in decide(client, key, "send_payment", enqueue_review=False).json()


def test_shadow_mode_is_a_paid_feature_and_reports_agreement(client):
    sess, key, acc = signup(client)
    assert decide(client, key, mode="shadow").json()["error"] == "feature_unavailable"
    set_plan(client, acc, "pro")
    decide(client, key, "read_invoice_summary", mode="shadow", observed_outcome="ALLOW")
    decide(client, key, "bulk_delete_users", mode="shadow", observed_outcome=True)
    d = decide(client, key, "send_payment", mode="shadow").json()
    assert "review" not in d                                  # shadow never queues
    client.post("/v1/decisions/{}/outcome".format(d["decision_id"]), json={"observed_outcome": "approved"}, headers=auth(key))
    rep = client.get("/v1/account/shadow-report", headers=auth(sess)).json()["report"]
    assert rep["decisions"] == 3 and rep["labelled"] == 3 and rep["agreement"] == round(1 / 3, 4)
    assert rep["stricter_than_you"] == 2 and rep["matrix"]["DENY"]["ALLOW"] == 1
    assert decide(client, key, observed_outcome="maybe").status_code == 400


def test_backtest_counts_records(client):
    sess, key, acc = signup(client)
    body = {"gate_id": "agent_mcp_guard", "records": [
        {"state": {"tool_name": "drop_table"}, "observed_outcome": "ALLOW", "id": "a"},
        {"state": {"tool_name": "list_orders", "user_role": "member"}, "observed_outcome": "ALLOW"},
        {"state": {"tool_name": "send_payment"}}]}
    assert client.post("/v1/backtest", json=body, headers=auth(key)).json()["error"] == "feature_unavailable"
    set_plan(client, acc, "pro")
    r = client.post("/v1/backtest", json=body, headers=auth(key)).json()
    assert r["records"] == 3 and r["agreement"] == 0.5 and r["differences"][0]["id"] == "a"
    assert r["matrix"]["REVIEW"]["unknown"] == 1
    assert client.get("/v1/account", headers=auth(key)).json()["account"]["usage"]["decisions"] == 3


# ----------------------------------------------------------------------------- keys, members, gates
def test_key_management_is_console_only_and_revocation_works(client):
    sess, key, acc = signup(client)
    assert client.post("/v1/account/keys", json={"label": "ci"}, headers=auth(key)).json()["error"] == "session_required"
    new = client.post("/v1/account/keys", json={"label": "ci"}, headers=auth(sess)).json()
    assert new["api_key"].startswith("ans_live_")
    r = client.post("/v1/account/keys", json={"label": "third"}, headers=auth(sess))
    assert r.status_code == 403 and r.json()["error"] == "key_limit"      # Keşif: 2 active keys
    assert client.delete("/v1/account/keys/" + new["key"]["id"], headers=auth(sess)).status_code == 200
    assert decide(client, new["api_key"]).json()["governed_by"] and "decision_id" not in decide(client, new["api_key"]).json()


def test_members_seats_and_reviewer_role(client):
    sess, key, acc = signup(client)
    r = client.post("/v1/account/members", json={"email": "rev@example.com", "role": "reviewer"}, headers=auth(sess))
    assert r.status_code == 403 and r.json()["error"] == "seat_limit"
    set_plan(client, acc, "pro")
    assert client.post("/v1/account/members", json={"email": "rev@example.com", "role": "reviewer"}, headers=auth(sess)).status_code == 200
    rsess = client.post("/v1/auth/verify", json={"token": last_token(client)}).json()["session"]
    me = client.get("/v1/account", headers=auth(rsess)).json()["account"]
    assert me["id"] == acc and me["me"]["role"] == "reviewer"
    assert client.get("/v1/account/keys", headers=auth(rsess)).status_code == 403
    assert client.get("/v1/reviews", headers=auth(rsess)).status_code == 200
    assert client.delete("/v1/account/members/rev@example.com", headers=auth(sess)).status_code == 200
    assert client.get("/v1/account", headers=auth(rsess)).status_code == 401


def test_custom_gate_limit_follows_plan(client):
    sess, key, acc = signup(client)
    gate = {"version": "1.0.0", "fields": ["amount"], "hard_rules": [
        {"id": "big", "field": "amount", "op": ">", "value": 1000, "effect": "REVIEW"}]}
    assert client.post("/v1/gates", json=dict(gate, gate_id="acme_one"), headers=auth(key)).status_code == 200
    r = client.post("/v1/gates", json=dict(gate, gate_id="acme_two"), headers=auth(key))
    assert r.status_code == 403 and r.json()["error"] == "gate_limit"
    b = client.post("/v1/gates/acme_one/decide", json={"state": {"amount": 5000}}, headers=auth(key)).json()
    assert b["verdict"] == "REVIEW" and b["decision_id"]


# ----------------------------------------------------------------------------- plans, statements, admin
def test_admin_requires_key(client):
    assert client.get("/v1/admin/metrics").status_code == 401
    assert client.get("/v1/admin/metrics", headers={"X-Admin-Key": "wrong" * 6}).status_code == 401


def test_plan_request_approval_statement_and_einvoice(client):
    sess, key, acc = signup(client)
    r = client.post("/v1/account/plan-request", json={"plan": "pro", "cycle": "monthly", "note": "200k/ay"}, headers=auth(sess)).json()
    assert r["status"] == "requested" and r["payment"]["provider"] == "manual"
    assert any("Plan talebi" in (m["Subject"] or "") for m in client.mail.OUTBOX)
    pend = client.get("/v1/admin/plan-requests", headers=H_ADMIN).json()["requests"]
    assert pend[0]["account_id"] == acc
    client.post("/v1/admin/plan-requests/{}/approve".format(pend[0]["id"]), headers=H_ADMIN)
    assert client.get("/v1/account", headers=auth(key)).json()["account"]["plan"] == "pro"
    m = client.get("/v1/admin/metrics", headers=H_ADMIN).json()["metrics"]
    assert m["mrr_cents"] == 9900 and m["accounts_by_plan"]["pro"] == 1
    period = client.store.period_of()
    st = client.post("/v1/admin/statements/generate", json={"period": period}, headers=H_ADMIN).json()["statements"]
    assert st[0]["total_cents"] == 9900 and st[0]["currency"] == "USD"
    marked = client.post("/v1/admin/statements/{}/mark".format(st[0]["id"]),
                         json={"status": "issued", "e_invoice_no": "GIB2026000000123"}, headers=H_ADMIN).json()["statement"]
    assert marked["status"] == "issued" and marked["e_invoice_no"] == "GIB2026000000123"
    mine = client.get("/v1/account/statements", headers=auth(sess)).json()
    assert mine["statements"][0]["e_invoice_no"] == "GIB2026000000123" and mine["current_period_estimate"]["base_cents"] == 9900


def test_overage_billing_per_started_thousand():
    sys.path.insert(0, ROOT)
    from commerce import plans
    assert plans.overage_cents("pro", 1) == 10 and plans.overage_cents("pro", 1000) == 10 and plans.overage_cents("pro", 1001) == 20
    assert plans.overage_cents("kesif", 5000) == 0
    assert plans.monthly_base_cents("pro", "yearly") == 8200 and plans.monthly_base_cents("gelistirici", "monthly") == 2900


def test_pilot_expires_to_kesif_and_suspension_blocks(client):
    sess, key, acc = signup(client)
    set_plan(client, acc, "pilot")
    assert client.get("/v1/account", headers=auth(key)).json()["account"]["plan"] == "pilot"
    with client.store.tx() as c:
        c.execute("UPDATE accounts SET plan_expires_at = ? WHERE id = ?", (time.time() - 1, acc))
    assert client.get("/v1/account", headers=auth(key)).json()["account"]["plan"] == "kesif"
    client.post("/v1/admin/accounts/{}/status".format(acc), json={"status": "suspended"}, headers=H_ADMIN)
    assert decide(client, key).json()["error"] == "account_suspended"


def test_admin_create_and_delete_account(client):
    r = client.post("/v1/admin/accounts", json={"email": "smoke@example.com", "plan": "pro"}, headers=H_ADMIN).json()
    key, acc = r["api_key"], r["account"]["id"]
    assert r["account"]["plan"] == "pro" and decide(client, key).status_code == 200
    assert client.delete("/v1/admin/accounts/" + acc, headers=H_ADMIN).status_code == 200
    assert client.get("/v1/account", headers=auth(key)).status_code == 401


def test_csv_export_is_plan_gated(client):
    sess, key, acc = signup(client)
    decide(client, key, "drop_table")
    assert client.get("/v1/account/decisions.csv", headers=auth(sess)).status_code == 403
    set_plan(client, acc, "pro")
    r = client.get("/v1/account/decisions.csv", headers=auth(sess))
    assert r.status_code == 200 and r.text.splitlines()[0].startswith("id,ts_iso,gate_id,verdict")
    assert ",DENY,tool_class:destructive," in r.text


def test_retention_purge(client):
    sess, key, acc = signup(client)
    decide(client, key)
    with client.store.tx() as c:
        c.execute("UPDATE decisions SET ts = ? WHERE account_id = ?", (time.time() - 8 * 86400, acc))
    assert client.post("/v1/admin/purge", headers=H_ADMIN).json()["removed"]["decisions"] == 1


# ----------------------------------------------------------------------------- webhooks
def test_webhook_url_rules_and_signature():
    sys.path.insert(0, ROOT)
    from commerce import store, webhooks
    for bad in ("http://example.com/h", "https://127.0.0.1/h", "https://10.0.2.2/h", "https://localhost/h"):
        with pytest.raises(store.CommerceError):
            webhooks.validate_url(bad)
    body = json.dumps({"event": "ping"}).encode()
    hdr = webhooks.sign("whsec_x", body, int(time.time()))
    assert webhooks.verify("whsec_x", body, hdr) and not webhooks.verify("whsec_y", body, hdr)
    assert not webhooks.verify("whsec_x", body, webhooks.sign("whsec_x", body, int(time.time()) - 900))


def test_webhooks_are_a_pro_feature(client):
    sess, key, acc = signup(client)
    r = client.patch("/v1/account", json={"webhook_url": "https://example.com/hook"}, headers=auth(sess))
    assert r.status_code == 403 and r.json()["feature"] == "webhooks"


def test_docs_compile_register_decide_flow(client):
    """The three-step example on pro/docs.html works as written."""
    sess, key, acc = signup(client)
    spec = client.post("/v1/policies/compile", json={"gate_id": "acme_payments",
                       "prompt": "5.000 doları aşan ödemeyi insana gönder. Başarısız deneme sayısı 3’ten fazlaysa reddet."}).json()["policy_spec"]
    r = client.post("/v1/gates", json=spec, headers=auth(key))
    assert r.status_code == 200, r.text
    b = client.post("/v1/gates/acme_payments/decide", json={"state": {"amount": 9200, "failed_attempts": 0}}, headers=auth(key)).json()
    assert b["verdict"] == "REVIEW" and b["trace"]["rule_id"] == "r1_amount_gt"
    b = client.post("/v1/gates/acme_payments/decide", json={"state": {"amount": 100, "failed_attempts": 5}}, headers=auth(key)).json()
    assert b["verdict"] == "DENY"


def test_instant_checkout_free_and_proforma(client):
    # 1. Instant free explore signup
    r = client.post("/v1/checkout/instant", json={
        "email": "instant_dev@example.com",
        "company": "FastDev Co",
        "plan": "kesif",
        "method": "free",
        "accept_terms": True,
        "kvkk_ack": True
    })
    assert r.status_code == 200, r.text
    b = r.json()
    assert b["status"] == "success"
    assert b["api_key"].startswith("ans_live_")
    assert b["session"].startswith("ans_sess_")

    # 2. Instant bank wire proforma invoice
    r_bank = client.post("/v1/checkout/instant", json={
        "email": "corp_buyer@example.com",
        "company": "Global Quant Inc.",
        "plan": "pro",
        "cycle": "monthly",
        "method": "bank",
        "currency": "USD",
        "accept_terms": True,
        "kvkk_ack": True
    })
    assert r_bank.status_code == 200, r_bank.text
    b_bank = r_bank.json()
    assert b_bank["status"] == "success"
    assert "invoice_pdf_url" in b_bank
    assert b_bank["invoice_no"].startswith("PRO-")

    # 3. Download proforma invoice PDF with the session
    pdf_r = client.get(b_bank["invoice_pdf_url"], headers=auth(b_bank["session"]))
    assert pdf_r.status_code == 200, pdf_r.text
    assert pdf_r.headers.get("content-type") == "application/pdf"
    assert pdf_r.content.startswith(b"%PDF")


def test_instant_checkout_never_hands_out_an_existing_account(client):
    s, key, acc = signup(client, email="victim@example.com")
    n = len(client.mail.OUTBOX)
    r = client.post("/v1/checkout/instant", json={"email": "victim@example.com", "plan": "kesif", "method": "free",
                                                  "accept_terms": True, "kvkk_ack": True})
    b = r.json()
    assert r.status_code == 200 and b["status"] == "login_link_sent"
    assert "session" not in b and "api_key" not in b
    assert len(client.mail.OUTBOX) == n + 1 and client.mail.OUTBOX[-1]["To"] == "victim@example.com"


def test_instant_checkout_requires_consent(client):
    r = client.post("/v1/checkout/instant", json={"email": "x@example.com", "plan": "kesif", "method": "free"})
    assert r.status_code == 400 and r.json()["error"] == "consent_required"


def test_instant_crypto_failure_creates_nothing(client, monkeypatch):
    from commerce import billing
    def boom(*a, **k):
        raise client.store.CommerceError(400, "transfer_not_found", "no transfer")
    monkeypatch.setattr(billing, "verify_crypto_payment", boom)
    q = client.post("/v1/checkout/crypto-quote", json={"email": "cr@example.com", "plan": "pro", "cycle": "monthly"}).json()
    r = client.post("/v1/checkout/instant", json={"email": "cr@example.com", "plan": "pro", "method": "crypto", "quote_id": q["quote_id"],
                                                  "tx_hash": "0x" + "b" * 64, "accept_terms": True, "kvkk_ack": True})
    assert r.status_code == 400 and r.json()["error"] == "transfer_not_found"
    assert client.store.member_of("cr@example.com") is None


def test_instant_crypto_success_and_replay(client, monkeypatch):
    from commerce import billing
    monkeypatch.setattr(billing, "verify_crypto_payment", lambda tx_hash, network, token, expected_usd, not_before=None: {
        "verified": True, "amount": expected_usd, "currency": "USDC", "network": "Base Mainnet", "tx_hash": tx_hash.lower()})
    q = client.post("/v1/checkout/crypto-quote", json={"email": "cr2@example.com", "plan": "pro", "cycle": "monthly"}).json()
    body = {"email": "cr2@example.com", "plan": "pro", "method": "crypto", "tx_hash": "0x" + "c" * 64, "quote_id": q["quote_id"],
            "accept_terms": True, "kvkk_ack": True}
    b = client.post("/v1/checkout/instant", json=body).json()
    assert b["status"] == "success" and b["plan"] == "pro" and b["invoice_no"].startswith("INV-")
    a = client.get("/v1/account", headers=auth(b["session"])).json()["account"]
    assert a["plan"] == "pro" and a["plan_expires_at"]
    note = next(m for m in client.mail.OUTBOX if "Ödeme alındı" in m["Subject"])
    assert "USDC" in note["Subject"] and "₺" not in note.get_content()
    q2 = client.post("/v1/checkout/crypto-quote", json={"email": "other@example.com", "plan": "pro", "cycle": "monthly"}).json()
    r = client.post("/v1/checkout/instant", json=dict(body, email="other@example.com", quote_id=q2["quote_id"]))
    assert r.status_code == 409 and client.store.member_of("other@example.com") is None
    # an existing customer is sent to the console instead of getting a sign-up quote
    assert client.post("/v1/checkout/crypto-quote", json={"email": "cr2@example.com", "plan": "pro"}).status_code == 409


def test_instant_card_goes_to_billing(client):
    b = client.post("/v1/checkout/instant", json={"email": "card@example.com", "plan": "gelistirici", "method": "card",
                                                  "company": "Kart A.Ş.", "accept_terms": True, "kvkk_ack": True}).json()
    assert b["status"] == "billing_required" and b["next"] == "billing" and b["session"].startswith("ans_sess_")
    a = client.get("/v1/account", headers=auth(b["session"])).json()["account"]
    assert a["plan"] == "kesif" and a["billing"]["legal_name"] == "Kart A.Ş."


def test_invoice_pdf_needs_the_owner(client):
    b = client.post("/v1/checkout/instant", json={"email": "bank@example.com", "plan": "pro", "method": "bank",
                                                  "accept_terms": True, "kvkk_ack": True}).json()
    url = b["invoice_pdf_url"]
    assert client.get(url).status_code == 401
    assert client.get(url, headers=auth(b["session"])).content.startswith(b"%PDF")
    assert client.get(url + "?token=" + b["session"]).status_code == 200
    s2, _, _ = signup(client, email="stranger@example.com")
    assert client.get(url, headers=auth(s2)).status_code == 404
    assert client.get(url, headers=H_ADMIN).status_code == 200
    # a bank transfer does not activate anything by itself
    assert client.get("/v1/account", headers=auth(b["session"])).json()["account"]["plan"] == "kesif"


def test_bank_transfer_mark_paid_and_approve_give_a_period(client):
    b = client.post("/v1/checkout/instant", json={"email": "wire@example.com", "plan": "pro", "method": "bank", "currency": "TRY",
                                                  "accept_terms": True, "kvkk_ack": True}).json()
    pid = b["payment_id"]
    r = client.post("/v1/admin/payments/{}/mark-paid".format(pid), json={"reference": "TEB-123"}, headers=H_ADMIN)
    assert r.status_code == 200 and r.json()["payment"]["status"] == "paid"
    a = client.get("/v1/account", headers=auth(b["session"])).json()["account"]
    assert a["plan"] == "pro" and a["plan_expires_at"] and a["plan_expires_at"] - time.time() < 32 * 86400
    assert client.get(b["invoice_pdf_url"], headers=auth(b["session"])).status_code == 200
    assert any("Ödeme alındı" in m["Subject"] for m in client.mail.OUTBOX)
    # approving a plain plan request also sets an expiry instead of an open-ended paid plan
    s, _, acc = signup(client, email="req@example.com")
    client.post("/v1/account/plan-request", json={"plan": "gelistirici", "cycle": "monthly"}, headers=auth(s))
    rid = client.get("/v1/admin/plan-requests", headers=H_ADMIN).json()["requests"][0]["id"]
    client.post("/v1/admin/plan-requests/{}/approve".format(rid), headers=H_ADMIN)
    a = client.get("/v1/account", headers=auth(s)).json()["account"]
    assert a["plan"] == "gelistirici" and a["plan_expires_at"]


def test_webhook_targets_must_be_public_and_redirects_are_not_followed(client, monkeypatch):
    from commerce import webhooks
    import socket
    for addr in ("100.64.1.1", "10.0.2.2", "127.0.0.1", "169.254.169.254", "::ffff:127.0.0.1"):
        monkeypatch.setattr(socket, "getaddrinfo", lambda h, p, proto=0, a=addr: [(0, 0, 0, "", (a, 443))])
        with pytest.raises(client.store.CommerceError):
            webhooks.validate_url("https://hook.example.com/x")
    assert any(isinstance(h, webhooks._NoRedirect) for h in webhooks._OPENER.handlers)


def test_csv_export_neutralises_formulas_and_mail_headers_survive_newlines(client):
    from commerce import mail
    m = mail._msg("a@example.com", "Plan talebi — Evil\r\nBcc: x@example.com", "body")
    assert "\n" not in m["Subject"] and "Bcc" not in str(m.keys())
    s, key, acc = signup(client, email="csv@example.com")
    client.post("/v1/admin/accounts/{}/plan".format(acc), json={"plan": "pro"}, headers=H_ADMIN)
    decide(client, key, external_id="=HYPERLINK(\"http://x\")")
    csv_txt = client.get("/v1/account/decisions.csv", headers=auth(s)).text
    assert "'=HYPERLINK" in csv_txt
