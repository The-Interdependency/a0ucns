# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 56:60
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 4:3
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 14:7
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
# === MODULE_BUILD ===
# id: service
#   module_name: service
#   module_kind: service
#   summary: Search service — clean interface for web search.
#   owner: hmmm
#   public_surface: SearchResult, SearchResponse, SearchService
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
# id: service_boundaries
#   summary: Search service — clean interface for web search.
#   auth_boundary: hmmm
#   storage_boundary: hmmm
#   network_boundary: hmmm
#   user_data_boundary: hmmm
#   admin_only: hmmm
#   owner: hmmm
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: service
#   summary: Search service — clean interface for web search.
#   exposes: SearchResult, SearchResponse, SearchService
# === END CAPABILITIES ===
# services/search/service.py
"""Search service — clean interface for web search."""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any

from . import (
    comprehensive_web_search,
    fetch_webpage_content,
    get_search_config,
)


@dataclass
class SearchResult:
    """A single search result."""
    url: str
    title: str
    snippet: str
    content: Optional[str] = None


@dataclass
class SearchResponse:
    """Response from a search query."""
    query: str
    results: List[SearchResult]
    total: int
    cached: bool = False


class SearchService:
    """
    Web search service.

    Usage:
        service = SearchService()
        result = await service.search("python async patterns")
        for r in result.results:
            print(f"{r.title}: {r.url}")
    """

    def __init__(self, default_depth: int = 1, fetch_content: bool = True):
        self.default_depth = default_depth
        self.fetch_content = fetch_content

    async def search(
        self,
        query: str,
        depth: Optional[int] = None,
        fetch_content: Optional[bool] = None,
    ) -> SearchResponse:
        """
        Search the web.

        Args:
            query: Search query
            depth: Search depth (1=quick, 2=thorough, 3=comprehensive)
            fetch_content: Whether to fetch full page content

        Returns:
            SearchResponse with results
        """
        depth = depth or self.default_depth

        # comprehensive_web_search is synchronous and, with return_sources=True,
        # returns (context_str, [{"url", "title"}, ...]). Run it off the event
        # loop so we don't block it, and use the source list as the result rows.
        # `fetch_content` is accepted for API compatibility; the comprehensive
        # search always fetches page content.
        import asyncio
        _context, raw_results = await asyncio.to_thread(
            comprehensive_web_search,
            query,
            max_pages=10 * depth,
            return_sources=True,
        )

        results = []
        for r in raw_results:
            if not isinstance(r, dict):
                continue
            results.append(SearchResult(
                url=r.get("url", ""),
                title=r.get("title", ""),
                snippet=r.get("snippet", ""),
                content=r.get("content"),
            ))

        return SearchResponse(
            query=query,
            results=results,
            total=len(results),
        )

    async def fetch_content(self, url: str) -> Optional[str]:
        """Fetch content from a URL."""
        return await fetch_webpage_content(url)

    def get_config(self) -> Dict[str, Any]:
        """Get current search configuration."""
        return get_search_config()
# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 56:60
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 4:3
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 14:7
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
