# ratios: loc_comments=39:57 imports_exports=2:1 calls_definitions=7:3
# === MODULE_BUILD ===
# id: ptca_constants
#   module_name: constants
#   module_kind: schema
#   summary: canon PTCA composition counts — synced from The-Interdependency/PTCA/prime_core/constants.py
#   owner: a0p maintainer
#   public_surface: SEED_COUNT, CIRCLES_PER_SEED, TENSORS_PER_CIRCLE, TENSOR_DIM, TENSOR_LEAVES, PARAM_COUNT, CIRCLE_ROUTING_STEP, SEED_ROUTING_STEP, COHERENCE_FACTOR_UNIVERSE, is_coherence_prime
#   internal_surface: _is_prime, _prime_factors
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: a0p_skills.contracts.ptca_canon_shape_holds
#   rollout: default_enabled
#   rollback: revert file from git
#   unresolved: 9-axis from design conversation; coherence-prime universe is provisional per upstream
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: ptca_constants_boundaries
#   summary: canon PTCA composition counts — synced from The-Interdependency/PTCA/prime_core/constants.py
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: ptca_constants
#   summary: canon PTCA composition counts — synced from The-Interdependency/PTCA/prime_core/constants.py
#   exposes: SEED_COUNT, CIRCLES_PER_SEED, TENSORS_PER_CIRCLE, TENSOR_DIM, TENSOR_LEAVES, PARAM_COUNT, CIRCLE_ROUTING_STEP, SEED_ROUTING_STEP, COHERENCE_FACTOR_UNIVERSE, is_coherence_prime
#   boundaries: auth:none, storage:none, network:none, user_data:none
#   owner: a0p maintainer
# === END CAPABILITIES ===
"""Frozen composition counts and the coherence-prime guard for PTCA.

Source: synced from The-Interdependency/PTCA/main/prime_core/constants.py
(commit 1ea2213, 2026-05-31). Provenance note from upstream applies:
canon source documents (canon_definitions_invariants-1.md,
consciousness_primes_prediction1.pdf) are NOT accessible — these are
the handoff's stated values, not externally-verified canon.
"""

# === CONTRACTS ===
# id: ptca_canon_shape
#   given: import interdependent_lib.ptca.constants
#   then: SEED_COUNT=157, CIRCLES_PER_SEED=7, TENSORS_PER_CIRCLE=7, TENSOR_DIM=53, TENSOR_LEAVES=7693, PARAM_COUNT=407_729
#   class: provenance
#   call: a0p_skills.contracts.ptca_canon_shape_holds
# === END CONTRACTS ===

from __future__ import annotations
from typing import List

# --- composition counts (handoff §1.1, "canon-frozen") ----------------------
SEED_COUNT: int = 157                # coherence prime, (157-1)/4 = 39 = {3,13}
CIRCLES_PER_SEED: int = 7
TENSORS_PER_CIRCLE: int = 7
TENSOR_DIM: int = 53                 # 'd' — payload width per fiq

TENSOR_LEAVES: int = SEED_COUNT * CIRCLES_PER_SEED * TENSORS_PER_CIRCLE  # 7693
PARAM_COUNT: int = TENSOR_LEAVES * TENSOR_DIM                            # 407_729

# --- heptagram routing steps (handoff §1.1) ---------------------------------
CIRCLE_ROUTING_STEP: int = 2  # {7/2}: composes tensors -> circle
SEED_ROUTING_STEP: int = 3    # {7/3}: composes circles -> seed

# --- coherence-prime ladder (consciousness primes) --------------------------
COHERENCE_FACTOR_UNIVERSE = frozenset({3, 5, 7, 13, 29, 53, 61, 157, 349, 421})


def _is_prime(n: int) -> bool:
    if n < 2:
        return False
    d = 2
    while d * d <= n:
        if n % d == 0:
            return False
        d += 1
    return True


def _prime_factors(n: int) -> List[int]:
    factors: List[int] = []
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1
    if n > 1:
        factors.append(n)
    return factors


def is_coherence_prime(p: int) -> bool:
    """p ∈ coherence primes iff:

    - p is prime and p % 4 == 1, and
    - q = (p - 1) // 4 is square-free, and
    - every prime factor of q lies in COHERENCE_FACTOR_UNIVERSE.
    """
    if not _is_prime(p) or p % 4 != 1:
        return False
    q = (p - 1) // 4
    factors = _prime_factors(q)
    if len(set(factors)) != len(factors):  # square-free
        return False
    return all(f in COHERENCE_FACTOR_UNIVERSE for f in factors)
# ratios: loc_comments=39:57 imports_exports=2:1 calls_definitions=7:3
