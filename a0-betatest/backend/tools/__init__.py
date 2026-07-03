# ratios: loc_comments=10:43 imports_exports=2:1 calls_definitions=1:0
# === MODULE_BUILD ===
# id: tools_pkg
#   module_name: tools
#   module_kind: service
#   summary: tools subpackage entry — re-exports the registry public surface and triggers register_builtins() so native tools are available immediately on import
#   owner: Erin Spencer
#   public_surface: Tool, ToolError, register, lookup, list_tools, invoke, register_builtins, TOOL_KIND_NATIVE, TOOL_KIND_WEBHOOK, TOOL_KIND_MCP
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: a0p_skills.contracts.tools_pkg_imports_holds
#   rollout: default_enabled
#   rollback: revert; tools.* re-exports unavailable
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: tools_pkg_boundaries
#   summary: pure re-export shim
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: tools_pkg
#   summary: pkg entry point
#   exposes: re-exports
#   boundaries: auth:none, storage:none, network:none, user_data:read
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: tools_pkg_imports
#   given: the tools package is imported
#   then: register_builtins() has populated the registry with at least 4 native tools
#   class: integration
#   call: a0p_skills.contracts.tools_pkg_imports_holds
# === END CONTRACTS ===
"""Tools subpackage — registers built-ins on import."""
from .registry import (
    Tool, ToolError, register, lookup, list_tools, invoke,
    TOOL_KIND_NATIVE, TOOL_KIND_WEBHOOK, TOOL_KIND_MCP,
)
from .builtin import register_builtins

# Idempotent — safe to call on every import.
register_builtins()

__all__ = [
    "Tool", "ToolError", "register", "lookup", "list_tools", "invoke",
    "register_builtins", "TOOL_KIND_NATIVE", "TOOL_KIND_WEBHOOK", "TOOL_KIND_MCP",
]
# ratios: loc_comments=10:43 imports_exports=2:1 calls_definitions=1:0
