# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 1:39
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 0:1
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 0:0
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
# === MODULE_BUILD ===
# id: interdependent_lib_pkg
#   module_name: interdependent_lib
#   module_kind: skill
#   summary: minimal vendored namespace exposing the msdmd parser to the a0p_skills runners
#   owner: hmmm
#   public_surface: none
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: hmmm
#   rollout: default_enabled
#   rollback: remove interdependent_lib/ and a0p_skills/ from the tree
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: interdependent_lib_pkg_boundaries
#   summary: minimal vendored namespace exposing the msdmd parser to the a0p_skills runners
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: hmmm
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: interdependent_lib_pkg
#   summary: minimal vendored namespace exposing the msdmd parser
#   exposes: none
# === END CAPABILITIES ===
"""interdependent_lib — minimal vendored namespace.

Only the ``_msdmd`` parser is vendored into odysseus-a0 (the msdmd toolchain
the a0p_skills runners depend on). The full interdependent_lib (pcea/ptca/
pcna/zfae) is *not* part of this fork.

Synced from The-Interdependency/a0-betatest backend; parser itself is
upstream skill-lib (msdmd/parsers/universal.py).
"""
__all__: list[str] = []
# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 1:39
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 0:1
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 0:0
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
