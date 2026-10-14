"""
answerr REST API (v1.2.0)
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

API_VERSION = "1.2.0"
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


def authenticate(request: Request) -> Optional[str]:
    """Returns the tenant name for a valid API key, else None."""
    key = request.headers.get("x-api-key") or ""
    auth = request.headers.get("authorization") or ""
    if not key and auth.lower().startswith("bearer "):
        key = auth[7:].strip()
    if not key:
        return None
    for k, tenant in API_KEYS.items():
        if hmac.compare_digest(k.encode(), key.encode()):
            return tenant
    return None


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
        import fcntl

        class _L:
            def __enter__(s):
                d = os.path.dirname(self.path) or "."
                os.makedirs(d, exist_ok=True)
                s.f = open(self.path + ".lock", "a")
                fcntl.flock(s.f, fcntl.LOCK_EX)
                return s

            def __exit__(s, *a):
                fcntl.flock(s.f, fcntl.LOCK_UN)
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
    print("[answerr] API {} ready in {:.1f} ms; {} built-in gates, {} tenant gates, {} API keys, reCAPTCHA {}".format(
        API_VERSION, (time.perf_counter() - t0) * 1000, len(BUILTIN_GATES), GATE_STORE.count(),
        len(API_KEYS), "on" if RECAPTCHA_SECRET else "off"))
    yield


app = FastAPI(
    title="answerr Decision API",
    description="Deterministic decision policies written in natural language, compiled to explicit rules, "
                "executed with a full trace. ITouch Bilişim Sistemleri Ltd. Şti.",
    version=API_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://answerr.me", "https://www.answerr.me", "https://api.answerr.me",
                   "https://pcworm.github.io", "http://localhost:3000", "http://localhost:8000",
                   "http://127.0.0.1:8000", "http://127.0.0.1:5500"],
    allow_origin_regex=r"https://([a-z0-9-]+\.)?answerr\.me",
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With", "X-API-Key", "X-Recaptcha-Token"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "Retry-After", "X-Answerr-Verdict", "X-Answerr-Policy-Seal"],
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
    tenant = authenticate(request)
    recaptcha = "absent"
    if tenant:
        tier, ident = "api_key", "tenant:" + tenant
    else:
        token = request.headers.get("x-recaptcha-token")
        if token:
            recaptcha = await run_in_threadpool(verify_recaptcha, token, ip)
        tier = "verified" if recaptcha == "verified" else "anonymous"
        ident = "ip:" + ip
    request.state.security = {"tenant": tenant, "rate_tier": tier, "recaptcha": recaptcha}

    remaining = None
    limit = SlidingWindowLimiter.TIERS[tier][0]
    if request.url.path not in ("/health", "/v1/health"):
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
    response.headers["Cache-Control"] = "no-store"
    response.headers["Server"] = "answerr"
    return response


def _security(request: Request) -> Dict[str, Any]:
    return getattr(request.state, "security", {"tenant": None, "rate_tier": "anonymous", "recaptcha": "absent"})


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
    cx: Optional[float] = None
    cy: Optional[float] = None
    zoom: Optional[float] = None


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
def build_engine(cx=None, cy=None, zoom=None, domain=None):
    if cx is not None and cy is not None and zoom is not None:
        if domain:
            return werr.WerrEngine(cx=cx, cy=cy, zoom=zoom, enable_domain=True, enable_lexical=True,
                                   enable_resonance=True, mode="hybrid", domain_mode="multi", tripod=True)
        return werr.WerrEngine(cx=cx, cy=cy, zoom=zoom, enable_domain=False, enable_lexical=False,
                               enable_resonance=False, mode="pure_fractal", domain_mode="none", tripod=True)
    return DEFAULT_ROUTER


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
        "docs_url": "/docs",
        "endpoints": {
            "decide": "POST /v1/decide",
            "gates": "GET|POST /v1/gates, DELETE /v1/gates/{gate_id}",
            "gate_decide": "POST /v1/gates/{gate_id}/decide",
            "compile_policy": "POST /v1/policies/compile",
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
    return {"status": "success", "presets": PRESETS}


@app.get("/v1/domains", tags=["Catalog"])
def get_domains():
    return {"status": "success",
            "available_domains": list(DOMAIN_GATES.keys()) + ["ddos_mitigation", "robotics_industrial"],
            "builtin_gates": list(BUILTIN_GATES.keys())}


@app.get("/v1/gates", tags=["Policy Gates"])
def list_gates(request: Request):
    tenant = _security(request)["tenant"]
    own = GATE_STORE.owned_by(tenant) if tenant else []
    return {"status": "success", "builtin": list(BUILTIN_GATES.values()), "gates": list(BUILTIN_GATES.values()) + own,
            "count": len(BUILTIN_GATES) + len(own), "tenant": tenant}


@app.post("/v1/gates", tags=["Policy Gates"])
def register_gate(req: PolicyGateCreateRequest, request: Request):
    tenant = _security(request)["tenant"]
    if not tenant:
        raise HTTPException(401, "An API key is required to register gates.")
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

    kernel = PK.evaluate(state, policy, bool(req.strict_policy))
    governs = bool(policy or req.strict_policy or kernel["tool"] or kernel["verdict"] == "DENY")

    seed = (policy or {}).get("seed_24b") or {}
    eff_cx = req.cx if req.cx is not None else seed.get("cx")
    eff_cy = req.cy if req.cy is not None else seed.get("cy")
    eff_zoom = req.zoom if req.zoom is not None else seed.get("zoom")
    engine = build_engine(eff_cx, eff_cy, eff_zoom, domain=req.domain)
    result = engine.decide(state=state, questions=werr_questions)

    fractal = {
        "active_coordinates": getattr(result, "active_coordinates", None),
        "escape_entropy": getattr(result, "escape_entropy", None),
        "quadrant_entropy": getattr(result, "quadrant_entropy", None),
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
        "security": {"rate_tier": sec["rate_tier"], "recaptcha": sec["recaptcha"],
                     "api_key": bool(sec["tenant"])},
        "telemetry": {
            "engine_latency_ms": round(getattr(result, "latency_ms", 0.0), 3),
            "total_request_latency_ms": round(total_ms, 3),
            "model_weights_bytes": 0,
            "policy_seal": trace["policy_seal"],
            "kernel_version": PK.KERNEL_VERSION,
        },
    }
    return JSONResponse(content=body, headers={"X-Answerr-Verdict": body["verdict"] or "",
                                               "X-Answerr-Policy-Seal": trace["policy_seal"] or ""})


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

    return {
        "status": "success",
        "task_id": req.task or "werr-systemone",
        "wire_protocol": "POST /v1/systemone (JevBench TypeSafe Compatible)",
        "system_level": "System-1 (Mandelbrot Boundary Wave Dynamics)",
        "vram_allocated_bytes": 0,
        "seed_footprint_bytes": 24,
        "model": req.model,
        "state": state,
        "result": answers_out,
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

    state = parse_prompt_to_state(user_content)

    result = DEFAULT_ROUTER.decide(
        state=state,
        questions={
            "permission": werr.NoulQuestion(instructions=f"Should request proceed: {user_content[:80]}?"),
            "action": werr.ChoiceQuestion(instructions="Pipeline action", criteria={
                "direct_api": "Fast Path API",
                "rate_limit": "Queue Throttling",
                "quarantine": "Audit Quarantine",
                "block": "Block Access"
            }),
            "threat": werr.ScoreQuestion(instructions="Threat Score", criteria=["Nominal", "Minor", "Substantial", "Critical"])
        }
    )

    total_ms = (time.perf_counter() - t_start) * 1000.0
    ans_noul = result.answers["permission"]
    ans_choice = result.answers["action"]
    ans_score = result.answers["threat"]

    decision_label = "APPROVED (İzin Verildi)" if ans_noul.decision else "DENIED (Engellendi)"
    werr_ver = getattr(werr, "__version__", "0.5.1")

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8560, log_level="info")
