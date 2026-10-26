# ratios: loc_comments=116:64 imports_exports=12:2 calls_definitions=26:2
# === MODULE_BUILD ===
# id: tools_gated_invoke
#   module_name: gated_invoke
#   module_kind: engine
#   summary: per-tool-call sentinel gate — evaluates the 13 sentinels against the tool name + serialized params, halts on any flag (creates a PendingOverride and emits zfae_override_created), only proceeds when no flag (or when caller supplied an approved override_id); emits zfae_tool_call + zfae_tool_result FIQ events on every invocation
#   owner: Erin Spencer
#   public_surface: gated_invoke
#   internal_surface: _dispatch
#   auth_boundary: bearer
#   storage_boundary: write
#   network_boundary: external
#   user_data_boundary: write
#   admin_only: false
#   tests: a0p_skills.contracts.tools_gated_invoke_halts_on_cliff_holds
#   rollout: default_enabled
#   rollback: revert; tools bypass the sentinel gate (UNSAFE)
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: tools_gated_invoke_boundaries
#   summary: sentinel gate + dispatch for one tool call
#   auth_boundary: bearer
#   storage_boundary: write
#   network_boundary: external
#   user_data_boundary: write
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: tools_gated_invoke
#   summary: sentinel-gated tool invocation
#   exposes: gated_invoke
#   boundaries: auth:bearer, storage:write, network:external, user_data:write
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: tools_gated_invoke_halts_on_cliff
#   given: a tool invocation whose params contain a canonical S4 cliff marker
#   then: gated_invoke raises ToolError(halt=True) with a pending override_id
#   class: correctness
#   call: a0p_skills.contracts.tools_gated_invoke_halts_on_cliff_holds
# === END CONTRACTS ===
"""Sentinel-gated tool invocation pipeline."""
from __future__ import annotations
import asyncio
import inspect
import json
from typing import Any, Optional

from interdependent_lib.zfae.sentinel_eval import evaluate as evaluate_sentinels, EventContext
from interdependent_lib.zfae import overrides as zfae_overrides
from interdependent_lib.zfae import fiq_emit

from .registry import Tool, ToolError, TOOL_KIND_NATIVE, TOOL_KIND_WEBHOOK, TOOL_KIND_MCP, TOOL_KIND_ODYSSEUS


async def _dispatch(tool: Tool, params: dict, user: dict) -> Any:
    """Route the actual call to the right backend by Tool.kind."""
    if tool.kind == TOOL_KIND_NATIVE:
        if tool.fn is None:
            raise ToolError(f"native tool {tool.name!r} has no fn bound")
        result = tool.fn(user=user, params=params)
        if inspect.isawaitable(result):
            return await result
        return result
    if tool.kind == TOOL_KIND_WEBHOOK:
        from . import webhook
        return await webhook.invoke(tool, params, user=user)
    if tool.kind == TOOL_KIND_MCP:
        from . import mcp_relay
        return await mcp_relay.invoke(tool, params, user=user)
    if tool.kind == TOOL_KIND_ODYSSEUS:
        from . import odysseus_relay
        return await odysseus_relay.invoke(tool, params, user=user)
    raise ToolError(f"unknown tool kind {tool.kind!r}")


async def gated_invoke(
    tool: Tool,
    params: dict,
    *,
    user: dict,
    sentinel_modes: Optional[dict] = None,
    sentinel_weights: Optional[dict] = None,
    pending_overrides_col=None,
    fiq_audit_col=None,
    override_id: Optional[str] = None,
) -> Any:
    """Run the 13-sentinel gate, then dispatch.

    Returns the tool's result on success. Raises ``ToolError(halt=True,
    override_id=...)`` if the gate halts and no approved override_id was
    supplied. Raises ``ToolError`` for any tool-side failure.
    """
    agent_id = user.get("id") or "local"
    user_id = agent_id

    # Build the EventContext from the tool name + serialized params (so a
    # cliff marker in any param string still trips S4 / S12).
    serialized = f"{tool.name} {json.dumps(params, sort_keys=True, default=str)}"
    ctx = EventContext(
        kind="tool_call",
        agent_id=agent_id, user_id=user_id,
        raw_request={"prompt": serialized, "tool": tool.name, "params": params},
        agent_sheet_modes=sentinel_modes,
        agent_sheet_weights=sentinel_weights,
    )
    verdict = evaluate_sentinels(ctx)

    # Emit verdict provenance regardless of outcome.
    if fiq_audit_col is not None:
        try:
            await fiq_emit.emit(
                fiq_audit_col,
                event_type="zfae_sentinel_verdict",
                agent_id=agent_id, user_id=user_id,
                payload={
                    "kind": "tool_call",
                    "tool": tool.name,
                    "flagged": list(verdict.flagged_sentinels),
                    "blocking_cliff": verdict.blocking_cliff,
                },
            )
        except Exception:
            pass

    if verdict.requires_override:
        # An override_id lifts the halt ONLY when it names a real, APPROVED
        # tool_call override for THIS exact tool + params (mirrors and tightens
        # ZFAERuntime._gate). Binding to the exact action stops an approval for
        # one call being replayed to resume a different flagged tool.
        existing = None
        if override_id and pending_overrides_col is not None:
            existing = await zfae_overrides.get(pending_overrides_col, override_id)
        req = (existing.raw_request or {}) if existing is not None else {}
        matches_this_call = (
            existing is not None
            and existing.agent_id == agent_id
            and existing.event_kind == "tool_call"
            and req.get("tool") == tool.name
            and json.dumps(req.get("params"), sort_keys=True, default=str)
            == json.dumps(params, sort_keys=True, default=str)
        )
        if not (matches_this_call and existing.status == "approved"):
            reuse_id = None
            rec = None
            if matches_this_call and existing.status == "pending":
                # Already a pending override for this exact call — reuse it so
                # the client re-approves the same record instead of piling up
                # duplicates on retry.
                reuse_id = existing.id
            elif pending_overrides_col is not None:
                # No usable override: none supplied, or the supplied id is for a
                # different action (e.g. a chat-level override forwarded into a
                # tool call that itself trips a sentinel). Mint a fresh pending
                # tool override so the client always has one to approve — never
                # halt with override_id=None here.
                reasons = {v.name: v.reason for v in verdict.verdicts if v.flagged}
                rec = await zfae_overrides.create_override(
                    pending_overrides_col,
                    agent_id=agent_id, user_id=user_id, event_kind="tool_call",
                    raw_request={"tool": tool.name, "params": params},
                    flagged_sentinels=list(verdict.flagged_sentinels),
                    reasons=reasons,
                    verdict_vector=list(verdict.vector),
                    disabled_sentinels=list(verdict.disabled_sentinels),
                    blocking_cliff=bool(verdict.blocking_cliff),
                )
            raise ToolError(
                f"sentinels halted tool {tool.name!r}",
                halt=True,
                override_id=(reuse_id or (rec.id if rec else None)),
                sentinel_verdict={
                    "flagged_sentinels": list(verdict.flagged_sentinels),
                    "blocking_cliff": verdict.blocking_cliff,
                    "vector": list(verdict.vector),
                },
            )

    # Emit invocation start (audit trail).
    if fiq_audit_col is not None:
        try:
            await fiq_emit.emit(
                fiq_audit_col,
                event_type="zfae_chat_reply",   # piggyback existing chat-event type
                agent_id=agent_id, user_id=user_id,
                payload={"kind": "tool_call", "tool": tool.name, "params_summary": list(params.keys())},
            )
        except Exception:
            pass

    return await _dispatch(tool, params, user)


__all__ = ["gated_invoke"]
# ratios: loc_comments=116:64 imports_exports=12:2 calls_definitions=26:2
