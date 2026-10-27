<div align="center">

# ANSWERR
### Zero-Latency Reflex AI & Dual-Cognition Decision Workspace

[![License: BSL 1.1](https://img.shields.io/badge/License-BSL_1.1-0ea5e9.svg)](LICENSE)
[![Production: answerr.me](https://img.shields.io/badge/Production-answerr.me-38bdf8.svg)](https://answerr.me)
[![Engine: WERR](https://img.shields.io/badge/Engine-WERR_Reflex-10b981.svg)](https://github.com/pCwOrM/werr)
[![Oracle: Werracle](https://img.shields.io/badge/Oracle-Werracle_On--Chain-f59e0b.svg)](https://github.com/pCwOrM/werracle)
[![FastAPI Runtime](https://img.shields.io/badge/API-FastAPI_0.110+-6366f1.svg)](api/)
[![WebMCP Benchmark](https://img.shields.io/badge/WebMCP-100%25_Accuracy-emerald.svg)](tests/)

<p align="center">
  <b>A unified dual-cognition decision framework that translates high-level natural language intent (System-2) into zero-memory, deterministic WERR procedural reflexes (System-1)—delivering sub-microsecond execution latency and zero runtime hallucination.</b>
</p>

[Quickstart](#-quickstart--local-api) •
[Dual-Cognition Architecture](#-dual-cognition-architecture) •
[API Reference](#-api-endpoints--usage) •
[WebMCP & Benchmarks](#-empirical-benchmarks--webmcp) •
[Enterprise Portal](#-enterprise-workspace--pro) •
[Ecosystem](#-the-werr-ecosystem) •
[Research Chronology](RESEARCH_CHRONOLOGY.md) •
[Türkçe Dokümantasyon](README_TR.md)

</div>

---

## 🏛️ The Paradigm

Modern autonomous agents and enterprise automation workflows are constrained by a critical failure mode: **probabilistic non-determinism in critical execution paths**. Passing complex operations directly to large generative models introduces unpredictable latency ($500\,\text{ms} - 3\,\text{s}$), high token costs, and catastrophic edge-case hallucinations.

**answerr** resolves this bottleneck through a **Dual-Cognition Cognitive Pipeline**:
1. **System-2 (Deliberative Compiler):** High-level intent, security policies, and natural language instructions are processed to formulate bounded coordinate invariants.
2. **System-1 (Deterministic WERR Reflex):** Runtime execution, API gating, and state transitions are dispatched through the **WERR** zero-memory fractal engine in $\le 0.3\,\mu\text{s}$ with zero neural weights and zero VRAM footprint.

```
                      User Prompt / Enterprise Policy
                                     │
                                     ▼
                    ┌─────────────────────────────────┐
                    │      System-2 Deliberation      │
                    │   Natural Language Compiler     │
                    └────────────────┬────────────────┘
                                     │ Deterministic Seed Projection
                                     ▼
                    ┌─────────────────────────────────┐
                    │       System-1 WERR Reflex      │
                    │   Zero-Memory Escape Invariant  │  ◄── < 0.3 μs Execution
                    └────────────────┬────────────────┘
                                     │
                 ┌───────────────────┼───────────────────┐
                 ▼                   ▼                   ▼
           [ALLOW / DENY]     [Route Index]       [Risk Metric]
             noul(q, c)       choice(q, opts)      score(m, v)
```

---

## ⚡ Quickstart & Local API

The answerr API server can be executed locally or deployed via Docker container.

### Local Python Setup

```bash
git clone https://github.com/pCwOrM/answerr.git
cd answerr
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8000
```

### Fast Reflex Decision Call

```python
import requests

# Dispatch a sub-microsecond System-1 reflex gate
response = requests.post(
    "https://api.answerr.me/v1/systemone/gate",
    json={
        "question": "Allow automated withdrawal of 500 USDC?",
        "context": "Daily velocity: 500/10000 limit, whitelisted receiver 0x48f..."
    }
)

decision = response.json()
print("Reflex Gate Decision:", decision)
# Output: {"allowed": true, "latency_us": 0.28, "engine": "werr-v0.5.1"}
```

---

## 📐 API Endpoints & Usage

answerr exposes a high-throughput, OpenAPI-compliant REST API:

| Endpoint | Method | Cognition Tier | Functionality |
|---|---|---|---|
| `/v1/systemone/gate` | `POST` | System-1 (WERR) | Ultra-fast binary boolean reflex (`noul`) |
| `/v1/systemone/choice` | `POST` | System-1 (WERR) | Deterministic categorical option router (`choice`) |
| `/v1/systemone/score` | `POST` | System-1 (WERR) | Continuous normalized severity/risk score (`score`) |
| `/v1/policies/compile` | `POST` | System-2 $\rightarrow$ System-1 | Compiles natural language rules into immutable reflex seeds |
| `/v1/audit/verify` | `POST` | Deterministic Audit | Verifies execution hash against Lean 4 topological boundary |

Interactive Swagger documentation is available at `https://api.answerr.me/docs`.

---

## 📊 Empirical Benchmarks & WebMCP

answerr has been benchmarked extensively under rigorous automated environments:

* **WebMCP Evaluation:** Attained **100% zero-defect decision accuracy** across 42 automated browser test scenarios (`windtunnel_webmcp_evaluation.py`).
* **Throughput Capacity:** Benchmarked at **> 3,200,000 evaluations/sec** per CPU core without memory allocations.
* **Latency Profile:** $p_{50} = 0.28\,\mu\text{s}$, $p_{99} = 0.35\,\mu\text{s}$, effectively eliminating AI inference overhead from critical microservice call paths.

Full empirical logs, stress-test transcripts, and ablations are preserved in [RESEARCH_CHRONOLOGY.md](RESEARCH_CHRONOLOGY.md).

---

## 🌐 Enterprise Workspace & Pro Portal

answerr delivers both a free public interface and an enterprise governance tier:

* **Public Portal:** [https://answerr.me](https://answerr.me) — Interactive decision sandbox and model exploration.
* **Enterprise Console:** [https://answerr.me/pro/](https://answerr.me/pro/) — Policy compiler, role-based access gates, and real-time audit ledger.
* **WerrSoma Visualizer:** [https://werrsoma.answerr.me](https://werrsoma.answerr.me) — High-dimensional connectome and decision topology visualizer.

---

## 🌐 The WERR Ecosystem

answerr integrates seamlessly into the tri-fold WERR architectural stack:

```
                          ┌─────────────────────────────┐
                          │            WERR             │
                          │   Core Mathematical Engine  │
                          │  Zero-Memory System-1 Reflex │
                          └──────────────┬──────────────┘
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
  ┌─────────────────────────────┐                 ┌─────────────────────────────┐
  │          Werracle           │                 │           answerr           │
  │   On-Chain Decision Oracle  │                 │  Dual-Cognition Workspace   │
  │  DeFi Risk Radar & DaaS     │                 │ Natural Language Gating API │
  │   https://radar.werracle.com│                 │     https://answerr.me      │
  └─────────────────────────────┘                 └─────────────────────────────┘
```

* **[`werr`](https://github.com/pCwOrM/werr):** The core procedural fractal engine and Lean 4 certified formal proofs.
* **[`werracle`](https://github.com/pCwOrM/werracle):** On-chain EVM oracle, Q16.16 escape math, and Uniswap v4 fee hooks.
* **`answerr`:** Dual-cognition workspace, natural language policy compiler, and cloud REST endpoints.

---

## 📄 Academic Citation & Archival References

If you cite or replicate this research in scientific publications, please use the following metadata:

```bibtex
@software{dagli2026answerr,
  author       = {Dağlı, Volkan and Dağlı, Zerrin and Dağlı, Dağhan},
  title        = {{answerr: Zero-Latency Reflex AI and Dual-Cognition Decision Workspace}},
  month        = oct,
  year         = 2026,
  publisher    = {Zenodo},
  version      = {v1.1.0},
  doi          = {10.5281/zenodo.22939253},
  url          = {https://github.com/pCwOrM/answerr}
}
```

* **Associated Preprint:** arXiv:2609.25498 `[cs.AI / math.DS]` ([https://arxiv.org/abs/2609.25498](https://arxiv.org/abs/2609.25498))
* **Full Research Chronology:** [`RESEARCH_CHRONOLOGY.md`](RESEARCH_CHRONOLOGY.md)

---

## ⚖️ License & Intellectual Property

* **Open-Science, Educational & Evaluation Use:** The Licensed Work is free to run, inspect, benchmark, test, fork, and replicate for all non-commercial academic research, personal evaluations, and testing under the **Business Source License 1.1 (BSL 1.1)**.
* **Commercial Operations & Production Licensing:** Any commercial production use, hosted SaaS deployment, or commercial integration requires a written Commercial License from the Licensor:
  * **Licensor:** `ITOUCH BİLİŞİM SİSTEMLERİ MÜHENDİSLİK DANIŞMANLIK SANAYİ VE TİCARET LİMİTED ŞİRKETİ` (`ITouch Systems` · Cukurova University Science Park, Adana, Türkiye).
  * **Scientific Co-Authors & Inventors:** Volkan Dağlı (*Anadolu University*), Dr. Zerrin Dağlı (*Mersin University — Academic Advisor, Co-Author & Co-Inventor*), Dağhan Dağlı (*Toros University — Co-Author & Co-Inventor*).
  * **Chain of Title & Assignment:** The scientific co-authors have irrevocably assigned administrative and IP management authority to Volkan Dağlı, who has transferred exclusive global commercial licensing and operational rights to ITouch Systems.
  * **Trademarks:** `WERR™`, `Werracle™`, `answerr™`, and `WerrSoma™` are trademarks owned exclusively by ITouch Systems.
  * **Patent Applications:** TÜRKPATENT **TR 2026/016285** & **TR 2026/016633**.
  * **Inquiries:** `ask@answerr.me` · `info@itouch.com.tr`

---

<div align="center">
  <sub>Developed by ITouch Systems · Cukurova University Science Park, Adana, Turkey</sub><br>
  <sub>Copyright &copy; 2026 ITouch Bilişim Sistemleri Ltd. Şti. All rights reserved.</sub>
</div>
