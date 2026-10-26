# ratios: loc_comments=87:49 imports_exports=5:3 calls_definitions=26:4
# === MODULE_BUILD ===
# id: msdmd_runner
#   module_name: runner
#   module_kind: skill
#   summary: msdmd CAPABILITIES coverage runner (deprecated in favour of skills.module_build_runner)
#   owner: a0p maintainer
#   public_surface: walk, report, main
#   internal_surface: SKIP_DIRS, _format_human
#   auth_boundary: none
#   storage_boundary: read
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: hmmm
#   rollout: default_enabled
#   rollback: remove module and call sites
#   deprecated: prefer skills.module_build_runner for canonical MODULE_BUILD coverage
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: msdmd_runner_boundaries
#   summary: msdmd CAPABILITIES coverage runner (deprecated in favour of skills.module_build_runner)
#   auth_boundary: none
#   storage_boundary: read
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: msdmd_runner
#   summary: msdmd CAPABILITIES coverage runner (deprecated in favour of skills.module_build_runner)
#   exposes: walk, report, main
#   boundaries: auth:none, storage:read, network:none, user_data:none
#   owner: a0p maintainer
# === END CAPABILITIES ===
"""msdmd runner — walks a tree, reports per-file entries + gap list.

Kept for back-compat with the earlier CAPABILITIES-block experiment.
The canonical executors live under ``a0p_skills.test_build`` and
``a0p_skills.meta_module_build`` and use this module's parser.
"""
from __future__ import annotations
import sys
from pathlib import Path
from .parser import walk_tree


SKIP_DIRS = {
    "__pycache__", "node_modules", ".git", ".venv", "venv", "env",
    "build", "dist", ".next", ".cache", "tests",
}


def walk(root: Path, block_name: str, exts: tuple[str, ...] = (".py",)):
    """Yield (path, entries) for every source file under `root`."""
    annotated, untested = walk_tree(root, block_name, extensions=exts)
    for p, e in annotated:
        yield p, e
    for p in untested:
        yield p, []


def report(
    root: Path,
    block_name: str = "CAPABILITIES",
    exts: tuple[str, ...] = (".py",),
) -> dict:
    """Aggregate coverage + gap list for `block_name` under `root`."""
    annotated, untested = walk_tree(root, block_name, extensions=exts)
    by_file: dict[str, list[dict]] = {}
    gaps: list[str] = []
    for p, entries in annotated:
        by_file[str(p.relative_to(root))] = entries
    for p in untested:
        rel = str(p.relative_to(root))
        by_file[rel] = []
        gaps.append(rel)
    scanned = len(annotated) + len(untested)
    return {
        "block_name": block_name,
        "root": str(root),
        "scanned": scanned,
        "covered": scanned - len(gaps),
        "gaps_count": len(gaps),
        "gaps": gaps,
        "by_file": by_file,
    }


def _format_human(r: dict) -> str:
    lines: list[str] = []
    lines.append(f"msdmd · {r['block_name']} · root={r['root']}")
    lines.append(f"scanned={r['scanned']}  covered={r['covered']}  gaps={r['gaps_count']}")
    lines.append("")
    if r["gaps"]:
        lines.append("GAPS (missing block):")
        for g in r["gaps"]:
            lines.append(f"  · {g}")
        lines.append("")
    lines.append("ENTRIES:")
    for f, entries in r["by_file"].items():
        if not entries:
            continue
        lines.append(f"  {f}")
        for e in entries:
            extras = [f"{k}={v}" for k, v in e.items() if k != "id"]
            lines.append(f"    - {e['id']}" + (("  " + " · ".join(extras)) if extras else ""))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    block = "CAPABILITIES"
    root = Path("/app/backend")
    as_json = False
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("-b", "--block"):
            block = argv[i + 1]
            i += 2
            continue
        if a in ("-r", "--root"):
            root = Path(argv[i + 1])
            i += 2
            continue
        if a == "--json":
            as_json = True
            i += 1
            continue
        i += 1
    r = report(root, block)
    if as_json:
        import json
        print(json.dumps(r, indent=2))
    else:
        print(_format_human(r))
    return 1 if r["gaps_count"] else 0


if __name__ == "__main__":
    sys.exit(main())

# === CONTRACTS ===
# id: msdmd_runner_loads
#   given: module declares its msdmd canon
#   then: the module imports cleanly under the current interpreter
#   class: integration
#   call: a0p_skills.contracts.module_imports_cleanly_holds
# === END CONTRACTS ===
# ratios: loc_comments=87:49 imports_exports=5:3 calls_definitions=26:4
