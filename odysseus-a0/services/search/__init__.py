# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 30:35
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 5:1
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 0:0
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
# === MODULE_BUILD ===
# id: search
#   module_name: search
#   module_kind: service
#   summary: Search service — web search with SearXNG.
#   owner: hmmm
#   public_surface: none
#   internal_surface: none
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
# id: search_boundaries
#   summary: Search service — web search with SearXNG.
#   auth_boundary: hmmm
#   storage_boundary: hmmm
#   network_boundary: hmmm
#   user_data_boundary: hmmm
#   admin_only: hmmm
#   owner: hmmm
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: search
#   summary: Search service — web search with SearXNG.
#   exposes: none
# === END CAPABILITIES ===
"""Search service — web search with SearXNG."""

from .core import (
    comprehensive_web_search,
    get_search_config,
    invalidate_search_cache,
    searxng_search_results,
    update_search_config,
)
from .content import fetch_webpage_content
from .providers import searxng_search, searxng_search_api, PROVIDER_INFO
from .analytics import get_search_stats, SearchEngineError, NetworkError, ParseError, RateLimitError
from .service import SearchService, SearchResult, SearchResponse

__all__ = [
    # Service interface (preferred)
    "SearchService",
    "SearchResult",
    "SearchResponse",
    # Low-level functions (for backwards compat)
    "comprehensive_web_search",
    "fetch_webpage_content",
    "get_search_config",
    "get_search_stats",
    "invalidate_search_cache",
    "searxng_search",
    "searxng_search_api",
    "searxng_search_results",
    "update_search_config",
    "PROVIDER_INFO",
    "SearchEngineError",
    "NetworkError",
    "ParseError",
    "RateLimitError",
]
# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 30:35
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 5:1
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 0:0
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
