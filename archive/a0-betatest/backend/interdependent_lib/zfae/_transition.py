# ratios: loc_comments=103:64 imports_exports=10:4 calls_definitions=27:7
# === MODULE_BUILD ===
# id: zfae_state_transition
#   module_name: _transition
#   module_kind: engine
#   summary: ZFAE transition rules — folds semantic features into Φ/Ψ/Ω ring snapshots via PCEA kernel cross-cut; produces nextSnapshot
#   owner: a0p maintainer
#   public_surface: bind_features_to_rings, advance_zfae_state, snapshot_after, ZFAE_RING_NAMES
#   internal_surface: _feature_tensor_for, _intent_hash
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: a0p_skills.contracts.zfae_transition_deterministic_holds
#   rollout: default_enabled
#   rollback: revert file from git
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: zfae_state_transition_boundaries
#   summary: ZFAE transition rules — folds semantic features into Φ/Ψ/Ω ring snapshots via PCEA kernel cross-cut; produces nextSnapshot
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: zfae_state_transition
#   summary: ZFAE transition rules — folds semantic features into Φ/Ψ/Ω ring snapshots via PCEA kernel cross-cut; produces nextSnapshot
#   exposes: bind_features_to_rings, advance_zfae_state, snapshot_after, ZFAE_RING_NAMES
#   boundaries: auth:none, storage:none, network:none, user_data:read
#   owner: a0p maintainer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: zfae_transition_deterministic
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.zfae_transition_deterministic_holds
# === END CONTRACTS ===
"""ZFAE state transition — the math of "this state, last state" for the agent.

Inputs:  the parsed semantic features + the prior ring/memory snapshot.
Output:  the next-state snapshot, with Φ/Ψ/Ω advanced via PCEA kernel cross-cut.

This is a pure function — same inputs → same outputs. No randomness,
no external services, no LLM.
"""
from __future__ import annotations
import hashlib
from typing import Any

from ..pcna.tensor import Tensor, zero_tensor
from ..pcea.kernel import kernel_step, grid_project
from ..pcna.group import aggregate as agg7
from ._parser import SemanticFeatures
from ._intent import IntentLabel


ZFAE_RING_NAMES: tuple[str, ...] = ("phi", "psi", "omega")


def _intent_hash(features: SemanticFeatures, intent: IntentLabel) -> str:
    h = hashlib.blake2b(
        f"{intent}::{','.join(features.tokens)}::{features.semantic_load}".encode(),
        digest_size=8,
    )
    return h.hexdigest()


def _feature_tensor_for(
    role: str,
    features: SemanticFeatures,
    intent: IntentLabel,
) -> Tensor:
    """Produce a deterministic per-role Tensor from features + intent."""
    salt = f"zfae::{role}::{intent}::{','.join(features.tokens)}"
    seed = int(hashlib.blake2b(salt.encode(), digest_size=4).hexdigest(), 16)
    return Tensor.from_seed(seed, salt)


def _as_tensor(value: Any, fallback_label: str) -> Tensor:
    """Coerce phi/psi/omega/etc. inputs into Tensor, falling back to zero."""
    if isinstance(value, Tensor):
        return value
    if isinstance(value, dict):
        # Accept a snapshot dict with payload list
        payload = value.get("payload")
        if isinstance(payload, (list, tuple)) and len(payload) > 0:
            try:
                from ..pcna.tensor import TENSOR_DIM
                if len(payload) == TENSOR_DIM:
                    return Tensor(payload)
            except Exception:
                pass
    if isinstance(value, (list, tuple)):
        from ..pcna.tensor import TENSOR_DIM
        if len(value) == TENSOR_DIM:
            return Tensor(list(value))
    # Final fallback — deterministic identity tied to the label
    return Tensor.from_seed(0, fallback_label)


def bind_features_to_rings(
    features: SemanticFeatures,
    intent: IntentLabel,
    *,
    phi: Any = None,
    psi: Any = None,
    omega: Any = None,
) -> dict[str, Tensor]:
    """Mix the semantic features into Φ Ψ Ω ring states (no mutation; returns new Tensors).

    Each role gets a feature tensor blended with its prior state via
    PCNA's 7-fold aggregate (mean), which is the same op the substrate
    uses at every layer. The blend is deterministic.
    """
    out: dict[str, Tensor] = {}
    for role, prior in (("phi", phi), ("psi", psi), ("omega", omega)):
        prior_tensor = _as_tensor(prior, fallback_label=f"zfae::{role}::prior")
        feature_tensor = _feature_tensor_for(role, features, intent)
        # Blend: deterministic mean of 7 components — six copies of feature
        # tensor plus one copy of the prior. Weighting biases toward novelty
        # without erasing memory.
        components = [feature_tensor] * 6 + [prior_tensor]
        out[role] = agg7(components)
    return out


def advance_zfae_state(
    bound: dict[str, Tensor],
    *,
    last_state: dict[str, Tensor] | None = None,
) -> dict[str, Tensor]:
    """Apply the PCEA kernel cross-cut: encrypt each new ring state against the prior."""
    last_state = last_state or {}
    encrypted: dict[str, Tensor] = {}
    for role, plain in bound.items():
        prev_key = last_state.get(role) or zero_tensor()
        encrypted[role] = kernel_step(plain, prev_key)
    return encrypted


def snapshot_after(
    features: SemanticFeatures,
    intent: IntentLabel,
    bound: dict[str, Tensor],
    ciphertexts: dict[str, Tensor],
    *,
    prior_snapshot: dict | None = None,
    tick_number: int | None = None,
    extras: dict | None = None,
) -> dict:
    """Build the nextSnapshot dict — JSON-serialisable view of agent state.

    Stores PLAINTEXT Tensors' payloads (the cipher field also kept for replay).
    The next call's caller can pass this back as `last_state` payload dicts.
    """
    prior_snapshot = prior_snapshot or {}
    extras = extras or {}
    tick = tick_number if tick_number is not None else int(prior_snapshot.get("tick", 0)) + 1

    def tensor_payload(t: Tensor) -> list[float]:
        return list(t.payload)

    plaintexts_view = {role: tensor_payload(grid_project(t)) for role, t in bound.items()}
    ciphertexts_view = {role: tensor_payload(t) for role, t in ciphertexts.items()}

    snapshot = {
        "tick": tick,
        "intent": intent,
        "intent_hash": _intent_hash(features, intent),
        "features": features.to_dict(),
        "phi": plaintexts_view.get("phi"),
        "psi": plaintexts_view.get("psi"),
        "omega": plaintexts_view.get("omega"),
        "phi_cipher": ciphertexts_view.get("phi"),
        "psi_cipher": ciphertexts_view.get("psi"),
        "omega_cipher": ciphertexts_view.get("omega"),
    }
    snapshot.update(extras)
    return snapshot


__all__ = [
    "ZFAE_RING_NAMES",
    "bind_features_to_rings",
    "advance_zfae_state",
    "snapshot_after",
]
# ratios: loc_comments=103:64 imports_exports=10:4 calls_definitions=27:7
