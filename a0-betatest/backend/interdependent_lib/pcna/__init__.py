# ratios: loc_comments=15:54 imports_exports=6:1 calls_definitions=0:0
# === MODULE_BUILD ===
# id: pcna_pkg
#   module_name: pcna
#   module_kind: engine
#   summary: six-ring inference engine (Φ Ψ Ω Θ Σ Ε) — legacy public facade backed by the canonical 61-seed network handoff
#   owner: a0p maintainer
#   public_surface: PCNAEngine, EDCM, EDCMScores, MemoryCore, zeta_inject, sigma_encode, theta_modulate
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: a0p_skills.contracts.pcna_engine_uses_network_handoff_holds
#   rollout: default_enabled
#   rollback: revert subpackage from git
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: pcna_pkg_boundaries
#   summary: six-ring inference engine (Φ Ψ Ω Θ Σ Ε) — legacy public facade backed by the canonical 61-seed network handoff
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: pcna_pkg
#   summary: six-ring inference engine (Φ Ψ Ω Θ Σ Ε) — legacy public facade backed by the canonical 61-seed network handoff
#   exposes: PCNAEngine, EDCM, EDCMScores, MemoryCore, zeta_inject, sigma_encode, theta_modulate
#   boundaries: auth:none, storage:none, network:none, user_data:none
#   owner: a0p maintainer
# === END CAPABILITIES ===
"""
PCNA — Prime Circled Neural Architecture.

Modular inference engine — six rings:
    Φ (phi)   — primary intent / surface ring
    Ψ (psi)   — substrate / filesystem-aligned ring (via sigma)
    Ω (omega) — outward broadcast / consensus ring
    Θ (theta) — modulation / phase ring
    Memory-L  — long-term memory (N=19 prime ring)
    Memory-S  — short-term memory (N=17 prime ring)

The canonical `NetworkEngine` now drives heartbeat state; this package keeps the legacy `PCNAEngine` facade and helper exports for compatibility.

"""
from .pcna import PCNAEngine
from .edcm import EDCM, EDCMScores
from .zeta import zeta_inject
from .sigma import sigma_encode
from .theta import theta_modulate
from .memory_core import MemoryCore

__all__ = [
    "PCNAEngine",
    "EDCM",
    "EDCMScores",
    "zeta_inject",
    "sigma_encode",
    "theta_modulate",
    "MemoryCore",
]

# === CONTRACTS ===
# id: pcna_pkg_loads
#   given: module declares its msdmd canon
#   then: the module imports cleanly under the current interpreter
#   class: integration
#   call: a0p_skills.contracts.module_imports_cleanly_holds
# === END CONTRACTS ===
# ratios: loc_comments=15:54 imports_exports=6:1 calls_definitions=0:0
