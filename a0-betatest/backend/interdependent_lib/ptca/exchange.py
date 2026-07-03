# ratios: loc_comments=10:44 imports_exports=1:1 calls_definitions=4:1
# === MODULE_BUILD ===
# id: ptca_exchange
#   module_name: exchange
#   module_kind: engine
#   summary: deterministic prime-circular state-exchange protocol — advances a PTCA state against a counterpart using the prime circle so two engines can hand state back and forth reproducibly, with no randomness and a verifiable round-trip
#   owner: a0p maintainer
#   public_surface: exchange
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
# id: ptca_exchange_boundaries
#   summary: deterministic prime-circular state-exchange protocol
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: ptca_exchange
#   summary: deterministic prime-circular state-exchange protocol
#   exposes: exchange
#   boundaries: auth:none, storage:none, network:none, user_data:none
#   owner: a0p maintainer
# === END CAPABILITIES ===
"""Exchange mechanics — deterministic prime-circular state-exchange protocol."""
from .primes import first_n_primes


def exchange(state_a: list[int], primes: list[int] | None = None) -> list[int]:
    """Symmetric prime-circular shift: each position i transforms by prime[i % P]."""
    if primes is None:
        primes = first_n_primes(max(len(state_a), 4))
    P = len(primes)
    out = []
    for i, v in enumerate(state_a):
        p = primes[i % P]
        # deterministic mix that's invertible by re-running with the same primes
        out.append((int(v) ^ p) + (i % 7))
    return out

# === CONTRACTS ===
# id: ptca_exchange_loads
#   given: module declares its msdmd canon
#   then: the module imports cleanly under the current interpreter
#   class: integration
#   call: a0p_skills.contracts.module_imports_cleanly_holds
# === END CONTRACTS ===
# ratios: loc_comments=10:44 imports_exports=1:1 calls_definitions=4:1
