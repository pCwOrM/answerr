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
SIGNATURE_TR = "\n—\nanswerr · Werr Technology\nITouch Bilişim Sistemleri Ltd. Şti. · Çukurova Teknokent, Adana\nhttps://answerr.me/pro/\n"
SIGNATURE_EN = "\n—\nanswerr · Werr Technology\nITouch Bilişim Sistemleri Ltd. Şti. · Çukurova Teknokent, Adana, Türkiye\nhttps://answerr.me/pro/\n"


def console_url() -> str:
    import os
    return os.environ.get(CONSOLE_URL_ENV, "https://answerr.me/pro/console/").rstrip("/") + "/"


def _msg(to: str, subject: str, body: str, reply_to: Optional[str] = None) -> EmailMessage:
    c = AM.cfg()
    m = EmailMessage()
    m["From"] = formataddr((c["from_name"], c["user"]))
    m["To"] = to
    m["Reply-To"] = reply_to or c["reply_to"]
    m["Subject"] = subject
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


def payment_paid(account: Optional[dict], pay: dict, billing: dict) -> None:
    """Card payment received: invoice details to ITouch (for the e-Arşiv/e-Fatura in Paraşüt) and a receipt to the buyer.
    Never contains card data; iyzico only returns the last four digits."""
    c = AM.cfg()
    when = _tr_date(pay.get("paid_at") or 0, "%d.%m.%Y %H:%M")
    until = _tr_date(pay["period_end"]) if pay.get("period_end") else "-"
    who = (account or {}).get("company") or billing.get("legal_name") or (account or {}).get("email") or "-"
    lines = [
        "Kartla ödeme alındı — fatura kesilmeli (Paraşüt).", "",
        "Ödeme no      : {}".format(pay["id"]),
        "iyzico ödeme  : {}".format(pay.get("payment_id") or "-"),
        "Tarih         : {}".format(when),
        "Ürün          : answerr {} / {}".format(pay.get("plan") or pay.get("kind"), pay.get("cycle") or "-"),
        "Dönem sonu    : {}".format(until),
        "Tutar (KDV h.): {}".format(_tl(pay["net_try"])),
        "KDV %20       : {}".format(_tl(pay["vat_try"])),
        "Toplam        : {}".format(_tl(pay["total_try"])),
        "Kart          : **** {}".format(pay.get("card_last4") or "----"), "",
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
    msgs = [_msg(c["notify_to"], "[answerr] Ödeme alındı — {} — {}".format(who, _tl(pay["total_try"])), "\n".join(lines))]
    to = billing.get("invoice_email") or (account or {}).get("email")
    if to and pay.get("kind") == "plan":
        en = (account or {}).get("lang") == "en"
        if en:
            body = ("Hello,\n\nWe received your payment of {} (VAT included) for the answerr {} plan. The plan is active until {}.\n"
                    "Your e-invoice will be sent to this address within two working days.\nPayment reference: {}\n\nConsole: {}\n").format(
                _tl(pay["total_try"]), pay.get("plan"), until, pay["id"], console_url()) + SIGNATURE_EN
            subj = "answerr — payment received"
        else:
            body = ("Merhaba,\n\nanswerr {} planı için {} (KDV dahil) ödemenizi aldık. Planınız {} tarihine kadar etkin.\n"
                    "e-Arşiv / e-Faturanız iki iş günü içinde bu adrese gönderilecek.\nÖdeme referansı: {}\n\nKonsol: {}\n").format(
                pay.get("plan"), _tl(pay["total_try"]), until, pay["id"], console_url()) + SIGNATURE_TR
            subj = "answerr — ödemeniz alındı"
        msgs.append(_msg(to, subj, body))
    _dispatch(msgs)


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
