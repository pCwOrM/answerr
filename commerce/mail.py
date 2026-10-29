"""Transactional e-mail for the commercial layer (sign-in links, invitations, plan requests, quota warnings).
Uses the SMTP settings of access_mailer (ask@answerr.me). Sending happens in a background thread;
when SMTP_PASSWORD is empty nothing is sent and the message is only logged (tests, local runs)."""
from __future__ import annotations

import threading
from email.message import EmailMessage
from email.utils import formataddr, make_msgid
from typing import Callable, List, Optional

import access_mailer as AM

CONSOLE_URL_ENV = "ANSWERR_CONSOLE_URL"
OUTBOX: List[EmailMessage] = []      # last messages, for tests and diagnostics (never contains passwords)
SIGNATURE_TR = "\n—\nanswerr · Werr Technology\nITouch Bilişim Sistemleri Ltd. Şti. · Çukurova Üniversitesi Teknokent, Adana\nhttps://answerr.me/pro/\n"
SIGNATURE_EN = "\n—\nanswerr · Werr Technology\nITouch Systems · Cukurova University Science Park, Adana, Turkey\nhttps://answerr.me/pro/\n"


def console_url() -> str:
    import os
    return os.environ.get(CONSOLE_URL_ENV, "https://answerr.me/pro/console/").rstrip("/") + "/"


def _msg(to: str, subject: str, body: str, reply_to: Optional[str] = None) -> EmailMessage:
    c = AM.cfg()
    m = EmailMessage()
    m["From"] = formataddr((c["from_name"], c["user"]))
    m["To"] = to
    m["Reply-To"] = reply_to or c["reply_to"]
    m["Subject"] = " ".join(str(subject).split())[:200]     # customer-supplied names must not break the header
    m["Message-ID"] = make_msgid(domain="answerr.me")
    m.set_content(body)
    return m


def _dispatch(msgs: List[EmailMessage], sync: bool = False) -> None:
    OUTBOX.extend(msgs)
    del OUTBOX[:-50]
    if not AM.cfg()["password"]:
        return

    def run():
        try:
            AM._send(msgs)
        except Exception as e:  # logged, never raised into the request
            AM.log_request({"mail_error": type(e).__name__, "subjects": [m["Subject"] for m in msgs]})
    if sync:
        run()
    else:
        threading.Thread(target=run, daemon=True).start()


def no_account(email: str, lang: str = "tr") -> None:
    """Sign-in asked for an address with no account. The API answers the same either way (no enumeration);
    only the mailbox owner learns that they need to sign up."""
    url = console_url() + "#signup"
    if lang == "en":
        subj, body = "answerr — no account for this address", (
            "Hello,\n\nSomeone (probably you) asked for an answerr sign-in link for this address, but there is no account "
            "with it. To create one:\n\n{}\n\nIf you did not ask for this, ignore this e-mail.\n").format(url) + SIGNATURE_EN
    else:
        subj, body = "answerr — bu adresle bir hesap yok", (
            "Merhaba,\n\nBu adres için answerr giriş bağlantısı istendi ama bu adresle açılmış bir hesap yok. "
            "Hesap açmak için:\n\n{}\n\nBu isteği siz yapmadıysanız bu e-postayı yok sayın.\n").format(url) + SIGNATURE_TR
    _dispatch([_msg(email, subj, body)])


def login_link(email: str, token: str, purpose: str, lang: str = "tr") -> None:
    url = console_url() + "#login=" + token
    if lang == "en":
        subj = "answerr — your sign-in link" if purpose != "signup" else "answerr — confirm your account"
        body = ("Hello,\n\nUse this link to {} answerr (valid for 20 minutes, single use):\n\n{}\n\n"
                "If you did not ask for it, ignore this e-mail; nothing will happen.\n").format(
                    "create your account on" if purpose == "signup" else "sign in to", url) + SIGNATURE_EN
    else:
        subj = "answerr — giriş bağlantınız" if purpose != "signup" else "answerr — hesabınızı onaylayın"
        body = ("Merhaba,\n\nanswerr {} için bağlantınız (20 dakika geçerli, tek kullanımlık):\n\n{}\n\n"
                "Bu isteği siz yapmadıysanız e-postayı yok sayın; hiçbir işlem yapılmaz.\n").format(
                    "hesabınızı oluşturmak" if purpose == "signup" else "konsoluna girmek", url) + SIGNATURE_TR
    _dispatch([_msg(email, subj, body)])


def invitation(email: str, inviter: str, company: str, role: str, token: str, lang: str = "tr") -> None:
    url = console_url() + "#login=" + token
    if lang == "en":
        body = ("Hello,\n\n{} invited you to the answerr account of {} as {}.\n\nAccept (valid 20 minutes):\n{}\n\n"
                "Later you can sign in at {} with this address.\n").format(inviter, company or "their team", role, url, console_url()) + SIGNATURE_EN
        subj = "answerr — you were invited"
    else:
        body = ("Merhaba,\n\n{} sizi {} answerr hesabına {} rolüyle davet etti.\n\nKabul etmek için (20 dakika geçerli):\n{}\n\n"
                "Daha sonra {} adresinden bu e-postayla giriş yapabilirsiniz.\n").format(inviter, company or "ekibinin", role, url, console_url()) + SIGNATURE_TR
        subj = "answerr — davet"
    _dispatch([_msg(email, subj, body)])


def invoice_download_token(payment_id: str) -> str:
    import hmac, hashlib
    secret = (AM.cfg().get("password") or "answerr_invoice_secret_2026").encode()
    return hmac.new(secret, f"answerr_invoice:{payment_id.strip().lower()}".encode(), hashlib.sha256).hexdigest()[:24]


def check_invoice_download_token(payment_id: str, token: str) -> bool:
    import hmac
    return bool(token) and hmac.compare_digest(invoice_download_token(payment_id), token.strip().lower())


def admin_wire_approve_token(payment_id: str) -> str:
    import hmac, hashlib
    secret = (AM.cfg().get("password") or "answerr_wire_secret_key_2026").encode()
    return hmac.new(secret, f"answerr_wire_approve:{payment_id.strip().lower()}".encode(), hashlib.sha256).hexdigest()[:32]


def check_admin_wire_approve_token(payment_id: str, token: str) -> bool:
    import hmac
    return bool(token) and hmac.compare_digest(admin_wire_approve_token(payment_id), token.strip().lower())

def plan_request(account: dict, req: dict, requester: str, payment_id: Optional[str] = None) -> None:
    c = AM.cfg()
    pay_id = payment_id or ""
    n = req.get("note") or ""
    if not pay_id and "havale/EFT proforma " in n:
        if n.strip().startswith("{"):
            try:
                import json as _j
                pay_id = _j.loads(n).get("pay_id", "")
            except Exception:
                pass
        if not pay_id and "havale/EFT proforma " in n:
            pay_id = n.split("havale/EFT proforma ")[-1].strip()

    approve_section = ""
    if pay_id:
        approve_tok = admin_wire_approve_token(pay_id)
        approve_url = f"https://api.answerr.me/v1/commerce/admin-approve-wire?pay_id={pay_id}&t={approve_tok}"
        approve_section = f"""
======================================================================
👉 HAVALE HESABA GELDİĞİNDE TEK TIKLA ONAYLAYIP PLANI AKTİFLEŞTİRMEK İÇİN:
{approve_url}

(Bu bağlantıya tıkladığınızda:
 1. Havale faturası resmi olarak ÖDENDİ olarak onaylanır.
 2. Müşterinin planı (250.000 karar) aktif edilir.
 3. Müşteriye aktif API anahtarı ve ÖDENDİ faturası mail olarak teslim edilir.)
======================================================================
"""

    admin_body = """Yeni answerr Banka Havalesi / Plan Talebi Alındı:

Hesap        : {id}
E-posta      : {email}
Şirket       : {company}
Mevcut Plan  : {cur}
Talep Edilen : {plan} / {cycle}
Ödeme ID     : {pay_id}
Proforma PDF : https://api.answerr.me/v1/account/payments/{pay_id}/invoice.pdf
Not          : {note}
Talep eden   : {who}
{approve_section}
Alternatif Konsol Onayı: POST /v1/admin/plan-requests/{rid}/approve ya da konsol › Yönetim.
""".format(
        id=account["id"], email=account["email"], company=account.get("company") or "-", cur=account.get("plan"),
        plan=req["plan"], cycle=req["cycle"], pay_id=pay_id or "-", note=req.get("note") or "-", who=requester, rid=req["id"],
        approve_section=approve_section
    )

    note_msg = _msg("pcworm@pcworm.net", f"[answerr HAVALE TALEP] {account.get('company') or account['email']} — {req['plan']} ({req['cycle']})",
                    admin_body, reply_to=requester)

    # Customer confirmation with Bank Details and Proforma PDF
    from . import billing, store as S
    lang = account.get("lang") or "tr"
    plan_name = {"gelistirici": "Geliştirici (Developer)", "pro": "Pro", "kurumsal": "Kurumsal"}.get(req["plan"], req["plan"])
    cycle_name = "Yıllık (366 Gün / 12 Ay)" if req["cycle"] == "yearly" else "Aylık (31 Gün / 1 Ay)"

    pay_rec = None
    if pay_id:
        try:
            pay_rec = S.get_payment(pay_id)
        except Exception:
            pay_rec = None

    tot_display = f"{float(pay_rec.get('total_try', 0)):,.2f} {pay_rec.get('currency', 'USD')}" if pay_rec else "-"
    inv_no = billing.invoice_number(pay_rec) if pay_rec else f"PRO-{pay_id[:8].upper()}"
    inv_dl_url = f"https://api.answerr.me/v1/invoice/{pay_id}.pdf?t={invoice_download_token(pay_id)}" if pay_id else ""

    if lang == "en":
        subj = f"answerr — Proforma Invoice & Bank Transfer Details ({inv_no})"
        body = f"""Hello,

We have received your request for the answerr {plan_name} ({cycle_name}).
Your Proforma Commercial Invoice has been generated and is attached to this email.

ORDER & PAYMENT SUMMARY
----------------------------------------------------------------------
Plan           : answerr {plan_name} ({cycle_name})
Total Amount   : {tot_display} (%0 VAT / Teknopark R&D Software Exemption)
Payment Ref    : {pay_id}
Proforma No    : {inv_no}
Invoice Link   : {inv_dl_url}

OFFICIAL CORPORATE BANK ACCOUNTS
----------------------------------------------------------------------
Bank Name      : Türk Ekonomi Bankası A.Ş. (TEB)
Branch         : Adana Toros Şb. (Branch Code: 446)
SWIFT / BIC    : TEBUTRIS
Beneficiary    : ITOUCH BİLİŞİM SİSTEMLERİ MÜHENDİSLİK DANIŞMANLIK SAN. VE TİC. LTD. ŞTİ.
TRY (TL) IBAN  : TR92 0003 2000 0000 0070 5754 65
USD ($) IBAN   : TR83 0003 2000 0000 0088 9467 48
EUR (€) IBAN   : TR28 0003 2000 0000 0088 9467 68
Base USDC      : 0x4945ef6e124eea2176ddf050b33db42b0ae8c7f7

* IMPORTANT: Please include your Payment Reference ({pay_id}) in the transfer description.

Once your transfer is received and verified by our finance team, your API key and plan will be activated immediately, and your official PAID Commercial Invoice will be delivered to you by email.
""" + SIGNATURE_EN
    else:
        subj = f"answerr — Proforma Faturanız ve Havale/EFT Ödeme Bilgileri ({inv_no})"
        body = f"""Merhaba,

answerr {plan_name} ({cycle_name}) talebiniz alınmıştır.
Ödemenize ait Proforma Ticari Faturanız düzenlenmiş olup ekte PDF olarak sunulmuştur.

SİPARİŞ VE ÖDEME ÖZETİ
----------------------------------------------------------------------
Plan           : answerr {plan_name} ({cycle_name})
Toplam Tutar   : {tot_display} (%0 KDV — 4691 s. Teknopark İstisnası)
Ödeme Ref      : {pay_id}
Proforma No    : {inv_no}
Fatura Linki   : {inv_dl_url}

RESMİ ŞİRKET BANKA HESAPLARIMIZ
----------------------------------------------------------------------
Banka Adı      : Türk Ekonomi Bankası A.Ş. (TEB)
Şube           : Adana Toros Şb. (Şube Kodu: 446)
SWIFT Kodu     : TEBUTRIS
Alıcı (Unvan)  : ITOUCH BİLİŞİM SİSTEMLERİ MÜHENDİSLİK DANIŞMANLIK SAN. VE TİC. LTD. ŞTİ.
TRY (TL) IBAN  : TR92 0003 2000 0000 0070 5754 65
USD ($) IBAN   : TR83 0003 2000 0000 0088 9467 48
EUR (€) IBAN   : TR28 0003 2000 0000 0088 9467 68
Base USDC      : 0x4945ef6e124eea2176ddf050b33db42b0ae8c7f7

* ÖNEMLİ: Havale veya EFT yaparken açıklama kısmına lütfen ödeme referansınızı ({pay_id}) yazınız.

Havaleniz banka hesabımıza ulaştığında ekibimiz tarafından onaylanacak; planınız ve API anahtarınız anında aktif edilerek tarafınıza resmi ÖDENDİ faturanız ile birlikte aktivasyon e-postası iletilecektir.
""" + SIGNATURE_TR

    conf_msg = _msg(requester, subj, body)
    conf_msg["Bcc"] = "ask@answerr.me"

    # Attach Proforma Invoice PDF if available
    if pay_rec:
        try:
            pdf_bytes = billing.generate_answerr_invoice_pdf(account, pay_rec)
            conf_msg.add_attachment(pdf_bytes, maintype="application", subtype="pdf", filename=f"proforma_invoice_{inv_no}.pdf")
        except Exception as e:
            AM.log_request({"pdf_attach_error": str(e), "pay_id": pay_id})

    _dispatch([note_msg, conf_msg])


def quota_warning(account: dict, pct: int, used: int, quota: int) -> None:
    lang = account.get("lang") or "tr"
    if lang == "en":
        subj = "answerr — {}% of your monthly decisions used".format(pct)
        body = ("Hello,\n\nYour account has used {:,} of {:,} decisions this month ({}%).\n{}\n\nUsage: {}\n").format(
            used, quota, pct, "When the quota is reached the API returns 429 unless overage is on." if pct < 100 else
            "The quota is reached: decision calls now return 429 unless overage is on.", console_url()) + SIGNATURE_EN
    else:
        subj = "answerr — aylık kararlarınızın %{}'i kullanıldı".format(pct)
        body = ("Merhaba,\n\nHesabınız bu ay {:,} kararlık kotanın {:,} kadarını kullandı (%{}).\n{}\n\nKullanım: {}\n").format(
            quota, used, pct, "Kota dolduğunda aşım açık değilse API 429 döner." if pct < 100 else
            "Kota doldu: aşım açık değilse karar çağrıları 429 dönüyor.", console_url()) + SIGNATURE_TR
    _dispatch([_msg(account["email"], subj, body)])


def run_async(fn: Callable, *a, **kw) -> None:
    threading.Thread(target=fn, args=a, kwargs=kw, daemon=True).start()


def _tr_date(ts: float, fmt: str = "%d.%m.%Y") -> str:
    import datetime as _dt
    return _dt.datetime.fromtimestamp(ts, _dt.timezone(_dt.timedelta(hours=3))).strftime(fmt)   # Türkiye, UTC+3


def _tl(x) -> str:
    """1234.5 -> '1.234,50 ₺'"""
    s = "{:,.2f}".format(float(x)).replace(",", "X").replace(".", ",").replace("X", ".")
    return s + " ₺"


def _amt(pay: dict, field: str) -> str:
    """Amount in the payment's own currency (TRY card/transfer, USD transfer, USDC/USDT on-chain)."""
    cur = (pay.get("currency") or "TRY").upper()
    if cur == "TRY":
        return _tl(pay.get(field) or 0)
    return "{:,.2f} {}".format(float(pay.get(field) or 0), cur)


def _method(pay: dict) -> str:
    prov = pay.get("provider") or "iyzico"
    if prov == "iyzico":
        return "kart **** {} · iyzico işlem no {}".format(pay.get("card_last4") or "----", pay.get("payment_id") or "-")
    if prov.startswith("crypto_"):
        return "{} · {} · TXID {}".format(prov[7:].upper(), pay.get("card_last4") or "", pay.get("payment_id") or "-")
    return "havale / EFT · referans {}".format(pay.get("payment_id") or pay.get("id"))


def payment_paid(account: Optional[dict], pay: dict, billing: dict) -> None:
    """Card payment received: invoice details to ITouch (for the e-Arşiv/e-Fatura in Paraşüt) and a receipt to the buyer.
    Never contains card data; iyzico only returns the last four digits."""
    c = AM.cfg()
    when = _tr_date(pay.get("paid_at") or 0, "%d.%m.%Y %H:%M")
    until = _tr_date(pay["period_end"]) if pay.get("period_end") else "-"
    who = (account or {}).get("company") or billing.get("legal_name") or (account or {}).get("email") or "-"
    lines = [
        "Ödeme alındı — fatura kesilmeli (Paraşüt).", "",
        "Ödeme no      : {}".format(pay["id"]),
        "Yöntem        : {}".format(_method(pay)),
        "Tarih         : {}".format(when),
        "Ürün          : answerr {} / {}".format(pay.get("plan") or pay.get("kind"), pay.get("cycle") or "-"),
        "Dönem sonu    : {}".format(until),
        "Tutar (KDV h.): {}".format(_amt(pay, "net_try")),
        "KDV (%0 Muaf) : {} (4691 s. Kanun & 3065 s. KDV K. Geçici 20/1 Teknopark İstisnası)".format(_amt(pay, "vat_try")),
        "Toplam        : {}".format(_amt(pay, "total_try")), "",
        "Fatura bilgileri",
        "Unvan / Ad    : {}".format(billing.get("legal_name") or "-"),
        "Vergi dairesi : {}".format(billing.get("tax_office") or "-"),
        "VKN / TCKN    : {}".format(billing.get("tax_id") or "-"),
        "Adres         : {}".format(billing.get("address") or "-"),
        "Şehir / Ülke  : {} / {}".format(billing.get("city") or "-", billing.get("country") or "Türkiye"),
        "Telefon       : {}".format(billing.get("phone") or "-"),
        "Fatura e-post.: {}".format(billing.get("invoice_email") or (account or {}).get("email") or "-"),
        "Hesap         : {} {}".format((account or {}).get("id") or "-", (account or {}).get("email") or ""), "",
        "Fatura kesildikten sonra numarasını ekstreye işleyin: konsol › Yönetim.",
    ]
    msgs = [_msg(c["notify_to"], "[answerr] Ödeme alındı — {} — {}".format(who, _amt(pay, "total_try")), "\n".join(lines))]
    to = billing.get("invoice_email") or (account or {}).get("email")
    if to and pay.get("kind") == "plan":
        msgs.append(order_confirmation(to, account, pay, billing, until))
    _dispatch(msgs)


LEGAL_DIR = __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "legal")
LEGAL_TEXTS = (("on-bilgilendirme", "On_Bilgilendirme_Formu"), ("mesafeli-satis", "Mesafeli_Satis_Sozlesmesi"))


def legal_version() -> str:
    """Version of the pre-contract texts shipped with the API (commerce/legal/*.txt, generated from site/legal)."""
    import os, re
    try:
        t = open(os.path.join(LEGAL_DIR, "mesafeli-satis.txt"), encoding="utf-8").read()
        m = re.search(r"Sürüm:\s*([0-9-]+)", t)
        return m.group(1) if m else "-"
    except OSError:
        return "-"


def order_confirmation(to: str, account: Optional[dict], pay: dict, billing: dict, until: str) -> EmailMessage:
    """Sipariş onayı: order details, VAT-inclusive total, buyer, consent record, and the two accepted texts attached
    as plain text (kalıcı veri saklayıcısı)."""
    import os
    plan = {"gelistirici": "Geliştirici", "pro": "Pro"}.get(pay.get("plan"), pay.get("plan") or "-")
    cycle = "yıllık (366 gün)" if pay.get("cycle") == "yearly" else "aylık (31 gün)"
    consent = _tr_date(billing["consent_ts"], "%d.%m.%Y %H:%M") if billing.get("consent_ts") else "-"
    body = "\n".join([
        "Merhaba,", "",
        "answerr siparişiniz tamamlandı. Bu e-posta sipariş onayınızdır; onayladığınız Ön Bilgilendirme Formu ve Mesafeli Satış "
        "Sözleşmesi ekte düz metin olarak yer alır. Lütfen saklayın.", "",
        "Sipariş",
        "Referans        : {}".format(pay["id"]),
        "Ürün            : answerr {} planı, {}".format(plan, cycle),
        "Plan bitişi     : {}".format(until),
        "Tutar (KDV h.)  : {}".format(_amt(pay, "net_try")),
        "KDV (%0 Muaf)   : {} (3065 s. KDV K. Geçici 20/1 Teknopark İstisnası)".format(_amt(pay, "vat_try")),
        "Toplam          : {} (%0 KDV — Teknopark Muafiyetli)".format(_amt(pay, "total_try")),
        "Ödeme           : {}".format(_method(pay)),
        "Ödeme tarihi    : {}".format(_tr_date(pay.get("paid_at") or 0, "%d.%m.%Y %H:%M")), "",
        "Alıcı",
        "Unvan / ad      : {}".format(billing.get("legal_name") or "-"),
        "Yetkili kişi    : {}".format(billing.get("contact_name") or "-"),
        "VKN / TCKN      : {} {}".format(billing.get("tax_id") or "-", ("(" + billing["tax_office"] + ")") if billing.get("tax_office") else ""),
        "Adres           : {} {}".format(billing.get("address") or "-", billing.get("city") or ""),
        "Telefon         : {}".format(billing.get("phone") or "-"), "",
        "Onay kaydı",
        "Ön bilgilendirme ve mesafeli satış onayı: {} · metin sürümü {}".format(consent, billing.get("legal_version") or legal_version()),
        "Cayma hakkı: Hizmet elektronik ortamda anında ifa edildiği için cayma hakkı yoktur (Mesafeli Sözleşmeler Yönetmeliği m.15/1-ğ).",
        "Gönüllü iade koşulları: https://answerr.me/pro/legal/iade-iptal.html", "",
        "Otomatik çekim yapılmaz. Plan bitmeden 7 gün önce hatırlatırız.",
        "e-Arşiv / e-Faturanız iki iş günü içinde bu adrese gönderilecek.", "",
        "Konsol: {}".format(console_url()),
    ]) + SIGNATURE_TR
    m = _msg(to, "answerr — sipariş onayı ve ödemeniz ({})".format(pay["id"]), body)
    m["Bcc"] = "ask@answerr.me"
    for slug, name in LEGAL_TEXTS:
        try:
            data = open(os.path.join(LEGAL_DIR, slug + ".txt"), encoding="utf-8").read()
            m.add_attachment(data, subtype="plain", filename="{}_{}.txt".format(name, legal_version()))
        except OSError:
            pass
    return m


def payment_review(pay: dict, reason: str) -> None:
    c = AM.cfg()
    _dispatch([_msg(c["notify_to"], "[answerr] Ödeme incelemede — {}".format(pay["id"]),
                    "iyzico sonucu otomatik onaylanmadı; plan etkinleştirilmedi.\n\nÖdeme no: {}\nHesap: {}\nTutar: {}\nNeden: {}\n\n"
                    "iyzico panelinde işlemi kontrol edin; uygunsa yönetici API'siyle planı elle etkinleştirin, değilse iade edin.\n".format(
                        pay["id"], pay.get("account_id") or "-", _tl(pay["total_try"]), reason))])


def renewal_reminder(account: dict, expires_at: float) -> None:
    d = _tr_date(expires_at)
    url = console_url() + "#billing"
    if (account.get("lang") or "tr") == "en":
        subj, body = "answerr — your plan ends on {}".format(d), (
            "Hello,\n\nYour answerr {} plan is paid until {}. To keep it, renew from the console; the new period starts when the "
            "current one ends, so renewing early loses nothing.\n\n{}\n\nIf you do nothing the account moves to the free Explore plan "
            "on that date; your gates, keys and logs stay.\n").format(account["plan"], d, url) + SIGNATURE_EN
    else:
        subj, body = "answerr — planınız {} tarihinde bitiyor".format(d), (
            "Merhaba,\n\nanswerr {} planınızın ödenmiş dönemi {} tarihinde bitiyor. Devam etmek için konsoldan yenileyin; yeni dönem "
            "mevcut dönemin bitiminden başlar, erken yenilemek bir şey kaybettirmez.\n\n{}\n\nYenilemezseniz hesap o tarihte ücretsiz "
            "Keşif planına geçer; kapılarınız, anahtarlarınız ve kayıtlarınız silinmez.\n").format(account["plan"], d, url) + SIGNATURE_TR
    _dispatch([_msg(account["email"], subj, body)])


def wire_approved(account: dict, pay: dict, api_key: Optional[str] = None) -> None:
    c = AM.cfg()
    from . import billing
    import json, time
    lang = account.get("lang") or "tr"
    plan_name = {"gelistirici": "Geliştirici (Developer)", "pro": "Pro", "kurumsal": "Kurumsal"}.get(pay.get("plan"), str(pay.get("plan") or "-").title())
    cycle_name = "Yıllık (366 Gün / 12 Ay)" if pay.get("cycle") == "yearly" else "Aylık (31 Gün / 1 Ay)"
    inv_no = billing.invoice_number(pay)
    inv_dl_url = f"https://api.answerr.me/v1/invoice/{pay['id']}.pdf?t={invoice_download_token(pay['id'])}"
    tot_str = f"{float(pay.get('total_try') or 0):,.2f} {pay.get('currency', 'USD')}"
    p_end = float(pay.get("period_end") or (time.time() + 31 * 86400))
    until_str = _tr_date(p_end, "%d.%m.%Y")
    to = (account.get("billing_json") and json.loads(account["billing_json"]).get("invoice_email")) or account.get("email")

    key_section_tr = f"""
API ANAHTARINIZ VE ENTEGRASYON BİLGİLERİ
----------------------------------------------------------------------
API Anahtarı   : {api_key}
API Gateway    : https://api.answerr.me
Dokümantasyon  : https://answerr.me/docs
Konsol Girişi  : https://answerr.me/pro/console/

Örnek Karar Sorgusu (cURL):
curl -X POST https://api.answerr.me/v1/decide \\
  -H "Authorization: Bearer {api_key}" \\
  -H "Content-Type: application/json" \\
  -d '{{"gate": "default", "subject": "user_123", "action": "checkout", "context": {{"amount": 100}}}}'
""" if api_key else f"""
KONSOL VE API ERİŞİMİ
----------------------------------------------------------------------
API Gateway    : https://api.answerr.me
Konsol Girişi  : https://answerr.me/pro/console/
* API anahtarlarınızı konsolunuzdan dilediğiniz an yönetebilir ve oluşturabilirsiniz.
"""

    key_section_en = f"""
YOUR API KEY & INTEGRATION DETAILS
----------------------------------------------------------------------
API Key        : {api_key}
API Gateway    : https://api.answerr.me
Documentation  : https://answerr.me/docs
Console Access : https://answerr.me/pro/console/

Example Decision Request (cURL):
curl -X POST https://api.answerr.me/v1/decide \\
  -H "Authorization: Bearer {api_key}" \\
  -H "Content-Type: application/json" \\
  -d '{{"gate": "default", "subject": "user_123", "action": "checkout", "context": {{"amount": 100}}}}'
""" if api_key else f"""
CONSOLE & API ACCESS
----------------------------------------------------------------------
API Gateway    : https://api.answerr.me
Console Access : https://answerr.me/pro/console/
* You can generate and manage additional API keys from your console anytime.
"""

    if lang == "en":
        subj = f"answerr — Payment Approved & API Key Activated ({inv_no})"
        body = f"""Hello,

Your bank transfer payment has been verified and confirmed.
Your answerr {plan_name} subscription is now ACTIVE until {until_str}.
Your official PAID Commercial Invoice has been issued and is attached to this email.

SUBSCRIPTION & PAYMENT DETAILS
----------------------------------------------------------------------
Plan           : answerr {plan_name} ({cycle_name})
Valid Until    : {until_str}
Total Paid     : {tot_str} (%0 VAT — Teknopark R&D Software Exemption)
Reference      : {pay.get('payment_id') or pay.get('id')}
Invoice No     : {inv_no}
Invoice Link   : {inv_dl_url}
{key_section_en}
Thank you for choosing answerr.
""" + SIGNATURE_EN
    else:
        subj = f"answerr — Ödemeniz Onaylandı, Planınız ve API Anahtarınız Aktif Edildi ({inv_no})"
        body = f"""Merhaba,

Banka havalesi / EFT ödemeniz şirketimiz tarafından teyit edilmiş ve onaylanmıştır.
answerr {plan_name} lisansınız {until_str} tarihine kadar başarıyla AKTİF edilmiştir.
Resmi ÖDENDİ mühürlü Ticari Faturanız düzenlenmiş olup ekte PDF olarak sunulmuştur.

ABONELİK VE ÖDEME ÖZETİ
----------------------------------------------------------------------
Plan           : answerr {plan_name} ({cycle_name})
Geçerlilik     : {until_str} tarihine kadar
Ödenen Tutar   : {tot_str} (%0 KDV — 4691 s. Teknopark İstisnası)
Ödeme Ref      : {pay.get('payment_id') or pay.get('id')}
Fatura No      : {inv_no}
Fatura Linki   : {inv_dl_url}
{key_section_tr}
Mali mühürlü yasal e-Arşiv / e-Faturanız Gelir İdaresi Başkanlığı (GİB) portalı üzerinden düzenlenip iletilecektir.

answerr'ı tercih ettiğiniz için teşekkür ederiz.
""" + SIGNATURE_TR

    m = _msg(to, subj, body)
    m["Bcc"] = "ask@answerr.me"
    try:
        pdf_bytes = billing.generate_answerr_invoice_pdf(account, pay)
        m.add_attachment(pdf_bytes, maintype="application", subtype="pdf", filename=f"commercial_invoice_{inv_no}.pdf")
    except Exception as e:
        AM.log_request({"pdf_attach_error": str(e), "pay_id": pay.get("id")})
    _dispatch([m])
