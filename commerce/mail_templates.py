"""
High-quality, responsive HTML email templates for answerr.me commercial layer.
Designed with obsidian tech styling, high contrast typography, accessible fallbacks,
and standard RFC multipart MIME compatibility.
"""
from __future__ import annotations

import html
from typing import List, Tuple, Optional

# Theme Palette (answerr Dark Obsidian & Tech Emerald / Blue)
BG_PAGE = "#07090e"
BG_CARD = "#0f172a"
BG_INNER = "#090d16"
BORDER = "#1e293b"
TEXT_WHITE = "#ffffff"
TEXT_MAIN = "#f1f5f9"
TEXT_MUTED = "#94a3b8"
TEXT_LABEL = "#64748b"
ACCENT_BLUE = "#3b82f6"
EMERALD_GREEN = "#10b981"


def _wrap_email(
    title: str,
    preheader: str,
    badge_text: str,
    badge_variant: str,  # 'green', 'blue', 'amber'
    headline: str,
    lead: str,
    rows: List[Tuple[str, str]],
    primary_btn_text: Optional[str] = None,
    primary_btn_url: Optional[str] = None,
    secondary_btn_text: Optional[str] = None,
    secondary_btn_url: Optional[str] = None,
    extra_box_title: Optional[str] = None,
    extra_box_html: Optional[str] = None,
    lang: str = "tr",
) -> str:
    badge_colors = {
        "green": ("#34d399", "rgba(16, 185, 129, 0.12)", "#10b981"),
        "blue": ("#60a5fa", "rgba(59, 130, 246, 0.12)", "#3b82f6"),
        "amber": ("#fbbf24", "rgba(245, 158, 11, 0.12)", "#f59e0b"),
    }
    fg, bg_pill, border_pill = badge_colors.get(badge_variant, badge_colors["blue"])

    rows_rendered = ""
    for label, val in rows:
        val_clean = val.replace("\n", "<br>")
        rows_rendered += f"""
        <tr>
          <td style="padding: 10px 14px; color: {TEXT_LABEL}; font-size: 13px; font-weight: 500; border-bottom: 1px solid {BORDER}; vertical-align: top; white-space: nowrap;">{html.escape(label)}</td>
          <td style="padding: 10px 14px; color: {TEXT_WHITE}; font-size: 13px; font-weight: 600; text-align: right; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, monospace; border-bottom: 1px solid {BORDER}; vertical-align: top;">{val_clean}</td>
        </tr>"""

    buttons_markup = ""
    if primary_btn_text and primary_btn_url:
        buttons_markup += f"""
        <a href="{html.escape(primary_btn_url)}" target="_blank" style="display: inline-block; padding: 12px 22px; background: #2563eb; color: #ffffff; font-weight: 600; font-size: 14px; text-decoration: none; border-radius: 8px; margin-right: 10px; margin-bottom: 10px;">{html.escape(primary_btn_text)}</a>"""
    if secondary_btn_text and secondary_btn_url:
        buttons_markup += f"""
        <a href="{html.escape(secondary_btn_url)}" target="_blank" style="display: inline-block; padding: 12px 22px; background: #1e293b; color: #cbd5e1; font-weight: 600; font-size: 14px; text-decoration: none; border-radius: 8px; border: 1px solid #334155; margin-bottom: 10px;">{html.escape(secondary_btn_text)}</a>"""

    extra_markup = ""
    if extra_box_title and extra_box_html:
        extra_markup = f"""
        <div style="background: {BG_INNER}; border: 1px solid {BORDER}; border-radius: 10px; padding: 18px; margin-top: 22px;">
          <div style="color: {TEXT_WHITE}; font-weight: 700; font-size: 12px; text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 12px;">{html.escape(extra_box_title)}</div>
          <div style="color: {TEXT_MAIN}; font-size: 13px; line-height: 1.6;">{extra_box_html}</div>
        </div>"""

    if lang == "en":
        legal_footer = (
            'ITouch Bilisim Sistemleri Ltd. Sti. (ITouch Systems) &bull; Cukurova Univ. Technopark No: 4/1-26 Adana / Turkey<br>'
            'Deterministic Policy Gate &amp; Boundary Dynamics Engine &bull; '
            '<a href="https://answerr.me" style="color: #64748b; text-decoration: underline;">answerr.me</a> &bull; '
            '<a href="mailto:ask@answerr.me" style="color: #64748b; text-decoration: underline;">ask@answerr.me</a>'
        )
    else:
        legal_footer = (
            'ITouch Bilişim Sistemleri Ltd. Şti. &bull; Çukurova Üniv. Teknokent No: 4/1-26 Sarıçam / Adana<br>'
            'Deterministik Karar Geçidi ve Dinamik Sınır Motoru &bull; '
            '<a href="https://answerr.me" style="color: #64748b; text-decoration: underline;">answerr.me</a> &bull; '
            '<a href="mailto:ask@answerr.me" style="color: #64748b; text-decoration: underline;">ask@answerr.me</a>'
        )

    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(title)}</title>
</head>
<body style="margin: 0; padding: 0; background: {BG_PAGE}; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased;">
  <div style="display: none; font-size: 1px; color: #07090e; line-height: 1px; max-height: 0px; max-width: 0px; opacity: 0; overflow: hidden;">{html.escape(preheader)}</div>
  <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="background: {BG_PAGE}; padding: 32px 14px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="max-width: 580px; background: {BG_CARD}; border: 1px solid {BORDER}; border-radius: 16px; overflow: hidden; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7);">
          <!-- Header Bar -->
          <tr>
            <td style="padding: 24px 28px 18px; border-bottom: 1px solid {BORDER};">
              <table width="100%" border="0" cellspacing="0" cellpadding="0">
                <tr>
                  <td>
                    <span style="font-size: 22px; font-weight: 800; color: {TEXT_WHITE}; letter-spacing: -0.5px;">answerr</span>
                    <span style="color: {ACCENT_BLUE}; font-size: 22px; font-weight: 800;">.</span>
                  </td>
                  <td align="right">
                    <span style="display: inline-block; font-size: 11px; font-weight: 700; color: {fg}; background: {bg_pill}; border: 1px solid {border_pill}; padding: 4px 12px; border-radius: 9999px; text-transform: uppercase; letter-spacing: 0.5px;">{html.escape(badge_text)}</span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          
          <!-- Body Content -->
          <tr>
            <td style="padding: 28px;">
              <h1 style="margin: 0 0 10px; font-size: 20px; font-weight: 800; color: {TEXT_WHITE}; line-height: 1.35;">{html.escape(headline)}</h1>
              <p style="margin: 0 0 22px; font-size: 14px; color: {TEXT_MUTED}; line-height: 1.6;">{html.escape(lead)}</p>
              
              <!-- Key Value Table -->
              <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background: {BG_INNER}; border: 1px solid {BORDER}; border-radius: 10px; border-collapse: collapse; overflow: hidden;">
                {rows_rendered}
              </table>
              
              {extra_markup}
              
              <!-- Call to Action Buttons -->
              <div style="margin-top: 26px;">
                {buttons_markup}
              </div>
            </td>
          </tr>
          
          <!-- Footer -->
          <tr>
            <td style="padding: 20px 28px; background: {BG_INNER}; border-top: 1px solid {BORDER}; text-align: center; color: {TEXT_LABEL}; font-size: 12px; line-height: 1.6;">
              {legal_footer}
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def render_wire_approved_html(
    lang: str,
    plan_name: str,
    cycle_name: str,
    until_str: str,
    tot_str: str,
    inv_no: str,
    inv_dl_url: str,
    pay_id: str,
    api_key: Optional[str] = None,
) -> str:
    if lang == "en":
        title = f"answerr — Payment Approved & License Active ({inv_no})"
        preheader = f"Your answerr {plan_name} subscription is now active until {until_str}."
        badge = "CONFIRMED & ACTIVE"
        headline = "Payment Verified & License Activated"
        lead = (
            f"Your bank transfer payment has been verified by our finance team. "
            f"Your answerr {plan_name} license is now ACTIVE until {until_str}. "
            f"Your official PAID Commercial Invoice has been issued and is attached."
        )
        rows = [
            ("Plan", f"answerr {plan_name} ({cycle_name})"),
            ("Valid Until", f"{until_str}"),
            ("Total Paid", f"{tot_str} (%0 VAT — Tech Park Exemption)"),
            ("Invoice No", inv_no),
            ("Payment Ref", pay_id),
        ]
        primary_btn = "📄 View Official Invoice (PDF)"
        secondary_btn = "🚀 Developer Console"
        extra_title = "YOUR API KEY & INTEGRATION DETAILS" if api_key else "CONSOLE & API ACCESS"
        if api_key:
            extra_content = (
                f'<div style="font-family: monospace; font-size: 13px; color: #38bdf8; background: #030712; padding: 10px 14px; border-radius: 6px; border: 1px solid #1e293b; word-break: break-all; margin-bottom: 12px;">{html.escape(api_key)}</div>'
                f'<div style="color: #94a3b8; font-size: 12px; line-height: 1.5;">'
                f'<strong>API Gateway:</strong> <a href="https://api.answerr.me" style="color: #38bdf8; text-decoration: none;">https://api.answerr.me</a><br>'
                f'<strong>Documentation:</strong> <a href="https://answerr.me/docs" style="color: #38bdf8; text-decoration: none;">answerr.me/docs</a><br>'
                f'<strong>Console Access:</strong> <a href="https://answerr.me/pro/console/" style="color: #38bdf8; text-decoration: none;">answerr.me/pro/console/</a>'
                f'</div>'
            )
        else:
            extra_content = (
                '<div style="color: #94a3b8; font-size: 12px; line-height: 1.5;">'
                'You can view and manage your API keys, usage limits, and team permissions anytime in the '
                '<a href="https://answerr.me/pro/console/" style="color: #38bdf8; text-decoration: none;">answerr Developer Console</a>.'
                '</div>'
            )
    else:
        title = f"answerr — Ödemeniz Onaylandı, Lisansınız Aktif Edildi ({inv_no})"
        preheader = f"answerr {plan_name} lisansınız {until_str} tarihine kadar aktif edilmiştir."
        badge = "ONAYLANDI & AKTİF"
        headline = "Havale Ödemeniz Onaylandı & Lisansınız Aktif"
        lead = (
            f"Banka havalesi / EFT ödemeniz finans birimimizce teyit edilmiş ve onaylanmıştır. "
            f"answerr {plan_name} lisansınız {until_str} tarihine kadar başarıyla AKTİF edilmiştir. "
            f"Resmi ÖDENDİ mühürlü Ticari Faturanız düzenlenmiş olup ekte PDF olarak sunulmuştur."
        )
        rows = [
            ("Plan", f"answerr {plan_name} ({cycle_name})"),
            ("Geçerlilik", f"{until_str} Tarihine Kadar"),
            ("Ödenen Tutar", f"{tot_str} (%0 KDV — 4691 s. Teknokent İstisnası)"),
            ("Fatura No", inv_no),
            ("Ödeme Ref", pay_id),
        ]
        primary_btn = "📄 Onaylı Fatura PDF'ini Aç"
        secondary_btn = "🚀 Geliştirici Konsolu"
        extra_title = "API ANAHTARINIZ VE ENTEGRASYON BİLGİLERİ" if api_key else "KONSOL VE API ERİŞİMİ"
        if api_key:
            extra_content = (
                f'<div style="font-family: monospace; font-size: 13px; color: #38bdf8; background: #030712; padding: 10px 14px; border-radius: 6px; border: 1px solid #1e293b; word-break: break-all; margin-bottom: 12px;">{html.escape(api_key)}</div>'
                f'<div style="color: #94a3b8; font-size: 12px; line-height: 1.5;">'
                f'<strong>API Gateway:</strong> <a href="https://api.answerr.me" style="color: #38bdf8; text-decoration: none;">https://api.answerr.me</a><br>'
                f'<strong>Dokümantasyon:</strong> <a href="https://answerr.me/docs" style="color: #38bdf8; text-decoration: none;">answerr.me/docs</a><br>'
                f'<strong>Konsol Girişi:</strong> <a href="https://answerr.me/pro/console/" style="color: #38bdf8; text-decoration: none;">answerr.me/pro/console/</a>'
                f'</div>'
            )
        else:
            extra_content = (
                '<div style="color: #94a3b8; font-size: 12px; line-height: 1.5;">'
                'API anahtarlarınızı, kullanım kotalarınızı ve ekip yetkilerini dilediğiniz an '
                '<a href="https://answerr.me/pro/console/" style="color: #38bdf8; text-decoration: none;">answerr Geliştirici Konsolu</a> üzerinden yönetebilirsiniz.'
                '</div>'
            )

    return _wrap_email(
        title=title,
        preheader=preheader,
        badge_text=badge,
        badge_variant="green",
        headline=headline,
        lead=lead,
        rows=rows,
        primary_btn_text=primary_btn,
        primary_btn_url=inv_dl_url,
        secondary_btn_text=secondary_btn,
        secondary_btn_url="https://answerr.me/pro/console/",
        extra_box_title=extra_title,
        extra_box_html=extra_content,
        lang=lang,
    )


def render_plan_request_html(
    lang: str,
    plan_name: str,
    cycle_name: str,
    tot_str: str,
    inv_no: str,
    inv_dl_url: str,
    pay_id: str,
) -> str:
    if lang == "en":
        title = f"answerr — Proforma Invoice & Bank Transfer Details ({inv_no})"
        preheader = f"Proforma invoice {inv_no} generated for answerr {plan_name}."
        badge = "PROFORMA INVOICE"
        headline = "Proforma Invoice & Bank Transfer Instructions"
        lead = (
            f"We have received your order for answerr {plan_name} ({cycle_name}). "
            f"Your Proforma Commercial Invoice is attached. Please complete the transfer using the bank accounts below."
        )
        rows = [
            ("Plan", f"answerr {plan_name} ({cycle_name})"),
            ("Total Due", f"{tot_str} (%0 VAT — Tech Park Exemption)"),
            ("Payment Ref", pay_id),
            ("Proforma No", inv_no),
        ]
        primary_btn = "📄 View Proforma Invoice (PDF)"
        secondary_btn = "🚀 Open Console"
        extra_title = "OFFICIAL CORPORATE BANK ACCOUNTS (SWIFT / WIRE / HAVALE)"
        extra_content = f"""
        <table width="100%" border="0" cellspacing="0" cellpadding="0" style="font-size: 12.5px; line-height: 1.6; color: #cbd5e1;">
          <tr><td style="color: #64748b; width: 110px;">Bank Name:</td><td style="font-weight: 600; color: #fff;">Turk Ekonomi Bankasi A.S. (TEB) — Adana Toros Br. (446)</td></tr>
          <tr><td style="color: #64748b;">SWIFT / BIC:</td><td style="font-family: monospace; font-weight: 700; color: #38bdf8;">TEBUTRIS</td></tr>
          <tr><td style="color: #64748b;">Beneficiary:</td><td style="font-weight: 600; color: #fff;">ITOUCH BILISIM SISTEMLERI MUHENDISLIK DANISMANLIK SAN. VE TIC. LTD. STI.</td></tr>
          <tr><td style="color: #64748b;">Tag 59 Short:</td><td style="color: #34d399; font-weight: 600;">ITOUCH BILISIM SISTEMLERI LTD. STI. <span style="color: #64748b; font-size: 11px;">(Recommended for SWIFT)</span></td></tr>
          <tr><td style="color: #64748b;">City / Country:</td><td>Adana / Turkey</td></tr>
          <tr><td style="color: #64748b; padding-top: 6px;">USD ($) IBAN:</td><td style="font-family: monospace; font-weight: 700; color: #fff; padding-top: 6px;">TR83 0003 2000 0000 0088 9467 48</td></tr>
          <tr><td style="color: #64748b;">EUR (€) IBAN:</td><td style="font-family: monospace; font-weight: 700; color: #fff;">TR28 0003 2000 0000 0088 9467 68</td></tr>
          <tr><td style="color: #64748b;">TRY (₺) IBAN:</td><td style="font-family: monospace; font-weight: 700; color: #fff;">TR92 0003 2000 0000 0070 5754 65</td></tr>
          <tr><td style="color: #64748b;">Base USDC:</td><td style="font-family: monospace; font-size: 11px; color: #94a3b8;">0x4945ef6e124eea2176ddf050b33db42b0ae8c7f7</td></tr>
        </table>
        <div style="margin-top: 12px; padding: 8px 12px; background: rgba(59, 130, 246, 0.1); border-left: 3px solid #3b82f6; border-radius: 4px; font-size: 12px; color: #93c5fd;">
          <strong>* Mandatory Transfer Memo / Reference:</strong> Please enter <code>{html.escape(pay_id)}</code> into the description/reference field of your transfer.
        </div>
        """
    else:
        title = f"answerr — Proforma Fatura ve Banka Havale Bilgileri ({inv_no})"
        preheader = f"answerr {plan_name} aboneliğiniz için {inv_no} numaralı proforma fatura oluşturuldu."
        badge = "PROFORMA FATURA"
        headline = "Proforma Faturanız ve Havale/EFT Talimatı"
        lead = (
            f"answerr {plan_name} ({cycle_name}) abonelik talebiniz alınmıştır. "
            f"Resmi Proforma Faturanız ekte PDF olarak sunulmuştur. Lütfen aşağıdaki resmi kurumsal banka hesaplarımıza transferi gerçekleştiriniz."
        )
        rows = [
            ("Plan", f"answerr {plan_name} ({cycle_name})"),
            ("Ödenecek Tutar", f"{tot_str} (%0 KDV — 4691 s. Teknokent İstisnası)"),
            ("Ödeme Ref (Açıklama)", pay_id),
            ("Proforma No", inv_no),
        ]
        primary_btn = "📄 Proforma Faturayı Aç (PDF)"
        secondary_btn = "🚀 Konsola Git"
        extra_title = "RESMİ KURUMSAL BANKA HESAPLARI (HAVALE / EFT / SWIFT)"
        extra_content = f"""
        <table width="100%" border="0" cellspacing="0" cellpadding="0" style="font-size: 12.5px; line-height: 1.6; color: #cbd5e1;">
          <tr><td style="color: #64748b; width: 110px;">Banka:</td><td style="font-weight: 600; color: #fff;">TEB (Türk Ekonomi Bankası A.Ş.) — Adana Toros Şb. (446)</td></tr>
          <tr><td style="color: #64748b;">SWIFT / BIC:</td><td style="font-family: monospace; font-weight: 700; color: #38bdf8;">TEBUTRIS</td></tr>
          <tr><td style="color: #64748b;">Alıcı Unvanı:</td><td style="font-weight: 600; color: #fff;">ITOUCH BİLİŞİM SİSTEMLERİ MÜHENDİSLİK DANIŞMANLIK SAN. VE TİC. LTD. ŞTİ.</td></tr>
          <tr><td style="color: #64748b;">SWIFT Alıcı Adı:</td><td style="color: #34d399; font-weight: 600;">ITOUCH BILISIM SISTEMLERI LTD. STI. <span style="color: #64748b; font-size: 11px;">(Yurt dışı transferler)</span></td></tr>
          <tr><td style="color: #64748b; padding-top: 6px;">TRY IBAN:</td><td style="font-family: monospace; font-weight: 700; color: #fff; padding-top: 6px;">TR92 0003 2000 0000 0070 5754 65</td></tr>
          <tr><td style="color: #64748b;">USD ($) IBAN:</td><td style="font-family: monospace; font-weight: 700; color: #fff;">TR83 0003 2000 0000 0088 9467 48</td></tr>
          <tr><td style="color: #64748b;">EUR (€) IBAN:</td><td style="font-family: monospace; font-weight: 700; color: #fff;">TR28 0003 2000 0000 0088 9467 68</td></tr>
          <tr><td style="color: #64748b;">Base USDC:</td><td style="font-family: monospace; font-size: 11px; color: #94a3b8;">0x4945ef6e124eea2176ddf050b33db42b0ae8c7f7</td></tr>
        </table>
        <div style="margin-top: 12px; padding: 8px 12px; background: rgba(59, 130, 246, 0.1); border-left: 3px solid #3b82f6; border-radius: 4px; font-size: 12px; color: #93c5fd;">
          <strong>* Zorunlu Transfer Açıklaması:</strong> Lütfen havale/EFT açıklama alanına <code>{html.escape(pay_id)}</code> referans numarasını yazınız.
        </div>
        """

    return _wrap_email(
        title=title,
        preheader=preheader,
        badge_text=badge,
        badge_variant="blue",
        headline=headline,
        lead=lead,
        rows=rows,
        primary_btn_text=primary_btn,
        primary_btn_url=inv_dl_url,
        secondary_btn_text=secondary_btn,
        secondary_btn_url="https://answerr.me/pro/console/",
        extra_box_title=extra_title,
        extra_box_html=extra_content,
        lang=lang,
    )
