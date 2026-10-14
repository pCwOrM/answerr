"""
Natural language (Turkish / English) -> draft policy compiler.

Deterministic and rule-based on purpose: every rule it emits points back to the
sentence it came from, every guess it has to make becomes a question for the
author, and the draft is never registered by this module. The draft is then
probed with generated test vectors and the executable checks in policy_checks.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

import policy_checks
import policy_kernel as K

# --------------------------------------------------------------- vocabulary
DENY_PAT = re.compile(r"(izin verme|izin vermeyin|reddet|engelle|yasakla|durdur|bloke|"
                      r"\bblock|\bdeny|\breject|\bforbid|\brefuse|never allow|do not allow|don't allow|\bprevent|\bstop|"
                      r"may not|must not|cannot|can't|not allowed|yapamaz|edemez)")
REVIEW_PAT = re.compile(r"(incele|insana|insan onay|onaya|onay iste|manuel|elle kontrol|3ds|3-d secure|\bmfa\b|"
                        r"\breview|\bhuman|approval|\bhold\b|escalate|devret|kuyrug|kontrole)")
ALLOW_PAT = re.compile(r"(izin ver(?!me)|otomatik onay|gecir|\ballow|\bpermit|auto.?approve)")
UNKNOWN_PAT = re.compile(r"(bilinmeyen|taninmayan|sema disi|unknown|unrecognized|out of schema)")

NUM_PAT = re.compile(r"(?<![\w.])(\d{1,3}(?:[.,]\d{3})+|\d+(?:[.,]\d+)?)\s*(bin|k|milyon|million|m)?(?![\w])")

GT_AFTER = ["uzerinde", "uzeri", "ustunde", "ustu", "fazla", "asan", "asarsa", "asiyorsa", "buyuk",
            "uzerindeyse", "ustundeyse", "fazlaysa", "ten fazla", "dan fazla", "den fazla", "tan fazla"]
GE_AFTER = ["ve uzeri", "veya uzeri", "ve ustu", "veya daha fazla", "ya da daha fazla", "or more"]
LT_AFTER = ["altinda", "alti", "az", "kucuk", "altindaysa", "ten az", "dan az", "den az"]
LE_AFTER = ["ve alti", "veya alti", "or less", "or fewer"]
GT_BEFORE = ["above", "over", "more than", "greater than", "exceeds", "exceeding", "higher than"]
GE_BEFORE = ["at least", "en az", "minimum"]
LT_BEFORE = ["below", "under", "less than", "fewer than", "lower than"]
LE_BEFORE = ["at most", "en fazla", "maximum", "up to"]

CURRENCY = ["dolar", "usd", "$", "tl", "lira", "euro", "eur", "try", "₺", "€"]

CONCEPTS = {
    "amount": {"words": ["tutar", "tutari", "amount", "odeme", "payment", "islem tutari", "transaction", "fiyat", "price"],
               "field_tokens": ["amount", "tutar", "total", "price", "value", "cart"],
               "canonical": "amount",
               "aliases": ["amount_usd", "amount_try", "cart_value", "transaction_amount", "tutar"]},
    "failures": {"words": ["hata", "hatali", "deneme", "basarisiz", "failed", "failure", "attempt", "retry", "yanlis sifre"],
                 "field_tokens": ["failed", "fail", "failures", "attempts", "attempt", "errors", "retries", "hata", "deneme"],
                 "canonical": "failed_attempts", "aliases": ["failures", "retries"]},
    "rate": {"words": ["saniyede", "dakikada", "istek", "request", "rate", "velocity", "frequency", "hiz", "rps", "per second"],
             "field_tokens": ["rate", "frequency", "freq", "velocity", "rps", "qps", "requests", "req"],
             "canonical": "req_frequency", "aliases": ["velocity", "request_rate"]},
    "risk": {"words": ["risk skoru", "risk puani", "risk score", "fraud score", "dolandiricilik skoru"],
             "field_tokens": ["risk", "fraud"], "canonical": "risk_score", "aliases": ["fraud_score"]},
    "trust": {"words": ["guven skoru", "guven puani", "trust score", "reputation"],
              "field_tokens": ["trust", "reputation", "guven"], "canonical": "trust_score", "aliases": []},
}

# Turkish / English action words -> tool tokens the kernel understands
TOOL_WORDS = {
    "sil": "delete", "silme": "delete", "siler": "delete", "silmek": "delete", "silinmesi": "delete",
    "silsin": "delete", "silebilir": "delete", "delete": "delete",
    "drop": "drop", "dusur": "drop", "truncate": "truncate", "bosalt": "truncate",
    "kaldir": "remove", "remove": "remove", "purge": "purge", "wipe": "wipe", "destroy": "destroy",
    "aktar": "transfer", "transfer": "transfer", "transferi": "transfer", "havale": "wire", "eft": "wire", "wire": "wire",
    "ode": "pay", "odeme": "pay", "pay": "pay", "refund": "refund", "iade": "refund", "withdraw": "withdraw", "cek": "withdraw",
    "calistir": "exec", "exec": "exec", "shell": "shell", "sudo": "sudo",
    "guncelle": "update", "update": "update", "yaz": "write", "write": "write",
    "gonder": "send", "send": "send", "email": "email", "eposta": "email",
    "yayinla": "deploy", "deploy": "deploy", "publish": "publish",
    "oku": "read", "read": "read", "listele": "list", "list": "list", "search": "search",
}
TOOL_CONTEXT = re.compile(r"(arac|tool|ajan|agent|komut|command|fonksiyon|function|islem|veritabani|database|sql|mcp)")

ROLE_WORDS = {
    "misafir": ["guest", "anonymous"], "guest": ["guest", "anonymous"], "anonim": ["guest", "anonymous"],
    "anonymous": ["guest", "anonymous"], "ziyaretci": ["guest", "visitor"],
    "bot": ["bot", "attacker"], "saldirgan": ["attacker", "bot"], "attacker": ["attacker", "bot"],
    "yonetici": ["admin"], "admin": ["admin"],
}


def _norm(s: str) -> str:
    return K.normalize_text(s)


def _parse_number(raw: str, mult: Optional[str]) -> float:
    s = raw
    if re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", s):
        s = re.sub(r"[.,]", "", s)
    else:
        s = s.replace(",", ".")
    v = float(s)
    if mult in ("bin", "k"):
        v *= 1000
    elif mult in ("milyon", "million", "m"):
        v *= 1_000_000
    return int(v) if v.is_integer() else v


def _comparator(before: str, after: str) -> Optional[str]:
    a = " " + after.strip()
    b = before.strip() + " "
    for w in GE_AFTER:
        if w in a:
            return ">="
    for w in LE_AFTER:
        if w in a:
            return "<="
    for w in GE_BEFORE:
        if b.endswith(w + " ") or (" " + w + " ") in (" " + b[-24:]):
            return ">="
    for w in LE_BEFORE:
        if b.endswith(w + " ") or (" " + w + " ") in (" " + b[-24:]):
            return "<="
    for w in GT_BEFORE:
        if (" " + w + " ") in (" " + b[-24:]):
            return ">"
    for w in LT_BEFORE:
        if (" " + w + " ") in (" " + b[-24:]):
            return "<"
    head = a[:28]
    for w in GT_AFTER:
        if re.search(r"(^|\s|')" + re.escape(w), head):
            return ">"
    for w in LT_AFTER:
        if re.search(r"(^|\s|')" + re.escape(w) + r"(\s|$|[a-z]*)", head):
            return "<"
    return None


PER_TIME = re.compile(r"(saniyede|dakikada|saatte|pencerede|per (second|minute|hour|window)|in the window|/s\b|/sn\b)")


def _concept(before: str, after: str) -> Optional[str]:
    near_after = after[:18]
    if any(c in near_after for c in CURRENCY):
        return "amount"
    if PER_TIME.search(before[-24:] + " " + after[:32]):
        return "rate"
    window = before[-48:] + " " + after[:24]
    best = None
    best_pos = -1
    for name, c in CONCEPTS.items():
        for w in c["words"]:
            pos = window.rfind(w)
            if pos > best_pos:
                best, best_pos = name, pos
    return best


def _resolve_field(concept: str, schema: List[str]) -> Tuple[str, List[str], Optional[str]]:
    c = CONCEPTS[concept]
    if not schema:
        return c["canonical"], c["aliases"], "No schema was given; used the standard field name '{}'.".format(c["canonical"])
    matches = [f for f in schema if any(t in c["field_tokens"] for t in K.tokenize(f))]
    if len(matches) == 1:
        return matches[0], [], None
    if len(matches) > 1:
        return matches[0], [], "Several fields could hold this value ({}); used '{}'.".format(", ".join(matches), matches[0])
    return c["canonical"], c["aliases"], "The schema has no field for '{}'; rule uses '{}' and will not fire until such a field is sent.".format(concept, c["canonical"])


def _effect(sn: str) -> Optional[str]:
    if REVIEW_PAT.search(sn):
        return "REVIEW"
    if DENY_PAT.search(sn):
        return "DENY"
    if ALLOW_PAT.search(sn):
        return "ALLOW"
    return None


def _split_sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    return [p.strip() for p in parts if p and p.strip()]


def compile_policy(prompt: str, gate_id: str = "draft_policy", schema: Optional[List[str]] = None,
                   sample_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    schema = list(schema or (list(sample_state.keys()) if sample_state else []))
    rules: List[Dict[str, Any]] = []
    questions: List[Dict[str, Any]] = []
    unparsed: List[str] = []
    sources: List[Dict[str, Any]] = []
    aliases: Dict[str, List[str]] = {}
    uses_tools = False
    n = 0

    for si, sentence in enumerate(_split_sentences(prompt)):
        sn = _norm(sentence)
        sn = re.sub(r"\b3\s*-\s*d\b", "3d", sn)  # "3-D Secure" is not a number
        if UNKNOWN_PAT.search(sn) and not NUM_PAT.search(sn):
            sources.append({"sentence": sentence, "rules": ["unknown_fallback"], "note": "Unknown fields go to human review."})
            continue
        eff = _effect(sn)
        made: List[str] = []

        # numeric conditions
        for m in NUM_PAT.finditer(sn):
            before, after = sn[:m.start()], sn[m.end():]
            concept = _concept(before, after)
            op = _comparator(before, after)
            raw = m.group(0).strip()
            if concept is None:
                questions.append({"sentence": sentence, "text": "Which field does '{}' refer to?".format(raw),
                                  "text_tr": "'{}' hangi alana ait?".format(raw)})
                continue
            if op is None:
                op = ">"
                questions.append({"sentence": sentence,
                                  "text": "Direction of '{}' is unclear; assumed 'greater than'.".format(raw),
                                  "text_tr": "'{}' için yön belirsiz; 'büyüktür' varsayıldı.".format(raw)})
            if op == ">" and re.search(r"\b(ustu|uzeri)\b", after[:16]) and concept == "failures":
                questions.append({"sentence": sentence,
                                  "text": "'{} and above' or 'more than {}'? Used '> {}'.".format(raw, raw, raw),
                                  "text_tr": "'{} ve üstü' mü, '{}'ten fazla' mı? '> {}' kullanıldı.".format(raw, raw, raw)})
            value = _parse_number(m.group(1), m.group(2))
            field, als, note = _resolve_field(concept, schema)
            if note:
                questions.append({"sentence": sentence, "text": note, "text_tr": note})
            if als:
                aliases[field] = als
            if eff is None:
                questions.append({"sentence": sentence, "text": "No action word found; assumed REVIEW.",
                                  "text_tr": "Eylem sözcüğü bulunamadı; İNCELE varsayıldı."})
            n += 1
            rid = "r{}_{}_{}".format(n, field, {">": "gt", ">=": "ge", "<": "lt", "<=": "le"}[op])
            rules.append({"id": rid, "field": field, "op": op, "value": value, "effect": eff or "REVIEW",
                          "reason": sentence, "source_sentence": si})
            made.append(rid)

        # tool / action words
        # drop routing phrases ("insana gönder", "send to a human") before looking for tool verbs
        sn_tools = re.sub(r"(insana|onaya|incelemeye|kuyruga|manuel)\s+\w+|send\s+(\w+\s+)?to\s+(a\s+)?(human|review)", " ", sn)
        words = re.findall(r"[a-z0-9]+", sn_tools)
        tool_tokens = []
        for w in words:
            for stem, tok in TOOL_WORDS.items():
                if w == stem or (len(stem) >= 4 and w.startswith(stem) and len(w) - len(stem) <= 4):
                    if tok not in tool_tokens:
                        tool_tokens.append(tok)
        explicit_names = re.findall(r"\b(drop|delete|truncate|transfer|wire|exec|shell|update|deploy)\b", sn)
        if tool_tokens and (TOOL_CONTEXT.search(sn) or explicit_names) and not made:
            uses_tools = True
            tool_field = next((f for f in schema if f in K.TOOL_FIELDS), "tool_name")
            n += 1
            rid = "r{}_tool_{}".format(n, "_".join(tool_tokens[:3]))
            rules.append({"id": rid, "field": tool_field, "op": "has_token", "value": tool_tokens,
                          "effect": eff or "REVIEW", "reason": sentence, "source_sentence": si})
            made.append(rid)
            if eff is None:
                questions.append({"sentence": sentence, "text": "No action word found; assumed REVIEW.",
                                  "text_tr": "Eylem sözcüğü bulunamadı; İNCELE varsayıldı."})

        # roles
        if not made:
            for w in words:
                if w in ROLE_WORDS and eff:
                    role_field = next((f for f in schema if any(t in K.SIG_ROLE for t in K.tokenize(f))), "user_role")
                    n += 1
                    rid = "r{}_role_{}".format(n, w)
                    rules.append({"id": rid, "field": role_field, "op": "has_token", "value": ROLE_WORDS[w],
                                  "effect": eff, "reason": sentence, "source_sentence": si})
                    made.append(rid)
                    break

        if made and re.search(r"\b(ve|and)\b", sn) and len(made) > 1:
            questions.append({"sentence": sentence,
                              "text": "Conditions joined with 'and' became separate rules (either one triggers). Should they apply only together?",
                              "text_tr": "'ve' ile bağlanan koşullar ayrı kurallar oldu (biri yeter). Birlikte mi geçerli olmalı?"})
        if made:
            sources.append({"sentence": sentence, "rules": made})
        else:
            unparsed.append(sentence)
            questions.append({"sentence": sentence, "text": "This sentence did not become a rule.",
                              "text_tr": "Bu cümle bir kurala dönüşmedi."})

    fields = list(dict.fromkeys(schema + [r["field"] for r in rules]))
    spec: Dict[str, Any] = {
        "gate_id": gate_id,
        "version": "1.0.0-draft",
        "title": (prompt.strip().split("\n")[0])[:80],
        "source_prompt": prompt,
        "unknown_fallback": "abstain_review",
        "fields": fields,
        "required_fields": [],
        "field_aliases": aliases,
        "hard_rules": [{k: v for k, v in r.items() if k != "source_sentence"} for r in rules],
        "feature_weights": {},
    }
    if uses_tools:
        spec["tool_policy"] = dict(K.DEFAULT_TOOL_POLICY)
    spec["policy_seal"] = K.policy_seal(spec)

    tests = generate_tests(spec, sample_state)
    checks = policy_checks.run_all(spec)
    return {
        "status": "needs_answers" if questions else "ready_for_review",
        "policy_spec": spec,
        "policy_seal": spec["policy_seal"],
        "sources": sources,
        "unparsed": unparsed,
        "questions": questions,
        "tests": tests,
        "tests_passed": sum(1 for t in tests if t["passed"]),
        "tests_total": len(tests),
        "checks": checks,
        "registered": False,
    }


def generate_tests(spec: Dict[str, Any], sample_state: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    tests = []
    for r in spec.get("hard_rules", []):
        for hit in (True, False):
            v = policy_checks.probe_value_for(r, hit)
            if v is None:
                continue
            st = {r["field"]: v}
            res = K.evaluate(st, spec, False)
            fired = any(c["rule_id"] == r["id"] for c in res["candidates"])
            if hit:
                ok = fired and K.SEVERITY[res["verdict"]] >= K.SEVERITY[r["effect"]]
                expect = "{} (or stricter)".format(r["effect"])
            else:
                ok = not fired
                expect = "rule {} not triggered".format(r["id"])
            tests.append({"rule_id": r["id"], "kind": "hit" if hit else "miss", "state": st,
                          "expect": expect, "verdict": res["verdict"], "matched_rule": res["rule_id"],
                          "passed": ok})
    ood = {"zz_unknown_probe_field": 1}
    res = K.evaluate(ood, spec, False)
    tests.append({"rule_id": "unknown_fallback", "kind": "ood", "state": ood, "expect": "REVIEW",
                  "verdict": res["verdict"], "matched_rule": res["rule_id"], "passed": res["verdict"] == "REVIEW"})
    if sample_state:
        res = K.evaluate(sample_state, spec, False)
        tests.append({"rule_id": "sample_state", "kind": "sample", "state": sample_state, "expect": "(your sample)",
                      "verdict": res["verdict"], "matched_rule": res["rule_id"], "passed": True})
    return tests
