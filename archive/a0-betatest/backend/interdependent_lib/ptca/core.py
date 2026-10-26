# ratios: loc_comments=101:91 imports_exports=8:3 calls_definitions=29:15
# === MODULE_BUILD ===
# id: ptca_core
#   module_name: core
#   module_kind: engine
#   summary: PTCA Core — N PTCA Seeds (N=157 canon for Φ/Ψ/Ω; tunable for Θ/Σ) plus aggregate-as-tensor projection upward; param count is N × 7 × 7 × 53
#   owner: a0p maintainer
#   public_surface: Core, DEFAULT_N, core_aggregate
#   internal_surface: _core_ucns_shape
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: a0p_skills.contracts.ptca_core_assembles_157_holds
#   rollout: default_enabled
#   rollback: revert file from git
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: ptca_core_boundaries
#   summary: PTCA Core — N PTCA Seeds (N=157 canon for Φ/Ψ/Ω; tunable for Θ/Σ) plus aggregate-as-tensor projection upward; param count is N × 7 × 7 × 53
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: ptca_core
#   summary: PTCA Core — N PTCA Seeds (N=157 canon for Φ/Ψ/Ω; tunable for Θ/Σ) plus aggregate-as-tensor projection upward; param count is N × 7 × 7 × 53
#   exposes: Core, DEFAULT_N, core_aggregate
#   boundaries: auth:none, storage:none, network:none, user_data:none
#   owner: a0p maintainer
# === END CAPABILITIES ===
"""PTCA Core — top layer of the layered model.

A `Core` is the topmost wrapper:

    Tensor   (PCNA)   ←  d=53 leaf scalars
    Circle   (PCTA)   ←  7 tensors + aggregate
    Seed     (PTCA)   ←  7 circles + aggregate
    Core     (this)   ←  N seeds + aggregate

For the three primary rings (Φ Ψ Ω) the user pins N=157 — matching the
upstream PTCA prime_core SEED_COUNT. For the gate (Θ) and observer
(Σ) rings, N is configurable (canon Θ=29, user Σ=53 read-only).

The aggregate at the core level is a single Tensor of width 53 — the
"all N seeds together is one tensor" referent. Like the lower layers,
aggregates are pure projections — they do NOT add parameters.

Independent param count: `N × 7 × 7 × 53`. For N=157 this is exactly
**407,729** (matches PTCA prime_core PARAM_COUNT verbatim).
"""
from __future__ import annotations
from fractions import Fraction
from typing import Sequence

import ucns

from ..pcna.tensor import Tensor, TENSOR_DIM
from ..pcta.circle import CIRCLE_SIZE
from .. import ucns_bridge as ub
from .seed import Seed, SEED_CIRCLES

# === CONTRACTS ===
# id: ptca_core_assembles_157
#   given: Core.with_n(157) built from canonical seeds
#   then: core has 157 seeds; param_count == 157*7*7*53 == 407_729
#   class: correctness
#   call: a0p_skills.contracts.ptca_core_assembles_157_holds
# === END CONTRACTS ===

# === CONTRACTS ===
# id: ptca_core_aggregate_is_tensor
#   given: a Core of N seeds
#   then: core.aggregate() returns a Tensor of width 53 (the core-level "8th referent")
#   class: correctness
#   call: a0p_skills.contracts.ptca_core_aggregate_is_tensor_holds
# === END CONTRACTS ===

# === CONTRACTS ===
# id: ptca_core_param_count_matches_canon
#   given: Core with default N=157
#   then: param_count() == PTCA prime_core PARAM_COUNT (407_729)
#   class: provenance
#   call: a0p_skills.contracts.ptca_core_param_count_matches_canon_holds
# === END CONTRACTS ===


# Canon default — Φ Ψ Ω rings per user spec.
DEFAULT_N: int = 157


def core_aggregate(tensors: Sequence[Tensor]) -> Tensor:
    """N-fold aggregate — element-wise mean over any number of Tensors.

    PCNA's `group.aggregate` enforces N=7 at the circle / seed layers.
    The core layer can have any N (157 for Φ/Ψ/Ω, 29 for Θ, 53 for Σ, …),
    so we provide a generalized aggregator here.
    """
    if not tensors:
        raise ValueError("core_aggregate requires at least one Tensor")
    n = len(tensors)
    sums = [0.0] * TENSOR_DIM
    for t in tensors:
        if not isinstance(t, Tensor):
            raise TypeError(
                f"core_aggregate expects Tensor instances; got {type(t).__name__}"
            )
        for i, v in enumerate(t.payload):
            sums[i] += v
    return Tensor([s / n for s in sums])


def _core_ucns_shape(content_hash: int = 0) -> "ucns.UCNSObject":
    """Depth-3 UCNS opaque host — same canonical form as lower layers."""
    face_bit = int(content_hash) & 1
    return ucns.UCNSObject(
        2,
        2,
        [(Fraction(0), ub.UNIT), (Fraction(1), ub.UNIT)],
        [face_bit, face_bit],
    )


class Core:
    """A PTCA core: N seeds + UCNS opaque host + aggregate Tensor."""

    __slots__ = (
        "_seeds", "_n", "_label", "_aggregate_cache", "_ucns_shape_cache",
    )

    def __init__(self, seeds: Sequence[Seed], label: str = ""):
        if not seeds:
            raise ValueError("Core requires at least one Seed")
        for s in seeds:
            if not isinstance(s, Seed):
                raise TypeError(
                    f"Core seeds must be Seed instances; got {type(s).__name__}"
                )
        self._seeds: tuple[Seed, ...] = tuple(seeds)
        self._n = len(self._seeds)
        self._label = str(label)
        self._aggregate_cache: Tensor | None = None
        self._ucns_shape_cache: "ucns.UCNSObject | None" = None

    # ---- factories ----------------------------------------------------------
    @classmethod
    def with_n(
        cls,
        n: int = DEFAULT_N,
        label: str = "phi",
        seed_step: int = 3,
        circle_step: int = 2,
        base_seed: int = 1,
    ) -> "Core":
        """Build a Core with N deterministic seeds.

        `label` is forwarded into each seed's deterministic content so
        differently-labeled cores produce differently-valued aggregates
        even at the same N and base_seed.
        """
        if n <= 0:
            raise ValueError(f"n must be positive; got {n}")
        seeds = [
            Seed.from_seed(
                base_seed * 10_000 + i,
                f"{label}::seed{i}",
                step=seed_step,
                circle_step=circle_step,
            )
            for i in range(n)
        ]
        return cls(seeds, label=label)

    @classmethod
    def from_seeds(cls, seeds: Sequence[Seed], label: str = "") -> "Core":
        return cls(seeds, label=label)

    # ---- introspection ------------------------------------------------------
    @property
    def seeds(self) -> tuple[Seed, ...]:
        return self._seeds

    @property
    def n(self) -> int:
        """Number of seeds in this core."""
        return self._n

    @property
    def label(self) -> str:
        """Ring label — 'phi' / 'psi' / 'omega' / 'theta' / 'sigma' / arbitrary."""
        return self._label

    def aggregate(self) -> Tensor:
        """Core-level "8th referent": aggregate of the N seed-aggregates."""
        if self._aggregate_cache is None:
            seed_aggs = [s.aggregate() for s in self._seeds]
            self._aggregate_cache = core_aggregate(seed_aggs)
        return self._aggregate_cache

    def param_count(self) -> int:
        """Independent scalar parameter count — N * 7 * 7 * 53. Aggregates are views."""
        return self._n * SEED_CIRCLES * CIRCLE_SIZE * TENSOR_DIM

    def ucns_shape(self) -> "ucns.UCNSObject":
        """UCNS opaque host — stable identity from the seed content hash."""
        if self._ucns_shape_cache is None:
            content_hash = hash(self._seeds)
            self._ucns_shape_cache = _core_ucns_shape(content_hash)
        return self._ucns_shape_cache

    # ---- equality / hashing -------------------------------------------------
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Core):
            return False
        return self._seeds == other._seeds and self._label == other._label

    def __hash__(self) -> int:
        return hash((self._seeds, self._label))

    def __repr__(self) -> str:
        return f"Core({self._label!r}, n={self._n}, params={self.param_count()})"


__all__ = ["Core", "DEFAULT_N", "core_aggregate"]
# ratios: loc_comments=101:91 imports_exports=8:3 calls_definitions=29:15
