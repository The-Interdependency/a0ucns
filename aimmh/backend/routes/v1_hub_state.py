# ratios: loc_comments=45:0 imports_exports=6:4 calls_definitions=15:4
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from db import db
from models.hub_state import HubStateOut, HubStateUpsertRequest
from services.auth import get_current_user, get_user_id


router = APIRouter(prefix="/api/v1/hub/state", tags=["hub-state"])
HUB_STATE_COLLECTION = "hub_workspace_state"


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.get("/{state_key}", response_model=HubStateOut)
async def get_hub_state(state_key: str, current_user: dict = Depends(get_current_user)):
    user_id = get_user_id(current_user)
    doc = await db[HUB_STATE_COLLECTION].find_one(
        {"user_id": user_id, "state_key": state_key},
        {"_id": 0},
    )
    if not doc:
        raise HTTPException(status_code=404, detail="State not found")
    return HubStateOut(**doc)


@router.put("/{state_key}", response_model=HubStateOut)
async def upsert_hub_state(state_key: str, request: HubStateUpsertRequest, current_user: dict = Depends(get_current_user)):
    user_id = get_user_id(current_user)
    payload = request.payload or {}
    updated_at = iso_now()
    await db[HUB_STATE_COLLECTION].update_one(
        {"user_id": user_id, "state_key": state_key},
        {
            "$set": {
                "user_id": user_id,
                "state_key": state_key,
                "payload": payload,
                "updated_at": updated_at,
            }
        },
        upsert=True,
    )
    return HubStateOut(state_key=state_key, payload=payload, updated_at=updated_at)


@router.delete("/{state_key}")
async def delete_hub_state(state_key: str, current_user: dict = Depends(get_current_user)):
    user_id = get_user_id(current_user)
    result = await db[HUB_STATE_COLLECTION].delete_one({"user_id": user_id, "state_key": state_key})
    if result.deleted_count == 0:
        return {"message": "State already absent"}
    return {"message": f"Deleted state {state_key}"}
# ratios: loc_comments=45:0 imports_exports=6:4 calls_definitions=15:4
