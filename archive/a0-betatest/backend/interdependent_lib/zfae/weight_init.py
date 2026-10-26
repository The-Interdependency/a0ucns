# ratios: loc_comments=39:65 imports_exports=3:4 calls_definitions=10:5
# === MODULE_BUILD ===
# id: zfae_weight_init
#   module_name: weight_init
#   module_kind: engine
#   summary: deterministic seed init for fresh ZFAE weights; three cores phi/psi/omega each shape (157, 53, 7, 7); per-agent reproducible
#   owner: Erin Spencer
#   public_surface: seed_initial_weights, seed_initial_three_core, seed_initial_gonal, CORE_NAMES, WEIGHT_SHAPE, WEIGHT_COUNT, WEIGHT_COUNT_PER_CORE, WEIGHT_COUNT_TOTAL, GONAL_SEED_WIDTH, default_metadata
#   internal_surface: _seeded_rng
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: a0p_skills.contracts.zfae_weight_init_deterministic_holds
#   rollout: default_enabled
#   rollback: revert file
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: zfae_weight_init_boundaries
#   summary: deterministic seed init for fresh ZFAE weights; three cores phi/psi/omega each shape (157, 53, 7, 7)
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: zfae_weight_init
#   summary: deterministic seed init for fresh ZFAE weights; three cores phi/psi/omega each shape (157, 53, 7, 7)
#   exposes: seed_initial_weights, seed_initial_three_core, CORE_NAMES, WEIGHT_SHAPE, WEIGHT_COUNT, WEIGHT_COUNT_PER_CORE, WEIGHT_COUNT_TOTAL, default_metadata
#   boundaries: auth:none, storage:none, network:none, user_data:read
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: zfae_weight_init_deterministic
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.zfae_weight_init_deterministic_holds
# === END CONTRACTS ===
"""Deterministic ZFAE weight initialization.

Per user spec — three 157-seed cores (phi, psi, omega):
  ZFAE_WEIGHT_SHAPE       = [157, 53, 7, 7]     per core
  WEIGHT_COUNT_PER_CORE   = 407_729
  WEIGHT_COUNT_TOTAL      = 1_223_187           (= 3 × 407_729)

Each core's storage order is (seeds, payload_width, circles, tensors_per_circle).
"""
from __future__ import annotations
import hashlib
import numpy as np

WEIGHT_SHAPE: tuple[int, int, int, int] = (157, 53, 7, 7)
WEIGHT_COUNT_PER_CORE: int = 157 * 53 * 7 * 7   # 407_729
# Backwards-compatible alias for the per-core count.
WEIGHT_COUNT: int = WEIGHT_COUNT_PER_CORE
CORE_NAMES: tuple[str, str, str] = ("phi", "psi", "omega")
WEIGHT_COUNT_TOTAL: int = WEIGHT_COUNT_PER_CORE * len(CORE_NAMES)   # 1_223_187


def _seeded_rng(agent_id: str, salt: str = "zfae_seed_init") -> np.random.Generator:
    """Deterministic numpy Generator keyed on agent_id."""
    seed_bytes = hashlib.blake2b(f"{salt}::{agent_id}".encode(), digest_size=8).digest()
    seed_int = int.from_bytes(seed_bytes, "big")
    return np.random.default_rng(seed_int)


def seed_initial_weights(agent_id: str, core: str = "phi") -> np.ndarray:
    """Produce a deterministic (157, 53, 7, 7) ndarray seeded from `agent_id`+`core`.

    Values in roughly [-0.5, +0.5]; small magnitude so the untrained weight
    bank is closer to identity than to chaos. Same `(agent_id, core)` always
    produces the same weights. Default core 'phi' preserves the prior single-core
    behaviour.
    """
    if core not in CORE_NAMES:
        raise ValueError(f"unknown core {core!r}; expected one of {CORE_NAMES}")
    rng = _seeded_rng(agent_id, salt=f"zfae_seed_init::{core}")
    return rng.uniform(-0.5, 0.5, size=WEIGHT_SHAPE).astype(np.float32)


def seed_initial_three_core(agent_id: str) -> dict[str, np.ndarray]:
    """Produce the three deterministic cores for `agent_id`."""
    return {name: seed_initial_weights(agent_id, core=name) for name in CORE_NAMES}


# Width of the private-gonal seed vector — the 4th persisted safetensors tensor.
GONAL_SEED_WIDTH: int = 53


def seed_initial_gonal(agent_id: str) -> np.ndarray:
    """Deterministic private-gonal seed vector (width 53) for `agent_id`.

    This is the secret entropy that seeds the per-agent PrivateGonal (phase +
    permutation) used by the Route A Gonal Inscription decoder. Persisted as
    the 4th safetensors tensor alongside the three cores.
    """
    rng = _seeded_rng(agent_id, salt="zfae_gonal_seed")
    return rng.uniform(-0.5, 0.5, size=GONAL_SEED_WIDTH).astype(np.float32)


def default_metadata(agent_id: str, training_step: int = 0) -> dict[str, str]:
    """Canonical safetensors metadata dict (str-valued per format requirement)."""
    return {
        "architecture": "a0_zfae",
        "core_names": ",".join(CORE_NAMES),
        "weight_shape": str(list(WEIGHT_SHAPE)),
        "weight_count_per_core": str(WEIGHT_COUNT_PER_CORE),
        "weight_count_total": str(WEIGHT_COUNT_TOTAL),
        # legacy alias for older readers
        "weight_count": str(WEIGHT_COUNT_PER_CORE),
        "training_step": str(training_step),
        "seeds_touched_phi": "0",
        "seeds_touched_psi": "0",
        "seeds_touched_omega": "0",
        "agent_id": agent_id,
        "created_from": "seed_init_then_teacher_distillation",
        "teacher_models_seen": "[]",
    }
# ratios: loc_comments=39:65 imports_exports=3:4 calls_definitions=10:5
