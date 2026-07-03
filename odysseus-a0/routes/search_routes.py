# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 84:43
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 7:1
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 36:6
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
# === MODULE_BUILD ===
# id: search_routes
#   module_name: search_routes
#   module_kind: route
#   summary: Search routes — /api/search/config GET, /api/search POST.
#   owner: hmmm
#   public_surface: setup_search_routes
#   internal_surface: _request_values
#   auth_boundary: hmmm
#   storage_boundary: hmmm
#   network_boundary: hmmm
#   user_data_boundary: hmmm
#   admin_only: hmmm
#   tests: hmmm
#   rollout: hmmm
#   rollback: hmmm
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: search_routes_boundaries
#   summary: Search routes — /api/search/config GET, /api/search POST.
#   auth_boundary: hmmm
#   storage_boundary: hmmm
#   network_boundary: hmmm
#   user_data_boundary: hmmm
#   admin_only: hmmm
#   owner: hmmm
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: search_routes
#   summary: Search routes — /api/search/config GET, /api/search POST.
#   exposes: setup_search_routes
# === END CAPABILITIES ===
"""Search routes — /api/search/config GET, /api/search POST."""

import logging
from typing import Dict, Any

from fastapi import APIRouter, Request

import time

from services.search import get_search_config, comprehensive_web_search, PROVIDER_INFO
from services.search.core import _call_provider
from services.search.providers import _get_provider_key, _get_search_instance

logger = logging.getLogger(__name__)


async def _request_values(request: Request) -> Dict[str, Any]:
    """Accept JSON, form data, or query params for search endpoints.

    The browser UI posts FormData, while the agent's generic app_api tool
    posts JSON. FastAPI Form(...) rejects JSON with a 422 before our handler
    runs, which made the model think SearXNG was broken.
    """
    values: Dict[str, Any] = dict(request.query_params)
    content_type = (request.headers.get("content-type") or "").lower()
    try:
        if "application/json" in content_type:
            body = await request.json()
            if isinstance(body, dict):
                values.update(body)
        else:
            form = await request.form()
            values.update(dict(form))
    except Exception:
        pass
    return values


def setup_search_routes(config) -> APIRouter:
    router = APIRouter(tags=["search"])

    @router.get("/api/search/config")
    async def get_search_settings() -> Dict[str, Any]:
        return get_search_config()

    @router.post("/api/search")
    async def do_web_search(request: Request) -> Dict[str, Any]:
        """Standalone web search — returns context string + source list.

        Used by Compare mode to pre-search once and share results across panes.
        """
        values = await _request_values(request)
        query = str(values.get("query") or values.get("q") or "").strip()
        if not query:
            return {"context": "", "sources": [], "error": "query is required"}
        time_filter = values.get("time_filter") or values.get("freshness")
        if time_filter is not None:
            time_filter = str(time_filter).strip() or None
        try:
            context, sources = comprehensive_web_search(
                query, return_sources=True, time_filter=time_filter,
            )
            return {"context": context, "sources": sources}
        except Exception as e:
            logger.error(f"Standalone web search failed: {e}")
            return {"context": "", "sources": [], "error": str(e)}

    @router.get("/api/search/providers")
    async def list_search_providers():
        """Return available search providers with config status."""
        providers = []
        for pid, (label, needs_key, needs_url) in PROVIDER_INFO.items():
            if pid == "disabled":
                continue
            available = True
            if needs_key and not _get_provider_key(pid):
                available = False
            if needs_url and pid == "searxng" and not _get_search_instance():
                available = False
            providers.append({
                "id": pid,
                "label": label,
                "available": available,
            })
        return providers

    @router.post("/api/search/query")
    async def search_with_provider(request: Request) -> Dict[str, Any]:
        """Search using a specific provider. Used by compare search mode."""
        values = await _request_values(request)
        query = str(values.get("query") or values.get("q") or "").strip()
        provider = str(values.get("provider") or "").strip()
        try:
            count = int(values.get("count") or values.get("limit") or 10)
        except Exception:
            count = 10
        if not query:
            return {"results": [], "provider": provider, "error": "query is required"}
        if provider not in PROVIDER_INFO or provider == "disabled":
            return {"results": [], "provider": provider, "error": "Unknown provider"}
        t0 = time.time()
        try:
            results = _call_provider(provider, query, min(count, 20))
            elapsed = round(time.time() - t0, 2)
            return {"results": results, "provider": provider, "time": elapsed}
        except Exception as e:
            elapsed = round(time.time() - t0, 2)
            logger.error(f"Search provider {provider} failed: {e}")
            return {"results": [], "provider": provider, "time": elapsed, "error": str(e)}

    return router
# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 84:43
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 7:1
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 36:6
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
