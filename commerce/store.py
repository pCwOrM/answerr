"""SQLite-backed commercial state for answerr.

One file (ANSWERR_COMMERCE_DB), WAL mode, one connection per thread, short transactions.
Secrets (API keys, session and login tokens) are stored only as SHA-256 hashes.
Billing periods and days follow Türkiye time (UTC+3, no DST).
"""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import sqlite3
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

from . import plans as P

SCHEMA_VERSION = 1
TR_OFFSET = 3 * 3600
LOGIN_TTL = 20 * 60
SESSION_TTL = 7 * 24 * 3600
REVIEW_TTL = 7 * 24 * 3600
KEY_CACHE_TTL = 30.0
ROLES = ("owner", "admin", "reviewer")
VERDICTS = ("ALLOW", "REVIEW", "DENY")
TERMS_VERSION = os.environ.get("ANSWERR_TERMS_VERSION", "2026-10-15")

_local = threading.local()
_init_lock = threading.Lock()
_initialised: Dict[str, bool] = {}
_key_cache: Dict[str, Tuple[float, Optional[Dict[str, Any]]]] = {}
_key_cache_lock = threading.Lock()


class CommerceError(Exception):
    def __init__(self, status: int, code: str, message: str, **extra):
        super().__init__(message)
        self.status, self.code, self.message, self.extra = status, code, message, extra


# ----------------------------------------------------------------------------- basics
def db_path() -> str:
    return os.environ.get("ANSWERR_COMMERCE_DB", "/var/lib/answerr/commerce.sqlite")


def now() -> float:
    return time.time()


def period_of(ts: Optional[float] = None) -> str:
    return time.strftime("%Y-%m", time.gmtime((ts if ts is not None else now()) + TR_OFFSET))


def day_of(ts: Optional[float] = None) -> str:
    return time.strftime("%Y-%m-%d", time.gmtime((ts if ts is not None else now()) + TR_OFFSET))


def sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def new_id(prefix: str, nbytes: int = 8) -> str:
    return "{}_{}".format(prefix, secrets.token_hex(nbytes))


def conn() -> sqlite3.Connection:
    path = db_path()
    c = getattr(_local, "conn", None)
    if c is None or getattr(_local, "path", None) != path:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        c = sqlite3.connect(path, timeout=5.0, isolation_level=None, check_same_thread=False)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("PRAGMA synchronous=NORMAL")
        c.execute("PRAGMA busy_timeout=5000")
        c.execute("PRAGMA foreign_keys=ON")
        _local.conn, _local.path = c, path
    if not _initialised.get(path):
        with _init_lock:
            if not _initialised.get(path):
                _migrate(c)
                _initialised[path] = True
    return c


class tx:
    """BEGIN IMMEDIATE ... COMMIT / ROLLBACK."""
    def __enter__(self):
        self.c = conn()
        self.c.execute("BEGIN IMMEDIATE")
        return self.c

    def __exit__(self, et, ev, tb):
        self.c.execute("ROLLBACK" if et else "COMMIT")
        return False


SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT);
CREATE TABLE IF NOT EXISTS accounts (
  id TEXT PRIMARY KEY, email TEXT NOT NULL, company TEXT, plan TEXT NOT NULL DEFAULT 'kesif',
  billing_cycle TEXT NOT NULL DEFAULT 'monthly', status TEXT NOT NULL DEFAULT 'active',
  overage_enabled INTEGER NOT NULL DEFAULT 0, plan_started_at REAL, plan_expires_at REAL,
  created_at REAL NOT NULL, lang TEXT DEFAULT 'tr', terms_version TEXT, terms_accepted_at REAL,
  kvkk_ack_at REAL, marketing_opt_in INTEGER DEFAULT 0, signup_ip TEXT,
  billing_json TEXT DEFAULT '{}', webhook_url TEXT, webhook_secret TEXT,
  store_review_state INTEGER NOT NULL DEFAULT 1, notes TEXT);
CREATE TABLE IF NOT EXISTS members (
  account_id TEXT NOT NULL REFERENCES accounts(id) ON DELETE CASCADE, email TEXT NOT NULL UNIQUE,
  role TEXT NOT NULL, created_at REAL NOT NULL, invited_by TEXT, joined_at REAL);
CREATE INDEX IF NOT EXISTS members_acc ON members(account_id);
CREATE TABLE IF NOT EXISTS api_keys (
  id TEXT PRIMARY KEY, account_id TEXT NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  prefix TEXT NOT NULL, key_hash TEXT NOT NULL UNIQUE, label TEXT, created_at REAL NOT NULL,
  created_by TEXT, revoked_at REAL, last_used_at REAL);
CREATE INDEX IF NOT EXISTS keys_acc ON api_keys(account_id);
CREATE TABLE IF NOT EXISTS login_tokens (
  token_hash TEXT PRIMARY KEY, email TEXT NOT NULL, purpose TEXT NOT NULL, payload TEXT,
  created_at REAL NOT NULL, expires_at REAL NOT NULL, used_at REAL, ip TEXT);
CREATE INDEX IF NOT EXISTS login_email ON login_tokens(email, created_at);
CREATE TABLE IF NOT EXISTS sessions (
  token_hash TEXT PRIMARY KEY, account_id TEXT NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  email TEXT NOT NULL, role TEXT NOT NULL, created_at REAL NOT NULL, expires_at REAL NOT NULL, revoked_at REAL);
CREATE TABLE IF NOT EXISTS usage (
  account_id TEXT NOT NULL, period TEXT NOT NULL, decisions INTEGER NOT NULL DEFAULT 0,
  warned80 INTEGER NOT NULL DEFAULT 0, warned100 INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (account_id, period));
CREATE TABLE IF NOT EXISTS usage_daily (
  account_id TEXT NOT NULL, day TEXT NOT NULL, decisions INTEGER NOT NULL DEFAULT 0,
  allow INTEGER NOT NULL DEFAULT 0, review INTEGER NOT NULL DEFAULT 0, deny INTEGER NOT NULL DEFAULT 0,
  shadow INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (account_id, day));
CREATE TABLE IF NOT EXISTS decisions (
  id TEXT PRIMARY KEY, account_id TEXT NOT NULL, ts REAL NOT NULL, gate_id TEXT, verdict TEXT NOT NULL,
  rule_id TEXT, reason TEXT, latency_ms REAL, mode TEXT NOT NULL DEFAULT 'live', observed TEXT, observed_at REAL,
  key_prefix TEXT, policy_seal TEXT, state_fields TEXT, external_id TEXT);
CREATE INDEX IF NOT EXISTS dec_acc_ts ON decisions(account_id, ts);
CREATE TABLE IF NOT EXISTS reviews (
  id TEXT PRIMARY KEY, account_id TEXT NOT NULL, decision_id TEXT, ts REAL NOT NULL, gate_id TEXT,
  rule_id TEXT, reason TEXT, state_json TEXT, status TEXT NOT NULL DEFAULT 'pending',
  resolved_by TEXT, resolved_at REAL, note TEXT, expires_at REAL NOT NULL, external_id TEXT);
CREATE INDEX IF NOT EXISTS rev_acc ON reviews(account_id, status, ts);
CREATE TABLE IF NOT EXISTS plan_requests (
  id TEXT PRIMARY KEY, account_id TEXT NOT NULL, ts REAL NOT NULL, plan TEXT NOT NULL, cycle TEXT NOT NULL,
  note TEXT, status TEXT NOT NULL DEFAULT 'pending', handled_at REAL, handled_by TEXT);
CREATE TABLE IF NOT EXISTS statements (
  id TEXT PRIMARY KEY, account_id TEXT NOT NULL, period TEXT NOT NULL, plan TEXT NOT NULL, cycle TEXT NOT NULL,
  base_cents INTEGER NOT NULL, quota INTEGER, used INTEGER NOT NULL, overage_units INTEGER NOT NULL,
  overage_cents INTEGER NOT NULL, total_cents INTEGER NOT NULL, currency TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'draft', provider TEXT, provider_ref TEXT, e_invoice_no TEXT,
  created_at REAL NOT NULL, issued_at REAL, paid_at REAL, UNIQUE (account_id, period));
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL NOT NULL, account_id TEXT, actor TEXT, action TEXT NOT NULL, detail TEXT);
CREATE INDEX IF NOT EXISTS ev_acc ON events(account_id, ts);
CREATE TABLE IF NOT EXISTS webhook_deliveries (
  id INTEGER PRIMARY KEY AUTOINCREMENT, account_id TEXT NOT NULL, ts REAL NOT NULL, event TEXT NOT NULL,
  url TEXT, status_code INTEGER, attempts INTEGER, error TEXT);
CREATE TABLE IF NOT EXISTS payments (
  id TEXT PRIMARY KEY, account_id TEXT, kind TEXT NOT NULL DEFAULT 'plan', plan TEXT, cycle TEXT,
  net_try TEXT NOT NULL, vat_try TEXT NOT NULL, total_try TEXT NOT NULL, currency TEXT NOT NULL DEFAULT 'TRY',
  provider TEXT NOT NULL, conversation_id TEXT NOT NULL UNIQUE, token TEXT UNIQUE, status TEXT NOT NULL DEFAULT 'initiated',
  payment_id TEXT, fraud_status INTEGER, card_last4 TEXT, error TEXT, created_by TEXT,
  created_at REAL NOT NULL, paid_at REAL, period_start REAL, period_end REAL, billing_json TEXT);
CREATE INDEX IF NOT EXISTS pay_acc ON payments(account_id, created_at);
"""


def _migrate(c: sqlite3.Connection) -> None:
    c.executescript(SCHEMA)
    c.execute("INSERT OR IGNORE INTO meta (k, v) VALUES ('schema_version', ?)", (str(SCHEMA_VERSION),))


def init() -> None:
    conn()


def event(c: sqlite3.Connection, account_id: Optional[str], actor: str, action: str, detail: Any = None) -> None:
    c.execute("INSERT INTO events (ts, account_id, actor, action, detail) VALUES (?, ?, ?, ?, ?)",
              (now(), account_id, actor, action, json.dumps(detail, ensure_ascii=False) if detail is not None else None))


def _row(r: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
    return dict(r) if r is not None else None


# ----------------------------------------------------------------------------- plans
def effective_plan(acc: Dict[str, Any]) -> str:
    plan = acc.get("plan") or P.DEFAULT_PLAN
    exp = acc.get("plan_expires_at")
    if exp and exp < now():
        return P.DEFAULT_PLAN
    return plan if plan in P.PLANS else P.DEFAULT_PLAN


def plan_of(acc: Dict[str, Any]) -> Dict[str, Any]:
    return P.get(effective_plan(acc))


# ----------------------------------------------------------------------------- login & sessions
def create_login_token(email: str, purpose: str, payload: Optional[Dict[str, Any]], ip: str) -> str:
    """Single-use, 20-minute link token. At most 5 per address per hour."""
    email = email.strip().lower()
    with tx() as c:
        n = c.execute("SELECT COUNT(*) FROM login_tokens WHERE email = ? AND created_at > ?",
                      (email, now() - 3600)).fetchone()[0]
        if n >= 5:
            raise CommerceError(429, "too_many_links", "Too many sign-in links for this address; try again in an hour.")
        raw = "ans_link_" + secrets.token_urlsafe(32)
        c.execute("INSERT INTO login_tokens (token_hash, email, purpose, payload, created_at, expires_at, ip) "
                  "VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (sha(raw), email, purpose, json.dumps(payload or {}), now(), now() + LOGIN_TTL, ip))
    return raw


def member_of(email: str) -> Optional[Dict[str, Any]]:
    return _row(conn().execute("SELECT * FROM members WHERE email = ?", (email.strip().lower(),)).fetchone())


def verify_login(raw: str, ip: str) -> Dict[str, Any]:
    """Consumes a link token. Signs up (creating the account and a first API key) or logs in."""
    first_key = None
    with tx() as c:
        r = c.execute("SELECT * FROM login_tokens WHERE token_hash = ?", (sha(raw or ""),)).fetchone()
        if not r or r["used_at"] or r["expires_at"] < now():
            raise CommerceError(400, "invalid_link", "This sign-in link is invalid or has expired.")
        c.execute("UPDATE login_tokens SET used_at = ? WHERE token_hash = ?", (now(), r["token_hash"]))
        email, payload = r["email"], json.loads(r["payload"] or "{}")
        m = c.execute("SELECT * FROM members WHERE email = ?", (email,)).fetchone()
        if m is None:
            if r["purpose"] != "signup":
                raise CommerceError(404, "no_account", "No account uses this address; sign up first.")
            acc_id = new_id("acc", 6)
            t = now()
            c.execute("INSERT INTO accounts (id, email, company, plan, created_at, lang, terms_version, terms_accepted_at, "
                      "kvkk_ack_at, marketing_opt_in, signup_ip, plan_started_at) VALUES (?, ?, ?, 'kesif', ?, ?, ?, ?, ?, ?, ?, ?)",
                      (acc_id, email, (payload.get("company") or "")[:120], t, payload.get("lang", "tr"),
                       payload.get("terms_version", TERMS_VERSION), t, t, 1 if payload.get("marketing") else 0, ip, t))
            c.execute("INSERT INTO members (account_id, email, role, created_at, joined_at) VALUES (?, ?, 'owner', ?, ?)",
                      (acc_id, email, t, t))
            event(c, acc_id, email, "account.created", {"plan": "kesif", "ip": ip})
            first_key = _create_key(c, acc_id, "default", email)
            m = c.execute("SELECT * FROM members WHERE email = ?", (email,)).fetchone()
        else:
            if m["joined_at"] is None:
                c.execute("UPDATE members SET joined_at = ? WHERE email = ?", (now(), email))
            acc = c.execute("SELECT status FROM accounts WHERE id = ?", (m["account_id"],)).fetchone()
            if acc is None or acc["status"] == "closed":
                raise CommerceError(403, "account_closed", "This account is closed.")
        sess = "ans_sess_" + secrets.token_urlsafe(32)
        c.execute("INSERT INTO sessions (token_hash, account_id, email, role, created_at, expires_at) VALUES (?, ?, ?, ?, ?, ?)",
                  (sha(sess), m["account_id"], email, m["role"], now(), now() + SESSION_TTL))
        event(c, m["account_id"], email, "session.created", {"ip": ip})
    out = {"session": sess, "expires_in": SESSION_TTL, "account_id": m["account_id"], "role": m["role"], "email": email}
    if first_key:
        out["api_key"] = first_key[0]
    return out


def resolve_session(raw: str) -> Optional[Dict[str, Any]]:
    if not raw or not raw.startswith("ans_sess_"):
        return None
    r = conn().execute("SELECT s.*, a.status AS account_status FROM sessions s JOIN accounts a ON a.id = s.account_id "
                       "WHERE s.token_hash = ?", (sha(raw),)).fetchone()
    if not r or r["revoked_at"] or r["expires_at"] < now() or r["account_status"] == "closed":
        return None
    m = conn().execute("SELECT role FROM members WHERE email = ? AND account_id = ?", (r["email"], r["account_id"])).fetchone()
    if not m:
        return None
    return {"account_id": r["account_id"], "email": r["email"], "role": m["role"], "via": "session"}


def revoke_session(raw: str) -> None:
    with tx() as c:
        c.execute("UPDATE sessions SET revoked_at = ? WHERE token_hash = ?", (now(), sha(raw or "")))


# ----------------------------------------------------------------------------- API keys
def _create_key(c: sqlite3.Connection, account_id: str, label: str, by: str) -> Tuple[str, Dict[str, Any]]:
    raw = "ans_live_" + secrets.token_urlsafe(30)
    kid = new_id("key", 6)
    prefix = raw[:13]
    c.execute("INSERT INTO api_keys (id, account_id, prefix, key_hash, label, created_at, created_by) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (kid, account_id, prefix, sha(raw), (label or "key")[:60], now(), by))
    event(c, account_id, by, "key.created", {"key_id": kid, "prefix": prefix})
    return raw, {"id": kid, "prefix": prefix, "label": label, "created_at": now()}


def create_api_key(account_id: str, label: str, by: str) -> Tuple[str, Dict[str, Any]]:
    with tx() as c:
        acc = _row(c.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone())
        n = c.execute("SELECT COUNT(*) FROM api_keys WHERE account_id = ? AND revoked_at IS NULL", (account_id,)).fetchone()[0]
        limit = plan_of(acc)["api_keys"]
        if n >= limit:
            raise CommerceError(403, "key_limit", "Your plan allows {} active API keys.".format(limit), limit=limit)
        return _create_key(c, account_id, label, by)


def list_keys(account_id: str) -> List[Dict[str, Any]]:
    rows = conn().execute("SELECT id, prefix, label, created_at, created_by, revoked_at, last_used_at FROM api_keys "
                          "WHERE account_id = ? ORDER BY created_at DESC", (account_id,)).fetchall()
    return [dict(r) for r in rows]


def revoke_key(account_id: str, key_id: str, by: str) -> bool:
    with tx() as c:
        r = c.execute("UPDATE api_keys SET revoked_at = ? WHERE id = ? AND account_id = ? AND revoked_at IS NULL",
                      (now(), key_id, account_id))
        if r.rowcount:
            event(c, account_id, by, "key.revoked", {"key_id": key_id})
    with _key_cache_lock:
        _key_cache.clear()
    return bool(r.rowcount)


def resolve_api_key(raw: str) -> Optional[Dict[str, Any]]:
    """Cached for 30 s per worker; a revoked key stops working everywhere within that time."""
    if not raw or not raw.startswith("ans_live_"):
        return None
    h = sha(raw)
    t = now()
    with _key_cache_lock:
        hit = _key_cache.get(h)
        if hit and hit[0] > t:
            return hit[1]
    r = conn().execute("SELECT k.id, k.account_id, k.prefix, k.last_used_at, a.status FROM api_keys k "
                       "JOIN accounts a ON a.id = k.account_id WHERE k.key_hash = ? AND k.revoked_at IS NULL",
                       (h,)).fetchone()
    val = None
    if r and r["status"] != "closed":
        val = {"account_id": r["account_id"], "key_id": r["id"], "prefix": r["prefix"], "role": "admin", "via": "api_key",
               "suspended": r["status"] == "suspended"}
        if not r["last_used_at"] or t - r["last_used_at"] > 300:
            try:
                conn().execute("UPDATE api_keys SET last_used_at = ? WHERE id = ?", (t, r["id"]))
            except sqlite3.OperationalError:
                pass
    with _key_cache_lock:
        if len(_key_cache) > 5000:
            _key_cache.clear()
        _key_cache[h] = (t + KEY_CACHE_TTL, val)
    return val


# ----------------------------------------------------------------------------- accounts
def get_account(account_id: str) -> Optional[Dict[str, Any]]:
    return _row(conn().execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone())


def usage_now(account_id: str, period: Optional[str] = None) -> int:
    r = conn().execute("SELECT decisions FROM usage WHERE account_id = ? AND period = ?",
                       (account_id, period or period_of())).fetchone()
    return int(r[0]) if r else 0


def account_view(account_id: str) -> Dict[str, Any]:
    acc = get_account(account_id)
    if not acc:
        raise CommerceError(404, "no_account", "Account not found.")
    plan_id = effective_plan(acc)
    plan = P.get(plan_id)
    used = usage_now(account_id)
    billing = json.loads(acc.get("billing_json") or "{}")
    return {
        "id": acc["id"], "email": acc["email"], "company": acc["company"], "status": acc["status"],
        "plan": plan_id, "plan_name": {"tr": plan["name_tr"], "en": plan["name_en"]},
        "plan_assigned": acc["plan"], "plan_expires_at": acc["plan_expires_at"], "billing_cycle": acc["billing_cycle"],
        "overage_enabled": bool(acc["overage_enabled"]), "limits": {k: plan.get(k) for k in
                                                                    ("quota", "overage_per_1000", "custom_gates", "retention_days", "seats", "api_keys")},
        "features": plan["features"],
        "usage": {"period": period_of(), "decisions": used, "quota": plan.get("quota"),
                  "remaining": None if plan.get("quota") is None else max(0, plan["quota"] - used)},
        "billing": billing, "webhook_url": acc["webhook_url"], "webhook_secret_set": bool(acc["webhook_secret"]),
        "store_review_state": bool(acc["store_review_state"]),
        "created_at": acc["created_at"], "lang": acc["lang"], "terms_version": acc["terms_version"],
    }


BILLING_FIELDS = ("legal_name", "contact_name", "tax_office", "tax_id", "address", "city", "country", "invoice_email", "phone")


def update_account(account_id: str, by: str, fields: Dict[str, Any]) -> Dict[str, Any]:
    with tx() as c:
        acc = _row(c.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone())
        if not acc:
            raise CommerceError(404, "no_account", "Account not found.")
        sets, vals, changed = [], [], []
        if "company" in fields and fields["company"] is not None:
            sets.append("company = ?"); vals.append(str(fields["company"])[:120]); changed.append("company")
        if "lang" in fields and fields["lang"] in ("tr", "en"):
            sets.append("lang = ?"); vals.append(fields["lang"]); changed.append("lang")
        if "overage_enabled" in fields and fields["overage_enabled"] is not None:
            if fields["overage_enabled"] and not P.get(effective_plan(acc)).get("overage_per_1000"):
                raise CommerceError(400, "no_overage", "Overage is not available on this plan.")
            sets.append("overage_enabled = ?"); vals.append(1 if fields["overage_enabled"] else 0); changed.append("overage_enabled")
        if "store_review_state" in fields and fields["store_review_state"] is not None:
            sets.append("store_review_state = ?"); vals.append(1 if fields["store_review_state"] else 0); changed.append("store_review_state")
        if "billing" in fields and isinstance(fields["billing"], dict):
            b = json.loads(acc.get("billing_json") or "{}")
            for k in BILLING_FIELDS:
                if k in fields["billing"] and fields["billing"][k] is not None:
                    b[k] = str(fields["billing"][k])[:300]
            sets.append("billing_json = ?"); vals.append(json.dumps(b, ensure_ascii=False)); changed.append("billing")
        if "webhook_url" in fields:
            url = (fields["webhook_url"] or "").strip()
            if url:
                if not P.has(effective_plan(acc), "webhooks"):
                    raise CommerceError(403, "feature_unavailable", "Webhooks are available on Pro and above.", feature="webhooks")
                from . import webhooks
                webhooks.validate_url(url)
            sets.append("webhook_url = ?"); vals.append(url or None); changed.append("webhook_url")
            if url and not acc.get("webhook_secret"):
                sets.append("webhook_secret = ?"); vals.append("whsec_" + secrets.token_urlsafe(24))
        if sets:
            c.execute("UPDATE accounts SET {} WHERE id = ?".format(", ".join(sets)), vals + [account_id])
            event(c, account_id, by, "account.updated", {"fields": changed})
    return account_view(account_id)


def rotate_webhook_secret(account_id: str, by: str) -> str:
    sec = "whsec_" + secrets.token_urlsafe(24)
    with tx() as c:
        c.execute("UPDATE accounts SET webhook_secret = ? WHERE id = ?", (sec, account_id))
        event(c, account_id, by, "webhook.secret_rotated")
    return sec


# ----------------------------------------------------------------------------- members
def list_members(account_id: str) -> List[Dict[str, Any]]:
    return [dict(r) for r in conn().execute(
        "SELECT email, role, created_at, invited_by, joined_at FROM members WHERE account_id = ? ORDER BY created_at",
        (account_id,)).fetchall()]


def invite_member(account_id: str, email: str, role: str, by: str) -> None:
    email = email.strip().lower()
    if role not in ("admin", "reviewer"):
        raise CommerceError(400, "bad_role", "Role must be admin or reviewer.")
    with tx() as c:
        acc = _row(c.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone())
        n = c.execute("SELECT COUNT(*) FROM members WHERE account_id = ?", (account_id,)).fetchone()[0]
        seats = plan_of(acc)["seats"]
        if n >= seats:
            raise CommerceError(403, "seat_limit", "Your plan includes {} seat(s).".format(seats), limit=seats)
        if c.execute("SELECT 1 FROM members WHERE email = ?", (email,)).fetchone():
            raise CommerceError(409, "member_exists", "This address already belongs to an account.")
        c.execute("INSERT INTO members (account_id, email, role, created_at, invited_by) VALUES (?, ?, ?, ?, ?)",
                  (account_id, email, role, now(), by))
        event(c, account_id, by, "member.invited", {"email": email, "role": role})


def remove_member(account_id: str, email: str, by: str) -> bool:
    email = email.strip().lower()
    with tx() as c:
        m = c.execute("SELECT role FROM members WHERE account_id = ? AND email = ?", (account_id, email)).fetchone()
        if not m:
            return False
        if m["role"] == "owner":
            raise CommerceError(400, "owner", "The owner cannot be removed.")
        c.execute("DELETE FROM members WHERE account_id = ? AND email = ?", (account_id, email))
        c.execute("UPDATE sessions SET revoked_at = ? WHERE account_id = ? AND email = ? AND revoked_at IS NULL",
                  (now(), account_id, email))
        event(c, account_id, by, "member.removed", {"email": email})
    return True


# ----------------------------------------------------------------------------- metering
def quota_check(account_id: str) -> Dict[str, Any]:
    """Raises CommerceError(429, 'quota_exceeded') when the plan quota is used up and overage is off."""
    acc = get_account(account_id)
    if not acc:
        raise CommerceError(401, "no_account", "Account not found.")
    if acc["status"] == "suspended":
        raise CommerceError(403, "account_suspended", "This account is suspended; contact ask@answerr.me.")
    plan_id = effective_plan(acc)
    plan = P.get(plan_id)
    used = usage_now(account_id)
    quota = plan.get("quota")
    if quota is not None and used >= quota and not (acc["overage_enabled"] and plan.get("overage_per_1000")):
        raise CommerceError(429, "quota_exceeded", "Monthly decision quota reached ({:,}). Enable overage or upgrade.".format(quota),
                            quota=quota, used=used, period=period_of())
    return {"account": acc, "plan_id": plan_id, "plan": plan, "used": used, "quota": quota}


def record_decision(account_id: str, *, key_prefix: Optional[str], gate_id: Optional[str], verdict: str,
                    rule_id: Optional[str], reason: Optional[str], latency_ms: float, mode: str,
                    observed: Optional[str], policy_seal: Optional[str], state: Dict[str, Any],
                    external_id: Optional[str], enqueue_review: bool, count: int = 1) -> Dict[str, Any]:
    t = now()
    period, day = period_of(t), day_of(t)
    did = new_id("dec", 10)
    review_id = None
    acc = get_account(account_id) or {}
    plan_id = effective_plan(acc)
    vcol = {"ALLOW": "allow", "REVIEW": "review", "DENY": "deny"}.get(verdict, "review")
    with tx() as c:
        c.execute("INSERT INTO usage (account_id, period, decisions) VALUES (?, ?, ?) "
                  "ON CONFLICT(account_id, period) DO UPDATE SET decisions = decisions + excluded.decisions",
                  (account_id, period, count))
        c.execute("INSERT INTO usage_daily (account_id, day, decisions, {v}, shadow) VALUES (?, ?, ?, 1, ?) "
                  "ON CONFLICT(account_id, day) DO UPDATE SET decisions = decisions + excluded.decisions, "
                  "{v} = {v} + 1, shadow = shadow + excluded.shadow".format(v=vcol),
                  (account_id, day, count, 1 if mode == "shadow" else 0))
        c.execute("INSERT INTO decisions (id, account_id, ts, gate_id, verdict, rule_id, reason, latency_ms, mode, observed, "
                  "observed_at, key_prefix, policy_seal, state_fields, external_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                  (did, account_id, t, gate_id, verdict, rule_id, (reason or "")[:300], round(latency_ms, 3), mode,
                   normalize_outcome(observed), t if observed is not None else None, key_prefix, policy_seal,
                   json.dumps(sorted(list(state.keys()))[:64]), (external_id or None) and str(external_id)[:120]))
        if enqueue_review and verdict == "REVIEW" and mode == "live" and P.has(plan_id, "review_queue"):
            review_id = new_id("rev", 10)
            keep_state = bool(acc.get("store_review_state", 1))
            c.execute("INSERT INTO reviews (id, account_id, decision_id, ts, gate_id, rule_id, reason, state_json, expires_at, external_id) "
                      "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                      (review_id, account_id, did, t, gate_id, rule_id, (reason or "")[:300],
                       json.dumps(state, ensure_ascii=False)[:16000] if keep_state else None, t + REVIEW_TTL,
                       (external_id or None) and str(external_id)[:120]))
        used = c.execute("SELECT decisions, warned80, warned100 FROM usage WHERE account_id = ? AND period = ?",
                         (account_id, period)).fetchone()
        warn = None
        quota = P.get(plan_id).get("quota")
        if quota:
            if used["decisions"] >= quota and not used["warned100"]:
                c.execute("UPDATE usage SET warned100 = 1, warned80 = 1 WHERE account_id = ? AND period = ?", (account_id, period))
                warn = 100
            elif used["decisions"] >= 0.8 * quota and not used["warned80"]:
                c.execute("UPDATE usage SET warned80 = 1 WHERE account_id = ? AND period = ?", (account_id, period))
                warn = 80
    return {"decision_id": did, "review_id": review_id, "warn": warn,
            "usage": {"period": period, "decisions": used["decisions"], "quota": quota}}


def normalize_outcome(v: Any) -> Optional[str]:
    if v is None:
        return None
    if isinstance(v, bool):
        return "ALLOW" if v else "DENY"
    s = str(v).strip().upper()
    aliases = {"APPROVE": "ALLOW", "APPROVED": "ALLOW", "ALLOWED": "ALLOW", "TRUE": "ALLOW", "PASS": "ALLOW", "GEÇ": "ALLOW",
               "BLOCK": "DENY", "BLOCKED": "DENY", "REJECT": "DENY", "REJECTED": "DENY", "FALSE": "DENY", "FRAUD": "DENY",
               "DENIED": "DENY", "DUR": "DENY", "MANUAL": "REVIEW", "HUMAN": "REVIEW", "ABSTAIN_REVIEW": "REVIEW"}
    s = aliases.get(s, s)
    if s not in VERDICTS:
        raise CommerceError(400, "bad_outcome", "observed_outcome must be ALLOW, REVIEW or DENY (or true/false).")
    return s


def set_outcome(account_id: str, decision_id: str, observed: Any, by: str) -> Dict[str, Any]:
    o = normalize_outcome(observed)
    with tx() as c:
        r = c.execute("UPDATE decisions SET observed = ?, observed_at = ? WHERE id = ? AND account_id = ?",
                      (o, now(), decision_id, account_id))
        if not r.rowcount:
            raise CommerceError(404, "no_decision", "Decision not found (it may be past your plan's retention).")
    return {"decision_id": decision_id, "observed": o}


def list_decisions(account_id: str, *, limit: int = 100, before: Optional[float] = None, verdict: Optional[str] = None,
                   gate_id: Optional[str] = None, mode: Optional[str] = None, since: Optional[float] = None) -> List[Dict[str, Any]]:
    q = "SELECT id, ts, gate_id, verdict, rule_id, reason, latency_ms, mode, observed, key_prefix, policy_seal, state_fields, external_id " \
        "FROM decisions WHERE account_id = ?"
    a: List[Any] = [account_id]
    if before:
        q += " AND ts < ?"; a.append(before)
    if since:
        q += " AND ts >= ?"; a.append(since)
    if verdict in VERDICTS:
        q += " AND verdict = ?"; a.append(verdict)
    if gate_id:
        q += " AND gate_id = ?"; a.append(gate_id)
    if mode in ("live", "shadow"):
        q += " AND mode = ?"; a.append(mode)
    q += " ORDER BY ts DESC LIMIT ?"
    a.append(max(1, min(int(limit), 10000)))
    out = []
    for r in conn().execute(q, a).fetchall():
        d = dict(r)
        d["state_fields"] = json.loads(d["state_fields"] or "[]")
        out.append(d)
    return out


def shadow_report(account_id: str, days: int = 30, gate_id: Optional[str] = None) -> Dict[str, Any]:
    since = now() - max(1, min(days, 400)) * 86400
    q = "SELECT verdict, observed, COUNT(*) n FROM decisions WHERE account_id = ? AND ts >= ?"
    a: List[Any] = [account_id, since]
    if gate_id:
        q += " AND gate_id = ?"; a.append(gate_id)
    q += " GROUP BY verdict, observed"
    matrix = {v: {o: 0 for o in VERDICTS + ("unknown",)} for v in VERDICTS}
    total = labelled = agree = 0
    for r in conn().execute(q, a).fetchall():
        v, o, n = r["verdict"], r["observed"] or "unknown", r["n"]
        if v not in matrix:
            continue
        matrix[v][o] = matrix[v].get(o, 0) + n
        total += n
        if o != "unknown":
            labelled += n
            if o == v:
                agree += n
    # answerr stops what you let through (potential catches) and lets through what you stopped (potential misses)
    caught = matrix["DENY"]["ALLOW"] + matrix["REVIEW"]["ALLOW"]
    relaxed = matrix["ALLOW"]["DENY"] + matrix["ALLOW"]["REVIEW"]
    return {"days": days, "gate_id": gate_id, "decisions": total, "labelled": labelled,
            "agreement": round(agree / labelled, 4) if labelled else None,
            "stricter_than_you": caught, "looser_than_you": relaxed,
            "matrix": matrix, "rows_are": "answerr verdict", "columns_are": "your observed outcome"}


def usage_series(account_id: str, days: int = 30) -> List[Dict[str, Any]]:
    days = max(1, min(days, 400))
    start = day_of(now() - (days - 1) * 86400)
    rows = {r["day"]: dict(r) for r in conn().execute(
        "SELECT day, decisions, allow, review, deny, shadow FROM usage_daily WHERE account_id = ? AND day >= ? ORDER BY day",
        (account_id, start)).fetchall()}
    out = []
    for i in range(days):
        d = day_of(now() - (days - 1 - i) * 86400)
        out.append(rows.get(d) or {"day": d, "decisions": 0, "allow": 0, "review": 0, "deny": 0, "shadow": 0})
    return out


# ----------------------------------------------------------------------------- reviews
def list_reviews(account_id: str, status: Optional[str] = "pending", limit: int = 100) -> List[Dict[str, Any]]:
    _expire_reviews()
    q = "SELECT * FROM reviews WHERE account_id = ?"
    a: List[Any] = [account_id]
    if status in ("pending", "approved", "rejected", "expired"):
        q += " AND status = ?"; a.append(status)
    q += " ORDER BY ts DESC LIMIT ?"
    a.append(max(1, min(limit, 1000)))
    out = []
    for r in conn().execute(q, a).fetchall():
        d = dict(r)
        d["state"] = json.loads(d.pop("state_json") or "null")
        out.append(d)
    return out


def get_review(account_id: str, review_id: str) -> Dict[str, Any]:
    _expire_reviews()
    r = conn().execute("SELECT * FROM reviews WHERE id = ? AND account_id = ?", (review_id, account_id)).fetchone()
    if not r:
        raise CommerceError(404, "no_review", "Review not found.")
    d = dict(r)
    d["state"] = json.loads(d.pop("state_json") or "null")
    return d


def resolve_review(account_id: str, review_id: str, action: str, note: Optional[str], by: str) -> Dict[str, Any]:
    status = {"approve": "approved", "reject": "rejected"}.get(action)
    if not status:
        raise CommerceError(400, "bad_action", "action must be approve or reject.")
    with tx() as c:
        r = c.execute("SELECT status, decision_id, expires_at FROM reviews WHERE id = ? AND account_id = ?",
                      (review_id, account_id)).fetchone()
        if not r:
            raise CommerceError(404, "no_review", "Review not found.")
        if r["status"] != "pending":
            raise CommerceError(409, "already_resolved", "This review is already {}.".format(r["status"]), review_status=r["status"])
        if r["expires_at"] < now():
            c.execute("UPDATE reviews SET status = 'expired' WHERE id = ?", (review_id,))
            raise CommerceError(409, "expired", "This review expired before it was resolved.")
        c.execute("UPDATE reviews SET status = ?, resolved_by = ?, resolved_at = ?, note = ? WHERE id = ?",
                  (status, by, now(), (note or "")[:500], review_id))
        if r["decision_id"]:
            c.execute("UPDATE decisions SET observed = ?, observed_at = ? WHERE id = ?",
                      ("ALLOW" if status == "approved" else "DENY", now(), r["decision_id"]))
        event(c, account_id, by, "review." + status, {"review_id": review_id})
    return get_review(account_id, review_id)


def _expire_reviews() -> None:
    try:
        conn().execute("UPDATE reviews SET status = 'expired' WHERE status = 'pending' AND expires_at < ?", (now(),))
    except sqlite3.OperationalError:
        pass


# ----------------------------------------------------------------------------- plan requests
def request_plan(account_id: str, plan: str, cycle: str, note: Optional[str], by: str) -> Dict[str, Any]:
    if plan not in P.PLANS:
        raise CommerceError(400, "bad_plan", "Unknown plan.")
    if cycle not in ("monthly", "yearly"):
        raise CommerceError(400, "bad_cycle", "cycle must be monthly or yearly.")
    rid = new_id("preq", 6)
    with tx() as c:
        c.execute("UPDATE plan_requests SET status = 'cancelled', handled_at = ? WHERE account_id = ? AND status = 'pending'",
                  (now(), account_id))
        c.execute("INSERT INTO plan_requests (id, account_id, ts, plan, cycle, note) VALUES (?, ?, ?, ?, ?, ?)",
                  (rid, account_id, now(), plan, cycle, (note or "")[:1000]))
        event(c, account_id, by, "plan.requested", {"plan": plan, "cycle": cycle})
    return {"id": rid, "plan": plan, "cycle": cycle, "status": "pending"}


def list_plan_requests(account_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
    q = "SELECT r.*, a.email, a.company, a.plan AS current_plan FROM plan_requests r JOIN accounts a ON a.id = r.account_id WHERE 1=1"
    args: List[Any] = []
    if account_id:
        q += " AND r.account_id = ?"; args.append(account_id)
    if status:
        q += " AND r.status = ?"; args.append(status)
    return [dict(r) for r in conn().execute(q + " ORDER BY r.ts DESC LIMIT 500", args).fetchall()]


def set_plan(account_id: str, plan: str, cycle: str, by: str, expires_at: Optional[float] = None,
             request_id: Optional[str] = None) -> Dict[str, Any]:
    if plan not in P.PLANS:
        raise CommerceError(400, "bad_plan", "Unknown plan.")
    if plan == "pilot" and not expires_at:
        expires_at = now() + P.get("pilot").get("duration_days", 60) * 86400
    with tx() as c:
        r = c.execute("UPDATE accounts SET plan = ?, billing_cycle = ?, plan_started_at = ?, plan_expires_at = ? WHERE id = ?",
                      (plan, cycle, now(), expires_at, account_id))
        if not r.rowcount:
            raise CommerceError(404, "no_account", "Account not found.")
        if not P.get(plan).get("overage_per_1000"):
            c.execute("UPDATE accounts SET overage_enabled = 0 WHERE id = ?", (account_id,))
        if request_id:
            c.execute("UPDATE plan_requests SET status = 'approved', handled_at = ?, handled_by = ? WHERE id = ?",
                      (now(), by, request_id))
        event(c, account_id, by, "plan.changed", {"plan": plan, "cycle": cycle, "expires_at": expires_at})
    return account_view(account_id)


def reject_plan_request(request_id: str, by: str) -> None:
    with tx() as c:
        c.execute("UPDATE plan_requests SET status = 'rejected', handled_at = ?, handled_by = ? WHERE id = ? AND status = 'pending'",
                  (now(), by, request_id))


def set_status(account_id: str, status: str, by: str) -> None:
    if status not in ("active", "suspended", "closed"):
        raise CommerceError(400, "bad_status", "status must be active, suspended or closed.")
    with tx() as c:
        c.execute("UPDATE accounts SET status = ? WHERE id = ?", (status, account_id))
        if status == "closed":
            c.execute("UPDATE api_keys SET revoked_at = ? WHERE account_id = ? AND revoked_at IS NULL", (now(), account_id))
            c.execute("UPDATE sessions SET revoked_at = ? WHERE account_id = ? AND revoked_at IS NULL", (now(), account_id))
        event(c, account_id, by, "account." + status)
    with _key_cache_lock:
        _key_cache.clear()


def delete_account(account_id: str, by: str) -> bool:
    """Hard delete (KVKK erasure or test cleanup). Statements are kept: they are accounting records."""
    with tx() as c:
        for t in ("decisions", "reviews", "usage", "usage_daily", "plan_requests", "webhook_deliveries"):
            c.execute("DELETE FROM {} WHERE account_id = ?".format(t), (account_id,))
        r = c.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
        event(c, account_id, by, "account.deleted")
    with _key_cache_lock:
        _key_cache.clear()
    return bool(r.rowcount)


# ----------------------------------------------------------------------------- usage statements (billing)
def build_statement(acc: Dict[str, Any], period: str) -> Dict[str, Any]:
    plan_id = acc["plan"] if acc["plan"] in P.PLANS else P.DEFAULT_PLAN
    plan = P.get(plan_id)
    used = usage_now(acc["id"], period)
    quota = plan.get("quota")
    over_units = max(0, used - quota) if (quota is not None and acc["overage_enabled"]) else 0
    base = P.monthly_base_cents(plan_id, acc["billing_cycle"])
    over = P.overage_cents(plan_id, over_units)
    return {"id": "st_{}_{}".format(period.replace("-", ""), acc["id"]), "account_id": acc["id"], "period": period,
            "plan": plan_id, "cycle": acc["billing_cycle"], "base_cents": base, "quota": quota, "used": used,
            "overage_units": over_units, "overage_cents": over, "total_cents": base + over,
            "currency": P.CATALOG.get("currency", "USD")}


def generate_statements(period: str, by: str) -> List[Dict[str, Any]]:
    """Creates or refreshes draft statements for every billable account. Issued ones are not touched."""
    out = []
    accs = [dict(r) for r in conn().execute("SELECT * FROM accounts WHERE status != 'closed'").fetchall()]
    with tx() as c:
        for acc in accs:
            st = build_statement(acc, period)
            if st["total_cents"] <= 0:
                continue
            ex = c.execute("SELECT status FROM statements WHERE account_id = ? AND period = ?", (acc["id"], period)).fetchone()
            if ex and ex["status"] != "draft":
                continue
            c.execute("INSERT INTO statements (id, account_id, period, plan, cycle, base_cents, quota, used, overage_units, "
                      "overage_cents, total_cents, currency, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
                      "ON CONFLICT(account_id, period) DO UPDATE SET plan = excluded.plan, cycle = excluded.cycle, "
                      "base_cents = excluded.base_cents, quota = excluded.quota, used = excluded.used, "
                      "overage_units = excluded.overage_units, overage_cents = excluded.overage_cents, total_cents = excluded.total_cents",
                      (st["id"], st["account_id"], period, st["plan"], st["cycle"], st["base_cents"], st["quota"], st["used"],
                       st["overage_units"], st["overage_cents"], st["total_cents"], st["currency"], now()))
            out.append(st)
        event(c, None, by, "statements.generated", {"period": period, "count": len(out)})
    return out


def list_statements(account_id: Optional[str] = None, period: Optional[str] = None) -> List[Dict[str, Any]]:
    q, a = "SELECT * FROM statements WHERE 1=1", []
    if account_id:
        q += " AND account_id = ?"; a.append(account_id)
    if period:
        q += " AND period = ?"; a.append(period)
    return [dict(r) for r in conn().execute(q + " ORDER BY period DESC, account_id LIMIT 2000", a).fetchall()]


def mark_statement(statement_id: str, status: str, by: str, e_invoice_no: Optional[str] = None,
                   provider: Optional[str] = None, provider_ref: Optional[str] = None) -> Dict[str, Any]:
    if status not in ("issued", "paid", "void"):
        raise CommerceError(400, "bad_status", "status must be issued, paid or void.")
    col = {"issued": "issued_at", "paid": "paid_at", "void": "issued_at"}[status]
    with tx() as c:
        r = c.execute("UPDATE statements SET status = ?, {} = ?, e_invoice_no = COALESCE(?, e_invoice_no), "
                      "provider = COALESCE(?, provider), provider_ref = COALESCE(?, provider_ref) WHERE id = ?".format(col),
                      (status, now(), e_invoice_no, provider, provider_ref, statement_id))
        if not r.rowcount:
            raise CommerceError(404, "no_statement", "Statement not found.")
        row = dict(c.execute("SELECT * FROM statements WHERE id = ?", (statement_id,)).fetchone())
        event(c, row["account_id"], by, "statement." + status, {"id": statement_id, "e_invoice_no": e_invoice_no})
    return row


# ----------------------------------------------------------------------------- admin
def admin_accounts(limit: int = 500) -> List[Dict[str, Any]]:
    per = period_of()
    rows = conn().execute(
        "SELECT a.id, a.email, a.company, a.plan, a.billing_cycle, a.status, a.overage_enabled, a.plan_expires_at, a.created_at, "
        "COALESCE(u.decisions, 0) AS decisions, (SELECT COUNT(*) FROM members m WHERE m.account_id = a.id) AS members, "
        "(SELECT COUNT(*) FROM api_keys k WHERE k.account_id = a.id AND k.revoked_at IS NULL) AS keys "
        "FROM accounts a LEFT JOIN usage u ON u.account_id = a.id AND u.period = ? ORDER BY a.created_at DESC LIMIT ?",
        (per, limit)).fetchall()
    return [dict(r) for r in rows]


def admin_metrics() -> Dict[str, Any]:
    c = conn()
    by_plan = {r["plan"]: r["n"] for r in c.execute(
        "SELECT plan, COUNT(*) n FROM accounts WHERE status = 'active' GROUP BY plan").fetchall()}
    mrr = 0
    for r in c.execute("SELECT plan, billing_cycle, plan_expires_at FROM accounts WHERE status = 'active'").fetchall():
        if r["plan_expires_at"] and r["plan_expires_at"] < now():
            continue
        mrr += P.monthly_base_cents(r["plan"], r["billing_cycle"])
    per = period_of()
    dec = c.execute("SELECT COALESCE(SUM(decisions), 0) FROM usage WHERE period = ?", (per,)).fetchone()[0]
    week = c.execute("SELECT COUNT(*) FROM accounts WHERE created_at > ?", (now() - 7 * 86400,)).fetchone()[0]
    pend = c.execute("SELECT COUNT(*) FROM plan_requests WHERE status = 'pending'").fetchone()[0]
    return {"period": per, "accounts_by_plan": by_plan, "accounts_total": sum(by_plan.values()),
            "mrr_cents": mrr, "currency": P.CATALOG.get("currency", "USD"), "decisions_this_period": dec,
            "signups_7d": week, "pending_plan_requests": pend}


# ----------------------------------------------------------------------------- card payments (iyzico checkout form)
PAYMENT_PERIOD_DAYS = {"monthly": 31, "yearly": 366}


def create_payment(account_id: Optional[str], kind: str, plan: Optional[str], cycle: Optional[str], net: str, vat: str,
                   total: str, provider: str, by: str, billing: Optional[Dict[str, Any]] = None,
                   currency: str = "TRY") -> Dict[str, Any]:
    pid = new_id("pay", 8)
    conv = "ans-" + secrets.token_hex(10)
    with tx() as c:
        c.execute("INSERT INTO payments (id, account_id, kind, plan, cycle, net_try, vat_try, total_try, currency, provider, conversation_id, "
                  "created_by, created_at, billing_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                  (pid, account_id, kind, plan, cycle, net, vat, total, currency, provider, conv, by, now(),
                   json.dumps(billing or {}, ensure_ascii=False)))
        event(c, account_id, by, "payment.initiated", {"payment_id": pid, "plan": plan, "cycle": cycle, "total_try": total, "currency": currency})
    return get_payment(pid)


def get_payment(pid: str = None, token: str = None, conversation_id: str = None) -> Optional[Dict[str, Any]]:
    if pid:
        r = conn().execute("SELECT * FROM payments WHERE id = ?", (pid,)).fetchone()
    elif token:
        r = conn().execute("SELECT * FROM payments WHERE token = ?", (token,)).fetchone()
    else:
        r = conn().execute("SELECT * FROM payments WHERE conversation_id = ?", (conversation_id,)).fetchone()
    return _row(r)


def set_payment_token(pid: str, token: str) -> None:
    with tx() as c:
        c.execute("UPDATE payments SET token = ? WHERE id = ?", (token, pid))


def fail_payment(pid: str, error: str, status: str = "failed") -> None:
    with tx() as c:
        c.execute("UPDATE payments SET status = ?, error = ? WHERE id = ? AND status IN ('initiated', 'pending_review')",
                  (status, (error or "")[:300], pid))


def complete_payment(pid: str, payment_id: str, fraud_status: int, card_last4: Optional[str]) -> Dict[str, Any]:
    """Idempotent: the first call marks the payment paid and activates or extends the plan; later calls return it unchanged."""
    with tx() as c:
        pay = _row(c.execute("SELECT * FROM payments WHERE id = ?", (pid,)).fetchone())
        if not pay:
            raise CommerceError(404, "no_payment", "Payment not found.")
        if pay["status"] == "paid":
            return {"payment": pay, "activated": False, "first": False}
        t = now()
        start = end = None
        if pay["kind"] == "plan" and pay["account_id"]:
            acc = _row(c.execute("SELECT * FROM accounts WHERE id = ?", (pay["account_id"],)).fetchone())
            # renewal of the same plan extends from the current end; anything else starts now
            base = acc["plan_expires_at"] if (acc and acc["plan"] == pay["plan"] and acc["plan_expires_at"]
                                              and acc["plan_expires_at"] > t) else t
            start, end = base, base + PAYMENT_PERIOD_DAYS.get(pay["cycle"], 31) * 86400
            c.execute("UPDATE accounts SET plan = ?, billing_cycle = ?, plan_started_at = COALESCE(?, plan_started_at), "
                      "plan_expires_at = ?, status = CASE WHEN status = 'suspended' THEN 'active' ELSE status END WHERE id = ?",
                      (pay["plan"], pay["cycle"], t if base == t else None, end, pay["account_id"]))
            c.execute("UPDATE plan_requests SET status = 'approved', handled_at = ?, handled_by = 'iyzico' "
                      "WHERE account_id = ? AND status = 'pending' AND plan = ?", (t, pay["account_id"], pay["plan"]))
            event(c, pay["account_id"], "iyzico", "plan.paid", {"plan": pay["plan"], "cycle": pay["cycle"], "until": end})
        c.execute("UPDATE payments SET status = 'paid', payment_id = ?, fraud_status = ?, card_last4 = ?, paid_at = ?, "
                  "period_start = ?, period_end = ?, error = NULL WHERE id = ?",
                  (str(payment_id), fraud_status, card_last4, t, start, end, pid))
        event(c, pay["account_id"], "iyzico", "payment.paid", {"payment_id": pid, "iyzico_payment_id": str(payment_id),
                                                                 "total_try": pay["total_try"]})
        pay = _row(c.execute("SELECT * FROM payments WHERE id = ?", (pid,)).fetchone())
    return {"payment": pay, "activated": pay["kind"] == "plan", "first": True}


def mark_refunded(pid: str, by: str, revoke_plan: bool = True, note: Optional[str] = None) -> Dict[str, Any]:
    """Records a cancel/refund done in the iyzico panel. With revoke_plan the paid period is taken back:
    the plan end moves back to where it was before this payment (an account with nothing left falls to Explore)."""
    with tx() as c:
        pay = _row(c.execute("SELECT * FROM payments WHERE id = ?", (pid,)).fetchone())
        if not pay:
            raise CommerceError(404, "no_payment", "Payment not found.")
        if pay["status"] != "paid":
            raise CommerceError(409, "not_paid", "Only a paid payment can be marked refunded (status: {}).".format(pay["status"]))
        revoked = False
        if revoke_plan and pay["kind"] == "plan" and pay["account_id"] and pay["period_end"]:
            acc = _row(c.execute("SELECT * FROM accounts WHERE id = ?", (pay["account_id"],)).fetchone())
            if acc and acc["plan"] == pay["plan"] and acc["plan_expires_at"]:
                new_end = acc["plan_expires_at"] - (pay["period_end"] - pay["period_start"])
                c.execute("UPDATE accounts SET plan_expires_at = ? WHERE id = ?", (min(new_end, acc["plan_expires_at"]), acc["id"]))
                if new_end <= now():
                    c.execute("UPDATE accounts SET plan = 'kesif', billing_cycle = 'monthly', plan_expires_at = NULL, "
                              "overage_enabled = 0 WHERE id = ?", (acc["id"],))
                revoked = True
        c.execute("UPDATE payments SET status = 'refunded', error = ? WHERE id = ?", ((note or "refunded")[:300], pid))
        event(c, pay["account_id"], by, "payment.refunded", {"payment_id": pid, "plan_revoked": revoked, "note": note})
    return {"payment": get_payment(pid), "plan_revoked": revoked}


def list_payments(account_id: Optional[str] = None, limit: int = 200) -> List[Dict[str, Any]]:
    q, a = "SELECT * FROM payments", []
    if account_id:
        q += " WHERE account_id = ?"; a.append(account_id)
    rows = [dict(r) for r in conn().execute(q + " ORDER BY created_at DESC LIMIT ?", a + [limit]).fetchall()]
    for r in rows:
        r.pop("billing_json", None) if account_id else None
    return rows


def expiring_accounts(within_days: int = 7) -> List[Dict[str, Any]]:
    t = now()
    return [dict(r) for r in conn().execute(
        "SELECT * FROM accounts WHERE status = 'active' AND plan_expires_at IS NOT NULL AND plan_expires_at > ? AND plan_expires_at < ? "
        "AND plan IN ('gelistirici', 'pro')", (t, t + within_days * 86400)).fetchall()]


def reminded(account_id: str, expires_at: float) -> bool:
    """True when a renewal reminder for this expiry was already sent; otherwise records it (atomically) and returns False."""
    key = "renewal.reminded:{}".format(int(expires_at))
    with tx() as c:
        if c.execute("SELECT 1 FROM events WHERE account_id = ? AND action = ?", (account_id, key)).fetchone():
            return True
        event(c, account_id, "system", key)
    return False


def account_events(account_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    return [dict(r) for r in conn().execute("SELECT ts, actor, action, detail FROM events WHERE account_id = ? ORDER BY id DESC LIMIT ?",
                                            (account_id, limit)).fetchall()]


# ----------------------------------------------------------------------------- retention
def purge() -> Dict[str, int]:
    """Applies each plan's retention to decisions and resolved reviews; drops expired tokens and sessions."""
    t = now()
    removed = {"decisions": 0, "reviews": 0, "tokens": 0, "sessions": 0}
    accs = [dict(r) for r in conn().execute("SELECT id, plan, plan_expires_at FROM accounts").fetchall()]
    with tx() as c:
        for a in accs:
            keep = plan_of(a)["retention_days"] * 86400
            removed["decisions"] += c.execute("DELETE FROM decisions WHERE account_id = ? AND ts < ?", (a["id"], t - keep)).rowcount
            removed["reviews"] += c.execute("DELETE FROM reviews WHERE account_id = ? AND status != 'pending' AND ts < ?",
                                            (a["id"], t - keep)).rowcount
        removed["tokens"] = c.execute("DELETE FROM login_tokens WHERE expires_at < ?", (t - 86400,)).rowcount
        removed["sessions"] = c.execute("DELETE FROM sessions WHERE expires_at < ? OR revoked_at < ?", (t, t - 86400)).rowcount
        c.execute("DELETE FROM webhook_deliveries WHERE ts < ?", (t - 30 * 86400,))
        c.execute("DELETE FROM usage_daily WHERE day < ?", (day_of(t - 400 * 86400),))
    return removed
