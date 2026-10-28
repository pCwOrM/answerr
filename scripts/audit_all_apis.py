import os
import sys
import json
import time
import urllib.request
import urllib.error

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def test_all():
    endpoints = [
        ("answerr Health (/v1/health)", "GET", "https://api.answerr.me/v1/health", None),
        ("werr Parameters Catalog (/v1/werr/parameters)", "GET", "https://api.answerr.me/v1/werr/parameters", None),
        ("answerr Decide Gate (/v1/decide)", "POST", "https://api.answerr.me/v1/decide", {
            "gate_id": "agent_mcp_guard",
            "state": {"tool_name": "read_db_metrics", "user_role": "agent"}
        }),
        ("werr System-One Wire (/v1/systemone)", "POST", "https://api.answerr.me/v1/systemone", {
            "state": {"speed": 1.5, "distance": 0.8},
            "questions": {"action": {"type": "noul", "instructions": "Is path clear?"}}
        }),
        ("OpenAI Chat Completions (/v1/chat/completions)", "POST", "https://api.answerr.me/v1/chat/completions", {
            "model": "werr-reflex-v1",
            "messages": [{"role": "user", "content": "Evaluate risk of transaction 450 USD"}]
        }),
        ("Werracle Node Status (/werracle/status)", "GET", "https://api.answerr.me/werracle/status", None),
        ("Radar Overview (api.werracle.com)", "GET", "https://api.werracle.com/v1/radar/overview", None)
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) answerr-audit/2.0",
        "Content-Type": "application/json"
    }

    print("=" * 80)
    print(" LIVE API CONNECTIVITY & PARAMETER AUDIT")
    print("=" * 80)

    for name, method, url, body in endpoints:
        t0 = time.time()
        try:
            data = json.dumps(body).encode("utf-8") if body else None
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=12) as resp:
                dur = (time.time() - t0) * 1000
                res = resp.read().decode("utf-8", errors="ignore")
                try:
                    rj = json.loads(res)
                    sample = list(rj.keys())[:5]
                    summary = f"Status {resp.status} | JSON Keys: {sample}"
                except Exception:
                    summary = f"Status {resp.status} | {len(res)} bytes"
                print(f"[PASS] {name:42} | {dur:6.1f} ms | {summary}")
        except Exception as e:
            dur = (time.time() - t0) * 1000
            print(f"[FAIL] {name:42} | {dur:6.1f} ms | ERROR: {e}")

    print("=" * 80)

if __name__ == "__main__":
    test_all()
