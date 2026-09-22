# ⚡ Learning Answerr: Zero-Latency Reflex AI & Dual-Process Cognition

Welcome to **A.N.S.W.E.R.R.** (Adaptive Neuro-Symbolic Wave Error Reflex Runtime)!

This guide helps students, researchers, and developers understand how to bridge high-latency deliberative language models with ultra-fast, zero-memory reflex decision loops.

---

## 🎯 1. Architectural Vision: Fast & Slow AI

Large Language Models (LLMs) excel at deliberative reasoning, linguistic synthesis, and complex planning. However, querying an LLM API:
* Incurs significant latency (typically 300ms to 3,000ms).
* Consumes network bandwidth and API credits.
* Is unsuitable for instant, real-time reactive tasks (e.g., UI feedback, collision reflex, rapid triage).

**Answerr implements a Dual-Process Cognitive Architecture:**
```
            +--------------------------------------------+
            |               Incoming Event               |
            +--------------------------------------------+
                                   |
                +------------------+------------------+
                |                                     |
       [System 1: Fast Reflex]              [System 2: Slow Thinking]
     Zero-Memory Fractal Decision               Deliberative LLM
       Latency: Sub-Millisecond               Latency: Hundreds of ms
                |                                     |
                v                                     v
       Immediate Action / UI Guard          Deep Synthesis & Strategy
```

---

## 🛠️ 2. Core Concepts You Will Learn

### A. Reflex Routing
Before triggering an expensive external LLM query, Answerr evaluates deterministic state coordinates to decide if an instant reflex response can resolve the user request immediately.

### B. In-Browser Client-Side Execution
Answerr does not require GPU servers or heavy cloud backends for its reflex layer. It runs 100% locally in any modern browser via JavaScript and Canvas rendering.

### C. WebMCP Standard Interoperability
Answerr exposes standard Web Model Context Protocol (WebMCP) endpoints so browser agents, web tools, and LLMs can query reflex status seamlessly.

---

## 🚀 3. Getting Started in 3 Steps

### Step 1: Launch the Interactive Benchmark
No build steps or bundlers needed:
1. Clone the repository:
   ```bash
   git clone https://github.com/pCwOrM/answerr.git
   cd answerr
   ```
2. Double-click `index.html` or open it with your browser:
   * Explore the interactive radar visualization.
   * Run the latency benchmark and compare simulated neural net inference against deterministic reflex routing.

### Step 2: Run the Local Python REST API Server
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run the FastAPI / Uvicorn server:
uvicorn api_server:app --host 0.0.0.0 --port 4431 --reload
```

### Step 3: Run the Automated API Client Test
```bash
python test_api.py
```
Verify that the decision responses return typed JSON payloads with verified latency metrics.

---

## 🎓 4. Student Projects & Hands-On Exercises

Want to build a student portfolio project or contribute to Answerr? Here are great starting points:

1. **Benchmark Data Visualizer:** Check out [Issue #9](https://github.com/pCwOrM/answerr/issues/9) to add a one-click CSV / JSON export of recorded latency trials.
2. **UI Dark/Light Mode Theme:** Check out [Issue #8](https://github.com/pCwOrM/answerr/issues/8) to implement a CSS theme toggle using `localStorage`.
3. **Agent Integration:** Connect an external LLM agent (via LangChain, LlamaIndex, or raw API) to route requests through Answerr's `/reflex` endpoint.

---

## 📖 5. Research & Documentation

* **Interactive Docs:** Open `docs.html` locally or visit [pCwOrM.github.io/answerr/docs.html](https://pCwOrM.github.io/answerr/docs.html).
* **Research Basis:** Powered by the foundational fractal synthesis research published on Zenodo ([10.5281/zenodo.22867037](https://doi.org/10.5281/zenodo.22867037)).
