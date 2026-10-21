"""Smoke checks against a running answerr API (canary or live). Exit code 0 = all passed.

    python deploy/smoke_checks.py http://127.0.0.1:8561
    python deploy/smoke_checks.py https://api.answerr.me
Uses only the standard library.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8560").rstrip("/")
EXPECT = os.environ.get("ANSWERR_EXPECT_VERSION", "1.3.1")
ADMIN = os.environ.get("ANSWERR_ADMIN_KEY", "")
UA = {"User-Agent": "answerr-smoke/" + EXPECT}
results = []


def call(method, path, body=None, headers=None):
    time.sleep(0.2)  # stay under the anonymous 10 req/s burst limit
    data = json.dumps(body).encode() if body is not None else None
    h = dict(UA, **(headers or {}))
    if data is not None:
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE + path, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, json.loads(r.read().decode() or "null"), dict(r.headers)
    except urllib.error.HTTPError as e:
        try:
            payload = json.loads(e.read().decode() or "null")
        except Exception:
            payload = None
        return e.code, payload, dict(e.headers)


def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))


Q = {"q": {"type": "noul", "text": "Should this tool call be permitted?"}}

st, h, _ = call("GET", "/v1/health")
check("health " + EXPECT, st == 200 and h and h.get("api_version") == EXPECT, h and h.get("api_version"))

cases = [
    ("bulk_delete_users", {"tool_name": "bulk_delete_users", "user_role": "admin", "auth_status": True}, "DENY"),
    ("drop_production_table", {"tool_name": "drop_production_table", "user_role": "agent_autonomous", "amount_usd": 12500}, "DENY"),
    ("read_invoice_summary", {"tool_name": "read_invoice_summary", "user_role": "admin", "auth_status": True, "failed_attempts": 0}, "ALLOW"),
    ("send_payment", {"tool_name": "send_payment", "user_role": "member", "auth_status": True, "amount_usd": 7200}, "REVIEW"),
    ("deploy_to_production", {"tool_name": "deploy_to_production", "user_role": "admin", "auth_status": True}, "REVIEW"),
    ("unknown field", {"tool_name": "read_invoice_summary", "user_role": "admin", "coffee_temp": 90}, "REVIEW"),
    ("get_api_key", {"tool_name": "get_api_key", "user_role": "admin", "auth_status": True}, "DENY"),
]
for name, state, want in cases:
    st, b, hd = call("POST", "/v1/decide", {"gate_id": "agent_mcp_guard", "strict_policy": True, "state": state, "questions": Q})
    got = b and b.get("verdict")
    check("agent gate: " + name, st == 200 and got == want, "{} (want {})".format(got, want))

pol = {"gate_id": "smoke", "fields": ["amount_usd"], "hard_rules": [{"id": "big", "field": "amount_usd", "op": ">", "value": 10000, "effect": "DENY"}]}
st, a, _ = call("POST", "/v1/decide", {"policy": pol, "state": {"amount_usd": 50000}, "questions": {"q": {"type": "noul", "text": "Allow?"}}})
st2, b, _ = call("POST", "/v1/decide", {"policy": pol, "state": {"amount_usd": 50000}, "questions": {"q": {"type": "noul", "text": "Block this?"}}})
def _dec(x):
    return ((x or {}).get("answers") or {}).get("q", {}).get("decision")


check("wording does not flip verdict", bool(a and b) and a.get("verdict") == b.get("verdict") == "DENY"
      and _dec(a) is False and _dec(b) is True,
      "{} / {}".format((a or {}).get("verdict", (a or {}).get("label")), (b or {}).get("verdict", (b or {}).get("label"))))

st, b, _ = call("POST", "/v1/gates", {"gate_id": "smoke_hijack", "title": "x", "hard_rules": []})
check("gate registration needs API key", st == 401, st)

st, b, _ = call("POST", "/v1/policies/compile", {
    "prompt": "Ajan silme aracı çağırırsa reddet. Tutar 5000 dolar üzerinde ise insana gönder.",
    "sample_state": {"tool_name": "delete_customer_ledger", "amount_usd": 7200}})
check("compiler", st == 200 and b and b.get("registered") is False and b.get("tests_passed") == b.get("tests_total"),
      b and "{}/{} tests".format(b.get("tests_passed"), b.get("tests_total")))

st, b, _ = call("POST", "/v1/access-request", {"email": "not-an-email"})
check("access form validates e-mail", st == 400, st)

st, b, _ = call("POST", "/v1/chat/completions", {"messages": [{"role": "user", "content": "status check"}]})
check("chat/completions still answers", st == 200 and b and b.get("choices"), st)

st, b, _ = call("POST", "/v1/decide", {"domain": "robotics_industrial"})
check("legacy preset still answers", st == 200 and b and "continue_operation" in (b.get("answers") or {}), st)

# ---------------------------------------------------------------- 1.3.0 commercial layer
if EXPECT >= "1.3.0":
    st, b, _ = call("GET", "/v1/openapi.json")
    check("openapi under /v1", st == 200 and b and "/v1/account" in (b.get("paths") or {}), st)
    st, b, _ = call("GET", "/v1/plans")
    check("plan catalog", st == 200 and b and list((b.get("plans") or {}))[:3] == ["kesif", "gelistirici", "pro"], st)
    st, b, _ = call("GET", "/v1/account")
    check("account needs auth", st == 401, st)
    if ADMIN:
        AH = {"X-Admin-Key": ADMIN}
        email = "smoke+{}@answerr.me".format(int(time.time()))
        st, b, _ = call("POST", "/v1/admin/accounts", {"email": email, "company": "smoke", "plan": "pro"}, AH)
        key, acc = (b or {}).get("api_key"), ((b or {}).get("account") or {}).get("id")
        check("admin onboards a Pro account", st == 200 and key and acc, st)
        if key:
            KH = {"Authorization": "Bearer " + key}
            st, d, hd = call("POST", "/v1/gates/agent_mcp_guard/decide", {"state": {"tool_name": "send_payment", "user_role": "member"},
                                                                          "external_id": "smoke"}, KH)
            rid = ((d or {}).get("review") or {}).get("id")
            check("metered decision + review queued", st == 200 and d.get("decision_id") and rid and d["usage"]["decisions"] == 1,
                  (d or {}).get("usage"))
            st, r, _ = call("POST", "/v1/reviews/{}/resolve".format(rid), {"action": "approve", "note": "smoke"}, KH)
            check("review resolved by API key", st == 200 and r["review"]["status"] == "approved", st)
            st, d, _ = call("POST", "/v1/decide", {"gate_id": "agent_mcp_guard", "mode": "shadow", "observed_outcome": "ALLOW",
                                                   "state": {"tool_name": "drop_table"}}, KH)
            st, r, _ = call("GET", "/v1/account/shadow-report?days=1", None, KH)
            check("shadow report", st == 200 and r["report"]["stricter_than_you"] >= 1, st)
            st, r, _ = call("POST", "/v1/account/keys", {"label": "x"}, KH)
            check("key management is console-only", st == 403, st)
        if acc:
            st, _, _ = call("DELETE", "/v1/admin/accounts/" + acc, None, AH)
            check("smoke account removed", st == 200, st)
            st, _, _ = call("GET", "/v1/account", None, {"Authorization": "Bearer " + (key or "")})
            # other workers may still hold the key in their 30 s cache; the account itself is gone either way (401 or 404)
            check("deleted account's key is dead", st in (401, 404), st)

# ---------------------------------------------------------------- 1.3.1 card payments (no money moves here)
if EXPECT >= "1.3.1":
    class _NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None
    def raw(method, path, data=None, headers=None):
        time.sleep(0.2)
        req = urllib.request.Request(BASE + path, data=data, method=method, headers=dict(UA, **(headers or {})))
        try:
            r = urllib.request.build_opener(_NoRedirect).open(req, timeout=15)
            return r.status, dict(r.headers)
        except urllib.error.HTTPError as e:
            return e.code, dict(e.headers)
    st, b, _ = call("GET", "/v1/plans")
    check("plans expose card_payments + TRY", st == 200 and "card_payments" in (b or {}) and b["plans"]["pro"].get("price_monthly_try"), st)
    st, hd = raw("POST", "/v1/billing/iyzico/callback", b"token=SMOKE-FAKE", {"Content-Type": "application/x-www-form-urlencoded"})
    loc = hd.get("Location") or hd.get("location") or ""
    check("forged callback is not reported as paid", st == 303 and "payment=unknown" in loc and "token=" not in loc, loc)
    st, b, _ = call("POST", "/v1/billing/iyzico/webhook", {"token": "SMOKE-FAKE", "status": "SUCCESS"})
    check("forged webhook is answered 200 and ignored", st == 200, st)
    st, b, _ = call("POST", "/v1/account/checkout", {"plan": "pro"})
    check("checkout needs a session", st == 401, st)
    if ADMIN:
        st, b, _ = call("GET", "/v1/admin/payments", None, {"X-Admin-Key": ADMIN})
        check("admin payments list", st == 200 and isinstance((b or {}).get("payments"), list), st)

width = max(len(n) for n, _, _ in results)
for n, ok, d in results:
    print("  {}  {:<{w}}  {}".format("PASS" if ok else "FAIL", n, d, w=width))
failed = [n for n, ok, _ in results if not ok]
print("{} / {} passed".format(len(results) - len(failed), len(results)))
sys.exit(1 if failed else 0)
