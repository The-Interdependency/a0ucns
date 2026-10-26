# ratios: loc_comments=45:44 imports_exports=8:5 calls_definitions=17:5
# === MODULE_BUILD ===
# id: app_settings
#   module_name: app_settings
#   module_kind: route
#   summary: admin-editable runtime settings — single Mongo doc with key/value overrides for non-secret URLs (Emergent Google OAuth widget URL, etc.); /api/settings GET for everyone, PATCH for admin only; values shadow env vars at runtime
#   owner: Erin Spencer
#   public_surface: router, get_setting
#   internal_surface: _DEFAULTS, _admin_only
#   auth_boundary: bearer
#   storage_boundary: write
#   network_boundary: none
#   user_data_boundary: write
#   admin_only: true
#   tests: a0p_skills.contracts.module_imports_cleanly_holds
#   rollout: default_enabled
#   rollback: revert; settings revert to env-defaults
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: app_settings_boundaries
#   summary: admin-editable URL settings
#   auth_boundary: bearer
#   storage_boundary: write
#   network_boundary: none
#   user_data_boundary: write
#   admin_only: true
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: app_settings
#   summary: editable runtime settings
#   exposes: router, get_setting
#   boundaries: auth:bearer, storage:write, network:none, user_data:write, admin:true
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: app_settings_loads
#   given: module declares its msdmd canon
#   then: the module imports cleanly under the current interpreter
#   class: integration
#   call: a0p_skills.contracts.module_imports_cleanly_holds
# === END CONTRACTS ===
"""Admin-editable, non-secret runtime settings (e.g. OAuth widget URLs)."""
from __future__ import annotations
import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from typing import Optional

from auth import get_current_user

router = APIRouter(prefix="/api/settings", tags=["settings"])

_DEFAULTS: dict[str, str] = {
    "emergent_google_oauth_url": "https://auth.emergentagent.com/",
    "skill_lib_index_url": "https://raw.githubusercontent.com/The-Interdependency/skill-lib/main/index.json",
    "skill_lib_repo": "The-Interdependency/skill-lib",
}


async def get_setting(name: str) -> str:
    """Resolve a setting: Mongo override > env var > _DEFAULTS."""
    from db import db as _db
    doc = await _db["app_settings"].find_one({"_id": "global"}) or {}
    if name in doc:
        return str(doc[name])
    env_key = name.upper()
    if env_key in os.environ:
        return os.environ[env_key]
    return _DEFAULTS.get(name, "")


def _admin_only(user: dict) -> None:
    if user.get("role") != "admin":
        raise HTTPException(403, "admin only")


@router.get("")
async def list_settings():
    """Public: returns current effective values for whitelisted keys."""
    out = {}
    for k in _DEFAULTS:
        out[k] = await get_setting(k)
    return {"settings": out, "editable_by_admin": list(_DEFAULTS.keys())}


class PatchBody(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    settings: dict[str, str]


@router.patch("")
async def patch_settings(body: PatchBody, user=Depends(get_current_user)):
    _admin_only(user)
    bad = [k for k in body.settings if k not in _DEFAULTS]
    if bad:
        raise HTTPException(400, f"unknown setting keys: {bad}")
    from db import db as _db
    await _db["app_settings"].update_one(
        {"_id": "global"}, {"$set": {k: v for k, v in body.settings.items()}}, upsert=True,
    )
    return await list_settings()


__all__ = ["router", "get_setting"]
# ratios: loc_comments=45:44 imports_exports=8:5 calls_definitions=17:5
