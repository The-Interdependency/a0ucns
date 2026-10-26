# ratios: loc_comments=72:65 imports_exports=4:4 calls_definitions=24:15
# === MODULE_BUILD ===
# id: pcna_tensor_leaf
#   module_name: tensor
#   module_kind: engine
#   summary: leaf Tensor — d=53 scalar payload, deterministic from a (seed, label) pair; the substrate of the layered (PCNA leaf → PCTA circle → PTCA seed → core) model
#   owner: a0p maintainer
#   public_surface: Tensor, TENSOR_DIM, zero_tensor, tensors_equal
#   internal_surface: _stretch_payload
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: a0p_skills.contracts.pcna_tensor_deterministic
#   rollout: default_enabled
#   rollback: revert file from git
#   payload_width: 53
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: pcna_tensor_leaf_boundaries
#   summary: leaf Tensor — d=53 scalar payload, deterministic from a (seed, label) pair; the substrate of the layered (PCNA leaf → PCTA circle → PTCA seed → core) model
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: pcna_tensor_leaf
#   summary: leaf Tensor — d=53 scalar payload, deterministic from a (seed, label) pair; the substrate of the layered (PCNA leaf → PCTA circle → PTCA seed → core) model
#   exposes: Tensor, TENSOR_DIM, zero_tensor, tensors_equal
#   boundaries: auth:none, storage:none, network:none, user_data:none
#   owner: a0p maintainer
# === END CAPABILITIES ===
"""PCNA leaf tensor — the bottom of the layered model.

A Tensor is a fixed-width (d=53) sequence of scalar payload values. It
is the *leaf* of the layered hierarchy:

  Tensor   ←  this module (PCNA-layer leaf)
  Circle   ←  PCTA module (7 tensors + aggregate)
  Seed     ←  PTCA module (7 circles + aggregate)
  Core     ←  ptca.core   (N seeds + aggregate)

The aggregate at any layer is itself a Tensor of width d=53 — that's
why "all seven together" is "another tensor" without changing type.
"""
from __future__ import annotations
import hashlib
import struct
from typing import Iterable

# === CONTRACTS ===
# id: pcna_tensor_deterministic
#   given: Tensor.from_seed(s, label) called twice with the same (s, label)
#   then: both calls produce equal Tensors with d=53 payload
#   class: correctness
#   call: a0p_skills.contracts.pcna_tensor_deterministic
# === END CONTRACTS ===

# Canon: payload width d = 53 (synced from PTCA prime_core/constants.py TENSOR_DIM).
TENSOR_DIM: int = 53


def _stretch_payload(seed: int, label: str, n: int = TENSOR_DIM) -> tuple[float, ...]:
    """Deterministically produce n floats in [-0.5, 0.5] from (seed, label).

    Uses SHA-256 of the salted input as the entropy source; cycles the
    digest as needed for n > 8. Pure stdlib, fully reproducible.
    """
    salt = f"a0p::pcna::tensor::{seed}::{label}".encode("utf-8")
    out: list[float] = []
    counter = 0
    while len(out) < n:
        block = hashlib.sha256(salt + counter.to_bytes(4, "little")).digest()  # 32 bytes
        for off in range(0, 32, 4):
            if len(out) >= n:
                break
            (raw,) = struct.unpack("<I", block[off:off + 4])
            out.append((raw / 0xFFFFFFFF) - 0.5)  # [-0.5, +0.5]
        counter += 1
    return tuple(out)


class Tensor:
    """A length-d=53 scalar payload tensor with deterministic construction."""

    __slots__ = ("_payload", "_seed", "_label")

    def __init__(self, payload: Iterable[float], seed: int = 0, label: str = ""):
        p = tuple(payload)
        if len(p) != TENSOR_DIM:
            raise ValueError(
                f"Tensor requires payload width d={TENSOR_DIM}, got {len(p)}"
            )
        self._payload = p
        self._seed = int(seed)
        self._label = str(label)

    # ---- factories ----------------------------------------------------------
    @classmethod
    def from_seed(cls, seed: int, label: str = "") -> "Tensor":
        """Deterministic Tensor reproducible from (seed, label)."""
        return cls(_stretch_payload(seed, label), seed=seed, label=label)

    @classmethod
    def zero(cls) -> "Tensor":
        return cls([0.0] * TENSOR_DIM)

    # ---- introspection ------------------------------------------------------
    @property
    def payload(self) -> tuple[float, ...]:
        return self._payload

    @property
    def seed(self) -> int:
        return self._seed

    @property
    def label(self) -> str:
        return self._label

    def width(self) -> int:
        return TENSOR_DIM

    def energy(self) -> float:
        """L2 norm of the payload."""
        s = 0.0
        for v in self._payload:
            s += v * v
        return s ** 0.5

    # ---- equality / hashing -------------------------------------------------
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Tensor):
            return False
        return self._payload == other._payload

    def __hash__(self) -> int:
        return hash(self._payload)

    def __repr__(self) -> str:
        head = ", ".join(f"{v:+.4f}" for v in self._payload[:3])
        return f"Tensor(d={TENSOR_DIM}, head=[{head}, …])"


def zero_tensor() -> Tensor:
    """Module-level convenience for the zero (identity-under-mean) tensor."""
    return Tensor.zero()


def tensors_equal(a: Tensor, b: Tensor, tol: float = 0.0) -> bool:
    """Equality with optional float tolerance. Exact when tol=0."""
    if tol <= 0.0:
        return a == b
    if not isinstance(a, Tensor) or not isinstance(b, Tensor):
        return False
    for x, y in zip(a.payload, b.payload):
        if abs(x - y) > tol:
            return False
    return True


__all__ = ["Tensor", "TENSOR_DIM", "zero_tensor", "tensors_equal"]
# ratios: loc_comments=72:65 imports_exports=4:4 calls_definitions=24:15
