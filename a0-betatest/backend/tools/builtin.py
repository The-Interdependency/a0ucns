# ratios: loc_comments=94:57 imports_exports=7:2 calls_definitions=26:5
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
import httpx
from typing import Any

from .registry import Tool, register, TOOL_KIND_NATIVE


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
    """GET a URL. Returns {status, headers, text} (text truncated to 16 KiB)."""
    url = params["url"]
    timeout = float(params.get("timeout", 10))
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as cli:
        r = await cli.get(url)
        text = r.text[:16384]
        return {
            "status": r.status_code,
            "headers": {k.lower(): v for k, v in r.headers.items() if k.lower() in ("content-type", "etag", "last-modified")},
            "text": text,
            "truncated": len(r.text) > 16384,
        }


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
# ratios: loc_comments=94:57 imports_exports=7:2 calls_definitions=26:5
