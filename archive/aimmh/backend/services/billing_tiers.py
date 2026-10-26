# ratios: loc_comments=56:0 imports_exports=4:7 calls_definitions=9:7
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from db import db

TIER_ORDER = {"free": 0, "supporter": 1, "pro": 2, "team": 3}
TIER_LIMITS: Dict[str, Dict[str, Any]] = {
    "free": {
        "max_instances": 5,
        "max_runs_per_month": 10,
        "hide_emergent_badge": False,
    },
    "supporter": {
        "max_instances": 15,
        "max_runs_per_month": 30,
        "hide_emergent_badge": True,
    },
    "pro": {
        "max_instances": None,
        "max_runs_per_month": None,
        "hide_emergent_badge": True,
    },
    "team": {
        "max_instances": None,
        "max_runs_per_month": None,
        "hide_emergent_badge": True,
    },
}


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def current_month_start_iso() -> str:
    now = datetime.now(timezone.utc)
    return datetime(now.year, now.month, 1, tzinfo=timezone.utc).isoformat()


def normalize_tier(value: Optional[str]) -> str:
    if value in TIER_ORDER:
        return value
    return "free"


async def get_user_doc(user_id: str) -> Optional[dict]:
    return await db.users.find_one({"$or": [{"id": user_id}, {"user_id": user_id}]}, {"_id": 0})


def derive_billing_profile(user_doc: Optional[dict]) -> dict:
    billing = (user_doc or {}).get("billing", {}) or {}
    tier = normalize_tier(billing.get("subscription_tier"))
    limits = TIER_LIMITS[tier]
    return {
        "subscription_tier": tier,
        "max_instances": limits["max_instances"],
        "max_runs_per_month": limits["max_runs_per_month"],
        "hide_emergent_badge": limits["hide_emergent_badge"],
        "supporter_eligible": tier in {"supporter", "pro", "team"},
        "team_seats": int(billing.get("team_seats") or (3 if tier == "team" else 1)),
    }


async def get_user_billing_profile(user_id: str) -> dict:
    return derive_billing_profile(await get_user_doc(user_id))


def merge_tier(current_tier: str, requested_tier: str) -> str:
    current = normalize_tier(current_tier)
    requested = normalize_tier(requested_tier)
    return requested if TIER_ORDER[requested] >= TIER_ORDER[current] else current
# ratios: loc_comments=56:0 imports_exports=4:7 calls_definitions=9:7
