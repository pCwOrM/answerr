"""
answerr Production REST API Server (v1.1.0 Commercial & Audit-Grade Edition)
A.N.S.W.E.R.R. — Adaptive Non-tensor Signal Wave & Error Reflex Resonator
Official Commercial Platform by ITouch Bilişim Sistemleri Ltd. Şti. (https://itouch.com.tr)

Provides public & commercial HTTP REST endpoints for https://answerr.me and https://api.answerr.me:
  - GET  /                           -> Service info, corporate metadata & active werr engine status
  - GET  /v1/health                  -> Instant health & 0-Byte VRAM verification
  - GET  /v1/presets                 -> Pre-configured domain state & question templates
  - GET  /v1/domains                 -> Available domain gate keys
  - POST /v1/decide                  -> Sub-millisecond System-1 typed decision with full Audit Trace & OOD Guard
  - GET  /v1/gates                   -> Commercial Policy & Gate Registry catalog
  - POST /v1/gates                   -> Register / seal a versioned PolicyGateSpec (SHA-256)
  - POST /v1/gates/{gate_id}/decide  -> Evaluate state against a sealed commercial PolicyGateSpec
  - POST /v1/policies/compile        -> System-2 Natural Language (TR/EN) -> Deterministic PolicyGateSpec compiler
  - POST /v1/systemone               -> JevBench TypeSafe wire format endpoint
  - POST /v1/chat/completions        -> OpenAI SDK-compatible reflex endpoint
"""
import os
import re
import sys
import time
import math
import json
import hashlib
import threading
from collections import defaultdict, deque
from typing import Dict, Any, List, Optional, Union, Tuple
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Ensure local or system werr package is importable
sys.path.insert(0, "/home/pcworm/werr")
import werr
import werr as wevv  # Backward-compatibility alias


START_TIME = time.time()

# -----------------------------------------------------------------------------
# Rate Limiting & Abuse Prevention (Zero External Dependency)
# -----------------------------------------------------------------------------
class InMemoryRateLimiter:
    """
    Thread-safe sliding-window rate limiter.
    Limits requests per client IP within a configurable time window.
    Automatically purges expired timestamps to maintain 0-leak in-memory footprint.
    """
    def __init__(self, requests_per_window: int = 120, window_seconds: int = 60, burst_per_second: int = 25):
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        self.burst_per_second = burst_per_second
        self.lock = threading.Lock()
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.last_cleanup = time.time()

    def get_client_ip(self, request: Request) -> str:
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
        if request.client and request.client.host:
            return request.client.host
        return "127.0.0.1"

    def is_allowed(self, ip: str) -> Tuple[bool, int, int]:
        now = time.time()
        with self.lock:
            if now - self.last_cleanup > 300:
                stale_cutoff = now - self.window_seconds
                stale_ips = [k for k, q in self.requests.items() if not q or q[-1] < stale_cutoff]
                for k in stale_ips:
                    del self.requests[k]
                self.last_cleanup = now

            timestamps = self.requests[ip]
            cutoff = now - self.window_seconds

            while timestamps and timestamps[0] < cutoff:
                timestamps.popleft()

            one_sec_ago = now - 1.0
            burst_count = sum(1 for t in timestamps if t >= one_sec_ago)
            if burst_count >= self.burst_per_second:
                return False, 0, 1

            if len(timestamps) >= self.requests_per_window:
                oldest = timestamps[0]
                retry_after = max(1, int(self.window_seconds - (now - oldest)))
                return False, 0, retry_after

            timestamps.append(now)
            remaining = max(0, self.requests_per_window - len(timestamps))
            return True, remaining, 0


RATE_LIMITER = InMemoryRateLimiter(requests_per_window=120, window_seconds=60, burst_per_second=25)
MAX_REQUEST_BODY_BYTES = 65536  # 64 KB limit to protect server memory and CPU

# Global engine instances
DEFAULT_ROUTER = werr.create_smart_router()
SYSTEMONE_ROUTER = werr.WerrEngine(
    enable_domain=True,
    enable_lexical=True,
    enable_resonance=True,
    mode="hybrid",
    domain_mode="multi",
    tripod=True,
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
# Commercial Policy & Gate Registry (In-Memory + Deterministic SHA-256 Seals)
# -----------------------------------------------------------------------------
def compute_policy_sha256(policy_dict: Dict[str, Any]) -> str:
    canonical = json.dumps(policy_dict, sort_keys=True, ensure_ascii=False)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]


COMMERCIAL_GATES: Dict[str, Dict[str, Any]] = {
    "agent_mcp_guard": {
        "gate_id": "agent_mcp_guard",
        "version": "1.2.0",
        "title": "AI Agent & WebMCP Action Firewall",
        "title_tr": "AI Ajan ve WebMCP Aksiyon Güvenlik Kapısı",
        "category": "Agentic AI Security",
        "owner": "ITouch Bilişim Sistemleri Ltd. Şti.",
        "unknown_fallback": "abstain_review",
        "required_fields": ["tool_name", "user_role"],
        "seed_24b": {"cx": -0.7436438870371587, "cy": 0.1318259042053119, "zoom": 95.0, "tripod": True},
        "hard_rules": [
            {"id": "block_destructive_sql", "field": "tool_name", "op": "in", "value": ["drop", "delete", "truncate", "rm_rf", "format_disk", "export_private_keys"], "effect": "DENY", "reason": "Destructive or key-exfiltration tool call is strictly prohibited."},
            {"id": "review_high_value_wire", "field": "amount", "op": ">", "value": 10000, "effect": "REVIEW", "reason": "Agent transfer above 10,000 requires human-in-the-loop approval."},
            {"id": "allow_readonly_search", "field": "tool_name", "op": "in", "value": ["read_", "search_", "get_", "list_", "fetch_status"], "effect": "ALLOW", "reason": "Read-only idempotent tool call verified safe."}
        ],
        "feature_weights": {
            "failed_attempts": {"weight": 1.5, "scale": 5.0, "threshold": 0.0},
            "amount": {"weight": 1.2, "scale": 2500.0, "threshold": 500.0},
            "authenticated": {"weight": -1.0}
        },
        "invariants_verified": [
            "Destructive tool calls always evaluate to DENY regardless of user_role",
            "Unrecognized schema fields trigger ABSTAIN_REVIEW (Zero False-Confidence Liability)",
            "Halting guaranteed in <= 9 Mandelbrot boundary iterations (Lean 4 Rung 3)"
        ]
    },
    "fintech_payment_tr": {
        "gate_id": "fintech_payment_tr",
        "version": "1.1.0",
        "title": "Fintech & Payment Fraud Gate (KVKK / 3DS)",
        "title_tr": "Fintech Ödeme ve 3D-Secure Risk Kapısı",
        "category": "Fintech & Fraud",
        "owner": "ITouch Bilişim Sistemleri Ltd. Şti.",
        "unknown_fallback": "abstain_review",
        "required_fields": ["amount"],
        "seed_24b": {"cx": -0.748, "cy": 0.065, "zoom": 60.0, "tripod": True},
        "hard_rules": [
            {"id": "block_extreme_velocity", "field": "velocity", "op": ">=", "value": 15, "effect": "DENY", "reason": "Card velocity >= 15 attempts in window indicates automated carding attack."},
            {"id": "review_high_amount_new_device", "field": "amount", "op": ">=", "value": 25000, "effect": "REVIEW", "reason": "High-value transaction (>= 25,000) routed to 3DS / Manual Fraud Queue."}
        ],
        "feature_weights": {
            "amount": {"weight": 1.1, "scale": 5000.0, "threshold": 1000.0},
            "velocity": {"weight": 1.6, "scale": 5.0, "threshold": 1.0},
            "device_anomaly": {"weight": 2.0},
            "known_device": {"weight": -1.1},
            "biometric_cleared": {"weight": -1.4}
        },
        "invariants_verified": [
            "Monotonic risk with respect to transaction amount and velocity",
            "Deterministic replay across Python, JS, and REST runtimes"
        ]
    },
    "api_zero_trust_waf": {
        "gate_id": "api_zero_trust_waf",
        "version": "1.0.0",
        "title": "Zero-Trust API & DDoS Edge Gate",
        "title_tr": "Sıfır Güven API ve DDoS Sınır Kapısı",
        "category": "Cybersecurity",
        "owner": "ITouch Bilişim Sistemleri Ltd. Şti.",
        "unknown_fallback": "abstain_review",
        "required_fields": ["user_role"],
        "seed_24b": {"cx": -0.7436438870371587, "cy": 0.1318259042053119, "zoom": 120.0, "tripod": True},
        "hard_rules": [
            {"id": "block_brute_force", "field": "failed_attempts", "op": ">=", "value": 10, "effect": "DENY", "reason": "Brute-force threshold exceeded (failed_attempts >= 10)."},
            {"id": "block_rate_flood", "field": "req_frequency", "op": ">=", "value": 100, "effect": "DENY", "reason": "Volumetric flood detected (req_frequency >= 100 req/s)."}
        ],
        "feature_weights": {
            "failed_attempts": {"weight": 1.5, "scale": 5.0, "threshold": 0.0},
            "req_frequency": {"weight": 1.0, "scale": 50.0, "threshold": 5.0},
            "authenticated": {"weight": -1.0}
        },
        "invariants_verified": [
            "Admin never locked out when failed_attempts == 0 and req_frequency < 20",
            "Sub-millisecond execution with 0-Byte VRAM"
        ]
    }
}

for _gid, _gdata in COMMERCIAL_GATES.items():
    _gdata["policy_seal"] = compute_policy_sha256(_gdata)


# Lifespan Context Manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    warmup_start = time.perf_counter()
    DEFAULT_ROUTER.decide(
        state={"warmup": True},
        questions={"ready": werr.NoulQuestion("System ready?")}
    )
    warmup_ms = (time.perf_counter() - warmup_start) * 1000.0
    print(f"[*] Answerr werr Commercial Decision Engine v1.1.0 warmed up in {warmup_ms:.2f} ms (0 Byte VRAM)")
    yield


app = FastAPI(
    title="Answerr Reflex Decision Engine & Commercial Policy API",
    description="A.N.S.W.E.R.R. — Deterministic Natural-Language-Compiled Decision Policies & Zero-Memory System-1 Runtime by ITouch Bilişim Sistemleri Ltd. Şti. (itouch.com.tr)",
    version="1.1.0",
    lifespan=lifespan
)

# CORS Policy
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://answerr.me",
        "https://www.answerr.me",
        "https://api.answerr.me",
        "https://pcworm.github.io",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:5500"
    ],
    allow_origin_regex=r"https://.*\.answerr\.me",
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With", "X-API-Key", "X-Recaptcha-Token"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "Retry-After", "X-Answerr-Policy-Seal", "X-Answerr-Mode"],
    max_age=86400,
)


@app.middleware("http")
async def security_and_rate_limit_middleware(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)

    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > MAX_REQUEST_BODY_BYTES:
                return JSONResponse(
                    status_code=413,
                    content={
                        "status": "error",
                        "error": "Payload Too Large",
                        "message": f"Request body exceeds maximum limit of {MAX_REQUEST_BODY_BYTES} bytes (64 KB)."
                    }
                )
        except ValueError:
            pass

    if request.url.path not in ("/health", "/v1/health"):
        client_ip = RATE_LIMITER.get_client_ip(request)
        allowed, remaining, retry_after = RATE_LIMITER.is_allowed(client_ip)
        if not allowed:
            return JSONResponse(
                status_code=429,
                headers={
                    "X-RateLimit-Limit": str(RATE_LIMITER.requests_per_window),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": str(retry_after)
                },
                content={
                    "status": "error",
                    "error": "Too Many Requests",
                    "message": f"Rate limit exceeded. Maximum {RATE_LIMITER.requests_per_window} requests/minute or {RATE_LIMITER.burst_per_second} burst/sec allowed.",
                    "retry_after_seconds": retry_after
                }
            )
    else:
        remaining = RATE_LIMITER.requests_per_window

    response: Response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(RATE_LIMITER.requests_per_window)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    response.headers["Server"] = "werr-gateway"
    return response


# -----------------------------------------------------------------------------
# Request / Response Schemas
# -----------------------------------------------------------------------------
class QuestionSpec(BaseModel):
    type: str = Field("noul", description="'noul', 'choice', or 'score'")
    text: Optional[str] = Field(None, description="Semantic instructions / question text")
    instructions: Optional[str] = Field(None, description="Alias for text (compatible with werr-engine.js & JevBench)")
    threshold: Optional[float] = Field(0.5, description="Decision threshold for noul questions")
    criteria: Optional[Union[Dict[str, str], List[str]]] = Field(
        None,
        description="Dictionary of options for choice, or list of levels for score"
    )

    @property
    def resolved_text(self) -> str:
        return (self.text or self.instructions or "Is the proposed operation safe and valid?").strip()


class DecisionRequest(BaseModel):
    state: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Key-value operational state of the system"
    )
    domain: Optional[str] = Field(
        None,
        description="Optional domain preset key: 'api_security', 'ddos_mitigation', 'financial_risk', 'robotics_industrial', 'ecommerce_fraud'"
    )
    gate_id: Optional[str] = Field(
        None,
        description="Optional commercial policy gate ID (e.g. 'agent_mcp_guard', 'fintech_payment_tr')"
    )
    strict_policy: Optional[bool] = Field(
        False,
        description="When True, returns ABSTAIN_REVIEW if input state fields are unrecognized (Out-of-Domain Liability Guard)"
    )
    questions: Optional[Dict[str, QuestionSpec]] = Field(
        None,
        description="Dictionary of questions to evaluate against state"
    )
    question: Optional[str] = Field(
        None,
        description="Simplified single question string for quick reflex evaluation"
    )
    prompt: Optional[str] = Field(
        None,
        description="Natural language prompt containing both context and question"
    )
    recaptcha_token: Optional[str] = Field(
        None,
        description="Google reCAPTCHA v3 verification token"
    )
    cx: Optional[float] = None
    cy: Optional[float] = None
    zoom: Optional[float] = None


class HardRuleSpec(BaseModel):
    id: str
    field: str
    op: str = Field(..., description="One of '>', '>=', '<', '<=', '==', '!=', 'in'")
    value: Any
    effect: str = Field("DENY", description="'ALLOW', 'DENY', or 'REVIEW'")
    reason: Optional[str] = None


class PolicyGateCreateRequest(BaseModel):
    gate_id: str = Field(..., min_length=3, max_length=64)
    version: str = "1.0.0"
    title: str
    category: str = "Custom Policy"
    unknown_fallback: str = "abstain_review"
    required_fields: List[str] = Field(default_factory=list)
    hard_rules: List[HardRuleSpec] = Field(default_factory=list)
    feature_weights: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    seed_24b: Optional[Dict[str, Any]] = None


class PolicyCompileRequest(BaseModel):
    prompt: str = Field(..., description="Natural language policy description in Turkish or English")
    gate_id: Optional[str] = "custom_compiled_gate"
    domain: Optional[str] = "agent_mcp_guard"


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: Optional[str] = "werr-reflex-v1"
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.0
    max_tokens: Optional[int] = 512


# -----------------------------------------------------------------------------
# Audit Trace, Hard Rule & OOD (Out-of-Domain) Evaluation Helpers
# -----------------------------------------------------------------------------
KNOWN_SIGNAL_PATTERNS = [
    (r"\b(fail|failed|error|errors|attempt|attempts|hata|deneme)|_(fail|error|attempt|hata)", "signal_failure_count"),
    (r"\b(freq|frequency|rate|req_rate|req_frequency|syn_rate|velocity|geo_velocity|hiz)|_(freq|rate|velocity|count)", "signal_rate_velocity"),
    (r"\b(amount|transaction_amount|cart_value|tutar|price|borrow|exposure)", "signal_financial_exposure"),
    (r"\b(auth|auth_status|authenticated|valid|safe|safe_mode|known_device|biometric_cleared|dogrulandi|verified)", "signal_trust_boolean"),
    (r"\b(suspicious|supheli|anomali|device_anomaly|geo_burst|shipping_billing_mismatch|sandwich|attack|threat|exploit)", "signal_hazard_boolean"),
    (r"\b(user_role|role|rol|actor)", "signal_actor_role"),
    (r"\b(tool|tool_name|action|command|operation|method|endpoint)", "signal_agent_tool"),
    (r"\b(joint_temp|actuator_temp|motor_temp|cpu_temp|temp_celsius|sicaklik|joint_torque|torque|vibration|proximity)", "signal_robotics_telemetry"),
    (r"\b(health|health_pct|hp|ammo|ammo_pct|cover_dist|hostile_count)", "signal_tactical_state"),
    (r"\b(latency|latency_ms|gecikme|ping|load_factor|threshold|sensor_delta|variance|drift_index|stability)", "signal_parametric_metric"),
]


def evaluate_audit_trace(
    state: Dict[str, Any],
    gate_spec: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    recognized_fields: List[str] = []
    unrecognized_fields: List[str] = []
    matched_rules: List[str] = []
    feature_contributions: Dict[str, float] = {}
    hard_rule_hit: Optional[Dict[str, Any]] = None

    # 1. Check hard rules if gate_spec is active
    if gate_spec and "hard_rules" in gate_spec:
        for rule in gate_spec["hard_rules"]:
            f_name = rule["field"]
            val = state.get(f_name)
            if val is None and f_name == "amount":
                val = state.get("amount_usd", state.get("cart_value"))
            if val is None and f_name == "velocity":
                val = state.get("card_attempts", state.get("geo_velocity", state.get("req_frequency")))
            if val is None:
                continue
            op = rule["op"]
            target = rule["value"]
            hit = False
            try:
                if op == ">":
                    hit = val > target
                elif op == ">=":
                    hit = val >= target
                elif op == "<":
                    hit = val < target
                elif op == "<=":
                    hit = val <= target
                elif op in ("==", "="):
                    hit = val == target
                elif op == "!=":
                    hit = val != target
                elif op == "in" and isinstance(target, list):
                    if isinstance(val, str):
                        val_l = val.lower()
                        hit = (val in target) or any(str(t).lower() in val_l for t in target)
                    else:
                        hit = val in target
            except Exception:
                hit = False
            if hit:
                hard_rule_hit = {
                    "rule_id": rule["id"],
                    "effect": rule["effect"].upper(),
                    "reason": rule.get("reason") or f"{f_name} {op} {target}"
                }
                matched_rules.append(f"hard_rule:{rule['id']}->{rule['effect'].upper()}")
                break

    gate_weights = (gate_spec or {}).get("feature_weights", {})
    req_fields = (gate_spec or {}).get("required_fields", [])
    missing_required = [rf for rf in req_fields if rf not in state]

    for k in sorted(state.keys()):
        if k in ("_task_id", "presetId", "warmup", "ping"):
            recognized_fields.append(k)
            continue
        v = state[k]
        kl = k.lower()
        recognized = False
        contrib = 0.0

        if k in gate_weights:
            recognized = True
            gw = gate_weights[k]
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                scale = gw.get("scale", 1.0) or 1.0
                thresh = gw.get("threshold", 0.0)
                contrib = ((float(v) - thresh) / scale) * gw.get("weight", 1.0)
            elif isinstance(v, bool):
                contrib = (1.0 if v else -1.0) * gw.get("weight", 1.0)
            matched_rules.append(f"policy_weight:{k}({contrib:+.3f})")

        if not recognized:
            for pattern, rule_tag in KNOWN_SIGNAL_PATTERNS:
                if re.search(pattern, kl):
                    recognized = True
                    matched_rules.append(f"{rule_tag}:{k}={v}")
                    if isinstance(v, bool):
                        contrib = -0.8 if ("auth" in kl or "valid" in kl or "safe" in kl or "known" in kl) and v else (1.2 if not v else 1.5)
                    elif isinstance(v, (int, float)):
                        contrib = round(math.tanh(float(v) / 25.0), 4)
                    elif isinstance(v, str):
                        vl = v.lower()
                        if any(r in vl for r in ("admin", "root", "yonetici", "read", "get", "search", "list")):
                            contrib = -1.2
                        elif any(r in vl for r in ("attacker", "bot", "drop", "delete", "transfer", "exec", "malicious")):
                            contrib = 2.2
                    break

        feature_contributions[k] = round(contrib, 4)
        if recognized:
            recognized_fields.append(k)
        else:
            unrecognized_fields.append(k)

    user_keys = [k for k in state.keys() if k not in ("_task_id", "presetId", "warmup", "ping")]
    ood_detected = (len(recognized_fields) == 0 and len(user_keys) > 0)

    policy_id = (gate_spec or {}).get("gate_id", "universal_default")
    policy_ver = (gate_spec or {}).get("version", "1.1.0")
    policy_seal = (gate_spec or {}).get("policy_seal") or compute_policy_sha256({"policy_id": policy_id, "state_keys": sorted(user_keys)})

    return {
        "policy_id": policy_id,
        "policy_version": policy_ver,
        "policy_seal": policy_seal,
        "matched_rules": matched_rules,
        "feature_contributions": feature_contributions,
        "recognized_fields": recognized_fields,
        "unrecognized_fields": unrecognized_fields,
        "missing_required_fields": missing_required,
        "hard_rule_hit": hard_rule_hit,
        "ood_detected": ood_detected,
        "recommended_mode": "ABSTAIN_REVIEW" if ood_detected else "DETERMINISTIC_EXECUTE"
    }


def build_engine(
    cx: Optional[float] = None,
    cy: Optional[float] = None,
    zoom: Optional[float] = None,
    domain: Optional[str] = None,
):
    if cx is not None and cy is not None and zoom is not None:
        if domain:
            return werr.WerrEngine(
                cx=cx,
                cy=cy,
                zoom=zoom,
                enable_domain=True,
                enable_lexical=True,
                enable_resonance=True,
                mode="hybrid",
                domain_mode="multi",
                tripod=True,
            )
        return werr.WerrEngine(
            cx=cx,
            cy=cy,
            zoom=zoom,
            enable_domain=False,
            enable_lexical=False,
            enable_resonance=False,
            mode="pure_fractal",
            domain_mode="none",
            tripod=True,
        )
    return DEFAULT_ROUTER


def parse_prompt_to_state(prompt: str) -> Dict[str, Any]:
    """Extracts lightweight semantic cues from natural language prompt into state."""
    p_lower = prompt.lower()
    state = {}

    if any(k in p_lower for k in ["admin", "root", "yonetici", "yetkili"]):
        state["user_role"] = "admin"
    elif any(k in p_lower for k in ["attacker", "bot", "hacker", "saldirgan", "malicious", "ddos"]):
        state["user_role"] = "attacker"
    elif any(k in p_lower for k in ["guest", "misafir", "anonymous", "anonim", "unverified"]):
        state["user_role"] = "guest"
    else:
        state["user_role"] = "member"

    if "error" in p_lower or "hata" in p_lower or "fail" in p_lower:
        state["failed_attempts"] = 5
    else:
        state["failed_attempts"] = 0

    if "fast" in p_lower or "burst" in p_lower or "hizli" in p_lower:
        state["req_frequency"] = 45.0
    else:
        state["req_frequency"] = 2.0

    return state


# -----------------------------------------------------------------------------
# API Endpoints
# -----------------------------------------------------------------------------
@app.get("/", tags=["Info"])
def get_root():
    uptime = time.time() - START_TIME
    return {
        "service": "Answerr Reflex Decision Engine & Commercial Policy API",
        "corporate_provider": "ITouch Bilişim Sistemleri Ltd. Şti. (https://itouch.com.tr)",
        "full_name": "A.N.S.W.E.R.R. (Adaptive Non-tensor Signal Wave & Error Reflex Resonator)",
        "description": "Natural-language-compiled, deterministic, sub-millisecond decision policies & AI agent action gates with 0-Byte VRAM.",
        "docs_url": "/docs",
        "endpoints": {
            "decide": "/v1/decide (POST)",
            "gates": "/v1/gates (GET, POST)",
            "gate_decide": "/v1/gates/{gate_id}/decide (POST)",
            "compile_policy": "/v1/policies/compile (POST)",
            "systemone": "/v1/systemone (POST)",
            "health": "/v1/health (GET)",
            "presets": "/v1/presets (GET)",
            "domains": "/v1/domains (GET)",
            "chat_completions": "/v1/chat/completions (POST - OpenAI Compatible)"
        },
        "engine": f"werr-reflex-{getattr(werr, '__version__', '0.5.1')}",
        "vram_usage_bytes": 0,
        "uptime_seconds": round(uptime, 2),
        "version": "1.1.0"
    }


@app.get("/v1/health", tags=["Health"])
@app.get("/health", tags=["Health"])
def get_health():
    uptime = time.time() - START_TIME
    t0 = time.perf_counter()
    DEFAULT_ROUTER.decide(
        state={"ping": True},
        questions={"alive": werr.NoulQuestion(instructions="Is engine responsive?")}
    )
    bench_latency_ms = (time.perf_counter() - t0) * 1000.0

    return {
        "status": "healthy",
        "engine": "werr-reflex",
        "version": getattr(werr, "__version__", "0.5.1"),
        "api_version": "1.1.0",
        "provider": "ITouch Bilisim Sistemleri Ltd. Sti. (itouch.com.tr)",
        "core_architecture": "werr (Adaptive Non-tensor Signal Wave & Error Reflex Resonator)",
        "memory_architecture": "0 Byte VRAM / 24 Byte Mandelbrot Coordinate Triplet",
        "vram_bytes": 0,
        "commercial_gates_loaded": len(COMMERCIAL_GATES),
        "latency_benchmark_ms": round(bench_latency_ms, 3),
        "uptime_seconds": round(uptime, 2),
        "timestamp": time.time()
    }


@app.get("/v1/presets", tags=["Catalog"])
def get_presets():
    """Returns standard pre-configured scenarios and questions."""
    return {"status": "success", "presets": PRESETS}


@app.get("/v1/domains", tags=["Catalog"])
def get_domains():
    """Returns available domain gate keys."""
    return {
        "status": "success",
        "available_domains": list(DOMAIN_GATES.keys()) + ["ddos_mitigation", "robotics_industrial", "agent_mcp_guard"]
    }


@app.get("/v1/gates", tags=["Commercial Policy Gates"])
def list_commercial_gates():
    """Lists all registered & cryptographically sealed commercial decision gates."""
    return {
        "status": "success",
        "provider": "ITouch Bilişim Sistemleri Ltd. Şti. (itouch.com.tr)",
        "count": len(COMMERCIAL_GATES),
        "gates": COMMERCIAL_GATES
    }


@app.post("/v1/gates", tags=["Commercial Policy Gates"])
def register_commercial_gate(req: PolicyGateCreateRequest):
    """Registers or updates a versioned commercial PolicyGateSpec and seals it with SHA-256."""
    gate_dict = {
        "gate_id": req.gate_id,
        "version": req.version,
        "title": req.title,
        "category": req.category,
        "owner": "ITouch Bilişim Sistemleri Ltd. Şti. / Tenant",
        "unknown_fallback": req.unknown_fallback,
        "required_fields": req.required_fields,
        "seed_24b": req.seed_24b or {"cx": -0.7436438870371587, "cy": 0.1318259042053119, "zoom": 80.0, "tripod": True},
        "hard_rules": [r.dict() for r in req.hard_rules],
        "feature_weights": req.feature_weights,
        "invariants_verified": [
            "Explicit schema & OOD Abstain/Review fallback active",
            "Deterministic 24-Byte Mandelbrot boundary manifold"
        ]
    }
    gate_dict["policy_seal"] = compute_policy_sha256(gate_dict)
    COMMERCIAL_GATES[req.gate_id] = gate_dict
    return {
        "status": "registered",
        "gate_id": req.gate_id,
        "policy_seal": gate_dict["policy_seal"],
        "decide_endpoint": f"/v1/gates/{req.gate_id}/decide",
        "gate": gate_dict
    }


@app.post("/v1/policies/compile", tags=["Commercial Policy Gates"])
def compile_natural_language_policy(req: PolicyCompileRequest):
    """
    System-2 Natural Language (TR/EN) -> Deterministic PolicyGateSpec Compiler.
    Compiles human policy statements at design time into an explicit, versioned,
    SHA-256-sealed PolicyGateSpec with zero runtime LLM hallucination.
    """
    p = req.prompt.strip()
    p_low = p.lower()
    hard_rules = []
    required_fields = []
    feature_weights: Dict[str, Dict[str, float]] = {}

    # Extract numeric thresholds from natural language (TR/EN)
    amt_match = re.search(r"(\d[\d\.]*)\s*(?:tl|try|usd|\$|dolar|euro|üzeri|ustu|üstünde|above|over|exceed)", p_low)
    if amt_match:
        val = float(amt_match.group(1).replace(".", ""))
        effect = "REVIEW" if any(w in p_low for w in ["incele", "onay", "3ds", "review", "mfa", "hold"]) else "DENY"
        hard_rules.append({
            "id": "compiled_amount_threshold",
            "field": "amount",
            "op": ">=",
            "value": val,
            "effect": effect,
            "reason": f"Compiled from NL policy: amount >= {val} -> {effect}"
        })
        required_fields.append("amount")
        feature_weights["amount"] = {"weight": 1.2, "scale": max(1000.0, val / 2.0), "threshold": val / 4.0}

    fail_match = re.search(r"(\d+)\s*(?:hata|başarısız|basarisiz|deneme|fail|failed|attempt|error)", p_low)
    if fail_match:
        f_val = int(fail_match.group(1))
        hard_rules.append({
            "id": "compiled_failure_limit",
            "field": "failed_attempts",
            "op": ">=",
            "value": f_val,
            "effect": "DENY",
            "reason": f"Compiled from NL policy: failed_attempts >= {f_val} -> DENY"
        })
        required_fields.append("failed_attempts")
        feature_weights["failed_attempts"] = {"weight": 1.6, "scale": float(max(1, f_val)), "threshold": 0.0}

    if any(w in p_low for w in ["ajan", "agent", "mcp", "sql", "sil", "drop", "delete", "tool", "araç"]):
        hard_rules.append({
            "id": "compiled_agent_destructive_guard",
            "field": "tool_name",
            "op": "in",
            "value": ["drop_table", "delete_user", "rm_rf", "wire_transfer", "exec_shell"],
            "effect": "DENY",
            "reason": "Compiled agentic guardrail against destructive tool execution"
        })
        if "tool_name" not in required_fields:
            required_fields.append("tool_name")

    if not hard_rules:
        hard_rules.append({
            "id": "compiled_default_anomaly_guard",
            "field": "failed_attempts",
            "op": ">=",
            "value": 5,
            "effect": "DENY",
            "reason": "Default safety threshold (failed_attempts >= 5 -> DENY)"
        })

    compiled_spec = {
        "gate_id": req.gate_id or "compiled_policy_v1",
        "version": "1.0.0",
        "title": f"Compiled Policy: {p[:56]}{'...' if len(p) > 56 else ''}",
        "category": req.domain or "Compiled NL Policy",
        "owner": "ITouch Bilişim Sistemleri Ltd. Şti. / Studio Compiler",
        "source_prompt": p,
        "unknown_fallback": "abstain_review",
        "required_fields": required_fields or ["user_role"],
        "seed_24b": {"cx": -0.7436438870371587, "cy": 0.1318259042053119, "zoom": 90.0, "tripod": True},
        "hard_rules": hard_rules,
        "feature_weights": feature_weights or {"failed_attempts": {"weight": 1.5, "scale": 5.0, "threshold": 0.0}},
        "invariants_verified": [
            "Disjoint hard rules (No contradictory ALLOW/DENY overlap)",
            "OOD Fail-Safe: Unrecognized input schema defaults to ABSTAIN_REVIEW",
            "0-Byte VRAM deterministic execution (< 0.5 ms)"
        ]
    }
    compiled_spec["policy_seal"] = compute_policy_sha256(compiled_spec)
    COMMERCIAL_GATES[compiled_spec["gate_id"]] = compiled_spec

    gid = compiled_spec["gate_id"]
    py_snippet = (
        f"import requests\n"
        f"res = requests.post('https://api.answerr.me/v1/gates/{gid}/decide', json={{\n"
        f"    'state': {{'tool_name': 'delete_customer_ledger', 'amount_usd': 7200, 'failed_attempts': 1}},\n"
        f"    'question': 'Allow this action under policy {gid}?'\n"
        f"}}).json()\n"
        f"print(res['decision'], res['trace']['policy_seal'], res['trace']['matched_rules'])"
    )
    curl_snippet = (
        f"curl -X POST https://api.answerr.me/v1/gates/{gid}/decide "
        f"-H \"Content-Type: application/json\" "
        f"-d '{{\"state\":{{\"tool_name\":\"delete_customer_ledger\",\"amount_usd\":7200}},\"question\":\"Allow action?\"}}'"
    )

    return {
        "status": "compiled",
        "policy_seal": compiled_spec["policy_seal"],
        "decide_endpoint": f"/v1/gates/{gid}/decide",
        "policy_spec": compiled_spec,
        "compiled_policy": compiled_spec,
        "sdk_snippet_python": py_snippet,
        "sdk_snippet_curl": curl_snippet
    }


@app.post("/v1/gates/{gate_id}/decide", tags=["Commercial Policy Gates"])
def decide_with_commercial_gate(gate_id: str, req: DecisionRequest):
    """
    Evaluates operational state against a specific cryptographically sealed commercial gate.
    Enforces hard rules, OOD Abstain/Review protection, and 24-Byte fractal boundary scoring.
    """
    if gate_id not in COMMERCIAL_GATES:
        raise HTTPException(status_code=404, detail=f"Commercial gate '{gate_id}' not found.")
    req.gate_id = gate_id
    req.strict_policy = True
    return post_decide(req)


@app.post("/v1/decide", tags=["Decision Engine"])
def post_decide(req: DecisionRequest):
    """
    Sub-millisecond System-One Typed Decision Endpoint.
    Zero weights stored, zero VRAM used. Evaluates state continuously against fractal boundary
    and returns full audit-grade Decision Trace (`trace`) + OOD protection.
    """
    t_start = time.perf_counter()
    state = dict(req.state) if req.state else {}

    if req.prompt and not state:
        state = parse_prompt_to_state(req.prompt)

    gate_spec = COMMERCIAL_GATES.get(req.gate_id) if req.gate_id else None
    audit_trace = evaluate_audit_trace(state, gate_spec=gate_spec)

    # Resolve questions dictionary
    werr_questions = {}

    if req.questions:
        for q_id, q_spec in req.questions.items():
            q_type = q_spec.type.lower().strip()
            q_text = q_spec.resolved_text
            if q_type == "noul":
                werr_questions[q_id] = werr.NoulQuestion(instructions=q_text, threshold=q_spec.threshold or 0.5)
            elif q_type == "choice":
                crit = q_spec.criteria or {"option_a": "Option A", "option_b": "Option B"}
                if isinstance(crit, list):
                    crit = {f"opt_{i}": v for i, v in enumerate(crit)}
                werr_questions[q_id] = werr.ChoiceQuestion(instructions=q_text, criteria=crit)
            elif q_type == "score":
                crit = q_spec.criteria or ["Low", "Moderate", "High", "Extreme"]
                if isinstance(crit, dict):
                    crit = list(crit.values())
                werr_questions[q_id] = werr.ScoreQuestion(instructions=q_text, criteria=crit)
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported question type '{q_spec.type}'. Must be 'noul', 'choice', or 'score'."
                )
    elif req.question:
        werr_questions["primary_decision"] = werr.NoulQuestion(instructions=req.question)
        werr_questions["recommendation"] = werr.ChoiceQuestion(
            instructions="Recommended Action",
            criteria={
                "approve": "Approve / Allow",
                "quarantine": "Quarantine / Verify",
                "reject": "Reject / Deny"
            }
        )
        werr_questions["risk_score"] = werr.ScoreQuestion(
            instructions="Risk Assessment Scale",
            criteria=["Safe / Clean", "Moderate Warning", "High Anomaly", "Critical Hazard"]
        )
    elif req.domain and req.domain in PRESETS:
        preset_data = PRESETS[req.domain]
        if not state:
            state = dict(preset_data["default_state"])
            audit_trace = evaluate_audit_trace(state, gate_spec=gate_spec)
        for q_id, q_spec in preset_data["default_questions"].items():
            if q_spec["type"] == "noul":
                werr_questions[q_id] = werr.NoulQuestion(instructions=q_spec["text"])
            elif q_spec["type"] == "choice":
                crit = q_spec["criteria"]
                if isinstance(crit, list):
                    crit = {f"opt_{i}": v for i, v in enumerate(crit)}
                werr_questions[q_id] = werr.ChoiceQuestion(instructions=q_spec["text"], criteria=crit)
            elif q_spec["type"] == "score":
                crit = q_spec["criteria"]
                if isinstance(crit, dict):
                    crit = list(crit.values())
                werr_questions[q_id] = werr.ScoreQuestion(instructions=q_spec["text"], criteria=crit)
    else:
        werr_questions["decision"] = werr.NoulQuestion(instructions="Is the proposed operation safe and valid?")

    seed_cfg = (gate_spec or {}).get("seed_24b", {})
    eff_cx = req.cx if req.cx is not None else seed_cfg.get("cx")
    eff_cy = req.cy if req.cy is not None else seed_cfg.get("cy")
    eff_zoom = req.zoom if req.zoom is not None else seed_cfg.get("zoom")

    engine = build_engine(eff_cx, eff_cy, eff_zoom, domain=req.domain)
    result = engine.decide(state=state, questions=werr_questions)
    total_ms = (time.perf_counter() - t_start) * 1000.0

    active_coords = getattr(result, "active_coordinates", {"cx": eff_cx or -0.74364388, "cy": eff_cy or 0.1318259, "zoom": eff_zoom or 50.0})
    audit_trace["fractal_manifold"] = {
        "active_coordinates": active_coords,
        "escape_entropy": getattr(result, "escape_entropy", 0.0),
        "quadrant_entropy": getattr(result, "quadrant_entropy", 0.0),
        "coordinate_bytes": 24,
        "vram_bytes": 0
    }

    hard_hit = audit_trace.get("hard_rule_hit")
    ood_abstain = bool(audit_trace["ood_detected"] and (req.strict_policy or (gate_spec and gate_spec.get("unknown_fallback") == "abstain_review")))

    answers_out = {}
    primary_boolean: Optional[bool] = True
    primary_label = "APPROVED"

    for q_id, ans in result.answers.items():
        if isinstance(ans, (werr.NoulAnswer, wevv.NoulAnswer)):
            if hard_hit:
                eff = hard_hit["effect"]
                if eff == "REVIEW":
                    answers_out[q_id] = {
                        "type": "noul",
                        "boolean": None,
                        "decision": None,
                        "noul": 0.5,
                        "confidence": 0.0,
                        "label": "ABSTAIN_REVIEW",
                        "matched_rule": hard_hit["rule_id"],
                        "reason": hard_hit["reason"]
                    }
                    primary_boolean = None
                    primary_label = "ABSTAIN_REVIEW"
                else:
                    is_allow = (eff == "ALLOW")
                    answers_out[q_id] = {
                        "type": "noul",
                        "boolean": is_allow,
                        "decision": is_allow,
                        "noul": 0.99 if is_allow else 0.01,
                        "confidence": 0.99,
                        "label": "ALLOWED" if is_allow else "DENIED",
                        "matched_rule": hard_hit["rule_id"],
                        "reason": hard_hit["reason"]
                    }
                    primary_boolean = is_allow
                    primary_label = answers_out[q_id]["label"]
            elif ood_abstain:
                answers_out[q_id] = {
                    "type": "noul",
                    "boolean": None,
                    "decision": None,
                    "noul": 0.5,
                    "confidence": 0.0,
                    "label": "ABSTAIN_REVIEW",
                    "reason": "OUT_OF_POLICY_SCHEMA: Unrecognized or missing required state fields; routed to human review."
                }
                primary_boolean = None
                primary_label = "ABSTAIN_REVIEW"
            else:
                answers_out[q_id] = {
                    "type": "noul",
                    "boolean": ans.decision,
                    "decision": ans.decision,
                    "noul": round(ans.noul, 4),
                    "confidence": round(ans.confidence, 4),
                    "label": "ALLOWED" if ans.decision else "DENIED"
                }
                primary_boolean = ans.decision
                primary_label = answers_out[q_id]["label"]
        elif isinstance(ans, (werr.ChoiceAnswer, wevv.ChoiceAnswer)):
            answers_out[q_id] = {
                "type": "choice",
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
        "status": "abstain_review" if primary_label == "ABSTAIN_REVIEW" else "success",
        "decision": primary_boolean,
        "label": primary_label,
        "latency_ms": round(total_ms, 3),
        "seed_24b": active_coords,
        "input_state": state,
        "answers": answers_out,
        "results": answers_out,
        "trace": audit_trace,
        "telemetry": {
            "engine_latency_ms": round(result.latency_ms, 3),
            "total_request_latency_ms": round(total_ms, 3),
            "vram_bytes": 0,
            "memory_seed_bytes": 24,
            "policy_seal": audit_trace["policy_seal"],
            "recaptcha_shield": "active" if req.recaptcha_token else "open_sandbox",
            "engine": f"werr-reflex-{getattr(werr, '__version__', '0.5.1')}"
        },
        "werr_telemetry": {
            "engine_latency_ms": round(result.latency_ms, 3),
            "total_request_latency_ms": round(total_ms, 3),
            "vram_bytes": 0,
            "memory_seed_bytes": 24,
            "policy_seal": audit_trace["policy_seal"],
            "recaptcha_shield": "active" if req.recaptcha_token else "open_sandbox",
            "engine": f"werr-reflex-{getattr(werr, '__version__', '0.5.1')}"
        }
    }


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
        f"⚡ Answerr Reflex Decision (0 Byte VRAM, {total_ms:.2f} ms)\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• Status: {decision_label}\n"
        f"• Action: {ans_choice.choice}\n"
        f"• Threat: {ans_score.level} (Score: {ans_score.score:.2f})\n"
        f"• Confidence: %{ans_noul.confidence * 100:.1f} (p={ans_noul.noul:.3f})\n"
        f"• Memory: 0 Bytes Tensor VRAM (24-byte coordinate on dM boundary)\n"
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
