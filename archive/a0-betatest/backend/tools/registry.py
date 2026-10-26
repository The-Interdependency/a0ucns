# ratios: loc_comments=91:66 imports_exports=4:10 calls_definitions=23:11
# === MODULE_BUILD ===
# id: tools_registry
#   module_name: registry
#   module_kind: engine
#   summary: in-process Tool registry + invocation surface — Tool, ToolError, register, lookup, list_tools, invoke; every invocation routes through the sentinel evaluator (gated_invoke) so cliff-mode S4/S12 etc. can halt before any side effect; tools may be native (python callable), webhook (user-registered URL with HMAC), or mcp (relayed to a registered MCP server)
#   owner: Erin Spencer
#   public_surface: Tool, ToolError, register, lookup, unregister, is_global, user_tool_names, list_tools, invoke, TOOL_KIND_NATIVE, TOOL_KIND_WEBHOOK, TOOL_KIND_MCP, TOOL_KIND_ODYSSEUS
#   internal_surface: _REG, _validate_input
#   auth_boundary: bearer
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: a0p_skills.contracts.tools_registry_register_and_invoke_holds
#   rollout: default_enabled
#   rollback: revert; agents lose tool-calling surface
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: tools_registry_boundaries
#   summary: pure in-process registry; per-invocation sentinel gating delegated to gated_invoke
#   auth_boundary: bearer
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: tools_registry
#   summary: tool spec + registry + invocation entry point
#   exposes: Tool, ToolError, register, lookup, unregister, is_global, user_tool_names, list_tools, invoke, TOOL_KIND_*
#   boundaries: auth:bearer, storage:none, network:none, user_data:read
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: tools_registry_register_and_invoke
#   given: a native Tool registered and invoked through gated_invoke
#   then: the registry returns the tool by name and a valid invocation returns
#         the callable result; an invocation that trips a cliff sentinel raises
#         ToolError with halt metadata attached
#   class: correctness
#   call: a0p_skills.contracts.tools_registry_register_and_invoke_holds
# === END CONTRACTS ===
"""In-process Tool registry + invocation surface."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Optional


TOOL_KIND_NATIVE = "native"
TOOL_KIND_WEBHOOK = "webhook"
TOOL_KIND_MCP = "mcp"
TOOL_KIND_ODYSSEUS = "odysseus"


class ToolError(Exception):
    """Raised for any tool-invocation failure. Sentinel halts carry `halt=True`."""

    def __init__(self, message: str, *, halt: bool = False, override_id: Optional[str] = None,
                 sentinel_verdict: Optional[dict] = None):
        super().__init__(message)
        self.halt = halt
        self.override_id = override_id
        self.sentinel_verdict = sentinel_verdict


@dataclass
class Tool:
    """Canonical Tool spec.

    `input_schema` is JSON Schema (a dict). For native tools, `fn` is a sync
    or async callable taking ``(user, params, ctx)`` and returning a JSON-safe
    value. For webhook tools, `webhook_url` is set; native dispatch uses
    `tools.webhook.invoke`. For mcp tools, `mcp_server_id` + `remote_name` are
    set; native dispatch uses `tools.mcp_relay.invoke`.
    """
    name: str
    kind: str  # one of TOOL_KIND_*
    description: str
    input_schema: dict = field(default_factory=dict)
    fn: Optional[Callable[..., Any]] = None
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    mcp_server_id: Optional[str] = None
    remote_name: Optional[str] = None
    owner_user_id: Optional[str] = None   # None for global / built-in
    source: str = "native"                # "native" | "user" | "mcp" | "skill-lib"
    tags: list[str] = field(default_factory=list)


_REG: dict[str, Tool] = {}


def register(tool: Tool) -> Tool:
    """Idempotent registration. Overwrites any existing entry with the same name."""
    _REG[tool.name] = tool
    return tool


def lookup(name: str) -> Optional[Tool]:
    return _REG.get(name)


def unregister(name: str) -> bool:
    """Remove a tool from the in-process registry. Returns True if present."""
    return _REG.pop(name, None) is not None


def is_global(name: str) -> bool:
    """True iff a global (built-in, owner_user_id=None) tool holds this name.
    Used to stop a user tool from shadowing a built-in across the process."""
    t = _REG.get(name)
    return t is not None and t.owner_user_id is None


def user_tool_names(user_id: str) -> set[str]:
    """Names of registry entries owned by this user (for hydrate reconciliation)."""
    return {n for n, t in _REG.items() if t.owner_user_id == user_id}


def list_tools(*, user_id: Optional[str] = None, include_globals: bool = True) -> list[Tool]:
    out: list[Tool] = []
    for t in _REG.values():
        if t.owner_user_id is None:
            if include_globals:
                out.append(t)
        elif t.owner_user_id == user_id:
            out.append(t)
    return sorted(out, key=lambda t: (t.source, t.name))


def _validate_input(tool: Tool, params: dict) -> None:
    """Minimal JSON-schema validation — required keys + basic type checks.

    We intentionally don't pull in jsonschema for one-key checks; the registry
    is a thin layer and the upstream `invoke` is the only caller.
    """
    schema = tool.input_schema or {}
    required = schema.get("required") or []
    for k in required:
        if k not in params:
            raise ToolError(f"tool {tool.name!r} missing required param {k!r}")
    props = schema.get("properties") or {}
    type_map = {"string": str, "integer": int, "number": (int, float), "boolean": bool, "array": list, "object": dict}
    for k, v in params.items():
        spec = props.get(k) or {}
        expected = type_map.get(spec.get("type"))
        if expected and not isinstance(v, expected):
            raise ToolError(f"tool {tool.name!r} param {k!r} expected {spec.get('type')}, got {type(v).__name__}")


async def invoke(
    name: str,
    params: dict,
    *,
    user: dict,
    sentinel_modes: Optional[dict] = None,
    sentinel_weights: Optional[dict] = None,
    pending_overrides_col=None,
    fiq_audit_col=None,
    override_id: Optional[str] = None,
) -> Any:
    """Invoke a tool through the sentinel gate.

    Raises ToolError if the tool is unknown, params fail validation, the
    sentinel gate halts, or the tool itself fails.
    """
    tool = lookup(name)
    if tool is None:
        raise ToolError(f"unknown tool {name!r}")
    _validate_input(tool, params)

    # Lazy import to avoid a cycle (gated_invoke imports back into registry).
    from .gated_invoke import gated_invoke
    return await gated_invoke(
        tool, params, user=user,
        sentinel_modes=sentinel_modes, sentinel_weights=sentinel_weights,
        pending_overrides_col=pending_overrides_col,
        fiq_audit_col=fiq_audit_col,
        override_id=override_id,
    )


__all__ = [
    "Tool", "ToolError", "register", "lookup", "unregister", "is_global",
    "user_tool_names", "list_tools", "invoke",
    "TOOL_KIND_NATIVE", "TOOL_KIND_WEBHOOK", "TOOL_KIND_MCP", "TOOL_KIND_ODYSSEUS",
]
# ratios: loc_comments=91:66 imports_exports=4:10 calls_definitions=23:11
