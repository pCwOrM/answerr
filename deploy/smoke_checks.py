"""Smoke checks against a running answerr API (canary or live). Exit code 0 = all passed.

    python deploy/smoke_checks.py http://127.0.0.1:8561
    python deploy/smoke_checks.py https://api.answerr.me
Uses only the standard library.
"""
import json
import sys
import time
import urllib.error
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8560").rstrip("/")
UA = {"User-Agent": "answerr-smoke/1.2.0"}
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
check("health 1.2.0", st == 200 and h and h.get("api_version") == "1.2.0", h and h.get("api_version"))

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

width = max(len(n) for n, _, _ in results)
for n, ok, d in results:
    print("  {}  {:<{w}}  {}".format("PASS" if ok else "FAIL", n, d, w=width))
failed = [n for n, ok, _ in results if not ok]
print("{} / {} passed".format(len(results) - len(failed), len(results)))
sys.exit(1 if failed else 0)
