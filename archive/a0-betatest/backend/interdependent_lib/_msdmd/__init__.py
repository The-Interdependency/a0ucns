# ratios: loc_comments=3:41 imports_exports=2:1 calls_definitions=0:0
# === MODULE_BUILD ===
# id: msdmd_pkg
#   module_name: _msdmd
#   module_kind: skill
#   summary: this project's msdmd application — parser + back-compat runner (canonical executors live in a0p_skills)
#   owner: a0p maintainer
#   public_surface: parse, walk, report, walk_tree, parse_text, parse_file
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: read
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: hmmm
#   rollout: default_enabled
#   rollback: remove imports from server.py and a0p_skills
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: msdmd_pkg_boundaries
#   summary: this project's msdmd application — parser + back-compat runner (canonical executors live in a0p_skills)
#   auth_boundary: none
#   storage_boundary: read
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: msdmd_pkg
#   summary: this project's msdmd application — parser, runner, coverage report
#   exposes: parse, walk, report
#   stability: stable
# === END CAPABILITIES ===
"""msdmd — Module Self-Declared Metadata in Markdown (this project's app)."""
from .parser import parse
from .runner import walk, report

__all__ = ["parse", "walk", "report"]

# === CONTRACTS ===
# id: msdmd_pkg_loads
#   given: module declares its msdmd canon
#   then: the module imports cleanly under the current interpreter
#   class: integration
#   call: a0p_skills.contracts.module_imports_cleanly_holds
# === END CONTRACTS ===
# ratios: loc_comments=3:41 imports_exports=2:1 calls_definitions=0:0
