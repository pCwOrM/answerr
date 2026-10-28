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
    assert billing.quote_try("gelistirici", "monthly") == {"net": "1449.00", "vat": "0.00", "total": "1449.00", "vat_rate": "0.0"}
    assert billing.quote_try("pro", "yearly")["total"] == "48588.00"      # 4049 × 12 (%0 KDV)


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
    assert b["mode"] == "redirect" and b["total"] == "1449.00"
    path, init = iz.fake.calls[-1]
    assert init["price"] == init["paidPrice"] == "1449.00" and init["currency"] == "TRY"
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
    assert any("Ödeme alındı" in x for x in subjects) and any("sipariş onayı" in x for x in subjects)
    conf = next(m for m in iz.mail.OUTBOX if "sipariş onayı" in m["Subject"])
    names = [a.get_filename() for a in conf.iter_attachments()]
    assert names == ["On_Bilgilendirme_Formu_2026-10-22.txt", "Mesafeli_Satis_Sozlesmesi_2026-10-22.txt"]
    text = conf.get_body(preferencelist=("plain",)).get_content()
    assert "1.449,00 ₺" in text and "metin sürümü 2026-10-22" in text and "m.15/1-ğ" in text
    note = next(m for m in iz.mail.OUTBOX if "Ödeme alındı" in m["Subject"]).get_content()
    assert "1234567890" in note and "1.449,00 ₺" in note and "0008" in note
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


def test_contact_person_is_the_buyer(iz):
    s, _, _ = signup(iz)
    iz.patch("/v1/account", json={"billing": dict(BILLING, contact_name="Ayşe Yılmaz")}, headers=auth(s))
    buy(iz, s)
    b = iz.fake.calls[-1][1]
    assert (b["buyer"]["name"], b["buyer"]["surname"]) == ("Ayşe", "Yılmaz")
    assert b["billingAddress"]["contactName"] == BILLING["legal_name"]


def test_refund_takes_back_the_period(iz):
    s, acc = ready(iz)
    buy(iz, s); callback(iz, "tok-1")
    pid = iz.get("/v1/account/payments", headers=auth(s)).json()["payments"][0]["id"]
    r = iz.post("/v1/admin/payments/{}/refunded".format(pid), json={"note": "iptal"}, headers=H_ADMIN)
    assert r.status_code == 200 and r.json()["plan_revoked"] is True
    a = iz.get("/v1/account", headers=auth(s)).json()["account"]
    assert a["plan"] == "kesif"
    assert iz.post("/v1/admin/payments/{}/refunded".format(pid), json={}, headers=H_ADMIN).status_code == 409



def test_crypto_checkout_activates_plan(client, monkeypatch):
    from commerce import billing
    monkeypatch.setattr(
        billing,
        "verify_crypto_payment",
        lambda tx_hash, network, token, expected_usd, not_before=None: {
            "verified": True,
            "amount": expected_usd,
            "currency": "USDC",
            "network": "Base Mainnet",
            "tx_hash": tx_hash.lower(),
        },
    )
    s, acc = ready(client)
    tx = "0x" + "a" * 64
    # no quote -> refused
    r0 = client.post("/v1/account/crypto-checkout", json={"plan": "pro", "cycle": "monthly", "tx_hash": tx, "accept_preinfo": True,
                                                         "accept_distance_sale": True}, headers=auth(s))
    assert r0.status_code == 400 and r0.json()["error"] == "quote_required"
    q = client.post("/v1/checkout/crypto-quote", json={"plan": "pro", "cycle": "monthly"}, headers=auth(s)).json()
    assert q["status"] == "success" and 99.0 < float(q["amount"]) < 100.0
    r = client.post(
        "/v1/account/crypto-checkout",
        json={
            "plan": "pro",
            "cycle": "monthly",
            "quote_id": q["quote_id"],
            "tx_hash": tx,
            "network": "base",
            "token": "USDC",
            "accept_preinfo": True,
            "accept_distance_sale": True,
        },
        headers=auth(s),
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["result"] == "paid" and data["payment"]["total_try"] == q["amount"] and data["payment"]["currency"] == "USDC"
    assert data["account"]["plan"] == "pro"
    # Replaying the same tx_hash is rejected with 409
    r2 = client.post(
        "/v1/account/crypto-checkout",
        json={
            "plan": "pro",
            "cycle": "monthly",
            "quote_id": q["quote_id"],
            "tx_hash": tx,
            "network": "base",
            "token": "USDC",
            "accept_preinfo": True,
            "accept_distance_sale": True,
        },
        headers=auth(s),
    )
    assert r2.status_code == 409 and r2.json()["error"] == "tx_already_used"


def test_crypto_rejects_old_treasury_transfers(monkeypatch):
    """An old USDC transfer into the treasury wallet must not buy a plan; a fresh one does."""
    import time as _t
    from commerce import billing, store as S
    dep = "0x" + billing.EVM_DEPOSIT_ADDRESS.lower().replace("0x", "").zfill(64)
    receipt = {"status": "0x1", "blockNumber": "0x10", "logs": [{"address": billing.EVM_CHAINS["base"]["tokens"]["USDC"][0],
               "topics": [billing.ERC20_TRANSFER_TOPIC, "0x" + "0" * 64, dep], "data": hex(99 * 10 ** 6)}]}
    age = {"ts": _t.time() - 10 * 86400}

    class R:
        def __init__(self, body): self.body = body
        def read(self): return self.body
        def __enter__(self): return self
        def __exit__(self, *a): return False

    def fake_urlopen(req, timeout=None):
        m = json.loads(req.data.decode())["method"]
        res = receipt if m == "eth_getTransactionReceipt" else {"timestamp": hex(int(age["ts"]))}
        return R(json.dumps({"result": res}).encode())
    monkeypatch.setattr(billing.urllib.request, "urlopen", fake_urlopen)
    tx = "0x" + "d" * 64
    with pytest.raises(S.CommerceError) as e:
        billing.verify_crypto_payment(tx, "base", "USDC", 99.0)
    assert e.value.code == "tx_too_old"
    age["ts"] = _t.time() - 600
    assert billing.verify_crypto_payment(tx, "base", "USDC", 99.0)["verified"] is True



def test_crypto_quotes_stop_front_running(client, monkeypatch):
    """Open quotes never share an amount, a quote can only be used by its owner, and a transfer made before the quote
    was issued is refused — so a stranger cannot claim someone else's payment."""
    import time
    from commerce import billing, store as S
    qa = billing.crypto_quote(None, "alice@example.com", "pro", "monthly")
    qb = billing.crypto_quote(None, "attacker@example.com", "pro", "monthly")
    assert qa["amount"] != qb["amount"] and all(99 < float(x["amount"]) < 100 for x in (qa, qb))
    amounts = {billing.crypto_quote(None, "u%d@example.com" % i, "pro", "monthly")["amount"] for i in range(40)}
    assert len(amounts) == 40 and qa["amount"] not in amounts
    dep = "0x" + billing.EVM_DEPOSIT_ADDRESS.lower().replace("0x", "").zfill(64)
    when = {"ts": time.time()}

    def receipt_for(amount):
        return {"status": "0x1", "blockNumber": "0x10", "logs": [{"address": billing.EVM_CHAINS["base"]["tokens"]["USDC"][0],
                "topics": [billing.ERC20_TRANSFER_TOPIC, "0x" + "0" * 64, dep], "data": hex(int(round(float(amount) * 10 ** 6)))}]}
    cur = {"r": receipt_for(qa["amount"])}

    class R:
        def __init__(self, b): self.b = b
        def read(self): return self.b
        def __enter__(self): return self
        def __exit__(self, *a): return False
    monkeypatch.setattr(billing.urllib.request, "urlopen", lambda req, timeout=None: R(json.dumps({"result": cur["r"] if "eth_getTransactionReceipt" in req.data.decode() else {"timestamp": hex(int(when["ts"]))}}).encode()))
    tx = "0x" + "e" * 64
    # attacker's own quote has a different amount
    with pytest.raises(S.CommerceError) as e:
        billing.verify_crypto_payment(tx, "base", "USDC", float(qb["amount"]), not_before=qb["created_at"])
    assert e.value.code == "mismatched_amount"
    # a transfer older than the quote is refused even with the right amount
    when["ts"] = qa["created_at"] - 3600
    with pytest.raises(S.CommerceError) as e:
        billing.verify_crypto_payment(tx, "base", "USDC", float(qa["amount"]), not_before=qa["created_at"] - 120)
    assert e.value.code == "tx_before_quote"
    when["ts"] = time.time()
    assert billing.verify_crypto_payment(tx, "base", "USDC", float(qa["amount"]), not_before=qa["created_at"] - 120)["verified"]
    # through the API the attacker cannot use alice's quote
    r = client.post("/v1/checkout/instant", json={"email": "attacker@example.com", "plan": "pro", "method": "crypto", "tx_hash": tx,
                                                  "quote_id": qa["quote_id"], "accept_terms": True, "kvkk_ack": True})
    assert r.status_code == 403 and r.json()["error"] == "quote_not_yours"
    r = client.post("/v1/checkout/instant", json={"email": "alice@example.com", "plan": "pro", "method": "crypto", "tx_hash": tx,
                                                  "quote_id": qa["quote_id"], "accept_terms": True, "kvkk_ack": True})
    assert r.status_code == 200 and r.json()["plan"] == "pro", r.text
    # the used amount is free again for new quotes later; the quote itself cannot be reused
    r = client.post("/v1/checkout/instant", json={"email": "alice2@example.com", "plan": "pro", "method": "crypto", "tx_hash": "0x" + "f" * 64,
                                                  "quote_id": qa["quote_id"], "accept_terms": True, "kvkk_ack": True})
    assert r.status_code in (400, 403, 409)
