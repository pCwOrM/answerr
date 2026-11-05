import os
import sys
from playwright.sync_api import sync_playwright

def generate_previews():
    from commerce import mail_templates

    wire_en = mail_templates.render_wire_approved_html(
        lang="en",
        plan_name="Pro",
        cycle_name="Monthly (1 Month)",
        until_str="04.12.2026",
        tot_str="99.00 USD",
        inv_no="INV-2026-0CA652A1",
        inv_dl_url="https://api.answerr.me/v1/invoice/preview_sample.pdf",
        pay_id="pay_sample_demo_123456",
        api_key="ans_live_demo_dummy_key_00000000000000000000"
    )

    wire_tr = mail_templates.render_wire_approved_html(
        lang="tr",
        plan_name="Pro",
        cycle_name="Aylık (31 Gün / 1 Ay)",
        until_str="04.12.2026",
        tot_str="99.00 USD",
        inv_no="INV-2026-0CA652A1",
        inv_dl_url="https://api.answerr.me/v1/invoice/preview_sample.pdf",
        pay_id="pay_sample_demo_123456",
        api_key="ans_live_demo_dummy_key_00000000000000000000"
    )

    req_en = mail_templates.render_plan_request_html(
        lang="en",
        plan_name="Pro",
        cycle_name="Monthly (1 Month)",
        tot_str="99.00 USD",
        inv_no="PRO-2026-5244743F",
        inv_dl_url="https://api.answerr.me/v1/invoice/preview_sample.pdf",
        pay_id="pay_sample_demo_123456"
    )

    req_tr = mail_templates.render_plan_request_html(
        lang="tr",
        plan_name="Pro",
        cycle_name="Aylık (31 Gün / 1 Ay)",
        tot_str="99.00 USD",
        inv_no="PRO-2026-5244743F",
        inv_dl_url="https://api.answerr.me/v1/invoice/preview_sample.pdf",
        pay_id="pay_sample_demo_123456"
    )

    os.makedirs("email_previews", exist_ok=True)
    with open("email_previews/wire_approved_en.html", "w", encoding="utf-8") as f: f.write(wire_en)
    with open("email_previews/wire_approved_tr.html", "w", encoding="utf-8") as f: f.write(wire_tr)
    with open("email_previews/plan_request_en.html", "w", encoding="utf-8") as f: f.write(req_en)
    with open("email_previews/plan_request_tr.html", "w", encoding="utf-8") as f: f.write(req_tr)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 640, "height": 900})
        for name in ["wire_approved_en", "wire_approved_tr", "plan_request_en", "plan_request_tr"]:
            page.goto(f"file:///{os.path.abspath(f'email_previews/{name}.html')}")
            page.screenshot(path=f"email_previews/{name}.png", full_page=True)
            print(f"Captured email_previews/{name}.png")
        browser.close()

if __name__ == "__main__":
    generate_previews()
