# ratios: loc_comments=53:58 imports_exports=5:7 calls_definitions=12:8
# === MODULE_BUILD ===
# id: fiq_motion
#   module_name: motion
#   module_kind: engine
#   summary: core fiq flux equation F = χ_route · χ_audit · χ_support · χ_attention · P_ab · D_r(Φ_a − Φ_b); pure functions
#   owner: Erin Spencer
#   public_surface: chi_route, chi_audit, chi_support, chi_attention, permeability, potential, flux
#   internal_surface: _omega_S_lookup
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: a0p_skills.contracts.fiq_flux_equation_holds
#   rollout: default_enabled
#   rollback: revert file
#   canon_pinned: Φ_a^(S)(t) = ω_S^⊤ Π_S z_a(t) − ρ · L_a(t)  (C1 minus; C2 ω_S fixed at declaration)
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: fiq_motion_boundaries
#   summary: core fiq flux equation F = χ_route · χ_audit · χ_support · χ_attention · P_ab · D_r(Φ_a − Φ_b); pure functions
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: fiq_motion
#   summary: core fiq flux equation F = χ_route · χ_audit · χ_support · χ_attention · P_ab · D_r(Φ_a − Φ_b); pure functions
#   exposes: chi_route, chi_audit, chi_support, chi_attention, permeability, potential, flux
#   boundaries: auth:none, storage:none, network:none, user_data:none
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: fiq_flux_equation
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.fiq_flux_equation_holds
# === END CONTRACTS ===
"""Core fiq flux equation — pure functions."""
from __future__ import annotations
from collections.abc import Sequence

from .gate import FiqGate
from .ficks import ficks


def chi_route(route_table: dict, gate: FiqGate) -> int:
    """1 iff a route exists between a and b under support S; else 0."""
    key = (gate.a, gate.b, gate.support)
    return 1 if route_table.get(key) else 0


def chi_audit(audit_clearance: dict, gate: FiqGate) -> int:
    """1 iff the audit lane has clearance for this gate; else 0."""
    return 1 if audit_clearance.get(gate.support) else 0


def chi_support(declared_supports: set[str], gate: FiqGate) -> int:
    """1 iff the gate's support is among declared supports for both a and b; else 0."""
    return 1 if gate.support in declared_supports else 0


def chi_attention(attention_state: dict, stratum: str, tick_ms: int) -> int:
    """1 iff the relevant stratum's attention fires at this tick."""
    from .tick_schedule import attention_fires
    if not attention_state.get(stratum, True):
        return 0
    return 1 if attention_fires(stratum, tick_ms) else 0


def permeability(p_max: float, declared: float | None) -> float:
    """Permeability is capped at p_max; declared overrides up to ceiling."""
    if declared is None:
        return p_max
    return max(0.0, min(float(p_max), float(declared)))


def _omega_S_lookup(omega_table: dict, support: str) -> Sequence[float]:
    """ω_S is fixed at support declaration time (C2). Caller supplies the table."""
    if support not in omega_table:
        raise ValueError(f"ω_S not declared for support {support!r}")
    return omega_table[support]


def potential(
    omega_table: dict,
    support: str,
    z_a: Sequence[float],
    L_a: float,
    rho: float = 1.0,
) -> float:
    """Φ_a^(S)(t) = ω_S^⊤ z_a(t) − ρ · L_a(t).

    Π_S (the support's projection matrix) is assumed pre-applied to z_a by
    the caller. C1: load penalty subtracts. C2: ω_S is looked up from the
    table declared at support-declaration time.
    """
    omega_S = _omega_S_lookup(omega_table, support)
    if len(omega_S) != len(z_a):
        raise ValueError(
            f"ω_S length {len(omega_S)} != z_a length {len(z_a)} for support {support!r}"
        )
    return sum(w * z for w, z in zip(omega_S, z_a)) - rho * L_a


def flux(
    gate: FiqGate,
    *,
    chi_r: int,
    chi_a: int,
    chi_s: int,
    chi_att: int,
    P_ab: float,
    phi_a: float,
    phi_b: float,
    D_r: float = 1.0,
) -> float:
    """F_{a→b}^(S)(t) = χ_route · χ_audit · χ_support · χ_attention · P_ab · D_r(Φ_a − Φ_b).

    All χ indicators must be 1 for non-zero flux. P_ab is bounded by the
    permeability ceiling at the gate.
    """
    gate_open = chi_r * chi_a * chi_s * chi_att
    if not gate_open:
        return 0.0
    return float(gate_open) * float(P_ab) * ficks(phi_a, phi_b, D_r)
# ratios: loc_comments=53:58 imports_exports=5:7 calls_definitions=12:8
