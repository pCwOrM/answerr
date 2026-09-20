"""
Answerr Reflex Decision Engine API - Production REST Server
A.N.S.W.E.R.R. (Adaptive Non-tensor Signal Wave & Error Reflex Resonator)
(Uyarlanabilir Tensörsüz Sinyal Dalgası ve Hata Refleksi Rezonatörü)
Powered by werr (Universal Fractal Natural Language Decision Map)

Features:
- Sub-millisecond deterministic typed decisions (noul, choice, score)
- 0 Bytes VRAM / Stored Weight Tensors (24-byte seed coordinate on dM boundary)
- Domain Gates: api_security, financial_risk, iot_safety, ecommerce_fraud, game_combat
- OpenAI-compatible /v1/chat/completions adapter
- Native bilingual support (Turkish / English)
- Microsecond latency telemetry
"""

import os
import sys
import time
from typing import Dict, List, Optional, Union, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Ensure werr (with fallback to wevv) is loaded
try:
    import werr
except ImportError:
    try:
        import wevv as werr
    except ImportError:
        sys.path.insert(0, '/home/pcworm/werr')
        sys.path.insert(0, '/home/pcworm/wevv_repo')
        try:
            import werr
        except ImportError:
            import wevv as werr

# Backward compatibility alias
wevv = werr

# Process start time for uptime calculation
START_TIME = time.time()

# Global engine instances
DEFAULT_ROUTER = werr.create_smart_router()
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


# Lifespan Context Manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warmup decision pass
    warmup_start = time.perf_counter()
    DEFAULT_ROUTER.decide(
        state={"warmup": True},
        questions={"ready": werr.NoulQuestion("System ready?")}
    )
    warmup_ms = (time.perf_counter() - warmup_start) * 1000.0
    print(f"[*] Answerr werr Decision Engine warmed up in {warmup_ms:.2f} ms (0 Byte VRAM)")
    yield


app = FastAPI(
    title="Answerr Reflex Decision Engine API",
    description="A.N.S.W.E.R.R. (Adaptive Non-tensor Signal Wave & Error Reflex Resonator) - 0 Bytes VRAM, < 1ms Latency",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Policy
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------------------------------------------
# Request / Response Schemas
# -----------------------------------------------------------------------------
class QuestionSpec(BaseModel):
    type: str = Field(..., description="'noul', 'choice', or 'score'")
    text: str = Field(..., description="Semantic instructions / question text")
    criteria: Optional[Union[Dict[str, str], List[str]]] = Field(
        None,
        description="Dictionary of options for choice, or list of levels for score"
    )


class DecisionRequest(BaseModel):
    state: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Key-value operational state of the system"
    )
    domain: Optional[str] = Field(
        None,
        description="Optional domain preset key: 'api_security', 'ddos_mitigation', 'financial_risk', 'robotics_industrial', 'ecommerce_fraud'"
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
    cx: Optional[float] = None
    cy: Optional[float] = None
    zoom: Optional[float] = None


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: Optional[str] = "werr-reflex-v1"
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.0
    max_tokens: Optional[int] = 512


# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------
def build_engine(cx: Optional[float] = None, cy: Optional[float] = None, zoom: Optional[float] = None):
    if cx is not None and cy is not None and zoom is not None:
        return werr.WerrEngine(cx=cx, cy=cy, zoom=zoom)
    return DEFAULT_ROUTER


def parse_prompt_to_state(prompt: str) -> Dict[str, Any]:
    """Extracts lightweight semantic cues from natural language prompt into state."""
    p_lower = prompt.lower()
    state = {}

    # Role recognition
    if any(k in p_lower for k in ["admin", "root", "yonetici", "yetkili"]):
        state["user_role"] = "admin"
    elif any(k in p_lower for k in ["attacker", "bot", "hacker", "saldirgan", "malicious", "ddos"]):
        state["user_role"] = "attacker"
    elif any(k in p_lower for k in ["guest", "misafir", "anonymous", "anonim", "unverified"]):
        state["user_role"] = "guest"
    else:
        state["user_role"] = "member"

    # Quantitative heuristics
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
        "service": "Answerr Reflex Decision Engine API",
        "full_name": "A.N.S.W.E.R.R. (Adaptive Non-tensor Signal Wave & Error Reflex Resonator)",
        "description": "Adaptive Non-tensor Signal Wave & Error Reflex Resonator (Uyarlanabilir Tensörsüz Sinyal Dalgası ve Hata Refleksi Rezonatörü) - Zero-Memory, Zero-Hallucination, Sub-millisecond System-One Decision Engine",
        "docs_url": "/docs",
        "endpoints": {
            "decide": "/v1/decide (POST)",
            "health": "/v1/health (GET)",
            "presets": "/v1/presets (GET)",
            "domains": "/v1/domains (GET)",
            "chat_completions": "/v1/chat/completions (POST - OpenAI Compatible)"
        },
        "engine": "werr-reflex-0.3.0",
        "vram_usage_bytes": 0,
        "uptime_seconds": round(uptime, 2),
        "version": "1.0.0"
    }


@app.get("/v1/health", tags=["Health"])
@app.get("/health", tags=["Health"])
def get_health():
    uptime = time.time() - START_TIME
    
    # Measure instantaneous reflex benchmark
    t0 = time.perf_counter()
    DEFAULT_ROUTER.decide(
        state={"ping": True},
        questions={"alive": werr.NoulQuestion(instructions="Is engine responsive?")}
    )
    bench_latency_ms = (time.perf_counter() - t0) * 1000.0

    return {
        "status": "healthy",
        "engine": "werr-reflex",
        "version": "0.3.0",
        "core_architecture": "werr (Adaptive Non-tensor Signal Wave & Error Reflex Resonator)",
        "memory_architecture": "0 Byte VRAM / 24 Byte Mandelbrot Coordinate Triplet",
        "vram_bytes": 0,
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
        "available_domains": list(DOMAIN_GATES.keys()) + ["ddos_mitigation", "robotics_industrial"]
    }


@app.post("/v1/decide", tags=["Decision Engine"])
def post_decide(req: DecisionRequest):
    """
    Sub-millisecond System-One Typed Decision Endpoint.
    Zero weights stored, zero VRAM used. Evaluates state continuously against fractal boundary.
    """
    t_start = time.perf_counter()
    state = dict(req.state) if req.state else {}

    # Extract state from prompt if provided
    if req.prompt and not state:
        state = parse_prompt_to_state(req.prompt)

    # Resolve questions dictionary
    werr_questions = {}

    if req.questions:
        for q_id, q_spec in req.questions.items():
            q_type = q_spec.type.lower().strip()
            if q_type == "noul":
                werr_questions[q_id] = werr.NoulQuestion(instructions=q_spec.text)
            elif q_type == "choice":
                crit = q_spec.criteria or {"option_a": "Option A", "option_b": "Option B"}
                if isinstance(crit, list):
                    crit = {f"opt_{i}": v for i, v in enumerate(crit)}
                werr_questions[q_id] = werr.ChoiceQuestion(instructions=q_spec.text, criteria=crit)
            elif q_type == "score":
                crit = q_spec.criteria or ["Low", "Moderate", "High", "Extreme"]
                if isinstance(crit, dict):
                    crit = list(crit.values())
                werr_questions[q_id] = werr.ScoreQuestion(instructions=q_spec.text, criteria=crit)
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported question type '{q_spec.type}'. Must be 'noul', 'choice', or 'score'."
                )
    elif req.question:
        # User provided a single natural language question
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
        # Load preset questions for the specified domain
        preset_data = PRESETS[req.domain]
        if not state:
            state = dict(preset_data["default_state"])
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
        # Default generic evaluation question
        werr_questions["decision"] = werr.NoulQuestion(instructions="Is the proposed operation safe and valid?")

    # Select engine
    engine = build_engine(req.cx, req.cy, req.zoom)
    
    # Compute decision
    result = engine.decide(state=state, questions=werr_questions)
    total_ms = (time.perf_counter() - t_start) * 1000.0

    # Format answers
    answers_out = {}
    primary_boolean = True
    primary_label = "APPROVED"

    for q_id, ans in result.answers.items():
        if isinstance(ans, (werr.NoulAnswer, wevv.NoulAnswer)):
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
        "status": "success",
        "decision": primary_boolean,
        "label": primary_label,
        "input_state": state,
        "answers": answers_out,
        "telemetry": {
            "engine_latency_ms": round(result.latency_ms, 3),
            "total_request_latency_ms": round(total_ms, 3),
            "vram_bytes": 0,
            "memory_seed_bytes": 24,
            "engine": "werr-reflex-0.3.0"
        },
        "werr_telemetry": {
            "engine_latency_ms": round(result.latency_ms, 3),
            "total_request_latency_ms": round(total_ms, 3),
            "vram_bytes": 0,
            "memory_seed_bytes": 24,
            "engine": "werr-reflex-0.3.0"
        }
    }


@app.post("/v1/chat/completions", tags=["OpenAI Adapter"])
def chat_completions(req: ChatCompletionRequest):
    """
    OpenAI-compatible chat completion endpoint.
    Allows standard LLM libraries (LangChain, LlamaIndex, OpenAI SDK) to query Answerr directly.
    """
    t_start = time.perf_counter()
    
    # Find last user message
    user_content = ""
    for msg in reversed(req.messages):
        if msg.role == "user":
            user_content = msg.content
            break

    if not user_content:
        user_content = "Evaluate system state"

    state = parse_prompt_to_state(user_content)
    
    # Run reflex evaluation
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
    
    content_text = (
        f"⚡ Answerr Reflex Decision (0 Byte VRAM, {total_ms:.2f} ms)\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• Status: {decision_label}\n"
        f"• Action: {ans_choice.choice}\n"
        f"• Threat: {ans_score.level} (Score: {ans_score.score:.2f})\n"
        f"• Confidence: %{ans_noul.confidence * 100:.1f} (p={ans_noul.noul:.3f})\n"
        f"• Memory: 0 Bytes Tensor VRAM (24-byte coordinate on dM boundary)\n"
        f"• Engine: werr 0.3.0 (Wave & Error Reflex Resonator)"
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
            "engine": "werr-reflex-0.3.0"
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
