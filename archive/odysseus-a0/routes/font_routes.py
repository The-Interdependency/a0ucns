# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 40:38
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 3:1
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 15:4
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
# === MODULE_BUILD ===
# id: font_routes
#   module_name: font_routes
#   module_kind: route
#   summary: Custom font discovery — lists user-supplied font files in static/fonts/custom/.
#   owner: hmmm
#   public_surface: setup_font_routes
#   internal_surface: _split_family_token, _derive_family
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
# id: font_routes_boundaries
#   summary: Custom font discovery — lists user-supplied font files in static/fonts/custom/.
#   auth_boundary: hmmm
#   storage_boundary: hmmm
#   network_boundary: hmmm
#   user_data_boundary: hmmm
#   admin_only: hmmm
#   owner: hmmm
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: font_routes
#   summary: Custom font discovery — lists user-supplied font files in static/fonts/custom/.
#   exposes: setup_font_routes
# === END CAPABILITIES ===
"""Custom font discovery — lists user-supplied font files in static/fonts/custom/."""
import os
import re
from fastapi import APIRouter

CUSTOM_FONTS_DIR = os.path.join("static", "fonts", "custom")
FONT_EXTENSIONS = {".ttf", ".otf", ".woff", ".woff2"}
FAMILY_SUFFIX_WORDS = ("Display", "Rounded", "Serif", "Sans", "Mono", "Code", "Text")


def _split_family_token(token):
    """Split common compact font-family suffixes without breaking brand names."""
    for suffix in FAMILY_SUFFIX_WORDS:
        if token.endswith(suffix) and len(token) > len(suffix):
            return f"{token[:-len(suffix)]} {suffix}"
    return re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', token)


def _derive_family(filename):
    """Derive a font-family name from a filename like 'JetBrainsMono-Regular.woff2' → 'JetBrains Mono'."""
    name = os.path.splitext(filename)[0]
    # Strip common weight/style suffixes
    name = re.sub(
        r'[-_ ]?(Thin|ExtraLight|UltraLight|Light|Regular|Medium|SemiBold|DemiBold|Bold|ExtraBold|UltraBold|Black|Heavy|Italic|Oblique|Variable|VF)$',
        '', name, flags=re.IGNORECASE
    )
    # Replace dashes/underscores with spaces
    name = re.sub(r'[-_]+', ' ', name).strip()
    name = " ".join(_split_family_token(part) for part in name.split())
    return name or filename


def setup_font_routes():
    router = APIRouter(prefix="/api/fonts", tags=["fonts"])

    @router.get("/custom")
    async def list_custom_fonts():
        """Return available custom fonts grouped by derived family name."""
        os.makedirs(CUSTOM_FONTS_DIR, exist_ok=True)
        families = {}
        for f in sorted(os.listdir(CUSTOM_FONTS_DIR)):
            ext = os.path.splitext(f)[1].lower()
            if ext not in FONT_EXTENSIONS:
                continue
            family = _derive_family(f)
            if family not in families:
                families[family] = []
            families[family].append({
                "file": f,
                "url": f"/static/fonts/custom/{f}",
                "format": ext.lstrip('.'),
            })
        return {"fonts": families}

    return router
# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 40:38
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 3:1
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 15:4
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
