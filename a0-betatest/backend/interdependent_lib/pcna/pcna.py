# ratios: loc_comments=70:64 imports_exports=9:1 calls_definitions=25:7
# === MODULE_BUILD ===
# id: pcna_engine_impl
#   module_name: pcna
#   module_kind: engine
#   summary: PCNAEngine compatibility facade over the canonical 61-seed network engine; preserves legacy inspector fields while routing heartbeat state through tensor rings and PCEA tick encryption
#   owner: a0p maintainer
#   public_surface: PCNAEngine
#   internal_surface: _signals_from_network_state
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: a0p_skills.contracts.pcna_engine_uses_network_handoff_holds
#   rollout: default_enabled
#   rollback: revert file from git
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: pcna_engine_impl_boundaries
#   summary: PCNAEngine compatibility facade over the canonical 61-seed network engine; preserves legacy inspector fields while routing heartbeat state through tensor rings and PCEA tick encryption
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: pcna_engine_impl
#   summary: PCNAEngine compatibility facade over the canonical 61-seed network engine; preserves legacy inspector fields while routing heartbeat state through tensor rings and PCEA tick encryption
#   exposes: PCNAEngine
#   boundaries: auth:none, storage:none, network:none, user_data:read
#   owner: a0p maintainer
# === END CAPABILITIES ===
"""PCNAEngine — legacy facade backed by the canonical PCNA network.

The repo now has two surfaces that must coexist for one compatibility
cycle:

* ``interdependent_lib.network.NetworkEngine`` is the canonical handoff
  implementation: topology-backed tensor rings, per-tick PCEA encryption,
  weighted coherence, and Σ host-integrity observation.
* ``PCNAEngine`` is the older inspector/ZFAE facade. Public callers still
  expect ``heartbeat()``, ``snapshot()``, ``ring_signals``, memory injection,
  and response/intention hooks.

This module keeps the legacy shape, but its heartbeat state comes from
``NetworkEngine``. That closes the old "canon topology rebuild pending"
handoff without breaking existing API consumers.
"""
from __future__ import annotations
from typing import Any
import time

from ..network import NetworkEngine, EngineState
from ..network.topology import RING_TOPOLOGY
from .edcm import EDCM
from .memory_core import MemoryCore
from .zeta import zeta_inject, harmonic_resonance
from .sigma import sigma_encode


# === CONTRACTS ===
# id: pcna_engine_uses_network_handoff
#   given: PCNAEngine().heartbeat("x")
#   then: the legacy facade advances the canonical NetworkEngine and exposes network-backed ring_signals / network snapshot data
#   class: integration
#   call: a0p_skills.contracts.pcna_engine_uses_network_handoff_holds
# === END CONTRACTS ===


class PCNAEngine:
    """Compatibility facade for legacy callers, powered by ``NetworkEngine``."""

    def __init__(self, n_primes: int = 157, base_seed: int = 1):
        self.n_primes = n_primes
        self.base_seed = base_seed
        # Keep the historical test/dev escape hatch: a non-default n_primes
        # builds smaller rings. Default construction preserves canonical ring
        # sizes from RING_TOPOLOGY (Φ/Ψ/Ω=53, Θ=29, memory rings=19/17, Σ=41).
        n_override = None
        if n_primes != 157:
            n_override = {name: n_primes for name in RING_TOPOLOGY}
        self.network = NetworkEngine(n_override=n_override)
        self.ring_signals: dict[str, float] = {
            "phi": 0.0, "psi": 0.0, "omega": 0.0,
            "theta": 0.0, "sigma": 0.0, "epsilon": 0.0,
        }
        self.edcm = EDCM()
        self.memory = MemoryCore()
        self.tick_count: int = 0
        self.heartbeat_last_ms: int | None = None
        self._last_network_state: EngineState | None = None
        self._intent_log: list[str] = []
        self._response_log: list[dict[str, Any]] = []

    def _signals_from_network_state(self, state: EngineState) -> dict[str, float]:
        """Map canonical network state into the legacy scalar signal shape."""
        signals = {k: 0.0 for k in self.ring_signals}
        for name, contribution in state.coherence.contributions.items():
            if name in signals:
                signals[name] = round(float(contribution), 6)
        sigma_energy = state.coherence.observer_signal.get("sigma", 0.0)
        # Bound the observer energy into the legacy [0,1] band.
        signals["sigma"] = round(min(1.0, float(sigma_energy)), 6)
        # Legacy epsilon means dissonance. Use the tamper bit when Σ drifted,
        # otherwise expose the unclaimed coherence headroom.
        signals["epsilon"] = 1.0 if state.tamper.drifted else round(max(0.0, 1.0 - state.coherence.total), 6)
        return signals

    def _legacy_cores_snapshot(self) -> dict:
        """Legacy `cores` shape from the canonical network rings."""
        snap = self.network.snapshot()
        rings = snap.get("rings", {})
        return {
            name: {
                "label": name,
                "n_primes": rings.get(name, {}).get("n_seeds"),
                "aggregate_energy": rings.get(name, {}).get("aggregate_energy"),
                "source": "network",
            }
            for name in ("phi", "psi", "omega")
            if name in rings
        }

    def heartbeat(self, intent: str | None = None) -> dict:
        """Run one canonical network tick and return the legacy inspector shape."""
        self.tick_count += 1
        now_ms = int(time.time() * 1000)
        self.heartbeat_last_ms = now_ms

        state = self.network.heartbeat()
        self._last_network_state = state
        self.ring_signals = self._signals_from_network_state(state)

        intent_match = 0.7 if intent else 0.4
        edcm_scores = self.edcm.score(
            prompt_tokens=0,
            completion_tokens=0,
            ring_signals=self.ring_signals,
            intent_match=intent_match,
        )

        sig = sigma_encode(f"tick:{self.tick_count}:{intent or ''}:{self.network.baseline_digest_hex[:12]}")
        self.memory.push_st(f"σ:{sig[:8]} π:{self.ring_signals['phi']}")

        return {
            "tick": self.tick_count,
            "ts_ms": now_ms,
            "ring_signals": dict(self.ring_signals),
            "edcm": edcm_scores.as_dict(),
            "resonance": harmonic_resonance(list(self.ring_signals.values())),
            "memory": self.memory.snapshot(),
            "network": self.network.snapshot(),
            "cores": self._legacy_cores_snapshot(),
            "coherence": {
                "total": state.coherence.total,
                "contributions": dict(state.coherence.contributions),
                "observer_signal": dict(state.coherence.observer_signal),
            },
            "tamper": {
                "drifted": state.tamper.drifted,
                "baseline_hex": state.tamper.baseline_hex,
                "current_hex": state.tamper.current_hex,
                "drift_count": state.tamper.drift_count,
            },
        }

    def inject_memory(self, messages: list[dict]) -> list[dict]:
        return zeta_inject(messages, self.memory.snapshot())

    def snapshot(self) -> dict:
        return {
            "n_primes": self.n_primes,
            "tick_count": self.tick_count,
            "heartbeat_last_ms": self.heartbeat_last_ms,
            "ring_signals": dict(self.ring_signals),
            "network": self.network.snapshot(),
            "cores": self._legacy_cores_snapshot(),
            "edcm_latest": (self.edcm.latest().as_dict() if self.edcm.latest() else None),
            "memory": self.memory.snapshot(),
            "intent_count": len(self._intent_log),
            "response_count": len(self._response_log),
        }

    def push_intent(self, intent: str) -> None:
        text = intent[:280]
        self._intent_log.append(text)
        self.memory.push_lt(f"intent:{text[:120]}")

    def absorb_response(self, model_id: str, text: str, usage: dict[str, Any] | None = None) -> None:
        record = {"model": model_id, "text": text[:280], "usage": usage or {}}
        self._response_log.append(record)
        self.memory.push_st(f"resp:{model_id}:{text[:80]}")

# === CONTRACTS ===
# id: pcna_engine_impl_loads
#   given: module declares its msdmd canon
#   then: the module imports cleanly under the current interpreter
#   class: integration
#   call: a0p_skills.contracts.module_imports_cleanly_holds
# === END CONTRACTS ===
# ratios: loc_comments=70:64 imports_exports=9:1 calls_definitions=25:7
