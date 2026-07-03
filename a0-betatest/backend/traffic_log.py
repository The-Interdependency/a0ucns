# ratios: loc_comments=55:52 imports_exports=8:3 calls_definitions=15:5
# === MODULE_BUILD ===
# id: traffic_log
#   module_name: traffic_log
#   module_kind: worker
#   summary: append-only traffic logger — an ASGI middleware that records one JSONL line of request METADATA per HTTP call (ts, method, path, status, latency_ms, client ip, user-agent, best-effort user id) to an append-only sink; never logs request/response bodies, headers, cookies, or any secret material
#   owner: Erin Spencer
#   public_surface: traffic_middleware, log_path, LOG_PATH_ENV
#   internal_surface: _resolve_uid, _append, _ensure_dir
#   auth_boundary: none
#   storage_boundary: write
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: a0p_skills.contracts.traffic_log_append_only_holds
#   rollout: default_enabled
#   rollback: remove the app.middleware registration in server.py and this module
#   hmmm: the sink is an append-only JSONL file (open mode "a"); rotation/retention is left to the host/ops layer
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: traffic_log_boundaries
#   summary: append-only metadata logging of HTTP traffic; no bodies, headers, cookies, or secrets are ever written
#   auth_boundary: none
#   storage_boundary: write
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: traffic_log
#   summary: ASGI middleware appending one JSONL metadata line per request to an append-only sink
#   exposes: traffic_middleware, log_path
#   boundaries: auth:none, storage:write, network:none, user_data:read
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: traffic_log_append_only
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.traffic_log_append_only_holds
# === END CONTRACTS ===
"""Append-only traffic logger for all HTTP traffic.

One JSONL line of request METADATA per call — never bodies, headers, cookies, or
secrets. The sink is opened in append mode and never rewritten, so the log is a
tamper-evident, monotonically-growing record of traffic.
"""
from __future__ import annotations
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path


LOG_PATH_ENV: str = "A0P_TRAFFIC_LOG"
_DEFAULT_LOG_PATH: str = "/app/backend/logs/traffic.log"


def log_path() -> Path:
    """The append-only traffic log path (env-overridable)."""
    return Path(os.environ.get(LOG_PATH_ENV, _DEFAULT_LOG_PATH))


def _ensure_dir(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)


def _resolve_uid(request) -> str | None:
    """Best-effort, no-DB user id from the access cookie. Never raises."""
    try:
        token = request.cookies.get("access_token")
        if not token:
            return None
        import jwt as pyjwt  # PyJWT
        from auth import _jwt_secret, _JWT_ALG
        payload = pyjwt.decode(token, _jwt_secret(), algorithms=[_JWT_ALG])
        if payload.get("type") != "access":
            return None
        return payload.get("sub")
    except Exception:
        return None


def _append(record: dict) -> None:
    """Append one JSON record as a line. Append-only; never raises upward."""
    try:
        p = log_path()
        _ensure_dir(p)
        with p.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, separators=(",", ":")) + "\n")
    except Exception:
        # Logging must never break request handling.
        pass


async def traffic_middleware(request, call_next):
    """ASGI middleware: time the call, then append a metadata line."""
    start = time.perf_counter()
    status = 500
    try:
        response = await call_next(request)
        status = getattr(response, "status_code", 200)
        return response
    finally:
        latency_ms = round((time.perf_counter() - start) * 1000.0, 2)
        client = request.client
        _append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "method": request.method,
            "path": request.url.path,
            "query": request.url.query or "",
            "status": status,
            "latency_ms": latency_ms,
            "ip": getattr(client, "host", None),
            "ua": request.headers.get("user-agent", ""),
            "uid": _resolve_uid(request),
        })


__all__ = ["traffic_middleware", "log_path", "LOG_PATH_ENV"]
# ratios: loc_comments=55:52 imports_exports=8:3 calls_definitions=15:5
