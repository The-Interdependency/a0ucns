# ratios: loc_comments=54:49 imports_exports=6:4 calls_definitions=22:4
# === MODULE_BUILD ===
# id: tools_mcp_relay
#   module_name: mcp_relay
#   module_kind: adapter
#   summary: relay tool invocations to external MCP servers registered per user — Streamable HTTP JSON-RPC client (Model Context Protocol over HTTP) with bearer-token auth; outbound only, the server-side surface lives in tools.mcp_server
#   owner: Erin Spencer
#   public_surface: invoke, list_remote_tools, ping_server
#   internal_surface: _post_rpc
#   auth_boundary: bearer
#   storage_boundary: read
#   network_boundary: external
#   user_data_boundary: read
#   admin_only: false
#   tests: a0p_skills.contracts.tools_mcp_relay_request_holds
#   rollout: default_enabled
#   rollback: revert; mcp-typed tools become invokable-but-unreachable
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: tools_mcp_relay_boundaries
#   summary: outbound JSON-RPC client to user-registered MCP servers
#   auth_boundary: bearer
#   storage_boundary: read
#   network_boundary: external
#   user_data_boundary: read
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: tools_mcp_relay
#   summary: outbound MCP JSON-RPC client
#   exposes: invoke, list_remote_tools, ping_server
#   boundaries: auth:bearer, storage:read, network:external, user_data:read
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: tools_mcp_relay_request
#   given: a synthetic MCP server registration with a malformed URL
#   then: ping_server returns {ok:false, error:...} instead of raising
#   class: integration
#   call: a0p_skills.contracts.tools_mcp_relay_request_holds
# === END CONTRACTS ===
"""Outbound JSON-RPC 2.0 client for the Model Context Protocol."""
from __future__ import annotations
import uuid
from typing import Any, Optional

import httpx

from .registry import Tool, ToolError


async def _post_rpc(url: str, method: str, params: Optional[dict] = None,
                    headers: Optional[dict] = None, timeout: float = 20.0) -> dict:
    """POST a JSON-RPC 2.0 request, return the parsed `result` or raise ToolError."""
    payload = {"jsonrpc": "2.0", "id": str(uuid.uuid4()), "method": method, "params": params or {}}
    h = {"Accept": "application/json", "Content-Type": "application/json"}
    h.update(headers or {})
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as cli:
        r = await cli.post(url, json=payload, headers=h)
    # A non-2xx response (e.g. FastAPI 401/404 with a {"detail": ...} body) is a
    # transport failure, not a JSON-RPC result — surface it instead of parsing
    # the error body and reporting an empty success.
    if r.status_code >= 400:
        raise ToolError(f"mcp server http {r.status_code}: {r.text[:200]}")
    try:
        data = r.json()
    except Exception as e:
        raise ToolError(f"mcp server returned non-JSON ({r.status_code}): {e}")
    if not isinstance(data, dict):
        raise ToolError(f"mcp server returned unexpected JSON ({type(data).__name__})")
    if "error" in data:
        err = data["error"] or {}
        raise ToolError(f"mcp error {err.get('code')}: {err.get('message') or err}")
    if "result" not in data:
        raise ToolError(f"mcp server returned no JSON-RPC result (status {r.status_code})")
    return data.get("result") or {}


async def ping_server(url: str, *, token: Optional[str] = None) -> dict:
    """List the remote server's tools. Returns {ok:bool, tools:[...], error:str|None}."""
    try:
        headers = {"Authorization": f"Bearer {token}"} if token else None
        result = await _post_rpc(url, "tools/list", headers=headers, timeout=10.0)
        tools = result.get("tools") or []
        return {"ok": True, "tools": tools, "error": None}
    except Exception as e:
        return {"ok": False, "tools": [], "error": f"{type(e).__name__}: {e}"}


async def list_remote_tools(server_rec: dict) -> list[dict]:
    """Return the remote tool list verbatim from /tools/list."""
    r = await ping_server(server_rec["url"], token=server_rec.get("token"))
    if not r["ok"]:
        raise ToolError(r["error"] or "mcp server unreachable")
    return r["tools"]


async def invoke(tool: Tool, params: dict, *, user: dict) -> Any:
    """Call /tools/call on the remote MCP server."""
    if not tool.mcp_server_id or not tool.remote_name:
        raise ToolError(f"mcp tool {tool.name!r} missing server_id or remote_name")
    from db import mcp_servers_col
    server = await mcp_servers_col.find_one({"_id": tool.mcp_server_id, "user_id": user["id"]})
    if not server:
        raise ToolError(f"mcp server {tool.mcp_server_id} not found for current user")
    headers = {"Authorization": f"Bearer {server['token']}"} if server.get("token") else None
    result = await _post_rpc(
        server["url"], "tools/call",
        params={"name": tool.remote_name, "arguments": params},
        headers=headers,
    )
    return result


__all__ = ["invoke", "list_remote_tools", "ping_server"]
# ratios: loc_comments=54:49 imports_exports=6:4 calls_definitions=22:4
