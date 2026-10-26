# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 25:32
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 4:1
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 10:1
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
# === MODULE_BUILD ===
# id: generated_images
#   module_name: generated_images
#   module_kind: hmmm
#   summary: hmmm
#   owner: hmmm
#   public_surface: resolve_generated_image_path
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
# id: generated_images_boundaries
#   summary: hmmm
#   auth_boundary: hmmm
#   storage_boundary: hmmm
#   network_boundary: hmmm
#   user_data_boundary: hmmm
#   admin_only: hmmm
#   owner: hmmm
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: generated_images
#   summary: hmmm
#   exposes: resolve_generated_image_path
# === END CAPABILITIES ===
import os
import re
from pathlib import Path

from fastapi import HTTPException


GENERATED_IMAGE_DIR = Path("data/generated_images")
GENERATED_IMAGE_RE = re.compile(
    r"^[a-f0-9]{8,64}\.(png|jpg|jpeg|webp|gif|mp4|mov|webm|mkv|m4v)$"
)
GENERATED_IMAGE_HEADERS = {
    "Cache-Control": "public, max-age=31536000, immutable",
    "X-Content-Type-Options": "nosniff",
}


def resolve_generated_image_path(filename: str) -> Path:
    if not isinstance(filename, str) or not GENERATED_IMAGE_RE.fullmatch(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")
    root = GENERATED_IMAGE_DIR.resolve()
    path = (GENERATED_IMAGE_DIR / filename).resolve()
    try:
        if os.path.commonpath([str(root), str(path)]) != str(root):
            raise ValueError
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid filename")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    return path
# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 25:32
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 4:1
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 10:1
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
