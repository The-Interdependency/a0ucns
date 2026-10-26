# ratios: loc_comments=59:54 imports_exports=8:3 calls_definitions=14:8
# === MODULE_BUILD ===
# id: network_engine
#   module_name: engine
#   module_kind: engine
#   summary: NetworkEngine — top-level binder for the canonical PCNA inference engine; holds rings, tick state, tamper watcher; supports per-ring N override for tests
#   owner: a0p maintainer
#   public_surface: NetworkEngine, EngineState
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: a0p_skills.contracts.network_engine_heartbeat_holds
#   rollout: default_enabled
#   rollback: detach ZFAEAgent from NetworkEngine; revert file
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: network_engine_boundaries
#   summary: NetworkEngine — top-level binder for the canonical PCNA inference engine; holds rings, tick state, tamper watcher; supports per-ring N override for tests
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: network_engine
#   summary: NetworkEngine — top-level binder for the canonical PCNA inference engine; holds rings, tick state, tamper watcher; supports per-ring N override for tests
#   exposes: NetworkEngine, EngineState
#   boundaries: auth:none, storage:none, network:none, user_data:read
#   owner: a0p maintainer
# === END CAPABILITIES ===
"""NetworkEngine — binds rings + tick + coherence + tamper into one façade.

Public usage:
    engine = NetworkEngine()             # default full-size
    state  = engine.heartbeat()          # advance one tick
    state.coherence.total                # scalar coherence score
    state.tamper.drifted                 # True iff Σ host-integrity drift
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from .topology import RING_TOPOLOGY, RING_ORDER
from .rings import Ring, build_all_rings, build_ring
from .propagate import Tick, TickResult
from .coherence import CoherenceScore, TamperReport, TamperWatcher, score_tick
from .sigma_source import HostDigest, gather_host_digest


# === CONTRACTS ===
# id: network_engine_heartbeat
#   given: NetworkEngine() then heartbeat() twice
#   then: tick_count advances 0→1→2; baseline_digest_hex is 64-char hex; tamper.drifted False on tick with no host change; snapshot() is JSON-shaped
#   class: correctness
#   call: a0p_skills.contracts.network_engine_heartbeat_holds
# === END CONTRACTS ===


@dataclass
class EngineState:
    """One full heartbeat's worth of network state."""
    tick: TickResult
    coherence: CoherenceScore
    tamper: TamperReport


class NetworkEngine:
    """Top-level canonical inference engine."""

    def __init__(self, n_override: Optional[dict[str, int]] = None):
        self._rings: dict[str, Ring] = build_all_rings(n_override)
        self._tick: Tick = Tick()
        # Baseline Σ digest captured at engine construction.
        baseline_ring = self._rings.get("sigma")
        baseline_digest: HostDigest = (
            baseline_ring.digest if baseline_ring and baseline_ring.digest
            else gather_host_digest()
        )
        self._tamper: TamperWatcher = TamperWatcher(baseline_digest)
        self._n_override = n_override or {}

    @property
    def rings(self) -> dict[str, Ring]:
        return self._rings

    @property
    def tick_count(self) -> int:
        return self._tick.tick_count

    @property
    def baseline_digest_hex(self) -> str:
        return self._tamper.baseline_hex

    def heartbeat(self) -> EngineState:
        """Advance one tick across every ring and score the result."""
        tick_result = self._tick.advance(self._rings)
        coherence = score_tick(tick_result)
        # Σ digest after this tick
        current_sigma = self._rings.get("sigma")
        current_digest = current_sigma.digest if current_sigma and current_sigma.digest else gather_host_digest()
        tamper = self._tamper.evaluate(current_digest, tick_result.tick_number)
        return EngineState(tick=tick_result, coherence=coherence, tamper=tamper)

    def snapshot(self) -> dict:
        """JSON-serialisable summary of the current engine state."""
        return {
            "tick_count": self.tick_count,
            "baseline_digest": self._tamper.baseline_hex,
            "rings": {
                name: {
                    "n_seeds": ring.n,
                    "step": ring.spec.step,
                    "direction": ring.spec.direction,
                    "weight": ring.spec.weight,
                    "scored": ring.spec.scored,
                    "role": ring.spec.role,
                    "aggregate_energy": ring.aggregate().energy(),
                }
                for name, ring in self._rings.items()
            },
            "n_override": self._n_override,
        }


__all__ = ["NetworkEngine", "EngineState"]
# ratios: loc_comments=59:54 imports_exports=8:3 calls_definitions=14:8
