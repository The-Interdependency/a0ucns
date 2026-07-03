# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 3:38
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 1:1
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 1:1
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
# === MODULE_BUILD ===
# id: task_endpoint
#   module_name: task_endpoint
#   module_kind: hmmm
#   summary: Shared resolver for background-task AI endpoint (auto-naming, memory, sorting).
#   owner: hmmm
#   public_surface: resolve_task_endpoint
#   internal_surface: none
#   auth_boundary: hmmm
#   storage_boundary: hmmm
#   network_boundary: hmmm
#   user_data_boundary: hmmm
#   admin_only: hmmm
#   tests: hmmm
#   rollout: hmmm
#   rollback: hmmm
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: task_endpoint_boundaries
#   summary: Shared resolver for background-task AI endpoint (auto-naming, memory, sorting).
#   auth_boundary: hmmm
#   storage_boundary: hmmm
#   network_boundary: hmmm
#   user_data_boundary: hmmm
#   admin_only: hmmm
#   owner: hmmm
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: task_endpoint
#   summary: Shared resolver for background-task AI endpoint (auto-naming, memory, sorting).
#   exposes: resolve_task_endpoint
# === END CAPABILITIES ===
"""Shared resolver for background-task AI endpoint (auto-naming, memory, sorting)."""

from src.endpoint_resolver import resolve_endpoint


def resolve_task_endpoint(fallback_url=None, fallback_model=None, fallback_headers=None, owner=None):
    """Return (endpoint_url, model, headers) for background tasks.

    Reads task_endpoint_id / task_model from admin settings.
    Falls back to the provided values when the setting is empty or the
    endpoint cannot be resolved.
    """
    return resolve_endpoint("task", fallback_url, fallback_model, fallback_headers, owner=owner)
# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 3:38
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 1:1
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 1:1
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
