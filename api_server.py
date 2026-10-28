"""
answerr REST API (v1.3.1)
ITouch Bilişim Sistemleri Ltd. Şti. — https://answerr.me

Endpoints
  GET    /                           service info
  GET    /v1/health                  health
  GET    /v1/presets, /v1/domains    demo catalog
  POST   /v1/decide                  typed decision; inline `policy` or `gate_id`; full trace
  GET    /v1/gates                   built-in gates (+ your own with an API key)
  POST   /v1/gates                   register a gate            (API key required)
  DELETE /v1/gates/{gate_id}         delete your gate           (API key required)
  POST   /v1/gates/{gate_id}/decide  decide with a gate         (API key required for custom gates)
  POST   /v1/policies/compile        natural language -> draft policy, tests and checks (never registers)
  POST   /v1/systemone               JevBench wire format (research)
  POST   /v1/chat/completions        OpenAI-compatible adapter (research)
  …      /v1/auth, /v1/account, /v1/reviews, /v1/backtest, /v1/plans, /v1/admin   commercial layer (commerce/router.py)
  GET    /v1/docs, /v1/redoc, /v1/openapi.json   interactive reference (under /v1 because only /v1 is proxied)

Verdicts for gated / strict / agent-tool requests come from policy_kernel.py, which is
mirrored by js/policy-kernel.js and checked for parity in tests/.

Configuration (environment, e.g. /etc/answerr/answerr.env):
  ANSWERR_API_KEYS          "tenant1:key1,tenant2:key2"
  ANSWERR_GATES_PATH        custom gate store (default /var/lib/answerr/gates.json)
  ANSWERR_RATELIMIT_DB      shared rate-limit store for all workers (default /var/lib/answerr/ratelimit.sqlite)
  ANSWERR_TRUSTED_PROXIES   hops skipped in X-Forwarded-For (default 127.0.0.1,::1,10.0.2.2 = VirtualBox NAT)
  RECAPTCHA_SECRET          reCAPTCHA v3 secret for the answerr.me site key
  RECAPTCHA_MIN_SCORE       default 0.5
  RECAPTCHA_HOSTNAMES       default answerr.me,www.answerr.me
  ANSWERR_WERR_PATH         path of the werr research package (default /home/pcworm/werr)
  ANSWERR_COMMERCE_DB       accounts, keys, usage, decision log, reviews (default /var/lib/answerr/commerce.sqlite)
  ANSWERR_ADMIN_KEY         ITouch operations key for /v1/admin/* (>= 24 chars; unset = admin API off)
  ANSWERR_CONSOLE_URL       console address used in sign-in e-mails (default https://answerr.me/pro/console/)
  ANSWERR_PAYMENT_PROVIDER  manual (default) | iyzico (see docs/commerce/IYZICO_ENTEGRASYONU.md)
"""
import hashlib
import hmac
import json
import math
import os
import re
import sys
import tempfile
import threading
import time
import urllib.parse
import urllib.request
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Tuple, Union

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(1, os.environ.get("ANSWERR_WERR_PATH", "/home/pcworm/werr"))
import werr  # noqa: E402  (research engine: fractal telemetry, choice/score, legacy presets)
import werr as wevv  # noqa: E402,F401  backward-compatibility alias

import access_mailer  # noqa: E402
import policy_checks  # noqa: E402
import policy_compiler  # noqa: E402
import policy_kernel as PK  # noqa: E402
from commerce import mail as CMAIL  # noqa: E402
from commerce import router as CROUTER  # noqa: E402
from commerce import store as CS  # noqa: E402
from commerce import webhooks as CHOOKS  # noqa: E402

API_VERSION = "1.3.1"
START_TIME = time.time()


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
def _parse_keys(raw: str) -> Dict[str, str]:
    out = {}
    for part in (raw or "").split(","):
        part = part.strip()
        if not part or ":" not in part:
            continue
        tenant, key = part.split(":", 1)
        if tenant.strip() and len(key.strip()) >= 24:
            out[key.strip()] = tenant.strip()
    return out


API_KEYS = _parse_keys(os.environ.get("ANSWERR_API_KEYS", ""))
GATES_PATH = os.environ.get("ANSWERR_GATES_PATH", "/var/lib/answerr/gates.json")
TRUSTED_PROXIES = {p.strip() for p in os.environ.get("ANSWERR_TRUSTED_PROXIES", "127.0.0.1,::1,10.0.2.2").split(",") if p.strip()}
RECAPTCHA_SECRET = os.environ.get("RECAPTCHA_SECRET", "").strip()
RECAPTCHA_MIN_SCORE = float(os.environ.get("RECAPTCHA_MIN_SCORE", "0.5"))
RECAPTCHA_HOSTNAMES = {h.strip() for h in os.environ.get("RECAPTCHA_HOSTNAMES", "answerr.me,www.answerr.me").split(",") if h.strip()}
RECAPTCHA_ACTIONS = {"decide", "compile", "sandbox", "access"}

GATE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_\-]{2,63}$")
MAX_GATES_TOTAL = 1000
MAX_GATES_PER_TENANT = 200
MAX_RULES = 100
MAX_REQUEST_BODY_BYTES = 65536


def _bearer(request: Request) -> str:
    key = request.headers.get("x-api-key") or ""
    auth = request.headers.get("authorization") or ""
    if not key and auth.lower().startswith("bearer "):
        key = auth[7:].strip()
    return key


def authenticate_principal(request: Request) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """(tenant, principal). Internal keys from ANSWERR_API_KEYS give a tenant without a principal
    (no metering). Customer API keys (ans_live_) and console sessions (ans_sess_) give tenant
    'acct:<id>' and a principal with account, role and channel."""
    key = _bearer(request)
    if not key:
        return None, None
    if key.startswith("ans_live_") or key.startswith("ans_sess_"):
        try:
            p = CS.resolve_api_key(key) if key.startswith("ans_live_") else CS.resolve_session(key)
        except Exception as e:  # commerce store unavailable: treat as anonymous, never 500
            print("[answerr] commerce auth unavailable:", e, file=sys.stderr)
            p = None
        return ("acct:" + p["account_id"], p) if p else (None, None)
    for k, tenant in API_KEYS.items():
        if hmac.compare_digest(k.encode(), key.encode()):
            return tenant, None
    return None, None


def authenticate(request: Request) -> Optional[str]:
    """Returns the tenant name for a valid key or session, else None."""
    return authenticate_principal(request)[0]


def _strip_port(entry: str) -> str:
    e = entry.strip().strip('"')
    if e.startswith("["):                      # [ipv6]:port
        return e[1:e.index("]")] if "]" in e else e
    if e.count(":") == 1:                      # ipv4:port (IIS ARR appends the client port)
        return e.split(":", 1)[0]
    return e


def client_ip(request: Request) -> str:
    """Real client address behind IIS (ARR) -> VirtualBox NAT -> Apache -> uvicorn.

    IIS appends "client:port" to X-Forwarded-For and Apache appends the NAT gateway
    (10.0.2.2), so a request reaches us as  XFF="<anything the client sent>, client:port, 10.0.2.2"
    from peer 127.0.0.1. Walking the chain from the right and skipping trusted hops
    yields the address IIS saw; entries the client wrote itself are never reached."""
    peer = request.client.host if request.client else "0.0.0.0"
    if peer not in TRUSTED_PROXIES:
        return peer
    chain = [_strip_port(p) for p in (request.headers.get("x-forwarded-for") or "").split(",") if p.strip()]
    for hop in reversed(chain):
        if hop and hop not in TRUSTED_PROXIES:
            return hop
    real = (request.headers.get("x-real-ip") or "").strip()
    return real or peer


def via_iis(request: Request) -> bool:
    return bool(request.headers.get("x-arr-log-id"))


# -----------------------------------------------------------------------------
# Rate limiting (per client IP, or per tenant for API-key callers)
# -----------------------------------------------------------------------------
class SlidingWindowLimiter:
    """Sliding-window limiter shared by all uvicorn workers through one SQLite file
    (ANSWERR_RATELIMIT_DB). Falls back to per-process memory if the file is unusable."""
    TIERS = {
        "anonymous": (60, 10),     # per window, per second
        "verified": (120, 20),     # reCAPTCHA-verified browser
        "api_key": (600, 50),
        "direct_shared": (300, 30),   # all non-IIS (direct :4431) anonymous traffic together
        "access_form": (5, 5),        # early-access form: 5 per hour per IP (window set below)
    }

    def __init__(self, window_seconds: int = 60, name: str = "rl"):
        self.window = window_seconds
        self.name = name
        self.lock = threading.Lock()
        self.hits: Dict[str, deque] = defaultdict(deque)
        self.last_cleanup = time.time()
        self.db_path = os.environ.get("ANSWERR_RATELIMIT_DB", "/var/lib/answerr/ratelimit.sqlite")
        self._local = threading.local()
        self.shared = self._init_db()

    def _conn(self):
        import sqlite3
        c = getattr(self._local, "conn", None)
        if c is None:
            c = sqlite3.connect(self.db_path, timeout=2.0, isolation_level=None)
            c.execute("PRAGMA journal_mode=WAL")
            c.execute("PRAGMA synchronous=OFF")
            self._local.conn = c
        return c

    def _init_db(self) -> bool:
        try:
            os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
            c = self._conn()
            c.execute("CREATE TABLE IF NOT EXISTS hits (k TEXT NOT NULL, ts REAL NOT NULL)")
            c.execute("CREATE INDEX IF NOT EXISTS hits_k_ts ON hits (k, ts)")
            return True
        except Exception as e:
            print("[answerr] shared rate limiter unavailable, using per-process memory:", e, file=sys.stderr)
            return False

    def check(self, ident: str, tier: str) -> Tuple[bool, int, int, int]:
        per_win, per_sec = self.TIERS[tier]
        key = "{}:{}:{}".format(self.name, tier, ident)
        now = time.time()
        if self.shared:
            try:
                return self._check_db(key, now, per_win, per_sec)
            except Exception:
                pass  # fall through to memory
        return self._check_mem(key, now, per_win, per_sec)

    def _check_db(self, key, now, per_win, per_sec):
        c = self._conn()
        c.execute("BEGIN IMMEDIATE")
        try:
            if now - self.last_cleanup > 300:
                c.execute("DELETE FROM hits WHERE ts < ?", (now - 3600,))
                self.last_cleanup = now
            c.execute("DELETE FROM hits WHERE k = ? AND ts < ?", (key, now - self.window))
            n_win, oldest, n_sec = c.execute(
                "SELECT COUNT(*), MIN(ts), SUM(CASE WHEN ts >= ? THEN 1 ELSE 0 END) FROM hits WHERE k = ?",
                (now - 1.0, key)).fetchone()
            n_sec = n_sec or 0
            if n_sec >= per_sec:
                c.execute("COMMIT")
                return False, per_win, 0, 1
            if n_win >= per_win:
                c.execute("COMMIT")
                return False, per_win, 0, max(1, int(self.window - (now - (oldest or now))))
            c.execute("INSERT INTO hits (k, ts) VALUES (?, ?)", (key, now))
            c.execute("COMMIT")
            return True, per_win, per_win - n_win - 1, 0
        except Exception:
            c.execute("ROLLBACK")
            raise

    def _check_mem(self, key, now, per_win, per_sec):
        with self.lock:
            if now - self.last_cleanup > 300:
                cutoff = now - self.window
                for k in [k for k, q in self.hits.items() if not q or q[-1] < cutoff]:
                    del self.hits[k]
                self.last_cleanup = now
            q = self.hits[key]
            while q and q[0] < now - self.window:
                q.popleft()
            if sum(1 for t in q if t >= now - 1.0) >= per_sec:
                return False, per_win, 0, 1
            if len(q) >= per_win:
                return False, per_win, 0, max(1, int(self.window - (now - q[0])))
            q.append(now)
            return True, per_win, per_win - len(q), 0


LIMITER = SlidingWindowLimiter()


# -----------------------------------------------------------------------------
# reCAPTCHA v3 — verified on the server, result cached per token
# -----------------------------------------------------------------------------
_RECAPTCHA_CACHE: Dict[str, Tuple[float, str]] = {}
_RECAPTCHA_LOCK = threading.Lock()


def verify_recaptcha(token: Optional[str], ip: str) -> str:
    """Returns 'verified', 'failed', 'absent' or 'not_configured'."""
    if not token:
        return "absent"
    if not RECAPTCHA_SECRET:
        return "not_configured"
    digest = hashlib.sha256(token.encode()).hexdigest()
    now = time.time()
    with _RECAPTCHA_LOCK:
        hit = _RECAPTCHA_CACHE.get(digest)
        if hit and now - hit[0] < 120:
            return hit[1]
    status = "failed"
    try:
        data = urllib.parse.urlencode({"secret": RECAPTCHA_SECRET, "response": token, "remoteip": ip}).encode()
        req = urllib.request.Request("https://www.google.com/recaptcha/api/siteverify", data=data, method="POST")
        with urllib.request.urlopen(req, timeout=3) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        if (body.get("success") and float(body.get("score", 0)) >= RECAPTCHA_MIN_SCORE
                and body.get("hostname") in RECAPTCHA_HOSTNAMES
                and body.get("action") in RECAPTCHA_ACTIONS):
            status = "verified"
    except Exception:
        status = "failed"
    with _RECAPTCHA_LOCK:
        if len(_RECAPTCHA_CACHE) > 5000:
            _RECAPTCHA_CACHE.clear()
        _RECAPTCHA_CACHE[digest] = (now, status)
    return status


# -----------------------------------------------------------------------------
# Gate registry: built-in gates (read-only) + tenant gates persisted to disk
# -----------------------------------------------------------------------------
def _load_builtin() -> Dict[str, Dict[str, Any]]:
    with open(os.path.join(HERE, "policies", "builtin_gates.json"), encoding="utf-8") as f:
        gates = json.load(f)
    for g in gates.values():
        g["policy_seal"] = PK.policy_seal(g)
    return gates


class GateStore:
    """Tenant gates in one JSON file. Safe with several uvicorn workers: writes take an
    exclusive flock and replace the file atomically; readers reload when the mtime changes."""

    def __init__(self, path: str):
        self.path = path
        self.lock = threading.Lock()
        self.gates: Dict[str, Dict[str, Any]] = {}
        self._mtime = None
        self.available = True
        self._reload(force=True)

    def _reload(self, force: bool = False):
        if not self.available:
            return
        try:
            st = os.stat(self.path)
            # inode changes on every atomic replace; mtime alone can repeat within one clock tick
            m = (st.st_ino, st.st_mtime_ns, st.st_size)
        except FileNotFoundError:
            self.gates, self._mtime = {}, None
            return
        if not force and m == self._mtime:
            return
        try:
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
            self.gates = data if isinstance(data, dict) else {}
            self._mtime = m
        except Exception as e:  # corrupt store: keep serving built-ins, never overwrite it
            print("[answerr] gate store unreadable, tenant gates disabled:", e, file=sys.stderr)
            self.available = False

    def _locked(self):
        try:
            import fcntl
            has_fcntl = True
        except ImportError:
            has_fcntl = False

        class _L:
            def __enter__(s):
                d = os.path.dirname(self.path) or "."
                os.makedirs(d, exist_ok=True)
                s.f = open(self.path + ".lock", "a")
                if has_fcntl:
                    fcntl.flock(s.f, fcntl.LOCK_EX)
                else:
                    try:
                        import msvcrt
                        msvcrt.locking(s.f.fileno(), msvcrt.LK_LOCK, 1)
                    except Exception:
                        pass
                return s

            def __exit__(s, *a):
                if has_fcntl:
                    fcntl.flock(s.f, fcntl.LOCK_UN)
                else:
                    try:
                        import msvcrt
                        msvcrt.locking(s.f.fileno(), msvcrt.LK_UNLCK, 1)
                    except Exception:
                        pass
                s.f.close()
        return _L()

    def _save(self):
        d = os.path.dirname(self.path) or "."
        fd, tmp = tempfile.mkstemp(dir=d, prefix=".gates.", suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(self.gates, f, ensure_ascii=False, indent=1, sort_keys=True)
        os.chmod(tmp, 0o600)
        os.replace(tmp, self.path)
        st = os.stat(self.path)
        self._mtime = (st.st_ino, st.st_mtime_ns, st.st_size)

    def get(self, gate_id: str) -> Optional[Dict[str, Any]]:
        self._reload()
        return self.gates.get(gate_id)

    def owned_by(self, tenant: str) -> List[Dict[str, Any]]:
        self._reload()
        return [g for g in self.gates.values() if g.get("tenant") == tenant]

    def count(self) -> int:
        self._reload()
        return len(self.gates)

    def put(self, gate: Dict[str, Any], tenant: str):
        if not self.available:
            raise HTTPException(503, "Gate store is unavailable.")
        with self.lock, self._locked():
            self._reload(force=True)
            existing = self.gates.get(gate["gate_id"])
            if existing and existing.get("tenant") != tenant:
                raise HTTPException(403, "Gate id belongs to another tenant.")
            if not existing:
                if len(self.gates) >= MAX_GATES_TOTAL:
                    raise HTTPException(507, "Gate store is full.")
                if sum(1 for g in self.gates.values() if g.get("tenant") == tenant) >= MAX_GATES_PER_TENANT:
                    raise HTTPException(429, "Gate limit for this tenant reached.")
            self.gates[gate["gate_id"]] = gate
            self._save()

    def drop_tenant(self, tenant: str) -> int:
        if not self.available:
            return 0
        with self.lock, self._locked():
            self._reload(force=True)
            ids = [k for k, g in self.gates.items() if g.get("tenant") == tenant]
            for k in ids:
                del self.gates[k]
            if ids:
                self._save()
            return len(ids)

    def delete(self, gate_id: str, tenant: str) -> bool:
        if not self.available:
            raise HTTPException(503, "Gate store is unavailable.")
        with self.lock, self._locked():
            self._reload(force=True)
            g = self.gates.get(gate_id)
            if not g:
                return False
            if g.get("tenant") != tenant:
                raise HTTPException(403, "Gate id belongs to another tenant.")
            del self.gates[gate_id]
            self._save()
            return True


BUILTIN_GATES = _load_builtin()
GATE_STORE = GateStore(GATES_PATH)
COMMERCIAL_GATES = BUILTIN_GATES  # backward-compatible name used by older clients/tests


def resolve_gate(gate_id: Optional[str], tenant: Optional[str]) -> Optional[Dict[str, Any]]:
    if not gate_id:
        return None
    if gate_id in BUILTIN_GATES:
        return BUILTIN_GATES[gate_id]
    g = GATE_STORE.get(gate_id)
    if not g:
        raise HTTPException(404, "Gate '{}' not found.".format(gate_id))
    if g.get("tenant") != tenant:
        raise HTTPException(401 if tenant is None else 403, "This gate needs its owner's API key.")
    return g


# -----------------------------------------------------------------------------
# Research engine instances (werr)
# -----------------------------------------------------------------------------
DEFAULT_ROUTER = werr.create_smart_router()
SYSTEMONE_ROUTER = werr.WerrEngine(
    enable_domain=True, enable_lexical=True, enable_resonance=True,
    mode="hybrid", domain_mode="multi", tripod=True,
)
DOMAIN_GATES = werr.DOMAIN_GATES

# Predefined domain presets matching answerr.me web client
PRESETS = {
    "api_security": {
        "title": "API Gateway & Security Guard",
        "description": "Zero-trust sub-millisecond edge firewall packet & credential evaluation",
        "default_state": {"user_role": "guest", "failed_attempts": 2, "req_frequency": 12.0},
        "default_questions": {
            "allow_request": {"type": "noul", "text": "Should this incoming request be permitted through?"},
            "route_destination": {
                "type": "choice",
                "text": "Target gateway pipeline",
                "criteria": {
                    "direct_api": "Direct API route (Fast Path)",
                    "rate_limiter": "Rate limiter queue buffer",
                    "sandbox_audit": "Sandbox quarantine / Auth challenge",
                    "drop_packet": "Drop packet & block IP"
                }
            },
            "threat_score": {
                "type": "score",
                "text": "Threat assessment score",
                "criteria": ["Clean / Safe", "Minor Anomaly", "High Risk", "Critical Threat"]
            }
        }
    },
    "ddos_mitigation": {
        "title": "L7 Edge DDoS & Bot Mitigation",
        "description": "Adaptive volumetric traffic filtering and rate governor",
        "default_state": {"syn_rate": 840, "ua_entropy": 0.12, "geo_burst": True, "failed_ratio": 0.88},
        "default_questions": {
            "pass_filter": {"type": "noul", "text": "Pass packet without challenge?"},
            "defense_action": {
                "type": "choice",
                "text": "Mitigation strategy",
                "criteria": {
                    "pass": "Bypass inspection",
                    "js_challenge": "Issue Silent JS Proof-of-Work",
                    "captcha": "Serve Interactive Verification",
                    "blackhole": "BGP Anycast Blackhole"
                }
            },
            "anomaly_level": {
                "type": "score",
                "text": "Traffic anomaly scale",
                "criteria": ["Nominal", "Elevated", "Volumetric Attack", "Infrastructure Threat"]
            }
        }
    },
    "financial_risk": {
        "title": "High-Frequency Financial Risk Evaluator",
        "description": "Instant fraud scoring and transaction clearance without LLM hallucinations",
        "default_state": {"amount": 25000, "user_trust_score": 0.45, "device_anomaly": True, "velocity": 8},
        "default_questions": {
            "approve_transfer": {"type": "noul", "text": "Approve transaction immediately?"},
            "action": {
                "type": "choice",
                "text": "Payment gateway routing",
                "criteria": {
                    "instant_clearing": "Instant STP Clearing",
                    "mfa_verify": "Step-up Multi-Factor Authentication",
                    "manual_hold": "Fraud Queue Manual Review",
                    "immediate_block": "Immediate Account Block"
                }
            },
            "risk_index": {
                "type": "score",
                "text": "Financial exposure score",
                "criteria": ["Safe", "Moderate", "High Exposure", "Definite Fraud"]
            }
        }
    },
    "robotics_industrial": {
        "title": "Autonomous Robotics & Industrial Safety Guard",
        "description": "Real-time mechanical torque, thermal anomaly, and emergency stop interlock",
        "default_state": {"joint_torque_nm": 98.4, "temp_celsius": 82.0, "vibration_g": 2.4, "proximity_m": 0.35},
        "default_questions": {
            "continue_operation": {"type": "noul", "text": "Is actuator state safe for continuous trajectory?"},
            "safety_protocol": {
                "type": "choice",
                "text": "Motor controller command",
                "criteria": {
                    "nominal_run": "Nominal Kinematic Velocity",
                    "torque_derate": "Derate Torque 40%",
                    "controlled_halt": "Controlled Deceleration to Standstill",
                    "hard_estop": "Trigger Hard Hardware E-STOP"
                }
            },
            "hazard_level": {
                "type": "score",
                "text": "Mechanical structural stress score",
                "criteria": ["Normal Operation", "Elevated Strain", "Warning Limit", "Critical Failure Risk"]
            }
        }
    },
    "ecommerce_fraud": {
        "title": "E-Commerce Checkout Fraud Guard",
        "description": "Checkout cart velocity, shipping delta, and stolen card protection",
        "default_state": {"cart_value": 1400, "shipping_billing_mismatch": True, "card_attempts": 3},
        "default_questions": {
            "allow_checkout": {"type": "noul", "text": "Allow order placement?"},
            "verification_tier": {
                "type": "choice",
                "text": "Checkout challenge tier",
                "criteria": {
                    "seamless": "Frictionless 1-Click Order",
                    "3ds_secure": "Trigger 3D Secure 2.0 Challenge",
                    "manual_hold": "Hold Order for Verification",
                    "void_transaction": "Decline and Flag Cardholder"
                }
            },
            "risk_score": {
                "type": "score",
                "text": "Cart risk index",
                "criteria": ["Low Risk", "Medium", "Suspicious", "High Fraud Likelihood"]
            }
        }
    }
}





# -----------------------------------------------------------------------------
# App, CORS, security middleware
# -----------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    t0 = time.perf_counter()
    DEFAULT_ROUTER.decide(state={"warmup": True}, questions={"ready": werr.NoulQuestion("System ready?")})
    PK.evaluate({"tool_name": "read_status"}, BUILTIN_GATES["agent_mcp_guard"])
    try:
        CS.init()
        threading.Thread(target=_housekeeping, daemon=True).start()
    except Exception as e:
        print("[answerr] commerce store unavailable:", e, file=sys.stderr)
    print("[answerr] API {} ready in {:.1f} ms; {} built-in gates, {} tenant gates, {} API keys, reCAPTCHA {}".format(
        API_VERSION, (time.perf_counter() - t0) * 1000, len(BUILTIN_GATES), GATE_STORE.count(),
        len(API_KEYS), "on" if RECAPTCHA_SECRET else "off"))
    yield


def _housekeeping():
    """Hourly retention purge and renewal reminders (idempotent; every worker may run them)."""
    while True:
        time.sleep(3600)
        try:
            CS.purge()
        except Exception as e:
            print("[answerr] purge failed:", e, file=sys.stderr)
        try:
            renewal_reminders()
        except Exception as e:
            print("[answerr] renewal reminders failed:", e, file=sys.stderr)


def renewal_reminders() -> int:
    """One e-mail per paid period, 7 days before it ends (the store records it atomically, so workers do not duplicate)."""
    from commerce import mail as CM
    sent = 0
    for acc in CS.expiring_accounts(7):
        if not CS.reminded(acc["id"], acc["plan_expires_at"]):
            CM.renewal_reminder(acc, acc["plan_expires_at"])
            sent += 1
    return sent


app = FastAPI(
    title="answerr Decision API",
    description="Deterministic decision policies written in natural language, compiled to explicit rules, "
                "executed with a full trace. ITouch Bilişim Sistemleri Ltd. Şti.",
    version=API_VERSION,
    lifespan=lifespan,
    docs_url="/v1/docs",
    redoc_url="/v1/redoc",
    openapi_url="/v1/openapi.json",
)


@app.exception_handler(CS.CommerceError)
async def _commerce_error(request: Request, exc: CS.CommerceError):
    return CROUTER.error_response(exc)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://answerr.me", "https://www.answerr.me", "https://api.answerr.me",
                   "https://werr.io", "https://www.werr.io",  # 28 Oct 2026: werr.io live demos (systemone, chat/completions)
                   "https://pcworm.github.io", "http://localhost:3000", "http://localhost:8000",
                   "http://127.0.0.1:8000", "http://127.0.0.1:5500"],
    allow_origin_regex=r"https://([a-z0-9-]+\.)?answerr\.me",
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With", "X-API-Key", "X-Recaptcha-Token", "X-Admin-Key"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "Retry-After", "X-Answerr-Verdict", "X-Answerr-Policy-Seal",
                    "X-Answerr-Decision-Id", "X-Answerr-Quota-Remaining", "Content-Disposition"],
    max_age=86400,
)


@app.middleware("http")
async def security_middleware(request: Request, call_next):
    from starlette.concurrency import run_in_threadpool

    if request.method == "OPTIONS":
        return await call_next(request)

    if request.method in ("POST", "PUT", "PATCH"):
        cl = request.headers.get("content-length")
        if cl is None:
            return JSONResponse(status_code=411, content={"status": "error", "error": "Length Required"})
        try:
            if int(cl) > MAX_REQUEST_BODY_BYTES:
                return JSONResponse(status_code=413, content={
                    "status": "error", "error": "Payload Too Large",
                    "message": "Request body exceeds {} bytes.".format(MAX_REQUEST_BODY_BYTES)})
        except ValueError:
            return JSONResponse(status_code=400, content={"status": "error", "error": "Bad Content-Length"})

    ip = client_ip(request)
    tenant, principal = await run_in_threadpool(authenticate_principal, request)
    recaptcha = "absent"
    if tenant:
        tier, ident = "api_key", "tenant:" + tenant
    else:
        token = request.headers.get("x-recaptcha-token")
        if token:
            recaptcha = await run_in_threadpool(verify_recaptcha, token, ip)
        tier = "verified" if recaptcha == "verified" else "anonymous"
        ident = "ip:" + ip
    request.state.security = {"tenant": tenant, "rate_tier": tier, "recaptcha": recaptcha, "principal": principal}

    remaining = None
    limit = SlidingWindowLimiter.TIERS[tier][0]
    if request.url.path not in ("/health", "/v1/health", "/v1/docs", "/v1/redoc", "/v1/openapi.json"):
        ok, limit, remaining, retry = LIMITER.check(ident, tier)
        if ok and not tenant and not via_iis(request) and (request.client and request.client.host in TRUSTED_PROXIES):
            ok, _, _, retry = LIMITER.check("direct", "direct_shared")
        if not ok:
            return JSONResponse(status_code=429, headers={
                "X-RateLimit-Limit": str(limit), "X-RateLimit-Remaining": "0", "Retry-After": str(retry)},
                content={"status": "error", "error": "Too Many Requests", "rate_tier": tier,
                         "retry_after_seconds": retry})

    response: Response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(limit)
    if remaining is not None:
        response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    if not request.url.path.startswith(("/v1/docs", "/v1/redoc")):
        response.headers["Cache-Control"] = "no-store"
    response.headers["Server"] = "answerr"
    return response


def _security(request: Request) -> Dict[str, Any]:
    return getattr(request.state, "security", {"tenant": None, "rate_tier": "anonymous", "recaptcha": "absent", "principal": None})


# -----------------------------------------------------------------------------
# Schemas
# -----------------------------------------------------------------------------
ALLOWED_OPS = {">", ">=", "<", "<=", "==", "=", "!=", "in", "not_in", "has_token"}
ALLOWED_EFFECTS = {"ALLOW", "DENY", "REVIEW"}


class QuestionSpec(BaseModel):
    type: str = Field("noul", description="'noul', 'choice' or 'score'")
    text: Optional[str] = None
    instructions: Optional[str] = None
    threshold: Optional[float] = 0.5
    criteria: Optional[Union[Dict[str, str], List[str]]] = None

    @property
    def resolved_text(self) -> str:
        return (self.text or self.instructions or "Is the proposed operation safe and valid?").strip()


class WerrParamsSpec(BaseModel):
    """Full werr v0.5.2 parameter configuration (auto/preset or explicit overrides)."""
    preset: Optional[str] = Field(
        None,
        description="'auto' (default, purpose-aligned by gate/domain), 'smart_router', 'security_guard', "
                    "'risk_evaluator', 'crown_core', or 'universal_cusp'"
    )
    mode: Optional[str] = Field(None, description="'hybrid', 'lexical', 'resonance', or 'pure_fractal'")
    domain_mode: Optional[str] = Field(None, description="'multi' or 'none'")
    enable_domain: Optional[bool] = Field(None, description="Axis 1 of 8-state cube: Multi-Domain Gate routing")
    enable_lexical: Optional[bool] = Field(None, description="Axis 2 of 8-state cube: Exact keyword anchoring")
    enable_resonance: Optional[bool] = Field(None, description="Axis 3 of 8-state cube: 4-stem & Mandelbrot pole resonance")
    tripod: Optional[bool] = Field(None, description="3-point triangular probe for dynamic fused escape velocity")
    cadence_lambda: Optional[float] = Field(None, ge=0.0, le=2.0, description="Trajectory cadence coupling (lambda)")
    cadence_beta: Optional[float] = Field(None, ge=0.0, le=2.0, description="Boundary damping factor (beta)")
    cadence_alpha: Optional[float] = Field(None, ge=0.0, le=1.0, description="Resonance blending weight (alpha)")
    temp_choice: Optional[float] = Field(None, ge=0.05, le=10.0, description="Softmax temperature for 4-quadrant choice")
    resolution: Optional[int] = Field(None, ge=8, le=128, description="Manifold sampling resolution")
    max_iter: Optional[int] = Field(None, ge=8, le=256, description="Mandelbrot escape iteration ceiling")
    cx: Optional[float] = Field(None, ge=-5.0, le=5.0, description="24B seed real coordinate (c_x)")
    cy: Optional[float] = Field(None, ge=-5.0, le=5.0, description="24B seed imaginary coordinate (c_y)")
    zoom: Optional[float] = Field(None, ge=0.01, le=1000000.0, description="24B seed magnification factor (zoom)")
    auto_route: Optional[bool] = Field(None, description="Force automatic domain routing on/off")
    preferred_domain: Optional[str] = Field(None, description="Preferred domain gate key")
    telemetry_opt_in: Optional[bool] = Field(None, description="Opt in/out of anonymous open-science telemetry")


WERR_PRESETS: Dict[str, Dict[str, Any]] = {
    "smart_router": {
        "id": "smart_router",
        "title_tr": "Akıllı Yönlendirici (Dengeli 4-Kadran · [1,1,1])",
        "title_en": "Smart Router (Balanced 4-Quadrant · [1,1,1])",
        "purpose_tr": "AI ajan araç kapıları (agent_mcp_guard) ve çok alanlı genel karar orkestrasyonu için en ideal kurgu.",
        "purpose_en": "Optimal for AI agent action gates (agent_mcp_guard) and multi-domain decision orchestration.",
        "cx": -0.10109636384562,
        "cy": 0.95628651080914,
        "zoom": 45.0,
        "mode": "hybrid",
        "domain_mode": "multi",
        "enable_domain": True,
        "enable_lexical": True,
        "enable_resonance": True,
        "tripod": True,
        "cadence_lambda": 0.10,
        "cadence_beta": 0.15,
        "cadence_alpha": 0.50,
        "temp_choice": 1.25,
        "resolution": 36,
        "max_iter": 36,
        "preferred_domain": "api_security",
    },
    "security_guard": {
        "id": "security_guard",
        "title_tr": "Sıfır Güven Kalkanı (Seahorse Vadisi Keskin Sınır · [1,1,1])",
        "title_en": "Zero-Trust Security Guard (Seahorse Valley Sharp Boundary · [1,1,1])",
        "purpose_tr": "API güvenlik duvarı (api_zero_trust_waf), DDoS engelleme ve yüksek hassasiyetli erişim denetimi için en ideal kurgu.",
        "purpose_en": "Optimal for zero-trust API WAF (api_zero_trust_waf), DDoS mitigation, and high-sensitivity access control.",
        "cx": -0.7436438870371587,
        "cy": 0.1318259042053119,
        "zoom": 120.0,
        "mode": "hybrid",
        "domain_mode": "multi",
        "enable_domain": True,
        "enable_lexical": True,
        "enable_resonance": True,
        "tripod": True,
        "cadence_lambda": 0.08,
        "cadence_beta": 0.12,
        "cadence_alpha": 0.60,
        "temp_choice": 1.00,
        "resolution": 36,
        "max_iter": 48,
        "preferred_domain": "api_security",
    },
    "risk_evaluator": {
        "id": "risk_evaluator",
        "title_tr": "Finansal Risk Değerlendirici (Yumuşak Gradyan · [1,1,1])",
        "title_en": "Financial Risk Evaluator (Smooth Gradient · [1,1,1])",
        "purpose_tr": "Ödeme, 3D Secure ve e-ticaret dolandırıcılık puanlaması (fintech_payment_tr) için sürekli kaçış gradyanlı kurgu.",
        "purpose_en": "Optimal for payment risk, 3D Secure and checkout fraud scoring (fintech_payment_tr) with smooth escape gradients.",
        "cx": -0.75,
        "cy": 0.10,
        "zoom": 25.0,
        "mode": "hybrid",
        "domain_mode": "multi",
        "enable_domain": True,
        "enable_lexical": True,
        "enable_resonance": True,
        "tripod": True,
        "cadence_lambda": 0.12,
        "cadence_beta": 0.18,
        "cadence_alpha": 0.55,
        "temp_choice": 1.10,
        "resolution": 36,
        "max_iter": 48,
        "preferred_domain": "financial_risk",
    },
    "crown_core": {
        "id": "crown_core",
        "title_tr": "Crown Core · Periyot-3 Üçayak Rezonansı ([1,1,1])",
        "title_en": "Crown Core · Period-3 Tripod Resonance ([1,1,1])",
        "purpose_tr": "Endüstriyel robotik güvenlik, IoT emniyet kilidi ve Werracle Z/9Z rezonans uyumlu donanım refleksi.",
        "purpose_en": "Optimal for industrial robotics safety, IoT interlocks, and Werracle Z/9Z resonant hardware reflexes.",
        "cx": -0.1225611668766536,
        "cy": 0.7448617666197442,
        "zoom": 64.0,
        "mode": "hybrid",
        "domain_mode": "multi",
        "enable_domain": True,
        "enable_lexical": True,
        "enable_resonance": True,
        "tripod": True,
        "cadence_lambda": 0.10,
        "cadence_beta": 0.15,
        "cadence_alpha": 0.50,
        "temp_choice": 1.00,
        "resolution": 48,
        "max_iter": 64,
        "preferred_domain": "iot_safety",
    },
    "universal_cusp": {
        "id": "universal_cusp",
        "title_tr": "Saf Fraktal · Evrensel Cusp ([0,0,0] · Sıfır Sözlük)",
        "title_en": "Pure Fractal · Universal Cusp ([0,0,0] · Zero Ontology)",
        "purpose_tr": "Alan sözlüklerini kapatarak yalnızca 16B durum vektörünün 24-bayt Mandelbrot sınırındaki (∂M) saf geometrik yörüngesini çalıştırır.",
        "purpose_en": "Locks domain ontologies off and evaluates pure 16D state projection on the 24-byte Mandelbrot boundary (∂M).",
        "cx": -0.7436438870371587,
        "cy": 0.1318259042053119,
        "zoom": 50.0,
        "mode": "pure_fractal",
        "domain_mode": "none",
        "enable_domain": False,
        "enable_lexical": False,
        "enable_resonance": False,
        "tripod": True,
        "cadence_lambda": 0.10,
        "cadence_beta": 0.15,
        "cadence_alpha": 0.50,
        "temp_choice": 1.25,
        "resolution": 36,
        "max_iter": 36,
        "preferred_domain": None,
    },
}

GATE_WERR_PROFILES: Dict[str, str] = {
    "agent_mcp_guard": "smart_router",
    "fintech_payment_tr": "risk_evaluator",
    "api_zero_trust_waf": "security_guard",
    "api_security": "security_guard",
    "ddos_mitigation": "security_guard",
    "financial_risk": "risk_evaluator",
    "ecommerce_fraud": "risk_evaluator",
    "robotics_industrial": "crown_core",
    "iot_safety": "crown_core",
    "game_combat": "smart_router",
}


class DecisionRequest(BaseModel):
    state: Optional[Dict[str, Any]] = Field(default_factory=dict)
    domain: Optional[str] = None
    gate_id: Optional[str] = None
    policy: Optional[Dict[str, Any]] = Field(None, description="Inline draft policy (not stored)")
    strict_policy: Optional[bool] = False
    questions: Optional[Dict[str, QuestionSpec]] = None
    question: Optional[str] = None
    prompt: Optional[str] = None
    recaptcha_token: Optional[str] = None
    mode: Optional[str] = Field(None, description="'live' (default) or 'shadow': logged and metered, never queued for review")
    autonomous: Optional[bool] = Field(False, description="When true, suppresses REVIEW verdict for Edge AI and autonomous agents; resolves deterministically based on confidence.")
    autonomous_bias: Optional[str] = Field("balanced", description="'balanced' (default), 'permissive', or 'fail_closed'")
    observed_outcome: Optional[Any] = Field(None, description="Your own decision for this case (ALLOW/REVIEW/DENY or true/false), for shadow reports")
    external_id: Optional[str] = Field(None, max_length=120, description="Your reference (order id, tool-call id); echoed in logs, reviews and webhooks")
    enqueue_review: Optional[bool] = Field(True, description="REVIEW verdicts go to the human-review queue (Pro and above)")
    cx: Optional[float] = None
    cy: Optional[float] = None
    zoom: Optional[float] = None
    werr_preset: Optional[str] = Field(None, description="Pre-calibrated werr profile ('auto', 'smart_router', 'security_guard', 'risk_evaluator', 'crown_core', 'universal_cusp')")
    werr_params: Optional[WerrParamsSpec] = Field(None, description="Full werr engine parameter overrides")


class HardRuleSpec(BaseModel):
    id: str = Field(..., min_length=1, max_length=80)
    field: str = Field(..., min_length=1, max_length=64)
    op: str
    value: Any
    effect: str = "DENY"
    reason: Optional[str] = Field(None, max_length=500)


class PolicyGateCreateRequest(BaseModel):
    gate_id: str
    version: str = "1.0.0"
    title: str = Field("Custom policy", max_length=120)
    category: str = Field("Custom Policy", max_length=60)
    unknown_fallback: str = "abstain_review"
    fields: List[str] = Field(default_factory=list)
    required_fields: List[str] = Field(default_factory=list)
    field_aliases: Dict[str, List[str]] = Field(default_factory=dict)
    hard_rules: List[HardRuleSpec] = Field(default_factory=list)
    feature_weights: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    tool_policy: Optional[Dict[str, str]] = None
    source_prompt: Optional[str] = Field(None, max_length=4000)


class PolicyCompileRequest(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=4000)
    gate_id: Optional[str] = "draft_policy"
    domain: Optional[str] = None
    schema_fields: Optional[List[str]] = None
    sample_state: Optional[Dict[str, Any]] = None


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: Optional[str] = "werr-reflex-v1"
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.0
    max_tokens: Optional[int] = 512
    domain: Optional[str] = None
    state: Optional[Dict[str, Any]] = None
    werr_preset: Optional[str] = None
    werr_params: Optional[WerrParamsSpec] = None


def validate_policy(p: Dict[str, Any]) -> Dict[str, Any]:
    """Normalizes an inline or registered policy and rejects malformed ones."""
    if not isinstance(p, dict):
        raise HTTPException(400, "policy must be an object")
    rules = p.get("hard_rules") or p.get("hardRules") or []
    if not isinstance(rules, list) or len(rules) > MAX_RULES:
        raise HTTPException(400, "hard_rules must be a list of at most {} rules".format(MAX_RULES))
    clean_rules = []
    for r in rules:
        if not isinstance(r, dict):
            raise HTTPException(400, "each rule must be an object")
        op = r.get("op")
        eff = str(r.get("effect", "DENY")).upper()
        if op not in ALLOWED_OPS:
            raise HTTPException(400, "unsupported op '{}'".format(op))
        if eff not in ALLOWED_EFFECTS:
            raise HTTPException(400, "unsupported effect '{}'".format(eff))
        if not isinstance(r.get("field"), str) or not r["field"] or len(r["field"]) > 64:
            raise HTTPException(400, "rule field must be a non-empty string")
        clean_rules.append({"id": str(r.get("id") or ("rule_" + r["field"]))[:80], "field": r["field"], "op": op,
                            "value": r.get("value"), "effect": eff, "reason": (r.get("reason") or None)})
    tool_policy = p.get("tool_policy") or p.get("toolPolicy")
    if tool_policy is not None:
        if not isinstance(tool_policy, dict) or any(str(v).upper() not in ALLOWED_EFFECTS for v in tool_policy.values()):
            raise HTTPException(400, "tool_policy values must be ALLOW, DENY or REVIEW")
        tool_policy = {k: str(v).upper() for k, v in tool_policy.items()}
    out = {
        "gate_id": str(p.get("gate_id") or p.get("id") or "inline_policy")[:64],
        "version": str(p.get("version") or "1.0.0")[:32],
        "unknown_fallback": p.get("unknown_fallback") or p.get("unknownFallback") or "abstain_review",
        "fields": [str(f)[:64] for f in (p.get("fields") or [])][:200],
        "required_fields": [str(f)[:64] for f in (p.get("required_fields") or p.get("requiredFields") or [])][:50],
        "field_aliases": {str(k)[:64]: [str(a)[:64] for a in (v or [])][:20]
                          for k, v in (p.get("field_aliases") or p.get("fieldAliases") or {}).items()},
        "hard_rules": clean_rules,
        "feature_weights": p.get("feature_weights") or p.get("featureWeights") or {},
    }
    if tool_policy is not None:
        out["tool_policy"] = tool_policy
    for k in ("title", "category", "source_prompt"):
        if p.get(k):
            out[k] = str(p[k])[:4000]
    return out


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def resolve_werr_engine(
    cx: Optional[float] = None,
    cy: Optional[float] = None,
    zoom: Optional[float] = None,
    domain: Optional[str] = None,
    gate_id: Optional[str] = None,
    policy: Optional[Dict[str, Any]] = None,
    werr_preset: Optional[str] = None,
    werr_params: Optional[WerrParamsSpec] = None,
) -> Tuple[Any, Dict[str, Any]]:
    """Resolves purpose-aligned optimal werr parameters and applies any explicit user overrides."""
    wp = werr_params or WerrParamsSpec()
    req_preset = (wp.preset or werr_preset or "auto").strip().lower()
    target_key = domain or gate_id or (policy or {}).get("gate_id") or ""
    if req_preset == "auto" or req_preset not in WERR_PRESETS:
        base_preset_id = GATE_WERR_PROFILES.get(target_key, "smart_router")
        selection_mode = "auto_optimal"
    else:
        base_preset_id = req_preset
        selection_mode = "user_preset"

    cfg = dict(WERR_PRESETS[base_preset_id])
    policy_seed = (policy or {}).get("seed_24b") or {}
    if selection_mode == "auto_optimal" and policy_seed:
        if policy_seed.get("cx") is not None:
            cfg["cx"] = float(policy_seed["cx"])
        if policy_seed.get("cy") is not None:
            cfg["cy"] = float(policy_seed["cy"])
        if policy_seed.get("zoom") is not None:
            cfg["zoom"] = float(policy_seed["zoom"])

    # Explicit top-level or werr_params overrides
    eff_cx = wp.cx if wp.cx is not None else cx
    eff_cy = wp.cy if wp.cy is not None else cy
    eff_zoom = wp.zoom if wp.zoom is not None else zoom
    if eff_cx is not None:
        cfg["cx"] = float(eff_cx)
        selection_mode = "user_custom"
    if eff_cy is not None:
        cfg["cy"] = float(eff_cy)
        selection_mode = "user_custom"
    if eff_zoom is not None:
        cfg["zoom"] = float(eff_zoom)
        selection_mode = "user_custom"

    # Legacy compatibility: if caller explicitly passed cx/cy/zoom without domain or werr_params or gate_id,
    # preserve pure_fractal unless they specified enable_domain/mode.
    if (cx is not None and cy is not None and zoom is not None
            and not domain and not gate_id and not policy and werr_params is None and not werr_preset):
        cfg["enable_domain"] = False
        cfg["enable_lexical"] = False
        cfg["enable_resonance"] = False
        cfg["mode"] = "pure_fractal"
        cfg["domain_mode"] = "none"

    for k in ("mode", "domain_mode", "enable_domain", "enable_lexical", "enable_resonance",
              "tripod", "cadence_lambda", "cadence_beta", "cadence_alpha", "temp_choice",
              "resolution", "max_iter", "preferred_domain"):
        val = getattr(wp, k, None)
        if val is not None:
            cfg[k] = val
            selection_mode = "user_custom"

    if domain and wp.preferred_domain is None:
        domain_map = {
            "ddos_mitigation": "api_security",
            "robotics_industrial": "iot_safety",
        }
        cfg["preferred_domain"] = domain_map.get(domain, domain if domain in DOMAIN_GATES else cfg.get("preferred_domain"))

    engine = werr.WerrEngine(
        cx=cfg["cx"],
        cy=cfg["cy"],
        zoom=cfg["zoom"],
        resolution=int(cfg["resolution"]),
        max_iter=int(cfg["max_iter"]),
        mode=cfg["mode"],
        domain_mode=cfg["domain_mode"],
        enable_domain=cfg["enable_domain"],
        enable_lexical=cfg["enable_lexical"],
        enable_resonance=cfg["enable_resonance"],
        tripod=bool(cfg["tripod"]),
        cadence_lambda=float(cfg["cadence_lambda"]),
        cadence_beta=float(cfg["cadence_beta"]),
        cadence_alpha=float(cfg["cadence_alpha"]),
        temp_choice=float(cfg["temp_choice"]),
    )
    effective_meta = {
        "selection_mode": selection_mode,
        "preset": base_preset_id,
        "state_cube": [
            1 if getattr(engine, "enable_domain", False) else 0,
            1 if getattr(engine, "enable_lexical", False) else 0,
            1 if getattr(engine, "enable_resonance", False) else 0,
        ],
        "mode": getattr(engine, "mode", cfg["mode"]),
        "domain_mode": getattr(engine, "domain_mode", cfg["domain_mode"]),
        "enable_domain": bool(getattr(engine, "enable_domain", False)),
        "enable_lexical": bool(getattr(engine, "enable_lexical", False)),
        "enable_resonance": bool(getattr(engine, "enable_resonance", False)),
        "tripod": bool(getattr(engine, "tripod", True)),
        "cadence_lambda": float(getattr(engine, "cadence_lambda", 0.10)),
        "cadence_beta": float(getattr(engine, "cadence_beta", 0.15)),
        "cadence_alpha": float(getattr(engine, "cadence_alpha", 0.50)),
        "temp_choice": float(getattr(engine, "temp_choice", 1.25)),
        "resolution": int(getattr(engine, "resolution", 36)),
        "max_iter": int(getattr(engine, "max_iter", 36)),
        "seed_24b": {"cx": float(cfg["cx"]), "cy": float(cfg["cy"]), "zoom": float(cfg["zoom"])},
        "preferred_domain": cfg.get("preferred_domain"),
        "auto_route": wp.auto_route,
    }
    return engine, effective_meta


def build_engine(cx=None, cy=None, zoom=None, domain=None):
    eng, _ = resolve_werr_engine(cx=cx, cy=cy, zoom=zoom, domain=domain)
    return eng


TELEMETRY_INGEST_URL = os.environ.get("ANSWERR_TELEMETRY_INGEST_URL", "http://127.0.0.1:8550/telemetry")
PUBLIC_TELEMETRY_ENABLED = os.environ.get("ANSWERR_PUBLIC_TELEMETRY", "1").strip().lower() in ("1", "true", "yes", "on")


def _dispatch_public_telemetry(
    state: Dict[str, Any],
    werr_questions: Dict[str, Any],
    result: Any,
    werr_meta: Dict[str, Any],
    source: str = "answerr_web",
    gate_id: Optional[str] = None,
    kernel_verdict: Optional[str] = None,
) -> None:
    """Non-blocking privacy-filtered telemetry dispatch to local werr-telemetry daemon (port 8550).
    Never called for authenticated customer API-key traffic unless explicitly opted in."""
    if not PUBLIC_TELEMETRY_ENABLED or "PYTEST_CURRENT_TEST" in os.environ:
        return
    try:
        from werr.telemetry import _sanitize_client_state, _sanitize_instruction
        from datetime import datetime, timezone

        q_list = []
        for q_name, q_obj in list(werr_questions.items())[:10]:
            ans = result.answers.get(q_name)
            q_type = getattr(q_obj, "__class__", type(q_obj)).__name__.lower().replace("question", "")
            if q_type not in ("noul", "choice", "score"):
                q_type = "noul"
            item: Dict[str, Any] = {
                "name": str(q_name)[:64],
                "type": q_type,
                "instruction": _sanitize_instruction(getattr(q_obj, "instructions", "")),
            }
            if ans is not None:
                if q_type == "noul":
                    item["decision"] = bool(getattr(ans, "decision", False))
                    item["probability"] = round(float(getattr(ans, "noul", 0.0)), 4)
                    item["confidence"] = round(float(getattr(ans, "confidence", 0.0)), 4)
                elif q_type == "choice":
                    item["decision"] = str(getattr(ans, "choice", ""))[:64]
                    item["probabilities"] = {str(k): round(float(v), 4) for k, v in getattr(ans, "probabilities", {}).items()}
                    item["confidence"] = round(float(getattr(ans, "confidence", 0.0)), 4)
                elif q_type == "score":
                    item["decision"] = round(float(getattr(ans, "score", 0.0)), 3)
                    item["probabilities"] = {str(k): round(float(v), 4) for k, v in getattr(ans, "probabilities", {}).items()}
                    item["confidence"] = round(float(getattr(ans, "confidence", 0.0)), 4)
            q_list.append(item)

        coords = getattr(result, "active_coordinates", None) or werr_meta.get("seed_24b") or {}
        state_summary = _sanitize_client_state(state if isinstance(state, dict) else {})
        state_summary["_werr_preset"] = str(werr_meta.get("preset", "smart_router"))[:32]
        state_summary["_werr_cube"] = "".join(str(x) for x in (werr_meta.get("state_cube") or [1, 1, 1]))
        if gate_id:
            state_summary["_gate_id"] = str(gate_id)[:32]
        if kernel_verdict:
            state_summary["_kernel_verdict"] = str(kernel_verdict)[:16]
        payload = json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "werr-{}-{}".format(getattr(werr, "__version__", "0.5.2"), werr_meta.get("preset", "auto"))[:48],
            "source": source[:32],
            "seed": {
                "cx": round(float(coords.get("cx", -0.10109636)), 8),
                "cy": round(float(coords.get("cy", 0.95628651)), 8),
                "zoom": round(float(coords.get("zoom", 45.0)), 4),
            },
            "state_summary": state_summary,
            "questions": q_list,
            "latency_ms": round(float(getattr(result, "latency_ms", 0.0)), 3),
        }, ensure_ascii=False).encode("utf-8")

        def _send():
            try:
                req = urllib.request.Request(
                    TELEMETRY_INGEST_URL,
                    data=payload,
                    headers={"Content-Type": "application/json", "User-Agent": "answerr-api/" + API_VERSION},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=1.5):
                    pass
            except Exception:
                pass

        threading.Thread(target=_send, daemon=True).start()
    except Exception:
        pass


def parse_prompt_to_state(prompt: str) -> Dict[str, Any]:
    p = PK.normalize_text(prompt)
    state: Dict[str, Any] = {}
    if any(k in p for k in ["admin", "root", "yonetici", "yetkili"]):
        state["user_role"] = "admin"
    elif any(k in p for k in ["attacker", "bot", "hacker", "saldirgan", "malicious", "ddos"]):
        state["user_role"] = "attacker"
    elif any(k in p for k in ["guest", "misafir", "anonymous", "anonim", "unverified"]):
        state["user_role"] = "guest"
    else:
        state["user_role"] = "member"
    state["failed_attempts"] = 5 if any(k in p for k in ["error", "hata", "fail"]) else 0
    state["req_frequency"] = 45.0 if any(k in p for k in ["fast", "burst", "hizli"]) else 2.0
    return state


def _trace(kernel: Dict[str, Any], policy: Optional[Dict[str, Any]], fractal: Dict[str, Any]) -> Dict[str, Any]:
    seal = (policy or {}).get("policy_seal") or (PK.policy_seal(policy) if policy else None)
    rule_hit = None
    if not kernel["rule_id"].startswith(("risk_", "tool_class:", "ood_", "missing_", "empty_", "no_signal", "type_mismatch", "unknown_op")):
        rule_hit = {"rule_id": kernel["rule_id"], "effect": kernel["verdict"], "reason": kernel["reason"]}
    return {
        "kernel_version": kernel["kernel_version"],
        "policy_id": kernel["policy_id"],
        "policy_version": kernel["policy_version"],
        "policy_seal": seal,
        "verdict": kernel["verdict"],
        "rule_id": kernel["rule_id"],
        "reason": kernel["reason"],
        "risk_score": kernel["risk_score"],
        "candidates": kernel["candidates"],
        "matched_rules": ["{}->{}".format(c["rule_id"], c["effect"]) for c in kernel["candidates"]],
        "tool": kernel["tool"],
        "feature_contributions": kernel["feature_contributions"],
        "recognized_fields": kernel["recognized_fields"],
        "unrecognized_fields": kernel["unrecognized_fields"],
        "missing_required_fields": kernel["missing_required_fields"],
        "hard_rule_hit": rule_hit,
        "ood_detected": kernel["ood_detected"],
        "strict": kernel["strict"],
        "recommended_mode": "ABSTAIN_REVIEW" if kernel["verdict"] == "REVIEW" else "DETERMINISTIC_EXECUTE",
        "fractal_manifold": fractal,
    }


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------
@app.get("/", tags=["Info"])
def get_root():
    return {
        "service": "answerr Decision API",
        "provider": "ITouch Bilişim Sistemleri Ltd. Şti. (https://itouch.com.tr)",
        "description": "Policies written in Turkish or English are compiled to explicit rules; every decision "
                       "returns its verdict, the rule behind it and a trace. No model runs at decision time.",
        "docs_url": "/v1/docs",
        "endpoints": {
            "decide": "POST /v1/decide",
            "gates": "GET|POST /v1/gates, DELETE /v1/gates/{gate_id}",
            "gate_decide": "POST /v1/gates/{gate_id}/decide",
            "compile_policy": "POST /v1/policies/compile",
            "werr_parameters": "GET /v1/werr/parameters",
            "access_request": "POST /v1/access-request",
            "systemone": "POST /v1/systemone (research)",
            "chat_completions": "POST /v1/chat/completions (research)",
            "health": "GET /v1/health",
        },
        "kernel_version": PK.KERNEL_VERSION,
        "version": API_VERSION,
        "uptime_seconds": round(time.time() - START_TIME, 1),
    }


@app.get("/v1/health", tags=["Health"])
@app.get("/health", tags=["Health"])
def get_health():
    t0 = time.perf_counter()
    PK.evaluate({"tool_name": "read_status", "user_role": "member"}, BUILTIN_GATES["agent_mcp_guard"])
    kernel_ms = (time.perf_counter() - t0) * 1000.0
    return {
        "status": "healthy",
        "api_version": API_VERSION,
        "kernel_version": PK.KERNEL_VERSION,
        "werr_version": getattr(werr, "__version__", "unknown"),
        "builtin_gates": len(BUILTIN_GATES),
        "tenant_gates": GATE_STORE.count(),
        "gate_store": "ok" if GATE_STORE.available else "unavailable",
        "recaptcha": "on" if RECAPTCHA_SECRET else "off",
        "kernel_latency_ms": round(kernel_ms, 3),
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "timestamp": time.time(),
    }


@app.get("/v1/presets", tags=["Catalog"])
def get_presets():
    return {"status": "success", "presets": PRESETS, "werr_presets": WERR_PRESETS, "gate_profiles": GATE_WERR_PROFILES}


@app.get("/v1/werr/parameters", tags=["Catalog"])
def get_werr_parameters():
    """Returns the complete werr v0.5.2 parameter catalog, 8-state orthogonal cube, and purpose-aligned profiles."""
    return {
        "status": "success",
        "werr_version": getattr(werr, "__version__", "0.5.2"),
        "default_selection": "auto",
        "gate_profiles": GATE_WERR_PROFILES,
        "presets": WERR_PRESETS,
        "orthogonal_cube_states": [
            {"state": [1, 1, 1], "mode": "hybrid", "label_tr": "Tam Hibrit (Crown Core)", "label_en": "Full Hybrid (Crown Core)",
             "description": "Domain Gate + Exact Lexical + 4-Stem & Mandelbrot Pole Resonance"},
            {"state": [1, 1, 0], "mode": "lexical", "label_tr": "Alan + Sözlüksel Mühür", "label_en": "Domain + Lexical Only",
             "description": "Domain Gate + Exact Lexical matching without morphological/pole resonance"},
            {"state": [1, 0, 1], "mode": "resonance", "label_tr": "Alan + Kutup Rezonansı", "label_en": "Domain + Pole Resonance",
             "description": "Domain Gate + Morphological 4-stem & Mandelbrot coordinate resonance"},
            {"state": [0, 0, 0], "mode": "pure_fractal", "label_tr": "Saf Fraktal (Evrensel Cusp)", "label_en": "Pure Fractal (Universal Cusp)",
             "description": "Zero ontology dictionaries; pure 16D state projection onto 24B Mandelbrot boundary (∂M)"},
        ],
        "hyperparameters": {
            "tripod": {"type": "bool", "default": True, "description": "3-point triangular probe for dynamic fused escape velocity"},
            "cadence_lambda": {"type": "float", "default": 0.10, "min": 0.0, "max": 2.0, "description": "Trajectory cadence coupling (λ)"},
            "cadence_beta": {"type": "float", "default": 0.15, "min": 0.0, "max": 2.0, "description": "Boundary damping factor (β)"},
            "cadence_alpha": {"type": "float", "default": 0.50, "min": 0.0, "max": 1.0, "description": "Resonance blending weight (α)"},
            "temp_choice": {"type": "float", "default": 1.25, "min": 0.05, "max": 10.0, "description": "4-quadrant choice softmax temperature (τ)"},
            "resolution": {"type": "int", "default": 36, "min": 8, "max": 128, "description": "Manifold sampling resolution (N)"},
            "max_iter": {"type": "int", "default": 36, "min": 8, "max": 256, "description": "Mandelbrot escape iteration ceiling (K)"},
        },
    }


@app.get("/v1/domains", tags=["Catalog"])
def get_domains():
    return {"status": "success",
            "available_domains": list(DOMAIN_GATES.keys()) + ["ddos_mitigation", "robotics_industrial"],
            "builtin_gates": list(BUILTIN_GATES.keys()),
            "werr_presets": list(WERR_PRESETS.keys())}


@app.get("/v1/gates", tags=["Policy Gates"])
def list_gates(request: Request):
    tenant = _security(request)["tenant"]
    own = GATE_STORE.owned_by(tenant) if tenant else []
    return {"status": "success", "builtin": list(BUILTIN_GATES.values()), "gates": list(BUILTIN_GATES.values()) + own,
            "count": len(BUILTIN_GATES) + len(own), "tenant": tenant}


@app.post("/v1/gates", tags=["Policy Gates"])
def register_gate(req: PolicyGateCreateRequest, request: Request):
    sec = _security(request)
    tenant = sec["tenant"]
    if not tenant:
        raise HTTPException(401, "An API key is required to register gates.")
    principal = sec.get("principal")
    if principal:
        if principal["role"] not in ("owner", "admin"):
            raise CS.CommerceError(403, "forbidden", "Reviewers cannot register gates.")
        limit = CS.plan_of(CS.get_account(principal["account_id"]))["custom_gates"]
        own = [g for g in GATE_STORE.owned_by(tenant) if g["gate_id"] != req.gate_id]
        if len(own) >= limit:
            raise CS.CommerceError(403, "gate_limit", "Your plan allows {} custom gate(s).".format(limit), limit=limit)
    if not GATE_ID_RE.match(req.gate_id):
        raise HTTPException(400, "gate_id must match ^[a-z0-9][a-z0-9_-]{2,63}$")
    if req.gate_id in BUILTIN_GATES:
        raise HTTPException(409, "Built-in gate ids cannot be overwritten.")
    gate = validate_policy(req.model_dump())
    gate.update({"gate_id": req.gate_id, "version": req.version, "title": req.title, "category": req.category,
                 "tenant": tenant, "owner": tenant, "registered_at": int(time.time())})
    checks = policy_checks.run_all(gate)
    gate["checks"] = checks
    gate["policy_seal"] = PK.policy_seal({k: v for k, v in gate.items() if k not in ("registered_at", "checks")})
    GATE_STORE.put(gate, tenant)
    return {"status": "registered", "gate_id": req.gate_id, "policy_seal": gate["policy_seal"],
            "decide_endpoint": "/v1/gates/{}/decide".format(req.gate_id), "checks": checks, "gate": gate}


@app.delete("/v1/gates/{gate_id}", tags=["Policy Gates"])
def delete_gate(gate_id: str, request: Request):
    tenant = _security(request)["tenant"]
    if not tenant:
        raise HTTPException(401, "An API key is required.")
    if gate_id in BUILTIN_GATES:
        raise HTTPException(409, "Built-in gates cannot be deleted.")
    if not GATE_STORE.delete(gate_id, tenant):
        raise HTTPException(404, "Gate not found.")
    return {"status": "deleted", "gate_id": gate_id}


@app.post("/v1/policies/compile", tags=["Policy Gates"])
def compile_policy(req: PolicyCompileRequest, request: Request):
    """Natural language -> draft policy. Returns the rules with the sentence each came from,
    open questions, generated tests and executed checks. Nothing is registered."""
    gate_id = (req.gate_id or "draft_policy").strip().lower()
    if not GATE_ID_RE.match(gate_id):
        gate_id = "draft_policy"
    if req.sample_state is not None and len(json.dumps(req.sample_state)) > 8000:
        raise HTTPException(400, "sample_state too large")
    out = policy_compiler.compile_policy(req.prompt, gate_id=gate_id, schema=req.schema_fields,
                                         sample_state=req.sample_state)
    out["security"] = _security(request)
    out["compiled_policy"] = out["policy_spec"]  # older clients
    return out


@app.post("/v1/gates/{gate_id}/decide", tags=["Policy Gates"])
def decide_with_gate(gate_id: str, req: DecisionRequest, request: Request):
    req.gate_id = gate_id
    req.strict_policy = True
    return post_decide(req, request)


@app.post("/v1/decide", tags=["Decision Engine"])
def post_decide(req: DecisionRequest, request: Request):
    t0 = time.perf_counter()
    sec = _security(request)
    principal = sec.get("principal")
    mode = (req.mode or "live").strip().lower()
    if mode not in ("live", "shadow"):
        raise HTTPException(400, "mode must be 'live' or 'shadow'.")
    if principal:
        CS.quota_check(principal["account_id"])          # 429 quota_exceeded / 403 suspended
        if mode == "shadow":
            CROUTER.feature(principal["account_id"], "shadow")
    if req.observed_outcome is not None:
        CS.normalize_outcome(req.observed_outcome)        # 400 on an unknown label
    state = dict(req.state) if req.state else {}
    if req.prompt and not state:
        state = parse_prompt_to_state(req.prompt)

    if req.policy is not None:
        policy = validate_policy(req.policy)
        policy["policy_seal"] = PK.policy_seal(policy)
    else:
        policy = resolve_gate(req.gate_id, sec["tenant"])

    # questions for the research engine (choice / score / legacy noul)
    werr_questions: Dict[str, Any] = {}
    noul_texts: Dict[str, str] = {}
    if req.questions:
        for q_id, q in req.questions.items():
            qt = q.type.lower().strip()
            if qt == "noul":
                werr_questions[q_id] = werr.NoulQuestion(instructions=q.resolved_text, threshold=q.threshold or 0.5)
                noul_texts[q_id] = q.resolved_text
            elif qt == "choice":
                crit = q.criteria or {"option_a": "Option A", "option_b": "Option B"}
                if isinstance(crit, list):
                    crit = {"opt_{}".format(i): v for i, v in enumerate(crit)}
                werr_questions[q_id] = werr.ChoiceQuestion(instructions=q.resolved_text, criteria=crit)
            elif qt == "score":
                crit = q.criteria or ["Low", "Moderate", "High", "Extreme"]
                if isinstance(crit, dict):
                    crit = list(crit.values())
                werr_questions[q_id] = werr.ScoreQuestion(instructions=q.resolved_text, criteria=crit)
            else:
                raise HTTPException(400, "Unsupported question type '{}'.".format(q.type))
    elif req.question:
        werr_questions["primary_decision"] = werr.NoulQuestion(instructions=req.question)
        noul_texts["primary_decision"] = req.question
    elif req.domain and req.domain in PRESETS:
        pre = PRESETS[req.domain]
        if not state:
            state = dict(pre["default_state"])
        for q_id, q in pre["default_questions"].items():
            if q["type"] == "noul":
                werr_questions[q_id] = werr.NoulQuestion(instructions=q["text"])
                noul_texts[q_id] = q["text"]
            elif q["type"] == "choice":
                crit = q["criteria"]
                if isinstance(crit, list):
                    crit = {"opt_{}".format(i): v for i, v in enumerate(crit)}
                werr_questions[q_id] = werr.ChoiceQuestion(instructions=q["text"], criteria=crit)
            elif q["type"] == "score":
                crit = q["criteria"]
                if isinstance(crit, dict):
                    crit = list(crit.values())
                werr_questions[q_id] = werr.ScoreQuestion(instructions=q["text"], criteria=crit)
    else:
        werr_questions["decision"] = werr.NoulQuestion(instructions="Is the proposed operation safe and valid?")
        noul_texts["decision"] = "Is the proposed operation safe and valid?"

    kernel = PK.evaluate(state, policy, bool(req.strict_policy), autonomous=req.autonomous, autonomous_bias=req.autonomous_bias or "balanced")
    governs = bool(policy or req.strict_policy or kernel["tool"] or kernel["verdict"] == "DENY")

    engine, werr_meta = resolve_werr_engine(
        cx=req.cx, cy=req.cy, zoom=req.zoom, domain=req.domain,
        gate_id=req.gate_id, policy=policy, werr_preset=req.werr_preset, werr_params=req.werr_params
    )
    result = engine.decide(
        state=state,
        questions=werr_questions,
        auto_route=werr_meta.get("auto_route"),
        preferred_domain=werr_meta.get("preferred_domain"),
    )

    werr_reflex_out: Dict[str, Any] = {}
    for q_id, ans in result.answers.items():
        if isinstance(ans, werr.NoulAnswer):
            werr_reflex_out[q_id] = {
                "type": "noul", "decision": ans.decision, "noul": round(ans.noul, 4),
                "confidence": round(ans.confidence, 4), "label": "ALLOWED" if ans.decision else "DENIED",
            }
        elif isinstance(ans, werr.ChoiceAnswer):
            werr_reflex_out[q_id] = {
                "type": "choice", "choice": ans.choice,
                "probabilities": {k: round(v, 4) for k, v in ans.probabilities.items()},
                "confidence": round(ans.confidence, 4),
            }
        elif isinstance(ans, werr.ScoreAnswer):
            werr_reflex_out[q_id] = {
                "type": "score", "score": round(ans.score, 3), "level": ans.level,
                "probabilities": {str(k): round(v, 4) for k, v in ans.probabilities.items()},
                "confidence": round(ans.confidence, 4),
            }

    fractal = {
        "active_coordinates": getattr(result, "active_coordinates", None) or werr_meta.get("seed_24b"),
        "escape_entropy": getattr(result, "escape_entropy", None),
        "quadrant_entropy": getattr(result, "quadrant_entropy", None),
        "routed_domain": getattr(result, "domain", None) or werr_meta.get("preferred_domain"),
        "werr_config": werr_meta,
        "werr_reflex": werr_reflex_out,
        "note": "Research telemetry; does not decide gated, strict or agent-tool requests.",
    }

    answers: Dict[str, Any] = {}
    primary: Optional[Dict[str, Any]] = None
    for q_id, ans in result.answers.items():
        if isinstance(ans, werr.NoulAnswer):
            if governs:
                answers[q_id] = PK.answer_question(kernel, noul_texts.get(q_id))
            else:
                answers[q_id] = {"type": "noul", "decision": ans.decision, "boolean": ans.decision,
                                 "noul": round(ans.noul, 4), "confidence": round(ans.confidence, 4),
                                 "label": "ALLOWED" if ans.decision else "DENIED", "source": "werr_research_engine",
                                 "kernel_verdict": kernel["verdict"]}
            primary = primary or answers[q_id]
        elif isinstance(ans, werr.ChoiceAnswer):
            answers[q_id] = {"type": "choice", "choice": ans.choice,
                             "probabilities": {k: round(v, 4) for k, v in ans.probabilities.items()},
                             "confidence": round(ans.confidence, 4)}
        elif isinstance(ans, werr.ScoreAnswer):
            answers[q_id] = {"type": "score", "score": round(ans.score, 3), "level": ans.level,
                             "probabilities": {str(k): round(v, 4) for k, v in ans.probabilities.items()},
                             "confidence": round(ans.confidence, 4)}

    trace = _trace(kernel, policy, fractal)
    total_ms = (time.perf_counter() - t0) * 1000.0
    label = primary["label"] if primary else kernel["label"]
    body = {
        "status": "abstain_review" if label == "ABSTAIN_REVIEW" else "success",
        "verdict": kernel["verdict"] if governs or not primary else ("ALLOW" if primary["decision"] else "DENY"),
        "decision": primary["decision"] if primary else (None if kernel["verdict"] == "REVIEW" else kernel["verdict"] == "ALLOW"),
        "label": label,
        "governed_by": "policy_kernel" if governs else "werr_research_engine",
        "latency_ms": round(total_ms, 3),
        "input_state": state,
        "answers": answers,
        "results": answers,
        "trace": trace,
        "werr_config": werr_meta,
        "security": {"rate_tier": sec["rate_tier"], "recaptcha": sec["recaptcha"],
                     "api_key": bool(sec["tenant"])},
        "autonomous_resolution": kernel.get("autonomous_resolution", False),
        "confidence_index": kernel.get("confidence_index", kernel.get("confidence", 1.0)),
        "confidence_band": kernel.get("confidence_band", "HIGH_CONFIDENCE"),
        "retry_recommended": kernel.get("retry_recommended", False),
        "original_verdict": kernel.get("original_verdict"),
        "telemetry": {
            "engine_latency_ms": round(getattr(result, "latency_ms", 0.0), 3),
            "total_request_latency_ms": round(total_ms, 3),
            "model_weights_bytes": 0,
            "policy_seal": trace["policy_seal"],
            "kernel_version": PK.KERNEL_VERSION,
            "werr_preset": werr_meta.get("preset"),
            "werr_state_cube": werr_meta.get("state_cube"),
        },
    }
    headers = {"X-Answerr-Verdict": body["verdict"] or "", "X-Answerr-Policy-Seal": trace["policy_seal"] or ""}
    if principal:
        _meter(principal, req, body, kernel, policy, trace, state, mode, total_ms, headers)
    opt_in = req.werr_params.telemetry_opt_in if req.werr_params else None
    if (not sec["tenant"] and opt_in is not False) or (sec["tenant"] and opt_in is True):
        _dispatch_public_telemetry(
            state, werr_questions, result, werr_meta,
            source="answerr_decide",
            gate_id=(policy or {}).get("gate_id") or req.gate_id,
            kernel_verdict=body["verdict"],
        )
    return JSONResponse(content=body, headers=headers)


def _meter(principal, req, body, kernel, policy, trace, state, mode, total_ms, headers):
    """Usage, decision log, review queue, webhooks and quota warnings for customer accounts."""
    rec = CS.record_decision(
        principal["account_id"], key_prefix=principal.get("prefix"),
        gate_id=(policy or {}).get("gate_id") or req.gate_id, verdict=body["verdict"] or kernel["verdict"],
        rule_id=kernel.get("rule_id"), reason=kernel.get("reason"), latency_ms=total_ms, mode=mode,
        observed=req.observed_outcome, policy_seal=trace.get("policy_seal"), state=state,
        external_id=req.external_id, enqueue_review=bool(req.enqueue_review if req.enqueue_review is not None else True))
    body["decision_id"] = rec["decision_id"]
    body["mode"] = mode
    body["usage"] = rec["usage"]
    headers["X-Answerr-Decision-Id"] = rec["decision_id"]
    if rec["usage"]["quota"] is not None:
        headers["X-Answerr-Quota-Remaining"] = str(max(0, rec["usage"]["quota"] - rec["usage"]["decisions"]))
    acc = None
    if rec["review_id"]:
        body["review"] = {"id": rec["review_id"], "status": "pending", "poll": "/v1/reviews/" + rec["review_id"]}
        acc = CS.get_account(principal["account_id"])
        CHOOKS.send(acc, "review.created", {"id": rec["review_id"], "decision_id": rec["decision_id"],
                                            "gate_id": (policy or {}).get("gate_id") or req.gate_id,
                                            "rule_id": kernel.get("rule_id"), "reason": kernel.get("reason"),
                                            "external_id": req.external_id, "console": CMAIL.console_url() + "#reviews"})
    if rec["warn"]:
        acc = acc or CS.get_account(principal["account_id"])
        CMAIL.quota_warning(acc, rec["warn"], rec["usage"]["decisions"], rec["usage"]["quota"])
        CHOOKS.send(acc, "quota.warning", {"percent": rec["warn"], **rec["usage"]})


class AccessRequest(BaseModel):
    email: str = Field(..., max_length=254)
    company: Optional[str] = Field(None, max_length=120)
    note: Optional[str] = Field(None, max_length=1000)
    lang: Optional[str] = "tr"
    source: Optional[str] = Field(None, max_length=80)
    website: Optional[str] = Field(None, max_length=200, description="honeypot, leave empty")


ACCESS_LIMITER = SlidingWindowLimiter(window_seconds=3600, name="access")


@app.post("/v1/access-request", tags=["Early access"])
def access_request(req: AccessRequest, request: Request):
    """Design-partner / early-access form. Delivered to ask@answerr.me with a confirmation to the sender."""
    sec = _security(request)
    ip = client_ip(request)
    ok, _, _, retry = ACCESS_LIMITER.check("ip:" + ip, "access_form")
    if not ok:
        raise HTTPException(429, "Too many requests from this address; try again later.")
    if not access_mailer.valid_email((req.email or "").strip().lower()):
        raise HTTPException(400, "Please enter a valid e-mail address.")
    if RECAPTCHA_SECRET and sec["recaptcha"] != "verified" and not sec["tenant"]:
        raise HTTPException(403, "reCAPTCHA verification failed.")
    out = access_mailer.handle(req.model_dump(), ip)
    if not out["ok"]:
        raise HTTPException(400, "Please enter a valid e-mail address.")
    return {"status": "received", "mailed": out.get("mailed", False)}


class SystemOneRequest(BaseModel):
    """JevBench-compatible TypeSafe wire format for POST /v1/systemone."""
    task: Optional[str] = None
    state: Optional[Dict[str, Any]] = Field(default_factory=dict)
    questions: Optional[Dict[str, Any]] = Field(default_factory=dict)
    model: Optional[str] = "werr-system-one"
    domain: Optional[str] = None
    werr_preset: Optional[str] = None
    werr_params: Optional[WerrParamsSpec] = None


@app.post("/v1/systemone", tags=["Decision Engine"])
def post_systemone(req: SystemOneRequest):
    """
    JevBench TypeSafe wire format endpoint.
    Accepts questions with 'type' + 'labels' (JevBench format) or 'type' + 'text' + 'criteria' (answerr format).
    """
    t_start = time.perf_counter()
    state = dict(req.state) if req.state else {}

    werr_questions = {}
    if req.questions:
        for q_id, q_def in req.questions.items():
            if isinstance(q_def, dict):
                q_type = str(q_def.get("type", "noul")).lower().strip()
                text = str(q_def.get("text") or q_def.get("instructions") or q_id)
                labels = q_def.get("labels") or q_def.get("criteria") or q_def.get("options")
                if q_type == "noul":
                    werr_questions[q_id] = werr.NoulQuestion(instructions=text)
                elif q_type == "choice":
                    if isinstance(labels, list):
                        crit = {lbl: lbl for lbl in labels}
                    elif isinstance(labels, dict):
                        crit = labels
                    else:
                        crit = {"option_a": "Option A", "option_b": "Option B"}
                    werr_questions[q_id] = werr.ChoiceQuestion(instructions=text, criteria=crit)
                elif q_type == "score":
                    if isinstance(labels, list):
                        crit = labels
                    elif isinstance(labels, dict):
                        crit = list(labels.values())
                    else:
                        crit = ["Low", "Moderate", "High", "Extreme"]
                    werr_questions[q_id] = werr.ScoreQuestion(instructions=text, criteria=crit)
                else:
                    werr_questions[q_id] = werr.NoulQuestion(instructions=text)

    if not werr_questions:
        werr_questions["decision"] = werr.NoulQuestion(instructions="Is the proposed operation safe and valid?")

    eval_state = dict(state)
    if req.task and "_task_id" not in eval_state:
        eval_state["_task_id"] = req.task
    if req.werr_params or req.werr_preset or req.domain:
        eng, werr_meta = resolve_werr_engine(domain=req.domain, werr_preset=req.werr_preset, werr_params=req.werr_params)
        result = eng.decide(state=eval_state, questions=werr_questions,
                            auto_route=werr_meta.get("auto_route"), preferred_domain=werr_meta.get("preferred_domain"))
    else:
        werr_meta = {"selection_mode": "auto_optimal", "preset": "smart_router", "state_cube": [1, 1, 1],
                     "seed_24b": {"cx": SYSTEMONE_ROUTER.cx, "cy": SYSTEMONE_ROUTER.cy, "zoom": SYSTEMONE_ROUTER.zoom}}
        result = SYSTEMONE_ROUTER.decide(state=eval_state, questions=werr_questions)
    total_ms = (time.perf_counter() - t_start) * 1000.0

    answers_out = {}
    for q_id, ans in result.answers.items():
        if isinstance(ans, (werr.NoulAnswer, wevv.NoulAnswer)):
            answers_out[q_id] = {
                "type": "noul",
                "decision": ans.decision,
                "boolean": ans.decision,
                "noul": round(ans.noul, 4),
                "confidence": round(ans.confidence, 4),
                "label": "ALLOWED" if ans.decision else "DENIED"
            }
        elif isinstance(ans, (werr.ChoiceAnswer, wevv.ChoiceAnswer)):
            answers_out[q_id] = {
                "type": "choice",
                "selected_label": ans.choice,
                "choice": ans.choice,
                "probabilities": {k: round(v, 4) for k, v in ans.probabilities.items()},
                "confidence": round(ans.confidence, 4)
            }
        elif isinstance(ans, (werr.ScoreAnswer, wevv.ScoreAnswer)):
            answers_out[q_id] = {
                "type": "score",
                "score": round(ans.score, 3),
                "level": ans.level,
                "probabilities": {str(k): round(v, 4) for k, v in ans.probabilities.items()},
                "confidence": round(ans.confidence, 4)
            }

    _dispatch_public_telemetry(state, werr_questions, result, werr_meta, source="answerr_systemone")
    return {
        "status": "success",
        "task_id": req.task or "werr-systemone",
        "wire_protocol": "POST /v1/systemone (JevBench TypeSafe Compatible)",
        "system_level": "System-1 (Fractal Boundary Wave Dynamics)",
        "vram_allocated_bytes": 0,
        "seed_footprint_bytes": 24,
        "model": req.model,
        "state": state,
        "result": answers_out,
        "werr_config": werr_meta,
        "telemetry": {
            "engine_latency_ms": round(result.latency_ms, 3),
            "total_request_latency_ms": round(total_ms, 3),
            "vram_bytes": 0,
            "memory_seed_bytes": 24,
            "engine": f"werr-reflex-{getattr(werr, '__version__', '0.5.1')}"
        }
    }


@app.post("/v1/chat/completions", tags=["OpenAI Adapter"])
def chat_completions(req: ChatCompletionRequest):
    """
    OpenAI-compatible chat completion endpoint.
    Allows standard LLM libraries (LangChain, LlamaIndex, OpenAI SDK) to query Answerr directly.
    """
    t_start = time.perf_counter()

    user_content = ""
    for msg in reversed(req.messages):
        if msg.role == "user":
            user_content = msg.content
            break

    if not user_content:
        user_content = "Evaluate system state"

    state = dict(req.state) if req.state else parse_prompt_to_state(user_content)
    eng, werr_meta = resolve_werr_engine(domain=req.domain, werr_preset=req.werr_preset, werr_params=req.werr_params)

    werr_questions = {
        "permission": werr.NoulQuestion(instructions=f"Should request proceed: {user_content[:160]}?"),
        "action": werr.ChoiceQuestion(instructions="Pipeline action", criteria={
            "direct_api": "Fast Path API",
            "rate_limit": "Queue Throttling",
            "quarantine": "Audit Quarantine",
            "block": "Block Access"
        }),
        "threat": werr.ScoreQuestion(instructions="Threat Score", criteria=["Nominal", "Minor", "Substantial", "Critical"])
    }
    result = eng.decide(
        state=state,
        questions=werr_questions,
        auto_route=werr_meta.get("auto_route"),
        preferred_domain=werr_meta.get("preferred_domain"),
    )

    total_ms = (time.perf_counter() - t_start) * 1000.0
    ans_noul = result.answers["permission"]
    ans_choice = result.answers["action"]
    ans_score = result.answers["threat"]

    decision_label = "APPROVED (İzin Verildi)" if ans_noul.decision else "DENIED (Engellendi)"
    werr_ver = getattr(werr, "__version__", "0.5.2")

    content_text = (
        f"answerr research reflex ({total_ms:.2f} ms)\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• Status: {decision_label}\n"
        f"• Action: {ans_choice.choice}\n"
        f"• Threat: {ans_score.level} (Score: {ans_score.score:.2f})\n"
        f"• Confidence: %{ans_noul.confidence * 100:.1f} (p={ans_noul.noul:.3f})\n"
        f"• Note: research engine output, not a policy decision\n"
        f"• Engine: werr {werr_ver} (Wave & Error Reflex Resonator)"
    )

    coords = getattr(result, "active_coordinates", None) or werr_meta.get("seed_24b") or {}
    return {
        "id": f"chatcmpl-answerr-{int(time.time()*1000)}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": req.model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content_text
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        },
        "werr_decision": {
            "decision": bool(ans_noul.decision),
            "noul": round(float(ans_noul.noul), 4),
            "confidence": round(float(ans_noul.confidence), 4),
            "action": ans_choice.choice,
            "action_probabilities": {k: round(float(v), 4) for k, v in ans_choice.probabilities.items()},
            "threat_score": round(float(ans_score.score), 3),
            "threat_level": ans_score.level,
            "active_coordinates": coords,
            "werr_config": werr_meta,
        },
        "telemetry": {
            "latency_ms": round(total_ms, 3),
            "vram_bytes": 0,
            "zero_memory": True,
            "engine": f"werr-reflex-{werr_ver}"
        },
        "werr_telemetry": {
            "latency_ms": round(total_ms, 3),
            "vram_bytes": 0,
            "zero_memory": True
        },
        "wevv_telemetry": {
            "latency_ms": round(total_ms, 3),
            "vram_bytes": 0,
            "zero_memory": True
        }
    }


# -----------------------------------------------------------------------------
# Commercial layer
# -----------------------------------------------------------------------------
SIGNUP_LIMITER = SlidingWindowLimiter(window_seconds=3600, name="signup")


def _limit_form(request: Request) -> None:
    ok, _, _, retry = SIGNUP_LIMITER.check("ip:" + client_ip(request), "access_form")
    if not ok:
        raise CS.CommerceError(429, "too_many_requests", "Too many requests from this address; try again later.")


def _require_human(request: Request) -> None:
    sec = _security(request)
    if RECAPTCHA_SECRET and sec["recaptcha"] != "verified" and not sec["tenant"]:
        raise CS.CommerceError(403, "recaptcha_failed", "reCAPTCHA verification failed; reload the page and try again.")


def _load_policy(gate_id: Optional[str], inline: Optional[Dict[str, Any]], tenant: str) -> Optional[Dict[str, Any]]:
    if inline is not None:
        pol = validate_policy(inline)
        pol["policy_seal"] = PK.policy_seal(pol)
        return pol
    if not gate_id:
        raise CS.CommerceError(400, "policy_required", "Send gate_id or policy.")
    return resolve_gate(gate_id, tenant)


CROUTER.configure(client_ip=client_ip, limit_form=_limit_form, require_human=_require_human,
                  load_policy=_load_policy, evaluate=PK.evaluate, drop_tenant_gates=GATE_STORE.drop_tenant)
app.include_router(CROUTER.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8560, log_level="info")
