# ratios: loc_comments=37:56 imports_exports=3:3 calls_definitions=19:2
# === MODULE_BUILD ===
# id: zfae_native_tools
#   module_name: native_tools
#   module_kind: engine
#   summary: deterministic native tool-use — maps a raw prompt to at most one built-in tool call (fetch_url / web_search / living_spec_lookup) using pure rule-based detection so the a0(zfae) native engine can trigger a tool mid-thought without any LLM; the selection is reproducible and the result is summarised into a compact deterministic line folded back into the native reply
#   owner: Erin Spencer
#   public_surface: select_native_tool, summarize_tool_result, NATIVE_TOOL_NAMES
#   internal_surface: _URL_RE, _SEARCH_HEADS, _SPEC_WORDS
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: a0p_skills.contracts.zfae_native_tool_selection_holds
#   rollout: default_enabled
#   rollback: revert; native engine never triggers tools
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: zfae_native_tools_boundaries
#   summary: pure deterministic tool selection from a raw prompt; no IO, no LLM
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: zfae_native_tools
#   summary: deterministic native tool selection + result summary
#   exposes: select_native_tool, summarize_tool_result, NATIVE_TOOL_NAMES
#   boundaries: auth:none, storage:none, network:none, user_data:read
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: zfae_native_tool_selection
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.zfae_native_tool_selection_holds
# === END CONTRACTS ===
"""Deterministic native tool-use for a0(zfae).

The native engine has no LLM to "decide" to call a tool, so the decision is
made by a pure rule-based selector over the raw prompt. At most one tool is
chosen per turn, fully reproducibly:

  - a URL in the prompt           → fetch_url
  - a search/lookup/find request  → web_search
  - a spec/module/contract query  → living_spec_lookup
  - otherwise                     → no tool
"""
from __future__ import annotations
import re
from typing import Optional

NATIVE_TOOL_NAMES: tuple[str, ...] = ("fetch_url", "web_search", "living_spec_lookup")

_URL_RE = re.compile(r"https?://[^\s)>\]]+")
_SEARCH_HEADS = ("search", "look up", "lookup", "find", "google", "web search")
_SPEC_WORDS = ("living spec", "module_build", "module build", "msdmd", "contract", "spec for", "module ")


def select_native_tool(raw_prompt: str) -> Optional[dict]:
    """Deterministically pick at most one built-in tool for `raw_prompt`.

    Returns ``{"name": str, "params": dict}`` or ``None``. Priority order is
    fixed: URL → spec query → search request.
    """
    text = (raw_prompt or "").strip()
    if not text:
        return None
    low = text.lower()

    m = _URL_RE.search(text)
    if m:
        return {"name": "fetch_url", "params": {"url": m.group(0)}}

    if any(w in low for w in _SPEC_WORDS):
        # Extract a compact query: drop common stopwords, keep salient tokens.
        q = re.sub(r"\b(the|a|an|of|for|please|show|me|what|is|are|in|living|spec)\b", " ", low)
        q = re.sub(r"\s+", " ", q).strip()
        return {"name": "living_spec_lookup", "params": {"query": q[:80]}}

    if any(low.startswith(h) or f" {h} " in f" {low} " for h in _SEARCH_HEADS):
        return {"name": "web_search", "params": {"query": text[:200]}}

    return None


def summarize_tool_result(name: str, result) -> str:
    """A compact, deterministic one-line summary of a tool result for the native reply."""
    if not isinstance(result, dict):
        return f"[tool:{name}] {str(result)[:160]}"
    if name == "fetch_url":
        return f"[tool:fetch_url] status {result.get('status')} · {len(str(result.get('text', '')))} bytes"
    if name == "web_search":
        results = result.get("results") or []
        top = results[0]["title"] if results and isinstance(results[0], dict) else "(no results)"
        return f"[tool:web_search] {len(results)} hits · top: {top[:90]}"
    if name == "living_spec_lookup":
        return f"[tool:living_spec_lookup] {result.get('count', 0)} modules matched"
    if result.get("error"):
        return f"[tool:{name}] error: {str(result['error'])[:120]}"
    return f"[tool:{name}] {str(result)[:160]}"


__all__ = ["select_native_tool", "summarize_tool_result", "NATIVE_TOOL_NAMES"]
# ratios: loc_comments=37:56 imports_exports=3:3 calls_definitions=19:2
