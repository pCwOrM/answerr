# 🤝 Contributing to answerr

Thank you for your interest in contributing to **answerr** — The Zero-Latency Reflex AI & Decision Platform!

We welcome contributions of all kinds: bug fixes, documentation improvements, new reflex templates, and performance optimizations.

---

## 🚀 Getting Started

1. **Fork the Repository:** Create a fork of [pCwOrM/answerr](https://github.com/pCwOrM/answerr).
2. **Clone your fork:**
   ```bash
   git clone https://github.com/<your-username>/answerr.git
   cd answerr
   ```
3. **Set up Python Environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

---

## 🛠️ Development & Testing

- **Testing the API Client:**
  ```bash
  python test_api.py
  ```
- **Running the Local REST Server:**
  ```bash
  uvicorn api_server:app --host 0.0.0.0 --port 4431 --reload
  ```
- **Local Web Interface:**
  Open `index.html` or `chat.html` directly in any modern browser. No build steps or bundlers are required.

---

## 📜 Pull Request Guidelines

1. **Create a Feature Branch:**
   ```bash
   git checkout -b feat/your-feature-name
   ```
2. **Commit with Clear Messages:**
   Use conventional commit prefixes: `feat:`, `fix:`, `docs:`, `perf:`, `refactor:`.
3. **Verify Integrity:**
   - Ensure Python files compile without syntax errors: `python -m py_compile api_server.py`.
   - Never commit sensitive API keys, tokens, or personal secrets.
4. **Submit your Pull Request:**
   Fill in the provided Pull Request template and link relevant issues.

---

## 💬 Community & Discussions

Have questions, suggestions, or want to showcase what you built with answerr?  
Join our [GitHub Discussions](https://github.com/pCwOrM/answerr/discussions)!
