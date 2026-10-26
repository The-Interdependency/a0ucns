# ratios: loc_comments=4:47 imports_exports=3:1 calls_definitions=0:0
# === MODULE_BUILD ===
# id: pcea_pkg
#   module_name: pcea
#   module_kind: engine
#   summary: PCEA — prime-circular bijective base encryption over the first 53 primes, keyed by the previous state (the 'this-state / last-state' cross-cut); the substrate that binds one inference tick to the next and seeds the decoder's deterministic generation
#   owner: a0p maintainer
#   public_surface: encrypt_state, decrypt_state, PCEAInstance, PRIME_CIRCLE
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: a0p_skills.contracts.pcea_round_trip_53
#   rollout: default_enabled
#   rollback: remove subpackage; no API surface impact
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: pcea_pkg_boundaries
#   summary: prime-circular bijective base encryption over first 53 primes (this state / last state)
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: pcea_pkg
#   summary: prime-circular bijective base encryption over first 53 primes (this state / last state)
#   exposes: encrypt_state, decrypt_state, PCEAInstance, PRIME_CIRCLE
#   boundaries: auth:none, storage:none, network:none, user_data:none
#   owner: a0p maintainer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: pcea_round_trip_53
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.pcea_round_trip_53
# === END CONTRACTS ===
"""
PCEA — Prime Circular Encryption Algorithm.

Built from spec at github.com/The-Interdependency/PCEA.
Pure-Python, zero-dependency. Bijective base-p encoding cycling over
the first 53 primes, additive shift keyed by the previous state.

"""
from .primes import PRIME_CIRCLE
from .cipher import encrypt_state, decrypt_state
from .instance import PCEAInstance

__all__ = ["PRIME_CIRCLE", "encrypt_state", "decrypt_state", "PCEAInstance"]
# ratios: loc_comments=4:47 imports_exports=3:1 calls_definitions=0:0
