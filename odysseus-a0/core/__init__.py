# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 36:46
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 7:1
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 0:0
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
# === MODULE_BUILD ===
# id: core
#   module_name: core
#   module_kind: hmmm
#   summary: Chat Core — the essential chat experience.
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
# id: core_boundaries
#   summary: Chat Core — the essential chat experience.
#   auth_boundary: hmmm
#   storage_boundary: hmmm
#   network_boundary: hmmm
#   user_data_boundary: hmmm
#   admin_only: hmmm
#   owner: hmmm
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: core
#   summary: Chat Core — the essential chat experience.
#   exposes: none
# === END CAPABILITIES ===
# core/__init__.py
"""
Chat Core — the essential chat experience.

This package contains only what's needed for:
- Streaming LLM responses
- Session management
- Model routing
- Authentication
"""

from src.llm_core import (
    llm_call,
    llm_call_async,
    stream_llm,
    list_model_ids,
    normalize_model_id,
    LLMConfig,
)
from .auth import AuthManager
from .constants import *
from .middleware import SecurityHeadersMiddleware
from .exceptions import (
    SessionNotFoundError,
    InvalidFileUploadError,
    LLMServiceError,
    WebSearchError,
)
from .models import Session, ChatMessage
from .session_manager import SessionManager

__all__ = [
    # LLM
    "llm_call",
    "llm_call_async",
    "stream_llm",
    "list_model_ids",
    "normalize_model_id",
    "LLMConfig",
    # Auth
    "AuthManager",
    # Middleware
    "SecurityHeadersMiddleware",
    # Exceptions
    "SessionNotFoundError",
    "InvalidFileUploadError",
    "LLMServiceError",
    "WebSearchError",
    # Models
    "Session",
    "ChatMessage",
    "SessionManager",
]
# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 36:46
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 7:1
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 0:0
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
