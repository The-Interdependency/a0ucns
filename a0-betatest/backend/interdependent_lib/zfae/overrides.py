# ratios: loc_comments=115:48 imports_exports=5:8 calls_definitions=23:9
# === MODULE_BUILD ===
# id: zfae_overrides
#   module_name: overrides
#   module_kind: service
#   summary: PendingOverride dataclass + lifecycle helpers for sentinel halt-and-override; backed by MongoDB pending_overrides_col
#   owner: Erin Spencer
#   public_surface: PendingOverride, create_override, approve, reject, expire, get, list_pending, OVERRIDE_DEFAULT_TIMEOUT_MS
#   internal_surface: _utc_now_ms
#   auth_boundary: none
#   storage_boundary: write
#   network_boundary: internal
#   user_data_boundary: write
#   admin_only: false
#   tests: a0p_skills.contracts.zfae_overrides_lifecycle_holds
#   rollout: default_enabled
#   rollback: drop pending_overrides_col; halts become hard FIQ_BLOCKED with no resume
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: zfae_overrides_boundaries
#   summary: per-user override records with timeout; mongo-persistent
#   auth_boundary: none
#   storage_boundary: write
#   network_boundary: internal
#   user_data_boundary: write
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: zfae_overrides
#   summary: sentinel halt-and-override pending records with approve/reject/expire lifecycle
#   exposes: PendingOverride, create_override, approve, reject, expire, get, list_pending
#   boundaries: auth:none, storage:write, network:internal, user_data:write
#   owner: Erin Spencer
# === END CAPABILITIES ===
"""Sentinel halt-and-override lifecycle.

Every flagged sentinel verdict creates one PendingOverride. User explicitly
approves or rejects; rejected becomes FIQ_BLOCKED. Expired becomes
FIQ_BLOCKED with reason 'user_override_timeout'.
"""
from __future__ import annotations
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Optional

OVERRIDE_DEFAULT_TIMEOUT_MS: int = 24 * 60 * 60 * 1000   # 24 hours


def _utc_now_ms() -> int:
    return int(time.time() * 1000)


@dataclass
class PendingOverride:
    """A held action awaiting user explicit approval or rejection."""
    id: str
    agent_id: str
    user_id: str
    event_kind: str                          # chat_reply | training_step | instance_create | …
    raw_request: dict                        # the original request payload
    flagged_sentinels: list[str]             # e.g. ["S4", "S12"]
    reasons: dict[str, str]                  # per-sentinel flag reason
    verdict_vector: list[Optional[float]]    # 13-dim, with null for off-mode
    disabled_sentinels: list[str]            # mode == off for this turn
    blocking_cliff: bool                     # True iff any cliff sentinel flagged
    status: str                              # pending | approved | rejected | expired
    created_ms: int
    expires_ms: int
    resolved_ms: Optional[int] = None
    resolved_by_user_id: Optional[str] = None
    justification: Optional[str] = None
    rejection_reason: Optional[str] = None


async def create_override(
    col,
    *,
    agent_id: str,
    user_id: str,
    event_kind: str,
    raw_request: dict,
    flagged_sentinels: list[str],
    reasons: dict[str, str],
    verdict_vector: list[Optional[float]],
    disabled_sentinels: list[str],
    blocking_cliff: bool,
    timeout_ms: int = OVERRIDE_DEFAULT_TIMEOUT_MS,
) -> PendingOverride:
    now = _utc_now_ms()
    rec = PendingOverride(
        id=str(uuid.uuid4()),
        agent_id=agent_id,
        user_id=user_id,
        event_kind=event_kind,
        raw_request=raw_request,
        flagged_sentinels=flagged_sentinels,
        reasons=reasons,
        verdict_vector=verdict_vector,
        disabled_sentinels=disabled_sentinels,
        blocking_cliff=blocking_cliff,
        status="pending",
        created_ms=now,
        expires_ms=now + timeout_ms,
    )
    doc = asdict(rec)
    doc["_id"] = doc.pop("id")
    await col.insert_one(doc)
    return rec


async def approve(col, override_id: str, user_id: str, justification: str = "") -> Optional[PendingOverride]:
    now = _utc_now_ms()
    r = await col.find_one_and_update(
        {"_id": override_id, "status": "pending"},
        {"$set": {
            "status": "approved",
            "resolved_ms": now,
            "resolved_by_user_id": user_id,
            "justification": justification,
        }},
        return_document=True,
    )
    return _from_doc(r)


async def reject(col, override_id: str, user_id: str, reason: str = "") -> Optional[PendingOverride]:
    now = _utc_now_ms()
    r = await col.find_one_and_update(
        {"_id": override_id, "status": "pending"},
        {"$set": {
            "status": "rejected",
            "resolved_ms": now,
            "resolved_by_user_id": user_id,
            "rejection_reason": reason,
        }},
        return_document=True,
    )
    return _from_doc(r)


async def expire(col) -> int:
    """Mark all pending overrides past their expiry as expired. Returns count."""
    now = _utc_now_ms()
    r = await col.update_many(
        {"status": "pending", "expires_ms": {"$lt": now}},
        {"$set": {"status": "expired", "resolved_ms": now}},
    )
    return r.modified_count


async def get(col, override_id: str) -> Optional[PendingOverride]:
    doc = await col.find_one({"_id": override_id})
    return _from_doc(doc)


async def list_pending(col, user_id: str = "local", limit: int = 100) -> list[PendingOverride]:
    out: list[PendingOverride] = []
    async for doc in col.find({"user_id": user_id, "status": "pending"}).sort("created_ms", -1).limit(limit):
        rec = _from_doc(doc)
        if rec:
            out.append(rec)
    return out


def _from_doc(doc: Optional[dict]) -> Optional[PendingOverride]:
    if doc is None:
        return None
    doc = dict(doc)
    if "_id" in doc:
        doc["id"] = doc.pop("_id")
    return PendingOverride(**{k: v for k, v in doc.items() if k in PendingOverride.__annotations__})


__all__ = [
    "PendingOverride", "OVERRIDE_DEFAULT_TIMEOUT_MS",
    "create_override", "approve", "reject", "expire", "get", "list_pending",
]

# === CONTRACTS ===
# id: zfae_overrides_loads
#   given: module declares its msdmd canon
#   then: the module imports cleanly under the current interpreter
#   class: integration
#   call: a0p_skills.contracts.module_imports_cleanly_holds
# === END CONTRACTS ===

# ratios: loc_comments=115:48 imports_exports=5:8 calls_definitions=23:9
