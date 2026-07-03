# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 107:50
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 5:4
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 38:4
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
# === MODULE_BUILD ===
# id: module_build_runner
#   module_name: module_build_runner
#   module_kind: skill
#   summary: meta-module-build skill executor — validates MODULE_BUILD schema + gap report
#   owner: a0p maintainer
#   public_surface: run, validate_entry, REQUIRED_FIELDS, BOUNDARY_FIELDS, summary
#   internal_surface: _allowed_module_kinds
#   auth_boundary: none
#   storage_boundary: read
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: hmmm
#   rollout: default_enabled
#   rollback: remove /api/skill/module-build route and this module
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: module_build_runner_boundaries
#   summary: meta-module-build skill executor — validates MODULE_BUILD schema + gap report
#   auth_boundary: none
#   storage_boundary: read
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: module_build_runner
#   summary: meta-module-build skill executor — validates MODULE_BUILD schema + gap report
#   exposes: run, validate_entry, REQUIRED_FIELDS, BOUNDARY_FIELDS, summary
#   boundaries: auth:none, storage:read, network:none, user_data:none
#   owner: a0p maintainer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: test_module_build_runner
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: hmmm
# === END CONTRACTS ===
"""meta-module-build skill executor.

Reads every `# === MODULE_BUILD ===` block, validates the required schema,
groups by module_kind and boundary risk, and emits a coverage gap list of
modules without any MODULE_BUILD declaration.

Per msdmd doctrine: gap list MUST remain visible in normal output.
"""
from __future__ import annotations
import sys
from collections import Counter
from pathlib import Path
from interdependent_lib._msdmd.parser import walk_tree


REQUIRED_FIELDS = (
    "id", "module_name", "module_kind", "summary", "owner",
    "public_surface", "internal_surface", "tests", "rollout", "rollback",
    # boundary fields are mandatory per meta-module-build SKILL.md
    "auth_boundary", "storage_boundary", "network_boundary",
    "user_data_boundary", "admin_only",
)

BOUNDARY_FIELDS = (
    "auth_boundary", "storage_boundary", "network_boundary",
    "user_data_boundary", "admin_only",
)

_ALLOWED_KINDS = {
    "skill", "service", "route", "adapter", "engine", "instrument",
    "ui_panel", "schema", "migration", "worker", "experiment", "hmmm",
}


def validate_entry(entry: dict) -> list[str]:
    """Return list of human-readable issues. Empty list = valid."""
    issues: list[str] = []
    for f in REQUIRED_FIELDS:
        if f not in entry:
            issues.append(f"missing required field: {f}")
        elif not str(entry[f]).strip():
            issues.append(f"empty required field: {f}")
    if entry.get("module_kind") and entry["module_kind"] not in _ALLOWED_KINDS:
        issues.append(
            f"module_kind={entry['module_kind']!r} not in {sorted(_ALLOWED_KINDS)}"
        )
    return issues


def run(root: Path) -> dict:
    annotated, untested = walk_tree(root, "MODULE_BUILD", skip={"tests", "__pycache__", "node_modules", ".git", ".venv", "venv", "dist", "build", ".pytest_cache", ".mypy_cache", ".tox"})
    entries: list[dict] = []
    invalid: list[dict] = []
    by_kind: Counter = Counter()
    boundary_risk: Counter = Counter()
    by_file: dict[str, list[dict]] = {}

    for path, es in annotated:
        rel = str(path.relative_to(root))
        by_file[rel] = es
        for e in es:
            e2 = {**e, "_file": rel}
            issues = validate_entry(e)
            if issues:
                invalid.append({**e2, "issues": issues})
            entries.append(e2)
            kind = e.get("module_kind", "hmmm")
            by_kind[kind] += 1
            for bf in BOUNDARY_FIELDS:
                v = (e.get(bf) or "").lower()
                # any boundary that isn't "none"/"false"/"hmmm" is real surface
                if v not in ("none", "false", "hmmm", ""):
                    boundary_risk[f"{bf}={v}"] += 1

    untested_list = [str(p.relative_to(root)) for p in untested]
    return {
        "skill": "meta-module-build",
        "root": str(root),
        "scanned": len(annotated) + len(untested),
        "covered": len(annotated),
        "gaps_count": len(untested),
        "gaps": untested_list,
        "entries": entries,
        "invalid": invalid,
        "valid_count": len(entries) - len(invalid),
        "invalid_count": len(invalid),
        "by_kind": dict(by_kind),
        "boundary_risk": dict(boundary_risk),
        "by_file": by_file,
    }


def summary(rep: dict) -> str:
    return (
        f"meta-module-build · {rep['scanned']} files · "
        f"{rep['covered']} covered / {rep['gaps_count']} gaps · "
        f"{rep['valid_count']} valid / {rep['invalid_count']} invalid manifests"
    )


def main(argv: list[str] | None = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    root = Path(argv[0]).resolve() if argv else Path("/app/backend")
    rep = run(root)
    print(summary(rep))
    print()
    if rep["by_kind"]:
        print("by kind:")
        for k, n in sorted(rep["by_kind"].items()):
            print(f"  · {k}: {n}")
        print()
    if rep["boundary_risk"]:
        print("boundary risk (non-none surfaces):")
        for k, n in sorted(rep["boundary_risk"].items(), key=lambda kv: -kv[1]):
            print(f"  · {k}: {n}")
        print()
    if rep["invalid"]:
        print("INVALID manifests:")
        for e in rep["invalid"]:
            print(f"  · {e['_file']} :: {e.get('id', '<no-id>')}")
            for i in e["issues"]:
                print(f"      - {i}")
        print()
    if rep["gaps"]:
        print("GAPS (no MODULE_BUILD block):")
        for g in rep["gaps"][:30]:
            print(f"  · {g}")
        if len(rep["gaps"]) > 30:
            print(f"  … {len(rep['gaps']) - 30} more")
    return 1 if (rep["gaps_count"] or rep["invalid_count"]) else 0


if __name__ == "__main__":
    sys.exit(main())
# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 107:50
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 5:4
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 38:4
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
