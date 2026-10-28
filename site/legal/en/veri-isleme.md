title: Data Processing Agreement
description: Data processing terms between the customer (controller) and ITouch (processor).
order: 8
---
# Data Processing Agreement (DPA)

**Version:** {{legal_version}}

This agreement is an annex to the [Terms of Service](kullanim-sartlari.html). The customer (the "**Controller**") engages {{company.legal_name}} (the "**Processor**") for the personal data it sends in answerr decision requests. It is intended to meet GDPR Article 28 and KVKK Article 12.

## 1. Subject and duration

- **Subject:** evaluating the state fields sent in decision requests with the policy kernel; keeping the decision log, the review queue and shadow-mode reports.
- **Data subjects:** the Controller's customers, users or employees, as determined by the Controller.
- **Data categories:** the fields the Controller sends. Special categories of personal data should not be sent.
- **Duration:** for the term of the service and the plan's retention period.

## 2. Processor obligations

1. Processes data only on the Controller's documented instructions (API calls and console settings).
2. Does not store field values in the decision log; stores only field names, the verdict, the rule and the latency. For the review queue the state vector is kept unless the Controller turns this off.
3. Limits access to authorised personnel bound by confidentiality.
4. Takes appropriate technical and organisational measures (GDPR Art. 32, KVKK Art. 12): TLS, hashed keys and sessions, role-based access, event log, automatic retention, backups.
5. Notifies the Controller of a personal-data breach without undue delay and at the latest within 72 hours of becoming aware of it.
6. Reasonably assists the Controller with data-subject requests and supervisory-authority inquiries.
7. At the end of the service, deletes the data at the end of the retention period, subject to legal retention obligations.

## 3. Sub-processors

| Sub-processor | Service | Location |
| --- | --- | --- |
| Contabo GmbH (Germany) | Server hosting (decision requests, decision log, review queue) | European Union |

The payment institution (iyzico), the e-invoice provider and Google reCAPTCHA have no access to decision-request data; they are services ITouch uses for its own customer and account data and are described in the [Privacy notice](kvkk-aydinlatma.html).

New sub-processors are announced to the Controller at least 30 days before they are added; the Controller may object on reasonable grounds.

## 4. International transfers

Hosting is in the European Union. For transfers from Türkiye, the parties sign the standard contract required under KVKK Article 9 and the Regulation on the Procedures and Principles for the Transfer of Personal Data Abroad, and notify the Board within the time limit. For Controllers that need hosting in Türkiye, on-premise or in-country deployment is offered on the Enterprise plan.

## 5. Audit

Once a year, with reasonable notice, the Controller may request information and documents showing compliance with this agreement.

*An English translation for convenience; the Turkish text prevails in case of conflict.*
