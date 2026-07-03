# ratios: loc_comments=81:44 imports_exports=3:1 calls_definitions=14:3
# === MODULE_BUILD ===
# id: provider_anthropic
#   module_name: anthropic_provider
#   module_kind: adapter
#   summary: Anthropic BYOK adapter — list models, messages via httpx
#   owner: a0p maintainer
#   public_surface: AnthropicProvider
#   internal_surface: version
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: external
#   user_data_boundary: read
#   admin_only: false
#   tests: hmmm
#   rollout: default_enabled
#   rollback: remove from providers.REGISTRY
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: provider_anthropic_boundaries
#   summary: Anthropic BYOK adapter — list models, messages via httpx
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: external
#   user_data_boundary: read
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: provider_anthropic
#   summary: Anthropic BYOK adapter — list models, messages via httpx
#   exposes: AnthropicProvider
#   boundaries: auth:none, storage:none, network:external, user_data:read
#   owner: a0p maintainer
# === END CAPABILITIES ===
"""Anthropic adapter — /v1/models + /v1/messages via httpx."""
from __future__ import annotations
import httpx
from .base import ChatResult


class AnthropicProvider:
    name = "anthropic"
    base = "https://api.anthropic.com/v1"
    version = "2023-06-01"

    async def list_models(self, api_key: str) -> list[dict]:
        async with httpx.AsyncClient(timeout=30.0) as c:
            r = await c.get(
                f"{self.base}/models",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": self.version,
                },
            )
            if r.status_code >= 400:
                # Fallback — Anthropic's /v1/models is recent; if it fails, hardcode well-known
                return [
                    {"id": "claude-sonnet-4-5-20250929", "provider": "anthropic", "label": "Claude Sonnet 4.5"},
                    {"id": "claude-haiku-4-5-20251001", "provider": "anthropic", "label": "Claude Haiku 4.5"},
                    {"id": "claude-opus-4-5-20251101", "provider": "anthropic", "label": "Claude Opus 4.5"},
                ]
            data = r.json().get("data", []) or r.json().get("models", [])
            return [{"id": m.get("id"), "provider": "anthropic",
                     "label": m.get("display_name") or m.get("id"),
                     "created": m.get("created_at")} for m in data]

    async def chat(
        self,
        api_key: str,
        model: str,
        messages: list[dict],
        system: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> ChatResult:
        # Anthropic expects messages without a system role; system is a top-level field.
        norm = []
        sys_buf = system or ""
        for m in messages:
            if m["role"] == "system":
                sys_buf = (sys_buf + "\n" + m["content"]).strip()
            else:
                norm.append({"role": m["role"], "content": m["content"]})
        payload = {
            "model": model,
            "messages": norm,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if sys_buf:
            payload["system"] = sys_buf
        async with httpx.AsyncClient(timeout=120.0) as c:
            r = await c.post(
                f"{self.base}/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": self.version,
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            if r.status_code >= 400:
                return ChatResult(
                    content="", error=f"anthropic {r.status_code}: {r.text[:400]}",
                    model_id=model, provider="anthropic",
                )
            j = r.json()
            blocks = j.get("content") or []
            content = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
            u = j.get("usage") or {}
            return ChatResult(
                content=content,
                usage={
                    "prompt": u.get("input_tokens", 0),
                    "completion": u.get("output_tokens", 0),
                    "total": u.get("input_tokens", 0) + u.get("output_tokens", 0),
                    "cache_read": u.get("cache_read_input_tokens", 0),
                    "cache_write": u.get("cache_creation_input_tokens", 0),
                },
                model_id=model,
                provider="anthropic",
            )

# === CONTRACTS ===
# id: provider_anthropic_loads
#   given: module declares its msdmd canon
#   then: the module imports cleanly under the current interpreter
#   class: integration
#   call: a0p_skills.contracts.module_imports_cleanly_holds
# === END CONTRACTS ===
# ratios: loc_comments=81:44 imports_exports=3:1 calls_definitions=14:3
