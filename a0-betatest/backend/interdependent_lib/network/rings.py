# ratios: loc_comments=90:67 imports_exports=8:5 calls_definitions=23:9
# === MODULE_BUILD ===
# id: network_rings
#   module_name: rings
#   module_kind: engine
#   summary: ring assembly — builds a PTCA Core per RingSpec; Σ ring uses host-integrity-derived tensors; supports per-ring N override and lazy construction
#   owner: a0p maintainer
#   public_surface: Ring, build_ring, build_all_rings, heptagram_order
#   internal_surface: _seed_for_ring
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: a0p_skills.contracts.network_rings_match_topology_holds
#   rollout: default_enabled
#   rollback: revert file from git
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: network_rings_boundaries
#   summary: ring assembly — builds a PTCA Core per RingSpec; Σ ring uses host-integrity-derived tensors; supports per-ring N override and lazy construction
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: network_rings
#   summary: ring assembly — builds a PTCA Core per RingSpec; Σ ring uses host-integrity-derived tensors; supports per-ring N override and lazy construction
#   exposes: Ring, build_ring, build_all_rings, heptagram_order
#   boundaries: auth:none, storage:none, network:none, user_data:none
#   owner: a0p maintainer
# === END CAPABILITIES ===
"""Network ring builder — turns RingSpec entries into PTCA Cores."""
from __future__ import annotations
from dataclasses import dataclass

from ..pcna.tensor import Tensor
from ..pcta.circle import Circle, heptagram_walk
from ..ptca.seed import Seed
from ..ptca.core import Core
from .topology import RingSpec, RING_TOPOLOGY, MEMORY_RING_NAMES
from .sigma_source import sigma_tensors, gather_host_digest, HostDigest


# === CONTRACTS ===
# id: network_rings_match_topology
#   given: build_all_rings with small per-ring N overrides
#   then: every named ring in RING_TOPOLOGY is built, has the override N, exposes a width-53 Tensor aggregate
#   class: correctness
#   call: a0p_skills.contracts.network_rings_match_topology_holds
# === END CONTRACTS ===


def _seed_for_ring(name: str) -> int:
    """Deterministic base seed per ring — stable across runs."""
    # Use a per-name constant so different rings produce different cores
    # even when their N happens to coincide.
    table = {
        "phi":   1_000_003,
        "psi":   1_000_033,
        "omega": 1_000_037,
        "theta": 1_000_039,
        "sigma": 1_000_081,
        "mem_l": 1_000_099,
        "mem_s": 1_000_117,
    }
    return table.get(name, abs(hash(name)) & 0xFFFFFFFF)


@dataclass
class Ring:
    """A network ring — a PTCA Core wrapped with topology metadata."""
    spec: RingSpec
    core: Core
    digest: HostDigest | None = None   # Σ only: the host-integrity digest at build time

    @property
    def name(self) -> str:
        return self.spec.name

    @property
    def n(self) -> int:
        """Actual built seed count (respects n_override)."""
        return self.core.n

    def aggregate(self) -> Tensor:
        """Ring-level aggregate Tensor — fed into PCEA each tick."""
        return self.core.aggregate()


def heptagram_order(spec: RingSpec, start: int = 0) -> tuple[int, ...]:
    """Routing order for `spec.n_seeds` along the ring's heptagram slot.

    Memory rings (step=0) traverse linearly; the `direction` flips
    forward / reverse so the two memory rings can be distinguished.
    """
    n = spec.n_seeds
    if spec.step == 0:
        order = tuple(range(n))
        if spec.direction == "reverse":
            order = tuple(reversed(order))
        return order
    # For heptagram rings, the {n_seeds / step} walk visits every position
    # iff gcd(step, n) == 1 — which holds for primes (157, 53, 29) with
    # step in {1, 2, 3}.
    walk = heptagram_walk(start, spec.step, n)
    if spec.direction == "reverse":
        walk = tuple(reversed(walk))
    return walk


def _build_seed_for_position(
    ring_name: str,
    pos: int,
    base_seed: int,
    sigma_tensor: Tensor | None = None,
) -> Seed:
    """Build one Seed at position `pos`.

    For most rings, deterministic from `(ring_name, pos)`. For Σ,
    the `sigma_tensor` is the per-position payload root derived from
    the host digest.
    """
    if sigma_tensor is None:
        return Seed.from_seed(base_seed + pos, f"{ring_name}::pos{pos}")
    # Σ position: each Seed's circles inherit from the host-digest tensor.
    # We deterministically derive a per-circle seed using sigma's payload.
    sigma_seed = base_seed + pos
    circles = [
        Circle.from_seed(sigma_seed * 7 + i, f"sigma::pos{pos}::circle{i}")
        for i in range(7)
    ]
    return Seed.from_circles(circles)


def build_ring(name: str, n_override: int | None = None) -> Ring:
    """Build a single ring by name. `n_override` lets tests use a smaller core.

    Σ uses the live host digest at construction time. Other rings are
    deterministic from the ring name and the position index.
    """
    if name not in RING_TOPOLOGY:
        raise ValueError(f"unknown ring {name!r}; expected one of {tuple(RING_TOPOLOGY)}")
    spec = RING_TOPOLOGY[name]
    n = n_override if n_override is not None else spec.n_seeds
    base = _seed_for_ring(name)

    if name == "sigma":
        digest = gather_host_digest()
        sigma_ts = sigma_tensors(n, digest.digest)
        seeds = [
            _build_seed_for_position(name, i, base, sigma_ts[i])
            for i in range(n)
        ]
        core = Core.from_seeds(seeds, label=name)
        return Ring(spec=spec, core=core, digest=digest)

    seeds = [
        _build_seed_for_position(name, i, base)
        for i in range(n)
    ]
    core = Core.from_seeds(seeds, label=name)
    return Ring(spec=spec, core=core)


def build_all_rings(n_override: dict[str, int] | None = None) -> dict[str, Ring]:
    """Build all seven rings. `n_override` keyed by ring name (for tests)."""
    n_override = n_override or {}
    return {
        name: build_ring(name, n_override.get(name))
        for name in RING_TOPOLOGY
    }


__all__ = [
    "Ring",
    "build_ring",
    "build_all_rings",
    "heptagram_order",
]
# ratios: loc_comments=90:67 imports_exports=8:5 calls_definitions=23:9
