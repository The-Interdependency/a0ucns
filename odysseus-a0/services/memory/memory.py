# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 2:37
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
# id: memory
#   module_name: memory
#   module_kind: service
#   summary: Compatibility import for the canonical memory manager.
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
# id: memory_boundaries
#   summary: Compatibility import for the canonical memory manager.
#   auth_boundary: hmmm
#   storage_boundary: hmmm
#   network_boundary: hmmm
#   user_data_boundary: hmmm
#   admin_only: hmmm
#   owner: hmmm
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: memory
#   summary: Compatibility import for the canonical memory manager.
#   exposes: none
# === END CAPABILITIES ===
"""Compatibility import for the canonical memory manager.

Historically this package carried a second copy of ``MemoryManager``. The
application runtime instantiates ``src.memory.MemoryManager``, so keeping a
parallel implementation here risks silent drift between import paths.
"""

from src.memory import MemoryManager, get_text_similarity, tokenize

__all__ = ["MemoryManager", "get_text_similarity", "tokenize"]
# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 2:37
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
