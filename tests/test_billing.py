"""Card payments through the iyzico Checkout Form (iyzico is mocked; no network)."""
import base64
import hashlib
import hmac
import json
from urllib.parse import parse_qs, urlparse

import pytest

from test_commerce import ADMIN, H_ADMIN, auth, client, signup  # noqa: F401  (fixture)

BILLING = {"legal_name": "Örnek Yazılım A.Ş.", "tax_id": "1234567890", "tax_office": "Seyhan", "address": "Atatürk Cd. 1",
           "city": "Adana", "phone": "0532 000 00 00", "invoice_email": "fatura@example.com"}


class FakeIyzico:
    def __init__(self):
        self.calls, self.sessions, self.override = [], {}, {}

    def __call__(self, prov, path, payload):
        self.calls.append((path, payload))
        if path.endswith("/initialize/auth/ecom"):
            tok = "tok-{}".format(len(self.sessions) + 1)
            self.sessions[tok] = payload
            return {"status": "success", "token": tok, "paymentPageUrl": "https://sandbox-cpp.iyzipay.com?token=" + tok}
        if path.endswith("/auth/ecom/detail"):
            init = self.sessions.get(payload["token"])
            if not init:
                return {"status": "failure", "errorMessage": "token not found"}
            res = {"status": "success", "paymentStatus": "SUCCESS", "paymentId": "2900" + payload["token"][-1],
                   "conversationId": payload.get("conversationId"), "basketId": init["basketId"], "price": float(init["price"]),
                   "paidPrice": float(init["paidPrice"]), "currency": "TRY", "fraudStatus": 1, "lastFourDigits": "0008"}
            res.update(self.override)
            return res
        return {"status": "failure"}


@pytest.fixture()
def iz(client, monkeypatch):
    monkeypatch.setenv("IYZICO_API_KEY", "sandbox-key")
    monkeypatch.setenv("IYZICO_SECRET_KEY", "sandbox-secret")
    monkeypatch.setenv("ANSWERR_PAYMENT_PROVIDER", "iyzico")
    from commerce import billing
    fake = FakeIyzico()
    monkeypatch.setattr(billing.IyzicoProvider, "post", lambda self, path, payload: fake(self, path, payload))
    client.fake = fake
    return client


def ready(c):
    s, _, acc = signup(c)
    r = c.patch("/v1/account", json={"billing": BILLING}, headers=auth(s))
    assert r.status_code == 200, r.text
    return s, acc


def buy(c, s, plan="gelistirici", cycle="monthly"):
    return c.post("/v1/account/checkout", json={"plan": plan, "cycle": cycle, "accept_preinfo": True,
                                                "accept_distance_sale": True}, headers=auth(s))


def callback(c, token):
    r = c.post("/v1/billing/iyzico/callback", data={"token": token}, follow_redirects=False)
    assert r.status_code == 303
    loc = r.headers["location"]
    assert "token=" not in loc
    return parse_qs(urlparse(loc).query)


def test_quote_adds_vat():
    from commerce import billing
    assert billing.quote_try("gelistirici", "monthly") == {"net": "1449.00", "vat": "289.80", "total": "1738.80", "vat_rate": "0.2"}
    assert billing.quote_try("pro", "yearly")["total"] == "58305.60"      # 4049 × 12 × 1.2


def test_signature_matches_iyzico_spec():
    from commerce import billing
    p = billing.IyzicoProvider.__new__(billing.IyzicoProvider)
    p.api_key, p.secret = "k", "s"
    h = p.auth_header("/payment/test", '{"a":1}', random_key="123")
    raw = base64.b64decode(h["Authorization"].split(" ", 1)[1]).decode()
    sig = hmac.new(b"s", b'123/payment/test{"a":1}', hashlib.sha256).hexdigest()
    assert raw == "apiKey:k&randomKey:123&signature:" + sig and h["x-iyzi-rnd"] == "123"


def test_card_payments_off_by_default(client):
    s, _ = ready(client)
    r = buy(client, s)
    assert r.status_code == 409 and r.json()["error"] == "card_payments_off"


def test_consent_and_billing_required(iz):
    s, _, _ = signup(iz)
    r = iz.post("/v1/account/checkout", json={"plan": "pro"}, headers=auth(s))
    assert r.json()["error"] == "consent_required"
    r = buy(iz, s)
    assert r.status_code == 400 and r.json()["error"] == "billing_incomplete"
    assert buy(iz, ready(iz)[0], plan="kurumsal").json()["error"] == "bad_plan"


def test_successful_payment_activates_plan_once(iz):
    s, acc = ready(iz)
    r = buy(iz, s)
    assert r.status_code == 200, r.text
    b = r.json()
    assert b["mode"] == "redirect" and b["total"] == "1738.80"
    path, init = iz.fake.calls[-1]
    assert init["price"] == init["paidPrice"] == "1738.80" and init["currency"] == "TRY"
    assert init["basketItems"][0]["itemType"] == "VIRTUAL" and init["enabledInstallments"] == [1]
    assert init["buyer"]["gsmNumber"] == "+905320000000" and "shippingAddress" not in init
    q = callback(iz, "tok-1")
    assert q["payment"] == ["paid"]
    a = iz.get("/v1/account", headers=auth(s)).json()["account"]
    assert a["plan"] == "gelistirici" and a["plan_expires_at"] > 0
    first_end = a["plan_expires_at"]
    n_mail = len(iz.mail.OUTBOX)
    # replays (callback again, webhook) change nothing and send nothing
    callback(iz, "tok-1")
    iz.post("/v1/billing/iyzico/webhook", json={"token": "tok-1", "iyziEventType": "CHECKOUT_FORM_AUTH", "status": "SUCCESS"})
    assert iz.get("/v1/account", headers=auth(s)).json()["account"]["plan_expires_at"] == first_end
    assert len(iz.mail.OUTBOX) == n_mail
    subjects = [m["Subject"] for m in iz.mail.OUTBOX]
    assert any("Ödeme alındı" in x for x in subjects) and any("ödemeniz alındı" in x for x in subjects)
    note = next(m for m in iz.mail.OUTBOX if "Ödeme alındı" in m["Subject"]).get_content()
    assert "1234567890" in note and "1.738,80 ₺" in note and "0008" in note
    pays = iz.get("/v1/account/payments", headers=auth(s)).json()["payments"]
    assert pays[0]["status"] == "paid" and "billing_json" not in pays[0] and "token" not in pays[0]


def test_renewal_extends_from_current_end(iz):
    s, _ = ready(iz)
    buy(iz, s); callback(iz, "tok-1")
    end1 = iz.get("/v1/account", headers=auth(s)).json()["account"]["plan_expires_at"]
    buy(iz, s); callback(iz, "tok-2")
    end2 = iz.get("/v1/account", headers=auth(s)).json()["account"]["plan_expires_at"]
    assert abs((end2 - end1) - 31 * 86400) < 5


def test_failed_and_tampered_payments_do_not_activate(iz):
    s, _ = ready(iz)
    buy(iz, s)
    iz.fake.override = {"paymentStatus": "FAILURE", "errorMessage": "Kart limiti yetersiz"}
    assert callback(iz, "tok-1")["payment"] == ["failed"]
    buy(iz, s)
    iz.fake.override = {"price": 1.0, "paidPrice": 1.0}
    assert callback(iz, "tok-2")["payment"] == ["review"]
    buy(iz, s)
    iz.fake.override = {"fraudStatus": 0}
    assert callback(iz, "tok-3")["payment"] == ["review"]
    assert iz.get("/v1/account", headers=auth(s)).json()["account"]["plan"] == "kesif"
    assert sum("incelemede" in m["Subject"] for m in iz.mail.OUTBOX) == 2


def test_forged_requests_are_ignored(iz):
    s, _ = ready(iz)
    assert callback(iz, "FAKE")["payment"] == ["unknown"]
    r = iz.post("/v1/billing/iyzico/webhook", json={"token": "FAKE", "status": "SUCCESS"})
    assert r.status_code == 200
    buy(iz, s)
    r = iz.post("/v1/billing/iyzico/webhook", json={"token": "tok-1", "status": "SUCCESS"},
                headers={"X-IYZ-SIGNATURE-V3": "00" * 32})
    assert r.status_code == 200
    assert iz.get("/v1/account", headers=auth(s)).json()["account"]["plan"] == "kesif"
    assert iz.get("/v1/billing/iyzico/webhook").status_code == 200


def test_signed_webhook_settles(iz):
    s, _ = ready(iz)
    buy(iz, s)
    conv = iz.fake.sessions["tok-1"]["conversationId"]
    body = {"iyziEventType": "CHECKOUT_FORM_AUTH", "iyziPaymentId": 29001, "token": "tok-1",
            "paymentConversationId": conv, "status": "SUCCESS"}
    msg = "sandbox-secret" + "CHECKOUT_FORM_AUTH" + "29001" + "tok-1" + conv + "SUCCESS"
    sig = hmac.new(b"sandbox-secret", msg.encode(), hashlib.sha256).hexdigest()
    assert iz.post("/v1/billing/iyzico/webhook", json=body, headers={"X-IYZ-SIGNATURE-V3": sig}).status_code == 200
    assert iz.get("/v1/account", headers=auth(s)).json()["account"]["plan"] == "gelistirici"


def test_admin_test_payment_works_while_customer_payments_off(client, monkeypatch):
    monkeypatch.setenv("IYZICO_API_KEY", "k")
    monkeypatch.setenv("IYZICO_SECRET_KEY", "s")
    from commerce import billing
    fake = FakeIyzico()
    monkeypatch.setattr(billing.IyzicoProvider, "post", lambda self, path, payload: fake(self, path, payload))
    assert client.post("/v1/admin/payments/test", json={"email": "a@b.co"}).status_code == 401
    assert client.post("/v1/admin/payments/test", json={"email": "a@b.co", "amount_try": "500"}, headers=H_ADMIN).status_code == 400
    r = client.post("/v1/admin/payments/test", json={"email": "a@b.co"}, headers=H_ADMIN)
    assert r.status_code == 200 and r.json()["total_try"] == "1.00"
    assert callback(client, "tok-1")["payment"] == ["paid"]
    p = client.get("/v1/admin/payments", headers=H_ADMIN).json()
    assert p["card_payments"] is False and p["payments"][0]["kind"] == "test" and p["payments"][0]["status"] == "paid"


def test_renewal_reminder_sent_once(iz):
    s, acc = ready(iz)
    buy(iz, s); callback(iz, "tok-1")
    st = iz.store
    with st.tx() as c:
        c.execute("UPDATE accounts SET plan_expires_at = ? WHERE id = ?", (st.now() + 3 * 86400, acc))
    assert iz.mod.renewal_reminders() == 1
    assert iz.mod.renewal_reminders() == 0
    assert "bitiyor" in iz.mail.OUTBOX[-1]["Subject"]


def test_downgrade_keeps_paid_period(iz):
    s, _ = ready(iz)
    buy(iz, s); callback(iz, "tok-1")
    r = iz.post("/v1/account/plan-request", json={"plan": "kesif"}, headers=auth(s))
    assert r.json()["status"] == "scheduled"
    assert iz.get("/v1/account", headers=auth(s)).json()["account"]["plan"] == "gelistirici"


def test_public_plans_flag(iz):
    b = iz.get("/v1/plans").json()
    assert b["card_payments"] is True and b["plans"]["pro"]["price_monthly_try"] == 4899


def test_admin_recheck_settles_held_payment(iz):
    s, _ = ready(iz)
    buy(iz, s)
    iz.fake.override = {"fraudStatus": 0}
    assert callback(iz, "tok-1")["payment"] == ["review"]
    iz.fake.override = {}
    pid = iz.get("/v1/account/payments", headers=auth(s)).json()["payments"][0]["id"]
    r = iz.post("/v1/admin/payments/{}/recheck".format(pid), headers=H_ADMIN)
    assert r.json()["result"] == "paid"
    assert iz.get("/v1/account", headers=auth(s)).json()["account"]["plan"] == "gelistirici"


def test_login_for_unknown_address_mails_signup_hint(client):
    r = client.post("/v1/auth/login", json={"email": "nobody@example.com"})
    assert r.status_code == 200 and r.json()["status"] == "sent"
    assert "hesap yok" in client.mail.OUTBOX[-1]["Subject"]
