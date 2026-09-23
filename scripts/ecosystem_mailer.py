#!/usr/bin/env python3
"""
ITouch Systems Unified Ecosystem Announcement & Outreach Mailer
Transmits curated project announcements and grant inquiries from
ask@answerr.me / noreply@answerr.me through mail.answerr.me (SSL 465).
"""

import sys
import os
import json
import ssl
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

MAIL_CONFIG_PATH = os.path.expanduser("~/.answerr/mail.json")

def load_mail_credentials():
    smtp_server = os.environ.get("SMTP_SERVER", "mail.answerr.me")
    smtp_port = int(os.environ.get("SMTP_PORT", 465))
    auth_user = os.environ.get("SMTP_USER", "ask@answerr.me")
    auth_pass = os.environ.get("SMTP_PASS", "")

    if os.path.exists(MAIL_CONFIG_PATH):
        try:
            with open(MAIL_CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                smtp_server = cfg.get("smtp_server", smtp_server)
                smtp_port = int(cfg.get("smtp_port", smtp_port))
                auth_user = cfg.get("email", auth_user)
                auth_pass = cfg.get("password", auth_pass)
        except Exception as e:
            print(f"Warning: could not load config from {MAIL_CONFIG_PATH}: {e}")

    return smtp_server, smtp_port, auth_user, auth_pass

SMTP_SERVER, SMTP_PORT, AUTH_USER, AUTH_PASS = load_mail_credentials()

DEFAULT_SENDER = "ITouch Systems AI <ask@answerr.me>"
NOREPLY_SENDER = "ITouch Systems Announcements <noreply@answerr.me>"
REPLY_TO = "ask@answerr.me, pcworm@pcworm.net"

CHANNELS = {
    # Test Channels
    "self_test": {
        "repo": "all",
        "category": "Self-Test",
        "name": "Owner Self-Test & Diagnostic",
        "to": ["pcworm@pcworm.net", "ask@answerr.me"],
        "sender": DEFAULT_SENDER,
        "subject": "✅ [Diagnostic] ITouch Systems Multi-Repo Ecosystem Mailer Active",
        "template": "self_test"
    },

    # Web3 / Blockchain Media & Editorial (for Werracle)
    "week_in_ethereum": {
        "repo": "werracle",
        "category": "Web3 Media",
        "name": "Week in Ethereum News",
        "to": ["editor@weekinethereumnews.com", "contact@weekinethereumnews.com"],
        "sender": DEFAULT_SENDER,
        "subject": "Project Submission: Werracle - Machine-Native On-Chain AI Decision Oracle (~21k gas)",
        "template": "werracle_editorial"
    },
    "solidity_weekly": {
        "repo": "werracle",
        "category": "Web3 Media",
        "name": "Solidity Weekly Newsletter",
        "to": ["solidityweekly@gmail.com"],
        "sender": DEFAULT_SENDER,
        "subject": "Solidity Showcase: Werracle & Volatility-Adaptive Uniswap v4 Hook",
        "template": "werracle_editorial"
    },
    "dlnews": {
        "repo": "werracle",
        "category": "Web3 Media",
        "name": "DL News / DefiLlama Editorial",
        "to": ["news@dlnews.com"],
        "sender": DEFAULT_SENDER,
        "subject": "DeFi Security: Werracle - Sub-Millisecond Intra-Block AI Decision Oracle",
        "template": "werracle_editorial"
    },
    "bankless": {
        "repo": "werracle",
        "category": "Web3 Media",
        "name": "Bankless Editorial Team",
        "to": ["editorial@banklesshq.com"],
        "sender": DEFAULT_SENDER,
        "subject": "Web3 Innovation: Zero-Storage On-Chain AI Oracle for Intra-Block Defense",
        "template": "werracle_editorial"
    },
    "coindesk_tips": {
        "repo": "werracle",
        "category": "Web3 Media",
        "name": "CoinDesk Newsdesk",
        "to": ["tips@coindesk.com"],
        "sender": NOREPLY_SENDER,
        "subject": "Tech Release: Zero-Storage Procedural AI Oracle on EVM (Werracle)",
        "template": "werracle_editorial"
    },
    "cointelegraph": {
        "repo": "werracle",
        "category": "Web3 Media",
        "name": "Cointelegraph Editorial",
        "to": ["editor@cointelegraph.com"],
        "sender": NOREPLY_SENDER,
        "subject": "Open-Source AI Oracle: Werracle Brings Intra-Block Decisioning to EVM",
        "template": "werracle_editorial"
    },
    "decrypt": {
        "repo": "werracle",
        "category": "Web3 Media",
        "name": "Decrypt Media",
        "to": ["tips@decrypt.co"],
        "sender": NOREPLY_SENDER,
        "subject": "Web3 AI: Werracle Replaces ZK-ML Latency with 21k Gas Bytecode Decisions",
        "template": "werracle_editorial"
    },

    # Web3 Foundation Grant Desks (for Werracle)
    "ethereum_esp": {
        "repo": "werracle",
        "category": "Grants",
        "name": "Ethereum Foundation Ecosystem Support Program",
        "to": ["esp@ethereum.org"],
        "sender": DEFAULT_SENDER,
        "subject": "Grant Inquiry: Werracle - Machine-Native On-Chain AI Decisions (Public Good / Open Source)",
        "template": "werracle_grant"
    },
    "uniswap_grants": {
        "repo": "werracle",
        "category": "Grants",
        "name": "Uniswap Foundation Grants Desk",
        "to": ["grants@uniswapfoundation.org"],
        "sender": DEFAULT_SENDER,
        "subject": "Grant Inquiry: WerracleFeeHook - Dynamic Chaos-Adaptive AMM Fee Governor for Uniswap v4",
        "template": "werracle_grant"
    },
    "arbitrum_grants": {
        "repo": "werracle",
        "category": "Grants",
        "name": "Arbitrum Foundation Grants",
        "to": ["grants@arbitrum.foundation"],
        "sender": DEFAULT_SENDER,
        "subject": "Grant Inquiry: Werracle - Stylus & EVM Machine-Native Decision Engine for Arbitrum One",
        "template": "werracle_grant"
    },
    "base_ecosystem": {
        "repo": "werracle",
        "category": "Grants",
        "name": "Base Ecosystem Fund",
        "to": ["build@base.org"],
        "sender": DEFAULT_SENDER,
        "subject": "Builder Grant: Werracle - Sub-Cent Native AI Decisions & MEV Shielding on Base",
        "template": "werracle_grant"
    },

    # AI & Edge Computing Editorial (for WERR & answerr)
    "tldr_ai": {
        "repo": "werr",
        "category": "AI Newsletters",
        "name": "TLDR AI Editorial (Dan)",
        "to": ["dan@tldr.tech"],
        "sender": DEFAULT_SENDER,
        "subject": "Project Submission: WERR - Zero-VRAM Machine-Native Reflex AI (27x faster than Gemma)",
        "template": "werr_editorial"
    },
    "the_rundown_ai": {
        "repo": "answerr",
        "category": "AI Newsletters",
        "name": "The Rundown AI (Rowan)",
        "to": ["rowan@therundown.ai"],
        "sender": DEFAULT_SENDER,
        "subject": "AI Launch: Answerr – Dual-Cognition AI Workspace (Sub-Millisecond System-1 Reflex)",
        "template": "answerr_editorial"
    },
    "bens_bites": {
        "repo": "answerr",
        "category": "AI Newsletters",
        "name": "Ben's Bites Newsletter",
        "to": ["ben@bensbites.co"],
        "sender": DEFAULT_SENDER,
        "subject": "Product Drop: Answerr - 0-Byte VRAM AI Reflex Workspace",
        "template": "answerr_editorial"
    },
    "alphasignal": {
        "repo": "mandelbrot",
        "category": "AI Newsletters",
        "name": "AlphaSignal AI Digest",
        "to": ["contact@alphasignal.ai"],
        "sender": DEFAULT_SENDER,
        "subject": "Research Feature: Orbital Error Dynamics & Fractal Neural Synthesis",
        "template": "mandelbrot_editorial"
    },
    "venturebeat_ai": {
        "repo": "werr",
        "category": "Tech Media",
        "name": "VentureBeat AI Desk",
        "to": ["ai-tips@venturebeat.com"],
        "sender": NOREPLY_SENDER,
        "subject": "Tech Breakthrough: Zero-Storage Procedural AI Replaces Tensor Weights at the Edge",
        "template": "werr_editorial"
    }
}

TEMPLATES = {
    "self_test": """Hello Owner & Diagnostic Desk,

This is an automated verification of the ITouch Systems multi-repo ecosystem dispatch infrastructure.

Active System Repositories:
1. Mandelbrot Fractal Neural Synthesis (Core Research): https://github.com/pCwOrM/mandelbrot-fractal-neural-synthesis
2. WERR (Zero-VRAM Edge Engine): https://github.com/pCwOrM/werr
3. Answerr (Dual-Cognition Platform & REST API): https://github.com/pCwOrM/answerr (https://answerr.me)
4. Werracle (On-Chain AI Decision Oracle): https://github.com/pCwOrM/werracle

All repositories are standardized under the Business Source License 1.1 (BSL 1.1) and backed by pending patent application TÜRKPATENT TR 2026/016285.

Dispatcher: ask@answerr.me
Server: mail.answerr.me:465 (SSL)
Status: Operational & Ready
""",

    "werracle_editorial": """Hello {recipient_name},

We are pleased to introduce Werracle, an open-source On-Chain AI Decision Oracle and Uniswap v4 dynamic fee governor operating inside a single 32-byte EVM storage slot.

Key Innovations:
• Zero Storage Overhead: Instead of multi-gigabyte neural weight matrices, decision boundaries are derived procedurally from a 24-byte coordinate triplet.
• Sub-Millisecond Execution: Fixed-point Q16.16 Pareto escape bytecode evaluates decisions in ~21,438 gas (< $0.001 on Base/Arbitrum), 1,000x faster than off-chain ZK-ML provers.
• Uniswap v4 Dynamic Fee Hook (WerracleFeeHook.sol): Adjusts swap fees dynamically between 0.05% and 0.50% based on real-time orderbook chaos.
• Cryptographically Sealed: Passed a 1,000-scenario deterministic verification suite with 100% parity.

Repository: https://github.com/pCwOrM/werracle
Interactive Simulator: https://pcworm.github.io/werracle/
Live API Status: https://api.answerr.me:4431/werracle/status

Developed by ITouch Systems (ITouch Bilişim Sistemleri Ltd. Şti., Çukurova Teknokent).
Contact: ask@answerr.me / info@itouch.com.tr
""",

    "werracle_grant": """Dear {recipient_name},

We are submitting a project inquiry for open-source public good support for Werracle (On-Chain AI Decision Oracle).

Problem Solved:
Current ZK-ML approaches incur 10–300s prover latency and 250k–500k gas verification overhead, making them incapable of intra-block flash-loan defense or real-time AMM fee adjustments. Werracle evaluates non-linear decision boundaries natively in EVM bytecode (~21k gas) within the same block.

Deliverables & Code:
• Contract Repository: https://github.com/pCwOrM/werracle
• Uniswap v4 Hook: https://github.com/pCwOrM/werracle/blob/main/contracts/hooks/WerracleFeeHook.sol
• Grant Proposal Dossier: https://github.com/pCwOrM/werracle/blob/main/docs/GRANT_PROPOSAL.md
• One-Pager: https://github.com/pCwOrM/werracle/blob/main/docs/ONE_PAGER.md

We would welcome the opportunity to discuss formal grant alignment.

Sincerely,
ITouch Systems (Çukurova Teknokent) & Autonomous AI Co-Developer
Email: ask@answerr.me | Corporate: info@itouch.com.tr
""",

    "werr_editorial": """Hello {recipient_name},

We are sharing WERR (Waves & Errors), an open-source, patented Zero-VRAM reflex decision engine designed for edge computing and low-latency robotics.

Empirical Benchmarks:
• Visual Tracking: Evaluated on the jevenator2 benchmark against Maisa's Diffusion-Gemma. WERR runs 27.8× faster (27.39 ms vs 761.8 ms) with 0 Bytes GPU VRAM and 0 false positives.
• Text Triage: On Apple M3 Max ($3,500) MLX benchmark (laya-mlx), WERR delivers 273–302 moves/sec (sub-2ms), outperforming MLX by 3.7× and cloud APIs by 78×.

Repository: https://github.com/pCwOrM/werr
Interactive Browser Demo: https://answerr.me
Research Preprint: https://doi.org/10.5281/zenodo.22867426

Best regards,
ITouch Systems Research Team (ask@answerr.me)
""",

    "answerr_editorial": """Hello {recipient_name},

We are pleased to introduce answerr (https://answerr.me), a dual-cognition AI platform that couples rapid System-1 procedural reflex triage with deep deliberative language reasoning.

Highlights:
• Dual-Process Architecture: Handles initial prompt triage and safety classification in <1ms without loading multi-gigabyte models into GPU VRAM.
• Production REST API: Hosted at https://api.answerr.me:4431 with instant health and telemetry endpoints.
• Open Science & Transparency: Full code open under BSL 1.1 at https://github.com/pCwOrM/answerr.

Try the live workspace: https://answerr.me
API Documentation: https://answerr.me/docs

Best regards,
ITouch Systems & Autonomous AI Agent (ask@answerr.me)
""",

    "mandelbrot_editorial": """Hello {recipient_name},

We are announcing Paper 2 in the Fractal Neural Synthesis series: "Orbital Error Dynamics: Self-Organized Criticality, Ephemeral Parameter Resonance, and Non-Linear Biological Ontologies in Zero-Storage Neural Synthesis".

This research proves that iterative polynomial escape dynamics on the boundary of the Mandelbrot set $\\mathbb{M}$ can replace static weight matrices in neural classification.

Zenodo Record: https://doi.org/10.5281/zenodo.22896856
Interactive 100% Client-Side Labs: https://pcworm.github.io/mandelbrot-fractal-neural-synthesis/
GitHub Repository: https://github.com/pCwOrM/mandelbrot-fractal-neural-synthesis

Best regards,
ITouch Systems Research Group (ask@answerr.me)
"""
}

def send_mail(channel_key, override_recipient=None):
    if channel_key not in CHANNELS:
        print(f"Error: channel '{channel_key}' not found.")
        return False

    ch = CHANNELS[channel_key]
    template_key = ch.get("template", "self_test")
    template_text = TEMPLATES.get(template_key, "")

    recipients = [override_recipient] if override_recipient else ch["to"]
    recipient_name = ch["name"]
    sender = ch.get("sender", DEFAULT_SENDER)
    subject = ch["subject"]
    body = template_text.format(recipient_name=recipient_name)

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg["Reply-To"] = REPLY_TO
    msg.attach(MIMEText(body, "plain", "utf-8"))

    print(f"Connecting to {SMTP_SERVER}:{SMTP_PORT} via SSL for '{channel_key}'...")
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context, timeout=20) as server:
            server.login(AUTH_USER, AUTH_PASS)
            server.sendmail(AUTH_USER, recipients, msg.as_string())
        print(f"SUCCESS: Email delivered to {recipients} ({recipient_name})")
        return True
    except Exception as e:
        print(f"ERROR delivering to {recipients}: {e}")
        return False

def list_channels():
    print("=" * 80)
    print("ITouch Systems Ecosystem Dispatch Channels Registry (mail.answerr.me)")
    print("=" * 80)
    categories = {}
    for k, v in CHANNELS.items():
        cat = v.get("category", "General")
        categories.setdefault(cat, []).append((k, v))

    for cat, items in categories.items():
        print(f"\n📂 [{cat}]")
        for k, v in items:
            recip = ", ".join(v['to'])
            print(f"  • {k:18} | Repo: {v.get('repo','all'):10} | {v['name']} ({recip})")
    print("=" * 80)

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("Usage:")
        print("  python ecosystem_mailer.py list")
        print("  python ecosystem_mailer.py test [channel_key]    # sends template to pcworm@pcworm.net")
        print("  python ecosystem_mailer.py send [channel_key]    # sends live to target recipient")
        print("  python ecosystem_mailer.py send_category [cat]   # sends to all in category")
        sys.exit(0)

    cmd = sys.argv[1].lower()

    if cmd == "list":
        list_channels()
    elif cmd == "test":
        target = sys.argv[2] if len(sys.argv) > 2 else "self_test"
        print(f"Executing DRY-RUN / TEST for channel '{target}' routed to 'pcworm@pcworm.net'...")
        send_mail(target, override_recipient="pcworm@pcworm.net")
    elif cmd == "send":
        if len(sys.argv) < 3:
            print("Specify channel_key to send. Run 'list' to see available channels.")
            sys.exit(1)
        target = sys.argv[2]
        send_mail(target)
    elif cmd == "send_category":
        if len(sys.argv) < 3:
            print("Specify category name.")
            sys.exit(1)
        cat_query = sys.argv[2].lower()
        matched = [k for k, v in CHANNELS.items() if cat_query in v.get("category", "").lower()]
        print(f"Dispatching to {len(matched)} channels in category '{cat_query}'...")
        for k in matched:
            send_mail(k)
    else:
        print(f"Unknown command: {cmd}")
