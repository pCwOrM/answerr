"""Payment providers.

answerr computes *what* is owed; collecting money and issuing the legal invoice are separate:

  1. Collection — ManualProvider (bank transfer, admin approval) or IyzicoProvider (card payment through the
     iyzico Checkout Form; one payment buys one period: 31 days for monthly, 366 days for yearly).
  2. Legal invoice — e-Arşiv / e-Fatura issued by ITouch (Paraşüt). Every paid card payment e-mails the buyer's
     billing details to MAIL_NOTIFY_TO so the invoice can be cut.

Security model for iyzico: the browser callback and the merchant webhook are treated only as *hints*. A payment is
completed solely after answerr itself retrieves the checkout-form result from iyzico with its own keys and checks
status, payment status, fraud status, conversation id, basket id and amount.

Environment:
  ANSWERR_PAYMENT_PROVIDER   manual (default) | iyzico
  IYZICO_API_KEY, IYZICO_SECRET_KEY, IYZICO_MERCHANT_ID, IYZICO_BASE_URL (https://api.iyzipay.com | https://sandbox-api.iyzipay.com)
  ANSWERR_PUBLIC_API_URL     callback base (default https://api.answerr.me)
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
import urllib.error
import urllib.request
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Dict, Optional

from . import plans as P
from . import store as S

VAT_RATE = Decimal(str(P.CATALOG.get("vat_rate", 0.0)))
TIMEOUT = 15


def money(x) -> str:
    return str(Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def quote_try(plan_id: str, cycle: str) -> Dict[str, str]:
    """Net, VAT and total in TRY for one period of a plan (prices in plans.json exclude VAT)."""
    p = P.get(plan_id)
    per_month = p.get("price_yearly_per_month_try") if cycle == "yearly" else p.get("price_monthly_try")
    if not per_month:
        raise S.CommerceError(400, "no_try_price", "This plan cannot be bought by card.")
    net = Decimal(str(per_month)) * (12 if cycle == "yearly" else 1)
    vat = (net * VAT_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return {"net": money(net), "vat": money(vat), "total": money(net + vat), "vat_rate": str(VAT_RATE)}


class PaymentProvider:
    name = "base"
    card_payments = False

    def checkout(self, account: Dict[str, Any], plan: str, cycle: str) -> Dict[str, Any]:
        raise NotImplementedError


class ManualProvider(PaymentProvider):
    """Plan change becomes a request; the team confirms by e-mail with bank details, and an admin
    activates the plan after payment (POST /v1/admin/plan-requests/{id}/approve)."""
    name = "manual"

    def checkout(self, account, plan, cycle):
        return {
            "provider": self.name,
            "mode": "request",
            "bank_accounts": P.CATALOG.get("bank_accounts", {}),
            "next": "Transfer to our TEB IBAN (TRY/USD/EUR) and download your UNPAID Proforma Commercial Invoice PDF; once verified, your invoice is stamped PAID and your plan activates."
        }


class IyzicoProvider(PaymentProvider):
    name = "iyzico"

    def __init__(self):
        self.api_key = os.environ.get("IYZICO_API_KEY", "").strip()
        self.secret = os.environ.get("IYZICO_SECRET_KEY", "").strip()
        self.merchant_id = os.environ.get("IYZICO_MERCHANT_ID", "").strip()
        self.base_url = os.environ.get("IYZICO_BASE_URL", "https://sandbox-api.iyzipay.com").rstrip("/")
        self.public_api = os.environ.get("ANSWERR_PUBLIC_API_URL", "https://api.answerr.me").rstrip("/")
        self.card_payments = bool(self.api_key and self.secret)

    def checkout(self, account, plan, cycle):
        return {"provider": self.name, "mode": "card", "quote_try": quote_try(plan, cycle),
                "next": "POST /v1/account/checkout opens the iyzico payment page; bank transfer stays available on request."}

    # -- transport --------------------------------------------------------------------------------------------------
    def auth_header(self, uri_path: str, body: str, random_key: Optional[str] = None) -> Dict[str, str]:
        """IYZWSv2: base64("apiKey:..&randomKey:..&signature:" + hex(HMAC-SHA256(randomKey + uriPath + body, secret)))."""
        rnd = random_key or "{}{}".format(int(time.time() * 1000), secrets.randbelow(10 ** 9))
        sig = hmac.new(self.secret.encode(), (rnd + uri_path + body).encode("utf-8"), hashlib.sha256).hexdigest()
        token = base64.b64encode("apiKey:{}&randomKey:{}&signature:{}".format(self.api_key, rnd, sig).encode()).decode()
        return {"Authorization": "IYZWSv2 " + token, "x-iyzi-rnd": rnd}

    def post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.card_payments:
            raise S.CommerceError(503, "provider_not_configured", "Card payments are not configured.")
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        headers = {"Content-Type": "application/json", "Accept": "application/json", "User-Agent": "answerr-billing/1.0"}
        headers.update(self.auth_header(path, body))
        req = urllib.request.Request(self.base_url + path, data=body.encode("utf-8"), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            try:
                return json.loads(e.read().decode("utf-8"))
            except Exception:
                return {"status": "failure", "errorCode": str(e.code), "errorMessage": "HTTP {}".format(e.code)}
        except Exception as e:
            return {"status": "failure", "errorCode": "network", "errorMessage": type(e).__name__}

    # -- checkout form ----------------------------------------------------------------------------------------------
    def initialize(self, pay: Dict[str, Any], buyer: Dict[str, Any], item_name: str, locale: str = "tr") -> Dict[str, Any]:
        total = pay["total_try"]
        payload = {
            "locale": "en" if locale == "en" else "tr",
            "conversationId": pay["conversation_id"],
            "price": total, "paidPrice": total, "currency": "TRY",
            "basketId": pay["id"], "paymentGroup": "PRODUCT",
            "callbackUrl": self.public_api + "/v1/billing/iyzico/callback",
            "enabledInstallments": [1],
            "buyer": buyer["buyer"],
            "billingAddress": buyer["address"],
            "basketItems": [{"id": pay["plan"] or pay["kind"], "name": item_name[:100], "category1": "Yazılım",
                             "category2": "SaaS abonelik", "itemType": "VIRTUAL", "price": total}],
        }
        res = self.post("/payment/iyzipos/checkoutform/initialize/auth/ecom", payload)
        if res.get("status") != "success" or not res.get("token") or not res.get("paymentPageUrl"):
            S.fail_payment(pay["id"], "{} {}".format(res.get("errorCode"), res.get("errorMessage")))
            raise S.CommerceError(502, "payment_init_failed", "The payment page could not be opened: {}".format(
                res.get("errorMessage") or "unknown error"))
        S.set_payment_token(pay["id"], res["token"])
        return {"provider": self.name, "mode": "redirect", "payment_page_url": res["paymentPageUrl"], "payment_id": pay["id"],
                "total_try": total}

    def retrieve(self, token: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """iyzico echoes the conversationId of *this* request, so it is sent here; basketId is the real binding."""
        body = {"locale": "tr", "token": token}
        if conversation_id:
            body["conversationId"] = conversation_id
        return self.post("/payment/iyzipos/checkoutform/auth/ecom/detail", body)

    def settle(self, token: str) -> Dict[str, Any]:
        """Retrieves the result for a token and completes or fails the matching payment. Safe to call repeatedly."""
        pay = S.get_payment(token=token)
        if not pay:
            return {"result": "unknown"}
        if pay["status"] == "paid":
            return {"result": "paid", "payment": pay, "activated": False}
        if pay["status"] == "failed":
            return {"result": "failed", "payment": pay}
        res = self.retrieve(token, pay["conversation_id"])
        if res.get("status") != "success":
            return {"result": "error", "payment": pay, "error": res.get("errorMessage")}
        ps = (res.get("paymentStatus") or "").upper()
        checks = {
            "conversation": res.get("conversationId") in (None, pay["conversation_id"]),
            "basket": res.get("basketId") == pay["id"],
            "currency": (res.get("currency") or "TRY") == "TRY",
            "amount": Decimal(str(res.get("price") or 0)) == Decimal(pay["total_try"])
                      and Decimal(str(res.get("paidPrice") or 0)) >= Decimal(pay["total_try"]),
        }
        if ps != "SUCCESS":
            S.fail_payment(pay["id"], "paymentStatus={} {}".format(ps, res.get("errorMessage") or ""))
            return {"result": "failed", "payment": S.get_payment(pay["id"])}
        if not all(checks.values()):
            S.fail_payment(pay["id"], "mismatch " + ",".join(k for k, v in checks.items() if not v), status="pending_review")
            return {"result": "review", "payment": S.get_payment(pay["id"])}
        fraud = int(res.get("fraudStatus", 1))
        if fraud != 1:
            S.fail_payment(pay["id"], "fraudStatus={}".format(fraud), status="pending_review")
            return {"result": "review", "payment": S.get_payment(pay["id"])}
        out = S.complete_payment(pay["id"], res.get("paymentId"), fraud, res.get("lastFourDigits"))
        out["result"] = "paid"
        return out

    def verify_webhook_v3(self, body: Dict[str, Any], header: str) -> bool:
        """X-IYZ-SIGNATURE-V3 for checkout-form (HPP) notifications:
        hex(HMAC-SHA256(secretKey + iyziEventType + iyziPaymentId + token + paymentConversationId + status, secretKey))."""
        if not header or not self.secret:
            return False
        msg = "{}{}{}{}{}{}".format(self.secret, body.get("iyziEventType", ""), body.get("iyziPaymentId", ""),
                                    body.get("token", ""), body.get("paymentConversationId", ""), body.get("status", ""))
        mac = hmac.new(self.secret.encode(), msg.encode("utf-8"), hashlib.sha256).hexdigest()
        return hmac.compare_digest(mac, header.strip().lower())


def provider() -> PaymentProvider:
    if os.environ.get("ANSWERR_PAYMENT_PROVIDER", "manual") == "iyzico":
        p = IyzicoProvider()
        if p.card_payments:
            return p
    return ManualProvider()


def iyzico() -> IyzicoProvider:
    return IyzicoProvider()


def buyer_from_account(acc: Dict[str, Any], member_email: str, ip: str) -> Dict[str, Any]:
    """Builds the iyzico buyer and billing address from the account's billing details. Raises 400 when incomplete."""
    b = json.loads(acc.get("billing_json") or "{}")
    missing = [k for k in ("legal_name", "tax_id", "address", "city", "phone") if not (b.get(k) or "").strip()]
    if missing:
        raise S.CommerceError(400, "billing_incomplete", "Fill in your billing details first: " + ", ".join(missing),
                              missing=missing)
    name = b["legal_name"].strip()
    # iyzico's buyer is a person: the authorised contact when given, otherwise the legal name split in two
    person = (b.get("contact_name") or "").strip() or name
    parts = person.split()
    first, last = (" ".join(parts[:-1]), parts[-1]) if len(parts) > 1 else (person, person)
    digits = "".join(ch for ch in b["tax_id"] if ch.isdigit())
    identity = digits if len(digits) == 11 else "11111111111"     # VKN (10 digits) is sent in the invoice, not here
    phone = "".join(ch for ch in b["phone"] if ch.isdigit() or ch == "+")
    if not phone.startswith("+"):
        phone = "+90" + phone.lstrip("0")
    country = b.get("country") or "Türkiye"
    return {
        "buyer": {"id": acc["id"], "name": first[:60], "surname": last[:60], "identityNumber": identity,
                  "email": (b.get("invoice_email") or member_email or acc["email"])[:100], "gsmNumber": phone[:20],
                  "registrationAddress": b["address"][:200], "city": b["city"][:60], "country": country[:60],
                  "ip": ip or "127.0.0.1"},
        "address": {"contactName": name[:100], "address": b["address"][:200], "city": b["city"][:60], "country": country[:60]},
        "billing": b,
    }


# ----------------------------------------------------------------------------- multi-chain crypto & PDF invoice
EVM_DEPOSIT_ADDRESS = "0x4945ef6e124eea2176ddf050b33db42b0ae8c7f7"
TRC20_DEPOSIT_ADDRESS = "TLMhaDJTVYBHBSGJ9nCQGLvqnYFPsBgLJu"
ERC20_TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

EVM_CHAINS = {
    "base": {
        "name": "Base Mainnet",
        "rpcs": ["https://mainnet.base.org", "https://base-rpc.publicnode.com"],
        "tokens": {
            "USDC": ("0x833589fcd6edb6e08f4c7c32d4f71b54bda02913", 6),
            "USDT": ("0xfde4c96c8593536e31f229ea8f37b2ada2699bb2", 6),
        },
    },
    "ethereum": {
        "name": "Ethereum Mainnet (ERC20)",
        "rpcs": ["https://ethereum-rpc.publicnode.com", "https://rpc.ankr.com/eth"],
        "tokens": {
            "USDC": ("0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", 6),
            "USDT": ("0xdac17f958d2ee523a2206206994597c13d831ec7", 6),
        },
    },
    "arbitrum": {
        "name": "Arbitrum One",
        "rpcs": ["https://arb1.arbitrum.io/rpc", "https://arbitrum-one-rpc.publicnode.com"],
        "tokens": {
            "USDC": ("0xaf88d065e77c8cc2239327c5edb3a432268e5831", 6),
            "USDT": ("0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9", 6),
        },
    },
    "bsc": {
        "name": "BNB Smart Chain (BEP20)",
        "rpcs": ["https://bsc-dataseed.binance.org", "https://bsc-rpc.publicnode.com"],
        "tokens": {
            "USDC": ("0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d", 18),
            "USDT": ("0x55d398326f99059ff775485246999027b3197955", 18),
        },
    },
}


def crypto_cents(email: Optional[str]) -> float:
    s = (email or "").strip().lower()
    if not s:
        return 0.0
    h = 0
    for ch in s:
        h = ((h * 31) + ord(ch)) & 0xFFFFFFFF
        if h >= 0x80000000:
            h -= 0x100000000
    return round((abs(h) % 90 + 10) / 100.0, 2)


def quote_usd(plan_id: str, cycle: str, email: Optional[str] = None) -> Dict[str, str]:
    """Net, VAT (0% Teknopark/Export exempt) and total in USD/USDC/USDT for one period of a plan.
    When email is given, adds deterministic unique cents ($0.10-$0.99) bound to the customer
    to ensure on-chain crypto transactions are non-fungible per buyer and immune to front-running."""
    p = P.get(plan_id)
    per_month = p.get("price_yearly_per_month") if cycle == "yearly" else p.get("price_monthly")
    if not per_month:
        raise S.CommerceError(400, "no_usd_price", "This plan cannot be bought online.")
    cents = Decimal(str(crypto_cents(email))) if email else Decimal("0.00")
    net = (Decimal(str(per_month)) * (12 if cycle == "yearly" else 1)) + cents
    return {"net": money(net), "vat": "0.00", "total": money(net), "vat_rate": "0.0"}


def _base58_decode(s: str) -> bytes:
    alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    num = 0
    for ch in s:
        num = num * 58 + alphabet.index(ch)
    combined = num.to_bytes(25, byteorder="big")
    return combined[:-4]


def _tron_hex41(addr: str) -> str:
    if addr.startswith("T") and len(addr) == 34:
        return _base58_decode(addr).hex().lower()
    return addr.lower().replace("0x", "")


CRYPTO_MAX_AGE = float(os.environ.get("ANSWERR_CRYPTO_MAX_AGE_HOURS", "72")) * 3600


def _check_age(ts: Optional[float]) -> None:
    """The deposit addresses are long-lived treasury wallets: only a transfer made for this purchase (recent) may be
    claimed, never an older transfer that happens to sit in the wallet's history."""
    if ts is None:
        raise S.CommerceError(502, "verification_error", "Could not read the transaction time.")
    if time.time() - ts > CRYPTO_MAX_AGE:
        raise S.CommerceError(400, "tx_too_old", "This transfer is older than {} hours; it cannot be used for a new purchase.".format(
            int(CRYPTO_MAX_AGE // 3600)))


def _evm_block_time(rpcs, block_number: str) -> Optional[float]:
    for rpc in rpcs:
        try:
            body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_getBlockByNumber", "params": [block_number, False]}).encode()
            req = urllib.request.Request(rpc, data=body, headers={"Content-Type": "application/json", "User-Agent": "answerr-billing/1.0"})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                blk = json.loads(r.read().decode("utf-8")).get("result") or {}
            if blk.get("timestamp"):
                return float(int(blk["timestamp"], 16))
        except Exception:
            continue
    return None


def verify_crypto_payment(tx_hash: str, network: str, token: str, expected_usd: float) -> Dict[str, Any]:
    """Verifies a recent on-chain USDC/USDT payment on Base, Ethereum, Arbitrum, BSC, or TRON TRC20."""
    tx_clean = (tx_hash or "").strip()
    net = (network or "base").strip().lower()
    tok = (token or "USDC").strip().upper()

    if net in ("tron", "trc20", "trx"):
        raw_id = tx_clean[2:] if tx_clean.lower().startswith("0x") else tx_clean
        if len(raw_id) != 64:
            raise S.CommerceError(400, "bad_tx_hash", "Invalid TRON TRC20 transaction hash (must be 64 hex chars).")
        target_hex41 = _tron_hex41(TRC20_DEPOSIT_ADDRESS)
        target_evm = target_hex41[2:] if target_hex41.startswith("41") else target_hex41
        try:
            req = urllib.request.Request(
                f"https://api.trongrid.io/v1/transactions/{raw_id}/events",
                headers={"Accept": "application/json", "User-Agent": "answerr-billing/1.0"},
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                ev_data = json.loads(r.read().decode("utf-8"))
            if ev_data.get("success") and ev_data.get("data"):
                for ev in ev_data["data"]:
                    if ev.get("event_name") == "Transfer" and ev.get("contract_address") == "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t":
                        res = ev.get("result") or {}
                        to_addr = str(res.get("to") or "").lower().replace("0x", "")
                        if to_addr == target_evm or to_addr == target_hex41:
                            amt = int(res.get("value") or 0) / 1e6
                            if abs(amt - expected_usd) > 0.05:
                                raise S.CommerceError(400, "mismatched_amount", f"Expected {expected_usd:.2f} USDT, found {amt:.2f} USDT. Transfer amount must match your account quote.")
                            bts = ev.get("block_timestamp")
                            _check_age(float(bts) / 1000.0 if bts else None)
                            return {"verified": True, "amount": amt, "currency": "USDT", "network": "TRON TRC20", "tx_hash": raw_id}
        except S.CommerceError:
            raise
        except Exception as e:
            raise S.CommerceError(502, "verification_error", f"Could not verify TRON transaction: {e}")
        raise S.CommerceError(400, "transfer_not_found", f"No verified USDT transfer to {TRC20_DEPOSIT_ADDRESS} found in TRON tx.")

    if net not in EVM_CHAINS:
        raise S.CommerceError(400, "unsupported_network", f"Unsupported network '{net}'. Choose base, trc20, ethereum, arbitrum, or bsc.")
    if not tx_clean.startswith("0x") or len(tx_clean) != 66:
        raise S.CommerceError(400, "bad_tx_hash", "Invalid EVM transaction hash (must start with 0x and be 66 characters).")

    chain = EVM_CHAINS[net]
    receipt = None
    for rpc in chain["rpcs"]:
        try:
            body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_getTransactionReceipt", "params": [tx_clean]}).encode("utf-8")
            req = urllib.request.Request(rpc, data=body, headers={"Content-Type": "application/json", "User-Agent": "answerr-billing/1.0"})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                resp = json.loads(r.read().decode("utf-8"))
            if resp.get("result"):
                receipt = resp["result"]
                break
        except Exception:
            continue

    if not receipt:
        raise S.CommerceError(400, "tx_not_found", f"Transaction not found or still pending on {chain['name']}.")
    if receipt.get("status") != "0x1":
        raise S.CommerceError(400, "tx_reverted", "Transaction reverted on-chain.")

    target_padded = "0x" + EVM_DEPOSIT_ADDRESS.lower().replace("0x", "").zfill(64)
    tokens_to_check = [tok] + [k for k in chain["tokens"] if k != tok]
    for t_sym in tokens_to_check:
        if t_sym not in chain["tokens"]:
            continue
        c_addr, decimals = chain["tokens"][t_sym]
        for log in receipt.get("logs") or []:
            if (log.get("address") or "").lower() == c_addr.lower():
                topics = [t.lower() for t in (log.get("topics") or [])]
                if len(topics) >= 3 and topics[0] == ERC20_TRANSFER_TOPIC and topics[2] == target_padded:
                    raw_val = int(log.get("data") or "0x0", 16)
                    amt = raw_val / float(10 ** decimals)
                    if abs(amt - expected_usd) > 0.05:
                        raise S.CommerceError(400, "mismatched_amount", f"Expected {expected_usd:.2f} {t_sym}, found {amt:.2f} {t_sym}. Transfer amount must match your account quote.")
                    _check_age(_evm_block_time(chain["rpcs"], receipt.get("blockNumber") or "latest"))
                    return {"verified": True, "amount": amt, "currency": t_sym, "network": chain["name"], "tx_hash": tx_clean.lower()}

    raise S.CommerceError(400, "transfer_not_found", f"No USDC/USDT transfer to {EVM_DEPOSIT_ADDRESS} found in transaction logs.")


def invoice_number(pay: Dict[str, Any]) -> str:
    """INV-YYYY-XXXXXXXX for a paid payment, PRO-YYYY-XXXXXXXX (proforma) otherwise; same rule as the PDF."""
    paid = str(pay.get("status") or "").lower() in ("paid", "verified", "completed", "active")
    ts = pay.get("paid_at") or pay.get("created_at") or time.time()
    return "{}-{}-{}".format("INV" if paid else "PRO", time.strftime("%Y", time.gmtime(ts)),
                             str(pay.get("id") or "").replace("pay_", "").upper()[:8])


def generate_answerr_invoice_pdf(acc: Optional[Dict[str, Any]], pay: Dict[str, Any]) -> bytes:
    """Generates an official A4 Commercial Invoice PDF (0% KDV under Law No. 4691 & 3065 Temporary Art. 20/1) with PAID or UNPAID stamp for answerr.me."""
    import io
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except ImportError:
        return b'%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 595 842]/Parent 2 0 R/Resources<<>>>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000056 00000 n\n0000000111 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF\n'

    font_dir = "/usr/share/fonts/truetype/dejavu"
    f_reg, f_bold, f_mono = "Helvetica", "Helvetica-Bold", "Courier"
    if os.path.exists(os.path.join(font_dir, "DejaVuSans.ttf")):
        try:
            pdfmetrics.registerFont(TTFont("DejaVu", os.path.join(font_dir, "DejaVuSans.ttf")))
            pdfmetrics.registerFont(TTFont("DejaVu-Bold", os.path.join(font_dir, "DejaVuSans-Bold.ttf")))
            pdfmetrics.registerFont(TTFont("DejaVu-Mono", os.path.join(font_dir, "DejaVuSansMono.ttf")))
            f_reg, f_bold, f_mono = "DejaVu", "DejaVu-Bold", "DejaVu-Mono"
        except Exception:
            pass

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    pay_status = str(pay.get("status") or "").lower()
    is_paid = pay_status in ("paid", "verified", "completed", "active")
    inv_no = invoice_number(pay)
    c.setTitle(f"Commercial Invoice {inv_no} ({'PAID' if is_paid else 'UNPAID'}) - ITouch Systems / answerr")

    c.setFillColor(colors.HexColor("#0A1230"))
    c.rect(0, height - 10 * mm, width, 10 * mm, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#10B981") if is_paid else colors.HexColor("#F59E0B"))
    c.rect(0, height - 11.2 * mm, width, 1.2 * mm, fill=1, stroke=0)

    y_top = height - 26 * mm
    c.setFont(f_bold, 16)
    c.setFillColor(colors.HexColor("#0A1230"))
    c.drawString(18 * mm, y_top + 6 * mm, "answerr PRO  |  ITouch Systems")
    c.setFont(f_reg, 8.5)
    c.setFillColor(colors.HexColor("#475569"))
    c.drawString(18 * mm, y_top + 1 * mm, "Deterministic Policy Gate & Reflex Decision Platform (https://answerr.me)")

    c.setFont(f_bold, 13.5)
    c.setFillColor(colors.HexColor("#0A1230"))
    c.drawRightString(width - 18 * mm, y_top + 6 * mm, "COMMERCIAL INVOICE" if is_paid else "COMMERCIAL INVOICE (PROFORMA)")
    c.setFont(f_reg, 7.8)
    c.setFillColor(colors.HexColor("#475569"))
    c.drawRightString(width - 18 * mm, y_top + 1 * mm, "TİCARİ FATURA / ÖDEME MAKBUZU (%0 KDV AR-GE)" if is_paid else "TİCARİ FATURA / ÖDEME BEKLEYEN TAHAKKUK")

    badge_w, badge_h = 54 * mm, 6.5 * mm
    badge_x, badge_y = width - 18 * mm - badge_w, y_top - 6.5 * mm
    c.setFillColor(colors.HexColor("#ECFDF5") if is_paid else colors.HexColor("#FEF3C7"))
    c.setStrokeColor(colors.HexColor("#10B981") if is_paid else colors.HexColor("#D97706"))
    c.roundRect(badge_x, badge_y, badge_w, badge_h, 1.5 * mm, fill=1, stroke=1)
    c.setFont(f_bold, 8.2)
    c.setFillColor(colors.HexColor("#047857") if is_paid else colors.HexColor("#B45309"))
    c.drawCentredString(badge_x + badge_w / 2.0, badge_y + 2 * mm, "STAMP: PAID / ÖDENDİ" if is_paid else "STAMP: UNPAID / ÖDEME BEKLİYOR")

    y_cursor = y_top - 9 * mm
    c.setStrokeColor(colors.HexColor("#CBD5E1"))
    c.line(18 * mm, y_cursor, width - 18 * mm, y_cursor)

    y_cursor -= 6 * mm
    c.setFont(f_bold, 8)
    c.setFillColor(colors.HexColor("#0284C7"))
    c.drawString(18 * mm, y_cursor, "ISSUED BY (SELLER / SATICI KURUM)")
    c.drawString(width - 84 * mm, y_cursor, "INVOICE DETAILS (FATURA BİLGİLERİ)")

    y_cursor -= 4.5 * mm
    c.setFont(f_bold, 8.5)
    c.setFillColor(colors.HexColor("#0F172A"))
    c.drawString(18 * mm, y_cursor, "ITOUCH BİLİŞİM SİSTEMLERİ MÜHENDİSLİK DANIŞMANLIK")
    y_cursor -= 4 * mm
    c.drawString(18 * mm, y_cursor, "SANAYİ VE TİCARET LİMİTED ŞİRKETİ")

    c.setFont(f_reg, 8)
    c.setFillColor(colors.HexColor("#334155"))
    for sl in [
        "Operating Brand: answerr™ & Werr™ Technology (ITouch Systems)",
        "Address: Balcalı Mah. Güney Kampüs/5 Sk. No: 4/1 İç Kapı No: 26",
        "Çukurova Üniversitesi Teknokent, 01330 Sarıçam / Adana, Türkiye",
        "Tax Office & ID (VKN): Yüreğir V.D. — 4690944558  |  MERSİS: 0469094455800001",
        "Web: https://answerr.me • https://werr.io  |  Email: ask@answerr.me • billing@werr.io",
    ]:
        y_cursor -= 4 * mm
        c.drawString(18 * mm, y_cursor, sl)

    paid_ts = float(pay.get("paid_at") or pay.get("created_at") or time.time())
    p_end = float(pay.get("period_end") or (paid_ts + 31 * 86400))
    curr = pay.get("currency") or "TRY"
    prov = pay.get("provider") or "iyzico"
    method_label = (
        "iyzico 3D Card" if prov == "iyzico"
        else ("Bank Wire / EFT (TEB)" if prov in ("manual", "bank_wire") else f"On-Chain Crypto ({prov.replace('crypto_', '').upper()})")
    )
    meta_rows = [
        ("Invoice No:", inv_no),
        ("Payment Ref:", str(pay.get("id") or "-")),
        ("Issue Date:", time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(paid_ts))),
        ("Service Period:", f"{time.strftime('%Y-%m-%d', time.gmtime(paid_ts))} to {time.strftime('%Y-%m-%d', time.gmtime(p_end))}"),
        ("Payment Method:", method_label),
        ("Status:", "PAID / ÖDENDİ (%0 KDV)" if is_paid else "UNPAID / ÖDEME BEKLİYOR"),
    ]
    my = y_top - 19.5 * mm
    for k_l, v_l in meta_rows:
        c.setFont(f_reg, 8)
        c.setFillColor(colors.HexColor("#64748B"))
        c.drawString(width - 84 * mm, my, k_l)
        c.setFont(f_bold, 8)
        c.setFillColor(colors.HexColor("#047857") if (k_l == "Status:" and is_paid) else (colors.HexColor("#B45309") if k_l == "Status:" else colors.HexColor("#0F172A")))
        c.drawRightString(width - 18 * mm, my, str(v_l)[:32])
        my -= 4.3 * mm

    y_cursor = min(y_cursor, my) - 6 * mm
    b = json.loads(pay.get("billing_json") or "{}") if isinstance(pay.get("billing_json"), str) else (pay.get("billing") or {})
    if not b and acc:
        try:
            b = json.loads(acc.get("billing_json") or "{}")
        except Exception:
            b = {}

    c.setFillColor(colors.HexColor("#F8FAFC"))
    c.setStrokeColor(colors.HexColor("#CBD5E1"))
    c.roundRect(18 * mm, y_cursor - 22 * mm, width - 36 * mm, 24 * mm, 2 * mm, fill=1, stroke=1)
    c.setFont(f_bold, 8)
    c.setFillColor(colors.HexColor("#0284C7"))
    c.drawString(22 * mm, y_cursor - 3.5 * mm, "BILLED TO (BUYER / ALICI BİLGİLERİ)")
    c.setFont(f_bold, 9)
    c.setFillColor(colors.HexColor("#0F172A"))
    buyer_name = b.get("legal_name") or (acc or {}).get("company") or (acc or {}).get("email") or "Valued answerr Subscriber"
    c.drawString(22 * mm, y_cursor - 8.5 * mm, str(buyer_name)[:70])
    c.setFont(f_reg, 8)
    c.setFillColor(colors.HexColor("#334155"))
    c.drawString(22 * mm, y_cursor - 13.5 * mm, f"Tax ID / VKN: {b.get('tax_id') or '-'} ({b.get('tax_office') or '-'})   |   Email: {b.get('invoice_email') or (acc or {}).get('email') or '-'}")
    c.drawString(22 * mm, y_cursor - 18.5 * mm, f"Address: {b.get('address') or '-'} {b.get('city') or ''} {b.get('country') or ''}"[:90])

    y_cursor -= 30 * mm
    c.setFillColor(colors.HexColor("#0A1230"))
    c.rect(18 * mm, y_cursor - 7 * mm, width - 36 * mm, 7 * mm, fill=1, stroke=0)
    c.setFont(f_bold, 8)
    c.setFillColor(colors.white)
    c.drawString(21 * mm, y_cursor - 4.8 * mm, "DESCRIPTION (YAZILIM HİZMETİ AÇIKLAMASI)")
    c.drawRightString(width - 21 * mm, y_cursor - 4.8 * mm, "AMOUNT (%0 KDV)")

    row_y = y_cursor - 19 * mm
    c.setFillColor(colors.white)
    c.setStrokeColor(colors.HexColor("#CBD5E1"))
    c.rect(18 * mm, row_y, width - 36 * mm, 12 * mm, fill=1, stroke=1)
    plan_title = {"gelistirici": "Geliştirici (Developer)", "pro": "Pro", "kurumsal": "Kurumsal (Enterprise)"}.get(pay.get("plan"), pay.get("plan") or "Pro")
    cycle_title = "Yıllık (366 Gün / 12 Ay)" if pay.get("cycle") == "yearly" else "Aylık (31 Gün / 1 Ay)"
    c.setFont(f_bold, 8.5)
    c.setFillColor(colors.HexColor("#0F172A"))
    c.drawString(21 * mm, row_y + 7 * mm, f"answerr PRO SaaS & Decision API Subscription — {plan_title} Plan ({cycle_title})")
    c.setFont(f_reg, 7.5)
    c.setFillColor(colors.HexColor("#475569"))
    c.drawString(21 * mm, row_y + 2.5 * mm, "4691 s. TGB Kanunu ve 3065 s. KDV Kanunu Geçici 20/1 md. (Teknopark Ar-Ge Yazılım İstisnası — %0 KDV)")
    tot_str = f"{float(pay.get('total_try') or 0):,.2f} {curr}"
    c.setFont(f_bold, 9)
    c.setFillColor(colors.HexColor("#15803D") if is_paid else colors.HexColor("#B45309"))
    c.drawRightString(width - 21 * mm, row_y + 4.8 * mm, tot_str)

    tot_y = row_y - 22 * mm
    c.setFillColor(colors.HexColor("#F8FAFC"))
    c.setStrokeColor(colors.HexColor("#CBD5E1"))
    c.roundRect(18 * mm, tot_y, width - 36 * mm, 17 * mm, 2 * mm, fill=1, stroke=1)
    c.setFont(f_bold, 7.8)
    c.setFillColor(colors.HexColor("#0284C7"))
    c.drawString(21 * mm, tot_y + 12 * mm, "TAX EXEMPTION & PAYMENT VERIFICATION (%0 KDV MUAFİYET VE ÖDEME KAYDI)")
    c.setFont(f_reg, 7.5)
    c.setFillColor(colors.HexColor("#334155"))
    c.drawString(21 * mm, tot_y + 7.2 * mm, f"Net: {tot_str}  |  KDV / VAT (0% — 4691 & 3065 Geçici 20/1 Teknopark İstisnası): 0.00 {curr}  |  {'Total Paid' if is_paid else 'Amount Due'}: {tot_str}")
    c.setFont(f_mono, 7.1)
    c.drawString(21 * mm, tot_y + 2.5 * mm, f"Reference / TXID: {pay.get('payment_id') or pay.get('id')} ({pay.get('card_last4') or prov}) — {'VERIFIED PAID' if is_paid else 'UNPAID / AWAITING SETTLEMENT'}")

    bank_y = tot_y - 26 * mm
    c.setFillColor(colors.HexColor("#FFFBEB") if not is_paid else colors.HexColor("#F8FAFC"))
    c.setStrokeColor(colors.HexColor("#F59E0B") if not is_paid else colors.HexColor("#CBD5E1"))
    c.roundRect(18 * mm, bank_y, width - 36 * mm, 22 * mm, 2 * mm, fill=1, stroke=1)
    c.setFont(f_bold, 7.8)
    c.setFillColor(colors.HexColor("#B45309") if not is_paid else colors.HexColor("#0284C7"))
    c.drawString(21 * mm, bank_y + 17 * mm, "OFFICIAL CORPORATE BANK ACCOUNTS (TEB — TÜRK EKONOMİ BANKASI A.Ş. / ADANA TOROS ŞB. 446 | SWIFT: TEBUTRIS)")
    c.setFont(f_reg, 7.2)
    c.setFillColor(colors.HexColor("#0F172A"))
    c.drawString(21 * mm, bank_y + 12.2 * mm, "Beneficiary (SWIFT): ITOUCH BILISIM SISTEMLERI LTD. STI.   |   Alıcı (Yurtiçi): ITOUCH BİLİŞİM SİSTEMLERİ LTD. ŞTİ.")
    c.setFont(f_mono, 7.2)
    c.drawString(21 * mm, bank_y + 7.4 * mm, "TRY (TL) IBAN : TR92 0003 2000 0000 0070 5754 65   |   USD IBAN : TR83 0003 2000 0000 0088 9467 48")
    c.drawString(21 * mm, bank_y + 2.8 * mm, "EUR IBAN      : TR28 0003 2000 0000 0088 9467 68   |   EVM USDC : 0x4945ef6e124eea2176ddf050b33db42b0ae8c7f7")

    c.showPage()
    c.save()
    return buf.getvalue()
