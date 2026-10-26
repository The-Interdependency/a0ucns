# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 226:80
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 10:4
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 69:17
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
# === MODULE_BUILD ===
# id: msdmd_refactor
#   module_name: msdmd_refactor
#   module_kind: hmmm
#   summary: msdmd_refactor — the single action that sets an msdmd refactor in motion.
#   owner: hmmm
#   public_surface: refactor_text, run, summary, main
#   internal_surface: _module_name, _module_kind, _sanitize_id, _sanitize_summary, _surfaces, _derive, _render, _module_build_block, _boundaries_block, _capabilities_block, _ratios_block, _split_prefix, _iter_py
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
# id: msdmd_refactor_boundaries
#   summary: msdmd_refactor — the single action that sets an msdmd refactor in motion.
#   auth_boundary: hmmm
#   storage_boundary: hmmm
#   network_boundary: hmmm
#   user_data_boundary: hmmm
#   admin_only: hmmm
#   owner: hmmm
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: msdmd_refactor
#   summary: msdmd_refactor — the single action that sets an msdmd refactor in motion.
#   exposes: refactor_text, run, summary, main
# === END CAPABILITIES ===
"""msdmd_refactor — the single action that sets an msdmd refactor in motion.

Run once against a project root; every in-scope Python module becomes
self-declaring:

  * RATIOS               bookend block at head + tail, values computed
                         mechanically so ratios_runner is green by
                         construction (the writer uses the same COMPUTERS
                         the checker validates with).
  * MODULE_BUILD         schema-complete skeleton. Statically derivable
    BOUNDARIES           fields (module_name, public/internal surface,
    CAPABILITIES         summary, a path-inferred module_kind) are filled
                         in; everything a machine cannot honestly know
                         (owner, boundaries, tests, rollout, rollback) is
                         set to `hmmm` per the canon skill — an explicit
                         boundary object, not a guess. The later "broad
                         shallow passes" replace each hmmm with a
                         source-backed value.

Idempotent. MODULE_BUILD / BOUNDARIES / CAPABILITIES are only inserted when
absent, so a human/agent edit is never clobbered. RATIOS is always
normalized (stripped + recomputed) because it is purely mechanical.

Python-only for now: the RATIOS computers and AST surface extraction assume
Python. Other supported-extension files are reported as `deferred`.

    python -m a0p_skills.msdmd_refactor <root> [--dry-run] [--phase all|ratios|scaffold]

Usage example (this fork):

    python -m a0p_skills.msdmd_refactor .            # whole tree
    python -m a0p_skills.msdmd_refactor core         # one directory (pilot)
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from interdependent_lib._msdmd.parser import parse_text
from a0p_skills.ratios_runner import COMPUTERS

# Directories the checkers also skip — keep this in sync with the runners.
_SKIP = {
    "tests", "__pycache__", "node_modules", ".git", ".venv", "venv",
    "dist", "build", ".next", ".nuxt", "target", ".pytest_cache",
    ".mypy_cache", ".tox",
}

_RATIOS_FENCE = re.compile(
    r"^#\s*===\s*RATIOS\s*===.*?^#\s*===\s*END\s+RATIOS\s*===\s*\n?",
    re.MULTILINE | re.DOTALL,
)

# Order matters: RATIOS is computed last (it must see the scaffold blocks as
# permanent comment lines), but rendered first at the head to match canon.
_SCAFFOLD_BLOCKS = ("MODULE_BUILD", "BOUNDARIES", "CAPABILITIES")


# --------------------------------------------------------------------------
# static derivation
# --------------------------------------------------------------------------
def _module_name(path: Path) -> str:
    stem = path.stem
    return path.parent.name if stem == "__init__" else stem


def _module_kind(rel: str) -> str:
    parts = {p.lower() for p in Path(rel).parts}
    if "routes" in parts:
        return "route"
    if "services" in parts or "mcp_servers" in parts:
        return "service"
    return "hmmm"


def _sanitize_id(name: str) -> str:
    cleaned = re.sub(r"[^0-9a-zA-Z_]", "_", name).strip("_").lower()
    return cleaned or "module"


def _sanitize_summary(text: str) -> str:
    line = text.strip().splitlines()[0].strip() if text.strip() else ""
    line = line.replace("===", "").replace("#", "").strip()
    if len(line) > 110:
        line = line[:107].rstrip() + "..."
    return line or "hmmm"


def _surfaces(tree: ast.Module) -> tuple[str, str]:
    """(public_surface, internal_surface) from top-level defs/classes."""
    pub: list[str] = []
    intern: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            (intern if node.name.startswith("_") else pub).append(node.name)
    return (", ".join(pub) or "none", ", ".join(intern) or "none")


def _derive(path: Path, rel: str, text: str) -> dict:
    name = _module_name(path)
    bid = _sanitize_id(name)
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return {
            "id": bid, "module_name": name, "module_kind": _module_kind(rel),
            "summary": "hmmm", "public_surface": "hmmm", "internal_surface": "hmmm",
        }
    pub, intern = _surfaces(tree)
    return {
        "id": bid,
        "module_name": name,
        "module_kind": _module_kind(rel),
        "summary": _sanitize_summary(ast.get_docstring(tree) or ""),
        "public_surface": pub,
        "internal_surface": intern,
    }


# --------------------------------------------------------------------------
# block rendering
# --------------------------------------------------------------------------
def _render(block: str, fields: list[tuple[str, str]], *, entry_id: str) -> str:
    lines = [f"# === {block} ==="]
    lines.append(f"# id: {entry_id}")
    lines.extend(f"#   {k}: {v}" for k, v in fields)
    lines.append(f"# === END {block} ===")
    return "\n".join(lines) + "\n"


def _module_build_block(d: dict) -> str:
    return _render("MODULE_BUILD", [
        ("module_name", d["module_name"]),
        ("module_kind", d["module_kind"]),
        ("summary", d["summary"]),
        ("owner", "hmmm"),
        ("public_surface", d["public_surface"]),
        ("internal_surface", d["internal_surface"]),
        ("auth_boundary", "hmmm"),
        ("storage_boundary", "hmmm"),
        ("network_boundary", "hmmm"),
        ("user_data_boundary", "hmmm"),
        ("admin_only", "hmmm"),
        ("tests", "hmmm"),
        ("rollout", "hmmm"),
        ("rollback", "hmmm"),
    ], entry_id=d["id"])


def _boundaries_block(d: dict) -> str:
    return _render("BOUNDARIES", [
        ("summary", d["summary"]),
        ("auth_boundary", "hmmm"),
        ("storage_boundary", "hmmm"),
        ("network_boundary", "hmmm"),
        ("user_data_boundary", "hmmm"),
        ("admin_only", "hmmm"),
        ("owner", "hmmm"),
    ], entry_id=f"{d['id']}_boundaries")


def _capabilities_block(d: dict) -> str:
    return _render("CAPABILITIES", [
        ("summary", d["summary"]),
        ("exposes", d["public_surface"]),
    ], entry_id=d["id"])


_SCAFFOLD_RENDERERS = {
    "MODULE_BUILD": _module_build_block,
    "BOUNDARIES": _boundaries_block,
    "CAPABILITIES": _capabilities_block,
}


def _ratios_block(text_without_ratios: str) -> str:
    parts = [
        ("loc_comments", "lines of code to lines commented",
         "ratios_runner.compute_loc_comments"),
        ("imports_exports", "import statements to public exports",
         "ratios_runner.compute_imports_exports"),
        ("calls_definitions", "call sites to definitions",
         "ratios_runner.compute_calls_definitions"),
    ]
    out = ["# === RATIOS ==="]
    for i, (cid, summary, basis) in enumerate(parts):
        value = COMPUTERS[cid](text_without_ratios)
        out.append(f"# id: {cid}")
        out.append(f"#   summary: {summary}")
        out.append(f"#   value: {value}")
        out.append(f"#   basis: {basis}")
        if i < len(parts) - 1:
            out.append("#")
    out.append("# === END RATIOS ===")
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------
# per-file transform
# --------------------------------------------------------------------------
def _split_prefix(text: str) -> tuple[str, str]:
    """Peel off a shebang and/or coding declaration so blocks land after them."""
    lines = text.splitlines(keepends=True)
    idx = 0
    if lines and lines[idx].startswith("#!"):
        idx += 1
    if idx < len(lines) and "coding" in lines[idx] and lines[idx].lstrip().startswith("#"):
        idx += 1
    return "".join(lines[:idx]), "".join(lines[idx:])


def refactor_text(text: str, path: Path, rel: str, phase: str) -> tuple[str, dict]:
    """Return (new_text, actions). actions records what changed."""
    actions = {"ratios": False, "scaffold": []}
    derived = _derive(path, rel, text)

    prefix, body = _split_prefix(text)

    # 1. scaffold blocks (insert only when absent) — these are permanent
    #    comment lines that RATIOS must count, so they go in before RATIOS.
    if phase in ("all", "scaffold"):
        new_blocks = ""
        for block in _SCAFFOLD_BLOCKS:
            if parse_text(text, block, "#"):
                continue  # already declared — never clobber
            new_blocks += _SCAFFOLD_RENDERERS[block](derived)
            actions["scaffold"].append(block)
        if new_blocks:
            body = new_blocks + body

    # 2. RATIOS — strip any existing fence, recompute on the post-scaffold
    #    body (sans ratios), then bookend head + tail. Green by construction.
    if phase in ("all", "ratios"):
        body = _RATIOS_FENCE.sub("", body)
        no_ratios = prefix + body
        block = _ratios_block(no_ratios)
        if not body.endswith("\n"):
            body += "\n"
        body = block + body
        if not body.endswith("\n"):
            body += "\n"
        body = body + block
        actions["ratios"] = True

    return prefix + body, actions


# --------------------------------------------------------------------------
# tree walk
# --------------------------------------------------------------------------
def _iter_py(root: Path):
    if root.is_file():
        if root.suffix == ".py":
            yield root
        return
    for child in sorted(root.iterdir()):
        if child.is_dir():
            if child.name in _SKIP:
                continue
            yield from _iter_py(child)
        elif child.is_file() and child.suffix == ".py":
            yield child


def run(root: Path, *, phase: str = "all", dry_run: bool = False) -> dict:
    root = root.resolve()
    base = root if root.is_dir() else root.parent
    changed: list[dict] = []
    skipped: list[str] = []
    for path in _iter_py(root):
        rel = str(path.relative_to(base))
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            skipped.append(rel)
            continue
        new_text, actions = refactor_text(text, path, rel, phase)
        if new_text != text:
            if not dry_run:
                path.write_text(new_text, encoding="utf-8")
            changed.append({"file": rel, **actions})
    return {
        "tool": "msdmd_refactor",
        "root": str(root),
        "phase": phase,
        "dry_run": dry_run,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "changed_count": len(changed),
        "skipped_count": len(skipped),
        "changed": changed,
        "skipped": skipped,
    }


def summary(rep: dict) -> str:
    ratios = sum(1 for c in rep["changed"] if c.get("ratios"))
    scaffold = sum(1 for c in rep["changed"] if c.get("scaffold"))
    mode = "DRY-RUN" if rep["dry_run"] else "applied"
    return (
        f"msdmd_refactor [{mode}] · phase={rep['phase']} · "
        f"{rep['changed_count']} files changed "
        f"({ratios} ratios, {scaffold} scaffolded) · "
        f"{rep['skipped_count']} skipped"
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="msdmd refactor — single-action writer")
    ap.add_argument("root", nargs="?", default=".", help="project root or subdir")
    ap.add_argument("--phase", choices=["all", "ratios", "scaffold"], default="all")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--report", help="write the JSON report to this path")
    args = ap.parse_args(argv)

    rep = run(Path(args.root), phase=args.phase, dry_run=args.dry_run)
    print(summary(rep))
    if args.report:
        Path(args.report).write_text(json.dumps(rep, indent=2), encoding="utf-8")
        print(f"report → {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 226:80
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 10:4
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 69:17
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
