# ratios: loc_comments=5:51 imports_exports=1:2 calls_definitions=3:2
# === MODULE_BUILD ===
# id: fiq_ficks_gradient
#   module_name: ficks
#   module_kind: engine
#   summary: ficks — gradient term D_r(Φ_a − Φ_b) in the fiq flux equation; named after Fick's law of diffusion; resolves "tics-per-tok" framing as the gradient of fiq tics per LLM token
#   owner: Erin Spencer
#   public_surface: ficks, gradient_potential
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: a0p_skills.contracts.ficks_gradient_holds
#   rollout: default_enabled
#   rollback: revert file
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: fiq_ficks_gradient_boundaries
#   summary: ficks — gradient term D_r(Φ_a − Φ_b) in the fiq flux equation; named after Fick's law of diffusion; resolves "tics-per-tok" framing as the gradient of fiq tics per LLM token
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: fiq_ficks_gradient
#   summary: ficks — gradient term D_r(Φ_a − Φ_b) in the fiq flux equation; named after Fick's law of diffusion; resolves "tics-per-tok" framing as the gradient of fiq tics per LLM token
#   exposes: ficks, gradient_potential
#   boundaries: auth:none, storage:none, network:none, user_data:none
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: ficks_gradient
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.ficks_gradient_holds
# === END CONTRACTS ===
"""ficks — the gradient term in the fiq flux equation.

Per user spec: tics-per-tok IS ficks. The gradient of fiq tics per LLM
token is exactly the gradient term D_r(Φ_a − Φ_b) in Fick's law of
diffusion. This module is the canonical computer.
"""
from __future__ import annotations


def ficks(phi_a: float, phi_b: float, D_r: float = 1.0) -> float:
    """The gradient term: D_r · (Φ_a − Φ_b).

    Positive when the source potential exceeds the target; this is the
    direction in which flux flows.
    """
    return float(D_r) * (float(phi_a) - float(phi_b))


def gradient_potential(phi_a: float, phi_b: float) -> float:
    """Bare gradient Φ_a − Φ_b without diffusion coefficient. Useful for tics-per-tok ratio reads."""
    return float(phi_a) - float(phi_b)
# ratios: loc_comments=5:51 imports_exports=1:2 calls_definitions=3:2
