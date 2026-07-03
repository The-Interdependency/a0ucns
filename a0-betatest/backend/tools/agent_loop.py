# ratios: loc_comments=195:62 imports_exports=4:4 calls_definitions=66:11
# === MODULE_BUILD ===
# id: tools_agent_loop
#   module_name: agent_loop
#   module_kind: engine
#   summary: provider-agnostic agentic tool-use loop over raw HTTP (BYOK) — normalizes OpenAI/xAI Chat Completions, Anthropic Messages, and Gemini generateContent function-calling into one multi-step loop; advertises tool JSON schema, detects model tool calls, runs an injected executor (sentinel-gated), threads tool results back, and loops until a final answer or max_iters; the network poster is injectable so the loop is fully unit-testable without live keys
#   owner: Erin Spencer
#   public_surface: run_tool_loop, tool_to_schema, ToolLoopHalt, MAX_ITERS_DEFAULT
#   internal_surface: _split_system, _to_provider_messages, _build_payload, _parse, _append_tool_turn, _endpoint, _httpx_poster
#   auth_boundary: bearer
#   storage_boundary: none
#   network_boundary: external
#   user_data_boundary: read
#   admin_only: false
#   tests: a0p_skills.contracts.tools_agent_loop_two_step_holds
#   rollout: default_enabled
#   rollback: revert; teacher path uses single-shot invoke (no tools)
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: tools_agent_loop_boundaries
#   summary: provider-agnostic agentic tool-use loop over raw HTTP (BYOK)
#   auth_boundary: bearer
#   storage_boundary: none
#   network_boundary: external
#   user_data_boundary: read
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: tools_agent_loop
#   summary: normalized cross-provider function-calling loop
#   exposes: run_tool_loop, tool_to_schema, ToolLoopHalt
#   boundaries: auth:bearer, storage:none, network:external, user_data:read
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: tools_agent_loop_two_step
#   given: a fake poster that returns a tool-call then a final answer for each provider
#   then: run_tool_loop executes the tool via the injected executor and returns the
#         final text plus a one-entry tool_trace
#   class: correctness
#   call: a0p_skills.contracts.tools_agent_loop_two_step_holds
# === END CONTRACTS ===
"""Provider-agnostic agentic tool-use loop (BYOK, raw HTTP).

The four supported providers expose the same conceptual loop with different
JSON shapes:

  OpenAI / xAI : messages[].tool_calls[].function{name,arguments(JSON str)}
  Anthropic    : content[]{type:tool_use, id, name, input}
  Gemini       : candidates[].content.parts[].functionCall{name,id,args}

``run_tool_loop`` normalizes all three behind one loop. The ``poster`` and
``executor`` are injected so the whole loop is deterministic + unit-testable.
"""
from __future__ import annotations
import json
from typing import Any, Awaitable, Callable, Optional

MAX_ITERS_DEFAULT: int = 4
_OPENAI_LIKE = ("openai", "xai")


class ToolLoopHalt(Exception):
    """Raised by an executor to stop the loop — a sentinel cliff halted a tool."""

    def __init__(self, override_id: Optional[str] = None, sentinel_verdict: Optional[dict] = None):
        super().__init__("tool loop halted by sentinel")
        self.override_id = override_id
        self.sentinel_verdict = sentinel_verdict


# ---- tool schema translation ----------------------------------------------

def tool_to_schema(tool: dict, provider: str) -> dict:
    """Translate a normalized tool ({name, description, input_schema}) to the
    provider's tool/function declaration shape."""
    name = tool["name"]
    desc = tool.get("description", "")
    params = tool.get("input_schema") or {"type": "object", "properties": {}}
    if provider in _OPENAI_LIKE:
        return {"type": "function", "function": {"name": name, "description": desc, "parameters": params}}
    if provider == "anthropic":
        return {"name": name, "description": desc, "input_schema": params}
    if provider == "gemini":
        return {"name": name, "description": desc, "parameters": params}
    raise ValueError(f"unknown provider {provider!r}")


# ---- endpoint + request/response normalization -----------------------------

def _endpoint(provider: str, model: str, api_key: str) -> tuple[str, dict, Optional[dict]]:
    if provider in _OPENAI_LIKE:
        base = "https://api.openai.com/v1" if provider == "openai" else "https://api.x.ai/v1"
        return (f"{base}/chat/completions",
                {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, None)
    if provider == "anthropic":
        return ("https://api.anthropic.com/v1/messages",
                {"x-api-key": api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"}, None)
    if provider == "gemini":
        return (f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                {"Content-Type": "application/json"}, {"key": api_key})
    raise ValueError(f"unknown provider {provider!r}")


def _split_system(generic: list[dict]) -> tuple[str, list[dict]]:
    sys_parts: list[str] = []
    conv: list[dict] = []
    for m in generic:
        if m.get("role") == "system":
            if m.get("content"):
                sys_parts.append(m["content"])
        else:
            conv.append({"role": m["role"], "content": m.get("content", "")})
    return "\n".join(sys_parts), conv


def _to_provider_messages(provider: str, conv: list[dict]) -> list[dict]:
    if provider in _OPENAI_LIKE:
        return list(conv)
    if provider == "anthropic":
        return [{"role": m["role"], "content": [{"type": "text", "text": m["content"]}]} for m in conv]
    if provider == "gemini":
        return [{"role": ("user" if m["role"] == "user" else "model"),
                 "parts": [{"text": m["content"]}]} for m in conv]
    raise ValueError(f"unknown provider {provider!r}")


def _build_payload(provider, model, messages, tool_schemas, system, max_tokens) -> dict:
    if provider in _OPENAI_LIKE:
        msgs = list(messages)
        if system and not any(m.get("role") == "system" for m in msgs):
            msgs = [{"role": "system", "content": system}] + msgs
        p: dict = {"model": model, "messages": msgs, "max_tokens": max_tokens}
        if tool_schemas:
            p["tools"] = tool_schemas
            p["tool_choice"] = "auto"
        return p
    if provider == "anthropic":
        p = {"model": model, "max_tokens": max_tokens, "messages": messages}
        if system:
            p["system"] = system
        if tool_schemas:
            p["tools"] = tool_schemas
        return p
    if provider == "gemini":
        p = {"contents": messages}
        if tool_schemas:
            p["tools"] = [{"functionDeclarations": tool_schemas}]
        if system:
            p["systemInstruction"] = {"parts": [{"text": system}]}
        return p
    raise ValueError(f"unknown provider {provider!r}")


def _parse(provider: str, j: dict) -> dict:
    """Normalize a provider response → {text, tool_calls:[{id,name,args}], raw, usage, error}."""
    if j.get("__error__"):
        return {"text": "", "tool_calls": [], "raw": None, "usage": {}, "error": j["__error__"]}
    if provider in _OPENAI_LIKE:
        ch = (j.get("choices") or [{}])[0]
        msg = ch.get("message") or {}
        tcs = []
        for tc in (msg.get("tool_calls") or []):
            fn = tc.get("function") or {}
            args = fn.get("arguments")
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}
            tcs.append({"id": tc.get("id") or f"call_{len(tcs)}", "name": fn.get("name"), "args": args or {}})
        u = j.get("usage") or {}
        return {"text": msg.get("content") or "", "tool_calls": tcs, "raw": msg,
                "usage": {"total": u.get("total_tokens", 0)}, "error": None}
    if provider == "anthropic":
        blocks = j.get("content") or []
        text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
        tcs = [{"id": b["id"], "name": b["name"], "args": b.get("input") or {}}
               for b in blocks if b.get("type") == "tool_use"]
        u = j.get("usage") or {}
        return {"text": text, "tool_calls": tcs, "raw": {"role": "assistant", "content": blocks},
                "usage": {"total": u.get("input_tokens", 0) + u.get("output_tokens", 0)}, "error": None}
    if provider == "gemini":
        cands = j.get("candidates") or []
        parts = ((cands[0].get("content") or {}).get("parts") or []) if cands else []
        text = "".join(p.get("text", "") for p in parts if "text" in p)
        tcs = []
        for i, p in enumerate(parts):
            fc = p.get("functionCall")
            if fc:
                tcs.append({"id": fc.get("id") or f"gem_{i}", "name": fc.get("name"), "args": fc.get("args") or {}})
        um = j.get("usageMetadata") or {}
        return {"text": text, "tool_calls": tcs, "raw": {"role": "model", "parts": parts},
                "usage": {"total": um.get("totalTokenCount", 0)}, "error": None}
    raise ValueError(f"unknown provider {provider!r}")


def _append_tool_turn(provider, messages, raw_assistant, results) -> list[dict]:
    """Thread the assistant tool-call turn + the tool results back, provider-native."""
    out = list(messages)
    out.append(raw_assistant)
    if provider in _OPENAI_LIKE:
        for r in results:
            out.append({"role": "tool", "tool_call_id": r["id"],
                        "content": json.dumps(r["result"], default=str)})
    elif provider == "anthropic":
        out.append({"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": r["id"], "content": json.dumps(r["result"], default=str)}
            for r in results]})
    elif provider == "gemini":
        out.append({"role": "user", "parts": [
            {"functionResponse": {"name": r["name"],
                                  "response": (r["result"] if isinstance(r["result"], dict) else {"result": r["result"]})}}
            for r in results]})
    return out


async def _httpx_poster(url: str, headers: dict, params: Optional[dict], payload: dict) -> dict:
    import httpx
    async with httpx.AsyncClient(timeout=120.0) as c:
        r = await c.post(url, headers=headers, params=params, json=payload)
        if r.status_code >= 400:
            return {"__error__": f"{r.status_code}: {r.text[:400]}"}
        return r.json()


# ---- the loop --------------------------------------------------------------

async def run_tool_loop(
    *,
    provider: str,
    model: str,
    api_key: str,
    generic_messages: list[dict],
    tools: list[dict],
    executor: Callable[[dict], Awaitable[Any]],
    system: str = "",
    max_iters: int = MAX_ITERS_DEFAULT,
    max_tokens: int = 1024,
    poster: Optional[Callable[..., Awaitable[dict]]] = None,
) -> dict:
    """Run the normalized agentic tool-use loop.

    Returns ``{final_text, tool_trace, usage, iterations, error, halted, override_id}``.
    """
    poster = poster or _httpx_poster
    sys_text, conv = _split_system(generic_messages)
    system_full = "\n".join([s for s in (system, sys_text) if s])
    messages = _to_provider_messages(provider, conv)
    tool_schemas = [tool_to_schema(t, provider) for t in tools] if tools else []
    url, headers, params = _endpoint(provider, model, api_key)

    tool_trace: list[dict] = []
    total_tokens = 0
    for it in range(max_iters):
        payload = _build_payload(provider, model, messages, tool_schemas, system_full, max_tokens)
        resp = await poster(url, headers, params, payload)
        parsed = _parse(provider, resp)
        total_tokens += int(parsed["usage"].get("total", 0) or 0)
        if parsed["error"]:
            return {"final_text": "", "tool_trace": tool_trace, "usage": {"total": total_tokens},
                    "iterations": it + 1, "error": parsed["error"], "halted": False, "override_id": None}
        if not parsed["tool_calls"]:
            return {"final_text": parsed["text"], "tool_trace": tool_trace,
                    "usage": {"total": total_tokens}, "iterations": it + 1,
                    "error": None, "halted": False, "override_id": None}
        results = []
        for tc in parsed["tool_calls"]:
            try:
                out = await executor(tc)
                status = "ok"
            except ToolLoopHalt as h:
                tool_trace.append({"name": tc["name"], "args": tc["args"], "status": "halted"})
                return {"final_text": "", "tool_trace": tool_trace, "usage": {"total": total_tokens},
                        "iterations": it + 1, "error": "sentinel_halt",
                        "halted": True, "override_id": h.override_id}
            except Exception as e:  # tool-side failure — feed the error back to the model
                out = {"error": str(e)}
                status = "error"
            results.append({"id": tc["id"], "name": tc["name"], "result": out})
            tool_trace.append({"name": tc["name"], "args": tc["args"], "status": status,
                               "result_preview": str(out)[:240]})
        messages = _append_tool_turn(provider, messages, parsed["raw"], results)

    return {"final_text": parsed.get("text", ""), "tool_trace": tool_trace,
            "usage": {"total": total_tokens}, "iterations": max_iters,
            "error": "max_iters_exceeded", "halted": False, "override_id": None}


__all__ = ["run_tool_loop", "tool_to_schema", "ToolLoopHalt", "MAX_ITERS_DEFAULT"]
# ratios: loc_comments=195:62 imports_exports=4:4 calls_definitions=66:11
