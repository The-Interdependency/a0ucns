# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 18:34
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 1:1
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 0:0
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
# === MODULE_BUILD ===
# id: youtube
#   module_name: youtube
#   module_kind: service
#   summary: YouTube service — transcript extraction.
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
# id: youtube_boundaries
#   summary: YouTube service — transcript extraction.
#   auth_boundary: hmmm
#   storage_boundary: hmmm
#   network_boundary: hmmm
#   user_data_boundary: hmmm
#   admin_only: hmmm
#   owner: hmmm
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: youtube
#   summary: YouTube service — transcript extraction.
#   exposes: none
# === END CAPABILITIES ===
# services/youtube/__init__.py
"""YouTube service — transcript extraction."""

from .youtube_handler import (
    init_youtube,
    is_youtube_url,
    extract_youtube_id,
    extract_transcript_async,
    format_transcript_for_context,
    fetch_youtube_comments,
    format_comments_for_context,
)

__all__ = [
    "init_youtube",
    "is_youtube_url",
    "extract_youtube_id",
    "extract_transcript_async",
    "format_transcript_for_context",
    "fetch_youtube_comments",
    "format_comments_for_context",
]
# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 18:34
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 1:1
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 0:0
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
