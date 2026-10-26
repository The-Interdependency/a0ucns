# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 7:37
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 1:0
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 0:0
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
# === MODULE_BUILD ===
# id: ranking
#   module_name: ranking
#   module_kind: hmmm
#   summary: Compatibility re-export shim for the live ranking module.
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
# id: ranking_boundaries
#   summary: Compatibility re-export shim for the live ranking module.
#   auth_boundary: hmmm
#   storage_boundary: hmmm
#   network_boundary: hmmm
#   user_data_boundary: hmmm
#   admin_only: hmmm
#   owner: hmmm
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: ranking
#   summary: Compatibility re-export shim for the live ranking module.
#   exposes: none
# === END CAPABILITIES ===
"""Compatibility re-export shim for the live ranking module.

The real implementation lives in :mod:`services.search.ranking`, which is what
the search runtime (services/search/core.py) imports. This module used to hold a
parallel copy; it now re-exports so the two cannot drift out of sync again.
"""

from services.search.ranking import (  # noqa: F401
    _AGE_FORMATS,
    _SPORTS_HINT_RE,
    _utcnow_naive,
    rank_search_results,
    recency_score,
)
# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 7:37
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 1:0
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 0:0
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
