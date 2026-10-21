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

VAT_RATE = Decimal(str(P.CATALOG.get("vat_rate", 0.20)))
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
        return {"provider": self.name, "mode": "request", "next": "We will e-mail payment details within one working day."}


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

    def retrieve(self, token: str) -> Dict[str, Any]:
        return self.post("/payment/iyzipos/checkoutform/auth/ecom/detail", {"locale": "tr", "token": token})

    def settle(self, token: str) -> Dict[str, Any]:
        """Retrieves the result for a token and completes or fails the matching payment. Safe to call repeatedly."""
        pay = S.get_payment(token=token)
        if not pay:
            return {"result": "unknown"}
        if pay["status"] == "paid":
            return {"result": "paid", "payment": pay, "activated": False}
        res = self.retrieve(token)
        if res.get("status") != "success":
            return {"result": "error", "payment": pay, "error": res.get("errorMessage")}
        ps = (res.get("paymentStatus") or "").upper()
        checks = {
            "conversation": res.get("conversationId") == pay["conversation_id"],
            "basket": res.get("basketId") in (None, pay["id"]),
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
    parts = name.split()
    first, last = (" ".join(parts[:-1]), parts[-1]) if len(parts) > 1 else (name, name)
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
