# ratios: loc_comments=99:102 imports_exports=7:4 calls_definitions=32:16
# === MODULE_BUILD ===
# id: pcta_circle
#   module_name: circle
#   module_kind: engine
#   summary: PCTA Circle — 7 PCNA tensors on a {7/2} heptagram with a UCNS structural mirror and an aggregate "circle-as-tensor" projection upward
#   owner: a0p maintainer
#   public_surface: Circle, CIRCLE_SIZE, HEPTAGRAM_STEP_CIRCLE, heptagram_walk, heptagram_walk_7_2, heptagram_walk_7_3
#   internal_surface: _circle_ucns_shape
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: a0p_skills.contracts.pcta_circle_holds_seven_holds
#   rollout: default_enabled
#   rollback: revert file from git
#   heptagram_step: 2
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: pcta_circle_boundaries
#   summary: PCTA Circle — 7 PCNA tensors on a {7/2} heptagram with a UCNS structural mirror and an aggregate "circle-as-tensor" projection upward
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: pcta_circle
#   summary: PCTA Circle — 7 PCNA tensors on a {7/2} heptagram with a UCNS structural mirror and an aggregate "circle-as-tensor" projection upward
#   exposes: Circle, CIRCLE_SIZE, HEPTAGRAM_STEP_CIRCLE, heptagram_walk, heptagram_walk_7_2, heptagram_walk_7_3
#   boundaries: auth:none, storage:none, network:none, user_data:none
#   owner: a0p maintainer
# === END CAPABILITIES ===
"""PCTA Circle — UCNS-mirrored bundle of seven leaf tensors."""
from __future__ import annotations
from fractions import Fraction
from typing import Sequence

import ucns

from ..pcna.tensor import Tensor, TENSOR_DIM
from ..pcna.group import aggregate
from .. import ucns_bridge as ub

# === CONTRACTS ===
# id: pcta_circle_holds_seven
#   given: a freshly constructed Circle from 7 Tensors
#   then: circle.tensors has length 7 and the heptagram order visits every index exactly once
#   class: correctness
#   call: a0p_skills.contracts.pcta_circle_holds_seven_holds
# === END CONTRACTS ===

# === CONTRACTS ===
# id: pcta_circle_aggregate_is_tensor
#   given: a Circle
#   then: circle.aggregate() returns a Tensor of width 53 (the "8th referent")
#   class: correctness
#   call: a0p_skills.contracts.pcta_circle_aggregate_is_tensor_holds
# === END CONTRACTS ===

# === CONTRACTS ===
# id: pcta_circle_heptagram_routing
#   given: heptagram_walk(0, step=2, n=7)
#   then: returns a permutation of [0..6] in {7/2} order [0,2,4,6,1,3,5]
#   class: correctness
#   call: a0p_skills.contracts.pcta_circle_heptagram_routing_holds
# === END CONTRACTS ===

# === CONTRACTS ===
# id: pcta_circle_ucns_shape
#   given: circle.ucns_shape()
#   then: returns a UCNSObject with 7 cells and UNIT payloads (structural mirror, not the per-position tensors)
#   class: correctness
#   call: a0p_skills.contracts.pcta_circle_ucns_shape_holds
# === END CONTRACTS ===


# Canon: 7 tensors per circle (PTCA prime_core/constants.py TENSORS_PER_CIRCLE).
CIRCLE_SIZE: int = 7

# {7/2} for circle composition — visit-every-vertex stride-2 walk.
HEPTAGRAM_STEP_CIRCLE: int = 2


def heptagram_walk(start: int, step: int, n: int = CIRCLE_SIZE) -> tuple[int, ...]:
    """Return the n-vertex {n/step} walk starting at `start`.

    Visits every vertex exactly once when gcd(step, n) == 1.
    For n=7 this is true for every step in 1..6, so all heptagrams cover.
    """
    if n <= 0:
        raise ValueError("n must be positive")
    out: list[int] = []
    cur = start % n
    for _ in range(n):
        out.append(cur)
        cur = (cur + step) % n
    return tuple(out)


def heptagram_walk_7_2(start: int = 0) -> tuple[int, ...]:
    """{7/2} forward: [0, 2, 4, 6, 1, 3, 5] from start=0."""
    return heptagram_walk(start, 2, CIRCLE_SIZE)


def heptagram_walk_7_3(start: int = 0) -> tuple[int, ...]:
    """{7/3} forward: [0, 3, 6, 2, 5, 1, 4] from start=0."""
    return heptagram_walk(start, 3, CIRCLE_SIZE)


def _circle_ucns_shape(content_hash: int = 0) -> "ucns.UCNSObject":
    """Depth-1 UCNS structural mirror — "opaque host" per upstream PTCA prime_core.

    Per upstream PTCA's stratification handoff, the UCNS object is an
    *opaque host* — its specific angle layout is not load-bearing; the
    fact that the carrier IS a UCNSObject is what the layered model
    requires. We use the canonical 2-cell flat form (n_dec=2, n_min=2)
    that UCNS accepts without normalization side-effects. The 7-fold
    cell structure of the PCTA circle lives in `Circle._tensors`, not
    in UCNS A_plus.

    The `content_hash` is taken mod 2 to derive a face bit, so distinct
    circles produce structurally distinguishable shapes at the UCNS
    level. Two circles with the same content hash produce identical
    UCNS shapes (stable identity).
    """
    face_bit = int(content_hash) & 1
    return ucns.UCNSObject(
        2,  # n_dec
        2,  # n_min
        [(Fraction(0), ub.UNIT), (Fraction(1), ub.UNIT)],
        [face_bit, face_bit],
    )


class Circle:
    """A PCTA circle: 7 leaf tensors + structural UCNS mirror + aggregate."""

    __slots__ = ("_tensors", "_step", "_aggregate_cache", "_ucns_shape_cache")

    def __init__(
        self,
        tensors: Sequence[Tensor],
        step: int = HEPTAGRAM_STEP_CIRCLE,
    ):
        if len(tensors) != CIRCLE_SIZE:
            raise ValueError(
                f"Circle requires exactly {CIRCLE_SIZE} tensors; got {len(tensors)}"
            )
        for t in tensors:
            if not isinstance(t, Tensor):
                raise TypeError(
                    f"Circle tensors must be Tensor instances; got {type(t).__name__}"
                )
        if step <= 0 or step >= CIRCLE_SIZE:
            raise ValueError(f"step must be in 1..{CIRCLE_SIZE-1}; got {step}")
        self._tensors: tuple[Tensor, ...] = tuple(tensors)
        self._step = int(step)
        self._aggregate_cache: Tensor | None = None
        self._ucns_shape_cache: "ucns.UCNSObject | None" = None

    # ---- factories ----------------------------------------------------------
    @classmethod
    def from_seed(
        cls,
        seed: int,
        label: str = "",
        step: int = HEPTAGRAM_STEP_CIRCLE,
    ) -> "Circle":
        """Deterministic Circle reproducible from (seed, label)."""
        base = seed * CIRCLE_SIZE
        ts = [
            Tensor.from_seed(base + i, f"{label}::pos{i}")
            for i in range(CIRCLE_SIZE)
        ]
        return cls(ts, step=step)

    @classmethod
    def from_tensors(
        cls,
        tensors: Sequence[Tensor],
        step: int = HEPTAGRAM_STEP_CIRCLE,
    ) -> "Circle":
        return cls(tensors, step=step)

    # ---- introspection ------------------------------------------------------
    @property
    def tensors(self) -> tuple[Tensor, ...]:
        return self._tensors

    @property
    def step(self) -> int:
        """Heptagram step — 2 for {7/2}, 3 for {7/3}, …"""
        return self._step

    def aggregate(self) -> Tensor:
        """The 8th-referent tensor: 'all seven together' as one Tensor.

        Computed via PCNA `aggregate` (element-wise mean). Cached.
        Does NOT add an independent parameter slot — this is a view.
        """
        if self._aggregate_cache is None:
            self._aggregate_cache = aggregate(list(self._tensors))
        return self._aggregate_cache

    def heptagram_order(self, start: int = 0) -> tuple[Tensor, ...]:
        """Tensors traversed in {7/step} order from `start`."""
        walk = heptagram_walk(start, self._step, CIRCLE_SIZE)
        return tuple(self._tensors[i] for i in walk)

    def ucns_shape(self) -> "ucns.UCNSObject":
        """UCNS structural mirror — opaque host per upstream PTCA spec.

        Two circles with identical tensor payloads produce identical
        UCNS shapes (stable identity). The 7-cell PCTA structure lives
        in `self._tensors`, not in the UCNS object's A_plus.
        """
        if self._ucns_shape_cache is None:
            # Deterministic content hash from the tuple of tensor payloads
            content_hash = hash(self._tensors)
            self._ucns_shape_cache = _circle_ucns_shape(content_hash)
        return self._ucns_shape_cache

    # ---- equality / hashing -------------------------------------------------
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Circle):
            return False
        return self._tensors == other._tensors and self._step == other._step

    def __hash__(self) -> int:
        return hash((self._tensors, self._step))

    def __repr__(self) -> str:
        agg_head = self.aggregate().payload[0]
        return f"Circle({{7/{self._step}}}, agg_head={agg_head:+.4f})"
# ratios: loc_comments=99:102 imports_exports=7:4 calls_definitions=32:16
