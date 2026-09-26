"""
answerr Server - Dual-Cognition AI API Gateway (FastAPI)
Bridges Gemini System-Two Deliberation with werr System-One Fractal Reflexes
"""
import os
import sys
import time
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Add local paths if present
LOCAL_WERR_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "werr"))
if os.path.exists(LOCAL_WERR_PATH) and LOCAL_WERR_PATH not in sys.path:
    sys.path.insert(0, LOCAL_WERR_PATH)

try:
    from werr import WerrEngine as EngineCls, NoulQuestion, ChoiceQuestion, ScoreQuestion
    HAS_LOCAL_ENGINE = True
except ImportError:
    try:
        from wevv import WevvEngine as EngineCls, NoulQuestion, ChoiceQuestion, ScoreQuestion
        HAS_LOCAL_ENGINE = True
    except ImportError:
        HAS_LOCAL_ENGINE = False

app = FastAPI(
    title="answerr API",
    description="Cognitive bridge between Gemini Flash System-2 and werr Zero-Memory System-1",
    version="0.3.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DecideRequest(BaseModel):
    state: Dict[str, Any]
    question_type: str = "noul" # noul, choice, score
    instructions: str = ""
    criteria: Optional[Any] = None
    threshold: float = 0.5

class ChatRequest(BaseModel):
    message: str
    api_key: Optional[str] = None
    model: Optional[str] = "gemini-2.5-flash"

@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "answerr",
        "has_local_engine": HAS_LOCAL_ENGINE,
        "engine": "werr-0.5.1-fractal",
        "tensor_vram_bytes": 0,
        "seed_bytes": 24
    }

@app.post("/api/decide")
def api_decide(req: DecideRequest):
    """Direct System-One werr Decision Endpoint (< 2ms)"""
    start_time = time.perf_counter()

    if HAS_LOCAL_ENGINE:
        engine = EngineCls(
            resolution=48,
            enable_domain=True,
            enable_lexical=True,
            enable_resonance=True,
            mode="hybrid",
            domain_mode="multi",
            tripod=True,
        )
        if req.question_type == "choice":
            q_obj = ChoiceQuestion(
                instructions=req.instructions,
                criteria=req.criteria if isinstance(req.criteria, dict) else {c: c for c in (req.criteria or ["yes", "no"])}
            )
        elif req.question_type == "score":
            q_obj = ScoreQuestion(
                instructions=req.instructions,
                criteria=req.criteria if isinstance(req.criteria, list) else ["Low", "Medium", "High", "Critical"]
            )
        else:
            q_obj = NoulQuestion(instructions=req.instructions, threshold=req.threshold)

        res = engine.decide(state=req.state, questions={"decision": q_obj})
        ans = res.answers["decision"]
        elapsed = (time.perf_counter() - start_time) * 1000.0

        return {
            "model": "werr-0.5.1-fractal",
            "type": req.question_type,
            "answer": ans.__dict__,
            "latency_ms": round(elapsed, 2),
            "memory_tensor_bytes": 0,
            "coordinate_bytes": 24
        }
    else:
        # Fallback simulation
        elapsed = (time.perf_counter() - start_time) * 1000.0
        return {
            "model": "werr-0.5.1-simulation",
            "type": req.question_type,
            "answer": {"decision": True, "confidence": 0.88, "noul": 0.88},
            "latency_ms": round(elapsed, 2),
            "memory_tensor_bytes": 0,
            "coordinate_bytes": 24
        }

# Mount static frontend files for production deployment
STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if os.path.exists(os.path.join(STATIC_DIR, "index.html")):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
