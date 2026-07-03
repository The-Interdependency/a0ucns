# ratios: loc_comments=210:60 imports_exports=16:11 calls_definitions=68:16
# === MODULE_BUILD ===
# id: api_extensions_routes
#   module_name: extensions
#   module_kind: route
#   summary: post-auth API extensions — custom keys vault (user-defined GitHub/GCP/AWS-style keys), Emergent demo quota (per-user daily token budget), living spec endpoint (auto-parses MODULE_BUILD/BOUNDARIES/CAPABILITIES/CONTRACTS/RATIOS blocks from the repo and serves them as JSON), audit feed (hash-chained FIQ events for the Tool/CoT Tape)
#   owner: Erin Spencer
#   public_surface: router, record_demo_usage, check_demo_quota
#   internal_surface: _quota_key, _today_utc, _scan_repo_blocks
#   auth_boundary: bearer
#   storage_boundary: write
#   network_boundary: none
#   user_data_boundary: write
#   admin_only: false
#   tests: a0p_skills.contracts.api_extensions_living_spec_holds
#   rollout: default_enabled
#   rollback: revert; loses custom-keys vault, demo quota, and living spec
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: api_extensions_routes_boundaries
#   summary: REST endpoints for custom keys, demo quota, living spec
#   auth_boundary: bearer
#   storage_boundary: write
#   network_boundary: none
#   user_data_boundary: write
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: api_extensions_routes
#   summary: REST endpoints for custom keys, demo quota, living spec
#   exposes: router, record_demo_usage, check_demo_quota
#   boundaries: auth:bearer, storage:write, network:none, user_data:write
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: api_extensions_living_spec
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.api_extensions_living_spec_holds
# === END CONTRACTS ===
"""Custom keys vault + Emergent demo quota + living spec endpoint."""
from __future__ import annotations
import os
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from auth import get_current_user
from db import custom_keys_col, demo_quota_col


router = APIRouter(prefix="/api", tags=["extensions"])

# Reuse the BYOK Fernet secret to encrypt custom key values at rest.
_FERNET = Fernet(os.environ["A0P_KEY_VAULT_SECRET"].encode())


# ---- Custom Keys Vault ---------------------------------------------------
class CustomKeyBody(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name: str = Field(..., min_length=1, max_length=64)
    value: str = Field(..., min_length=1)
    label: Optional[str] = Field(None, max_length=120)
    kind: Optional[str] = Field(None, max_length=32)  # free-form: github, gcp, aws, ...


def _enc(v: str) -> str:
    return _FERNET.encrypt(v.encode("utf-8")).decode("utf-8")


def _dec(v: str) -> str:
    return _FERNET.decrypt(v.encode("utf-8")).decode("utf-8")


_NAME_RE = re.compile(r"^[a-zA-Z0-9_.:-]{1,64}$")


@router.get("/custom-keys")
async def list_custom_keys(user=Depends(get_current_user)):
    cursor = custom_keys_col.find({"user_id": user["id"]}).sort("name", 1)
    out = []
    async for d in cursor:
        out.append({
            "id": d["_id"],
            "name": d["name"],
            "label": d.get("label"),
            "kind": d.get("kind"),
            "preview": "•" * 8 + (d.get("preview_tail") or ""),
            "created_at_ms": d.get("created_at_ms"),
            "updated_at_ms": d.get("updated_at_ms"),
            "rotated_count": d.get("rotated_count", 0),
        })
    return {"keys": out}


@router.put("/custom-keys")
async def upsert_custom_key(body: CustomKeyBody, user=Depends(get_current_user)):
    if not _NAME_RE.match(body.name):
        raise HTTPException(400, "name must be [a-zA-Z0-9_.:-]{1,64}")
    now = int(time.time() * 1000)
    preview_tail = body.value[-4:] if len(body.value) >= 6 else ""
    existing = await custom_keys_col.find_one({"user_id": user["id"], "name": body.name})
    if existing:
        await custom_keys_col.update_one(
            {"_id": existing["_id"]},
            {"$set": {
                "value_enc": _enc(body.value),
                "label": body.label or existing.get("label"),
                "kind": body.kind or existing.get("kind"),
                "preview_tail": preview_tail,
                "updated_at_ms": now,
            }, "$inc": {"rotated_count": 1}},
        )
        return {"ok": True, "id": existing["_id"], "rotated": True}
    rec = {
        "_id": str(uuid.uuid4()),
        "user_id": user["id"],
        "name": body.name,
        "value_enc": _enc(body.value),
        "label": body.label,
        "kind": body.kind,
        "preview_tail": preview_tail,
        "created_at_ms": now,
        "updated_at_ms": now,
        "rotated_count": 0,
    }
    await custom_keys_col.insert_one(rec)
    return {"ok": True, "id": rec["_id"], "rotated": False}


@router.post("/custom-keys/{key_id}/reveal")
async def reveal_custom_key(key_id: str, user=Depends(get_current_user)):
    rec = await custom_keys_col.find_one({"_id": key_id, "user_id": user["id"]})
    if not rec:
        raise HTTPException(404, "key not found")
    return {"name": rec["name"], "value": _dec(rec["value_enc"])}


@router.delete("/custom-keys/{key_id}")
async def delete_custom_key(key_id: str, user=Depends(get_current_user)):
    r = await custom_keys_col.delete_one({"_id": key_id, "user_id": user["id"]})
    if r.deleted_count == 0:
        raise HTTPException(404, "key not found")
    return {"ok": True}


# ---- Emergent demo quota -------------------------------------------------
def _today_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _budget() -> int:
    try:
        return int(os.environ.get("EMERGENT_DEMO_DAILY_TOKEN_BUDGET", "25000"))
    except ValueError:
        return 25000


async def check_demo_quota(user_id: str, projected_tokens: int = 1) -> dict:
    """Return remaining quota + whether the request fits. Does not consume."""
    day = _today_utc()
    rec = await demo_quota_col.find_one({"user_id": user_id, "day": day})
    used = int(rec.get("tokens_used", 0)) if rec else 0
    budget = _budget()
    remaining = max(0, budget - used)
    return {
        "day": day,
        "budget": budget,
        "used": used,
        "remaining": remaining,
        "fits": projected_tokens <= remaining,
    }


async def record_demo_usage(user_id: str, tokens: int) -> dict:
    """Atomically add `tokens` to today's bucket. Returns the new state."""
    day = _today_utc()
    await demo_quota_col.update_one(
        {"user_id": user_id, "day": day},
        {"$inc": {"tokens_used": int(tokens)},
         "$setOnInsert": {"user_id": user_id, "day": day, "first_at_ms": int(time.time() * 1000)},
         "$set": {"last_at_ms": int(time.time() * 1000)}},
        upsert=True,
    )
    return await check_demo_quota(user_id)


@router.get("/demo-quota")
async def get_demo_quota(user=Depends(get_current_user)):
    return await check_demo_quota(user["id"])


# ---- Living spec (auto-parses doc-as-code blocks) ------------------------
_REPO_ROOTS = [
    Path("/app/backend/interdependent_lib"),
    Path("/app/backend/agents"),
    Path("/app/backend/providers"),
    Path("/app/backend/auth"),
    Path("/app/backend/a0p_skills"),
    Path("/app/backend/tests"),
    Path("/app/backend"),
    Path("/app/frontend/src"),
]
_SKIP_DIRS = {"__pycache__", "node_modules", "build", "dist", ".next", ".git"}
_EXTS = {".py", ".js", ".jsx", ".ts", ".tsx"}


def _iter_repo_files():
    seen = set()
    for root in _REPO_ROOTS:
        if not root.is_dir():
            continue
        for p in sorted(root.rglob("*")):
            if not p.is_file() or p.suffix.lower() not in _EXTS:
                continue
            if any(part in _SKIP_DIRS for part in p.parts):
                continue
            if p in seen:
                continue
            # Don't yield the same file under two roots (backend tree overlaps).
            seen.add(p)
            yield p


def _scan_repo_blocks() -> list[dict]:
    from interdependent_lib._msdmd.parser import parse_file, parse_ratios_file
    BLOCKS = ("MODULE_BUILD", "BOUNDARIES", "CAPABILITIES", "CONTRACTS", "RATIOS")
    modules: list[dict] = []
    for p in _iter_repo_files():
        try:
            entries_by_kind = {k: (parse_file(p, k) or []) for k in BLOCKS if k != "RATIOS"}
            entries_by_kind["RATIOS"] = parse_ratios_file(p) or []
        except Exception:
            entries_by_kind = {k: [] for k in BLOCKS}
        mb = entries_by_kind["MODULE_BUILD"]
        if not mb:
            continue
        head = mb[0]
        modules.append({
            "path": str(p.relative_to(Path("/app"))),
            "id": head.get("id"),
            "module_name": head.get("module_name"),
            "module_kind": head.get("module_kind"),
            "summary": head.get("summary"),
            "owner": head.get("owner"),
            "public_surface": head.get("public_surface"),
            "tests": head.get("tests"),
            "blocks": {k: entries_by_kind[k] for k in BLOCKS},
        })
    return modules


@router.get("/spec/living")
async def living_spec():
    """Return every msdmd block in the repo as structured JSON.

    No auth: the spec is public canon. (Endpoint is mounted under /api so it's
    reachable from the frontend through the ingress.)
    """
    from living_spec import scan_repo_blocks
    modules = scan_repo_blocks()
    by_kind: dict[str, int] = {}
    for m in modules:
        kind = m.get("module_kind") or "unknown"
        by_kind[kind] = by_kind.get(kind, 0) + 1
    return {
        "generated_at_ms": int(time.time() * 1000),
        "count": len(modules),
        "by_kind": by_kind,
        "modules": modules,
    }


@router.get("/audit/feed")
async def audit_feed(agent_id: str = "", limit: int = 50, kind: str = ""):
    """Return the most recent hash-chained FIQ events.

    Filters: ``agent_id`` (exact match), ``kind`` (event_type prefix). Public
    inside the app — surfaces the same canonical chain that the Workspace
    Tool/CoT Tape polls every few seconds. Each row carries prev_hash + this_hash
    so any client can verify chain integrity locally.
    """
    from db import fiq_audit_col
    q: dict = {}
    if agent_id:
        q["agent_id"] = agent_id
    if kind:
        q["event_type"] = {"$regex": f"^{kind}"}
    limit = max(1, min(int(limit), 200))
    cursor = fiq_audit_col.find(q).sort("timestamp_ms", -1).limit(limit)
    out = []
    async for d in cursor:
        out.append({
            "id": str(d.get("_id")),
            "event_type": d.get("event_type"),
            "agent_id": d.get("agent_id"),
            "user_id": d.get("user_id"),
            "payload": d.get("payload"),
            "timestamp_ms": d.get("timestamp_ms"),
            "prev_hash": d.get("prev_hash"),
            "this_hash": d.get("this_hash"),
        })
    # Reverse to chronological so the UI appends downward.
    return {"count": len(out), "events": list(reversed(out))}


__all__ = ["router", "record_demo_usage", "check_demo_quota"]
# ratios: loc_comments=210:60 imports_exports=16:11 calls_definitions=68:16
