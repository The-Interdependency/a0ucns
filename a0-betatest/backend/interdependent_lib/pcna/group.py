# ratios: loc_comments=21:80 imports_exports=3:4 calls_definitions=9:3
# === MODULE_BUILD ===
# id: pcna_group_aggregate
#   module_name: group
#   module_kind: engine
#   summary: "all seven together is a tensor" — aggregate composition op that lifts 7 Tensors to 1 Tensor (the 8th referent, the projection upward into the next layer)
#   owner: a0p maintainer
#   public_surface: GROUP_SIZE, aggregate, identity_tensor, is_identity
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: a0p_skills.contracts.pcna_aggregate_identity_holds
#   rollout: default_enabled
#   rollback: revert file from git
#   group_size: 7
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: pcna_group_aggregate_boundaries
#   summary: "all seven together is a tensor" — aggregate composition op that lifts 7 Tensors to 1 Tensor (the 8th referent, the projection upward into the next layer)
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: pcna_group_aggregate
#   summary: "all seven together is a tensor" — aggregate composition op that lifts 7 Tensors to 1 Tensor (the 8th referent, the projection upward into the next layer)
#   exposes: GROUP_SIZE, aggregate, identity_tensor, is_identity
#   boundaries: auth:none, storage:none, network:none, user_data:none
#   owner: a0p maintainer
# === END CAPABILITIES ===
"""PCNA group operator — the "seven together is one" lift.

The user's framing:
    one circle = seven tensors plus the tensor that is all seven tensors
    one seed   = seven circles plus the tensor that is all seven circles

This module implements the "all seven together" operator at the
tensor layer. The aggregate is itself a Tensor of width d=53 — same
type as its inputs — which is exactly why the structure is recursive
without ever changing type.

Important: the aggregate is the *eighth* tensor in the user's
description; it does NOT multiply into the per-core parameter count.
It is a projection / view upward, not an additional independent
payload. The independent param count for a Φ-core is 157·7·7·53 =
407,729, identical to canon `PARAM_COUNT`.
"""
from __future__ import annotations
from typing import Sequence
from .tensor import Tensor, TENSOR_DIM

# === CONTRACTS ===
# id: pcna_aggregate_size
#   given: aggregate(7 tensors)
#   then: returns one Tensor of width d=53
#   class: correctness
#   call: a0p_skills.contracts.pcna_aggregate_size_holds
# === END CONTRACTS ===

# === CONTRACTS ===
# id: pcna_aggregate_identity
#   given: aggregate of seven identity (zero) tensors
#   then: returns the identity tensor (zero of width 53)
#   class: correctness
#   call: a0p_skills.contracts.pcna_aggregate_identity_holds
# === END CONTRACTS ===

# === CONTRACTS ===
# id: pcna_aggregate_deterministic
#   given: aggregate called twice on the same seven tensors
#   then: both calls return equal Tensors
#   class: correctness
#   call: a0p_skills.contracts.pcna_aggregate_deterministic_holds
# === END CONTRACTS ===


# Canon: 7 tensors per circle, 7 circles per seed — heptagram.
GROUP_SIZE: int = 7


def aggregate(tensors: Sequence[Tensor]) -> Tensor:
    """Lift seven Tensors to one aggregate Tensor (the layer-above view).

    The aggregate is the element-wise mean of the seven payloads. This
    choice satisfies the contracts:
      - same width d=53
      - identity element under aggregate: the zero tensor
      - deterministic / pure function
    """
    if len(tensors) != GROUP_SIZE:
        raise ValueError(f"aggregate expects exactly {GROUP_SIZE} tensors; got {len(tensors)}")
    sums = [0.0] * TENSOR_DIM
    for t in tensors:
        if not isinstance(t, Tensor):
            raise TypeError(f"aggregate expects Tensor instances; got {type(t).__name__}")
        for i, v in enumerate(t.payload):
            sums[i] += v
    return Tensor([s / GROUP_SIZE for s in sums])


def identity_tensor() -> Tensor:
    """The identity under aggregate: the zero tensor of width 53."""
    return Tensor.zero()


def is_identity(t: Tensor) -> bool:
    """True iff every payload entry is exactly 0.0."""
    if not isinstance(t, Tensor):
        return False
    return all(v == 0.0 for v in t.payload)


__all__ = ["GROUP_SIZE", "aggregate", "identity_tensor", "is_identity"]
# ratios: loc_comments=21:80 imports_exports=3:4 calls_definitions=9:3
