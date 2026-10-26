# ratios: loc_comments=99:50 imports_exports=7:7 calls_definitions=15:10
# === MODULE_BUILD ===
# id: network_coherence
#   module_name: coherence
#   module_kind: engine
#   summary: EDCM-style coherence scoring — weights each scored ring's aggregate energy, sums to a total; tracks Σ digest drift as tamper signal (pen-test resistance)
#   owner: a0p maintainer
#   public_surface: CoherenceScore, TamperReport, score_tick, evaluate_tamper, ring_energy
#   internal_surface: _normalize
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: a0p_skills.contracts.network_coherence_weights_sum_holds
#   rollout: default_enabled
#   rollback: revert file from git
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: network_coherence_boundaries
#   summary: EDCM-style coherence scoring — weights each scored ring's aggregate energy, sums to a total; tracks Σ digest drift as tamper signal (pen-test resistance)
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: network_coherence
#   summary: EDCM-style coherence scoring — weights each scored ring's aggregate energy, sums to a total; tracks Σ digest drift as tamper signal (pen-test resistance)
#   exposes: CoherenceScore, TamperReport, score_tick, evaluate_tamper, ring_energy
#   boundaries: auth:none, storage:none, network:none, user_data:read
#   owner: a0p maintainer
# === END CAPABILITIES ===
"""Coherence scoring + Σ drift / tamper evidence."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Iterable

from ..pcna.tensor import Tensor
from .topology import RING_TOPOLOGY, SCORED_RING_NAMES, RING_WEIGHTS
from .propagate import TickResult
from .sigma_source import HostDigest


# === CONTRACTS ===
# id: network_coherence_weights_sum
#   given: score_tick(tick_result) applied to a heartbeat
#   then: coherence.total == sum(contributions); Σ goes into observer_signal not contributions; every scored ring contributes
#   class: correctness
#   call: a0p_skills.contracts.network_coherence_weights_sum_holds
# === END CONTRACTS ===


def ring_energy(t: Tensor) -> float:
    """Convenience — Tensor L2 energy used in scoring."""
    return t.energy()


def _normalize(energies: dict[str, float]) -> dict[str, float]:
    """Min-max normalize across scored rings, so scoring isn't dominated by one ring."""
    if not energies:
        return {}
    lo = min(energies.values())
    hi = max(energies.values())
    span = hi - lo
    if span <= 0:
        return {k: 0.5 for k in energies}
    return {k: (v - lo) / span for k, v in energies.items()}


@dataclass
class CoherenceScore:
    tick_number: int
    contributions: dict[str, float] = field(default_factory=dict)  # ring → weighted normalized energy
    total: float = 0.0
    observer_signal: dict[str, float] = field(default_factory=dict)  # Σ observer (un-weighted)


def score_tick(tick: TickResult) -> CoherenceScore:
    """Compute the weighted coherence sum for one TickResult.

    Σ contributes to `observer_signal` (un-weighted, surfaced separately).
    """
    raw_energies: dict[str, float] = {}
    observer_energies: dict[str, float] = {}

    for name, rt in tick.rings.items():
        e = ring_energy(rt.plaintext_aggregate)
        spec = RING_TOPOLOGY[name]
        if spec.scored:
            raw_energies[name] = e
        else:
            observer_energies[name] = e

    normalized = _normalize(raw_energies)
    contributions: dict[str, float] = {}
    total = 0.0
    for name, n_val in normalized.items():
        w = RING_WEIGHTS[name]
        contrib = n_val * w
        contributions[name] = contrib
        total += contrib

    return CoherenceScore(
        tick_number=tick.tick_number,
        contributions=contributions,
        total=total,
        observer_signal=observer_energies,
    )


@dataclass
class TamperReport:
    """Result of Σ digest drift evaluation."""
    drifted: bool                       # True if Σ digest changed since baseline
    baseline_hex: str
    current_hex: str
    drift_count: int = 0                # how many distinct digests seen in this session
    last_drift_tick: int | None = None


class TamperWatcher:
    """Tracks Σ digest history across ticks. Emits a TamperReport on demand."""

    def __init__(self, baseline: HostDigest):
        self._baseline_hex: str = baseline.digest_hex
        self._last_hex: str = baseline.digest_hex
        self._seen: set[str] = {baseline.digest_hex}
        self._last_drift_tick: int | None = None

    @property
    def baseline_hex(self) -> str:
        return self._baseline_hex

    def evaluate(self, current: HostDigest, tick_number: int) -> TamperReport:
        cur_hex = current.digest_hex
        drifted = cur_hex != self._baseline_hex
        if cur_hex != self._last_hex:
            self._seen.add(cur_hex)
            self._last_drift_tick = tick_number
            self._last_hex = cur_hex
        return TamperReport(
            drifted=drifted,
            baseline_hex=self._baseline_hex,
            current_hex=cur_hex,
            drift_count=max(0, len(self._seen) - 1),
            last_drift_tick=self._last_drift_tick,
        )


def evaluate_tamper(
    baseline: HostDigest,
    current: HostDigest,
    tick_number: int = 0,
) -> TamperReport:
    """One-shot drift check (no history)."""
    drifted = current.digest_hex != baseline.digest_hex
    return TamperReport(
        drifted=drifted,
        baseline_hex=baseline.digest_hex,
        current_hex=current.digest_hex,
        drift_count=1 if drifted else 0,
        last_drift_tick=tick_number if drifted else None,
    )


__all__ = [
    "CoherenceScore",
    "TamperReport",
    "TamperWatcher",
    "ring_energy",
    "score_tick",
    "evaluate_tamper",
]
# ratios: loc_comments=99:50 imports_exports=7:7 calls_definitions=15:10
