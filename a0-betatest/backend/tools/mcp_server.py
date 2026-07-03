# ratios: loc_comments=126:48 imports_exports=15:5 calls_definitions=45:7
# === MODULE_BUILD ===
# id: tools_mcp_server
#   module_name: mcp_server
#   module_kind: route
#   summary: expose a0p AS an MCP server — JSON-RPC 2.0 over HTTP at /api/mcp; methods: initialize, tools/list, tools/call (sentinel-gated), resources/list (living-spec modules), resources/read; bearer-token authenticated against a per-user MCP_PUBLISH_TOKEN
#   owner: Erin Spencer
#   public_surface: router, get_or_create_publish_token
#   internal_surface: _rpc_ok, _rpc_err, _resolve_caller
#   auth_boundary: bearer
#   storage_boundary: write
#   network_boundary: external
#   user_data_boundary: write
#   admin_only: false
#   tests: a0p_skills.contracts.tools_mcp_server_initialize_holds
#   rollout: default_enabled
#   rollback: revert; external MCP clients (Claude Desktop, Cursor, etc.) cannot connect
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: tools_mcp_server_boundaries
#   summary: inbound JSON-RPC 2.0 surface for external MCP clients
#   auth_boundary: bearer
#   storage_boundary: write
#   network_boundary: external
#   user_data_boundary: write
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: tools_mcp_server
#   summary: a0p MCP server endpoint
#   exposes: router, get_or_create_publish_token
#   boundaries: auth:bearer, storage:write, network:external, user_data:write
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: tools_mcp_server_initialize
#   given: a JSON-RPC initialize call against the MCP server with no token
#   then: the response carries the MCP serverInfo and protocolVersion fields
#         and does not require auth for initialize
#   class: integration
#   call: a0p_skills.contracts.tools_mcp_server_initialize_holds
# === END CONTRACTS ===
"""a0p Model Context Protocol server (HTTP JSON-RPC 2.0)."""
from __future__ import annotations
import secrets
import time
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from auth import get_current_user
from .registry import list_tools, lookup, invoke as registry_invoke, ToolError


router = APIRouter(prefix="/api/mcp", tags=["mcp"])

_PROTOCOL_VERSION = "2024-11-05"
_SERVER_INFO = {"name": "a0p", "version": "0.1.0"}


def _rpc_ok(req_id: Any, result: dict) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _rpc_err(req_id: Any, code: int, message: str, data: Optional[dict] = None) -> dict:
    err = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": req_id, "error": err}


async def get_or_create_publish_token(user: dict) -> str:
    """Return the user's current MCP publish token, minting one if needed."""
    from db import users_col
    rec = await users_col.find_one({"_id": user["id"]}, {"mcp_publish_token": 1})
    tok = (rec or {}).get("mcp_publish_token")
    if tok:
        return tok
    tok = "a0p_mcp_" + secrets.token_urlsafe(28)
    await users_col.update_one({"_id": user["id"]}, {"$set": {"mcp_publish_token": tok}})
    return tok


@router.get("/publish-token")
async def get_publish_token(user=Depends(get_current_user)):
    """Return (or mint) the bearer token external MCP clients use to call this user's MCP surface."""
    tok = await get_or_create_publish_token(user)
    return {
        "url": "/api/mcp",
        "token": tok,
        "header": "Authorization: Bearer " + tok,
    }


@router.post("/publish-token/rotate")
async def rotate_publish_token(user=Depends(get_current_user)):
    from db import users_col
    tok = "a0p_mcp_" + secrets.token_urlsafe(28)
    await users_col.update_one({"_id": user["id"]}, {"$set": {"mcp_publish_token": tok}})
    return {"token": tok}


async def _resolve_caller(request: Request) -> Optional[dict]:
    """Map an Authorization: Bearer <token> on the JSON-RPC endpoint to a user."""
    auth = request.headers.get("Authorization", "")
    if not auth.lower().startswith("bearer "):
        return None
    tok = auth[7:].strip()
    if not tok.startswith("a0p_mcp_"):
        return None
    from db import users_col
    user = await users_col.find_one({"mcp_publish_token": tok})
    if not user:
        return None
    user["id"] = user.pop("_id")
    user.pop("password_hash", None)
    return user


@router.post("")
async def mcp_rpc(request: Request) -> dict:
    """Single JSON-RPC entrypoint; method names follow the MCP spec."""
    try:
        body = await request.json()
    except Exception:
        return _rpc_err(None, -32700, "parse error")
    method = body.get("method")
    req_id = body.get("id")
    params = body.get("params") or {}

    # `initialize` is open — clients use it to discover server capabilities.
    if method == "initialize":
        return _rpc_ok(req_id, {
            "protocolVersion": _PROTOCOL_VERSION,
            "serverInfo": _SERVER_INFO,
            "capabilities": {"tools": {"listChanged": False}, "resources": {"listChanged": False}},
        })

    caller = await _resolve_caller(request)
    if caller is None:
        return _rpc_err(req_id, -32001, "unauthorized — supply Authorization: Bearer <a0p_mcp_...> token")

    if method == "tools/list":
        tools = list_tools(user_id=caller["id"], include_globals=True)
        return _rpc_ok(req_id, {
            "tools": [
                {"name": t.name, "description": t.description,
                 "inputSchema": t.input_schema or {"type": "object"},
                 "source": t.source, "tags": t.tags}
                for t in tools
            ],
        })

    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        from db import pending_overrides_col, fiq_audit_col
        try:
            result = await registry_invoke(
                name, args,
                user=caller,
                pending_overrides_col=pending_overrides_col,
                fiq_audit_col=fiq_audit_col,
            )
            return _rpc_ok(req_id, {"content": [{"type": "text", "text": str(result)}], "structuredContent": result})
        except ToolError as e:
            return _rpc_err(req_id, -32002, str(e), {
                "halt": e.halt, "override_id": e.override_id,
                "sentinel_verdict": e.sentinel_verdict,
            })

    if method == "resources/list":
        from living_spec import scan_repo_blocks
        mods = scan_repo_blocks()
        return _rpc_ok(req_id, {
            "resources": [
                {"uri": f"a0p://spec/{m['id']}", "name": m["module_name"],
                 "description": m["summary"], "mimeType": "application/json"}
                for m in mods[:200] if m.get("id")
            ],
        })

    if method == "resources/read":
        uri = params.get("uri", "")
        if not uri.startswith("a0p://spec/"):
            return _rpc_err(req_id, -32602, f"unknown uri scheme {uri!r}")
        target_id = uri[len("a0p://spec/"):]
        from living_spec import scan_repo_blocks
        for m in scan_repo_blocks():
            if m.get("id") == target_id:
                import json as _json
                return _rpc_ok(req_id, {
                    "contents": [{"uri": uri, "mimeType": "application/json",
                                  "text": _json.dumps(m, indent=2)}]
                })
        return _rpc_err(req_id, -32603, f"resource not found: {uri}")

    return _rpc_err(req_id, -32601, f"method not found: {method}")


__all__ = ["router", "get_or_create_publish_token"]
# ratios: loc_comments=126:48 imports_exports=15:5 calls_definitions=45:7
