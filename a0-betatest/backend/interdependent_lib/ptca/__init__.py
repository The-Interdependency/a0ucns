# ratios: loc_comments=15:47 imports_exports=6:1 calls_definitions=0:0
# === MODULE_BUILD ===
# id: ptca_pkg
#   module_name: ptca
#   module_kind: engine
#   summary: seeds-layer wrapper — re-exports current PTCAInstance plus prime utilities (canon stratified prime_core rebuild pending)
#   owner: a0p maintainer
#   public_surface: PTCAInstance, PrimeTensor, SentinelChannel, hash_state, exchange, first_n_primes, PRIMES_FIRST_N
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: a0p_skills.contracts.ptca_canon_shape_holds
#   rollout: default_enabled
#   rollback: revert subpackage from git
#   unresolved: 9-axis from design conversation not present in upstream prime_core; awaiting clarification
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: ptca_pkg_boundaries
#   summary: seeds-layer wrapper — re-exports current PTCAInstance plus prime utilities (canon stratified prime_core rebuild pending)
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: ptca_pkg
#   summary: seeds-layer wrapper — re-exports current PTCAInstance plus prime utilities (canon stratified prime_core rebuild pending)
#   exposes: PTCAInstance, PrimeTensor, SentinelChannel, hash_state, exchange, first_n_primes, PRIMES_FIRST_N
#   boundaries: auth:none, storage:none, network:none, user_data:none
#   owner: a0p maintainer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: ptca_canon_shape
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.ptca_canon_shape_holds
# === END CONTRACTS ===
"""
PTCA — Prime Tensor Circular Architecture.

Sentinel channels, prime-node tensors, provenance hashing, exchange mechanics.
Pure Python (uses python list-of-lists for tensor shape [N, 4, 7, 7]).

"""
from .primes import PRIMES_FIRST_N, first_n_primes
from .tensor import PrimeTensor
from .sentinels import SentinelChannel
from .provenance import hash_state
from .exchange import exchange
from .instance import PTCAInstance

__all__ = [
    "PRIMES_FIRST_N",
    "first_n_primes",
    "PrimeTensor",
    "SentinelChannel",
    "hash_state",
    "exchange",
    "PTCAInstance",
]
# ratios: loc_comments=15:47 imports_exports=6:1 calls_definitions=0:0
