# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 15:34
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 1:2
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 4:2
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
# === MODULE_BUILD ===
# id: upload_limits
#   module_name: upload_limits
#   module_kind: hmmm
#   summary: Small helpers for route-local upload size caps.
#   owner: hmmm
#   public_surface: format_byte_limit, read_upload_limited
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
# id: upload_limits_boundaries
#   summary: Small helpers for route-local upload size caps.
#   auth_boundary: hmmm
#   storage_boundary: hmmm
#   network_boundary: hmmm
#   user_data_boundary: hmmm
#   admin_only: hmmm
#   owner: hmmm
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: upload_limits
#   summary: Small helpers for route-local upload size caps.
#   exposes: format_byte_limit, read_upload_limited
# === END CAPABILITIES ===
"""Small helpers for route-local upload size caps."""

from fastapi import HTTPException, UploadFile


def format_byte_limit(limit: int) -> str:
    if limit % (1024 * 1024) == 0:
        return f"{limit // (1024 * 1024)} MB"
    if limit % 1024 == 0:
        return f"{limit // 1024} KB"
    return f"{limit} bytes"


async def read_upload_limited(upload: UploadFile, limit: int, label: str = "Upload") -> bytes:
    """Read an UploadFile with a hard byte cap."""
    data = await upload.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(
            status_code=413,
            detail=f"{label} exceeds {format_byte_limit(limit)} limit",
        )
    return data
# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 15:34
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 1:2
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 4:2
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
