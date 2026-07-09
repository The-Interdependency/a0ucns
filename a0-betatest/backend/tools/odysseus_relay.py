# ratios: loc_comments=200:118 imports_exports=13:5 calls_definitions=65:8
# === MODULE_BUILD ===
# id: tools_odysseus_relay
#   module_name: odysseus_relay
#   module_kind: adapter
#   summary: relay a0p tool calls to a registered Odysseus workspace over its scoped /api/codex/* REST surface — outbound httpx client attaching the per-connection Bearer api_token; the destination host is the operator-registered base_url (never agent-supplied) and the path is pinned to the /api/codex/ prefix; an SSRF guard refuses non-global hosts unless the connection is explicitly allow_private (self-hosted/localhost opt-in), so Odysseus's own api_token scopes bound every capability while a0p sentinels gate each call
#   owner: Erin Spencer
#   public_surface: probe_capabilities, request, invoke, safe_tool_name, ODYSSEUS_CATALOGUE
#   internal_surface: _guard_path, _resolve_spec, _assert_allowed_host
#   auth_boundary: bearer
#   storage_boundary: read
#   network_boundary: external
#   user_data_boundary: read
#   admin_only: false
#   tests: a0p_skills.contracts.tools_odysseus_relay_request_holds
#   rollout: default_enabled
#   rollback: revert; odysseus-typed tools become invokable-but-unreachable
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: tools_odysseus_relay_boundaries
#   summary: outbound scoped-REST client to a user-registered Odysseus workspace
#   auth_boundary: bearer
#   storage_boundary: read
#   network_boundary: external
#   user_data_boundary: read
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: tools_odysseus_relay
#   summary: outbound Odysseus /api/codex/* REST client
#   exposes: probe_capabilities, request, invoke, safe_tool_name, ODYSSEUS_CATALOGUE
#   boundaries: auth:bearer, storage:read, network:external, user_data:read
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: tools_odysseus_relay_request
#   given: an Odysseus /api/codex/* surface stubbed with an httpx MockTransport
#   then: request() round-trips a 200 JSON body with the Bearer token attached,
#         surfaces a non-2xx as ToolError, and refuses any path outside
#         /api/codex/ before touching the network
#   class: integration
#   call: a0p_skills.contracts.tools_odysseus_relay_request_holds
# === END CONTRACTS ===
"""Outbound scoped-REST client for a registered Odysseus workspace.

Odysseus (The-Interdependency/odysseus-a0) exposes its agent-facing surface as
scope-gated REST under ``/api/codex/*`` (memory, email, todos, calendar,
documents, cookbook), authorized by a per-user ``api_token`` whose scopes bound
what each call may touch. It does not speak HTTP-MCP, so a0p reaches it over
this REST relay rather than ``tools.mcp_relay``.

Boundary discipline:
  * The destination host is the operator-registered ``base_url`` of a specific
    Odysseus connection, never a value the agent supplies — so this is not an
    SSRF surface; only the ``/api/codex/`` sub-path and method vary.
  * Every call carries the connection's Bearer ``api_token``; Odysseus enforces
    per-capability scopes, and a0p's sentinel gate runs first on every call.
  * Only read-scoped GETs with no required body are pre-named in the catalogue;
    all writes go through the explicit ``request`` passthrough rather than a
    fabricated endpoint body schema.
"""
from __future__ import annotations
import asyncio
import hashlib
import ipaddress
import json
import posixpath
import re
import socket
from typing import Any, Optional
from urllib.parse import urlparse, urlsplit, urlunsplit, unquote

import httpx

from .registry import Tool, ToolError, TOOL_KIND_ODYSSEUS


_CODEX_PREFIX = "/api/codex/"
_ALLOWED_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}
_UNSAFE_NAME_RE = re.compile(r"[^a-zA-Z0-9_-]")
# Cap what a single Odysseus tool result feeds back into the agent's next
# provider request, so a verbose endpoint can't blow the model context.
_MAX_RESULT_BYTES = 16384


def safe_tool_name(workspace: str, cap: str, server_id: str) -> str:
    """Build a provider-safe, globally-unique public tool name for a capability.

    OpenAI / Anthropic / Gemini function names must match ``[A-Za-z0-9_-]`` and
    are length-bounded (~64). The workspace name is user-chosen, so sanitize it
    (non-conforming chars -> ``_``) for the readable part and bound the whole name
    to 64 chars. The disambiguator hashes the stable per-connection ``server_id``
    (a UUID), NOT the workspace name — the in-process tool registry is keyed by
    name across all users, so hashing the connection id keeps two users who both
    name a workspace ``home`` (and two same-user names that sanitize alike) from
    colliding onto one another's ``Tool``.
    """
    ws = _UNSAFE_NAME_RE.sub("_", workspace).strip("_") or "ws"
    # 48 bits of the server-id digest — collision-resistant for any realistic
    # number of same-named workspaces, while staying within the 64-char limit.
    h = hashlib.sha256((server_id or workspace).encode("utf-8")).hexdigest()[:12]
    name = f"odysseus_{ws}_{h}_{cap}"
    if len(name) <= 64:
        return name
    keep = 64 - len(f"odysseus__{h}_{cap}")
    ws = ws[:max(1, keep)]
    return f"odysseus_{ws}_{h}_{cap}"[:64]


_NAT64 = (ipaddress.ip_network("64:ff9b::/96"), ipaddress.ip_network("64:ff9b:1::/48"))


async def _assert_allowed_host(base_url: str, allow_private: bool) -> None:
    """SSRF guard for a registered workspace host.

    Resolves ``base_url``'s host and, unless the connection is explicitly marked
    ``allow_private`` (a local-first / self-hosted Odysseus on localhost or a
    LAN — the common case), refuses any address that is not globally routable.
    This mirrors the ``fetch_url`` guard so a registered ``base_url`` cannot aim
    a0p at cloud metadata (169.254.169.254), loopback, or internal services;
    ``allow_private`` is a per-connection opt-in the user sets knowingly. DNS is
    resolved in a worker thread with a bounded timeout, and an IPv6 wrapper's
    embedded IPv4 (v4-mapped / 6to4 / Teredo / NAT64) is checked too.
    """
    p = urlparse(base_url)
    host = p.hostname
    if not host:
        raise ToolError("odysseus: base_url missing host")
    if allow_private:
        return  # user opted in to a private / self-hosted target
    port = p.port or (443 if p.scheme == "https" else 80)
    try:
        infos = await asyncio.wait_for(
            asyncio.to_thread(socket.getaddrinfo, host, port, 0, 0, socket.IPPROTO_TCP),
            timeout=5.0,
        )
    except asyncio.TimeoutError:
        raise ToolError(f"odysseus: DNS resolution timed out for host {host!r}")
    except socket.gaierror as e:
        raise ToolError(f"odysseus: cannot resolve host {host!r}: {e}")
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        candidates = [ip]
        if isinstance(ip, ipaddress.IPv6Address):
            if ip.ipv4_mapped:
                candidates.append(ip.ipv4_mapped)
            if ip.sixtofour:
                candidates.append(ip.sixtofour)
            if ip.teredo:
                candidates.extend(a for a in ip.teredo if a)
            if any(ip in net for net in _NAT64):
                candidates.append(ipaddress.ip_address(int(ip) & 0xFFFFFFFF))
        for cand in candidates:
            if not cand.is_global:
                raise ToolError(
                    f"odysseus: refusing non-global address {cand} for host {host!r} "
                    "(set allow_private on the connection for a self-hosted Odysseus)")


# Stable capability key -> call spec. `request` is the generic scoped passthrough
# (the agent supplies method + /api/codex/ path); the rest are read-only GETs.
ODYSSEUS_CATALOGUE: dict[str, dict] = {
    "capabilities": {
        "method": "GET", "path": "/api/codex/capabilities", "scope": "(open)",
        "description": "Report which Odysseus capabilities this api_token may use.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    "memory_list": {
        "method": "GET", "path": "/api/codex/memory", "scope": "memory:read",
        "description": "List all stored Odysseus memories. This endpoint has no "
                       "server-side filter — it returns the full memory list.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    "todos_list": {
        "method": "GET", "path": "/api/codex/todos", "scope": "todos:read",
        "query": ["archived", "label"],
        "description": "List the user's Odysseus to-dos (optional archived, label).",
        "input_schema": {"type": "object", "properties": {
            "archived": {"type": "boolean"}, "label": {"type": "string"}}, "required": []},
    },
    "documents_list": {
        "method": "GET", "path": "/api/codex/documents", "scope": "docs:read",
        "query": ["search", "language", "sort", "limit", "archived"],
        "description": "List/search the user's Odysseus documents (optional "
                       "search, language, sort, limit, archived).",
        "input_schema": {"type": "object", "properties": {
            "search": {"type": "string"}, "language": {"type": "string"},
            "sort": {"type": "string"}, "limit": {"type": "integer"},
            "archived": {"type": "boolean"}}, "required": []},
    },
    "calendar_events": {
        "method": "GET", "path": "/api/codex/calendar/events", "scope": "calendar:read",
        "query": ["start", "end", "calendar"],
        "description": "List Odysseus calendar events in a window. start and end "
                       "are REQUIRED (ISO datetimes); calendar is optional.",
        "input_schema": {"type": "object", "properties": {
            "start": {"type": "string"}, "end": {"type": "string"},
            "calendar": {"type": "string"}}, "required": ["start", "end"]},
    },
    "request": {
        "method": None, "path": None, "scope": "(varies — Odysseus enforces per path)",
        "description": ("Generic scoped passthrough to any /api/codex/* endpoint. "
                        "params: {method, path (must start with /api/codex/), query?, body?}."),
        "input_schema": {"type": "object", "properties": {
            "method": {"type": "string"}, "path": {"type": "string"},
            "query": {"type": "object"}, "body": {"type": "object"}},
            "required": ["method", "path"]},
    },
}


def _guard_path(path: str) -> str:
    """Refuse anything that is not a relative path strictly under /api/codex/.

    Beyond the raw prefix check, decode percent-encoding and reject any ``.``/
    ``..`` segment, then confirm the normalized path still resolves under the
    prefix — so ``/api/codex/../admin`` (or an encoded ``%2e%2e`` variant) cannot
    escape the scoped surface once the client/server normalizes the URL.
    """
    if not isinstance(path, str) or not path.startswith(_CODEX_PREFIX):
        raise ToolError(f"odysseus: path must start with {_CODEX_PREFIX!r}, got {path!r}")
    if "://" in path or path.startswith("//"):
        raise ToolError("odysseus: path must be a relative /api/codex/ path, not a URL")
    decoded = unquote(urlsplit(path).path)
    if any(seg in (".", "..") for seg in decoded.split("/")):
        raise ToolError(f"odysseus: path must not contain '.'/'..' segments: {path!r}")
    norm = posixpath.normpath(decoded)
    if norm != _CODEX_PREFIX.rstrip("/") and not (norm + "/").startswith(_CODEX_PREFIX):
        raise ToolError(f"odysseus: path escapes {_CODEX_PREFIX!r}: {path!r}")
    return path


async def request(base_url: str, token: Optional[str], method: str, path: str, *,
                  query: Optional[dict] = None, json_body: Optional[dict] = None,
                  timeout: float = 20.0, allow_private: bool = False,
                  client: Optional[httpx.AsyncClient] = None) -> Any:
    """Call one Odysseus /api/codex/* endpoint; return parsed JSON or raise ToolError.

    The destination host is ``base_url`` (the operator-registered workspace host,
    never agent-supplied) and the path is pinned to ``/api/codex/``. The SSRF
    guard runs before egress unless ``allow_private`` opts the connection in to a
    self-hosted/localhost target. ``client`` lets a caller inject a pre-built
    AsyncClient (the contract test's MockTransport); when omitted a short-lived
    client is created here.
    """
    method = (method or "GET").upper()
    if method not in _ALLOWED_METHODS:
        raise ToolError(f"odysseus: unsupported method {method!r}")
    _guard_path(path)
    # Validate base_url (incl. a malformed port) BEFORE the host guard, which also
    # reads the port — so a bad URL raises ToolError (handled) rather than a bare
    # ValueError that the /api/tools invoke route would turn into a 500. Building
    # the URL by components also keeps the guarded /api/codex/ path in the PATH; a
    # base_url with a query/fragment would otherwise push it into the query and
    # defeat the pinning.
    sp = urlsplit(base_url)
    if sp.scheme not in ("http", "https") or not sp.netloc:
        raise ToolError(f"odysseus: base_url must be http(s)://host[:port], got {base_url!r}")
    if sp.query or sp.fragment:
        raise ToolError("odysseus: base_url must not contain a query or fragment")
    try:
        _ = sp.port  # property raises ValueError on a malformed port
    except ValueError:
        raise ToolError(f"odysseus: invalid port in base_url {base_url!r}")
    await _assert_allowed_host(base_url, allow_private)
    url = urlunsplit((sp.scheme, sp.netloc, sp.path.rstrip("/") + path, "", ""))
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    async def _do(cli: httpx.AsyncClient) -> Any:
        # An offline / timing-out / connection-reset workspace raises
        # httpx.RequestError, which is NOT a ToolError — surface it as one so the
        # invoke route returns a handled tool failure instead of a 500. Only the
        # exception class name is included (the message can embed the base_url).
        try:
            r = await cli.request(method, url, params=query or None, json=json_body, headers=headers)
        except httpx.RequestError as e:
            raise ToolError(f"odysseus request failed ({type(e).__name__})")
        # A non-2xx (Odysseus 401/403/404 with a {"detail": ...} body) or an
        # off-host redirect is a transport failure, not a result — surface it.
        if r.status_code >= 400 or r.is_redirect:
            raise ToolError(f"odysseus http {r.status_code}: {r.text[:200]}")
        try:
            data = r.json()
        except Exception:
            return {"raw": r.text[:_MAX_RESULT_BYTES], "status": r.status_code,
                    "truncated": len(r.text) > _MAX_RESULT_BYTES}
        # Cap large JSON too: the tool loop serializes the whole result back into
        # the next request, so a big memory/document list would blow the context.
        serialized = json.dumps(data, default=str)
        if len(serialized) > _MAX_RESULT_BYTES:
            return {"truncated": True, "bytes": len(serialized),
                    "preview": serialized[:_MAX_RESULT_BYTES],
                    "note": "Odysseus result truncated — use a narrower query / pagination."}
        return data

    if client is not None:
        return await _do(client)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as cli:
        return await _do(cli)


async def probe_capabilities(base_url: str, token: Optional[str],
                             allow_private: bool = False) -> dict:
    """GET /api/codex/capabilities. Returns {ok, capabilities, error_kind} (never raises)."""
    try:
        data = await request(base_url, token, "GET", "/api/codex/capabilities",
                             timeout=10.0, allow_private=allow_private)
        return {"ok": True, "capabilities": data, "error_kind": None}
    except Exception as e:
        # Return ONLY the exception class name (safe — not user content). The raw
        # message can embed the registered base_url / stack detail, so it is never
        # carried in this dict (which would taint every field returned to the API).
        return {"ok": False, "capabilities": None, "error_kind": type(e).__name__}


def _resolve_spec(cap_key: str) -> dict:
    spec = ODYSSEUS_CATALOGUE.get(cap_key)
    if spec is None:
        raise ToolError(f"odysseus: unknown capability {cap_key!r}")
    return spec


async def invoke(tool: Tool, params: dict, *, user: dict) -> Any:
    """Dispatch a TOOL_KIND_ODYSSEUS tool call to its registered connection."""
    if tool.kind != TOOL_KIND_ODYSSEUS:
        raise ToolError(f"odysseus_relay got non-odysseus tool {tool.name!r}")
    if not tool.mcp_server_id:
        raise ToolError(f"odysseus tool {tool.name!r} missing connection id")
    spec = _resolve_spec(tool.remote_name or "")
    from db import odysseus_servers_col
    conn = await odysseus_servers_col.find_one({"_id": tool.mcp_server_id, "user_id": user["id"]})
    if not conn:
        raise ToolError(f"odysseus connection {tool.mcp_server_id} not found for current user")
    base_url, token = conn["base_url"], conn.get("token")
    allow_private = bool(conn.get("allow_private", False))
    params = params or {}
    if (tool.remote_name or "") == "request":
        return await request(base_url, token, params.get("method", "GET"), params.get("path", ""),
                             query=params.get("query"), json_body=params.get("body"),
                             allow_private=allow_private)
    query = {k: params[k] for k in (spec.get("query") or []) if k in params} or None
    body = params if spec["method"] in ("POST", "PUT", "PATCH") else None
    return await request(base_url, token, spec["method"], spec["path"],
                         query=query, json_body=body, allow_private=allow_private)


__all__ = ["probe_capabilities", "request", "invoke", "safe_tool_name",
           "ODYSSEUS_CATALOGUE", "TOOL_KIND_ODYSSEUS"]
# ratios: loc_comments=200:118 imports_exports=13:5 calls_definitions=65:8
