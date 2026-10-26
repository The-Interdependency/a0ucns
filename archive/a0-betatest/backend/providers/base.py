# ratios: loc_comments=21:42 imports_exports=2:2 calls_definitions=0:4
# === MODULE_BUILD ===
# id: provider_base
#   module_name: base
#   module_kind: adapter
#   summary: common Protocol + TypedDict contract for BYOK LLM provider adapters
#   owner: a0p maintainer
#   public_surface: ProviderAdapter, ChatResult
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: hmmm
#   rollout: default_enabled
#   rollback: revert file; all provider adapters break at import
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: provider_base_boundaries
#   summary: common Protocol + TypedDict contract for BYOK LLM provider adapters
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: provider_base
#   summary: common Protocol + TypedDict contract for BYOK LLM provider adapters
#   exposes: ProviderAdapter, ChatResult
#   boundaries: auth:none, storage:none, network:none, user_data:none
#   owner: a0p maintainer
# === END CAPABILITIES ===
"""Common interface for BYOK LLM providers."""
from __future__ import annotations
from typing import Any, Protocol, TypedDict


class ChatResult(TypedDict, total=False):
    content: str
    usage: dict
    model_id: str
    provider: str
    raw: Any
    error: str


class ProviderAdapter(Protocol):
    name: str
    async def list_models(self, api_key: str) -> list[dict]: ...
    async def chat(
        self,
        api_key: str,
        model: str,
        messages: list[dict],
        system: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> ChatResult: ...

# === CONTRACTS ===
# id: provider_base_loads
#   given: module declares its msdmd canon
#   then: the module imports cleanly under the current interpreter
#   class: integration
#   call: a0p_skills.contracts.module_imports_cleanly_holds
# === END CONTRACTS ===
# ratios: loc_comments=21:42 imports_exports=2:2 calls_definitions=0:4
