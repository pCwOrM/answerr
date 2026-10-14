"""Plan catalog: commerce/plans.json is the single source of truth for quotas, prices and features.
The pricing page is checked against it in tests/test_commerce.py."""
import json
import os
from typing import Any, Dict, Optional

_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plans.json")
with open(_PATH, encoding="utf-8") as _f:
    CATALOG: Dict[str, Any] = json.load(_f)

PLANS: Dict[str, Dict[str, Any]] = CATALOG["plans"]
DEFAULT_PLAN = "kesif"
PAID_PLANS = ("gelistirici", "pro")


def get(plan_id: Optional[str]) -> Dict[str, Any]:
    return PLANS.get(plan_id or DEFAULT_PLAN) or PLANS[DEFAULT_PLAN]


def has(plan_id: Optional[str], feature: str) -> bool:
    return bool(get(plan_id).get("features", {}).get(feature))


def public_catalog() -> Dict[str, Any]:
    out = {k: v for k, v in CATALOG.items() if k != "plans"}
    out["plans"] = {k: v for k, v in sorted(PLANS.items(), key=lambda kv: kv[1].get("order", 99)) if v.get("public")}
    return out


def monthly_base_cents(plan_id: str, cycle: str) -> int:
    p = get(plan_id)
    if cycle == "yearly":
        v = p.get("price_yearly_per_month")
    else:
        v = p.get("price_monthly")
    return int(round((v or 0) * 100))


def overage_cents(plan_id: str, units: int) -> int:
    """Overage is billed per started block of 1,000 decisions."""
    per = get(plan_id).get("overage_per_1000")
    if not per or units <= 0:
        return 0
    blocks = (units + 999) // 1000
    return int(round(blocks * per * 100))
