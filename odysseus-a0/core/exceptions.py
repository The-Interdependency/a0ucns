# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 19:38
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 0:4
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 4:8
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
# === MODULE_BUILD ===
# id: exceptions
#   module_name: exceptions
#   module_kind: hmmm
#   summary: Custom exceptions for the application.
#   owner: hmmm
#   public_surface: SessionNotFoundError, InvalidFileUploadError, LLMServiceError, WebSearchError
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
# id: exceptions_boundaries
#   summary: Custom exceptions for the application.
#   auth_boundary: hmmm
#   storage_boundary: hmmm
#   network_boundary: hmmm
#   user_data_boundary: hmmm
#   admin_only: hmmm
#   owner: hmmm
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: exceptions
#   summary: Custom exceptions for the application.
#   exposes: SessionNotFoundError, InvalidFileUploadError, LLMServiceError, WebSearchError
# === END CAPABILITIES ===
# src/exceptions.py
"""Custom exceptions for the application."""

class SessionNotFoundError(Exception):
    """Raised when a requested session is not found."""
    def __init__(self, session_id: str):
        self.session_id = session_id
        super().__init__(f"Session '{session_id}' not found")

class InvalidFileUploadError(Exception):
    """Raised when a file upload fails validation."""
    def __init__(self, message: str, filename: str = None):
        self.filename = filename
        self.message = message
        super().__init__(message)

class LLMServiceError(Exception):
    """Raised when there is an error communicating with the LLM service."""
    def __init__(self, message: str, endpoint: str = None):
        self.endpoint = endpoint
        self.message = message
        super().__init__(message)

class WebSearchError(Exception):
    """Raised when there is an error with web search functionality."""
    def __init__(self, message: str, query: str = None):
        self.query = query
        self.message = message
        super().__init__(message)
# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 19:38
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 0:4
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 4:8
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
