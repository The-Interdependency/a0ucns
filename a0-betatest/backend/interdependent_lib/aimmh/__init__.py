# ratios: loc_comments=16:48 imports_exports=1:1 calls_definitions=0:0
# === MODULE_BUILD ===
# id: aimmh_pkg
#   module_name: aimmh
#   module_kind: engine
#   summary: AIMMH — async multi-model orchestration over a single call_fn(model_id, messages) abstraction; the five patterns (single, fan-out, daisy-chain, synthesize, council) are what let the workspace compare or compose frontier models on one prompt without coupling to any vendor SDK
#   owner: a0p maintainer
#   public_surface: fan_out, daisy_chain, room_all, room_synthesized, council, ModelResult
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: hmmm
#   rollout: default_enabled
#   rollback: remove imports from server.py
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: aimmh_pkg_boundaries
#   summary: async multi-model orchestration patterns over a call_fn(model_id, messages)
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: aimmh_pkg
#   summary: async multi-model orchestration patterns over a call_fn(model_id, messages)
#   exposes: fan_out, daisy_chain, room_all, room_synthesized, council, ModelResult
#   boundaries: auth:none, storage:none, network:none, user_data:none
#   owner: a0p maintainer
# === END CAPABILITIES ===
"""
AIMMH — AI Multimodel Multimodal Hub.

Async multi-model conversation orchestration. Built from spec:
six interaction patterns — fan_out, daisy_chain, room_all, room_synthesized,
council, roleplay. The runtime gives `call_fn` async function and a list of
model_ids; the patterns decide who-sees-what.

"""
from .patterns import (
    ModelResult,
    fan_out,
    daisy_chain,
    room_all,
    room_synthesized,
    council,
)

__all__ = [
    "ModelResult",
    "fan_out",
    "daisy_chain",
    "room_all",
    "room_synthesized",
    "council",
]

# === CONTRACTS ===
# id: aimmh_pkg_loads
#   given: module declares its msdmd canon
#   then: the module imports cleanly under the current interpreter
#   class: integration
#   call: a0p_skills.contracts.module_imports_cleanly_holds
# === END CONTRACTS ===
# ratios: loc_comments=16:48 imports_exports=1:1 calls_definitions=0:0
