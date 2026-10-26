# ratios: loc_comments=3:42 imports_exports=2:1 calls_definitions=0:0
# === MODULE_BUILD ===
# id: agents_pkg
#   module_name: agents
#   module_kind: service
#   summary: per-agent CRUD; semi-permanent character-sheet-bound instances; each owns Φ/Ψ/Ω/MemL/MemS + per-instance ZFAE weight bank + archive
#   owner: Erin Spencer
#   public_surface: AgentInstance, CharacterSheet, AgentMode, PXResolution, AgentStore, ALL_MODES
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: write
#   network_boundary: internal
#   user_data_boundary: write
#   admin_only: false
#   tests: a0p_skills.contracts.agent_instance_full_crud_holds
#   rollout: default_enabled
#   rollback: remove /api/instances/* routes; agents preserved on disk
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: agents_pkg_boundaries
#   summary: per-agent CRUD; semi-permanent character-sheet-bound instances; each owns Φ/Ψ/Ω/MemL/MemS + per-instance ZFAE weight bank + archive
#   auth_boundary: none
#   storage_boundary: write
#   network_boundary: internal
#   user_data_boundary: write
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: agents_pkg
#   summary: per-agent CRUD; semi-permanent character-sheet-bound instances; each owns Φ/Ψ/Ω/MemL/MemS + per-instance ZFAE weight bank + archive
#   exposes: AgentInstance, CharacterSheet, AgentMode, PXResolution, AgentStore, ALL_MODES
#   boundaries: auth:none, storage:write, network:internal, user_data:write
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: agent_instance_full_crud
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.agent_instance_full_crud_holds
# === END CONTRACTS ===
"""Agents package — persistent character-sheet-bound instances."""
from .schema import AgentInstance, CharacterSheet, AgentMode, PXResolution, ALL_MODES
from .store import AgentStore

__all__ = ["AgentInstance", "CharacterSheet", "AgentMode", "PXResolution", "AgentStore", "ALL_MODES"]
# ratios: loc_comments=3:42 imports_exports=2:1 calls_definitions=0:0
