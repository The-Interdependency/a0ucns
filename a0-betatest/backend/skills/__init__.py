# ratios: loc_comments=10:42 imports_exports=2:1 calls_definitions=0:0
# === MODULE_BUILD ===
# id: skills_pkg
#   module_name: skills
#   module_kind: service
#   summary: skills subpackage entry — re-exports registry + sync helpers
#   owner: Erin Spencer
#   public_surface: Skill, SkillExistsWarning, register_skill, list_skills, get_skill, delete_skill, check_overlap, pull_from_skill_lib
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: a0p_skills.contracts.module_imports_cleanly_holds
#   rollout: default_enabled
#   rollback: revert
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: skills_pkg_boundaries
#   summary: re-export shim
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: skills_pkg
#   summary: package re-exports
#   exposes: re-exports
#   boundaries: auth:none, storage:none, network:none, user_data:read
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: skills_pkg_loads
#   given: module declares its msdmd canon
#   then: the module imports cleanly under the current interpreter
#   class: integration
#   call: a0p_skills.contracts.module_imports_cleanly_holds
# === END CONTRACTS ===
"""Skills subpackage."""
from .registry import (
    Skill, SkillExistsWarning, register_skill, list_skills, get_skill,
    delete_skill, check_overlap, tokenize_scope, tokenize_logic, OVERLAP_THRESHOLD,
)
from .sync import pull_from_skill_lib, push_to_skill_lib_stub

__all__ = [
    "Skill", "SkillExistsWarning", "register_skill", "list_skills", "get_skill",
    "delete_skill", "check_overlap", "tokenize_scope", "tokenize_logic",
    "OVERLAP_THRESHOLD", "pull_from_skill_lib", "push_to_skill_lib_stub",
]
# ratios: loc_comments=10:42 imports_exports=2:1 calls_definitions=0:0
