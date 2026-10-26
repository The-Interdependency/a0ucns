# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 3:37
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
# id: analytics
#   module_name: analytics
#   module_kind: hmmm
#   summary: Compatibility re-export shim for the live analytics module.
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
# id: analytics_boundaries
#   summary: Compatibility re-export shim for the live analytics module.
#   auth_boundary: hmmm
#   storage_boundary: hmmm
#   network_boundary: hmmm
#   user_data_boundary: hmmm
#   admin_only: hmmm
#   owner: hmmm
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: analytics
#   summary: Compatibility re-export shim for the live analytics module.
#   exposes: none
# === END CAPABILITIES ===
"""Compatibility re-export shim for the live analytics module.

The real implementation lives in :mod:`services.search.analytics`, which is
what the search runtime imports. Alias this module to that implementation so
mutable module state such as ``ANALYTICS_FILE`` cannot drift out of sync.
"""

import sys

from services.search import analytics as _analytics

sys.modules[__name__] = _analytics
# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 3:37
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
