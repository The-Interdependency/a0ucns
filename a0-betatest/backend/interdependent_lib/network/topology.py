# ratios: loc_comments=46:62 imports_exports=3:3 calls_definitions=6:2
# === MODULE_BUILD ===
# id: network_topology
#   module_name: topology
#   module_kind: schema
#   summary: ring topology spec — names, per-ring N (Φ Ψ Ω 157, Θ 29, Σ 53, MemL 19, MemS 17), heptagram routing slots (lock-step avoidance via unique step+direction), ring weights for coherence scoring
#   owner: a0p maintainer
#   public_surface: RingSpec, RING_TOPOLOGY, RING_WEIGHTS, RING_ORDER, SCORED_RING_NAMES, OBSERVER_RING_NAMES, MEMORY_RING_NAMES
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: a0p_skills.contracts.network_topology_canonical_holds
#   rollout: default_enabled
#   rollback: revert file from git
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: network_topology_boundaries
#   summary: ring topology spec — names, per-ring N (Φ Ψ Ω 157, Θ 29, Σ 53, MemL 19, MemS 17), heptagram routing slots (lock-step avoidance via unique step+direction), ring weights for coherence scoring
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: network_topology
#   summary: ring topology spec — names, per-ring N (Φ Ψ Ω 157, Θ 29, Σ 53, MemL 19, MemS 17), heptagram routing slots (lock-step avoidance via unique step+direction), ring weights for coherence scoring
#   exposes: RingSpec, RING_TOPOLOGY, RING_WEIGHTS, RING_ORDER, SCORED_RING_NAMES, OBSERVER_RING_NAMES, MEMORY_RING_NAMES
#   boundaries: auth:none, storage:none, network:none, user_data:none
#   owner: a0p maintainer
# === END CAPABILITIES ===
"""Network ring topology — canonical spec for the a0p inference engine.

Per the user's spec (with all corrections folded in):

    Ring     N seeds    Heptagram slot       Role                Weight
    -----    -------    -----------------    -----------------   -------
    Φ phi      157      {7/2} forward        primary intent      0.30
    Ψ psi      157      {7/3} forward        substrate            0.15
    Ω omega    157      {7/2} reverse        broadcast            0.15
    Θ theta     29      {7/3} reverse        microkernel gate     0.20
    Σ sigma     53      {7/1} forward        host-integrity OBS   0.00  (observer)
    Mem-L       19      linear forward       long-term memory     0.12
    Mem-S       17      linear reverse       short-term memory    0.08

Six heptagram slots exist: (step, direction) ∈ {1,2,3} × {+,−}. Five
non-memory rings each get a unique slot — sixth slot stays free for
future expansion. Memory rings are linear (no heptagram routing).

Σ is read-only over host integrity (OS files + installed programs) —
its tensors are derived from a blake2b digest of the watched state.
A drift in Σ digest signals potential tamper.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal


# === CONTRACTS ===
# id: network_topology_canonical
#   given: import interdependent_lib.network.topology
#   then: per-ring N values match the user spec (Φ Ψ Ω 157, Θ 29, Σ 53, MemL 19, MemS 17); lock-step avoidance holds (unique heptagram slots); scored weights sum to 1.0
#   class: provenance
#   call: a0p_skills.contracts.network_topology_canonical_holds
# === END CONTRACTS ===


Direction = Literal["forward", "reverse", "linear"]


@dataclass(frozen=True)
class RingSpec:
    """Topology metadata for one ring of the network engine."""
    name: str
    n_seeds: int
    step: int           # 0 for memory rings (linear); 1/2/3 for heptagram rings
    direction: Direction
    weight: float       # contribution to coherence score; 0 = observer
    scored: bool        # True if this ring's energy enters the coherence aggregate
    role: str           # human-readable purpose


# Canonical topology (after user corrections — 2026-06-02).
RING_TOPOLOGY: dict[str, RingSpec] = {
    "phi":   RingSpec("phi",   n_seeds=157, step=2, direction="forward",  weight=0.30, scored=True,  role="primary_intent"),
    "psi":   RingSpec("psi",   n_seeds=157, step=3, direction="forward",  weight=0.15, scored=True,  role="substrate"),
    "omega": RingSpec("omega", n_seeds=157, step=2, direction="reverse",  weight=0.15, scored=True,  role="broadcast"),
    "theta": RingSpec("theta", n_seeds=29,  step=3, direction="reverse",  weight=0.20, scored=True,  role="microkernel_gate"),
    "sigma": RingSpec("sigma", n_seeds=53,  step=1, direction="forward",  weight=0.00, scored=False, role="host_integrity_observer"),
    "mem_l": RingSpec("mem_l", n_seeds=19,  step=0, direction="forward",  weight=0.12, scored=True,  role="long_term_memory"),
    "mem_s": RingSpec("mem_s", n_seeds=17,  step=0, direction="reverse",  weight=0.08, scored=True,  role="short_term_memory"),
}

RING_ORDER: tuple[str, ...] = (
    "phi", "psi", "omega", "theta", "sigma", "mem_l", "mem_s",
)

RING_WEIGHTS: dict[str, float] = {name: spec.weight for name, spec in RING_TOPOLOGY.items()}

SCORED_RING_NAMES: tuple[str, ...] = tuple(n for n, s in RING_TOPOLOGY.items() if s.scored)
OBSERVER_RING_NAMES: tuple[str, ...] = tuple(n for n, s in RING_TOPOLOGY.items() if not s.scored)
MEMORY_RING_NAMES: tuple[str, ...] = ("mem_l", "mem_s")


def unique_heptagram_slots() -> bool:
    """All non-memory rings must have unique (step, direction) pairs (lock-step avoidance)."""
    slots = [
        (spec.step, spec.direction)
        for name, spec in RING_TOPOLOGY.items()
        if name not in MEMORY_RING_NAMES
    ]
    return len(set(slots)) == len(slots)


__all__ = [
    "RingSpec",
    "RING_TOPOLOGY",
    "RING_WEIGHTS",
    "RING_ORDER",
    "SCORED_RING_NAMES",
    "OBSERVER_RING_NAMES",
    "MEMORY_RING_NAMES",
    "unique_heptagram_slots",
]
# ratios: loc_comments=46:62 imports_exports=3:3 calls_definitions=6:2
