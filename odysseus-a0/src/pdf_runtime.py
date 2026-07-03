# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 10:34
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 1:1
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 1:1
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
# === MODULE_BUILD ===
# id: pdf_runtime
#   module_name: pdf_runtime
#   module_kind: hmmm
#   summary: Small helpers for optional PDF runtime dependencies.
#   owner: hmmm
#   public_surface: load_pymupdf_for_pdf_viewer
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
# id: pdf_runtime_boundaries
#   summary: Small helpers for optional PDF runtime dependencies.
#   auth_boundary: hmmm
#   storage_boundary: hmmm
#   network_boundary: hmmm
#   user_data_boundary: hmmm
#   admin_only: hmmm
#   owner: hmmm
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: pdf_runtime
#   summary: Small helpers for optional PDF runtime dependencies.
#   exposes: load_pymupdf_for_pdf_viewer
# === END CAPABILITIES ===
"""Small helpers for optional PDF runtime dependencies."""

PDF_VIEWER_PYMUPDF_MISSING = (
    "PDF viewer requires PyMuPDF. Install optional PDF dependencies with "
    "`pip install -r requirements-optional.txt` (PyMuPDF is AGPL-3.0)."
)


def load_pymupdf_for_pdf_viewer():
    """Return the PyMuPDF module, or raise a user-facing setup hint."""
    try:
        import fitz  # PyMuPDF, optional
    except ImportError as exc:
        raise RuntimeError(PDF_VIEWER_PYMUPDF_MISSING) from exc
    return fitz
# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 10:34
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 1:1
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 1:1
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
