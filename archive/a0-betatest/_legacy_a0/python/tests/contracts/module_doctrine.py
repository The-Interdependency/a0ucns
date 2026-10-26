# 56:12 0:0 0:0
# DOC module: tests.contracts.module_doctrine
# DOC label: Module doctrine adherence
# DOC description: Enforces the a0p module doctrine for python/routes/*.py:
# every route file carries a complete # DOC block (module, label,
# description, tier, role — each exactly once) with role drawn from the
# allowed set, opens/closes with the # N:M annotation, and — when it
# defines a module-level APIRouter — is registered in ALL_ROUTERS.
from __future__ import annotations

import re
import pathlib

_ROUTES_DIR = pathlib.Path(__file__).resolve().parents[2] / "routes"
_INIT = _ROUTES_DIR / "__init__.py"

_REQUIRED_ONCE = ("module", "label", "description", "tier", "role")
_ALLOWED_ROLES = {
    "route", "api", "service", "engine", "orchestrator", "schema",
    "component", "page", "test", "contract", "doctrine", "config",
    "script", "adapter", "hot_swap", "module",
}
_ANNOTATION = re.compile(r"^#\s*\d+:\d+(\s+\d+:\d+){0,2}\s*$")
_DOC_LINE = re.compile(r"^# DOC (\w+):")
_ROUTER_DEF = re.compile(r"^router\s*[:=]")


def _route_files() -> list[pathlib.Path]:
    return [p for p in sorted(_ROUTES_DIR.glob("*.py")) if p.name != "__init__.py"]


def test_route_doc_blocks_are_complete() -> None:
    """Every route file declares module/label/description/tier/role exactly
    once, with role from the allowed set."""
    problems: list[str] = []
    for p in _route_files():
        keys: list[str] = []
        role_val: str | None = None
        for line in p.read_text(encoding="utf-8").splitlines():
            m = _DOC_LINE.match(line)
            if m:
                keys.append(m.group(1))
                if m.group(1) == "role":
                    role_val = line.split(":", 1)[1].strip()
        for req in _REQUIRED_ONCE:
            n = keys.count(req)
            if n != 1:
                problems.append(f"{p.name}: '# DOC {req}:' appears {n}× (want exactly 1)")
        if role_val is not None and role_val not in _ALLOWED_ROLES:
            problems.append(f"{p.name}: role '{role_val}' not in allowed set")
    assert not problems, "\n  " + "\n  ".join(problems)


def test_route_files_are_annotated() -> None:
    """Every route file opens and closes with a # N:M annotation comment."""
    problems: list[str] = []
    for p in _route_files():
        lines = [l for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
        if not lines:
            problems.append(f"{p.name}: empty file")
            continue
        if not _ANNOTATION.match(lines[0]):
            problems.append(f"{p.name}: first line is not an annotation: {lines[0]!r}")
        if not _ANNOTATION.match(lines[-1]):
            problems.append(f"{p.name}: last line is not an annotation: {lines[-1]!r}")
    assert not problems, "\n  " + "\n  ".join(problems)


def test_router_defining_files_are_registered() -> None:
    """Any route file that defines a module-level APIRouter is imported and
    placed in ALL_ROUTERS (else its endpoints never mount)."""
    init_text = _INIT.read_text(encoding="utf-8")
    imported = set(re.findall(r"from \.(\w+) import router", init_text))
    problems: list[str] = []
    for p in _route_files():
        text = p.read_text(encoding="utf-8")
        if any(_ROUTER_DEF.match(l) for l in text.splitlines()):
            if p.stem not in imported:
                problems.append(f"{p.name}: defines a router but is not imported in __init__.py")
    assert not problems, "\n  " + "\n  ".join(problems)
# 56:12 0:0 0:0
