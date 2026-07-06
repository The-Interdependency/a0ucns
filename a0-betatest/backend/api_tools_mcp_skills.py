# ratios: loc_comments=235:62 imports_exports=14:20 calls_definitions=95:21
# === MODULE_BUILD ===
# id: api_tools_mcp_skills_routes
#   module_name: api_tools_mcp_skills
#   module_kind: route
#   summary: REST surface for the tools / MCP-client / skills layer — /api/tools (list, register user-webhook tool, invoke), /api/mcp/servers (CRUD external MCP servers, refresh their tools), /api/skills (list, register w/ overlap warning, delete, sync from skill-lib)
#   owner: Erin Spencer
#   public_surface: router
#   internal_surface: _refresh_mcp_tools, _user_id
#   auth_boundary: bearer
#   storage_boundary: write
#   network_boundary: external
#   user_data_boundary: write
#   admin_only: false
#   tests: a0p_skills.contracts.api_tools_mcp_skills_router_holds
#   rollout: default_enabled
#   rollback: revert; user cannot manage tools/mcp/skills from the UI
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: api_tools_mcp_skills_routes_boundaries
#   summary: REST endpoints for tools, mcp client, and skills
#   auth_boundary: bearer
#   storage_boundary: write
#   network_boundary: external
#   user_data_boundary: write
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: api_tools_mcp_skills_routes
#   summary: tools/mcp/skills REST surface
#   exposes: router
#   boundaries: auth:bearer, storage:write, network:external, user_data:write
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: api_tools_mcp_skills_router_loads
#   given: module declares its msdmd canon
#   then: the module imports cleanly under the current interpreter
#   class: integration
#   call: a0p_skills.contracts.module_imports_cleanly_holds
# === END CONTRACTS ===
"""REST surface for tools, MCP client (external server registry), and skills."""
from __future__ import annotations
import time
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from auth import get_current_user
from db import (
    user_tools_col, mcp_servers_col, skills_col,
    pending_overrides_col, fiq_audit_col,
)

import tools as tools_pkg
from tools.registry import Tool, ToolError, TOOL_KIND_NATIVE, TOOL_KIND_WEBHOOK, TOOL_KIND_MCP, list_tools as _list_tools
from tools import mcp_relay
import skills as skills_pkg


router = APIRouter(prefix="/api", tags=["tools+mcp+skills"])


# ---- Tools ---------------------------------------------------------------
class WebhookToolBody(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name: str = Field(..., min_length=2, max_length=64)
    description: str = ""
    webhook_url: str
    webhook_secret: Optional[str] = None
    input_schema: dict = {}
    tags: list[str] = []


class InvokeToolBody(BaseModel):
    params: dict = {}
    override_id: Optional[str] = None


async def _hydrate_user_tools(user_id: str) -> None:
    """Sync this user's Mongo tool records into the in-process registry.

    Reconciles both ways: registry entries owned by the user that no longer
    exist in Mongo are evicted (so a deleted tool stops being invokable/listable
    without a restart), and a user tool never overwrites a global built-in of
    the same name.
    """
    current: dict[str, dict] = {}
    async for d in user_tools_col.find({"user_id": user_id}):
        current[d["name"]] = d
    # Evict registry entries this user owns that are gone from Mongo.
    for stale in tools_pkg.user_tool_names(user_id) - set(current):
        tools_pkg.unregister(stale)
    for name, d in current.items():
        if tools_pkg.is_global(name):
            continue  # never shadow a built-in
        kind = d.get("kind") or TOOL_KIND_WEBHOOK
        tools_pkg.register(Tool(
            name=name, kind=kind,
            description=d.get("description", ""),
            input_schema=d.get("input_schema") or {},
            webhook_url=d.get("webhook_url"),
            webhook_secret=d.get("webhook_secret"),
            mcp_server_id=d.get("mcp_server_id"),
            remote_name=d.get("remote_name"),
            owner_user_id=user_id,
            source=d.get("source") or ("mcp" if kind == TOOL_KIND_MCP else "user"),
            tags=list(d.get("tags") or []),
        ))


@router.get("/tools")
async def list_tools_api(user=Depends(get_current_user)):
    await _hydrate_user_tools(user["id"])
    out = []
    for t in _list_tools(user_id=user["id"], include_globals=True):
        out.append({
            "name": t.name, "kind": t.kind, "description": t.description,
            "input_schema": t.input_schema, "source": t.source, "tags": t.tags,
            "owner_user_id": t.owner_user_id,
            "mcp_server_id": t.mcp_server_id, "remote_name": t.remote_name,
        })
    return {"count": len(out), "tools": out}


@router.post("/tools/webhook")
async def register_webhook_tool(body: WebhookToolBody, user=Depends(get_current_user)):
    if not body.webhook_url.startswith(("http://", "https://")):
        raise HTTPException(400, "webhook_url must be http(s)://...")
    doc = {
        "_id": str(uuid.uuid4()), "user_id": user["id"],
        "name": body.name, "description": body.description,
        "kind": TOOL_KIND_WEBHOOK,
        "webhook_url": body.webhook_url,
        "webhook_secret": body.webhook_secret,
        "input_schema": body.input_schema or {"type": "object"},
        "tags": body.tags or [], "source": "user",
        "created_at_ms": int(time.time() * 1000),
    }
    if tools_pkg.is_global(body.name):
        raise HTTPException(409, f"tool name {body.name!r} is reserved by a built-in tool")
    if await user_tools_col.find_one({"user_id": user["id"], "name": body.name}):
        raise HTTPException(409, f"tool {body.name!r} already exists for this user")
    await user_tools_col.insert_one(doc)
    await _hydrate_user_tools(user["id"])
    return {"ok": True, "tool": {"id": doc["_id"], "name": body.name}}


@router.delete("/tools/{name}")
async def delete_tool(name: str, user=Depends(get_current_user)):
    r = await user_tools_col.delete_one({"user_id": user["id"], "name": name})
    if r.deleted_count == 0:
        raise HTTPException(404, "tool not found (cannot delete built-ins)")
    # Evict from the in-process registry so the deleted tool (and its webhook
    # secret) can no longer be invoked or listed before the next restart — but
    # only when the current registry entry is this user's own tool, never a
    # built-in or another user's entry that happens to share the name.
    existing = tools_pkg.lookup(name)
    if existing is not None and existing.owner_user_id == user["id"]:
        tools_pkg.unregister(name)
    return {"ok": True}


@router.post("/tools/{name}/invoke")
async def invoke_tool(name: str, body: InvokeToolBody, user=Depends(get_current_user)):
    await _hydrate_user_tools(user["id"])
    try:
        result = await tools_pkg.invoke(
            name, body.params,
            user=user,
            pending_overrides_col=pending_overrides_col,
            fiq_audit_col=fiq_audit_col,
            override_id=body.override_id,
        )
        return {"ok": True, "result": result}
    except ToolError as e:
        from fastapi.responses import JSONResponse
        payload = {"ok": False, "error": str(e), "halt": e.halt,
                   "override_id": e.override_id, "sentinel_verdict": e.sentinel_verdict}
        return JSONResponse(status_code=202 if e.halt else 400, content=payload)


# ---- MCP servers (client-side registry) ----------------------------------
class MCPServerBody(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name: str = Field(..., min_length=2, max_length=64)
    url: str
    token: Optional[str] = None


async def _refresh_mcp_tools(user_id: str, server: dict) -> dict:
    """Probe the remote server, mirror its tools into user_tools_col."""
    probe = await mcp_relay.ping_server(server["url"], token=server.get("token"))
    if not probe["ok"]:
        return {"ok": False, "tools": [], "error": probe["error"]}
    now = int(time.time() * 1000)
    # Clear stale mcp tools from this server first.
    await user_tools_col.delete_many({"user_id": user_id, "mcp_server_id": server["_id"]})
    out: list[str] = []
    for t in probe["tools"]:
        rname = t.get("name")
        if not rname:
            continue
        doc = {
            "_id": str(uuid.uuid4()), "user_id": user_id,
            "name": f"mcp:{server['name']}:{rname}",
            "kind": TOOL_KIND_MCP,
            "description": t.get("description", ""),
            "input_schema": t.get("inputSchema") or {"type": "object"},
            "mcp_server_id": server["_id"], "remote_name": rname,
            "tags": ["mcp", server["name"]], "source": "mcp",
            "created_at_ms": now,
        }
        await user_tools_col.insert_one(doc)
        out.append(doc["name"])
    await mcp_servers_col.update_one({"_id": server["_id"]}, {"$set": {"last_refresh_ms": now, "tools_count": len(out)}})
    return {"ok": True, "tools": out, "error": None}


@router.get("/mcp/servers")
async def list_mcp_servers(user=Depends(get_current_user)):
    out = []
    async for d in mcp_servers_col.find({"user_id": user["id"]}).sort("name", 1):
        out.append({"id": d["_id"], "name": d["name"], "url": d["url"],
                    "tools_count": d.get("tools_count", 0),
                    "last_refresh_ms": d.get("last_refresh_ms"),
                    "has_token": bool(d.get("token"))})
    return {"servers": out}


@router.post("/mcp/servers")
async def add_mcp_server(body: MCPServerBody, user=Depends(get_current_user)):
    if not body.url.startswith(("http://", "https://")):
        raise HTTPException(400, "url must be http(s)://...")
    if await mcp_servers_col.find_one({"user_id": user["id"], "name": body.name}):
        raise HTTPException(409, f"mcp server {body.name!r} already exists")
    doc = {"_id": str(uuid.uuid4()), "user_id": user["id"],
           "name": body.name, "url": body.url, "token": body.token,
           "created_at_ms": int(time.time() * 1000), "tools_count": 0}
    await mcp_servers_col.insert_one(doc)
    refresh = await _refresh_mcp_tools(user["id"], doc)
    return {"ok": True, "id": doc["_id"], "refresh": refresh}


@router.post("/mcp/servers/{server_id}/refresh")
async def refresh_mcp_server(server_id: str, user=Depends(get_current_user)):
    server = await mcp_servers_col.find_one({"_id": server_id, "user_id": user["id"]})
    if not server:
        raise HTTPException(404, "mcp server not found")
    return await _refresh_mcp_tools(user["id"], server)


@router.delete("/mcp/servers/{server_id}")
async def delete_mcp_server(server_id: str, user=Depends(get_current_user)):
    server = await mcp_servers_col.find_one({"_id": server_id, "user_id": user["id"]})
    if not server:
        raise HTTPException(404, "mcp server not found")
    await user_tools_col.delete_many({"user_id": user["id"], "mcp_server_id": server_id})
    await mcp_servers_col.delete_one({"_id": server_id})
    return {"ok": True}


# ---- Skills --------------------------------------------------------------
class SkillBody(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name: str = Field(..., min_length=2, max_length=80)
    description: str = ""
    prompt_template: str = ""
    tool_bindings: list[str] = []
    sentinel_overrides: dict = {}
    scope_tokens: Optional[list[str]] = None
    logic_set_tokens: Optional[list[str]] = None
    force: bool = False


@router.get("/skills")
async def list_skills_api(user=Depends(get_current_user)):
    skills = await skills_pkg.list_skills(skills_col, user_id=user["id"])
    return {"count": len(skills), "skills": [s.__dict__ for s in skills]}


@router.post("/skills/check-overlap")
async def check_overlap(body: SkillBody, user=Depends(get_current_user)):
    scope = body.scope_tokens or skills_pkg.tokenize_scope(body.name + " " + body.description)
    logic = body.logic_set_tokens or skills_pkg.tokenize_logic(body.description)
    matches = await skills_pkg.check_overlap(skills_col, scope, logic, user_id=user["id"])
    return {"scope_tokens": scope, "logic_set_tokens": logic, "matches": matches}


@router.post("/skills")
async def register_skill_api(body: SkillBody, user=Depends(get_current_user)):
    try:
        sk = await skills_pkg.register_skill(
            skills_col, user_id=user["id"],
            name=body.name, description=body.description,
            prompt_template=body.prompt_template,
            tool_bindings=body.tool_bindings,
            sentinel_overrides=body.sentinel_overrides,
            scope_tokens=body.scope_tokens, logic_set_tokens=body.logic_set_tokens,
            force=body.force,
        )
        return {"ok": True, "skill": sk.__dict__}
    except skills_pkg.SkillExistsWarning as w:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=409, content={
            "ok": False, "error": str(w), "similar": w.similar,
            "hint": "POST again with force=true to register anyway",
        })


@router.delete("/skills/{skill_id}")
async def delete_skill_api(skill_id: str, user=Depends(get_current_user)):
    ok = await skills_pkg.delete_skill(skills_col, skill_id, user["id"])
    if not ok:
        raise HTTPException(404, "skill not found or not owned by you")
    return {"ok": True}


@router.post("/skills/sync")
async def sync_skills_api(user=Depends(get_current_user)):
    # Public global skill pull; any logged-in user may trigger it.
    result = await skills_pkg.pull_from_skill_lib(skills_col)
    return result


@router.post("/skills/publish")
async def publish_skills_api(user=Depends(get_current_user)):
    """Publish any skills the user has flagged ``publishable=True`` back to
    The-Interdependency/skill-lib via the GitHub API (needs SKILL_LIB_GH_TOKEN)."""
    return await skills_pkg.push_to_skill_lib_stub(skills_col, user_id=user["id"])


@router.patch("/skills/{skill_id}/publishable")
async def mark_publishable(skill_id: str, publishable: bool = True, user=Depends(get_current_user)):
    """Mark a user-owned skill as publishable (or revoke)."""
    r = await skills_col.update_one(
        {"_id": skill_id, "owner_user_id": user["id"]},
        {"$set": {"publishable": bool(publishable)}},
    )
    if r.matched_count == 0:
        raise HTTPException(404, "skill not found or not yours")
    return {"ok": True, "publishable": bool(publishable)}


__all__ = ["router"]
# ratios: loc_comments=235:62 imports_exports=14:20 calls_definitions=95:21
