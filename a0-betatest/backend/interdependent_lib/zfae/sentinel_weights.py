# ratios: loc_comments=52:55 imports_exports=3:4 calls_definitions=14:3
# === MODULE_BUILD ===
# id: zfae_sentinel_weights
#   module_name: sentinel_weights
#   module_kind: schema
#   summary: per-agent sentinel weight resolution — default 0.90 attention budget distributed across 13 sentinels; user-editable; under-budget reverts to inference channel
#   owner: Erin Spencer
#   public_surface: SENTINEL_WEIGHTS_DEFAULT, INFERENCE_CHANNEL_DEFAULT, validate_weights, resolve_weights, inference_channel
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: a0p_skills.contracts.sentinel_weights_default_sum_holds
#   rollout: default_enabled
#   rollback: revert file; all sentinels equal-weighted
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: zfae_sentinel_weights_boundaries
#   summary: pure validation + merge
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: zfae_sentinel_weights
#   summary: defaults + per-agent override + inference channel residual
#   exposes: SENTINEL_WEIGHTS_DEFAULT, validate_weights, resolve_weights, inference_channel
#   boundaries: auth:none, storage:none, network:none, user_data:read
#   owner: Erin Spencer
# === END CAPABILITIES ===
"""Per-agent sentinel-weight defaults and resolution.

Canon attention budget: 1.0 total.
Default sentinel share: 0.90 (= sum of the 13 defaults below).
Inference channel: 1.0 − sum(active sentinel weights) − sum(off-mode sentinel weights).

User edits never silently upscale. Under-budget weights revert to inference channel.
"""
from __future__ import annotations
from .sentinels import all_names
from .sentinel_modes import SentinelMode


INFERENCE_CHANNEL_DEFAULT: float = 0.10

SENTINEL_WEIGHTS_DEFAULT: dict[str, float] = {
    "S1":  0.07,
    "S2":  0.07,
    "S3":  0.10,
    "S4":  0.05,
    "S5":  0.10,
    "S6":  0.08,
    "S7":  0.06,
    "S8":  0.06,
    "S9":  0.05,
    "S10": 0.08,
    "S11": 0.07,
    "S12": 0.05,
    "S13": 0.06,
}
# Sum: 0.90 (the canonical sentinel attention budget by default)


def validate_weights(weights: dict[str, float]) -> dict[str, float]:
    """Coerce + bounds-check a partial weight override. Each weight ∈ [0, 1]."""
    valid_keys = set(all_names())
    out: dict[str, float] = {}
    for k, v in weights.items():
        if k not in valid_keys:
            raise ValueError(f"unknown sentinel name {k!r}; expected one of S1..S13")
        f = float(v)
        if f < 0.0 or f > 1.0:
            raise ValueError(f"sentinel {k} weight {f} outside [0, 1]")
        out[k] = f
    return out


def resolve_weights(agent_weights: dict[str, float] | None) -> dict[str, float]:
    """Merge defaults with partial override; clamp total to ≤ 1.0; do not upscale."""
    resolved = dict(SENTINEL_WEIGHTS_DEFAULT)
    if agent_weights:
        resolved.update(validate_weights(agent_weights))
    total = sum(resolved.values())
    if total > 1.0:
        # Defensive: scale DOWN if user goes over; never upscale.
        scale = 1.0 / total
        resolved = {k: v * scale for k, v in resolved.items()}
    return resolved


def inference_channel(
    resolved_weights: dict[str, float],
    resolved_modes: dict[str, SentinelMode],
) -> float:
    """Compute the inference channel = 1.0 − sum(weights of active sentinels).

    Off-mode sentinels' weights revert to the inference channel (they don't compute).
    Observe/flag-mode sentinels' weights stay in the sentinel channel.
    """
    sentinel_total = sum(
        w for name, w in resolved_weights.items()
        if resolved_modes.get(name, SentinelMode.OBSERVE) != SentinelMode.OFF
    )
    return max(0.0, min(1.0, 1.0 - sentinel_total))


__all__ = [
    "SENTINEL_WEIGHTS_DEFAULT", "INFERENCE_CHANNEL_DEFAULT",
    "validate_weights", "resolve_weights", "inference_channel",
]

# === CONTRACTS ===
# id: zfae_sentinel_weights_loads
#   given: module declares its msdmd canon
#   then: the module imports cleanly under the current interpreter
#   class: integration
#   call: a0p_skills.contracts.module_imports_cleanly_holds
# === END CONTRACTS ===

# ratios: loc_comments=52:55 imports_exports=3:4 calls_definitions=14:3
