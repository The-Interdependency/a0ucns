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
# id: providers
#   module_name: providers
#   module_kind: hmmm
#   summary: Compatibility wrapper for the canonical services.search.providers module.
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
# id: providers_boundaries
#   summary: Compatibility wrapper for the canonical services.search.providers module.
#   auth_boundary: hmmm
#   storage_boundary: hmmm
#   network_boundary: hmmm
#   user_data_boundary: hmmm
#   admin_only: hmmm
#   owner: hmmm
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: providers
#   summary: Compatibility wrapper for the canonical services.search.providers module.
#   exposes: none
# === END CAPABILITIES ===
"""Compatibility wrapper for the canonical services.search.providers module.

Historically Odysseus carried duplicate provider implementations under both
``src.search`` and ``services.search``. Keep the old import path working, but
make provider behavior come from one source of truth.
"""

import sys

from services.search import providers as _providers

sys.modules[__name__] = _providers
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
