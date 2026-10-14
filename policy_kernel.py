"""
answerr policy kernel (Python) — deterministic verdict layer.

Mirrors js/policy-kernel.js line for line. Both runtimes are checked against
tests/policy_vectors.json, so the same state + policy gives the same verdict
on the server, in the browser and in Node.

Verdicts: ALLOW, REVIEW (hand to a human), DENY.
Combination rule: the most severe candidate wins (DENY > REVIEW > ALLOW),
like an explicit-deny-wins access policy. The question text never changes
the verdict; it only decides how the verdict is expressed as a boolean.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from typing import Any, Dict, List, Optional

KERNEL_VERSION = "1.0.0"

SEVERITY = {"ALLOW": 0, "REVIEW": 1, "DENY": 2}
LABELS = {"ALLOW": "ALLOWED", "REVIEW": "ABSTAIN_REVIEW", "DENY": "DENIED"}

RISK_ALLOW_MAX = 0.2   # risk <= this -> ALLOW (when nothing else applies)
RISK_DENY_MIN = 1.4    # risk >= this -> DENY

TOOL_FIELDS = ["tool", "tool_name", "action", "command", "operation", "method",
               "endpoint", "function", "function_name"]

# Tool verb classes. Matching is on whole tokens of the tool name, after
# splitting on _ - . / : spaces and camelCase, so "bulk_delete_users" and
# "deleteUser" both yield the token "delete".
TOOL_CLASSES = {
    "destructive": ["drop", "delete", "del", "remove", "rm", "rmdir", "unlink", "truncate",
                    "destroy", "purge", "wipe", "erase", "kill", "terminate", "shutdown",
                    "revoke", "sil", "silme", "kaldir", "yoket"],
    "privileged": ["exec", "execute", "shell", "bash", "sudo", "eval", "spawn", "chmod",
                   "chown", "grant", "escalate", "impersonate", "su", "ssh", "private",
                   "secret", "secrets", "credential", "credentials", "password", "passwd",
                   "calistir"],
    "financial": ["transfer", "wire", "withdraw", "pay", "payment", "payout", "refund",
                  "charge", "swap", "trade", "buy", "sell", "order", "purchase", "mint",
                  "burn", "approve", "sign", "odeme", "ode", "aktar", "havale", "eft", "satin"],
    "write": ["update", "write", "insert", "create", "add", "put", "patch", "set", "modify",
              "edit", "upload", "deploy", "publish", "release", "merge", "push", "commit",
              "send", "email", "mail", "post", "invite", "rename", "move", "migrate",
              "install", "import", "export", "restart", "reboot", "scale", "enable",
              "disable", "assign", "reset", "guncelle", "yaz", "ekle", "olustur", "gonder",
              "yayinla"],
    "read": ["read", "get", "list", "search", "query", "view", "fetch", "ping", "status",
             "describe", "show", "count", "find", "lookup", "inspect", "check", "health",
             "summary", "summarize", "preview", "oku", "listele", "ara", "sorgula",
             "goruntule"],
}
# Two-token combinations that make an otherwise harmless verb destructive.
TOOL_COMBOS = [("format", ["disk", "drive", "volume", "partition"], "destructive")]

DEFAULT_TOOL_POLICY = {
    "destructive": "DENY",
    "privileged": "DENY",
    "financial": "REVIEW",
    "write": "REVIEW",
    "read": "ALLOW",
    "unknown": "REVIEW",
}
CLASS_ORDER = ["destructive", "privileged", "financial", "write", "read"]
# Words that are verbs in one tool name and nouns in another ("create_order" vs
# "get_order_status"). After a leading read verb they are read as nouns and ignored.
AMBIGUOUS_NOUNS = ["order", "orders", "status", "payment", "payments", "post", "posts",
                   "email", "emails", "mail", "release", "trade", "trades", "charge",
                   "charges", "transfer", "transfers", "update", "updates", "export",
                   "import", "sign", "set", "count", "summary", "health", "preview",
                   "check", "view"]

# Signal vocabulary. A state key is "recognized" without a policy when every
# token of the key is in KNOWN_VOCAB ("coffee_temp" is not: "coffee" is unknown).
SIG_FAILURE = ["fail", "failed", "failure", "failures", "error", "errors", "attempt",
               "attempts", "retry", "retries", "hata", "hatali", "deneme", "basarisiz"]
SIG_RATE = ["rate", "freq", "frequency", "velocity", "rps", "qps", "hiz", "burst"]
SIG_AMOUNT = ["amount", "tutar", "price", "total", "exposure", "borrow", "value"]
SIG_TRUST_BOOL = ["auth", "authenticated", "verified", "valid", "known", "biometric",
                  "mfa", "dogrulandi", "dogrulanmis", "safe"]
SIG_HAZARD_BOOL = ["suspicious", "anomaly", "attack", "threat", "exploit", "mismatch",
                   "blacklisted", "supheli", "anomali", "sandwich", "burst"]
SIG_ROLE = ["role", "rol", "actor"]
SIG_RISK_SCORE = ["risk", "fraud", "anomaly", "drift"]
SIG_TRUST_SCORE = ["trust", "reputation", "guven"]
SIG_TEMP = ["temp", "temperature", "sicaklik"]
SIG_LOAD = ["torque", "tork", "load", "yuk"]
SIG_VIBRATION = ["vibration", "titresim"]
SIG_PROXIMITY = ["proximity", "distance", "mesafe"]
QUALIFIERS = ["user", "tool", "name", "action", "command", "operation", "method", "endpoint",
              "function", "status", "count", "usd", "try", "tl", "eur", "ms", "pct",
              "percent", "sec", "per", "min", "score", "id", "uuid", "tenant", "req",
              "request", "requests", "num", "number", "level", "cart", "card", "device",
              "geo", "ip", "country", "account", "session", "time", "window", "transaction",
              "kmh", "celsius", "nm", "g", "m", "joint", "motor", "cpu", "core", "actuator",
              "ratio", "kullanici", "islem", "sayisi", "is", "has"]

KNOWN_VOCAB = set(
    SIG_FAILURE + SIG_RATE + SIG_AMOUNT + SIG_TRUST_BOOL + SIG_HAZARD_BOOL + SIG_ROLE
    + SIG_RISK_SCORE + SIG_TRUST_SCORE + SIG_TEMP + SIG_LOAD + SIG_VIBRATION
    + SIG_PROXIMITY + QUALIFIERS + TOOL_FIELDS
)

ROLE_RISK = [
    (["admin", "root", "superuser", "owner", "yonetici", "kurucu"], -1.5),
    (["member", "user", "kullanici", "uye", "employee", "staff"], -0.8),
    (["service", "internal", "system", "sistem"], -0.5),
    (["agent", "bot_agent", "assistant", "ajan"], 0.3),
    (["guest", "anonymous", "anonim", "misafir", "unverified", "visitor"], 0.9),
    (["suspicious", "supheli"], 1.8),
    (["attacker", "malicious", "hacker", "bot", "saldirgan", "zararli"], 2.5),
]

DENY_POLARITY = re.compile(
    r"\b(block|deny|reject|refuse|forbid|halt|stop|quarantine|shutdown|revert|"
    r"engelle|reddet|durdur|blokla|kapat|karantina|yasakla)"
)

META_KEYS = {"_task_id", "presetId", "warmup", "ping"}


# ---------------------------------------------------------------- helpers
def normalize_text(s: Any) -> str:
    s = str(s)
    s = s.replace("İ", "i")
    s = s.lower()
    s = s.replace("̇", "")
    table = str.maketrans({"ı": "i", "ş": "s", "ğ": "g", "ü": "u", "ö": "o", "ç": "c",
                           "â": "a", "î": "i", "û": "u"})
    return s.translate(table)


def tokenize(s: Any) -> List[str]:
    raw = str(s)
    raw = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", raw)
    raw = normalize_text(raw)
    return [t for t in re.split(r"[^a-z0-9]+", raw) if t]


def round4(x: float) -> float:
    return math.floor(x * 10000.0 + 0.5) / 10000.0


def is_number(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _canon(o: Any) -> Any:
    if isinstance(o, dict):
        return {k: _canon(o[k]) for k in sorted(o.keys())}
    if isinstance(o, list):
        return [_canon(x) for x in o]
    if isinstance(o, float) and o.is_integer():
        return int(o)
    return o


def canonical_json(o: Any) -> str:
    return json.dumps(_canon(o), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def policy_seal(policy: Dict[str, Any]) -> str:
    body = {k: v for k, v in (policy or {}).items() if k not in ("policy_seal", "seal")}
    return "sha256:" + hashlib.sha256(canonical_json(body).encode("utf-8")).hexdigest()


def _any_in(tokens: List[str], vocab: List[str]) -> bool:
    return any(t in vocab for t in tokens)


# ---------------------------------------------------------------- tool class
def classify_tool(value: Any) -> Dict[str, Any]:
    tokens = tokenize(value)
    classes = []
    first_verb = None
    for t in tokens:
        hit = [c for c in CLASS_ORDER if t in TOOL_CLASSES[c]]
        if not hit:
            continue
        if first_verb == "read" and t in AMBIGUOUS_NOUNS and not any(c in ("destructive", "privileged") for c in hit):
            continue
        if first_verb is None:
            first_verb = hit[-1] if "read" in hit else hit[0]
        for c in hit:
            if c not in classes:
                classes.append(c)
    classes = [c for c in CLASS_ORDER if c in classes]
    for verb, objs, cls in TOOL_COMBOS:
        if verb in tokens and any(o in tokens for o in objs) and cls not in classes:
            classes.insert(0, cls)
    primary = None
    for cls in CLASS_ORDER:
        if cls in classes:
            primary = cls
            break
    return {"tokens": tokens, "classes": classes, "primary": primary or "unknown"}


# ---------------------------------------------------------------- policy schema
def policy_fields(policy: Optional[Dict[str, Any]]) -> List[str]:
    if not policy:
        return []
    out = []
    for f in policy.get("fields", []) or []:
        out.append(f)
    for f in policy.get("required_fields", []) or []:
        out.append(f)
    for f in (policy.get("feature_weights") or {}).keys():
        out.append(f)
    for r in policy.get("hard_rules", []) or []:
        if r.get("field"):
            out.append(r["field"])
    for f, aliases in (policy.get("field_aliases") or {}).items():
        out.append(f)
        out.extend(aliases or [])
    seen, uniq = set(), []
    for f in out:
        if f not in seen:
            seen.add(f)
            uniq.append(f)
    return uniq


def resolve_field(state: Dict[str, Any], field: str, policy: Optional[Dict[str, Any]]):
    if field in state:
        return True, state[field], field
    aliases = ((policy or {}).get("field_aliases") or {}).get(field) or []
    for a in aliases:
        if a in state:
            return True, state[a], a
    return False, None, None


# ---------------------------------------------------------------- hard rules
NUMERIC_OPS = (">", ">=", "<", "<=")


def _eq(a: Any, b: Any) -> bool:
    if is_number(a) and is_number(b):
        return a == b
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if isinstance(a, str) and isinstance(b, str):
        return a == b
    return False


def eval_rule(rule: Dict[str, Any], state: Dict[str, Any], policy: Optional[Dict[str, Any]]):
    present, val, used = resolve_field(state, rule.get("field", ""), policy)
    if not present:
        return None
    op = rule.get("op")
    target = rule.get("value")
    effect = str(rule.get("effect", "DENY")).upper()
    if effect not in SEVERITY:
        effect = "REVIEW"
    rid = rule.get("id") or ("rule_" + str(rule.get("field")))
    reason = rule.get("reason") or "{} {} {}".format(rule.get("field"), op, json.dumps(target, ensure_ascii=False))

    if op in NUMERIC_OPS:
        if not is_number(val) or not is_number(target):
            return {"effect": "REVIEW", "rule_id": "type_mismatch:" + rid,
                    "reason": "Field '{}' is not numeric; rule {} cannot be evaluated.".format(used, rid)}
        hit = ((op == ">" and val > target) or (op == ">=" and val >= target)
               or (op == "<" and val < target) or (op == "<=" and val <= target))
    elif op in ("==", "="):
        hit = _eq(val, target)
    elif op == "!=":
        hit = not _eq(val, target)
    elif op == "in":
        hit = isinstance(target, list) and any(_eq(val, t) for t in target)
    elif op == "not_in":
        hit = isinstance(target, list) and not any(_eq(val, t) for t in target)
    elif op == "has_token":
        toks = tokenize(val) if isinstance(val, str) else []
        want = [normalize_text(t) for t in (target if isinstance(target, list) else [target])]
        hit = any(t in toks for t in want)
    else:
        return {"effect": "REVIEW", "rule_id": "unknown_op:" + rid,
                "reason": "Unsupported operator '{}' in rule {}.".format(op, rid)}
    if hit:
        return {"effect": effect, "rule_id": rid, "reason": reason}
    return None


# ---------------------------------------------------------------- risk signals
def signal_contribution(key: str, v: Any, state: Dict[str, Any]) -> Optional[float]:
    toks = tokenize(key)
    if isinstance(v, bool):
        if _any_in(toks, SIG_HAZARD_BOOL):
            return 2.5 if v else -0.5
        if _any_in(toks, SIG_TRUST_BOOL):
            return -0.8 if v else 1.2
        return None
    if is_number(v):
        x = float(v)
        if _any_in(toks, SIG_RISK_SCORE) and _any_in(toks, ["score", "ratio", "index"]):
            return 2.4 if x >= 0.7 else (1.1 if x >= 0.4 else -0.6)
        if _any_in(toks, SIG_TRUST_SCORE):
            return -1.2 if x >= 0.7 else (1.8 if x < 0.4 else 0.2)
        if _any_in(toks, SIG_FAILURE):
            return (x / 5.0) * 1.5
        if _any_in(toks, SIG_RATE):
            return x / 50.0
        if _any_in(toks, SIG_AMOUNT):
            return min(3.0, math.log10(x / 1000.0) * 1.2) if x > 2000 else -0.3
        if _any_in(toks, SIG_TEMP):
            return ((x - 75.0) / 10.0) * 2.2 if x > 75 else (1.5 if x < 5 else -0.5)
        if _any_in(toks, SIG_LOAD):
            return ((x - 85.0) / 10.0) * 1.8 if x > 85 else -0.4
        if _any_in(toks, SIG_VIBRATION):
            return (x - 1.0) * 1.8 if x > 1.8 else -0.5
        if _any_in(toks, SIG_PROXIMITY):
            return 0.8 if x < 10 else -0.3
        return None
    if isinstance(v, str) and _any_in(toks, SIG_ROLE):
        vt = tokenize(v)
        for words, r in ROLE_RISK:
            if any(w in vt for w in words) or normalize_text(v) in words:
                return r
        return 0.0
    return None


def rule_owned_fields(policy: Optional[Dict[str, Any]]) -> set:
    owned = set()
    aliases = (policy or {}).get("field_aliases") or {}
    for r in (policy or {}).get("hard_rules", []) or []:
        f = r.get("field")
        if f:
            owned.add(f)
            owned.update(aliases.get(f) or [])
    return owned


def key_recognized(key: str, policy_field_set: set) -> bool:
    if key in policy_field_set:
        return True
    toks = tokenize(key)
    return len(toks) > 0 and all(t in KNOWN_VOCAB for t in toks)


# ---------------------------------------------------------------- main
def evaluate(state: Optional[Dict[str, Any]], policy: Optional[Dict[str, Any]] = None,
             strict: bool = False) -> Dict[str, Any]:
    state = dict(state or {})
    policy = policy or None
    strict = bool(strict or (policy and policy.get("unknown_fallback") == "abstain_review"))
    keys = sorted(k for k in state.keys() if k not in META_KEYS)
    pfields = set(policy_fields(policy))
    candidates: List[Dict[str, Any]] = []
    contributions: Dict[str, float] = {}
    recognized: List[str] = []
    unrecognized: List[str] = []

    if not keys:
        candidates.append({"effect": "REVIEW", "rule_id": "empty_state",
                           "reason": "No state fields were provided."})

    # 1. required fields
    missing = []
    for rf in (policy or {}).get("required_fields", []) or []:
        present, _, _ = resolve_field(state, rf, policy)
        if not present:
            missing.append(rf)
    if missing:
        candidates.append({"effect": "REVIEW", "rule_id": "missing_required",
                           "reason": "Required field(s) missing: " + ", ".join(missing)})

    # 2. tool classification
    tool_info = None
    tool_policy = dict(DEFAULT_TOOL_POLICY)
    tool_policy.update((policy or {}).get("tool_policy") or {})
    for tf in TOOL_FIELDS:
        if tf in state and isinstance(state[tf], str):
            info = classify_tool(state[tf])
            eff = tool_policy.get(info["primary"], "REVIEW")
            tool_info = {"field": tf, "value": state[tf], "tokens": info["tokens"],
                         "classes": info["classes"], "class": info["primary"], "effect": eff}
            candidates.append({"effect": eff, "rule_id": "tool_class:" + info["primary"],
                               "reason": "Tool '{}' classified as {}.".format(state[tf], info["primary"])})
            break

    # 3. explicit hard rules (all evaluated; most severe wins later)
    for rule in (policy or {}).get("hard_rules", []) or []:
        hit = eval_rule(rule, state, policy)
        if hit:
            candidates.append(hit)

    # 4. risk signals and schema recognition
    weights = (policy or {}).get("feature_weights") or {}
    owned = rule_owned_fields(policy)
    risk = 0.0
    has_signal = False
    for k in keys:
        v = state[k]
        rec = key_recognized(k, pfields)
        contrib = None
        if k in weights:
            w = weights[k] or {}
            if is_number(v):
                scale = w.get("scale", 1.0) or 1.0
                contrib = ((float(v) - w.get("threshold", 0.0)) / scale) * w.get("weight", 1.0)
            elif isinstance(v, bool):
                contrib = (1.0 if v else -1.0) * w.get("weight", 1.0)
        if contrib is None and rec and k not in TOOL_FIELDS and k not in owned:
            contrib = signal_contribution(k, v, state)
        if contrib is not None:
            has_signal = True
            risk += contrib
            contributions[k] = round4(contrib)
        else:
            contributions[k] = 0.0
        (recognized if rec else unrecognized).append(k)

    risk = round4(risk)
    ood = len(unrecognized) > 0
    if ood and strict:
        candidates.append({"effect": "REVIEW", "rule_id": "ood_unrecognized_fields",
                           "reason": "Unrecognized field(s): " + ", ".join(unrecognized)})

    if risk >= RISK_DENY_MIN:
        candidates.append({"effect": "DENY", "rule_id": "risk_high",
                           "reason": "Risk score {} >= {}.".format(risk, RISK_DENY_MIN)})
    elif risk > RISK_ALLOW_MAX:
        candidates.append({"effect": "REVIEW", "rule_id": "risk_mid",
                           "reason": "Risk score {} is between {} and {}.".format(risk, RISK_ALLOW_MAX, RISK_DENY_MIN)})
    elif has_signal or tool_info:
        candidates.append({"effect": "ALLOW", "rule_id": "risk_low",
                           "reason": "Risk score {} <= {}.".format(risk, RISK_ALLOW_MAX)})
    elif not candidates:
        candidates.append({"effect": "REVIEW", "rule_id": "no_signal",
                           "reason": "No recognized risk signal; nothing to decide on."})

    # 5. combine: most severe wins, first such candidate is the primary rule
    best = candidates[0]
    for c in candidates[1:]:
        if SEVERITY[c["effect"]] > SEVERITY[best["effect"]]:
            best = c
    verdict = best["effect"]
    rule_based = not best["rule_id"].startswith("risk_")
    if verdict == "REVIEW":
        confidence = 0.0
    elif rule_based:
        confidence = 1.0
    else:
        edge = (RISK_ALLOW_MAX - risk) if verdict == "ALLOW" else (risk - RISK_DENY_MIN)
        confidence = round4(min(1.0, 0.5 + edge / 2.0))
    if ood and not strict:
        confidence = min(confidence, 0.5)
    # noul = probability that the action may proceed, consistent with the verdict
    if verdict == "REVIEW":
        noul = 0.5
    elif rule_based:
        noul = 1.0 if verdict == "ALLOW" else 0.0
    else:
        noul = round4(1.0 / (1.0 + math.exp((risk - RISK_ALLOW_MAX) * 2.0)))

    return {
        "kernel_version": KERNEL_VERSION,
        "verdict": verdict,
        "label": LABELS[verdict],
        "rule_id": best["rule_id"],
        "reason": best["reason"],
        "confidence": confidence,
        "risk_score": risk,
        "noul": noul,
        "candidates": candidates,
        "tool": tool_info,
        "recognized_fields": recognized,
        "unrecognized_fields": unrecognized,
        "missing_required_fields": missing,
        "feature_contributions": contributions,
        "ood_detected": ood,
        "strict": strict,
        "policy_id": (policy or {}).get("gate_id") or (policy or {}).get("id") or "universal_default",
        "policy_version": (policy or {}).get("version") or KERNEL_VERSION,
    }


def question_polarity(text: Optional[str]) -> str:
    return "deny" if DENY_POLARITY.search(normalize_text(text or "")) else "allow"


def answer_question(result: Dict[str, Any], text: Optional[str]) -> Dict[str, Any]:
    pol = question_polarity(text)
    v = result["verdict"]
    if v == "REVIEW":
        decision = None
    elif pol == "deny":
        decision = v == "DENY"
    else:
        decision = v == "ALLOW"
    return {
        "type": "noul",
        "decision": decision,
        "boolean": decision,
        "verdict": v,
        "label": result["label"],
        "status": result["label"],
        "question_polarity": pol,
        "noul": result["noul"] if pol == "allow" else round4(1.0 - result["noul"]),
        "confidence": result["confidence"],
        "matched_rule": result["rule_id"],
        "reason": result["reason"],
    }
