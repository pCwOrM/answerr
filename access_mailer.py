"""
Early-access requests from answerr.me/pro -> ask@answerr.me (SMTP over SSL).

Configuration (environment):
  SMTP_HOST (mail.answerr.me) SMTP_PORT (465) SMTP_USER (ask@answerr.me) SMTP_PASSWORD
  MAIL_FROM_NAME   display name, default "answerr · Werr Technology"
  MAIL_NOTIFY_TO   where requests are delivered, default ask@answerr.me
  MAIL_REPLY_TO    Reply-To for the confirmation, default "Volkan Dagli <ask@answerr.me>, pcworm@pcworm.net"
  ANSWERR_ACCESS_LOG  JSONL log of requests, default /var/lib/answerr/access_requests.jsonl
Nothing is sent when SMTP_PASSWORD is empty; the request is still logged.
"""

from __future__ import annotations

import json
import os
import re
import smtplib
import ssl
import threading
import time
from email.message import EmailMessage
from email.utils import formataddr, make_msgid
from typing import Any, Dict

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]{1,64}@[A-Za-z0-9.\-]{1,190}\.[A-Za-z]{2,24}$")
_LOCK = threading.Lock()


def cfg() -> Dict[str, Any]:
    return {
        "host": os.environ.get("SMTP_HOST", "mail.answerr.me"),
        "port": int(os.environ.get("SMTP_PORT", "465")),
        "user": os.environ.get("SMTP_USER", "ask@answerr.me"),
        "password": os.environ.get("SMTP_PASSWORD", ""),
        "from_name": os.environ.get("MAIL_FROM_NAME", "answerr · Werr Technology"),
        "notify_to": os.environ.get("MAIL_NOTIFY_TO", "ask@answerr.me"),
        "reply_to": os.environ.get("MAIL_REPLY_TO", "Volkan Dagli <ask@answerr.me>, pcworm@pcworm.net"),
        "log": os.environ.get("ANSWERR_ACCESS_LOG", "/var/lib/answerr/access_requests.jsonl"),
    }


def valid_email(addr: str) -> bool:
    return bool(addr) and len(addr) <= 254 and bool(EMAIL_RE.match(addr)) and ".." not in addr


def _clean(s: Any, n: int) -> str:
    return re.sub(r"[\r\n\t]+", " ", str(s or "")).strip()[:n]


def log_request(entry: Dict[str, Any]) -> None:
    path = cfg()["log"]
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with _LOCK, open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _send(msgs) -> None:
    c = cfg()
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(c["host"], c["port"], context=ctx, timeout=20) as s:
        s.login(c["user"], c["password"])
        for m in msgs:
            s.send_message(m)


def build_messages(req: Dict[str, Any]) -> list:
    c = cfg()
    sender = formataddr((c["from_name"], c["user"]))
    lang = req.get("lang") if req.get("lang") in ("tr", "en") else "tr"

    note = EmailMessage()
    note["From"] = sender
    note["To"] = c["notify_to"]
    note["Reply-To"] = req["email"]
    note["Subject"] = "[answerr Pro] Tasarım ortaklığı talebi — {}".format(req["email"])
    note["Message-ID"] = make_msgid(domain="answerr.me")
    note.set_content(
        "Yeni erken erişim / tasarım ortaklığı talebi\n\n"
        "E-posta : {email}\nŞirket  : {company}\nNot     : {note}\nDil     : {lang}\n"
        "Kaynak  : {source}\nZaman   : {ts}\nIP      : {ip}\n".format(
            email=req["email"], company=req.get("company") or "-", note=req.get("note") or "-",
            lang=lang, source=req.get("source") or "-", ts=req["ts_iso"], ip=req.get("ip") or "-"))

    conf = EmailMessage()
    conf["From"] = sender
    conf["To"] = req["email"]
    conf["Reply-To"] = c["reply_to"]
    conf["Message-ID"] = make_msgid(domain="answerr.me")
    if lang == "en":
        conf["Subject"] = "answerr Pro — we received your request"
        conf.set_content(
            "Hello,\n\nThank you for your interest in the answerr Pro design-partner programme. "
            "We received your request and will get back to you within two working days.\n\n"
            "The pilot runs in shadow mode next to your current rules and is free of charge.\n\n"
            "Volkan Dagli\nanswerr · Werr Technology · ITouch Systems · Cukurova University Science Park\nhttps://answerr.me/pro/\n")
    else:
        conf["Subject"] = "answerr Pro — talebinizi aldık"
        conf.set_content(
            "Merhaba,\n\nanswerr Pro tasarım ortaklığı programına gösterdiğiniz ilgi için teşekkür ederiz. "
            "Talebinizi aldık; en geç iki iş günü içinde size dönüş yapacağız.\n\n"
            "Pilot, mevcut kurallarınızın yanında gölge modda çalışır ve ücretsizdir.\n\n"
            "Volkan Dağlı\nanswerr · Werr Technology · ITouch Bilişim Sistemleri · Çukurova Üniversitesi Teknokent\nhttps://answerr.me/pro/\n")
    return [note, conf]


def handle(payload: Dict[str, Any], ip: str) -> Dict[str, Any]:
    """Validates, logs and (if configured) mails a request. Returns a status dict."""
    email = _clean(payload.get("email"), 254).lower()
    if not valid_email(email):
        return {"ok": False, "error": "invalid_email"}
    if _clean(payload.get("website"), 200):  # honeypot field; humans never fill it
        return {"ok": True, "status": "received"}
    req = {
        "email": email,
        "company": _clean(payload.get("company"), 120),
        "note": _clean(payload.get("note"), 1000),
        "lang": payload.get("lang") if payload.get("lang") in ("tr", "en") else "tr",
        "source": _clean(payload.get("source"), 80),
        "ip": ip,
        "ts": int(time.time()),
        "ts_iso": time.strftime("%Y-%m-%d %H:%M:%S %z"),
    }
    sent = False
    error = None
    if cfg()["password"]:
        try:
            _send(build_messages(req))
            sent = True
        except Exception as e:  # never leak SMTP details to the client
            error = type(e).__name__
    log_request(dict(req, mailed=sent, mail_error=error))
    return {"ok": True, "status": "received", "mailed": sent}
