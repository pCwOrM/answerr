title: Terms of Service
description: Terms of service for the answerr decision API, console and website.
order: 1
---
# Terms of Service

**Version:** {{legal_version}}

These terms govern the use of the answerr decision API, the answerr console, the answerr.me website and the related documentation (the "**Service**") provided by {{company.legal_name}} ("**ITouch**", "we"). By creating an account or using the Service you accept these terms. If you accept them on behalf of an organisation, you confirm that you are authorised to bind it.

## 1. Parties and contact

- **Provider:** {{company.legal_name}}
- **MERSIS:** {{company.mersis}} · **Tax:** {{company.tax}} · {{company.trade_registry}}
- **Address:** {{company.address}}
- **E-mail:** {{company.email}} · **Phone:** {{company.phone}} · **Registered e-mail (KEP):** {{company.kep}}

## 2. The Service

answerr is software that compiles decision policies written in natural language into explicit rules and returns, for each request, an **ALLOW**, **REVIEW** (hand over to a human) or **DENY** verdict. Verdicts are deterministic: the same policy and the same input give the same result. No AI model runs at decision time.

The Service covers the API, the console (account, API keys, usage, decision log, review queue, shadow-mode and backtest reports, plan and payment details) and the documentation. Plan contents are published on the [Pricing](../pricing.html) page and at `GET /v1/plans`.

## 3. Account and security

1. Accounts are opened with a work e-mail; sign-in uses single-use links sent to that address.
2. API keys are shown only when they are created. You are responsible for keeping them secret and for the requests made with them. Revoke a key in the console as soon as you suspect it has leaked.
3. You can add members to the account (owner, admin and reviewer roles). The account owner is responsible for what members do.

## 4. Acceptable use

You may not use the Service for:

- an unlawful purpose, automated decisions that infringe people's fundamental rights and freedoms, or discrimination;
- attempts to get around the Service's security, quotas or rate limits, or to access other users' data;
- copying the Service by reverse engineering to offer a competing service (the licences of open-source components remain unaffected);
- putting special categories of personal data (health, biometric, criminal convictions and the like) into decision requests when they are not necessary.

## 5. Automated decisions and responsibility

answerr is a decision **tool**; whether to act on a verdict, and the consequences of doing so, are yours. You write and approve your policies. For operations with significant effects (payments, access, deleting data) we recommend routing REVIEW verdicts to human review and giving people a way to object. The right of individuals not to be subject to decisions based solely on automated processing (GDPR Art. 22, KVKK Art. 11/1-(g)) is your obligation towards your own customers.

## 6. Plans, quotas and fees

1. Plans other than the free Explore plan are paid. Customers in Türkiye pay the Turkish-lira prices on the [Pricing](../pricing.html) page; customers abroad and customers paying with crypto assets (USDC / USDT) pay the US-dollar prices. Under Law No. 4691 and Temporary Article 20/1 of VAT Law No. 3065 (Technopark R&D software exemption), and the export-of-services exemption for customers abroad, invoices carry 0% VAT. The total is shown before you pay.
2. A decision is one call to `/v1/decide` or `/v1/gates/{id}/decide`, or one record in `/v1/backtest`. Compiling policies, reading, health checks and running the open kernel in your own environment are not counted.
3. When the monthly quota is used up, decision calls return HTTP 429 unless overage is enabled. With overage enabled, each started block of 1,000 decisions is billed at the plan's overage price.
4. Quotas and usage counters reset at the start of each calendar month, Türkiye time. A paid plan period is 31 days for monthly and 366 days for yearly payment and does not renew automatically. Payment and refund terms are in the [Distance Sales Agreement](mesafeli-satis.html) and [Cancellation & Refund](iade-iptal.html).
5. Price changes are announced by e-mail at least 30 days in advance; they never apply to periods already paid, only to later purchases. Price-lock commitments given to founding customers apply for the period stated in writing.

## 7. Data

For the data you send in decision requests **you are the controller** and ITouch is the **processor**; this relationship is governed by the [Data Processing Agreement](veri-isleme.html). ITouch is the controller of your account data; see the [Privacy notice](kvkk-aydinlatma.html) and the [Privacy Policy](gizlilik.html). The decision log is deleted automatically when your plan's retention period ends.

## 8. Service level

The Service is provided "as is". Unless your plan says otherwise, no specific availability is committed. Service status is published on the [Status](../status.html) page. Enterprise SLAs are set in a separate agreement.

## 9. Intellectual property

The rights in the Service, software, policy kernel, compiler and brands belong to ITouch; open-source components are subject to their own licences (e.g. BSL 1.1). The policies you write and the data you send are yours. We may use only anonymous, aggregated usage statistics to improve the Service.

## 10. Limitation of liability

To the extent permitted by law, ITouch's total liability under these terms is limited to the fees you paid for the Service in the 12 months before the event giving rise to the claim. We are not liable for indirect loss, loss of profit, or the consequences of your policies or of how you act on verdicts. Liability for intent and gross negligence, and the mandatory rules of consumer law (Law No. 6502) for users who are consumers, remain unaffected.

## 11. Suspension and termination

You can close your account at any time. We may suspend or close an account for a serious breach of these terms, unpaid invoices or use that threatens the security of the Service, with notice where possible. On closure, API keys and sessions are revoked, decision records are deleted at the end of the retention period, and invoice records that must be kept by law are retained.

## 12. Changes

We may change these terms. Material changes are announced by e-mail at least 30 days before they take effect. If you do not accept a change you may close your account before it takes effect, and the unused part of the paid period is refunded. Continuing to use the Service after the effective date means you accept the new terms.

## 13. Governing law and jurisdiction

These terms are governed by the laws of the Republic of Türkiye. For disputes between merchants, the courts and enforcement offices of Adana have jurisdiction. If you are a consumer, your right to apply to consumer arbitration committees and consumer courts remains unaffected.
