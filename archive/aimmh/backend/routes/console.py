# ratios: loc_comments=77:0 imports_exports=6:4 calls_definitions=24:5
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timezone
from typing import Dict, Any

from db import db
from models.context import CostLimitPreferencesRequest, ContextLogUpdateRequest
from services.auth import get_current_user, get_user_id

router = APIRouter(prefix="/api/console", tags=["console"])


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.get("/preferences")
async def get_console_preferences(current_user: dict = Depends(get_current_user)):
    user_id = get_user_id(current_user)
    doc = await db.console_preferences.find_one({"user_id": user_id}, {"_id": 0})
    if doc:
        return doc

    return {
        "user_id": user_id,
        "enforce_token_limit": False,
        "enforce_cost_limit": False,
        "token_limit": 25000,
        "cost_limit_usd": 25.0,
        "updated_at": _now_iso(),
    }


@router.put("/preferences")
async def update_console_preferences(
    payload: CostLimitPreferencesRequest,
    current_user: dict = Depends(get_current_user),
):
    user_id = get_user_id(current_user)
    doc = {
        "user_id": user_id,
        "enforce_token_limit": payload.enforce_token_limit,
        "enforce_cost_limit": payload.enforce_cost_limit,
        "token_limit": payload.token_limit,
        "cost_limit_usd": payload.cost_limit_usd,
        "updated_at": _now_iso(),
    }
    await db.console_preferences.update_one(
        {"user_id": user_id},
        {"$set": doc},
        upsert=True,
    )
    return doc


@router.get("/context-logs")
async def get_context_logs(
    limit: int = Query(default=30, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
):
    user_id = get_user_id(current_user)
    logs = await db.context_logs.find(
        {"user_id": user_id},
        {"_id": 0},
    ).sort("created_at", -1).limit(limit).to_list(limit)
    return {"logs": logs}


@router.put("/context-logs/{entry_id}")
async def update_context_log(
    entry_id: str,
    payload: ContextLogUpdateRequest,
    current_user: dict = Depends(get_current_user),
):
    user_id = get_user_id(current_user)
    updates: Dict[str, Any] = {
        key: value
        for key, value in payload.model_dump().items()
        if value is not None
    }

    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")

    updates["updated_at"] = _now_iso()

    result = await db.context_logs.update_one(
        {"id": entry_id, "user_id": user_id},
        {"$set": updates},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Context log not found")

    updated = await db.context_logs.find_one({"id": entry_id, "user_id": user_id}, {"_id": 0})
    return updated
# ratios: loc_comments=77:0 imports_exports=6:4 calls_definitions=24:5
