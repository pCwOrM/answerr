"""Payment provider boundary.

answerr computes *what* is owed (store.build_statement / generate_statements). Collecting money and
issuing the legal invoice are separate steps:

  1. Collection  — a PaymentProvider (today: ManualProvider = bank transfer / EFT on request;
                    later: iyzico checkout form + subscriptions, see docs/commerce/IYZICO_ENTEGRASYONU.md).
  2. Legal invoice — e-Fatura / e-Arşiv Fatura issued by ITouch's accounting integrator (GİB).
                    Its number is attached to the statement with mark_statement(..., e_invoice_no=...).

The provider is selected with ANSWERR_PAYMENT_PROVIDER (manual | iyzico). Only `manual` is active.
"""
from __future__ import annotations

import os
from typing import Any, Dict

from . import store as S


class PaymentProvider:
    name = "base"

    def checkout(self, account: Dict[str, Any], plan: str, cycle: str) -> Dict[str, Any]:
        raise NotImplementedError

    def handle_callback(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError


class ManualProvider(PaymentProvider):
    """Plan change becomes a request; the team confirms by e-mail with bank details, and an admin
    activates the plan after payment (POST /v1/admin/plan-requests/{id}/approve)."""
    name = "manual"

    def checkout(self, account, plan, cycle):
        return {"provider": self.name, "mode": "request", "next": "We will e-mail payment details within one working day."}

    def handle_callback(self, payload):
        raise S.CommerceError(404, "no_callback", "Manual payments have no callback.")


class IyzicoProvider(PaymentProvider):
    """Placeholder that keeps the integration boundary explicit. Enabled only after the steps in
    docs/commerce/IYZICO_ENTEGRASYONU.md are completed with ITouch's merchant account."""
    name = "iyzico"

    def __init__(self):
        self.api_key = os.environ.get("IYZICO_API_KEY", "")
        self.secret = os.environ.get("IYZICO_SECRET_KEY", "")
        self.base_url = os.environ.get("IYZICO_BASE_URL", "https://sandbox-api.iyzipay.com")

    def checkout(self, account, plan, cycle):
        raise S.CommerceError(501, "provider_not_enabled", "Online payment is not enabled yet; your request was recorded.")

    def handle_callback(self, payload):
        raise S.CommerceError(501, "provider_not_enabled", "iyzico callbacks are not enabled yet.")


def provider() -> PaymentProvider:
    return IyzicoProvider() if os.environ.get("ANSWERR_PAYMENT_PROVIDER", "manual") == "iyzico" else ManualProvider()
