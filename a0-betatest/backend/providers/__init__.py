# ratios: loc_comments=12:48 imports_exports=5:1 calls_definitions=2:0
# === MODULE_BUILD ===
# id: providers_pkg
#   module_name: providers
#   module_kind: adapter
#   summary: BYOK adapter registry — openai, anthropic, gemini, xai (Emergent removed; build is platform-free)
#   owner: a0p maintainer
#   public_surface: REGISTRY, ProviderAdapter, ChatResult
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: external
#   user_data_boundary: read
#   admin_only: false
#   tests: hmmm
#   rollout: default_enabled
#   rollback: remove provider imports from server.py
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: providers_pkg_boundaries
#   summary: BYOK adapter registry — openai, anthropic, gemini, xai (Emergent removed; build is platform-free)
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: external
#   user_data_boundary: read
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: providers_pkg
#   summary: BYOK adapter registry — openai, anthropic, gemini, xai (Emergent removed; build is platform-free)
#   exposes: REGISTRY, ProviderAdapter, ChatResult
#   boundaries: auth:none, storage:none, network:external, user_data:read
#   owner: a0p maintainer
# === END CAPABILITIES ===
"""LLM provider adapters — BYOK pass-through via httpx.

Each adapter exposes:
    list_models(api_key) -> list[dict]
    chat(api_key, model, messages, **opts) -> {"content": str, "usage": dict, ...}

No platform-specific runtime dependencies. Every call uses the user's
own provider API key, decrypted from the BYOK vault per request.
"""
from .base import ProviderAdapter, ChatResult
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .gemini_provider import GeminiProvider
from .xai_provider import XAIProvider

REGISTRY: dict[str, ProviderAdapter] = {
    "openai":    OpenAIProvider(),
    "anthropic": AnthropicProvider(),
    "gemini":    GeminiProvider(),
    "xai":       XAIProvider(),
}

__all__ = ["REGISTRY", "ProviderAdapter", "ChatResult"]

# === CONTRACTS ===
# id: providers_pkg_loads
#   given: module declares its msdmd canon
#   then: the module imports cleanly under the current interpreter
#   class: integration
#   call: a0p_skills.contracts.module_imports_cleanly_holds
# === END CONTRACTS ===
# ratios: loc_comments=12:48 imports_exports=5:1 calls_definitions=2:0
