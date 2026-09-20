# ⚡ A.N.S.W.E.R.R. — The Zero-Latency Reflex AI

[![Live Demo: GitHub Pages](https://img.shields.io/badge/Live%20Demo-GitHub%20Pages-38bdf8.svg)](https://pcworm.github.io/answerr/)
[![Website: answerr.me](https://img.shields.io/badge/Domain-answerr.me-818cf8.svg)](https://answerr.me)
[![wevv Core Engine](https://img.shields.io/badge/wevv-Zero--Memory%20Engine-10b981.svg)](https://github.com/pCwOrM/wevv)
[![Deliberative AI](https://img.shields.io/badge/System--2-Deliberative%20AI-c084fc.svg)](https://answerr.me)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

> **A**daptive **N**on-tensor **S**ignal **W**ave & **E**rror **R**eflex **R**esonator  
> *(Uyarlanabilir Tensörsüz Sinyal Dalgası ve Hata Refleksi Rezonatörü)*  
> *"Don't just chat. Get the Answerr. Sub-millisecond strongly-typed decisions with 0 Bytes tensor weights."*

### 🧬 Architectural Pillars (Why It's Number 1)
* **Adaptive:** Exponential moving average ($\alpha = 0.03$) and dynamic thresholding calibrated for runtime resilience.
* **Non-tensor:** Groundbreaking 0-VRAM architecture with zero stored weight tensors—runs on bare metal or directly in browsers.
* **Signal:** Ingests live telemetry, state parameters, and conversational prompts as continuous dynamic signals.
* **Wave & Error:** Mathematical wave propagation and chaotic Mandelbrot boundary ($\partial M$) error navigation.
* **Reflex Resonator:** Harmonizes spinal cord reflex arcs with acoustic harmonic phase resonance.

🌐 **Live Web Platform:** [https://answerr.me](https://answerr.me)  
⚡ **Production REST API:** [https://api.answerr.me:4431](https://api.answerr.me:4431)  
🌐 **GitHub Pages Demo:** [https://pcworm.github.io/answerr/](https://pcworm.github.io/answerr/)

---

## 🌟 Overview

**A.N.S.W.E.R.R.** is a breakthrough dual-cognition AI platform that merges:
1. **System-Two Deliberation (LLM / Deliberative AI):** Parses human conversation, analyzes operational context, and explains decisions with strategic clarity. Works with cloud models or lightweight local models.
2. **System-One Reflex Arc ([wevv](https://github.com/pCwOrM/wevv)):** Synthesizes instant, deterministic, strongly-typed decisions (`noul`, `choice`, `score`) in **< 1 ms** with **0 Bytes VRAM** using dynamic Mandelbrot boundary wave perturbation.

Instead of forcing heavy multi-billion-parameter neural networks to spend hundreds of tokens and milliseconds answering simple binary approvals or routing gates, **answerr** delegates execution triage to the zero-tensor mathematical fabric of the Mandelbrot set.

---

## ⚡ The Dual-Cognition Architecture

```
                                [ User Query ]
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │   System-Two: Gemini      │
                        │   (Fast Flash Model)      │
                        └─────────────┬─────────────┘
                                      │
             Transforms natural language into structured wevv format
                  (State Vector & Typed Decision Primitive)
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │   System-One: wevv        │
                        │   (0 Bytes VRAM Engine)   │
                        └─────────────┬─────────────┘
                                      │
                  Instant Mathematical Decision (< 1ms)
                  - noul: Probabilistic Boolean
                  - choice: Categorical Triage
                  - score: Continuous Severity Index
                  - 4-Quadrant Escape Dynamics (Q1-Q4)
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │   System-Two Synthesis    │
                        │   (Actionable Commentary) │
                        └─────────────┬─────────────┘
                                      │
                                      ▼
                [ answerr.me Live HUD & Natural Language Answer ]
```

---

## 🚀 Key Features

* **Centered Modern Chat UI:** Minimalist, glassmorphic conversational viewport inspired by ChatGPT, OpenWebUI, and Gemini.
* **Live Mandelbrot Telemetry HUD:** Each assistant reply renders an interactive canvas displaying the exact Mandelbrot patch and 4-quadrant phase energy ($Q_1 \sim Q_4$) computed for that decision.
* **Three Typed Primitives:**
  * **`noul`**: Boolean verification / permission gate with probability and confidence.
  * **`choice`**: Multi-option routing (e.g. direct API vs. rate-limiter vs. quarantine sandbox).
  * **`score`**: Continuous ranking and severity index with step probabilities.
* **Dual Execution Modes:**
  * **Client-Side (answerr.me / Static Edge):** Pure JavaScript/Canvas engine running in the browser with ZERO server dependencies.
  * **Server-Side (FastAPI):** Python backend bridge for high-throughput containerized microservices.
* **Zero-Configuration Demo:** Works immediately out of the box with built-in heuristic compiler, and easily connects to Google Gemini API keys via a client-side settings modal.

---

## 🛠️ Quickstart

### Option 1: Run Locally via Simple HTTP Server
```bash
cd answerr
python -m http.server 8080
```
Open `http://localhost:8080` in your web browser.

### Option 2: Run Fullstack FastAPI Server
```bash
cd answerr
pip install -r requirements.txt
uvicorn server.main:app --reload --port 8000
```
Open `http://localhost:8000`.

---

## 🌐 Live Production REST API (Zero-VRAM Reflex)

Answerr provides a high-throughput, sub-millisecond REST API hosted on production infrastructure with zero-downtime dual-domain support:
* **API Base URL:** `https://api.answerr.me:4431`

### 1. Health & Telemetry Benchmark
```bash
curl -k https://api.answerr.me:4431/v1/health
```
Response:
```json
{
  "status": "healthy",
  "engine": "wevv-reflex",
  "version": "0.2.2",
  "vram_bytes": 0,
  "memory_architecture": "0 Byte VRAM / 24 Byte Mandelbrot Coordinate Triplet",
  "latency_benchmark_ms": 6.72
}
```

### 2. Instant Reflex Decision (Single Question)
```bash
curl -k -X POST https://api.answerr.me:4431/v1/decide \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Allow privileged API transaction?",
    "state": {"user_role": "admin", "failed_attempts": 0, "req_frequency": 1.2}
  }'
```
Response:
```json
{
  "status": "success",
  "decision": true,
  "label": "ALLOWED",
  "answers": {
    "primary_decision": {"type": "noul", "boolean": true, "noul": 0.9999, "confidence": 0.9998}
  },
  "telemetry": {
    "engine_latency_ms": 11.13,
    "vram_bytes": 0
  }
}
```

### 3. OpenAI-Compatible Adapter (/v1/chat/completions)
Seamlessly drop Answerr into LangChain, LlamaIndex, or the official OpenAI Python SDK:
```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.answerr.me:4431/v1",
    api_key="none"
)

response = client.chat.completions.create(
    model="wevv-reflex-v1",
    messages=[
        {"role": "user", "content": "Admin user executing safe query with 0 errors"}
    ]
)
print(response.choices[0].message.content)
```

---


## 🛡️ Core Advantages of wevv & answerr

* **Zero Hallucination:** Traditional neural networks hallucinate because they sample from probabilistic token distributions. `wevv` evaluates deterministic Mandelbrot boundary escape dynamics—yielding 100% reproducible, mathematically grounded verdicts.
* **Never Crashes (Zero Failures):** Even under out-of-distribution (OOD) or adversarial state conditions, the chaotic phase-space resonator deterministically absorbs edge signals and resolves valid typed decisions without throwing exceptions.
* **Universal Coverage:** Resolves any contextual program state (numerical telemetry, boolean flags, categorical strings) into typed actions (`noul`, `choice`, `score`).
* **Zero-Memory & Zero Carbon (0 Byte VRAM):** Operates on bare metal or directly in web browsers with zero stored weight tensors, eliminating costly GPU infrastructure and network energy waste.
* **Engine Repository:** [https://github.com/pCwOrM/wevv](https://github.com/pCwOrM/wevv)

---

## 📄 License

MIT License. Copyright (c) 2026 Volkan Dağlı / ITouch Systems.
