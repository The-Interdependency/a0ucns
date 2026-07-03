# ratios: loc_comments=55:47 imports_exports=3:2 calls_definitions=18:2
# === MODULE_BUILD ===
# id: living_spec_scanner
#   module_name: living_spec
#   module_kind: service
#   summary: pure scanner over the repo that returns every msdmd block as JSON; no DB / network dependencies; used by the /api/spec/living endpoint and by contract tests
#   owner: Erin Spencer
#   public_surface: scan_repo_blocks, REPO_ROOTS
#   internal_surface: _iter_repo_files
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: a0p_skills.contracts.api_extensions_living_spec_holds
#   rollout: default_enabled
#   rollback: revert; /api/spec/living loses its source
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: living_spec_scanner_boundaries
#   summary: read-only filesystem scan
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: living_spec_scanner
#   summary: scan repo files and return msdmd block JSON
#   exposes: scan_repo_blocks, REPO_ROOTS
#   boundaries: auth:none, storage:none, network:none, user_data:read
#   owner: Erin Spencer
# === END CAPABILITIES ===
"""Pure-function repo scanner — returns every msdmd block as a JSON-safe list."""
from __future__ import annotations
from pathlib import Path


REPO_ROOTS = [
    Path("/app/backend/interdependent_lib"),
    Path("/app/backend/agents"),
    Path("/app/backend/providers"),
    Path("/app/backend/auth"),
    Path("/app/backend/a0p_skills"),
    Path("/app/backend/tests"),
    Path("/app/backend"),
    Path("/app/frontend/src"),
]
_SKIP_DIRS = {"__pycache__", "node_modules", "build", "dist", ".next", ".git"}
_EXTS = {".py", ".js", ".jsx", ".ts", ".tsx"}


def _iter_repo_files():
    seen: set[Path] = set()
    for root in REPO_ROOTS:
        if not root.is_dir():
            continue
        for p in sorted(root.rglob("*")):
            if not p.is_file() or p.suffix.lower() not in _EXTS:
                continue
            if any(part in _SKIP_DIRS for part in p.parts):
                continue
            if p in seen:
                continue
            seen.add(p)
            yield p


def scan_repo_blocks() -> list[dict]:
    """Walk the repo, parse every msdmd block (per file), return a flat list of module dicts.

    A module entry includes the path (relative to /app) plus the parsed
    MODULE_BUILD / BOUNDARIES / CAPABILITIES / CONTRACTS / RATIOS entries for
    that file. Files without a MODULE_BUILD block are skipped.
    """
    from interdependent_lib._msdmd.parser import parse_file, parse_ratios_file
    BLOCKS = ("MODULE_BUILD", "BOUNDARIES", "CAPABILITIES", "CONTRACTS", "RATIOS")
    modules: list[dict] = []
    for p in _iter_repo_files():
        try:
            entries_by_kind = {k: (parse_file(p, k) or []) for k in BLOCKS if k != "RATIOS"}
            entries_by_kind["RATIOS"] = parse_ratios_file(p) or []
        except Exception:
            entries_by_kind = {k: [] for k in BLOCKS}
        mb = entries_by_kind["MODULE_BUILD"]
        if not mb:
            continue
        head = mb[0]
        modules.append({
            "path": str(p.relative_to(Path("/app"))),
            "id": head.get("id"),
            "module_name": head.get("module_name"),
            "module_kind": head.get("module_kind"),
            "summary": head.get("summary"),
            "owner": head.get("owner"),
            "public_surface": head.get("public_surface"),
            "tests": head.get("tests"),
            "blocks": {k: entries_by_kind[k] for k in BLOCKS},
        })
    return modules


__all__ = ["scan_repo_blocks", "REPO_ROOTS"]

# === CONTRACTS ===
# id: living_spec_scanner_loads
#   given: module declares its msdmd canon
#   then: the module imports cleanly under the current interpreter
#   class: integration
#   call: a0p_skills.contracts.module_imports_cleanly_holds
# === END CONTRACTS ===

# ratios: loc_comments=55:47 imports_exports=3:2 calls_definitions=18:2
