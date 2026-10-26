# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 105:35
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 5:4
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 28:4
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
# === MODULE_BUILD ===
# id: boundaries_runner
#   module_name: boundaries_runner
#   module_kind: skill
#   summary: risk-boundary-build skill executor — validates BOUNDARIES blocks against canon schema; reports gaps + hmmm
#   owner: a0p maintainer
#   public_surface: run, validate_entry, REQUIRED_FIELDS, summary
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: read
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: hmmm
#   rollout: default_enabled
#   rollback: remove /api/skill/boundaries route and this module
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: boundaries_runner_boundaries
#   summary: risk-boundary-build skill executor — validates BOUNDARIES blocks against canon schema; reports gaps + hmmm
#   auth_boundary: none
#   storage_boundary: read
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: boundaries_runner
#   summary: risk-boundary-build skill executor — validates BOUNDARIES blocks against canon schema; reports gaps + hmmm
#   exposes: run, validate_entry, REQUIRED_FIELDS, summary
#   boundaries: auth:none, storage:read, network:none, user_data:none
#   owner: a0p maintainer
# === END CAPABILITIES ===
"""risk-boundary-build skill executor."""
from __future__ import annotations
import sys
from collections import Counter
from pathlib import Path
from interdependent_lib._msdmd.parser import walk_tree


REQUIRED_FIELDS = (
    "id", "summary",
    "auth_boundary", "storage_boundary", "network_boundary",
    "user_data_boundary", "admin_only",
)

_AUTH = {"none", "read", "write", "admin", "hmmm"}
_STORAGE = {"none", "read", "write", "delete", "migration", "hmmm"}
_NETWORK = {"none", "internal", "external", "hmmm"}
_USER_DATA = {"none", "read", "write", "delete", "hmmm"}
_BOOL_HMMM = {"true", "false", "hmmm"}

_ENUMS = {
    "auth_boundary": _AUTH,
    "storage_boundary": _STORAGE,
    "network_boundary": _NETWORK,
    "user_data_boundary": _USER_DATA,
    "admin_only": _BOOL_HMMM,
}


def validate_entry(entry: dict) -> list[str]:
    issues: list[str] = []
    for f in REQUIRED_FIELDS:
        if f not in entry:
            issues.append(f"missing required field: {f}")
        elif not str(entry[f]).strip():
            issues.append(f"empty required field: {f}")
    for field, allowed in _ENUMS.items():
        v = (entry.get(field) or "").lower()
        if v and v not in allowed:
            issues.append(f"{field}={v!r} not in {sorted(allowed)}")
    return issues


_SKIP = {"tests", "__pycache__", "node_modules", ".git", ".venv", "venv",
         "dist", "build", ".pytest_cache", ".mypy_cache", ".tox"}


def run(root: Path) -> dict:
    annotated, untested = walk_tree(root, "BOUNDARIES", skip=_SKIP)
    entries: list[dict] = []
    invalid: list[dict] = []
    hmmm_count = 0
    risk_summary: Counter = Counter()
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
            for f in ("auth_boundary", "storage_boundary", "network_boundary",
                      "user_data_boundary", "admin_only"):
                v = (e.get(f) or "").lower()
                if v == "hmmm":
                    hmmm_count += 1
                if v not in ("none", "false", "hmmm", ""):
                    risk_summary[f"{f}={v}"] += 1

    return {
        "skill": "risk-boundary-build",
        "root": str(root),
        "scanned": len(annotated) + len(untested),
        "covered": len(annotated),
        "gaps_count": len(untested),
        "gaps": [str(p.relative_to(root)) for p in untested],
        "entries": entries,
        "invalid": invalid,
        "valid_count": len(entries) - len(invalid),
        "invalid_count": len(invalid),
        "hmmm_count": hmmm_count,
        "risk_summary": dict(risk_summary),
        "by_file": by_file,
    }


def summary(rep: dict) -> str:
    return (
        f"risk-boundary-build · {rep['scanned']} files · "
        f"{rep['covered']} covered / {rep['gaps_count']} gaps · "
        f"{rep['valid_count']} valid / {rep['invalid_count']} invalid · "
        f"{rep['hmmm_count']} hmmm fields"
    )


def main(argv: list[str] | None = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    root = Path(argv[0]).resolve() if argv else Path("/app/backend")
    rep = run(root)
    print(summary(rep))
    if rep["risk_summary"]:
        print("\nrisk surface (non-none):")
        for k, n in sorted(rep["risk_summary"].items(), key=lambda kv: -kv[1]):
            print(f"  · {k}: {n}")
    if rep["invalid"]:
        print("\nINVALID:")
        for e in rep["invalid"]:
            print(f"  · {e['_file']} :: {e.get('id', '<no-id>')}")
            for i in e["issues"]:
                print(f"      - {i}")
    if rep["gaps"]:
        print(f"\nGAPS ({len(rep['gaps'])}):")
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
#   value: 105:35
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 5:4
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 28:4
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
