# ratios: loc_comments=30:25 imports_exports=7:1 calls_definitions=8:2
"""
adapters.py — Bridge from aimmh_lib.conversations.CallFn to the aimmh backend.

This module is intentionally NOT re-exported from aimmh_lib/__init__.py because
importing it pulls in backend service dependencies. Import explicitly:

    import sys
    sys.path.insert(0, "/path/to/aimmh/backend")

    from aimmh_lib.adapters import make_call_fn
    from aimmh_lib import daisy_chain, roleplay

    call = make_call_fn(user={"api_keys": {}})
    results = await daisy_chain(call, ["gpt-4o", "claude-haiku-4-5-20251001"], "Hello")
"""

from __future__ import annotations

import uuid
from typing import Optional


def make_call_fn(
    user: dict,
    registry: Optional[dict] = None,
    thread_id_prefix: str = "lib",
) -> "CallFn":
    """Create a CallFn that delegates to the backend's generate_response.

    Args:
        user: Backend user dict. api_keys sub-dict maps developer_id → key.
              Emergent-managed providers (openai/anthropic/google) fall back
              to EMERGENT_LLM_KEY env var when key is absent or "UNIVERSAL".
              Minimal example: {"api_keys": {}}
        registry: Model registry dict (same format as DEFAULT_REGISTRY).
                  Defaults to DEFAULT_REGISTRY from backend services.llm.
        thread_id_prefix: Namespace prefix for generated thread IDs.

    Returns:
        CallFn: async (model_id: str, messages: list[dict]) -> str

    Raises:
        ImportError: If backend/services is not on sys.path.
    """
    try:
        from services.llm import generate_response, DEFAULT_REGISTRY  # type: ignore
    except ImportError as e:
        raise ImportError(
            "Could not import backend services. Ensure the backend directory "
            "is on sys.path before calling make_call_fn().\n"
            "  import sys; sys.path.insert(0, '/home/user/aimmh/backend')"
        ) from e

    resolved_registry = registry if registry is not None else DEFAULT_REGISTRY

    async def call_fn(model_id: str, messages: list[dict]) -> str:
        thread_id = f"{thread_id_prefix}_{uuid.uuid4().hex[:12]}"
        chunks: list[str] = []
        async for chunk in generate_response(
            model_id=model_id,
            messages=messages,
            thread_id=thread_id,
            user=user,
            registry=resolved_registry,
        ):
            chunks.append(chunk)
        return "".join(chunks)

    return call_fn
# ratios: loc_comments=30:25 imports_exports=7:1 calls_definitions=8:2
