# ratios: loc_comments=138:74 imports_exports=11:2 calls_definitions=48:6
# === MODULE_BUILD ===
# id: tools_builtin
#   module_name: builtin
#   module_kind: engine
#   summary: register the built-in native tools — living_spec_lookup, vault_get_key, fetch_url, web_search; each one declares its JSON Schema and is sentinel-gated automatically by the registry's invoke
#   owner: Erin Spencer
#   public_surface: register_builtins
#   internal_surface: _living_spec_lookup, _vault_get_key, _fetch_url, _web_search
#   auth_boundary: bearer
#   storage_boundary: read
#   network_boundary: external
#   user_data_boundary: read
#   admin_only: false
#   tests: a0p_skills.contracts.tools_builtin_registers_holds
#   rollout: default_enabled
#   rollback: revert; built-in tools disappear
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: tools_builtin_boundaries
#   summary: built-in native tools (read-only outward calls)
#   auth_boundary: bearer
#   storage_boundary: read
#   network_boundary: external
#   user_data_boundary: read
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: tools_builtin
#   summary: built-in tool registration
#   exposes: register_builtins
#   boundaries: auth:bearer, storage:read, network:external, user_data:read
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: tools_builtin_registers
#   given: register_builtins() is called against an empty registry
#   then: at least the canonical four tools (living_spec_lookup, vault_get_key,
#         fetch_url, web_search) are present afterward
#   class: correctness
#   call: a0p_skills.contracts.tools_builtin_registers_holds
# === END CONTRACTS ===
"""Built-in native tools."""
from __future__ import annotations
import asyncio
import ipaddress
import socket
from urllib.parse import urlparse

import httpx
from typing import Any

from .registry import Tool, ToolError, register, TOOL_KIND_NATIVE


async def _assert_public_url(url: str) -> None:
    """Reject non-public fetch targets (SSRF guard).

    Refuses non-http(s) schemes and any host that resolves to a non-globally-
    routable address — private, loopback, link-local (incl. cloud metadata
    169.254.169.254), shared/CGNAT (100.64.0.0/10), reserved, multicast, or
    unspecified — for both IPv4 and IPv6, via ``not ip.is_global`` (which also
    covers ranges ``is_private`` misses). Applied before the request and after
    every redirect. DNS is resolved in a worker thread with a bounded timeout so
    a slow/hostile lookup cannot block the event loop. (Residual: DNS rebinding
    between this check and connect; a full fix pins the resolved IP at connect.)
    """
    p = urlparse(url)
    if p.scheme not in ("http", "https"):
        raise ToolError(f"fetch_url: unsupported scheme {p.scheme!r}")
    host = p.hostname
    if not host:
        raise ToolError("fetch_url: missing host")
    port = p.port or (443 if p.scheme == "https" else 80)
    try:
        infos = await asyncio.wait_for(
            asyncio.to_thread(socket.getaddrinfo, host, port, 0, 0, socket.IPPROTO_TCP),
            timeout=5.0,
        )
    except asyncio.TimeoutError:
        raise ToolError(f"fetch_url: DNS resolution timed out for host {host!r}")
    except socket.gaierror as e:
        raise ToolError(f"fetch_url: cannot resolve host {host!r}: {e}")
    _NAT64 = (ipaddress.ip_network("64:ff9b::/96"), ipaddress.ip_network("64:ff9b:1::/48"))
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        # An IPv6 address can embed an IPv4 (v4-mapped, 6to4, Teredo, NAT64), so
        # a globally-classified wrapper like 64:ff9b::a9fe:a9fe translates to
        # 169.254.169.254. Reject if the address OR any embedded IPv4 is
        # non-globally-routable.
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
                raise ToolError(f"fetch_url: refusing non-global address {cand} for host {host!r}")


async def _living_spec_lookup(*, user: dict, params: dict) -> dict:
    """Lookup msdmd blocks by module_name or substring."""
    from living_spec import scan_repo_blocks
    q = (params.get("query") or "").lower().strip()
    kind = params.get("module_kind")
    mods = scan_repo_blocks()
    out = []
    for m in mods:
        if kind and m.get("module_kind") != kind:
            continue
        hay = " ".join(filter(None, [m.get("module_name"), m.get("summary"), m.get("path"), m.get("id")])).lower()
        if not q or q in hay:
            out.append({
                "module_name": m.get("module_name"), "module_kind": m.get("module_kind"),
                "summary": m.get("summary"), "path": m.get("path"),
                "id": m.get("id"), "owner": m.get("owner"),
            })
    return {"count": len(out), "modules": out[:50]}


async def _vault_get_key(*, user: dict, params: dict) -> dict:
    """Return the metadata for a key by name (NEVER returns the plaintext).

    This tool intentionally returns only metadata. A separate /api/custom-keys/{id}/reveal
    endpoint serves the plaintext under direct user authority — agents may not
    self-serve plaintext credentials. Returns {name, kind, label, preview_tail,
    rotated_count}.
    """
    from db import custom_keys_col
    name = params.get("name")
    rec = await custom_keys_col.find_one({"user_id": user["id"], "name": name})
    if not rec:
        return {"found": False}
    return {
        "found": True,
        "name": rec["name"], "kind": rec.get("kind"), "label": rec.get("label"),
        "preview_tail": rec.get("preview_tail"), "rotated_count": rec.get("rotated_count", 0),
    }


async def _fetch_url(*, user: dict, params: dict) -> dict:
    """GET a URL. Returns {status, headers, text} (text truncated to 16 KiB).

    Redirects are followed manually so the SSRF guard runs on every hop — an
    open redirect to a loopback/metadata address is rejected mid-chain.
    """
    url = params["url"]
    timeout = float(params.get("timeout", 10))
    max_redirects = 5
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as cli:
        for _ in range(max_redirects + 1):
            await _assert_public_url(url)
            r = await cli.get(url)
            if r.is_redirect and r.headers.get("location"):
                url = str(httpx.URL(r.url).join(r.headers["location"]))
                continue
            text = r.text[:16384]
            return {
                "status": r.status_code,
                "headers": {k.lower(): v for k, v in r.headers.items() if k.lower() in ("content-type", "etag", "last-modified")},
                "text": text,
                "truncated": len(r.text) > 16384,
            }
    raise ToolError("fetch_url: too many redirects")


async def _web_search(*, user: dict, params: dict) -> dict:
    """Minimal DuckDuckGo HTML proxy search — no API key required.

    Returns the first 8 results: {title, url, snippet}. Best effort —
    will return an empty list rather than raise on parse failures.
    """
    import re, html
    q = params["query"]
    async with httpx.AsyncClient(timeout=15, follow_redirects=True,
                                 headers={"User-Agent": "Mozilla/5.0 (compatible; a0p-agent/0.1)"}) as cli:
        r = await cli.post("https://html.duckduckgo.com/html/", data={"q": q})
    body = r.text
    results: list[dict[str, str]] = []
    # Look for the standard DDG result anchor.
    pattern = re.compile(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>.*?<a[^>]+class="result__snippet"[^>]*>(.*?)</a>', re.DOTALL)
    for m in pattern.finditer(body):
        url, title_html, snippet_html = m.group(1), m.group(2), m.group(3)
        title = re.sub(r"<[^>]+>", "", title_html)
        snippet = re.sub(r"<[^>]+>", "", snippet_html)
        results.append({"title": html.unescape(title).strip(), "url": url, "snippet": html.unescape(snippet).strip()})
        if len(results) >= 8:
            break
    return {"query": q, "results": results}


def register_builtins() -> list[Tool]:
    """Register the canonical four native tools. Idempotent."""
    tools = [
        Tool(name="living_spec_lookup", kind=TOOL_KIND_NATIVE,
             description="Search the live msdmd doc-as-code blocks by name / summary / path / id.",
             input_schema={
                 "type": "object",
                 "properties": {"query": {"type": "string"},
                                "module_kind": {"type": "string"}},
                 "required": [],
             },
             fn=_living_spec_lookup, source="native", tags=["docs", "introspection"]),
        Tool(name="vault_get_key", kind=TOOL_KIND_NATIVE,
             description="Return metadata for a developer-keys vault entry by name (NEVER the plaintext).",
             input_schema={"type": "object",
                           "properties": {"name": {"type": "string"}},
                           "required": ["name"]},
             fn=_vault_get_key, source="native", tags=["secrets", "introspection"]),
        Tool(name="fetch_url", kind=TOOL_KIND_NATIVE,
             description="HTTP GET a URL and return the first 16KiB of body text + a few headers.",
             input_schema={"type": "object",
                           "properties": {"url": {"type": "string"},
                                          "timeout": {"type": "number"}},
                           "required": ["url"]},
             fn=_fetch_url, source="native", tags=["network", "scrape"]),
        Tool(name="web_search", kind=TOOL_KIND_NATIVE,
             description="DuckDuckGo HTML search — returns title/url/snippet for the top 8 results.",
             input_schema={"type": "object",
                           "properties": {"query": {"type": "string"}},
                           "required": ["query"]},
             fn=_web_search, source="native", tags=["network", "search"]),
    ]
    return [register(t) for t in tools]


__all__ = ["register_builtins"]
# ratios: loc_comments=138:74 imports_exports=11:2 calls_definitions=48:6
