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


def plan_request(account: dict, req: dict, requester: str) -> None:
    c = AM.cfg()
    note = _msg(c["notify_to"], "[answerr] Plan talebi — {} → {} ({})".format(account.get("company") or account["email"], req["plan"], req["cycle"]),
                "Hesap   : {id}\nE-posta : {email}\nŞirket  : {company}\nMevcut  : {cur}\nTalep   : {plan} / {cycle}\nNot     : {note}\n"
                "Talep eden: {who}\n\nOnay: POST /v1/admin/plan-requests/{rid}/approve (yönetici anahtarı) ya da konsol › Yönetim.\n".format(
                    id=account["id"], email=account["email"], company=account.get("company") or "-", cur=account.get("plan"),
                    plan=req["plan"], cycle=req["cycle"], note=req.get("note") or "-", who=requester, rid=req["id"]),
                reply_to=requester)
    lang = account.get("lang") or "tr"
    if lang == "en":
        conf = _msg(requester, "answerr — plan request received",
                    "Hello,\n\nWe received your request to move to the {} plan ({} billing). We will confirm by e-mail and send "
                    "the payment details within one working day; the plan becomes active when payment is received.\n".format(req["plan"], req["cycle"]) + SIGNATURE_EN)
    else:
        conf = _msg(requester, "answerr — plan talebiniz alındı",
                    "Merhaba,\n\n{} planına ({} faturalama) geçiş talebinizi aldık. Bir iş günü içinde e-postayla onaylayıp ödeme "
                    "bilgilerini gönderiyoruz; plan, ödeme alındığında etkinleşir.\n".format(req["plan"], "yıllık" if req["cycle"] == "yearly" else "aylık") + SIGNATURE_TR)
    _dispatch([note, conf])


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
