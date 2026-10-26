# ratios: loc_comments=80:44 imports_exports=3:1 calls_definitions=16:3
# === MODULE_BUILD ===
# id: provider_gemini
#   module_name: gemini_provider
#   module_kind: adapter
#   summary: Google Gemini BYOK adapter — list models, generateContent via httpx
#   owner: a0p maintainer
#   public_surface: GeminiProvider
#   internal_surface: none
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
# id: provider_gemini_boundaries
#   summary: Google Gemini BYOK adapter — list models, generateContent via httpx
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: external
#   user_data_boundary: read
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: provider_gemini
#   summary: Google Gemini BYOK adapter — list models, generateContent via httpx
#   exposes: GeminiProvider
#   boundaries: auth:none, storage:none, network:external, user_data:read
#   owner: a0p maintainer
# === END CAPABILITIES ===
"""Google Gemini adapter — generativelanguage.googleapis.com via httpx."""
from __future__ import annotations
import httpx
from .base import ChatResult


class GeminiProvider:
    name = "gemini"
    base = "https://generativelanguage.googleapis.com/v1beta"

    async def list_models(self, api_key: str) -> list[dict]:
        async with httpx.AsyncClient(timeout=30.0) as c:
            r = await c.get(f"{self.base}/models", params={"key": api_key})
            if r.status_code >= 400:
                return []
            out = []
            for m in r.json().get("models", []):
                mid = m.get("name", "").replace("models/", "")
                # Filter to chat-capable
                methods = m.get("supportedGenerationMethods", []) or []
                if "generateContent" not in methods:
                    continue
                out.append({
                    "id": mid,
                    "provider": "gemini",
                    "label": m.get("displayName", mid),
                    "context_window": m.get("inputTokenLimit"),
                    "output_limit": m.get("outputTokenLimit"),
                    "modality": "multimodal",
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
        contents = []
        for m in messages:
            if m["role"] == "system":
                # Gemini system is via systemInstruction
                continue
            role = "user" if m["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": m["content"]}]})

        payload: dict = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}

        async with httpx.AsyncClient(timeout=120.0) as c:
            r = await c.post(
                f"{self.base}/models/{model}:generateContent",
                params={"key": api_key},
                headers={"Content-Type": "application/json"},
                json=payload,
            )
            if r.status_code >= 400:
                return ChatResult(
                    content="", error=f"gemini {r.status_code}: {r.text[:400]}",
                    model_id=model, provider="gemini",
                )
            j = r.json()
            cands = j.get("candidates") or []
            content = ""
            if cands:
                parts = (cands[0].get("content") or {}).get("parts") or []
                content = "".join(p.get("text", "") for p in parts)
            um = j.get("usageMetadata") or {}
            return ChatResult(
                content=content,
                usage={
                    "prompt": um.get("promptTokenCount", 0),
                    "completion": um.get("candidatesTokenCount", 0),
                    "total": um.get("totalTokenCount", 0),
                    "cache_read": um.get("cachedContentTokenCount", 0),
                },
                model_id=model,
                provider="gemini",
            )

# === CONTRACTS ===
# id: provider_gemini_loads
#   given: module declares its msdmd canon
#   then: the module imports cleanly under the current interpreter
#   class: integration
#   call: a0p_skills.contracts.module_imports_cleanly_holds
# === END CONTRACTS ===
# ratios: loc_comments=80:44 imports_exports=3:1 calls_definitions=16:3
