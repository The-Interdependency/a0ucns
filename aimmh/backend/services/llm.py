# ratios: loc_comments=296:18 imports_exports=10:9 calls_definitions=58:10
"""LLM integration service — Emergent + OpenAI-compatible providers.

Model registry defines which provider/auth to use for each model.
Responses are persisted chunk-by-chunk (sacred logs).
"""

import os
import json
import uuid
import asyncio
import logging
import httpx
from copy import deepcopy
from typing import Any, AsyncGenerator, Dict, List, Optional

from emergentintegrations.llm.chat import LlmChat, UserMessage

from services.secrets import SecretDecryptionError, decrypt_secret

logger = logging.getLogger(__name__)

# ---- Default Model Registry ----
# Seeded on first load; users can extend via API

UNIVERSAL_DEVELOPER_IDS = ("openai", "anthropic", "google")


DEFAULT_REGISTRY = {
    "openai": {
        "name": "OpenAI",
        "auth_type": "emergent",
        "base_url": None,
        "website": "https://openai.com",
        "models": [
            {"model_id": "gpt-4o", "display_name": "GPT-4o"},
            {"model_id": "gpt-4o-mini", "display_name": "GPT-4o Mini"},
            {"model_id": "o1", "display_name": "o1"},
        ],
    },
    "anthropic": {
        "name": "Anthropic",
        "auth_type": "emergent",
        "base_url": None,
        "website": "https://anthropic.com",
        "models": [
            {"model_id": "claude-sonnet-4-5-20250929", "display_name": "Claude Sonnet 4.5"},
            {"model_id": "claude-haiku-4-5-20251001", "display_name": "Claude Haiku 4.5"},
            {"model_id": "claude-opus-4-5-20251101", "display_name": "Claude Opus 4.5"},
        ],
    },
    "google": {
        "name": "Google",
        "auth_type": "emergent",
        "base_url": None,
        "website": "https://ai.google.dev",
        "models": [
            {"model_id": "gemini-2.0-flash", "display_name": "Gemini 2.0 Flash"},
            {"model_id": "gemini-2.5-pro", "display_name": "Gemini 2.5 Pro"},
            {"model_id": "gemini-2.5-flash", "display_name": "Gemini 2.5 Flash"},
            {"model_id": "gemini-2.5-flash-lite", "display_name": "Gemini 2.5 Flash Lite"},
        ],
    },
    "xai": {
        "name": "xAI",
        "auth_type": "openai_compatible",
        "base_url": "https://api.x.ai/v1",
        "website": "https://x.ai",
        "models": [
            {"model_id": "grok-4", "display_name": "Grok 4"},
            {"model_id": "grok-3", "display_name": "Grok 3"},
            {"model_id": "grok-2", "display_name": "Grok 2"},
        ],
    },
    "deepseek": {
        "name": "DeepSeek",
        "auth_type": "openai_compatible",
        "base_url": "https://api.deepseek.com",
        "website": "https://www.deepseek.com",
        "models": [
            {"model_id": "deepseek-chat", "display_name": "DeepSeek V3"},
            {"model_id": "deepseek-reasoner", "display_name": "DeepSeek R1"},
        ],
    },
    "perplexity": {
        "name": "Perplexity",
        "auth_type": "openai_compatible",
        "base_url": "https://api.perplexity.ai",
        "website": "https://www.perplexity.ai",
        "models": [
            {"model_id": "sonar-pro", "display_name": "Sonar Pro"},
            {"model_id": "sonar", "display_name": "Sonar"},
        ],
    },
}


def model_default_payload(developer_id: str, model_id: str) -> Dict[str, Any]:
    if developer_id == "anthropic":
        return {
            "model": model_id,
            "system": "You are a helpful assistant.",
            "max_tokens": 1024,
            "temperature": 0.7,
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": True,
        }
    if developer_id == "google":
        return {
            "model": model_id,
            "contents": [{"role": "user", "parts": [{"text": "Hello"}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1024},
        }
    return {
        "model": model_id,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello"},
        ],
        "temperature": 0.7,
        "max_tokens": 1024,
        "stream": True,
    }


def universal_managed_model_ids(developer_id: str) -> set[str]:
    developer = DEFAULT_REGISTRY.get(developer_id, {})
    return {
        model.get("model_id")
        for model in developer.get("models", [])
        if isinstance(model, dict) and model.get("model_id")
    }


def reconcile_registry_developers(registry: Optional[Dict[str, Any]]) -> tuple[Dict[str, Any], bool]:
    current = deepcopy(registry or {})
    next_registry = deepcopy(current)

    for developer_id in UNIVERSAL_DEVELOPER_IDS:
        next_registry[developer_id] = deepcopy(DEFAULT_REGISTRY[developer_id])

    changed = next_registry != current
    return next_registry, changed

# Map model_id → (developer_id, provider_for_emergent)
EMERGENT_PROVIDER_MAP = {
    "openai": "openai",
    "anthropic": "anthropic",
    "google": "gemini",
}


def _is_retryable(error_text: str) -> bool:
    lowered = (error_text or "").lower()
    markers = ["502", "503", "504", "badgateway", "gateway",
               "temporarily unavailable", "timeout", "rate limit", "429"]
    return any(m in lowered for m in markers)


def resolve_model(model_id: str, registry: dict) -> Optional[Dict[str, Any]]:
    """Resolve a model_id to its developer info from the registry."""
    for dev_id, dev in registry.items():
        for m in dev.get("models", []):
            mid = m if isinstance(m, str) else m.get("model_id", "")
            if mid == model_id:
                return {
                    "developer_id": dev_id,
                    "auth_type": dev.get("auth_type", "emergent"),
                    "base_url": dev.get("base_url"),
                    "provider": EMERGENT_PROVIDER_MAP.get(dev_id, dev_id),
                }
    return None


def get_api_key_for_developer(user: dict, developer_id: str) -> str:
    """Get the appropriate API key for a developer.

    Emergent developers (openai/anthropic/google) default to EMERGENT_LLM_KEY.
    Others use user-provided keys.
    """
    user_keys = user.get("api_keys", {})
    # Let a decryption failure propagate: a user who configured BYOK must not be
    # silently downgraded to the shared EMERGENT_LLM_KEY when their stored key
    # cannot be decrypted (missing/rotated API_KEY_ENCRYPTION_KEY). Empty and
    # legacy-plaintext values pass through without raising.
    user_key = decrypt_secret(user_keys.get(developer_id, ""))

    emergent_devs = {"openai", "anthropic", "google"}
    if developer_id in emergent_devs:
        if user_key and user_key not in ("UNIVERSAL", ""):
            return user_key
        return os.environ.get("EMERGENT_LLM_KEY", "")

    return user_key or ""


async def stream_emergent(
    api_key: str,
    model_id: str,
    provider: str,
    messages: List[dict],
    thread_id: str,
) -> AsyncGenerator[str, None]:
    """Stream from Emergent-supported models (GPT, Claude, Gemini)."""
    user_messages = [m for m in messages if m["role"] == "user"]
    if not user_messages:
        yield "[ERROR] No user messages found"
        return

    # Build conversation history for system message
    history = ""
    if len(messages) > 1:
        parts = []
        for msg in messages[:-1][-10:]:
            prefix = "User" if msg["role"] == "user" else "Assistant"
            parts.append(f"{prefix}: {msg['content']}")
        if parts:
            history = "\n".join(parts)

    system_msg = "You are a helpful AI assistant."
    if history:
        system_msg += f"\n\nPrevious conversation:\n{history}"

    session_id = f"{thread_id}-{model_id}" if thread_id else str(uuid.uuid4())
    user_msg = UserMessage(text=user_messages[-1]["content"])
    backoff = [0.8, 1.6, 2.4]

    for attempt in range(3):
        try:
            chat = LlmChat(
                api_key=api_key,
                session_id=f"{session_id}-{attempt}",
                system_message=system_msg,
            ).with_model(provider, model_id)

            response = await chat.send_message(user_msg)
            # Simulate streaming by yielding word chunks
            words = response.split()
            for word in words:
                yield word + " "
                await asyncio.sleep(0.02)
            return
        except Exception as e:
            err = str(e)
            if attempt < 2 and _is_retryable(err):
                logger.warning("Retryable error %s/%s (attempt %d): %s", provider, model_id, attempt + 1, err)
                await asyncio.sleep(backoff[attempt])
                continue
            if _is_retryable(err):
                yield f"[ERROR] Provider temporarily unavailable: {err}"
            else:
                yield f"[ERROR] {err}"
            return


async def stream_openai_compatible(
    base_url: str,
    api_key: str,
    model_id: str,
    messages: List[dict],
) -> AsyncGenerator[str, None]:
    """Stream from OpenAI-compatible APIs (Grok, DeepSeek, Perplexity)."""
    backoff = [0.8, 1.6, 2.4]
    async with httpx.AsyncClient() as client:
        for attempt in range(3):
            try:
                async with client.stream(
                    "POST",
                    f"{base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model_id,
                        "messages": messages,
                        "stream": True,
                    },
                    timeout=90.0,
                ) as resp:
                    if resp.status_code != 200:
                        error_text = (await resp.aread()).decode(errors="ignore")
                        combined = f"API error {resp.status_code}: {error_text}"
                        if attempt < 2 and _is_retryable(combined):
                            await asyncio.sleep(backoff[attempt])
                            continue
                        yield f"[ERROR] {combined}"
                        return

                    async for line in resp.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                                content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue
                    return
            except Exception as e:
                err = str(e)
                if attempt < 2 and _is_retryable(err):
                    await asyncio.sleep(backoff[attempt])
                    continue
                yield f"[ERROR] {err}"
                return


async def generate_response(
    model_id: str,
    messages: List[dict],
    thread_id: str,
    user: dict,
    registry: dict,
) -> AsyncGenerator[str, None]:
    """Unified generator — resolves model to provider and streams."""
    info = resolve_model(model_id, registry)
    if not info:
        yield f"[ERROR] Unknown model: {model_id}. Add it via the model registry."
        return

    try:
        api_key = get_api_key_for_developer(user, info["developer_id"])
    except SecretDecryptionError:
        # Stored BYOK key cannot be decrypted (missing/rotated
        # API_KEY_ENCRYPTION_KEY). Surface a structured error via the [ERROR]
        # convention instead of a shared-key fallback or an unhandled 500.
        yield (f"[ERROR] Stored API key for {info['developer_id']} could not be decrypted. "
               f"Re-enter it in Settings, or fix API_KEY_ENCRYPTION_KEY.")
        return
    if not api_key:
        yield f"[ERROR] No API key for {info['developer_id']}. Add one in Settings."
        return

    if info["auth_type"] == "emergent":
        async for chunk in stream_emergent(api_key, model_id, info["provider"], messages, thread_id):
            yield chunk
    elif info["auth_type"] == "openai_compatible":
        if not info.get("base_url"):
            yield f"[ERROR] No base URL configured for {info['developer_id']}"
            return
        async for chunk in stream_openai_compatible(info["base_url"], api_key, model_id, messages):
            yield chunk
    else:
        yield f"[ERROR] Unsupported auth type: {info['auth_type']}"


async def validate_universal_key() -> dict:
    """Quick validation ping for the Emergent universal key."""
    key = os.environ.get("EMERGENT_LLM_KEY", "")
    if not key:
        return {"status": "missing", "message": "EMERGENT_LLM_KEY not configured"}
    try:
        chat = LlmChat(
            api_key=key,
            session_id=str(uuid.uuid4()),
            system_message="You are a helpful AI assistant.",
        ).with_model("openai", "gpt-4o-mini")
        response = await asyncio.wait_for(
            chat.send_message(UserMessage(text="ping")), timeout=12
        )
        if response:
            return {"status": "valid", "message": "Universal key is valid"}
        return {"status": "error", "message": "No response during validation"}
    except Exception as e:
        msg = str(e)
        status = "invalid" if any(w in msg.lower() for w in ["invalid", "auth", "unauthorized", "401"]) else "error"
        return {"status": status, "message": msg}
# ratios: loc_comments=296:18 imports_exports=10:9 calls_definitions=58:10
