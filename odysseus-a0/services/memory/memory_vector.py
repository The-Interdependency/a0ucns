# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 2:33
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 1:1
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 0:0
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
# === MODULE_BUILD ===
# id: memory_vector
#   module_name: memory_vector
#   module_kind: service
#   summary: Compatibility import for the canonical memory vector store.
#   owner: hmmm
#   public_surface: none
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
# id: memory_vector_boundaries
#   summary: Compatibility import for the canonical memory vector store.
#   auth_boundary: hmmm
#   storage_boundary: hmmm
#   network_boundary: hmmm
#   user_data_boundary: hmmm
#   admin_only: hmmm
#   owner: hmmm
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: memory_vector
#   summary: Compatibility import for the canonical memory vector store.
#   exposes: none
# === END CAPABILITIES ===
"""Compatibility import for the canonical memory vector store."""

from src.memory_vector import MemoryVectorStore

__all__ = ["MemoryVectorStore"]
# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 2:33
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 1:1
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 0:0
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
