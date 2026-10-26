# ratios: loc_comments=87:47 imports_exports=8:4 calls_definitions=40:6
# === MODULE_BUILD ===
# id: test_build_runner
#   module_name: test_build_runner
#   module_kind: skill
#   summary: test-build skill executor — imports each CONTRACTS `call:` and runs it
#   owner: a0p maintainer
#   public_surface: run, summary, run_async
#   internal_surface: _import_callable, _run_one
#   auth_boundary: none
#   storage_boundary: read
#   network_boundary: external
#   user_data_boundary: read
#   admin_only: false
#   tests: hmmm
#   rollout: default_enabled
#   rollback: remove /api/skill/test-build route and this module
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: test_build_runner_boundaries
#   summary: test-build skill executor — imports each CONTRACTS `call:` and runs it
#   auth_boundary: none
#   storage_boundary: read
#   network_boundary: external
#   user_data_boundary: read
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: test_build_runner
#   summary: test-build skill executor — imports each CONTRACTS `call:` and runs it
#   exposes: run, summary, run_async
#   boundaries: auth:none, storage:read, network:external, user_data:read
#   owner: a0p maintainer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: test_test_build_runner
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: hmmm
# === END CONTRACTS ===
"""test-build skill executor.

Reads every `# === CONTRACTS ===` block in the source tree, imports the
function at `call:`, runs it, and reports PASS / FAIL / ERROR per contract
plus a visible untested-list of modules with no CONTRACTS block.

Per msdmd doctrine: the untested-list must remain visible.
"""
from __future__ import annotations
import asyncio
import importlib
import sys
from collections import Counter
from pathlib import Path
from typing import Any
from interdependent_lib._msdmd.parser import walk_tree


def _import_callable(call_path: str):
    if not call_path or "." not in call_path:
        raise ValueError(f"invalid call path: {call_path!r}")
    mod_path, _, fn_name = call_path.rpartition(".")
    mod = importlib.import_module(mod_path)
    return getattr(mod, fn_name)


async def _run_one(entry: dict) -> dict:
    call = entry.get("call")
    if not call or call.strip() == "hmmm":
        return {**entry, "status": "SKIP", "error": "call: hmmm (unresolved)"}
    if entry.get("deprecated"):
        return {**entry, "status": "SKIP", "error": "deprecated"}
    try:
        fn = _import_callable(call)
    except Exception as e:
        return {**entry, "status": "ERROR", "error": f"import: {type(e).__name__}: {e}"}
    try:
        if asyncio.iscoroutinefunction(fn):
            await fn()
        else:
            result = fn()
            if asyncio.iscoroutine(result):
                await result
    except AssertionError as e:
        return {**entry, "status": "FAIL", "error": str(e) or "AssertionError"}
    except Exception as e:
        return {**entry, "status": "ERROR", "error": f"{type(e).__name__}: {e}"}
    return {**entry, "status": "PASS", "error": None}


async def run_async(root: Path) -> dict:
    annotated, untested = walk_tree(root, "CONTRACTS", skip={"tests", "__pycache__", "node_modules", ".git", ".venv", "venv", "dist", "build", ".pytest_cache", ".mypy_cache", ".tox"})
    entries: list[tuple[Path, dict]] = []
    for path, es in annotated:
        for e in es:
            entries.append((path, e))
    results: list[dict[str, Any]] = []
    for path, e in entries:
        r = await _run_one(e)
        r["_file"] = str(path.relative_to(root))
        results.append(r)
    counts = Counter(r["status"] for r in results)
    return {
        "skill": "test-build",
        "root": str(root),
        "results": results,
        "counts": dict(counts),
        "untested": [str(p.relative_to(root)) for p in untested],
        "untested_count": len(untested),
    }


def run(root: Path) -> dict:
    return asyncio.run(run_async(root))


def summary(report: dict) -> str:
    c = report["counts"]
    return (
        f"test-build · {sum(c.values())} contracts · "
        f"{c.get('PASS', 0)} pass / {c.get('FAIL', 0)} fail / "
        f"{c.get('ERROR', 0)} error / {c.get('SKIP', 0)} skipped · "
        f"{report['untested_count']} modules without CONTRACTS"
    )


def main(argv: list[str] | None = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    root = Path(argv[0]).resolve() if argv else Path("/app/backend")
    rep = run(root)
    for r in rep["results"]:
        sym = {"PASS": "✓", "FAIL": "✗", "ERROR": "!", "SKIP": "-"}.get(r["status"], "?")
        tail = "" if r["status"] == "PASS" else f" — {r.get('error') or ''}"
        print(f"  {sym} {r['id']}{tail}")
    print()
    print(summary(rep))
    if rep["untested"]:
        print()
        print("UNTESTED (no CONTRACTS block):")
        for f in rep["untested"][:20]:
            print(f"  · {f}")
        if len(rep["untested"]) > 20:
            print(f"  … {len(rep['untested']) - 20} more")
    c = rep["counts"]
    return 0 if (c.get("FAIL", 0) + c.get("ERROR", 0)) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
# ratios: loc_comments=87:47 imports_exports=8:4 calls_definitions=40:6
