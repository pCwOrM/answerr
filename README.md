# 🔮 answerr: Dual-Cognition AI Decision Chatbot

[![Website: answerr.me](https://img.shields.io/badge/Live-answerr.me-38bdf8.svg)](https://answerr.me)
[![wevv Core Engine](https://img.shields.io/badge/wevv-Zero--Memory%20Engine-10b981.svg)](https://github.com/pCwOrM/wevv)
[![Gemini 2.5 Flash](https://img.shields.io/badge/System--2-Gemini%20Flash-818cf8.svg)](https://deepmind.google/technologies/gemini/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

> **Where Gemini Reasons and wevv Decides in Zero-Memory Fractal Geometry.**  
> *"Translating unstructured natural language triage into sub-millisecond, strongly-typed decisions with 0 Bytes tensor weights."*

🌐 **Live Web Application:** [answerr.me](https://answerr.me)

---

## 🌟 Overview

**answerr** is a next-generation conversational AI platform establishing the cognitive bridge between:
1. **System-Two Deliberation (Google Gemini Flash):** Parses complex human language, extracts structured operational state, and translates outcomes into strategic commentary and actionable advice.
2. **System-One Reflex Arc ([wevv](https://github.com/pCwOrM/wevv)):** Synthesizes instant, deterministic, strongly-typed decisions (`noul`, `choice`, `score`) in **< 1 ms** with **0 Bytes VRAM** from a 24-byte Mandelbrot boundary seed triplet $(c_x, c_y, \text{zoom})$.

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

## 🧪 Scientific Foundation

* **Base Paper:** *"Universal Fractal Natural Language Decision Map: Real-Time Edge Triage Across Heterogeneous Domains"* (Dağlı et al., September 2026).
* **Companion Theory:** *"Mandelbrot Fractal Neural Synthesis: Zero-Storage Procedural Weight Derivation and Non-Linear Decision Boundaries"* (IEEE / Zenodo DOI: [10.5281/zenodo.22802921](https://doi.org/10.5281/zenodo.22802921)).
* **Engine Repository:** [https://github.com/pCwOrM/wevv](https://github.com/pCwOrM/wevv).

---

## 📄 License

MIT License. Copyright (c) 2026 Volkan Dağlı / ITouch Systems.
