"""Compiler tests: the studio templates must compile to the intended rules (TR and EN)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import policy_compiler as C  # noqa: E402

AGENT = {"tool_name": "delete_customer_ledger", "amount_usd": 7200, "failed_attempts": 1, "auth_status": True}
PAY = {"amount_try": 31000, "velocity": 2, "risk_score": 0.42, "known_device": True}
API = {"user_role": "guest", "req_frequency": 12, "failed_attempts": 2}

CASES = [
    ("Otonom AI ajanı veritabanında drop, delete veya truncate aracı çağırmak isterse reddet. İşlem tutarı 5000 dolar "
     "üzerinde ise insana gönder. Hatalı deneme sayısı 3 üstündeyse engelle. Bilinmeyen alanlarda insana devret.", AGENT,
     {("tool_name", "has_token", "DENY"), ("amount_usd", ">", "REVIEW"), ("failed_attempts", ">", "DENY")}, "DENY"),
    ("If the agent calls a drop, delete or truncate tool, deny it. Send amounts above 5,000 USD to a human. "
     "Block when failed attempts are more than 3. Unknown fields go to human review.", AGENT,
     {("tool_name", "has_token", "DENY"), ("amount_usd", ">", "REVIEW"), ("failed_attempts", ">", "DENY")}, "DENY"),
    ("Tutar 25.000 TL ve üzeri ise 3D Secure incelemesine gönder. Saniyede 15 veya daha fazla deneme varsa reddet. "
     "Risk skoru 0,8 üzerindeyse insana devret.", PAY,
     {("amount_try", ">=", "REVIEW"), ("velocity", ">=", "DENY"), ("risk_score", ">", "REVIEW")}, "REVIEW"),
    ("Send amounts of 25,000 TRY or more to 3-D Secure review. Deny when there are 15 or more attempts per window. "
     "Hand to a human when the risk score is above 0.8.", PAY,
     {("amount_try", ">=", "REVIEW"), ("velocity", ">=", "DENY"), ("risk_score", ">", "REVIEW")}, "REVIEW"),
    ("Misafir kullanıcıları insana devret. Saniyede 100 istek üzerinde engelle. Başarısız deneme 10 veya daha fazla ise reddet.", API,
     {("user_role", "has_token", "REVIEW"), ("req_frequency", ">", "DENY"), ("failed_attempts", ">=", "DENY")}, "REVIEW"),
]


@pytest.mark.parametrize("prompt,sample,expected,sample_verdict", CASES)
def test_templates(prompt, sample, expected, sample_verdict):
    r = C.compile_policy(prompt, "t_draft", sample_state=sample)
    got = {(h["field"], h["op"], h["effect"]) for h in r["policy_spec"]["hard_rules"]}
    assert got == expected
    assert r["questions"] == [] and r["unparsed"] == []
    assert r["tests_passed"] == r["tests_total"]
    assert all(c["passed"] for c in r["checks"])
    assert [t["verdict"] for t in r["tests"] if t["kind"] == "sample"] == [sample_verdict]
    assert r["registered"] is False


def test_unparsed_sentence_becomes_question():
    r = C.compile_policy("Müşteri memnuniyeti önemlidir.", "t_draft")
    assert r["unparsed"] and r["questions"] and r["status"] == "needs_answers"


def test_missing_schema_field_is_reported():
    r = C.compile_policy("Tutar 5000 dolar üzerindeyse reddet.", "t_draft", schema=["user_role"])
    assert any("no field" in q["text"] for q in r["questions"])
