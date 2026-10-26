# ratios: loc_comments=85:47 imports_exports=3:1 calls_definitions=21:3
# === MODULE_BUILD ===
# id: provider_openai
#   module_name: openai_provider
#   module_kind: adapter
#   summary: OpenAI BYOK adapter — list models, chat completion via httpx
#   owner: a0p maintainer
#   public_surface: OpenAIProvider
#   internal_surface: base, name
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
# id: provider_openai_boundaries
#   summary: OpenAI BYOK adapter — list models, chat completion via httpx
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: external
#   user_data_boundary: read
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: provider_openai
#   summary: OpenAI BYOK adapter — list models, chat completion via httpx
#   exposes: OpenAIProvider
#   boundaries: auth:none, storage:none, network:external, user_data:read
#   owner: a0p maintainer
# === END CAPABILITIES ===
"""OpenAI adapter — /v1/models + /v1/chat/completions via httpx."""
from __future__ import annotations
import httpx
from .base import ChatResult


class OpenAIProvider:
    name = "openai"
    base = "https://api.openai.com/v1"

    async def list_models(self, api_key: str) -> list[dict]:
        async with httpx.AsyncClient(timeout=30.0) as c:
            r = await c.get(
                f"{self.base}/models",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            r.raise_for_status()
            data = r.json().get("data", [])
            # Filter to chat-capable / common families
            out = []
            for m in data:
                mid = m.get("id", "")
                if any(k in mid for k in ("gpt-", "o1", "o3", "o4")):
                    out.append({
                        "id": mid,
                        "provider": "openai",
                        "label": mid,
                        "context_window": None,
                        "modality": "text",
                        "created": m.get("created"),
                    })
            return out

    async def chat(
        self,
        api_key: str,
        model: str,
        messages: list[dict],
        system: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> ChatResult:
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.extend(messages)
        payload = {
            "model": model,
            "messages": msgs,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=120.0) as c:
            # Newer OpenAI models (gpt-5*, o-series) reject `max_tokens` (want
            # `max_completion_tokens`) and only allow the default temperature.
            # Retry, adapting the payload to whatever the API complains about, so
            # one adapter serves both legacy and current models.
            r = await c.post(f"{self.base}/chat/completions", headers=headers, json=payload)
            for _ in range(2):
                if r.status_code < 400:
                    break
                err = r.text
                adjusted = False
                if "max_completion_tokens" in err and "max_tokens" in payload:
                    payload["max_completion_tokens"] = payload.pop("max_tokens")
                    adjusted = True
                if "temperature" in err and "temperature" in payload:
                    payload.pop("temperature", None)
                    adjusted = True
                if not adjusted:
                    break
                r = await c.post(f"{self.base}/chat/completions", headers=headers, json=payload)
            if r.status_code >= 400:
                return ChatResult(
                    content="", error=f"openai {r.status_code}: {r.text[:400]}",
                    model_id=model, provider="openai",
                )
            j = r.json()
            choice = (j.get("choices") or [{}])[0]
            content = (choice.get("message") or {}).get("content", "") or ""
            usage = j.get("usage") or {}
            return ChatResult(
                content=content,
                usage={
                    "prompt": usage.get("prompt_tokens", 0),
                    "completion": usage.get("completion_tokens", 0),
                    "total": usage.get("total_tokens", 0),
                },
                model_id=model,
                provider="openai",
            )

# === CONTRACTS ===
# id: provider_openai_loads
#   given: module declares its msdmd canon
#   then: the module imports cleanly under the current interpreter
#   class: integration
#   call: a0p_skills.contracts.module_imports_cleanly_holds
# === END CONTRACTS ===
# ratios: loc_comments=85:47 imports_exports=3:1 calls_definitions=21:3
