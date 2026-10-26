# ratios: loc_comments=73:50 imports_exports=7:3 calls_definitions=23:5
# === MODULE_BUILD ===
# id: a0p_skills_frontend_module_build_runner
#   module_name: frontend_module_build_runner
#   module_kind: skill
#   summary: walks /app/frontend/src/**/*.{js,jsx,ts,tsx} and validates each module has a MODULE_BUILD block; reports COVERED / MISSING / INVALID per file
#   owner: Erin Spencer
#   public_surface: main, scan_frontend
#   internal_surface: _validate_block
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: a0p_skills.contracts.frontend_module_build_runner_smoke_holds
#   rollout: default_enabled
#   rollback: revert; frontend modules become unvalidated
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: a0p_skills_frontend_module_build_runner_boundaries
#   summary: read-only walk of the frontend source tree; emits a report to stdout/json
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: a0p_skills_frontend_module_build_runner
#   summary: read-only walk of the frontend source tree; emits a report to stdout/json
#   exposes: main, scan_frontend
#   boundaries: auth:none, storage:none, network:none, user_data:read
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: frontend_module_build_runner_smoke
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.frontend_module_build_runner_smoke_holds
# === END CONTRACTS ===
"""Walk the frontend tree and validate MODULE_BUILD coverage on every TS/JS module.

Usage::

    python -m a0p_skills.frontend_module_build_runner [path]

Exits non-zero if any non-trivial module is missing a MODULE_BUILD block.
"""
from __future__ import annotations
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from interdependent_lib._msdmd.parser import parse_file

# Default root and extensions to validate.
_DEFAULT_ROOT = Path("/app/frontend/src")
_EXTENSIONS: tuple[str, ...] = (".js", ".jsx", ".ts", ".tsx", ".mjs")
_SKIP_DIRS: frozenset[str] = frozenset({"node_modules", "build", "dist", ".next", "__tests__"})
# Tiny entrypoint / index files don't require a block.
_TRIVIAL_FILES: frozenset[str] = frozenset({"index.js", "index.jsx", "index.ts", "index.tsx", "reportWebVitals.js", "setupTests.js"})


@dataclass
class FileReport:
    path: str
    covered: bool
    block_count: int
    reason: str = ""


def _iter_files(root: Path) -> Iterable[Path]:
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        if any(part in _SKIP_DIRS for part in p.parts):
            continue
        if p.suffix.lower() not in _EXTENSIONS:
            continue
        yield p


def _is_trivial(p: Path) -> bool:
    return p.name in _TRIVIAL_FILES


def scan_frontend(root: Path = _DEFAULT_ROOT) -> dict:
    reports: list[FileReport] = []
    for p in _iter_files(root):
        if _is_trivial(p):
            continue
        blocks = parse_file(p, "MODULE_BUILD") or []
        if not blocks:
            reports.append(FileReport(str(p), False, 0, reason="missing MODULE_BUILD block"))
            continue
        # Spot-check each entry has the required keys. parse_file returns a list of
        # flat dicts keyed by field name; the first key is `id`.
        invalid_reason = ""
        for entry in blocks:
            required = ("module_name", "module_kind", "summary", "owner", "public_surface")
            missing = [k for k in required if not entry.get(k)]
            if missing:
                invalid_reason = f"entry {entry.get('id', '?')!r} missing keys: {missing}"
                break
        reports.append(FileReport(str(p), not invalid_reason, len(blocks), reason=invalid_reason))

    covered = [r for r in reports if r.covered]
    missing = [r for r in reports if not r.covered]
    return {
        "root": str(root),
        "total_modules": len(reports),
        "covered": len(covered),
        "missing": len(missing),
        "missing_files": [{"path": r.path, "reason": r.reason} for r in missing],
        "ok": len(missing) == 0,
    }


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    root = Path(argv[0]) if argv else _DEFAULT_ROOT
    if not root.is_dir():
        print(f"frontend root not found: {root}", file=sys.stderr)
        return 2

    report = scan_frontend(root)
    if "--json" in argv:
        print(json.dumps(report, indent=2))
    else:
        print(f"frontend-module-build · {report['total_modules']} modules · {report['covered']} covered · {report['missing']} missing")
        if report["missing_files"]:
            print("\nMISSING:")
            for m in report["missing_files"]:
                print(f"  · {m['path']}   ({m['reason']})")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
# ratios: loc_comments=73:50 imports_exports=7:3 calls_definitions=23:5
