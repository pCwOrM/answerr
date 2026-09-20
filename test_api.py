import urllib.request
import json
import ssl
import time
import sys

# Ensure UTF-8 output on all platforms
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def test_api(name, url, payload=None, method=None):
    print(f"\n==================================================")
    print(f"[*] TEST: {name}")
    print(f"[*] URL : {url}")
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Answerr-TestClient/1.0"
    }
    
    t0 = time.perf_counter()
    try:
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers=headers, method=method or "POST")
        else:
            req = urllib.request.Request(url, headers=headers, method=method or "GET")
            
        with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            content = resp.read().decode("utf-8")
            print(f"[+] HTTP STATUS : {resp.status} (Roundtrip: {elapsed_ms:.2f} ms)")
            try:
                parsed = json.loads(content)
                print(f"[+] JSON RESPONSE:\n{json.dumps(parsed, indent=2, ensure_ascii=False)}")
            except Exception:
                print(f"[+] RAW RESPONSE:\n{content[:500]}")
    except Exception as e:
        print(f"[-] ERROR: {e}")

if __name__ == "__main__":
    # 1. Health Check via api.answerr.me:4431
    test_api(
        "Health & Zero-VRAM Status (api.answerr.me)",
        "https://api.answerr.me:4431/v1/health"
    )

    # 2. Presets Catalog via api.answerr.me:4431
    test_api(
        "Preset Scenarios Catalog (api.answerr.me)",
        "https://api.answerr.me:4431/v1/presets"
    )

    # 3. Simple Instant Reflex Decision via api.answerr.me:4431
    test_api(
        "Instant Reflex Decision (Single Question)",
        "https://api.answerr.me:4431/v1/decide",
        payload={
            "question": "Allow privileged API transaction?",
            "state": {
                "user_role": "admin",
                "failed_attempts": 0,
                "req_frequency": 1.2
            }
        }
    )

    # 4. Multi-Question Typed Decision (werr / System-1 Specification)
    test_api(
        "Multi-Question Typed Decision (Noul + Choice + Score)",
        "https://api.answerr.me:4431/v1/decide",
        payload={
            "domain": "api_security",
            "state": {
                "user_role": "attacker",
                "failed_attempts": 15,
                "req_frequency": 120.0
            }
        }
    )

    # 5. OpenAI-compatible /v1/chat/completions adapter
    test_api(
        "OpenAI SDK Compatible Adapter (/v1/chat/completions)",
        "https://api.answerr.me:4431/v1/chat/completions",
        payload={
            "model": "werr-reflex-v1",
            "messages": [
                {"role": "system", "content": "You are a reflex decision engine."},
                {"role": "user", "content": "Member user attempting 1 payment with 0 errors."}
            ]
        }
    )
