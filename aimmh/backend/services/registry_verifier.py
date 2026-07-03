# ratios: loc_comments=270:0 imports_exports=9:4 calls_definitions=98:8
from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any, Dict, List, Optional

import httpx
from emergentintegrations.llm.chat import LlmChat, UserMessage

from models.registry import VerificationResponse, VerificationResult
from services.llm import EMERGENT_PROVIDER_MAP, get_api_key_for_developer


class RegistryVerificationError(Exception):
    def __init__(self, status: str, message: str):
        self.status = status
        self.message = message
        super().__init__(message)


def _classify_error(message: str) -> tuple[str, str]:
    lowered = (message or "").lower()
    if any(marker in lowered for marker in ["401", "403", "unauthorized", "forbidden", "invalid api key", "invalid_api_key", "authentication"]):
        return "auth_failed", message
    if any(marker in lowered for marker in ["429", "rate limit", "quota"]):
        return "rate_limited", message
    if any(marker in lowered for marker in ["404", "model_not_found", "unknown model", "does not exist", "not found"]):
        return "model_missing", message
    if any(marker in lowered for marker in ["timeout", "connection", "dns", "temporarily unavailable", "502", "503", "504"]):
        return "connection_error", message
    return "error", message or "Unknown verification error"


async def _strict_probe_emergent(api_key: str, developer_id: str, model_id: str) -> tuple[str, str, int]:
    provider = EMERGENT_PROVIDER_MAP.get(developer_id, developer_id)
    start = time.perf_counter()
    try:
        chat = LlmChat(
            api_key=api_key,
            session_id=f"verify-{developer_id}-{uuid.uuid4().hex[:10]}",
            system_message="Reply with the single token OK.",
        ).with_model(provider, model_id)
        response = await asyncio.wait_for(chat.send_message(UserMessage(text="ping")), timeout=15)
        latency_ms = int((time.perf_counter() - start) * 1000)
        if response:
            return "verified", "Model responded to lightweight probe", latency_ms
        return "error", "No response from provider", latency_ms
    except Exception as exc:
        latency_ms = int((time.perf_counter() - start) * 1000)
        status, message = _classify_error(str(exc))
        return status, message, latency_ms


async def _strict_probe_openai_compatible(base_url: str, api_key: str, model_id: str) -> tuple[str, str, int]:
    normalized_base = base_url.rstrip("/")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    start = time.perf_counter()
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            models_resp = await client.get(f"{normalized_base}/models", headers=headers)
            latency_ms = int((time.perf_counter() - start) * 1000)
            if models_resp.status_code == 200:
                payload = models_resp.json() if models_resp.headers.get("content-type", "").startswith("application/json") else {}
                data = payload.get("data", []) if isinstance(payload, dict) else []
                model_ids = {item.get("id") for item in data if isinstance(item, dict) and item.get("id")}
                if model_id in model_ids:
                    return "verified", "Model discovered from provider /models endpoint", latency_ms
            elif models_resp.status_code in {401, 403, 429}:
                status, message = _classify_error(f"HTTP {models_resp.status_code}: {models_resp.text}")
                return status, message, latency_ms
        except Exception:
            pass

        start = time.perf_counter()
        try:
            probe_resp = await client.post(
                f"{normalized_base}/chat/completions",
                headers=headers,
                json={
                    "model": model_id,
                    "messages": [{"role": "user", "content": "ping"}],
                    "stream": False,
                    "max_tokens": 1,
                },
            )
            latency_ms = int((time.perf_counter() - start) * 1000)
            if probe_resp.status_code == 200:
                return "verified", "Model responded to lightweight probe", latency_ms
            status, message = _classify_error(f"HTTP {probe_resp.status_code}: {probe_resp.text}")
            return status, message, latency_ms
        except Exception as exc:
            latency_ms = int((time.perf_counter() - start) * 1000)
            status, message = _classify_error(str(exc))
            return status, message, latency_ms


async def verify_single_model(current_user: dict, registry: dict, developer_id: str, model_id: str, mode: str = "strict") -> VerificationResult:
    developer = (registry or {}).get(developer_id)
    if not developer:
        return VerificationResult(
            scope="model",
            developer_id=developer_id,
            model_id=model_id,
            status="error",
            message="Developer not found in registry",
            verification_mode=mode,
        )

    api_key = get_api_key_for_developer(current_user, developer_id)
    if not api_key:
        return VerificationResult(
            scope="model",
            developer_id=developer_id,
            developer_name=developer.get("name"),
            model_id=model_id,
            status="missing_key",
            message="No API key configured for this developer",
            verification_mode=mode,
            website=developer.get("website"),
            base_url=developer.get("base_url"),
        )

    auth_type = developer.get("auth_type", "emergent")
    if auth_type == "emergent":
        status, message, latency_ms = await _strict_probe_emergent(api_key, developer_id, model_id)
    else:
        base_url = developer.get("base_url")
        if not base_url:
            status, message, latency_ms = "error", "No base URL configured", 0
        else:
            status, message, latency_ms = await _strict_probe_openai_compatible(base_url, api_key, model_id)

    return VerificationResult(
        scope="model",
        developer_id=developer_id,
        developer_name=developer.get("name"),
        model_id=model_id,
        status=status,
        message=message,
        verification_mode=mode,
        website=developer.get("website"),
        base_url=developer.get("base_url"),
        latency_ms=latency_ms,
    )


async def verify_developer_models(current_user: dict, registry: dict, developer_id: str, mode: str = "light") -> VerificationResponse:
    developer = (registry or {}).get(developer_id)
    if not developer:
        return VerificationResponse(scope="developer", verification_mode=mode, total_count=1, results=[VerificationResult(
            scope="developer",
            developer_id=developer_id,
            status="error",
            message="Developer not found in registry",
            verification_mode=mode,
        )])

    models = developer.get("models", []) or []
    normalized_models = [m.get("model_id") if isinstance(m, dict) else m for m in models]
    if not normalized_models:
        return VerificationResponse(scope="developer", verification_mode=mode, total_count=0, results=[])

    results: List[VerificationResult] = []
    if mode == "strict":
        for model_id in normalized_models:
            results.append(await verify_single_model(current_user, registry, developer_id, model_id, mode="strict"))
    else:
        if developer.get("auth_type", "emergent") == "openai_compatible" and developer.get("base_url"):
            api_key = get_api_key_for_developer(current_user, developer_id)
            if not api_key:
                results = [VerificationResult(
                    scope="developer",
                    developer_id=developer_id,
                    developer_name=developer.get("name"),
                    model_id=model_id,
                    status="missing_key",
                    message="No API key configured for this developer",
                    verification_mode="light",
                    website=developer.get("website"),
                    base_url=developer.get("base_url"),
                ) for model_id in normalized_models]
            else:
                normalized_base = developer.get("base_url", "").rstrip("/")
                headers = {"Authorization": f"Bearer {api_key}"}
                async with httpx.AsyncClient(timeout=15.0) as client:
                    try:
                        start = time.perf_counter()
                        response = await client.get(f"{normalized_base}/models", headers=headers)
                        latency_ms = int((time.perf_counter() - start) * 1000)
                        if response.status_code == 200:
                            payload = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                            data = payload.get("data", []) if isinstance(payload, dict) else []
                            provider_models = {item.get("id") for item in data if isinstance(item, dict) and item.get("id")}
                            for model_id in normalized_models:
                                if model_id in provider_models:
                                    results.append(VerificationResult(
                                        scope="developer",
                                        developer_id=developer_id,
                                        developer_name=developer.get("name"),
                                        model_id=model_id,
                                        status="verified",
                                        message="Found via provider /models listing",
                                        verification_mode="light",
                                        website=developer.get("website"),
                                        base_url=developer.get("base_url"),
                                        latency_ms=latency_ms,
                                    ))
                                else:
                                    results.append(VerificationResult(
                                        scope="developer",
                                        developer_id=developer_id,
                                        developer_name=developer.get("name"),
                                        model_id=model_id,
                                        status="model_missing",
                                        message="Model not present in provider /models listing",
                                        verification_mode="light",
                                        website=developer.get("website"),
                                        base_url=developer.get("base_url"),
                                        latency_ms=latency_ms,
                                    ))
                        else:
                            status, message = _classify_error(f"HTTP {response.status_code}: {response.text}")
                            results = [VerificationResult(
                                scope="developer",
                                developer_id=developer_id,
                                developer_name=developer.get("name"),
                                model_id=model_id,
                                status=status,
                                message=message,
                                verification_mode="light",
                                website=developer.get("website"),
                                base_url=developer.get("base_url"),
                                latency_ms=latency_ms,
                            ) for model_id in normalized_models]
                    except Exception as exc:
                        status, message = _classify_error(str(exc))
                        results = [VerificationResult(
                            scope="developer",
                            developer_id=developer_id,
                            developer_name=developer.get("name"),
                            model_id=model_id,
                            status=status,
                            message=message,
                            verification_mode="light",
                            website=developer.get("website"),
                            base_url=developer.get("base_url"),
                        ) for model_id in normalized_models]
        else:
            representative = normalized_models[0]
            representative_result = await verify_single_model(current_user, registry, developer_id, representative, mode="strict")
            results.append(representative_result.model_copy(update={"scope": "developer", "verification_mode": "light"}))
            for model_id in normalized_models[1:]:
                results.append(VerificationResult(
                    scope="developer",
                    developer_id=developer_id,
                    developer_name=developer.get("name"),
                    model_id=model_id,
                    status="verified_via_provider" if representative_result.status == "verified" else representative_result.status,
                    message=(
                        f"Provider connection verified via representative probe on {representative}; this model was not individually probed to preserve free-tier usage."
                        if representative_result.status == "verified"
                        else representative_result.message
                    ),
                    verification_mode="light",
                    website=developer.get("website"),
                    base_url=developer.get("base_url"),
                    latency_ms=representative_result.latency_ms,
                ))

    return VerificationResponse(
        scope="developer",
        verification_mode=mode,
        verified_count=sum(1 for item in results if item.status in {"verified", "verified_via_provider"}),
        total_count=len(results),
        results=results,
    )


async def verify_registry(current_user: dict, registry: dict, mode: str = "light") -> VerificationResponse:
    all_results: List[VerificationResult] = []
    for developer_id in (registry or {}).keys():
        response = await verify_developer_models(current_user, registry, developer_id, mode=mode)
        all_results.extend(response.results)
    return VerificationResponse(
        scope="registry",
        verification_mode=mode,
        verified_count=sum(1 for item in all_results if item.status in {"verified", "verified_via_provider"}),
        total_count=len(all_results),
        results=all_results,
    )
# ratios: loc_comments=270:0 imports_exports=9:4 calls_definitions=98:8
