# ratios: loc_comments=26:42 imports_exports=7:2 calls_definitions=9:2
# === MODULE_BUILD ===
# id: tools_webhook
#   module_name: webhook
#   module_kind: adapter
#   summary: invoke user-registered webhook tools — POSTs the JSON params to the user's URL with an HMAC-SHA256 signature header (X-A0P-Signature) so the user can verify the call came from a0p
#   owner: Erin Spencer
#   public_surface: invoke
#   internal_surface: _sign
#   auth_boundary: bearer
#   storage_boundary: none
#   network_boundary: external
#   user_data_boundary: read
#   admin_only: false
#   tests: a0p_skills.contracts.tools_webhook_signs_holds
#   rollout: default_enabled
#   rollback: revert; webhook-typed tools fail to dispatch
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: tools_webhook_boundaries
#   summary: outbound HMAC-signed webhook calls
#   auth_boundary: bearer
#   storage_boundary: none
#   network_boundary: external
#   user_data_boundary: read
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: tools_webhook
#   summary: hmac-signed webhook dispatcher
#   exposes: invoke
#   boundaries: auth:bearer, storage:none, network:external, user_data:read
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: tools_webhook_signs
#   given: a webhook Tool with a known secret and a known payload
#   then: _sign produces the expected HMAC-SHA256 hex digest
#   class: correctness
#   call: a0p_skills.contracts.tools_webhook_signs_holds
# === END CONTRACTS ===
"""HMAC-signed user-webhook tool dispatcher."""
from __future__ import annotations
import hashlib
import hmac
import json
from typing import Any

import httpx

from .registry import Tool, ToolError


def _sign(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


async def invoke(tool: Tool, params: dict, *, user: dict) -> Any:
    if not tool.webhook_url:
        raise ToolError(f"webhook tool {tool.name!r} missing webhook_url")
    payload = {"tool": tool.name, "params": params, "user_id": user.get("id")}
    body = json.dumps(payload, sort_keys=True).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if tool.webhook_secret:
        headers["X-A0P-Signature"] = "sha256=" + _sign(tool.webhook_secret, body)
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as cli:
        r = await cli.post(tool.webhook_url, content=body, headers=headers)
    if r.status_code >= 400:
        raise ToolError(f"webhook {tool.name!r} returned {r.status_code}: {r.text[:200]}")
    try:
        return r.json()
    except Exception:
        return {"raw": r.text[:4096]}


__all__ = ["invoke"]
# ratios: loc_comments=26:42 imports_exports=7:2 calls_definitions=9:2
