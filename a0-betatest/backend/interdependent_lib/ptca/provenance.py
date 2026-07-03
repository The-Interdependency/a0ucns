# ratios: loc_comments=10:43 imports_exports=2:1 calls_definitions=2:1
# === MODULE_BUILD ===
# id: ptca_provenance
#   module_name: provenance
#   module_kind: engine
#   summary: deterministic SHA-256 provenance hashing for tensor ops + lineage chains
#   owner: a0p maintainer
#   public_surface: hash_state
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: hmmm
#   rollout: default_enabled
#   rollback: revert file from git
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: ptca_provenance_boundaries
#   summary: deterministic SHA-256 provenance hashing for tensor ops + lineage chains
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: ptca_provenance
#   summary: deterministic SHA-256 provenance hashing for tensor ops + lineage chains
#   exposes: hash_state
#   boundaries: auth:none, storage:none, network:none, user_data:none
#   owner: a0p maintainer
# === END CAPABILITIES ===
"""Provenance hashing — deterministic SHA-256 over tensor state + op metadata."""
import hashlib
import json


def hash_state(state, op: str = "", parents: list[str] | None = None) -> str:
    """Return a hex digest binding the state (any json-serializable) to an op + parents."""
    payload = {
        "op": op,
        "parents": parents or [],
        "state": state,
    }
    blob = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()

# === CONTRACTS ===
# id: ptca_provenance_loads
#   given: module declares its msdmd canon
#   then: the module imports cleanly under the current interpreter
#   class: integration
#   call: a0p_skills.contracts.module_imports_cleanly_holds
# === END CONTRACTS ===
# ratios: loc_comments=10:43 imports_exports=2:1 calls_definitions=2:1
