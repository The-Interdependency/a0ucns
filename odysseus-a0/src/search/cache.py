# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 3:36
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 2:0
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 0:0
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
# === MODULE_BUILD ===
# id: cache
#   module_name: cache
#   module_kind: hmmm
#   summary: Compatibility wrapper for the canonical services.search.cache module.
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
# id: cache_boundaries
#   summary: Compatibility wrapper for the canonical services.search.cache module.
#   auth_boundary: hmmm
#   storage_boundary: hmmm
#   network_boundary: hmmm
#   user_data_boundary: hmmm
#   admin_only: hmmm
#   owner: hmmm
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: cache
#   summary: Compatibility wrapper for the canonical services.search.cache module.
#   exposes: none
# === END CAPABILITIES ===
"""Compatibility wrapper for the canonical services.search.cache module.

``src.search.cache`` stays importable for older agent/deep-research code, but the
implementation now lives in ``services.search.cache`` so the two cannot drift.
"""

import sys

from services.search import cache as _cache

sys.modules[__name__] = _cache
# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 3:36
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 2:0
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 0:0
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
