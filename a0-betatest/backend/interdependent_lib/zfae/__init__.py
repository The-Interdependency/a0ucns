# ratios: loc_comments=58:53 imports_exports=9:2 calls_definitions=7:5
# === MODULE_BUILD ===
# id: zfae_pkg
#   module_name: zfae
#   module_kind: engine
#   summary: a0(ZFAE) — the inference provider, not an agent label. Exposes A0ZFAEInferenceEngine (native deterministic), plus the legacy ZFAEAgent persona for backward-compat with prior PCNAEngine wiring
#   owner: a0p maintainer
#   public_surface: A0ZFAEInferenceEngine, ENGINE, infer, InferenceResult, MISSING_NATIVE_MESSAGE, ZFAEAgent
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: a0p_skills.contracts.zfae_engine_native_only_holds
#   rollout: default_enabled
#   rollback: remove imports from server.py /api/chat/zfae route
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: zfae_pkg_boundaries
#   summary: a0(ZFAE) — the inference provider, not an agent label. Exposes A0ZFAEInferenceEngine (native deterministic), plus the legacy ZFAEAgent persona for backward-compat with prior PCNAEngine wiring
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: zfae_pkg
#   summary: a0(ZFAE) — the inference provider, not an agent label. Exposes A0ZFAEInferenceEngine (native deterministic), plus the legacy ZFAEAgent persona for backward-compat with prior PCNAEngine wiring
#   exposes: A0ZFAEInferenceEngine, ENGINE, infer, InferenceResult, MISSING_NATIVE_MESSAGE, ZFAEAgent
#   boundaries: auth:none, storage:none, network:none, user_data:read
#   owner: a0p maintainer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: zfae_engine_native_only
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.zfae_engine_native_only_holds
# === END CONTRACTS ===
"""ZFAE — the inference provider canon.

Per user spec 2026-06-02 onward:
  • a0(zfae) is the inference PROVIDER, not an agent label.
  • A0ZFAEInferenceEngine produces runtime replies via deterministic
    template grammar; never via LLM.
  • Three cores per agent (phi/psi/omega), each on its own gonal
    (default/mirror/private); each core shape [157, 53, 7, 7]
    = 407,729 trainable scalars; agent total 1,223,187.
  • 13 sentinels (S1-S13) gate every state-mutating event with mode
    observe/flag/off + per-agent editable weights.
"""
from __future__ import annotations
import time
import uuid

from ..pcna import PCNAEngine
from .inference import (
    A0ZFAEInferenceEngine,
    InferenceResult,
    MISSING_NATIVE_MESSAGE,
    ENGINE,
    infer,
)
from .sentinels import (
    Sentinel, SENTINELS, SentinelMode, SentinelVerdict, Verdict13,
    MODE_OBSERVE, MODE_FLAG, MODE_OFF,
    all_names, is_cliff, is_structural, is_slope,
)
from .sentinel_modes import SENTINEL_MODES_DEFAULT, resolve_modes, validate_modes, bulk_set
from .sentinel_weights import (
    SENTINEL_WEIGHTS_DEFAULT, INFERENCE_CHANNEL_DEFAULT,
    resolve_weights, validate_weights, inference_channel,
)
from .overrides import (
    PendingOverride, OVERRIDE_DEFAULT_TIMEOUT_MS,
    create_override, approve as approve_override,
    reject as reject_override, expire as expire_overrides,
    get as get_override, list_pending as list_pending_overrides,
)


class ZFAEAgent:
    """Legacy persistent agent persona — wraps a PCNAEngine for the inspector."""

    def __init__(self, name: str = "a0(zfae)", base_seed: int = 1):
        self.id = str(uuid.uuid4())
        self.name = name
        self.born_ms = int(time.time() * 1000)
        self.engine = PCNAEngine(n_primes=157, base_seed=base_seed)

    def receive(self, user_text: str) -> dict:
        self.engine.push_intent(user_text)
        return self.engine.heartbeat(intent=user_text)

    def absorb(self, model_id: str, text: str, usage: dict | None = None) -> None:
        self.engine.absorb_response(model_id, text, usage)

    def card(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "born_ms": self.born_ms,
            "snapshot": self.engine.snapshot(),
        }


__all__ = [
    "A0ZFAEInferenceEngine", "InferenceResult", "MISSING_NATIVE_MESSAGE",
    "ENGINE", "infer", "ZFAEAgent",
    "Sentinel", "SENTINELS", "SentinelMode", "SentinelVerdict", "Verdict13",
    "MODE_OBSERVE", "MODE_FLAG", "MODE_OFF",
    "all_names", "is_cliff", "is_structural", "is_slope",
    "SENTINEL_MODES_DEFAULT", "resolve_modes", "validate_modes", "bulk_set",
    "SENTINEL_WEIGHTS_DEFAULT", "INFERENCE_CHANNEL_DEFAULT",
    "resolve_weights", "validate_weights", "inference_channel",
    "PendingOverride", "OVERRIDE_DEFAULT_TIMEOUT_MS",
    "create_override", "approve_override", "reject_override",
    "expire_overrides", "get_override", "list_pending_overrides",
]
# ratios: loc_comments=58:53 imports_exports=9:2 calls_definitions=7:5
