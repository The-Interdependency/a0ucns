# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 98:35
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 5:4
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 34:4
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
# === MODULE_BUILD ===
# id: capabilities_runner
#   module_name: capabilities_runner
#   module_kind: skill
#   summary: cap-build skill executor — parses CAPABILITIES blocks, builds capability map, flags duplicates/hmmm/gaps
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
#   rollback: remove /api/skill/capabilities route and this module
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: capabilities_runner_boundaries
#   summary: cap-build skill executor — parses CAPABILITIES blocks, builds capability map, flags duplicates/hmmm/gaps
#   auth_boundary: none
#   storage_boundary: read
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: capabilities_runner
#   summary: cap-build skill executor — parses CAPABILITIES blocks, builds capability map, flags duplicates/hmmm/gaps
#   exposes: run, validate_entry, REQUIRED_FIELDS, summary
#   boundaries: auth:none, storage:read, network:none, user_data:none
#   owner: a0p maintainer
# === END CAPABILITIES ===
"""cap-build skill executor."""
from __future__ import annotations
import sys
from collections import Counter
from pathlib import Path
from interdependent_lib._msdmd.parser import walk_tree


REQUIRED_FIELDS = ("id", "summary", "exposes")

_SKIP = {"tests", "__pycache__", "node_modules", ".git", ".venv", "venv",
         "dist", "build", ".pytest_cache", ".mypy_cache", ".tox"}


def validate_entry(entry: dict) -> list[str]:
    issues: list[str] = []
    for f in REQUIRED_FIELDS:
        if f not in entry:
            issues.append(f"missing required field: {f}")
        elif not str(entry[f]).strip():
            issues.append(f"empty required field: {f}")
    return issues


def run(root: Path) -> dict:
    annotated, untested = walk_tree(root, "CAPABILITIES", skip=_SKIP)
    entries: list[dict] = []
    invalid: list[dict] = []
    by_id: dict[str, list[str]] = {}
    duplicates: list[dict] = []
    pending = 0
    by_class: Counter = Counter()
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
            cid = e.get("id", "")
            if cid:
                by_id.setdefault(cid, []).append(rel)
            cls = e.get("class") or "unspecified"
            by_class[cls] += 1
            if (e.get("exposes") or "").lower() == "hmmm":
                pending += 1
            if (e.get("boundaries") or "").lower().find("hmmm") != -1:
                pending += 1

    for cid, files in by_id.items():
        if len(files) > 1:
            duplicates.append({"id": cid, "files": files})

    return {
        "skill": "cap-build",
        "root": str(root),
        "scanned": len(annotated) + len(untested),
        "covered": len(annotated),
        "gaps_count": len(untested),
        "gaps": [str(p.relative_to(root)) for p in untested],
        "entries": entries,
        "invalid": invalid,
        "valid_count": len(entries) - len(invalid),
        "invalid_count": len(invalid),
        "duplicates": duplicates,
        "duplicates_count": len(duplicates),
        "pending_count": pending,
        "by_class": dict(by_class),
        "by_file": by_file,
    }


def summary(rep: dict) -> str:
    return (
        f"cap-build · {rep['scanned']} files · "
        f"{rep['covered']} covered / {rep['gaps_count']} gaps · "
        f"{rep['valid_count']} valid / {rep['invalid_count']} invalid · "
        f"{rep['duplicates_count']} duplicates · {rep['pending_count']} pending"
    )


def main(argv: list[str] | None = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    root = Path(argv[0]).resolve() if argv else Path("/app/backend")
    rep = run(root)
    print(summary(rep))
    if rep["by_class"]:
        print("\nby class:")
        for k, n in sorted(rep["by_class"].items()):
            print(f"  · {k}: {n}")
    if rep["duplicates"]:
        print(f"\nDUPLICATES ({len(rep['duplicates'])}):")
        for d in rep["duplicates"][:20]:
            print(f"  · {d['id']} in {d['files']}")
    if rep["invalid"]:
        print(f"\nINVALID ({len(rep['invalid'])}):")
        for e in rep["invalid"][:20]:
            print(f"  · {e['_file']} :: {e.get('id', '<no-id>')}")
            for i in e["issues"]:
                print(f"      - {i}")
    if rep["gaps"]:
        print(f"\nGAPS ({len(rep['gaps'])}):")
        for g in rep["gaps"][:30]:
            print(f"  · {g}")
        if len(rep["gaps"]) > 30:
            print(f"  … {len(rep['gaps']) - 30} more")
    return 1 if (rep["gaps_count"] or rep["invalid_count"] or rep["duplicates_count"]) else 0


if __name__ == "__main__":
    sys.exit(main())
# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 98:35
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 5:4
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 34:4
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
