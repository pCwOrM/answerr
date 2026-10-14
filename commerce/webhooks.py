"""Signed outbound webhooks (review.created, review.resolved, quota.warning).

Signature header (Stripe-style):
    X-Answerr-Signature: t=<unix seconds>,v1=<hex HMAC-SHA256(secret, "<t>.<raw body>")>
Receivers should recompute the HMAC and reject timestamps older than 5 minutes.

Only https:// URLs that resolve to public addresses are accepted (no SSRF into private networks).
Delivery runs in a background thread with 3 attempts (0 s, 2 s, 8 s); each outcome is logged.
"""
from __future__ import annotations

import hashlib
import hmac
import ipaddress
import json
import socket
import threading
import time
import urllib.parse
import urllib.request
from typing import Any, Dict

from . import store as S

TIMEOUT = 5.0


def validate_url(url: str) -> None:
    u = urllib.parse.urlparse(url)
    if u.scheme != "https" or not u.hostname:
        raise S.CommerceError(400, "bad_webhook_url", "Webhook URL must start with https://")
    if len(url) > 500:
        raise S.CommerceError(400, "bad_webhook_url", "Webhook URL is too long.")
    try:
        infos = socket.getaddrinfo(u.hostname, u.port or 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        raise S.CommerceError(400, "bad_webhook_url", "Webhook host does not resolve.")
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast or ip.is_unspecified:
            raise S.CommerceError(400, "bad_webhook_url", "Webhook host must be a public address.")


def sign(secret: str, body: bytes, ts: int) -> str:
    mac = hmac.new(secret.encode(), str(ts).encode() + b"." + body, hashlib.sha256).hexdigest()
    return "t={},v1={}".format(ts, mac)


def verify(secret: str, body: bytes, header: str, tolerance: int = 300) -> bool:
    """Reference verifier (also used in tests and shown in the docs)."""
    try:
        parts = dict(p.split("=", 1) for p in header.split(","))
        ts = int(parts["t"])
    except Exception:
        return False
    if abs(time.time() - ts) > tolerance:
        return False
    return hmac.compare_digest(sign(secret, body, ts).split("v1=")[1], parts.get("v1", ""))


def _deliver(account_id: str, url: str, secret: str, event: str, payload: Dict[str, Any]) -> None:
    body = json.dumps({"event": event, "created": int(time.time()), "data": payload}, ensure_ascii=False).encode("utf-8")
    status, err, attempt = None, None, 0
    for attempt, delay in enumerate((0, 2, 8), start=1):
        if delay:
            time.sleep(delay)
        try:
            validate_url(url)
            ts = int(time.time())
            req = urllib.request.Request(url, data=body, method="POST", headers={
                "Content-Type": "application/json", "User-Agent": "answerr-webhooks/1.0",
                "X-Answerr-Event": event, "X-Answerr-Signature": sign(secret, body, ts)})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                status = r.status
            if 200 <= status < 300:
                err = None
                break
            err = "HTTP {}".format(status)
        except urllib.error.HTTPError as e:
            status, err = e.code, "HTTP {}".format(e.code)
        except Exception as e:  # network errors are logged, never raised into the request path
            err = type(e).__name__
    try:
        S.conn().execute("INSERT INTO webhook_deliveries (account_id, ts, event, url, status_code, attempts, error) "
                         "VALUES (?, ?, ?, ?, ?, ?, ?)", (account_id, time.time(), event, url, status, attempt, err))
    except Exception:
        pass


def send(account: Dict[str, Any], event: str, payload: Dict[str, Any], sync: bool = False) -> None:
    url, secret = account.get("webhook_url"), account.get("webhook_secret")
    if not url or not secret:
        return
    if sync:
        _deliver(account["id"], url, secret, event, payload)
    else:
        threading.Thread(target=_deliver, args=(account["id"], url, secret, event, payload), daemon=True).start()


def recent(account_id: str, limit: int = 50):
    return [dict(r) for r in S.conn().execute(
        "SELECT ts, event, url, status_code, attempts, error FROM webhook_deliveries WHERE account_id = ? ORDER BY id DESC LIMIT ?",
        (account_id, limit)).fetchall()]
