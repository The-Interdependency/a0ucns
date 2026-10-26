# ratios: loc_comments=26:54 imports_exports=6:1 calls_definitions=3:0
# === MODULE_BUILD ===
# id: fiq_pkg
#   module_name: fiq
#   module_kind: engine
#   summary: fiq motion canon — boundary law for audited motion between PCNA/PCTA/PTCA strata; tick schedule (3/5/7); χ indicators; FIQ_TRANSFER/BUFFERED/BLOCKED events; sentinels S1-S9, R0, fiques_time
#   owner: Erin Spencer
#   public_surface: FiqGate, flux, chi_route, chi_audit, chi_support, chi_attention, ficks, FIQ_TRANSFER, FIQ_BUFFERED, FIQ_BLOCKED, AuditLog, TICK_SCHEDULE, PSI_MS, PHI_MS, OMEGA_MS, attention_fires
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: read
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: a0p_skills.contracts.fiq_pkg_exports_holds
#   rollout: default_enabled
#   rollback: detach Tier-2/Tier-1 emitters and revert imports
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: fiq_pkg_boundaries
#   summary: fiq motion canon — boundary law for audited motion between PCNA/PCTA/PTCA strata; tick schedule (3/5/7); χ indicators; FIQ_TRANSFER/BUFFERED/BLOCKED events; sentinels S1-S9, R0, fiques_time
#   auth_boundary: none
#   storage_boundary: read
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: fiq_pkg
#   summary: fiq motion canon — boundary law for audited motion between PCNA/PCTA/PTCA strata; tick schedule (3/5/7); χ indicators; FIQ_TRANSFER/BUFFERED/BLOCKED events; sentinels S1-S9, R0, fiques_time
#   exposes: FiqGate, flux, chi_route, chi_audit, chi_support, chi_attention, ficks, FIQ_TRANSFER, FIQ_BUFFERED, FIQ_BLOCKED, AuditLog, TICK_SCHEDULE, PSI_MS, PHI_MS, OMEGA_MS, attention_fires
#   boundaries: auth:none, storage:read, network:none, user_data:none
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: fiq_pkg_exports
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.fiq_pkg_exports_holds
# === END CONTRACTS ===
"""fiq motion canon.

Etymology — pinned for the first entry per user spec:
  fiq        singular  — one auditable boundary gate / event
  fiques     plural    — many fiqs in flight
  fiques time         — sentinel probe; ψ-core in ω-stratum (LCM 21ms) watching fiques over time
  ficks      gradient  — D_r(Φ_a − Φ_b); named after Fick's law of diffusion (flux ∝ gradient).
                          Resolves the "tics-per-tok" framing: ficks is the gradient of fiq tics
                          per LLM token. Scrabble noted as a minor planning influence on
                          letter-value, scarcity, and positional-load thinking.

Canon equation (locked):
  Φ_a^(S)(t) = ω_S^⊤ Π_S z_a(t) − ρ · L_a(t)     (C1: minus locked; C2: ω_S fixed at declaration)
  F_{a→b}^(S)(t) = χ_route · χ_audit · χ_support · χ_attention · P_ab · D_r(Φ_a − Φ_b)
"""
from .tick_schedule import (
    PSI_MS, PHI_MS, OMEGA_MS, TICK_SCHEDULE, LCM_TABLE,
    attention_fires, fully_aligned,
)
from .gate import FiqGate, GateMode
from .motion import (
    chi_route, chi_audit, chi_support, chi_attention,
    permeability, potential, flux,
)
from .ficks import ficks, gradient_potential
from .events import (
    FIQ_TRANSFER, FIQ_BUFFERED, FIQ_BLOCKED,
    AuditEvent, chain_hash, verify_chain,
)
from .audit import AuditLog

__all__ = [
    "PSI_MS", "PHI_MS", "OMEGA_MS", "TICK_SCHEDULE", "LCM_TABLE",
    "attention_fires", "fully_aligned",
    "FiqGate", "GateMode",
    "chi_route", "chi_audit", "chi_support", "chi_attention",
    "permeability", "potential", "flux",
    "ficks", "gradient_potential",
    "FIQ_TRANSFER", "FIQ_BUFFERED", "FIQ_BLOCKED",
    "AuditEvent", "chain_hash", "verify_chain",
    "AuditLog",
]
# ratios: loc_comments=26:54 imports_exports=6:1 calls_definitions=3:0
