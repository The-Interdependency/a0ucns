# ratios: loc_comments=199:52 imports_exports=6:7 calls_definitions=73:10
# === MODULE_BUILD ===
# id: ratios_runner
#   module_name: ratios_runner
#   module_kind: skill
#   summary: ratios skill executor — recomputes loc_comments/imports_exports/calls_definitions and gates on drift + first/last-line placement of the single-line RATIOS declaration
#   owner: a0p maintainer
#   public_surface: run, COMPUTERS, compute_loc_comments, compute_imports_exports, compute_calls_definitions
#   internal_surface: _strip_ratios_lines, _iter_source, _DOCSTRING_OPEN
#   auth_boundary: none
#   storage_boundary: read
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: hmmm
#   rollout: default_enabled
#   rollback: remove /api/skill/ratios route and this module
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: ratios_runner_boundaries
#   summary: ratios skill executor — recomputes loc_comments/imports_exports/calls_definitions per file; fails on drift
#   auth_boundary: none
#   storage_boundary: read
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: ratios_runner
#   summary: ratios skill executor — recomputes loc_comments/imports_exports/calls_definitions per file; fails on drift
#   exposes: run, COMPUTERS, compute_loc_comments, compute_imports_exports, compute_calls_definitions
#   boundaries: auth:none, storage:read, network:none, user_data:none
#   owner: a0p maintainer
# === END CAPABILITIES ===
"""ratios skill executor — recomputes canonical computers + drift gate."""
from __future__ import annotations
import os
import re
import sys
from pathlib import Path
from interdependent_lib._msdmd.parser import (
    marker_for, parse_ratios, ratios_placement, RATIO_IDS,
)


_SKIP = {"tests", "__pycache__", "node_modules", ".git", ".venv", "venv",
         "dist", "build", ".pytest_cache", ".mypy_cache", ".tox"}

# Legacy fenced block (kept so transitional files don't pollute the counts) +
# the canonical single-line form `<marker> ratios: ...`.
_RATIOS_FENCE = re.compile(r"^#\s*===\s*RATIOS\s*===.*?^#\s*===\s*END\s+RATIOS\s*===",
                           re.MULTILINE | re.DOTALL)
_RATIOS_LINE = re.compile(r"^\s*(?:#|//|--)\s*ratios:.*$", re.MULTILINE)


def _strip_ratios_lines(text: str) -> str:
    """Remove every RATIOS declaration (legacy block + single-line) so the
    ratios self-exclude from their own computation."""
    text = _RATIOS_FENCE.sub("", text)
    text = _RATIOS_LINE.sub("", text)
    return text


def _split_lines(text: str) -> list[str]:
    return text.splitlines()


_IMPORT_RE = re.compile(r"^\s*(?:import\s|from\s+\S+\s+import\s)")
_DEF_RE = re.compile(r"^\s*(?:async\s+)?def\s+\w+|^\s*class\s+\w+")
_TOP_DEF_RE = re.compile(r"^(?:async\s+)?def\s+(\w+)|^class\s+(\w+)")
_NESTED_CLASS_METHOD_RE = re.compile(r"^\s{4}(?:async\s+)?def\s+\w+")
_CALL_RE = re.compile(r"\b\w+\(")
_DOCSTRING_OPEN = re.compile(r'^\s*([rRbBuUfF]{0,2})("""|\'\'\')')


def _classify_lines(text: str) -> dict[str, list[int]]:
    """Return line index lists: code, comment, docstring, blank."""
    lines = _split_lines(text)
    in_doc = False
    quote = None
    out = {"code": [], "comment": [], "docstring": [], "blank": []}
    for i, raw in enumerate(lines):
        stripped = raw.strip()
        if not stripped:
            out["blank"].append(i)
            continue
        if in_doc:
            out["docstring"].append(i)
            if quote and quote in raw:
                in_doc = False
                quote = None
            continue
        m = _DOCSTRING_OPEN.match(raw)
        if m and stripped.startswith(("'''", '"""')) or (m and m.group(2) and stripped.startswith(m.group(1) + m.group(2))):
            q = m.group(2)
            # docstring open
            out["docstring"].append(i)
            # close on same line?
            rest = raw[m.end():]
            if q in rest:
                continue
            in_doc = True
            quote = q
            continue
        if stripped.startswith("#"):
            out["comment"].append(i)
            continue
        out["code"].append(i)
    return out


def compute_loc_comments(text: str) -> str:
    """N:M where N = non-blank non-comment code lines, M = comment+docstring lines."""
    cls = _classify_lines(_strip_ratios_lines(text))
    n = len(cls["code"])
    m = len(cls["comment"]) + len(cls["docstring"])
    return f"{n}:{m}"


def compute_imports_exports(text: str) -> str:
    text = _strip_ratios_lines(text)
    import_count = sum(1 for line in _split_lines(text) if _IMPORT_RE.match(line))
    export_count = 0
    for line in _split_lines(text):
        m = _TOP_DEF_RE.match(line)
        if m:
            name = m.group(1) or m.group(2)
            if name and not name.startswith("_"):
                export_count += 1
    if "__all__" in text:
        export_count += 1
    return f"{import_count}:{export_count}"


def compute_calls_definitions(text: str) -> str:
    text = _strip_ratios_lines(text)
    lines = _split_lines(text)
    def_count = 0
    call_count = 0
    for line in lines:
        stripped = line.strip()
        is_def_line = bool(_TOP_DEF_RE.match(line)) or bool(_NESTED_CLASS_METHOD_RE.match(line))
        if is_def_line:
            def_count += 1
            continue
        if not stripped or stripped.startswith("#"):
            continue
        # exclude string-only lines (rough docstring filter)
        if stripped.startswith(("'''", '"""')) or stripped.startswith(("'", '"')):
            continue
        if _CALL_RE.search(line):
            call_count += 1
    return f"{call_count}:{def_count}"


COMPUTERS = {
    "loc_comments": compute_loc_comments,
    "imports_exports": compute_imports_exports,
    "calls_definitions": compute_calls_definitions,
}


def _iter_source(root: Path):
    """Yield every source file under root with a known comment marker."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _SKIP]
        for fn in sorted(filenames):
            p = Path(dirpath) / fn
            if marker_for(p) is not None:
                yield p


def run(root: Path, strict: bool = False) -> dict:
    drift: list[dict] = []
    pending: list[dict] = []
    verified: list[dict] = []
    unverifiable: list[dict] = []
    misplaced: list[dict] = []
    untested: list[Path] = []
    by_file: dict[str, list[dict]] = {}
    scanned = 0
    covered = 0

    for path in _iter_source(root):
        scanned += 1
        rel = str(path.relative_to(root))
        marker = marker_for(path)
        text = path.read_text(encoding="utf-8", errors="ignore")
        entries = parse_ratios(text, marker)
        if not entries:
            untested.append(path)
            continue
        covered += 1
        by_file[rel] = entries

        first_ok, last_ok = ratios_placement(text, marker)
        if not (first_ok and last_ok):
            misplaced.append({"file": rel, "first_line": first_ok, "last_line": last_ok})

        for e in entries:
            cid = e.get("id", "")
            value = (e.get("value") or "").strip()
            if value == "hmmm":
                pending.append({"file": rel, "id": cid})
                continue
            comp = COMPUTERS.get(cid)
            if comp is None:
                unverifiable.append({"file": rel, "id": cid, "value": value})
                continue
            try:
                actual = comp(text)
            except Exception as ex:
                drift.append({"file": rel, "id": cid, "recorded": value,
                              "computed": f"<error: {ex}>"})
                continue
            if actual != value:
                drift.append({"file": rel, "id": cid, "recorded": value,
                              "computed": actual})
            else:
                verified.append({"file": rel, "id": cid, "value": value})

    return {
        "skill": "ratios",
        "root": str(root),
        "scanned": scanned,
        "covered": covered,
        "gaps_count": len(untested),
        "gaps": [str(p.relative_to(root)) for p in untested],
        "drift": drift,
        "drift_count": len(drift),
        "misplaced": misplaced,
        "misplaced_count": len(misplaced),
        "pending": pending,
        "pending_count": len(pending),
        "verified": verified,
        "verified_count": len(verified),
        "unverifiable": unverifiable,
        "by_file": by_file,
    }


def summary(rep: dict) -> str:
    return (
        f"ratios · {rep['scanned']} files · "
        f"{rep['covered']} covered / {rep['gaps_count']} gaps · "
        f"{rep['verified_count']} verified · {rep['drift_count']} drift · "
        f"{rep['misplaced_count']} misplaced · "
        f"{rep['pending_count']} hmmm · {len(rep['unverifiable'])} unverifiable"
    )


def main(argv: list[str] | None = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    strict = "--strict" in argv
    if strict:
        argv = [a for a in argv if a != "--strict"]
    root = Path(argv[0]).resolve() if argv else Path("/app/backend")
    rep = run(root, strict=strict)
    print(summary(rep))
    if rep["drift"]:
        print(f"\nDRIFT ({len(rep['drift'])}):")
        for d in rep["drift"][:20]:
            print(f"  · {d['file']} :: {d['id']}: recorded {d['recorded']} ≠ computed {d['computed']}")
    if rep["misplaced"]:
        print(f"\nMISPLACED ({len(rep['misplaced'])}) — ratios must sit on first AND last line:")
        for m in rep["misplaced"][:20]:
            print(f"  · {m['file']}: first_line={m['first_line']} last_line={m['last_line']}")
    if strict and rep["gaps"]:
        print(f"\nGAPS ({len(rep['gaps'])}):")
        for g in rep["gaps"][:30]:
            print(f"  · {g}")
    fail = rep["drift_count"] or rep["misplaced_count"] or (strict and rep["gaps_count"])
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())

# === CONTRACTS ===
# id: ratios_runner_loads
#   given: module declares its msdmd canon
#   then: the module imports cleanly under the current interpreter
#   class: integration
#   call: a0p_skills.contracts.module_imports_cleanly_holds
# === END CONTRACTS ===
# ratios: loc_comments=199:52 imports_exports=6:7 calls_definitions=73:10
