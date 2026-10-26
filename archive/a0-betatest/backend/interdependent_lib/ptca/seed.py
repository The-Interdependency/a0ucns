# ratios: loc_comments=91:84 imports_exports=8:1 calls_definitions=26:14
# === MODULE_BUILD ===
# id: ptca_seed
#   module_name: seed
#   module_kind: engine
#   summary: PTCA Seed — 7 PCTA circles on a {7/3} heptagram with a UCNS opaque-host shape and an aggregate "seed-as-tensor" projection upward
#   owner: a0p maintainer
#   public_surface: Seed, SEED_CIRCLES, HEPTAGRAM_STEP_SEED
#   internal_surface: _seed_ucns_shape
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: a0p_skills.contracts.ptca_seed_holds_seven_holds
#   rollout: default_enabled
#   rollback: revert file from git
#   heptagram_step: 3
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: ptca_seed_boundaries
#   summary: PTCA Seed — 7 PCTA circles on a {7/3} heptagram with a UCNS opaque-host shape and an aggregate "seed-as-tensor" projection upward
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: ptca_seed
#   summary: PTCA Seed — 7 PCTA circles on a {7/3} heptagram with a UCNS opaque-host shape and an aggregate "seed-as-tensor" projection upward
#   exposes: Seed, SEED_CIRCLES, HEPTAGRAM_STEP_SEED
#   boundaries: auth:none, storage:none, network:none, user_data:none
#   owner: a0p maintainer
# === END CAPABILITIES ===
"""PTCA Seed — UCNS-mirrored bundle of seven PCTA circles."""
from __future__ import annotations
from fractions import Fraction
from typing import Sequence

import ucns

from ..pcna.tensor import Tensor, TENSOR_DIM
from ..pcna.group import aggregate
from ..pcta.circle import Circle, heptagram_walk, CIRCLE_SIZE
from .. import ucns_bridge as ub

# === CONTRACTS ===
# id: ptca_seed_holds_seven
#   given: a freshly constructed Seed from 7 Circles
#   then: seed.circles has length 7 and the {7/3} heptagram visits every index exactly once
#   class: correctness
#   call: a0p_skills.contracts.ptca_seed_holds_seven_holds
# === END CONTRACTS ===

# === CONTRACTS ===
# id: ptca_seed_aggregate_is_tensor
#   given: a Seed
#   then: seed.aggregate() returns a Tensor of width 53 (the seed-level "8th referent")
#   class: correctness
#   call: a0p_skills.contracts.ptca_seed_aggregate_is_tensor_holds
# === END CONTRACTS ===

# === CONTRACTS ===
# id: ptca_seed_heptagram_routing
#   given: heptagram_walk(0, step=3, n=7)
#   then: returns the canonical {7/3} permutation (0, 3, 6, 2, 5, 1, 4)
#   class: correctness
#   call: a0p_skills.contracts.ptca_seed_heptagram_routing_holds
# === END CONTRACTS ===


# Canon: 7 circles per seed (PTCA prime_core/constants.py CIRCLES_PER_SEED).
SEED_CIRCLES: int = 7

# {7/3} for seed composition — visit-every-vertex stride-3 walk.
HEPTAGRAM_STEP_SEED: int = 3


def _seed_ucns_shape(content_hash: int = 0) -> "ucns.UCNSObject":
    """Depth-2 UCNS opaque host for a 7-circle seed.

    Same "opaque host" doctrine as the PCTA circle: the UCNS carrier
    proves seed-IS-a-UCNS-object, and stable identity follows from the
    content hash. Per-circle structure lives in `Seed._circles`.

    We use the canonical 2-cell form with an antipode bit derived from
    the content hash, matching the upstream PTCA prime_core stratum
    layout where each level wraps the lower one without changing the
    UCNS algebra's load.
    """
    face_bit = int(content_hash) & 1
    return ucns.UCNSObject(
        2,  # n_dec
        2,  # n_min
        [(Fraction(0), ub.UNIT), (Fraction(1), ub.UNIT)],
        [face_bit, face_bit],
    )


class Seed:
    """A PTCA seed: 7 PCTA circles + UCNS structural mirror + aggregate."""

    __slots__ = ("_circles", "_step", "_aggregate_cache", "_ucns_shape_cache")

    def __init__(
        self,
        circles: Sequence[Circle],
        step: int = HEPTAGRAM_STEP_SEED,
    ):
        if len(circles) != SEED_CIRCLES:
            raise ValueError(
                f"Seed requires exactly {SEED_CIRCLES} circles; got {len(circles)}"
            )
        for c in circles:
            if not isinstance(c, Circle):
                raise TypeError(
                    f"Seed circles must be Circle instances; got {type(c).__name__}"
                )
        if step <= 0 or step >= SEED_CIRCLES:
            raise ValueError(f"step must be in 1..{SEED_CIRCLES-1}; got {step}")
        self._circles: tuple[Circle, ...] = tuple(circles)
        self._step = int(step)
        self._aggregate_cache: Tensor | None = None
        self._ucns_shape_cache: "ucns.UCNSObject | None" = None

    # ---- factories ----------------------------------------------------------
    @classmethod
    def from_seed(
        cls,
        seed: int,
        label: str = "",
        step: int = HEPTAGRAM_STEP_SEED,
        circle_step: int = 2,
    ) -> "Seed":
        """Deterministic Seed reproducible from (seed, label)."""
        base = seed * SEED_CIRCLES
        circles = [
            Circle.from_seed(base + i, f"{label}::circle{i}", step=circle_step)
            for i in range(SEED_CIRCLES)
        ]
        return cls(circles, step=step)

    @classmethod
    def from_circles(
        cls,
        circles: Sequence[Circle],
        step: int = HEPTAGRAM_STEP_SEED,
    ) -> "Seed":
        return cls(circles, step=step)

    # ---- introspection ------------------------------------------------------
    @property
    def circles(self) -> tuple[Circle, ...]:
        return self._circles

    @property
    def step(self) -> int:
        """Heptagram step — 3 for {7/3}."""
        return self._step

    def aggregate(self) -> Tensor:
        """Seed-level "8th referent": aggregate of the seven circle-aggregates.

        Each Circle exposes an aggregate Tensor (its own 8th referent);
        the Seed aggregates those seven into one Tensor — that one
        Tensor IS the seed at the next layer up. Cached. No new
        independent params introduced.
        """
        if self._aggregate_cache is None:
            circle_aggs = [c.aggregate() for c in self._circles]
            self._aggregate_cache = aggregate(circle_aggs)
        return self._aggregate_cache

    def heptagram_order(self, start: int = 0) -> tuple[Circle, ...]:
        """Circles traversed in {7/3} order from `start`."""
        walk = heptagram_walk(start, self._step, SEED_CIRCLES)
        return tuple(self._circles[i] for i in walk)

    def ucns_shape(self) -> "ucns.UCNSObject":
        """UCNS opaque host — stable identity from the circle content hash."""
        if self._ucns_shape_cache is None:
            content_hash = hash(self._circles)
            self._ucns_shape_cache = _seed_ucns_shape(content_hash)
        return self._ucns_shape_cache

    def param_count(self) -> int:
        """Independent scalar parameters under this seed (no aggregate counted)."""
        # 7 circles × 7 tensors × TENSOR_DIM (=53). Aggregates are views, not params.
        return SEED_CIRCLES * CIRCLE_SIZE * TENSOR_DIM

    # ---- equality / hashing -------------------------------------------------
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Seed):
            return False
        return self._circles == other._circles and self._step == other._step

    def __hash__(self) -> int:
        return hash((self._circles, self._step))

    def __repr__(self) -> str:
        agg_head = self.aggregate().payload[0]
        return f"Seed({{7/{self._step}}}, circles={SEED_CIRCLES}, agg_head={agg_head:+.4f})"
# ratios: loc_comments=91:84 imports_exports=8:1 calls_definitions=26:14
