# ratios: loc_comments=53:73 imports_exports=3:1 calls_definitions=8:9
# === MODULE_BUILD ===
# id: ptca_tensor
#   module_name: tensor
#   module_kind: engine
#   summary: canon stratified prime-indexed tensor — shape [N,7,7,53] (seed × circle × tensor × payload); the Fiq→Circle→Seed model from prime_core, N×7×7×53 leaves (407,729 for N=157) matching PTCA prime_core PARAM_COUNT
#   owner: a0p maintainer
#   public_surface: PrimeTensor
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: a0p_skills.contracts.ptca_tensor_canon_shape_holds
#   rollout: default_enabled
#   rollback: revert file from git
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: ptca_tensor_boundaries
#   summary: canon stratified prime-indexed tensor — shape [N,7,7,53] (seed × circle × tensor × payload), N×7×7×53 leaves matching PTCA prime_core PARAM_COUNT
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: ptca_tensor
#   summary: canon stratified prime-indexed tensor — shape [N,7,7,53] (seed × circle × tensor × payload), N×7×7×53 leaves matching PTCA prime_core PARAM_COUNT
#   exposes: PrimeTensor
#   boundaries: auth:none, storage:none, network:none, user_data:none
#   owner: a0p maintainer
# === END CAPABILITIES ===
"""PrimeTensor — canon stratified nested-list tensor indexed by prime nodes.

Rebuilt from the legacy flat [N, 4, 7, 7] shape to the canon prime_core
stratification [N, 7, 7, 53] — seed × circle × tensor × payload:

    payload  ← 53 leaf scalars per fiq tensor          (PCNA TENSOR_DIM)
    tensor   ← 7 tensors per circle, routed {7/2}       (PCTA)
    circle   ← 7 circles per seed,   routed {7/3}       (PTCA)
    seed     ← N prime-indexed seeds (N=157 canon Φ/Ψ/Ω)

The leaf count N×7×7×53 is 407,729 for N=157, matching PTCA prime_core
PARAM_COUNT verbatim. Pure Python, no numpy — every value is a deterministic
function of (seed, prime, axis indices).
"""
from __future__ import annotations
from .primes import first_n_primes
from .constants import (
    CIRCLES_PER_SEED,
    TENSORS_PER_CIRCLE,
    TENSOR_DIM,
    CIRCLE_ROUTING_STEP,
    SEED_ROUTING_STEP,
)


class PrimeTensor:
    """Tensor whose first axis is indexed by the first N primes.

    Shape: (N, 7, 7, 53) — seed × circle × tensor × payload. The three inner
    axes are the canon Fiq→Circle→Seed stratification (53-wide payload, 7
    tensors per circle via {7/2}, 7 circles per seed via {7/3}).
    """

    CIRCLES = CIRCLES_PER_SEED      # 7  — circles per seed
    TENSORS = TENSORS_PER_CIRCLE    # 7  — tensors per circle
    DIM = TENSOR_DIM                # 53 — payload width per fiq tensor

    def __init__(self, n_primes: int, fill: float = 0.0):
        self.n = n_primes
        self.primes = first_n_primes(n_primes)
        # nested list: [N][7][7][53]
        self.data = [
            [[[fill] * self.DIM for _ in range(self.TENSORS)]
             for _ in range(self.CIRCLES)]
            for _ in range(self.n)
        ]

    def set(self, i: int, c: int, t: int, d: int, v: float) -> None:
        self.data[i][c][t][d] = v

    def get(self, i: int, c: int, t: int, d: int) -> float:
        return self.data[i][c][t][d]

    def slice_node(self, i: int) -> list:
        """The [7, 7, 53] circle×tensor×payload block for prime node i."""
        return self.data[i]

    def param_count(self) -> int:
        """Independent leaf scalars — N × 7 × 7 × 53 (407,729 for N=157)."""
        return self.n * self.CIRCLES * self.TENSORS * self.DIM

    def energy(self) -> float:
        """L2-style energy across the tensor (no numpy)."""
        s = 0.0
        for seed_block in self.data:
            for circle_block in seed_block:
                for tensor_row in circle_block:
                    for v in tensor_row:
                        s += v * v
        return s ** 0.5

    def seed_from_int(self, seed: int) -> None:
        """Deterministic fill — values derived from primes, seed and axis indices.

        The circle/tensor strides fold in the canon heptagram routing steps
        ({7/3} for circles, {7/2} for tensors) so differently-routed leaves
        stay distinguishable.
        """
        for i, prime in enumerate(self.primes):
            for c in range(self.CIRCLES):
                for t in range(self.TENSORS):
                    base = seed * prime + c * SEED_ROUTING_STEP * 101 + t * CIRCLE_ROUTING_STEP * 53
                    for d in range(self.DIM):
                        self.data[i][c][t][d] = ((base + d * 7) % 9973) / 9973.0

    def summary(self) -> dict:
        return {
            "n_primes": self.n,
            "shape": [self.n, self.CIRCLES, self.TENSORS, self.DIM],
            "param_count": self.param_count(),
            "primes_head": self.primes[:8],
            "primes_tail": self.primes[-3:],
            "energy": round(self.energy(), 6),
        }

# === CONTRACTS ===
# id: ptca_tensor_loads
#   given: module declares its msdmd canon
#   then: the module imports cleanly under the current interpreter
#   class: integration
#   call: a0p_skills.contracts.module_imports_cleanly_holds
# === END CONTRACTS ===
# === CONTRACTS ===
# id: ptca_tensor_canon_shape
#   given: PrimeTensor(157) built on the canon stratification
#   then: shape == [157,7,7,53] and param_count == 407_729 (PTCA prime_core PARAM_COUNT); set/get round-trips
#   class: correctness
#   call: a0p_skills.contracts.ptca_tensor_canon_shape_holds
# === END CONTRACTS ===
# ratios: loc_comments=53:73 imports_exports=3:1 calls_definitions=8:9
