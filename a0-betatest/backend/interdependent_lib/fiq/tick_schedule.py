# ratios: loc_comments=29:59 imports_exports=3:3 calls_definitions=7:4
# === MODULE_BUILD ===
# id: fiq_tick_schedule
#   module_name: tick_schedule
#   module_kind: schema
#   summary: ψ/φ/ω consciousness-prime tick constants (3/5/7); orthogonal stratum + core attention axes; logical default with optional real-time toggle
#   owner: Erin Spencer
#   public_surface: PSI_MS, PHI_MS, OMEGA_MS, TICK_SCHEDULE, LCM_TABLE, attention_fires, fully_aligned, RealtimeToggle
#   internal_surface: _lcm
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: a0p_skills.contracts.fiq_tick_schedule_canon_holds
#   rollout: default_enabled
#   rollback: revert to ad-hoc tick counter
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: fiq_tick_schedule_boundaries
#   summary: ψ/φ/ω consciousness-prime tick constants (3/5/7); orthogonal stratum + core attention axes; logical default with optional real-time toggle
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: fiq_tick_schedule
#   summary: ψ/φ/ω consciousness-prime tick constants (3/5/7); orthogonal stratum + core attention axes; logical default with optional real-time toggle
#   exposes: PSI_MS, PHI_MS, OMEGA_MS, TICK_SCHEDULE, LCM_TABLE, attention_fires, fully_aligned, RealtimeToggle
#   boundaries: auth:none, storage:none, network:none, user_data:none
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: fiq_tick_schedule_canon
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.fiq_tick_schedule_canon_holds
# === END CONTRACTS ===
"""Tick schedule canon.

ψ (tensor stratum)   Δt = 3 ms — fastest stratum (PCNA leaves)
φ (circle stratum)   Δt = 5 ms — middle stratum (PCTA circles)
ω (seed stratum)     Δt = 7 ms — slowest stratum (PTCA seeds)

3 · 5 · 7 mutually coprime → no two cores of different tick identities
ever coincide outside their LCM intervals. Stratum tick (movement
between adjacent strata) and core attention (within-stratum
propagation) are orthogonal axes; both must fire for a transfer to
proceed.

Logical default: ticks are integer counters; ψ fires on tick % 3 == 0,
φ on tick % 5 == 0, ω on tick % 7 == 0. A RealtimeToggle attaches an
asyncio wall-clock loop when needed.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import gcd

PSI_MS: int = 3
PHI_MS: int = 5
OMEGA_MS: int = 7


def _lcm(a: int, b: int) -> int:
    return a * b // gcd(a, b)


TICK_SCHEDULE: dict[str, int] = {
    "psi": PSI_MS,
    "phi": PHI_MS,
    "omega": OMEGA_MS,
}

LCM_TABLE: dict[tuple[str, str], int] = {
    ("psi", "phi"): _lcm(PSI_MS, PHI_MS),         # 15
    ("psi", "omega"): _lcm(PSI_MS, OMEGA_MS),     # 21  ← fiques time
    ("phi", "omega"): _lcm(PHI_MS, OMEGA_MS),     # 35
    ("psi", "phi", "omega"): _lcm(_lcm(PSI_MS, PHI_MS), OMEGA_MS),  # 105
}


def attention_fires(stratum: str, tick_ms: int) -> bool:
    """True iff the given stratum's attention fires at this absolute tick (ms)."""
    if stratum not in TICK_SCHEDULE:
        raise ValueError(f"unknown stratum {stratum!r}; expected one of {tuple(TICK_SCHEDULE)}")
    return tick_ms % TICK_SCHEDULE[stratum] == 0


def fully_aligned(strata: tuple[str, ...], tick_ms: int) -> bool:
    """True iff every stratum's attention fires at this tick (LCM-aligned)."""
    return all(attention_fires(s, tick_ms) for s in strata)


@dataclass
class RealtimeToggle:
    """Optional real-time scheduler — wall-clock alignment for debug/inspection.

    When enabled, an asyncio loop sleeps until the next stratum tick. Off by default.
    """
    enabled: bool = False
    base_unit_ms: int = 1
# ratios: loc_comments=29:59 imports_exports=3:3 calls_definitions=7:4
