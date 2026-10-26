# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 12:42
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
# id: a0p_skills_pkg
#   module_name: a0p_skills
#   module_kind: skill
#   summary: vendored msdmd skill executors + the msdmd_refactor single-action orchestrator
#   owner: hmmm
#   public_surface: ratios_runner, module_build_runner, boundaries_runner, capabilities_runner, msdmd_refactor
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: write
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: hmmm
#   rollout: default_enabled
#   rollback: remove a0p_skills/ from the tree
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: a0p_skills_pkg_boundaries
#   summary: vendored msdmd skill executors + the msdmd_refactor single-action orchestrator
#   auth_boundary: none
#   storage_boundary: write
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: hmmm
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: a0p_skills_pkg
#   summary: vendored msdmd skill executors + the msdmd_refactor single-action orchestrator
#   exposes: ratios_runner, module_build_runner, boundaries_runner, capabilities_runner, msdmd_refactor
# === END CAPABILITIES ===
"""a0p_skills — vendored msdmd toolchain for odysseus-a0.

Checkers (read-only, report drift + coverage gaps):
  ratios_runner         → RATIOS   bookend recomputation
  module_build_runner   → MODULE_BUILD schema + gap report
  boundaries_runner     → BOUNDARIES schema + gap report
  capabilities_runner   → CAPABILITIES schema + gap report

Writer (the single action that sets the refactor in motion):
  msdmd_refactor        → inserts RATIOS + scaffolds MODULE_BUILD/BOUNDARIES/
                          CAPABILITIES across the tree, idempotently.
"""
from . import (
    ratios_runner,
    module_build_runner,
    boundaries_runner,
    capabilities_runner,
    msdmd_refactor,
)

__all__ = [
    "ratios_runner",
    "module_build_runner",
    "boundaries_runner",
    "capabilities_runner",
    "msdmd_refactor",
]
# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 12:42
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
