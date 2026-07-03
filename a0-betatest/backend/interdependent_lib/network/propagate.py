# ratios: loc_comments=53:58 imports_exports=6:4 calls_definitions=11:8
# === MODULE_BUILD ===
# id: network_propagate
#   module_name: propagate
#   module_kind: engine
#   summary: tick advancement — runs one heartbeat across all rings, applies PCEA `kernel_step` cross-cut between ticks, holds last-state keys
#   owner: a0p maintainer
#   public_surface: Tick, TickResult, RingTickResult
#   internal_surface: _initial_key
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: a0p_skills.contracts.network_tick_is_deterministic_holds
#   rollout: default_enabled
#   rollback: revert file from git
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: network_propagate_boundaries
#   summary: tick advancement — runs one heartbeat across all rings, applies PCEA `kernel_step` cross-cut between ticks, holds last-state keys
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: network_propagate
#   summary: tick advancement — runs one heartbeat across all rings, applies PCEA `kernel_step` cross-cut between ticks, holds last-state keys
#   exposes: Tick, TickResult, RingTickResult
#   boundaries: auth:none, storage:none, network:none, user_data:read
#   owner: a0p maintainer
# === END CAPABILITIES ===
"""Tick propagation — one heartbeat advances every ring once.

Per tick:
  1. Each ring computes its core aggregate (the ring's current state).
  2. The aggregate is PCEA-encrypted against the previous tick's plaintext
     aggregate (the key). Per PCEA boundary contract this is the only
     security-relevant step — losing the previous-tick aggregate (the
     key) means an observer can't decrypt the new state.
  3. The new plaintext aggregate is retained as the key for the next
     tick's encryption.

The Σ ring is rebuilt from the live host digest on every tick — so any
host-integrity drift surfaces as a change in Σ's aggregate that the
PCEA cross-cut binds to a new ciphertext stream.
"""
from __future__ import annotations
from dataclasses import dataclass, field

from ..pcna.tensor import Tensor, zero_tensor
from ..pcea.kernel import kernel_step
from .rings import Ring, build_ring
from .topology import RING_ORDER


# === CONTRACTS ===
# id: network_tick_is_deterministic
#   given: NetworkEngine().heartbeat()
#   then: tick_number advances; rings dict has one entry per ring in RING_ORDER; encryption actually changed each ring's aggregate
#   class: correctness
#   call: a0p_skills.contracts.network_tick_is_deterministic_holds
# === END CONTRACTS ===


def _initial_key(ring_name: str) -> Tensor:
    """First-ever 'last state' for a ring — deterministic and ring-specific."""
    return Tensor.from_seed(ord(ring_name[0]) * 1009 + len(ring_name), f"init::{ring_name}")


@dataclass
class RingTickResult:
    name: str
    plaintext_aggregate: Tensor
    ciphertext_aggregate: Tensor


@dataclass
class TickResult:
    tick_number: int
    rings: dict[str, RingTickResult] = field(default_factory=dict)


class Tick:
    """Holds per-ring previous-tick keys; advances all rings together."""

    def __init__(self):
        self._last_keys: dict[str, Tensor] = {
            name: _initial_key(name) for name in RING_ORDER
        }
        self._tick_count: int = 0

    @property
    def tick_count(self) -> int:
        return self._tick_count

    def advance(
        self,
        rings: dict[str, Ring],
        refresh_sigma: bool = True,
    ) -> TickResult:
        """Run one tick — encrypt every ring's aggregate against last key."""
        self._tick_count += 1
        result = TickResult(tick_number=self._tick_count)

        for name in RING_ORDER:
            ring = rings.get(name)
            if ring is None:
                continue

            # Refresh Σ from the live host digest each tick.
            if name == "sigma" and refresh_sigma:
                rings[name] = build_ring("sigma", n_override=ring.n)
                ring = rings[name]

            plain = ring.aggregate()
            last_key = self._last_keys.get(name) or zero_tensor()
            cipher = kernel_step(plain, last_key)
            self._last_keys[name] = plain  # advance key

            result.rings[name] = RingTickResult(
                name=name,
                plaintext_aggregate=plain,
                ciphertext_aggregate=cipher,
            )

        return result

    def last_key(self, ring_name: str) -> Tensor | None:
        return self._last_keys.get(ring_name)


__all__ = ["Tick", "TickResult", "RingTickResult"]
# ratios: loc_comments=53:58 imports_exports=6:4 calls_definitions=11:8
