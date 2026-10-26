# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 8:34
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 2:1
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 0:0
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
# === MODULE_BUILD ===
# id: research
#   module_name: research
#   module_kind: service
#   summary: Research service — deep research with LLM-in-the-loop.
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
# id: research_boundaries
#   summary: Research service — deep research with LLM-in-the-loop.
#   auth_boundary: hmmm
#   storage_boundary: hmmm
#   network_boundary: hmmm
#   user_data_boundary: hmmm
#   admin_only: hmmm
#   owner: hmmm
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: research
#   summary: Research service — deep research with LLM-in-the-loop.
#   exposes: none
# === END CAPABILITIES ===
# services/research/__init__.py
"""Research service — deep research with LLM-in-the-loop."""

from .service import ResearchService, ResearchResult, ResearchSource
from .research_handler import ResearchHandler

__all__ = [
    "ResearchService",
    "ResearchResult",
    "ResearchSource",
    "ResearchHandler",
]
# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 8:34
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 2:1
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 0:0
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
