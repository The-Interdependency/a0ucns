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
# id: msdmd_pkg
#   module_name: _msdmd
#   module_kind: skill
#   summary: vendored msdmd parser package (parse_text / parse_file / walk_tree / marker_for)
#   owner: hmmm
#   public_surface: parse_text, parse_file, walk_tree, marker_for, parse, walk
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: read
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: hmmm
#   rollout: default_enabled
#   rollback: remove interdependent_lib/_msdmd/ from the tree
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: msdmd_pkg_boundaries
#   summary: vendored msdmd parser package
#   auth_boundary: none
#   storage_boundary: read
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: hmmm
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: msdmd_pkg
#   summary: vendored msdmd parser package
#   exposes: parse_text, parse_file, walk_tree, marker_for
# === END CAPABILITIES ===
"""msdmd — Module Self-Declared Metadata in Markdown (vendored parser only)."""
from .parser import parse_text, parse_file, walk_tree, marker_for, parse, walk

__all__ = ["parse_text", "parse_file", "walk_tree", "marker_for", "parse", "walk"]
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
