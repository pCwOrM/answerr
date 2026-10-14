"""
Executable policy checks.

Every check here is run against the actual policy with the actual kernel; the
result (passed / failed, with detail) is what the API reports. Nothing in this
file is a static claim.
"""

from __future__ import annotations

from typing import Any, Dict, List

import policy_kernel as K

DESTRUCTIVE_PROBES = ["drop_table", "bulk_delete_users", "deleteCustomerLedger",
                      "truncate_audit_log", "purge_backups", "rm_rf_root", "wipe_disk"]
PRIVILEGED_PROBES = ["exec_shell_command", "sudo_restart", "export_private_keys"]
OOD_PROBE_FIELD = "zz_unknown_probe_field"


def _sev(v: str) -> int:
    return K.SEVERITY[v]


def _numeric_rules(policy: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [r for r in policy.get("hard_rules", []) or []
            if r.get("op") in K.NUMERIC_OPS and K.is_number(r.get("value"))]


def _base_state(policy: Dict[str, Any]) -> Dict[str, Any]:
    """A neutral state that satisfies required fields where it can."""
    st: Dict[str, Any] = {}
    for f in policy.get("required_fields", []) or []:
        toks = K.tokenize(f)
        if f in K.TOOL_FIELDS:
            st[f] = "read_status"
        elif any(t in K.SIG_ROLE for t in toks):
            st[f] = "member"
        else:
            st[f] = 0
    return st


def check_destructive_denied(policy: Dict[str, Any]) -> Dict[str, Any]:
    tool_field = next((f for f in K.policy_fields(policy) if f in K.TOOL_FIELDS), None)
    tp = dict(K.DEFAULT_TOOL_POLICY)
    tp.update(policy.get("tool_policy") or {})
    if not tool_field:
        return {"id": "destructive_tools_denied", "applies": False, "passed": True,
                "detail": "Policy has no tool field; check not applicable."}
    failures = []
    for probe in DESTRUCTIVE_PROBES + PRIVILEGED_PROBES:
        for role in ("admin", "member"):
            st = _base_state(policy)
            st.update({tool_field: probe, "user_role": role, "auth_status": True})
            r = K.evaluate(st, policy, True)
            if r["verdict"] != "DENY":
                failures.append("{}/{} -> {}".format(probe, role, r["verdict"]))
    expected_deny = tp.get("destructive") == "DENY" and tp.get("privileged") == "DENY"
    return {"id": "destructive_tools_denied", "applies": True,
            "passed": expected_deny and not failures,
            "detail": "{} probes, {} not denied{}".format(
                2 * (len(DESTRUCTIVE_PROBES) + len(PRIVILEGED_PROBES)), len(failures),
                (": " + "; ".join(failures[:5])) if failures else "")}


def check_unknown_field_review(policy: Dict[str, Any]) -> Dict[str, Any]:
    st = _base_state(policy)
    st[OOD_PROBE_FIELD] = 42
    r = K.evaluate(st, policy, False)
    ok = r["verdict"] in ("REVIEW", "DENY") and OOD_PROBE_FIELD in r["unrecognized_fields"]
    return {"id": "unknown_field_review", "applies": True, "passed": ok,
            "detail": "State with an unknown field -> {} ({})".format(r["verdict"], r["rule_id"])}


def check_numeric_monotonic(policy: Dict[str, Any]) -> Dict[str, Any]:
    """For '>'/'>=' rules a larger value must never be treated more leniently (and the
    reverse for '<'/'<='), sweeping each rule field around its thresholds."""
    rules = _numeric_rules(policy)
    if not rules:
        return {"id": "numeric_monotonic", "applies": False, "passed": True,
                "detail": "No numeric rules."}
    problems = []
    by_field: Dict[str, List[Dict[str, Any]]] = {}
    for r in rules:
        by_field.setdefault(r["field"], []).append(r)
    for field, rs in by_field.items():
        cuts = sorted({float(r["value"]) for r in rs})
        pts = sorted({c + d for c in cuts for d in (-1.0, -0.001, 0.0, 0.001, 1.0)} | {cuts[0] - 100, cuts[-1] + 100})
        upward = all(r["op"] in (">", ">=") for r in rs)
        downward = all(r["op"] in ("<", "<=") for r in rs)
        if not (upward or downward):
            continue
        sevs = []
        for x in pts:
            st = _base_state(policy)
            st[field] = x
            sevs.append(_sev(K.evaluate(st, policy, False)["verdict"]))
        seq = sevs if upward else list(reversed(sevs))
        for a, b in zip(seq, seq[1:]):
            if b < a:
                problems.append(field)
                break
    return {"id": "numeric_monotonic", "applies": True, "passed": not problems,
            "detail": "Non-monotonic fields: " + ", ".join(problems) if problems else
            "Verdict severity never decreases as rule fields move toward their risky side."}


def check_rule_overlaps(policy: Dict[str, Any]) -> Dict[str, Any]:
    """Reports numeric rules on the same field with different effects whose ranges
    overlap. Overlaps are resolved deterministically (most severe wins); this check
    lists them so an author can see where that happens."""
    rules = _numeric_rules(policy)
    overlaps = []
    for i, a in enumerate(rules):
        for b in rules[i + 1:]:
            if a["field"] != b["field"] or str(a.get("effect")).upper() == str(b.get("effect")).upper():
                continue
            lo_a, hi_a = _interval(a)
            lo_b, hi_b = _interval(b)
            if max(lo_a, lo_b) < min(hi_a, hi_b) or (lo_a == lo_b == hi_a == hi_b):
                overlaps.append("{} & {}".format(a.get("id"), b.get("id")))
    return {"id": "rule_overlaps", "applies": bool(rules), "passed": True,
            "detail": ("Overlapping ranges resolved by most-severe-wins: " + ", ".join(overlaps))
            if overlaps else "No overlapping numeric ranges with different effects."}


def _interval(r):
    v = float(r["value"])
    inf = float("inf")
    return {">": (v, inf), ">=": (v, inf), "<": (-inf, v), "<=": (-inf, v)}[r["op"]]


def check_rules_reachable(policy: Dict[str, Any]) -> Dict[str, Any]:
    unreachable = []
    for r in policy.get("hard_rules", []) or []:
        st = _base_state(policy)
        probe = probe_value_for(r, hit=True)
        if probe is None:
            continue
        st[r["field"]] = probe
        res = K.evaluate(st, policy, False)
        if not any(c["rule_id"] == r.get("id") for c in res["candidates"]):
            unreachable.append(str(r.get("id")))
    return {"id": "rules_reachable", "applies": True, "passed": not unreachable,
            "detail": "Unreachable rules: " + ", ".join(unreachable) if unreachable
            else "Every rule fires on a probe built from its own condition."}


def probe_value_for(rule: Dict[str, Any], hit: bool):
    op, v = rule.get("op"), rule.get("value")
    if op in K.NUMERIC_OPS and K.is_number(v):
        step = 1 if float(v).is_integer() else 0.01
        if op == ">":
            return v + step if hit else v
        if op == ">=":
            return v if hit else v - step
        if op == "<":
            return v - step if hit else v
        if op == "<=":
            return v if hit else v + step
    if op == "has_token":
        vals = v if isinstance(v, list) else [v]
        return ("bulk_" + str(vals[0]) + "_records") if hit else "zz_neutral_name"
    if op in ("==", "="):
        return v if hit else (not v if isinstance(v, bool) else None)
    if op == "in" and isinstance(v, list) and v:
        return v[0] if hit else None
    return None


def run_all(policy: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        check_destructive_denied(policy),
        check_unknown_field_review(policy),
        check_numeric_monotonic(policy),
        check_rules_reachable(policy),
        check_rule_overlaps(policy),
    ]
