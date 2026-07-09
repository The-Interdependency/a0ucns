# ratios: loc_comments=373:118 imports_exports=19:25 calls_definitions=157:29
# === MODULE_BUILD ===
# id: api_tools_mcp_skills_routes
#   module_name: api_tools_mcp_skills
#   module_kind: route
#   summary: REST surface for the tools / MCP-client / Odysseus-client / skills layer — /api/tools (list, register user-webhook tool, invoke), /api/mcp/servers (CRUD external MCP servers, refresh their tools), /api/odysseus/servers (CRUD registered Odysseus workspaces, refresh their scoped /api/codex/* catalogue tools), /api/skills (list, register w/ overlap warning, delete, sync from skill-lib)
#   owner: Erin Spencer
#   public_surface: router
#   internal_surface: _refresh_mcp_tools, _safe_mcp_tool_name, _migrate_allow_lists, _user_id
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
import hashlib
import logging
import re
import time
import uuid
from typing import Any, Optional
from urllib.parse import urlsplit

_log = logging.getLogger("a0p.tools_mcp_skills")

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from pymongo.errors import DuplicateKeyError

from auth import get_current_user
from db import (
    user_tools_col, mcp_servers_col, odysseus_servers_col, skills_col,
    pending_overrides_col, fiq_audit_col, agent_instances_col,
)

import tools as tools_pkg
from tools.registry import (
    Tool, ToolError, TOOL_KIND_NATIVE, TOOL_KIND_WEBHOOK, TOOL_KIND_MCP,
    TOOL_KIND_ODYSSEUS, list_tools as _list_tools,
)
from tools import mcp_relay, odysseus_relay
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


_UNSAFE_TOOL_NAME_RE = re.compile(r"[^A-Za-z0-9_-]+")


def _safe_mcp_tool_name(server_name: str, server_id: str, remote_name: str) -> str:
    """Provider-safe, globally-unique public name for a mirrored MCP tool.

    Mirrors ``tools.odysseus_relay.safe_tool_name``'s discipline (the Odysseus
    client already applies it): OpenAI/Anthropic/Gemini function names must match
    ``[A-Za-z0-9_-]`` and are ~64-char bounded. The old ``mcp:{name}:{remote}``
    form was provider-unsafe (``:`` and raw user/remote text) AND keyed the
    process-wide tool registry on the user-chosen server name, so two users who
    both name a server ``home`` (or a name reused after delete) collided onto one
    another's ``Tool``. Sanitize the readable parts and disambiguate with a hash
    of the STABLE per-server id (a UUID), never the name.
    """
    sv = _UNSAFE_TOOL_NAME_RE.sub("_", server_name or "").strip("_") or "srv"
    rn = _UNSAFE_TOOL_NAME_RE.sub("_", remote_name or "").strip("_") or "tool"
    # Hash the (server_id, RAW remote_name) pair — not just the server id — so two
    # long remote names that sanitize/truncate to the same readable prefix still
    # get distinct public names instead of colliding (which would DuplicateKeyError
    # and silently drop the second tool on a namespaced MCP server).
    h = hashlib.sha256(
        f"{server_id or server_name or ''}\x00{remote_name or ''}".encode("utf-8")
    ).hexdigest()[:12]
    name = f"mcp_{sv}_{h}_{rn}"
    if len(name) <= 64:
        return name
    # Both readable parts are user/remote-chosen; bound them, keep hash intact.
    budget = 64 - len(f"mcp__{h}_")
    half = max(1, budget // 2)
    return f"mcp_{sv[:half]}_{h}_{rn[:budget - half]}"[:64]


async def _migrate_allow_lists(user_id: str, rename_map: dict) -> int:
    """Rewrite this user's agent allow-lists from old->new MCP tool names.

    The public MCP tool name changed (``mcp:<server>:<remote>`` -> sanitized
    ``mcp_<server>_<hash>_<remote>``). Agents resolve ``sheet.tools_allowed`` by
    EXACT name (runtime ``tools_lookup``), and a refresh deletes the old rows and
    writes only the new names — so without this, agents that had the old name
    saved would silently lose the MCP tool after a refresh. Migrate the acting
    user's agents in place so the allow-list keeps pointing at the same tool.
    """
    if not rename_map:
        return 0
    migrated = 0
    cursor = agent_instances_col.find(
        {"user_id": user_id, "sheet.tools_allowed": {"$in": list(rename_map)}})
    async for agent in cursor:
        allowed = (agent.get("sheet") or {}).get("tools_allowed") or []
        new_allowed = [rename_map.get(x, x) for x in allowed]
        if new_allowed != allowed:
            await agent_instances_col.update_one(
                {"_id": agent["_id"]}, {"$set": {"sheet.tools_allowed": new_allowed}})
            migrated += 1
    return migrated


async def _refresh_mcp_tools(user_id: str, server: dict) -> dict:
    """Probe the remote server, mirror its tools into user_tools_col."""
    probe = await mcp_relay.ping_server(server["url"], token=server.get("token"))
    if not probe["ok"]:
        return {"ok": False, "tools": [], "error": probe["error"]}
    now = int(time.time() * 1000)
    # Clear stale mcp tools from this server first.
    await user_tools_col.delete_many({"user_id": user_id, "mcp_server_id": server["_id"]})
    out: list[str] = []
    skipped: list[str] = []
    rename_map: dict = {}   # old public name -> new public name (successful writes only)
    for t in probe["tools"]:
        rname = t.get("name")
        if not rname:
            continue
        name = _safe_mcp_tool_name(server["name"], server["_id"], rname)
        doc = {
            "_id": str(uuid.uuid4()), "user_id": user_id,
            "name": name,
            "kind": TOOL_KIND_MCP,
            "description": t.get("description", ""),
            "input_schema": t.get("inputSchema") or {"type": "object"},
            "mcp_server_id": server["_id"], "remote_name": rname,
            "tags": ["mcp", server["name"]], "source": "mcp",
            "created_at_ms": now,
        }
        try:
            await user_tools_col.insert_one(doc)
            out.append(name)
            rename_map[f"mcp:{server['name']}:{rname}"] = name
        except DuplicateKeyError:
            # Another tool of this user already holds the generated name; skip it
            # (never 500 the create/refresh or leave an orphan server).
            skipped.append(name)
    # Migrate saved agent allow-lists from the old name form to the new one.
    migrated = await _migrate_allow_lists(user_id, rename_map)
    await mcp_servers_col.update_one({"_id": server["_id"]}, {"$set": {"last_refresh_ms": now, "tools_count": len(out)}})
    return {"ok": True, "tools": out, "skipped": skipped, "migrated_agents": migrated, "error": None}


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


# ---- Odysseus workspaces (scoped /api/codex/* REST client) ---------------
class OdysseusServerBody(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name: str = Field(..., min_length=2, max_length=64)
    base_url: str
    token: Optional[str] = None
    # Opt-in for a self-hosted / localhost / LAN Odysseus. When false (default)
    # the SSRF guard refuses non-global base_url hosts.
    allow_private: bool = False


async def _refresh_odysseus_tools(user_id: str, conn: dict) -> dict:
    """Probe the Odysseus capabilities endpoint, (re)mirror the catalogue tools.

    Every catalogue capability is materialized as an ``odysseus:<name>:<cap>``
    tool of kind ``odysseus``; Odysseus itself enforces api_token scopes at call
    time, so a capability the token cannot reach simply returns a scoped error
    when invoked. The probe result (what the token *can* reach) is returned so
    the caller sees the effective grant.
    """
    probe = await odysseus_relay.probe_capabilities(
        conn["base_url"], conn.get("token"), bool(conn.get("allow_private", False)))
    now = int(time.time() * 1000)
    await user_tools_col.delete_many({"user_id": user_id, "mcp_server_id": conn["_id"], "source": "odysseus"})
    out: list[str] = []
    skipped: list[str] = []
    for cap, spec in odysseus_relay.ODYSSEUS_CATALOGUE.items():
        # Provider-safe, globally-unique public name ([A-Za-z0-9_-], <=64) so
        # OpenAI/Anthropic/Gemini tool-calling accepts the schema and two users'
        # same-named workspaces don't collide in the process-wide registry;
        # remote_name keeps the raw cap.
        name = odysseus_relay.safe_tool_name(conn["name"], cap, conn["_id"])
        doc = {
            "_id": str(uuid.uuid4()), "user_id": user_id,
            "name": name,
            "kind": TOOL_KIND_ODYSSEUS,
            "description": spec.get("description", ""),
            "input_schema": spec.get("input_schema") or {"type": "object"},
            "mcp_server_id": conn["_id"], "remote_name": cap,
            "tags": ["odysseus", conn["name"]], "source": "odysseus",
            "created_at_ms": now,
        }
        try:
            await user_tools_col.insert_one(doc)
            out.append(name)
        except DuplicateKeyError:
            # A non-odysseus tool of this user already holds the generated name;
            # skip it (never 500 the create/refresh or leave an orphan server).
            skipped.append(name)
    # Keep the detailed probe error server-side only; never reflect the raw
    # exception text (which can carry internal host/stack detail) back to the
    # caller. The client gets a coarse reachability signal instead.
    if not probe["ok"]:
        # Log only the exception CLASS name (safe — not user content). The full
        # message can embed the registered base_url, so it is never logged.
        _log.warning("odysseus workspace probe failed (kind=%s)",
                     probe.get("error_kind") or "error")
    coarse = None if probe["ok"] else "workspace unreachable or refused"
    await odysseus_servers_col.update_one(
        {"_id": conn["_id"]},
        {"$set": {"last_refresh_ms": now, "tools_count": len(out),
                  "reachable": probe["ok"], "probe_error": coarse}},
    )
    return {"ok": True, "tools": out, "skipped": skipped,
            "capabilities": probe["capabilities"],
            "reachable": probe["ok"], "error": coarse}


@router.get("/odysseus/servers")
async def list_odysseus_servers(user=Depends(get_current_user)):
    out = []
    async for d in odysseus_servers_col.find({"user_id": user["id"]}).sort("name", 1):
        out.append({"id": d["_id"], "name": d["name"], "base_url": d["base_url"],
                    "tools_count": d.get("tools_count", 0),
                    "last_refresh_ms": d.get("last_refresh_ms"),
                    "reachable": d.get("reachable"), "has_token": bool(d.get("token")),
                    "allow_private": bool(d.get("allow_private", False))})
    return {"servers": out}


@router.post("/odysseus/servers")
async def add_odysseus_server(body: OdysseusServerBody, user=Depends(get_current_user)):
    if not body.base_url.startswith(("http://", "https://")):
        raise HTTPException(400, "base_url must be http(s)://...")
    if "?" in body.base_url or "#" in body.base_url:
        raise HTTPException(400, "base_url must not contain a query or fragment")
    try:
        _sp = urlsplit(body.base_url)
        _ = _sp.port  # raises ValueError on a malformed port
    except ValueError:
        raise HTTPException(400, "base_url has an invalid port")
    if not _sp.netloc:
        raise HTTPException(400, "base_url must include a host (e.g. http://host:port)")
    if not (body.token or "").strip():
        # /api/codex/capabilities can answer without a token, but the actual data
        # routes are api_token-scoped and reject session-less server-to-server
        # calls — so a token is required or every mirrored tool fails at invoke.
        raise HTTPException(400, "an Odysseus api_token is required (the /api/codex/* data routes are token-scoped)")
    if await odysseus_servers_col.find_one({"user_id": user["id"], "name": body.name}):
        raise HTTPException(409, f"odysseus workspace {body.name!r} already exists")
    doc = {"_id": str(uuid.uuid4()), "user_id": user["id"],
           "name": body.name, "base_url": body.base_url.rstrip("/"), "token": body.token,
           "allow_private": bool(body.allow_private),
           "created_at_ms": int(time.time() * 1000), "tools_count": 0}
    await odysseus_servers_col.insert_one(doc)
    refresh = await _refresh_odysseus_tools(user["id"], doc)
    # Register the mirrored tools in-process now (mirrors webhook registration),
    # so an agent tool loop can build provider schemas without waiting for a
    # later /api/tools hydrate.
    await _hydrate_user_tools(user["id"])
    return {"ok": True, "id": doc["_id"], "refresh": refresh}


@router.post("/odysseus/servers/{server_id}/refresh")
async def refresh_odysseus_server(server_id: str, user=Depends(get_current_user)):
    conn = await odysseus_servers_col.find_one({"_id": server_id, "user_id": user["id"]})
    if not conn:
        raise HTTPException(404, "odysseus workspace not found")
    refresh = await _refresh_odysseus_tools(user["id"], conn)
    await _hydrate_user_tools(user["id"])
    return refresh


@router.delete("/odysseus/servers/{server_id}")
async def delete_odysseus_server(server_id: str, user=Depends(get_current_user)):
    conn = await odysseus_servers_col.find_one({"_id": server_id, "user_id": user["id"]})
    if not conn:
        raise HTTPException(404, "odysseus workspace not found")
    await user_tools_col.delete_many({"user_id": user["id"], "mcp_server_id": server_id, "source": "odysseus"})
    await odysseus_servers_col.delete_one({"_id": server_id})
    # Evict the now-deleted tools from the in-process registry so an agent stops
    # advertising them before the next /api/tools hydrate (reconcile drops any
    # registry entry no longer backed by a Mongo row).
    await _hydrate_user_tools(user["id"])
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
# ratios: loc_comments=373:118 imports_exports=19:25 calls_definitions=157:29
