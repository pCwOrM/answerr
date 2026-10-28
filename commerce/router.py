"""HTTP surface of the commercial layer (mounted by api_server.py).

Authentication
  Authorization: Bearer ans_live_…   API key   (machines: decisions, reviews, outcomes, usage)
  Authorization: Bearer ans_sess_…   session   (console: everything incl. keys, members, billing)
  X-Admin-Key: …                     ITouch operations (ANSWERR_ADMIN_KEY)
Roles: owner > admin > reviewer. Reviewers can read logs and resolve reviews only.
"""
from __future__ import annotations

import csv
import hmac
import io
import json
import os
import time
from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

import access_mailer as AM

from . import billing, mail, plans as P, store as S, webhooks

router = APIRouter()
CTX: Dict[str, Callable] = {}          # filled by api_server.configure_commerce()
MAX_BACKTEST = 1000


def configure(**deps) -> None:
    CTX.update(deps)


# ----------------------------------------------------------------------------- helpers
def principal(request: Request) -> Optional[Dict[str, Any]]:
    return (getattr(request.state, "security", None) or {}).get("principal")


def need(request: Request, *, roles=("owner", "admin", "reviewer"), session_only: bool = False) -> Dict[str, Any]:
    p = principal(request)
    if not p:
        raise S.CommerceError(401, "unauthorized", "Sign in or send an answerr API key (Authorization: Bearer …).")
    if session_only and p["via"] != "session":
        raise S.CommerceError(403, "session_required", "This action is available from the console only.")
    if p["role"] not in roles:
        raise S.CommerceError(403, "forbidden", "Your role ({}) cannot do this.".format(p["role"]))
    return p


def feature(account_id: str, name: str) -> None:
    acc = S.get_account(account_id)
    if not P.has(S.effective_plan(acc), name):
        raise S.CommerceError(403, "feature_unavailable", "'{}' is not included in your plan.".format(name), feature=name,
                              upgrade="https://answerr.me/pro/pricing.html")


def admin(request: Request) -> str:
    key = os.environ.get("ANSWERR_ADMIN_KEY", "")
    got = request.headers.get("x-admin-key") or ""
    if len(key) < 24 or not hmac.compare_digest(key.encode(), got.encode()):
        raise S.CommerceError(401, "admin_only", "Admin key required.")
    return "admin"


def ip_of(request: Request) -> str:
    return CTX["client_ip"](request) if "client_ip" in CTX else (request.client.host if request.client else "")


def human_check(request: Request) -> None:
    """Browser forms: per-IP limit and reCAPTCHA (when configured)."""
    if "limit_form" in CTX:
        CTX["limit_form"](request)
    if "require_human" in CTX:
        CTX["require_human"](request)


# ----------------------------------------------------------------------------- public
@router.get("/v1/plans", tags=["Plans & billing"])
def get_plans():
    return {"status": "success", **P.public_catalog(), "card_payments": billing.provider().name == "iyzico",
            "crypto_payments": True, "evm_deposit_address": billing.EVM_DEPOSIT_ADDRESS,
            "trc20_deposit_address": billing.TRC20_DEPOSIT_ADDRESS,
            "base_usdc_contract": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
            "card_currency": "TRY", "vat_rate": float(billing.VAT_RATE)}


class SignupRequest(BaseModel):
    email: str = Field(..., max_length=254)
    company: Optional[str] = Field(None, max_length=120)
    accept_terms: bool = False
    kvkk_ack: bool = False
    marketing: bool = False
    lang: Optional[str] = "tr"
    website: Optional[str] = Field(None, max_length=200, description="honeypot")


class LoginRequest(BaseModel):
    email: str = Field(..., max_length=254)
    lang: Optional[str] = "tr"
    website: Optional[str] = Field(None, max_length=200)


class VerifyRequest(BaseModel):
    token: str = Field(..., max_length=200)


SENT = {"status": "sent", "message": "If the address can be used, a sign-in link is on its way (valid 20 minutes)."}


@router.post("/v1/auth/signup", tags=["Accounts"])
def signup(req: SignupRequest, request: Request):
    email = (req.email or "").strip().lower()
    if not AM.valid_email(email):
        raise S.CommerceError(400, "bad_email", "Please enter a valid e-mail address.")
    if not (req.accept_terms and req.kvkk_ack):
        raise S.CommerceError(400, "consent_required", "Accept the terms of service and acknowledge the KVKK notice to continue.")
    human_check(request)
    if (req.website or "").strip():
        return SENT
    lang = req.lang if req.lang in ("tr", "en") else "tr"
    existing = S.member_of(email)
    purpose = "login" if existing else "signup"
    tok = S.create_login_token(email, purpose, {"company": req.company, "lang": lang, "marketing": req.marketing,
                                                "terms_version": S.TERMS_VERSION}, ip_of(request))
    mail.login_link(email, tok, purpose, lang)
    return SENT


@router.post("/v1/auth/login", tags=["Accounts"])
def login(req: LoginRequest, request: Request):
    email = (req.email or "").strip().lower()
    if not AM.valid_email(email):
        raise S.CommerceError(400, "bad_email", "Please enter a valid e-mail address.")
    human_check(request)
    if (req.website or "").strip():
        return SENT
    lang = req.lang if req.lang in ("tr", "en") else "tr"
    if S.member_of(email):          # same answer either way: no account enumeration
        tok = S.create_login_token(email, "login", {}, ip_of(request))
        mail.login_link(email, tok, "login", lang)
    else:
        mail.no_account(email, lang)
    return SENT


@router.post("/v1/auth/verify", tags=["Accounts"])
def verify(req: VerifyRequest, request: Request):
    out = S.verify_login(req.token.strip(), ip_of(request))
    out["status"] = "success"
    out["account"] = S.account_view(out["account_id"])
    return out


@router.post("/v1/auth/logout", tags=["Accounts"])
def logout(request: Request):
    auth = request.headers.get("authorization") or ""
    if auth.lower().startswith("bearer ans_sess_"):
        S.revoke_session(auth[7:].strip())
    return {"status": "success"}


# ----------------------------------------------------------------------------- account
class AccountPatch(BaseModel):
    company: Optional[str] = Field(None, max_length=120)
    lang: Optional[str] = None
    overage_enabled: Optional[bool] = None
    store_review_state: Optional[bool] = None
    webhook_url: Optional[str] = Field(None, max_length=500)
    billing: Optional[Dict[str, Optional[str]]] = None


@router.get("/v1/account", tags=["Accounts"])
def get_account(request: Request):
    p = need(request)
    view = S.account_view(p["account_id"])
    view["me"] = {"email": p.get("email"), "role": p["role"], "via": p["via"], "key_prefix": p.get("prefix")}
    view["pending_plan_request"] = next(iter(S.list_plan_requests(p["account_id"], "pending")), None)
    return {"status": "success", "account": view}


@router.patch("/v1/account", tags=["Accounts"])
def patch_account(req: AccountPatch, request: Request):
    p = need(request, roles=("owner", "admin"), session_only=True)
    fields = req.model_dump(exclude_unset=True)
    return {"status": "success", "account": S.update_account(p["account_id"], p["email"], fields)}


@router.get("/v1/account/webhook-secret", tags=["Accounts"])
def get_webhook_secret(request: Request):
    p = need(request, roles=("owner", "admin"), session_only=True)
    acc = S.get_account(p["account_id"])
    return {"status": "success", "webhook_secret": acc.get("webhook_secret")}


@router.post("/v1/account/webhook-secret", tags=["Accounts"])
def rotate_webhook_secret(request: Request):
    p = need(request, roles=("owner", "admin"), session_only=True)
    return {"status": "success", "webhook_secret": S.rotate_webhook_secret(p["account_id"], p["email"])}


@router.post("/v1/account/webhook-test", tags=["Accounts"])
def webhook_test(request: Request):
    p = need(request, roles=("owner", "admin"), session_only=True)
    feature(p["account_id"], "webhooks")
    acc = S.get_account(p["account_id"])
    if not acc.get("webhook_url"):
        raise S.CommerceError(400, "no_webhook", "Set a webhook URL first.")
    webhooks.send(acc, "ping", {"account_id": acc["id"], "message": "answerr webhook test"}, sync=True)
    return {"status": "success", "deliveries": webhooks.recent(acc["id"], 1)}


@router.get("/v1/account/webhooks", tags=["Accounts"])
def webhook_log(request: Request):
    p = need(request, roles=("owner", "admin"))
    return {"status": "success", "deliveries": webhooks.recent(p["account_id"])}


class KeyCreate(BaseModel):
    label: str = Field("key", max_length=60)


@router.get("/v1/account/keys", tags=["Accounts"])
def keys(request: Request):
    p = need(request, roles=("owner", "admin"))
    return {"status": "success", "keys": S.list_keys(p["account_id"])}


@router.post("/v1/account/keys", tags=["Accounts"])
def create_key(req: KeyCreate, request: Request):
    p = need(request, roles=("owner", "admin"), session_only=True)
    raw, row = S.create_api_key(p["account_id"], req.label, p["email"])
    return {"status": "created", "api_key": raw, "key": row, "note": "Shown once. Store it in a secret manager."}


@router.delete("/v1/account/keys/{key_id}", tags=["Accounts"])
def delete_key(key_id: str, request: Request):
    p = need(request, roles=("owner", "admin"), session_only=True)
    if not S.revoke_key(p["account_id"], key_id, p["email"]):
        raise S.CommerceError(404, "no_key", "Key not found or already revoked.")
    return {"status": "revoked", "key_id": key_id}


class Invite(BaseModel):
    email: str = Field(..., max_length=254)
    role: str = "reviewer"


@router.get("/v1/account/members", tags=["Accounts"])
def members(request: Request):
    p = need(request)
    return {"status": "success", "members": S.list_members(p["account_id"]), "seats": S.plan_of(S.get_account(p["account_id"]))["seats"]}


@router.post("/v1/account/members", tags=["Accounts"])
def invite(req: Invite, request: Request):
    p = need(request, roles=("owner", "admin"), session_only=True)
    email = req.email.strip().lower()
    if not AM.valid_email(email):
        raise S.CommerceError(400, "bad_email", "Please enter a valid e-mail address.")
    S.invite_member(p["account_id"], email, req.role, p["email"])
    acc = S.get_account(p["account_id"])
    tok = S.create_login_token(email, "invite", {}, ip_of(request))
    mail.invitation(email, p["email"], acc.get("company") or "", req.role, tok, acc.get("lang") or "tr")
    return {"status": "invited", "members": S.list_members(p["account_id"])}


@router.delete("/v1/account/members/{email}", tags=["Accounts"])
def remove_member(email: str, request: Request):
    p = need(request, roles=("owner", "admin"), session_only=True)
    if not S.remove_member(p["account_id"], email, p["email"]):
        raise S.CommerceError(404, "no_member", "Member not found.")
    return {"status": "removed", "members": S.list_members(p["account_id"])}


@router.get("/v1/account/usage", tags=["Usage"])
def usage(request: Request, days: int = 30):
    p = need(request)
    view = S.account_view(p["account_id"])
    return {"status": "success", "usage": view["usage"], "series": S.usage_series(p["account_id"], days)}


@router.get("/v1/account/events", tags=["Accounts"])
def events(request: Request, limit: int = 100):
    p = need(request, roles=("owner", "admin"))
    return {"status": "success", "events": S.account_events(p["account_id"], min(max(limit, 1), 500))}


# ----------------------------------------------------------------------------- decision log, shadow, outcomes
@router.get("/v1/account/decisions", tags=["Decision log"])
def decisions(request: Request, limit: int = 100, verdict: Optional[str] = None, gate_id: Optional[str] = None,
              mode: Optional[str] = None, before: Optional[float] = None):
    p = need(request)
    rows = S.list_decisions(p["account_id"], limit=min(limit, 500), verdict=verdict, gate_id=gate_id, mode=mode, before=before)
    return {"status": "success", "decisions": rows, "next_before": rows[-1]["ts"] if len(rows) == min(limit, 500) else None,
            "retention_days": S.plan_of(S.get_account(p["account_id"]))["retention_days"]}


@router.get("/v1/account/decisions.csv", tags=["Decision log"])
def decisions_csv(request: Request, days: int = 30, verdict: Optional[str] = None, gate_id: Optional[str] = None,
                  mode: Optional[str] = None):
    p = need(request)
    feature(p["account_id"], "export")
    rows = S.list_decisions(p["account_id"], limit=10000, verdict=verdict, gate_id=gate_id, mode=mode,
                            since=time.time() - max(1, min(days, 400)) * 86400)
    buf = io.StringIO()
    w = csv.writer(buf)
    cols = ["id", "ts_iso", "gate_id", "verdict", "rule_id", "reason", "latency_ms", "mode", "observed", "key_prefix",
            "policy_seal", "external_id", "state_fields"]
    w.writerow(cols)
    for r in rows:
        w.writerow([r["id"], time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(r["ts"])), r["gate_id"], r["verdict"], r["rule_id"],
                    r["reason"], r["latency_ms"], r["mode"], r["observed"] or "", r["key_prefix"] or "", r["policy_seal"] or "",
                    r["external_id"] or "", " ".join(r["state_fields"])])
    return Response(content=buf.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="answerr-decisions-{}.csv"'.format(S.day_of())})


class Outcome(BaseModel):
    observed_outcome: Any


@router.post("/v1/decisions/{decision_id}/outcome", tags=["Decision log"])
def outcome(decision_id: str, req: Outcome, request: Request):
    p = need(request, roles=("owner", "admin"))
    return {"status": "success", **S.set_outcome(p["account_id"], decision_id, req.observed_outcome, p.get("email") or p.get("prefix"))}


@router.get("/v1/account/shadow-report", tags=["Shadow mode"])
def shadow(request: Request, days: int = 30, gate_id: Optional[str] = None):
    p = need(request)
    feature(p["account_id"], "shadow")
    return {"status": "success", "report": S.shadow_report(p["account_id"], days, gate_id)}


class BacktestRecord(BaseModel):
    state: Dict[str, Any]
    observed_outcome: Optional[Any] = None
    id: Optional[str] = Field(None, max_length=120)


class BacktestRequest(BaseModel):
    gate_id: Optional[str] = None
    policy: Optional[Dict[str, Any]] = None
    strict: bool = True
    records: List[BacktestRecord] = Field(..., min_length=1)


@router.post("/v1/backtest", tags=["Shadow mode"])
def backtest(req: BacktestRequest, request: Request):
    """Replays historical records against a gate or a draft policy. Each record counts as one decision."""
    p = need(request, roles=("owner", "admin"))
    feature(p["account_id"], "backtest")
    if len(req.records) > MAX_BACKTEST:
        raise S.CommerceError(400, "too_many_records", "At most {} records per call.".format(MAX_BACKTEST))
    q = S.quota_check(p["account_id"])
    quota = q["quota"]
    if quota is not None and not q["account"]["overage_enabled"] and q["used"] + len(req.records) > quota:
        raise S.CommerceError(429, "quota_exceeded", "This backtest would exceed your monthly quota.", quota=quota, used=q["used"])
    policy = CTX["load_policy"](req.gate_id, req.policy, "acct:" + p["account_id"])
    evaluate = CTX["evaluate"]
    t0 = time.perf_counter()
    matrix = {v: {o: 0 for o in S.VERDICTS + ("unknown",)} for v in S.VERDICTS}
    rules: Dict[str, int] = {}
    diffs = []
    for i, rec in enumerate(req.records):
        k = evaluate(rec.state, policy, req.strict)
        obs = S.normalize_outcome(rec.observed_outcome) if rec.observed_outcome is not None else None
        matrix[k["verdict"]][obs or "unknown"] += 1
        rules[k["rule_id"] or "-"] = rules.get(k["rule_id"] or "-", 0) + 1
        if obs and obs != k["verdict"] and len(diffs) < 200:
            diffs.append({"index": i, "id": rec.id, "verdict": k["verdict"], "observed": obs, "rule_id": k["rule_id"], "reason": k["reason"]})
    ms = (time.perf_counter() - t0) * 1000
    S.record_decision(p["account_id"], key_prefix=p.get("prefix"), gate_id=(policy or {}).get("gate_id"), verdict="REVIEW",
                      rule_id="backtest", reason="backtest of {} records".format(len(req.records)), latency_ms=ms, mode="shadow",
                      observed=None, policy_seal=(policy or {}).get("policy_seal"), state={}, external_id=None,
                      enqueue_review=False, count=len(req.records))
    labelled = sum(n for v in matrix.values() for o, n in v.items() if o != "unknown")
    agree = sum(matrix[v][v] for v in S.VERDICTS)
    return {"status": "success", "records": len(req.records), "elapsed_ms": round(ms, 3),
            "policy_id": (policy or {}).get("gate_id"), "policy_seal": (policy or {}).get("policy_seal"),
            "matrix": matrix, "agreement": round(agree / labelled, 4) if labelled else None,
            "stricter_than_you": matrix["DENY"]["ALLOW"] + matrix["REVIEW"]["ALLOW"],
            "looser_than_you": matrix["ALLOW"]["DENY"] + matrix["ALLOW"]["REVIEW"],
            "rules_fired": dict(sorted(rules.items(), key=lambda kv: -kv[1])), "differences": diffs}


# ----------------------------------------------------------------------------- reviews
class Resolve(BaseModel):
    action: str
    note: Optional[str] = Field(None, max_length=500)


@router.get("/v1/reviews", tags=["Human review"])
def reviews(request: Request, status: Optional[str] = "pending", limit: int = 100):
    p = need(request)
    feature(p["account_id"], "review_queue")
    return {"status": "success", "reviews": S.list_reviews(p["account_id"], status, limit)}


@router.get("/v1/reviews/{review_id}", tags=["Human review"])
def review(review_id: str, request: Request):
    p = need(request)
    return {"status": "success", "review": S.get_review(p["account_id"], review_id)}


@router.post("/v1/reviews/{review_id}/resolve", tags=["Human review"])
def resolve(review_id: str, req: Resolve, request: Request):
    p = need(request)
    feature(p["account_id"], "review_queue")
    r = S.resolve_review(p["account_id"], review_id, req.action, req.note, p.get("email") or p.get("prefix") or "api")
    webhooks.send(S.get_account(p["account_id"]), "review.resolved",
                  {k: r.get(k) for k in ("id", "decision_id", "gate_id", "status", "resolved_by", "resolved_at", "note", "external_id")})
    return {"status": "success", "review": r}


# ----------------------------------------------------------------------------- plans & statements
class PlanReq(BaseModel):
    plan: str
    cycle: str = "monthly"
    note: Optional[str] = Field(None, max_length=1000)


@router.post("/v1/account/plan-request", tags=["Plans & billing"])
def plan_request(req: PlanReq, request: Request):
    p = need(request, roles=("owner", "admin"), session_only=True)
    acc = S.get_account(p["account_id"])
    if req.plan == "kesif":
        if acc["plan"] in P.PAID_PLANS and (acc.get("plan_expires_at") or 0) > time.time():
            # paid period is kept; the account falls back to Explore when it ends (no renewal is charged)
            return {"status": "scheduled", "until": acc["plan_expires_at"], "account": S.account_view(p["account_id"])}
        out = S.set_plan(p["account_id"], "kesif", "monthly", p["email"])
        return {"status": "changed", "account": out}
    r = S.request_plan(p["account_id"], req.plan, req.cycle, req.note, p["email"])
    mail.plan_request(acc, r, p["email"])
    nxt = billing.provider().checkout(acc, req.plan, req.cycle)
    proforma_url = None
    if req.plan in P.PAID_PLANS and req.cycle in ("monthly", "yearly"):
        q_try = billing.quote_try(req.plan, req.cycle)
        b_info = json.loads(acc.get("billing_json") or "{}")
        unpaid_pay = S.create_payment(
            acc["id"], "plan", req.plan, req.cycle, q_try["net"], "0.00", q_try["total"],
            "bank_wire", p["email"], billing=b_info, currency="TRY"
        )
        proforma_url = "/v1/account/payments/{}/invoice.pdf".format(unpaid_pay["id"])
        nxt["proforma_invoice_pdf_url"] = proforma_url
        nxt["bank_accounts"] = P.CATALOG.get("bank_accounts", {})
    return {"status": "requested", "request": r, "payment": nxt, "proforma_invoice_pdf_url": proforma_url}


@router.get("/v1/account/plan-requests", tags=["Plans & billing"])
def plan_requests(request: Request):
    p = need(request, roles=("owner", "admin"))
    return {"status": "success", "requests": S.list_plan_requests(p["account_id"])}


@router.get("/v1/account/statements", tags=["Plans & billing"])
def statements(request: Request):
    p = need(request, roles=("owner", "admin"))
    cur = S.build_statement(S.get_account(p["account_id"]), S.period_of())
    return {"status": "success", "current_period_estimate": cur, "statements": S.list_statements(p["account_id"])}


# ----------------------------------------------------------------------------- card payments (iyzico)
CONSOLE = os.environ.get("ANSWERR_CONSOLE_URL", "https://answerr.me/pro/console/").rstrip("/") + "/"
WEBHOOK_LOG_MAX = 5 * 1024 * 1024


class CheckoutReq(BaseModel):
    plan: str
    cycle: str = "monthly"
    accept_preinfo: bool = False
    accept_distance_sale: bool = False
    lang: Optional[str] = "tr"


def _settle(token: str) -> Dict[str, Any]:
    """Settles a checkout token and sends the e-mails once (only on the first transition)."""
    before = S.get_payment(token=token)
    out = billing.iyzico().settle(token)
    pay = out.get("payment") or {}
    if out.get("result") == "paid" and out.get("first"):
        acc = S.get_account(pay["account_id"]) if pay.get("account_id") else None
        mail.payment_paid(acc, pay, json.loads(pay.get("billing_json") or "{}"))
    elif out.get("result") == "review" and before and before["status"] == "initiated":
        mail.payment_review(pay, pay.get("error") or "review")
    return out


@router.get("/v1/account/checkout/quote", tags=["Plans & billing"])
def checkout_quote(request: Request, plan: str, cycle: str = "monthly"):
    need(request, roles=("owner", "admin"), session_only=True)
    if plan not in P.PAID_PLANS or cycle not in ("monthly", "yearly"):
        raise S.CommerceError(400, "bad_plan", "Card payment is available for the Developer and Pro plans.")
    return {"status": "success", "plan": plan, "cycle": cycle, "currency": "TRY", **billing.quote_try(plan, cycle),
            "period_days": S.PAYMENT_PERIOD_DAYS[cycle], "card_payments": billing.provider().name == "iyzico"}


@router.post("/v1/account/checkout", tags=["Plans & billing"])
def checkout(req: CheckoutReq, request: Request):
    """Opens an iyzico payment page for one period of a paid plan (price in TRY, 20% VAT added).
    The plan is activated only after answerr verifies the result with iyzico."""
    p = need(request, roles=("owner", "admin"), session_only=True)
    if req.plan not in P.PAID_PLANS or req.cycle not in ("monthly", "yearly"):
        raise S.CommerceError(400, "bad_plan", "Card payment is available for the Developer and Pro plans.")
    if not (req.accept_preinfo and req.accept_distance_sale):
        raise S.CommerceError(400, "consent_required", "Accept the preliminary information form and the distance sales contract.")
    prov = billing.provider()
    if prov.name != "iyzico":
        raise S.CommerceError(409, "card_payments_off", "Card payments are not open yet; send a plan request for bank transfer.")
    acc = S.get_account(p["account_id"])
    if acc["status"] != "active" and acc["status"] != "suspended":
        raise S.CommerceError(403, "account_inactive", "This account cannot make payments.")
    buyer = billing.buyer_from_account(acc, p.get("email") or acc["email"], ip_of(request))
    q = billing.quote_try(req.plan, req.cycle)
    pay = S.create_payment(acc["id"], "plan", req.plan, req.cycle, q["net"], q["vat"], q["total"], "iyzico", p["email"],
                           billing=dict(buyer["billing"], consent_preinfo=True, consent_distance_sale=True,
                                        consent_ts=int(time.time()), legal_version=mail.legal_version()))
    plan = P.get(req.plan)
    name = "answerr {} — {}".format(plan["name_tr"], "yıllık (12 ay)" if req.cycle == "yearly" else "aylık (1 ay)")
    out = prov.initialize(pay, buyer, name, req.lang or acc.get("lang") or "tr")
    return {"status": "success", **out, **q}


class InstantCheckoutReq(BaseModel):
    email: str = Field(..., max_length=254)
    company: Optional[str] = Field(None, max_length=120)
    tax_id: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=30)
    plan: str = "kesif"
    cycle: str = "monthly"
    method: str = "free"
    tx_hash: Optional[str] = None
    network: Optional[str] = "base"
    token: Optional[str] = "USDC"
    currency: Optional[str] = "USD"
    accept_terms: bool = False
    kvkk_ack: bool = False
    marketing: bool = False
    lang: Optional[str] = "tr"
    website: Optional[str] = None


@router.post("/v1/checkout/instant", tags=["Plans & billing"])
def instant_checkout(req: InstantCheckoutReq, request: Request):
    """Fast B2B API provisioning: instant free key, verified crypto, iyzico card, or bank transfer proforma invoice."""
    email = (req.email or "").strip().lower()
    if not AM.valid_email(email):
        raise S.CommerceError(400, "bad_email", "Please enter a valid e-mail address.")
    if not (req.accept_terms and req.kvkk_ack):
        raise S.CommerceError(400, "consent_required", "Accept the terms of service and acknowledge the KVKK notice to continue.")
    human_check(request)
    if (req.website or "").strip():
        return {"status": "success", "message": "OK"}
    lang = req.lang if req.lang in ("tr", "en") else "tr"

    method = {"iyzico": "card"}.get(req.method, req.method)
    if method not in ("free", "crypto", "bank", "card"):
        raise S.CommerceError(400, "bad_method", "Choose free, card, bank or crypto.")
    target_plan = req.plan if req.plan in P.PLANS else "kesif"
    cycle = req.cycle if req.cycle in ("monthly", "yearly") else "monthly"
    if target_plan not in P.PAID_PLANS:
        target_plan, method = "kesif", "free"
    if method == "free":
        target_plan = "kesif"

    # An address that already has an account never gets a session from this public form: that would let anyone who
    # knows a customer's e-mail sign in as them. The owner receives a sign-in link instead.
    if S.member_of(email):
        tok = S.create_login_token(email, "login", {}, ip_of(request))
        mail.login_link(email, tok, "login", lang)
        return {"status": "login_link_sent", "message": (
            "Bu e-posta adresiyle bir hesap zaten var. Giriş bağlantısını e-postanıza gönderdik; ödemeyi konsoldaki "
            "Plan ve fatura bölümünden yapabilirsiniz." if lang == "tr" else
            "An account with this e-mail already exists. We sent a sign-in link to it; you can pay from Plan & billing in the console.")}

    b_info = {
        "legal_name": (req.company or "").strip()[:120],
        "invoice_email": email,
        "tax_id": (req.tax_id or "").strip()[:50],
        "address": (req.address or "").strip()[:200],
        "phone": (req.phone or "").strip()[:30],
    }
    b_info = {k: v for k, v in b_info.items() if v}
    consent = {"consent_preinfo": True, "consent_distance_sale": True, "consent_ts": int(time.time()),
               "legal_version": mail.legal_version()}

    # Crypto: verify on-chain first, so a failed or reused transaction never creates an account or a plan.
    ver = tok_key = None
    if method == "crypto":
        tx_clean = (req.tx_hash or "").strip().lower()
        if not tx_clean:
            raise S.CommerceError(400, "bad_tx_hash", "Please provide a valid transaction hash (TXID).")
        tok_key = "crypto:" + tx_clean
        if S.get_payment(token=tok_key):
            raise S.CommerceError(409, "tx_already_used", "This transaction hash has already been claimed.")
        q_usd = billing.quote_usd(target_plan, cycle)
        ver = billing.verify_crypto_payment(req.tx_hash, req.network or "base", req.token or "USDC", float(q_usd["total"]))

    # New accounts always start on Explore; a paid plan is set only by a verified payment.
    prov = S.instant_provision_account(email, company=req.company, plan="kesif", ip=ip_of(request), lang=lang,
                                       billing_info=b_info)
    acc_id, sess, raw_api_key = prov["account_id"], prov["session"], prov["api_key"]
    base = {"session": sess, "account_id": acc_id, "api_key": raw_api_key}

    if method == "free":
        return dict(base, status="success", plan="kesif", message=(
            "API anahtarınız anında tahsis edildi. Konsola hemen giriş yapabilirsiniz." if lang == "tr"
            else "Your API key has been provisioned. You can enter the console now."))

    if method == "crypto":
        pay = S.create_payment(acc_id, "plan", target_plan, cycle, q_usd["net"], "0.00", q_usd["total"],
                               "crypto_" + (req.network or "base").lower(), email, billing=dict(b_info, **consent),
                               currency=ver["currency"])
        try:
            S.set_payment_token(pay["id"], tok_key)
        except Exception:
            S.fail_payment(pay["id"], "tx_already_used")
            raise S.CommerceError(409, "tx_already_used", "This transaction hash has already been claimed.")
        out = S.complete_payment(pay["id"], ver["tx_hash"], 1, ver["network"][:16])
        if out.get("first"):
            mail.payment_paid(S.get_account(acc_id), out["payment"], dict(b_info, **consent))
        return dict(base, status="success", plan=target_plan, payment_id=pay["id"],
                    invoice_no=billing.invoice_number(out["payment"]),
                    invoice_pdf_url="/v1/account/payments/{}/invoice.pdf".format(pay["id"]),
                    message=("Ödemeniz zincir üstünde doğrulandı, planınız etkinleştirildi ve faturanız hazırlandı." if lang == "tr"
                             else "Payment verified on-chain, plan activated and invoice generated."))

    if method == "bank":
        curr = "TRY" if req.currency == "TRY" else "USD"
        q = billing.quote_try(target_plan, cycle) if curr == "TRY" else billing.quote_usd(target_plan, cycle)
        pay = S.create_payment(acc_id, "plan", target_plan, cycle, q["net"], q.get("vat", "0.00"), q["total"],
                               "bank_wire", email, billing=dict(b_info, **consent), currency=curr)
        r = S.request_plan(acc_id, target_plan, cycle, "havale/EFT proforma " + pay["id"], email)
        mail.plan_request(S.get_account(acc_id), r, email)
        return dict(base, status="success", plan="kesif", requested_plan=target_plan, payment_id=pay["id"],
                    invoice_no=billing.invoice_number(pay),
                    invoice_pdf_url="/v1/account/payments/{}/invoice.pdf".format(pay["id"]),
                    bank_accounts=P.CATALOG.get("bank_accounts", {}),
                    message=("Proforma faturanız hazır. Havale/EFT ulaştığında planınız etkinleşir; bu arada Keşif planıyla başlayabilirsiniz."
                             if lang == "tr" else
                             "Your proforma invoice is ready. The plan activates when the transfer arrives; meanwhile you can start on Explore."))

    # card: iyzico needs the full billing address; the console's Plan & billing view collects it and opens the payment page
    return dict(base, status="billing_required", plan="kesif", requested_plan=target_plan, cycle=cycle, next="billing",
                message=("Hesabınız açıldı. Kartla ödeme için fatura bilgilerinizi tamamlayıp ödeme sayfasına geçin." if lang == "tr"
                         else "Your account is ready. Complete your billing details to continue to the card payment page."))


class CryptoCheckoutReq(BaseModel):
    plan: str
    cycle: str = "monthly"
    tx_hash: str = Field(..., max_length=160)
    network: str = "base"
    token: str = "USDC"
    accept_preinfo: bool = False
    accept_distance_sale: bool = False


@router.post("/v1/account/crypto-checkout", tags=["Plans & billing"])
def crypto_checkout(req: CryptoCheckoutReq, request: Request):
    """Verifies an on-chain USDC/USDT transaction (Base, TRON TRC20, Ethereum, Arbitrum, BSC) and activates the plan immediately (0% KDV)."""
    p = need(request, roles=("owner", "admin"), session_only=True)
    if req.plan not in P.PAID_PLANS or req.cycle not in ("monthly", "yearly"):
        raise S.CommerceError(400, "bad_plan", "Crypto payment is available for the Developer and Pro plans.")
    if not (req.accept_preinfo and req.accept_distance_sale):
        raise S.CommerceError(400, "consent_required", "Accept the preliminary information form and the distance sales contract.")
    acc = S.get_account(p["account_id"])
    if acc["status"] not in ("active", "suspended"):
        raise S.CommerceError(403, "account_inactive", "This account cannot make payments.")
    tx_clean = (req.tx_hash or "").strip().lower()
    if not tx_clean:
        raise S.CommerceError(400, "bad_tx_hash", "Please provide a valid transaction hash (TXID).")
    tok_key = "crypto:" + tx_clean
    if S.get_payment(token=tok_key):
        raise S.CommerceError(409, "tx_already_used", "This transaction hash has already been claimed.")
    q_usd = billing.quote_usd(req.plan, req.cycle)
    ver = billing.verify_crypto_payment(req.tx_hash, req.network, req.token, float(q_usd["total"]))
    b_info = json.loads(acc.get("billing_json") or "{}")
    b_info.update({"consent_preinfo": True, "consent_distance_sale": True, "consent_ts": int(time.time()), "legal_version": mail.legal_version()})
    pay = S.create_payment(
        acc["id"], "plan", req.plan, req.cycle, q_usd["net"], "0.00", q_usd["total"],
        "crypto_" + req.network.lower(), p["email"], billing=b_info, currency=ver["currency"]
    )
    try:
        S.set_payment_token(pay["id"], tok_key)
    except Exception:
        S.fail_payment(pay["id"], "tx_already_used")
        raise S.CommerceError(409, "tx_already_used", "This transaction hash has already been claimed.")
    out = S.complete_payment(pay["id"], ver["tx_hash"], 1, ver["network"][:16])
    if out.get("first"):
        mail.payment_paid(acc, out["payment"], b_info)
    return {
        "status": "success",
        "result": "paid",
        "payment": out["payment"],
        "account": S.account_view(acc["id"]),
        "invoice_pdf_url": "/v1/account/payments/{}/invoice.pdf".format(pay["id"]),
    }


@router.get("/v1/account/payments/{payment_id}/invoice.pdf", tags=["Plans & billing"])
@router.get("/v1/invoice/{payment_id}.pdf", tags=["Plans & billing"])
def account_payment_invoice_pdf(payment_id: str, request: Request, token: Optional[str] = None):
    """PDF for one of the caller's payments (PAID invoice or UNPAID proforma). Needs the account's session or API key
    (Authorization header), an ITouch admin key, or — for plain links opened in a browser — ?token=<session>."""
    p = principal(request)
    if not p and token and token.startswith("ans_sess_"):
        sess_rec = S.resolve_session(token)
        if sess_rec:
            p = {"account_id": sess_rec["account_id"], "email": sess_rec["email"], "role": sess_rec["role"], "via": "session"}
    is_admin = False
    if not p:
        try:
            admin(request)
            is_admin = True
        except S.CommerceError:
            raise S.CommerceError(401, "unauthorized", "Sign in to download this invoice.")
    pay = S.get_payment(pid=payment_id)
    if not pay or (not is_admin and pay.get("account_id") != p["account_id"]):
        raise S.CommerceError(404, "no_payment", "Payment or proforma invoice record not found.")
    acc = S.get_account(pay["account_id"]) if pay.get("account_id") else None
    pdf_bytes = billing.generate_answerr_invoice_pdf(acc, pay)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'inline; filename="answerr-invoice-{}.pdf"'.format(payment_id), "Cache-Control": "no-store",
                 "Referrer-Policy": "no-referrer"},
    )


@router.get("/v1/account/payments", tags=["Plans & billing"])
def account_payments(request: Request):
    p = need(request, roles=("owner", "admin"))
    keep = ("id", "kind", "plan", "cycle", "net_try", "vat_try", "total_try", "currency", "status", "card_last4",
            "created_at", "paid_at", "period_start", "period_end")
    return {"status": "success", "payments": [{k: r.get(k) for k in keep} for r in S.list_payments(p["account_id"], 100)]}


async def _form_body(request: Request) -> Dict[str, str]:
    """application/x-www-form-urlencoded without python-multipart (not installed on every host)."""
    from urllib.parse import parse_qs
    try:
        raw = (await request.body())[:20000].decode("utf-8", "replace")
        return {k: v[0] for k, v in parse_qs(raw).items() if v}
    except Exception:
        return {}


@router.api_route("/v1/billing/iyzico/callback", methods=["GET", "POST"], tags=["Plans & billing"])
async def iyzico_callback(request: Request):
    """Browser return from the iyzico payment page. The posted token is only a hint: the result is retrieved from iyzico
    server-to-server and checked before anything is activated. The token is never put in the redirect URL."""
    token = None
    if request.method == "POST":
        token = (await _form_body(request)).get("token")
    token = (token or request.query_params.get("token") or "").strip()[:200]
    result, ref = "unknown", ""
    if token:
        try:
            out = _settle(token)
            result = out.get("result", "error")
            ref = (out.get("payment") or {}).get("id") or ""
        except S.CommerceError:
            result = "error"
    dest = CONSOLE + "?payment={}{}#billing".format(result, "&ref=" + ref if ref else "")
    return Response(status_code=303, headers={"Location": dest, "Cache-Control": "no-store"})


def _log_webhook(entry: Dict[str, Any]) -> None:
    path = os.path.join(os.path.dirname(S.db_path()) or ".", "iyzico_webhooks.jsonl")
    try:
        if os.path.exists(path) and os.path.getsize(path) > WEBHOOK_LOG_MAX:
            os.replace(path, path + ".1")
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False)[:4000] + "\n")
    except Exception:
        pass


@router.api_route("/v1/billing/iyzico/webhook", methods=["GET", "POST"], tags=["Plans & billing"])
@router.api_route("/v1/billing/iyzico/webhoc", methods=["GET", "POST"], include_in_schema=False)
async def iyzico_webhook(request: Request):
    """iyzico merchant notification. The payload is never trusted: the token it names is re-checked with iyzico.
    Always answers 200 so iyzico does not retry for events answerr does not handle."""
    if request.method != "POST":
        return {"status": "success"}
    body: Dict[str, Any] = {}
    try:
        body = await request.json()
    except Exception:
        body = await _form_body(request)
    if not isinstance(body, dict):
        body = {}
    sig = request.headers.get("x-iyz-signature-v3") or ""
    prov = billing.iyzico()
    signed = prov.verify_webhook_v3(body, sig) if sig else None
    token = str(body.get("token") or "").strip()[:200]
    if not token and body.get("paymentConversationId"):
        pay = S.get_payment(conversation_id=str(body["paymentConversationId"])[:80])
        token = (pay or {}).get("token") or ""
    result = "ignored"
    if token and signed is not False and prov.card_payments:
        try:
            result = _settle(token).get("result", "error")
        except S.CommerceError:
            result = "error"
    elif signed is False:
        result = "bad_signature"
    _log_webhook({"ts": int(time.time()), "event": str(body.get("iyziEventType") or "")[:60],
                  "status": str(body.get("status") or "")[:30], "conversation": str(body.get("paymentConversationId") or "")[:80],
                  "signed": signed, "result": result})
    return {"status": "success"}


# ----------------------------------------------------------------------------- admin
class AdminCreate(BaseModel):
    email: str
    company: Optional[str] = None
    plan: str = "kesif"
    cycle: str = "monthly"
    lang: str = "tr"


class AdminPlan(BaseModel):
    plan: str
    cycle: str = "monthly"
    expires_days: Optional[int] = None


class AdminStatus(BaseModel):
    status: str


class StatementsRun(BaseModel):
    period: Optional[str] = None


class StatementMark(BaseModel):
    status: str
    e_invoice_no: Optional[str] = Field(None, max_length=60)
    provider: Optional[str] = Field(None, max_length=30)
    provider_ref: Optional[str] = Field(None, max_length=120)


@router.get("/v1/admin/metrics", tags=["Admin"])
def a_metrics(request: Request):
    admin(request)
    return {"status": "success", "metrics": S.admin_metrics()}


@router.get("/v1/admin/accounts", tags=["Admin"])
def a_accounts(request: Request):
    admin(request)
    return {"status": "success", "accounts": S.admin_accounts()}


@router.post("/v1/admin/accounts", tags=["Admin"])
def a_create(req: AdminCreate, request: Request):
    """Onboards an account directly (enterprise, pilot, smoke tests). Returns its first API key once."""
    who = admin(request)
    email = req.email.strip().lower()
    if not AM.valid_email(email):
        raise S.CommerceError(400, "bad_email", "Invalid e-mail.")
    if S.member_of(email):
        raise S.CommerceError(409, "member_exists", "This address already belongs to an account.")
    tok = S.create_login_token(email, "signup", {"company": req.company, "lang": req.lang, "terms_version": S.TERMS_VERSION},
                               ip_of(request))
    out = S.verify_login(tok, ip_of(request))
    S.revoke_session(out["session"])
    acc = S.set_plan(out["account_id"], req.plan, req.cycle, who) if req.plan != "kesif" else S.account_view(out["account_id"])
    return {"status": "created", "account": acc, "api_key": out.get("api_key")}


@router.get("/v1/admin/accounts/{account_id}", tags=["Admin"])
def a_account(account_id: str, request: Request):
    admin(request)
    return {"status": "success", "account": S.account_view(account_id), "members": S.list_members(account_id),
            "keys": S.list_keys(account_id), "events": S.account_events(account_id, 50),
            "statements": S.list_statements(account_id), "plan_requests": S.list_plan_requests(account_id)}


@router.post("/v1/admin/accounts/{account_id}/plan", tags=["Admin"])
def a_plan(account_id: str, req: AdminPlan, request: Request):
    who = admin(request)
    exp = time.time() + req.expires_days * 86400 if req.expires_days else None
    return {"status": "success", "account": S.set_plan(account_id, req.plan, req.cycle, who, exp)}


@router.post("/v1/admin/accounts/{account_id}/status", tags=["Admin"])
def a_status(account_id: str, req: AdminStatus, request: Request):
    who = admin(request)
    S.set_status(account_id, req.status, who)
    return {"status": "success", "account": S.account_view(account_id)}


@router.delete("/v1/admin/accounts/{account_id}", tags=["Admin"])
def a_delete(account_id: str, request: Request):
    who = admin(request)
    if not S.delete_account(account_id, who):
        raise S.CommerceError(404, "no_account", "Account not found.")
    if "drop_tenant_gates" in CTX:
        CTX["drop_tenant_gates"]("acct:" + account_id)
    return {"status": "deleted", "account_id": account_id}


@router.get("/v1/admin/plan-requests", tags=["Admin"])
def a_plan_requests(request: Request, status: Optional[str] = "pending"):
    admin(request)
    return {"status": "success", "requests": S.list_plan_requests(None, status)}


@router.post("/v1/admin/plan-requests/{request_id}/approve", tags=["Admin"])
def a_approve(request_id: str, request: Request):
    who = admin(request)
    r = next((x for x in S.list_plan_requests(None, "pending") if x["id"] == request_id), None)
    if not r:
        raise S.CommerceError(404, "no_request", "Pending request not found.")
    return {"status": "success", "account": S.set_plan(r["account_id"], r["plan"], r["cycle"], who, request_id=request_id)}


@router.post("/v1/admin/plan-requests/{request_id}/reject", tags=["Admin"])
def a_reject(request_id: str, request: Request):
    who = admin(request)
    S.reject_plan_request(request_id, who)
    return {"status": "success"}


@router.post("/v1/admin/statements/generate", tags=["Admin"])
def a_statements(req: StatementsRun, request: Request):
    who = admin(request)
    import re
    if req.period and not re.match(r"^\d{4}-\d{2}$", req.period):
        raise S.CommerceError(400, "bad_period", "period must look like 2026-10.")
    # default: the previous calendar month (Türkiye time)
    first = time.mktime(time.strptime(S.period_of() + "-01", "%Y-%m-%d"))
    period = req.period or S.period_of(first - 86400)
    return {"status": "success", "period": period, "statements": S.generate_statements(period, who)}


@router.get("/v1/admin/statements", tags=["Admin"])
def a_statement_list(request: Request, period: Optional[str] = None):
    admin(request)
    return {"status": "success", "statements": S.list_statements(None, period)}


@router.post("/v1/admin/statements/{statement_id}/mark", tags=["Admin"])
def a_mark(statement_id: str, req: StatementMark, request: Request):
    who = admin(request)
    return {"status": "success", "statement": S.mark_statement(statement_id, req.status, who, req.e_invoice_no, req.provider, req.provider_ref)}


class AdminTestPay(BaseModel):
    amount_try: str = "1.00"
    legal_name: str = Field("ITouch Bilişim Sistemleri Ltd. Şti.", max_length=120)
    contact_name: str = Field("Volkan Dağlı", max_length=120)
    email: str = Field(..., max_length=254)
    phone: str = Field("+908503115203", max_length=20)
    address: str = Field("Balcalı Mah. Güney Kampüs/5 Sk. No: 4/1 İç Kapı No: 26, Sarıçam", max_length=200)
    city: str = "Adana"
    tax_id: str = Field("4690944558", max_length=11)


@router.get("/v1/admin/payments", tags=["Admin"])
def a_payments(request: Request, account_id: Optional[str] = None, limit: int = 200):
    admin(request)
    return {"status": "success", "card_payments": billing.provider().name == "iyzico",
            "payments": S.list_payments(account_id, max(1, min(limit, 1000)))}


@router.post("/v1/admin/payments/{payment_id}/recheck", tags=["Admin"])
def a_recheck_payment(payment_id: str, request: Request):
    """Asks iyzico again for a payment that is initiated or held for review (e.g. after a fix) and settles it."""
    admin(request)
    pay = S.get_payment(payment_id)
    if not pay or not pay.get("token"):
        raise S.CommerceError(404, "no_payment", "Payment not found.")
    out = _settle(pay["token"])
    return {"status": "success", "result": out.get("result"), "payment": S.get_payment(payment_id)}


class AdminRefund(BaseModel):
    revoke_plan: bool = True
    note: Optional[str] = Field(None, max_length=300)


@router.post("/v1/admin/payments/{payment_id}/refunded", tags=["Admin"])
def a_refunded(payment_id: str, req: AdminRefund, request: Request):
    """Record a cancel or refund made in the iyzico panel; by default the paid period is taken back."""
    by = admin(request)
    return {"status": "success", **S.mark_refunded(payment_id, by, req.revoke_plan, req.note)}


@router.post("/v1/admin/payments/test", tags=["Admin"])
def a_test_payment(req: AdminTestPay, request: Request):
    """A small test charge through iyzico (no plan is changed). Works even while customer card payments are off,
    so the live integration can be proven before it is opened. Refund it from the iyzico panel afterwards."""
    by = admin(request)
    amt = billing.money(req.amount_try)
    if not (billing.Decimal("1.00") <= billing.Decimal(amt) <= billing.Decimal("10.00")):
        raise S.CommerceError(400, "bad_amount", "Test amount must be between 1.00 and 10.00 TRY.")
    prov = billing.iyzico()
    acc = {"id": "itouch-test", "email": req.email, "billing_json": json.dumps(
        {"legal_name": req.legal_name, "contact_name": req.contact_name, "tax_id": req.tax_id, "address": req.address, "city": req.city, "phone": req.phone,
         "invoice_email": req.email}, ensure_ascii=False)}
    buyer = billing.buyer_from_account(acc, req.email, ip_of(request))
    pay = S.create_payment(None, "test", None, None, amt, "0.00", amt, "iyzico", by, billing=buyer["billing"])
    return {"status": "success", **prov.initialize(pay, buyer, "answerr entegrasyon testi", "tr")}


@router.post("/v1/admin/purge", tags=["Admin"])
def a_purge(request: Request):
    admin(request)
    return {"status": "success", "removed": S.purge()}


def error_response(e: S.CommerceError) -> JSONResponse:
    body = {"status": "error", "error": e.code, "message": e.message}
    body.update(e.extra)
    headers = {"Retry-After": "3600"} if e.code == "quota_exceeded" else None
    return JSONResponse(status_code=e.status, content=body, headers=headers)
