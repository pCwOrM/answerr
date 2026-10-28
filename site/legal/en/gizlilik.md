title: Privacy Policy
description: What data answerr keeps, why, for how long and how it is protected.
order: 3
---
# Privacy Policy

**Version:** {{legal_version}}

In short: we try not to keep the data you send for decisions. The decision log stores field **names**, the verdict, the rule and the latency; it does not store field **values**. The one exception is decisions handed to a human: the state vector is kept in the review queue so that the reviewer can decide. You can turn this off in the console.

## Decision requests

| What | Kept? | For how long? |
| --- | --- | --- |
| Verdict, rule id, reason, latency, policy seal | Yes | Plan retention period |
| Names of the fields sent | Yes | Plan retention period |
| Values of the fields sent | No | — |
| State vector of decisions handed to a human | Yes (can be turned off) | Plan retention period; unresolved items expire after 7 days |
| Your reference id (`external_id`) | Yes | Plan retention period |
| The actual outcome you report in shadow mode | Yes | Plan retention period |

### Anonymous demo requests and research telemetry

Demo requests made without an API key (the Black Box on answerr.me and similar pages) are not written to any customer decision log. They are sent to **research telemetry** to develop the werr research engine.

- **What is sent:** the first 20 state fields, the first 100 characters of text values, the question text and the verdict.
- **What is masked:** field names that carry passwords, keys or secrets are sent as `[REDACTED]`; e-mail addresses and values that look like access keys are masked too.
- **What is not recorded:** IP addresses are not written to telemetry.
- **How it may be used:** these records may be used in anonymous research datasets. Do not type personal data into the demo.

Customer traffic that arrives with an API key is **not** sent to telemetry, unless the request explicitly opts in with `werr_params.telemetry_opt_in: true`.

## Account data

E-mail, company name, members, plan, billing details and usage counts are kept while your account is open. Details are in the [Privacy notice](kvkk-aydinlatma.html).

## Payments

Card payments are made on iyzico's secure payment page. The card number, expiry date and security code never reach answerr; we keep only the amount, the status, the payment reference and the last 4 digits. For bank transfers we keep the transfer reference, and for crypto payments the transaction hash and network. Your billing details are used to issue the e-Archive / e-Invoice.

## Security

- API keys, sessions and sign-in links are stored only as SHA-256 hashes; we cannot see the keys themselves.
- Connections are encrypted with TLS. Webhooks are signed with HMAC-SHA256 and sent only to public https addresses.
- Access is role-based (owner, admin, reviewer). Account actions are written to an event log you can see in the console.

## AI and training

No model runs at decision time. Your data is not used to train any AI model.

## Deletion

To close your account or ask for your data to be deleted, write to {{company.email}}. Invoice records are kept for the legally required period.
