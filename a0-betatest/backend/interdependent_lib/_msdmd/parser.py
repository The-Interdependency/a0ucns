# ratios: loc_comments=134:86 imports_exports=4:8 calls_definitions=49:10
# === MODULE_BUILD ===
# id: msdmd_parser
#   module_name: parser
#   module_kind: skill
#   summary: canonical msdmd block parser + single-line RATIOS reader (loc_comments/imports_exports/calls_definitions on first & last line)
#   owner: a0p maintainer
#   public_surface: parse_text, parse_file, walk_tree, marker_for, parse_ratios, parse_ratios_file, ratios_placement, RATIO_IDS
#   internal_surface: _MARKERS, _DEFAULT_SKIP, _block_regex, _RATIOS_LINE_RE
#   auth_boundary: none
#   storage_boundary: read
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: hmmm
#   rollout: default_enabled
#   rollback: revert to mine — last working sha in git history
#   since: 2026-05-31
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: msdmd_parser_boundaries
#   summary: canonical msdmd parser — line-for-line sync of skill-lib/msdmd/parsers/universal.py
#   auth_boundary: none
#   storage_boundary: read
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: msdmd_parser
#   summary: canonical msdmd block parser + single-line RATIOS reader
#   exposes: parse_text, parse_file, walk_tree, marker_for, parse_ratios, parse_ratios_file, ratios_placement
#   boundaries: auth:none, storage:read, network:none, user_data:none
#   owner: a0p maintainer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: test_parser
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: hmmm
# === END CONTRACTS ===
"""Universal msdmd parser — pure stdlib.

Implements the parser contract from ``msdmd/SKILL.md``: extracts every
``# === <NAME> ===`` … ``# === END <NAME> ===`` block from a source file
and returns its entries as flat dicts.

Comment marker is auto-detected by file extension. The block syntax
itself is identical across languages; only the per-line marker changes.

Public API:

    parse_text(text, block_name, marker="#") -> list[dict]
    parse_file(path, block_name)             -> list[dict]
    walk_tree(root, block_name, *, skip=None, extensions=None)
        -> tuple[annotated, untested]

This module has zero non-stdlib dependencies and is safe to copy
verbatim into any project that wants msdmd support.

Synced from The-Interdependency/skill-lib/main/msdmd/parsers/universal.py.
"""
from __future__ import annotations
import re
from pathlib import Path
from typing import Iterable

# extension → comment marker
_MARKERS: dict[str, str] = {
    ".py": "#", ".rb": "#", ".ex": "#", ".exs": "#", ".sh": "#",
    ".ts": "//", ".tsx": "//", ".js": "//", ".jsx": "//", ".mjs": "//",
    ".rs": "//", ".go": "//", ".java": "//", ".c": "//", ".cpp": "//",
    ".cc": "//", ".h": "//", ".hpp": "//", ".swift": "//", ".kt": "//",
    ".sql": "--", ".lua": "--", ".hs": "--",
}

_DEFAULT_SKIP = (
    "__pycache__", "node_modules", ".git", ".venv", "venv",
    "dist", "build", ".next", ".nuxt", "target", ".pytest_cache",
    ".mypy_cache", ".tox",
)

# Canonical ratio ids carried by the single-line RATIOS declaration.
RATIO_IDS = ("loc_comments", "imports_exports", "calls_definitions")
_RATIOS_LINE_RE = lambda m: re.compile(rf"^{re.escape(m)}\s*ratios:\s*(?P<body>.+?)\s*$")
_RATIOS_TOKEN_RE = re.compile(r"(?P<key>[a-z_]+)=(?P<val>\S+)")


def marker_for(path: Path) -> str | None:
    """Return the comment marker for a file path, or None if unsupported."""
    return _MARKERS.get(path.suffix.lower())


def _block_regex(block_name: str, marker: str) -> re.Pattern[str]:
    m = re.escape(marker)
    name = re.escape(block_name)
    return re.compile(
        rf"^{m} === {name} ===\s*$(?P<body>.*?)^{m} === END {name} ===\s*$",
        re.MULTILINE | re.DOTALL,
    )


def parse_text(text: str, block_name: str, marker: str = "#") -> list[dict]:
    """Extract every entry from every matching block in ``text``.

    Entries are flat ``dict[str, str]`` keyed by field name. The first
    line of an entry must be ``id: <id>``; subsequent lines until
    the next ``id:`` (or block end) carry indented ``<key>: <value>``
    pairs.
    """
    block_re = _block_regex(block_name, marker)
    m = re.escape(marker)
    id_re = re.compile(rf"^\s*{m}\s*id:\s*(?P<id>\S+)\s*$")
    field_re = re.compile(rf"^\s*{m}\s+(?P<key>[a-z_]+):\s*(?P<val>.+?)\s*$")

    entries: list[dict] = []
    for block in block_re.finditer(text):
        current: dict[str, str] | None = None
        for line in block.group("body").splitlines():
            line = line.rstrip()
            mid = id_re.match(line)
            if mid:
                if current is not None:
                    entries.append(current)
                current = {"id": mid.group("id")}
                continue
            if current is None:
                continue
            mf = field_re.match(line)
            if mf:
                current[mf.group("key")] = mf.group("val")
        if current is not None:
            entries.append(current)
    return entries


def parse_file(path: Path, block_name: str) -> list[dict]:
    """Parse a single file. Returns [] if the file's extension has no
    known comment marker or if the file can't be read."""
    marker = marker_for(path)
    if marker is None:
        return []
    try:
        return parse_text(path.read_text(encoding="utf-8"), block_name, marker)
    except (OSError, UnicodeDecodeError):
        return []


def parse_ratios(text: str, marker: str = "#") -> list[dict]:
    """Read single-line RATIOS declarations.

    Unlike the other msdmd declarations, RATIOS is NOT a fenced block — it is a
    single comment line of the form::

        <marker> ratios: loc_comments=N:M imports_exports=N:M calls_definitions=N:M

    The canonical placement is the file's first line and its last line. This
    reader returns one flat ``{"id", "value"}`` dict per (declaration × ratio)
    so a drift gate can verify every occurrence.
    """
    line_re = _RATIOS_LINE_RE(marker)
    out: list[dict] = []
    for raw in text.splitlines():
        lm = line_re.match(raw.rstrip())
        if not lm:
            continue
        for tm in _RATIOS_TOKEN_RE.finditer(lm.group("body")):
            out.append({"id": tm.group("key"), "value": tm.group("val")})
    return out


def parse_ratios_file(path: Path) -> list[dict]:
    """parse_ratios for a file path (marker auto-detected); [] on unreadable."""
    marker = marker_for(path)
    if marker is None:
        return []
    try:
        return parse_ratios(path.read_text(encoding="utf-8"), marker)
    except (OSError, UnicodeDecodeError):
        return []


def ratios_placement(text: str, marker: str = "#") -> tuple[bool, bool]:
    """Return (first_line_has_ratios, last_non_blank_line_has_ratios)."""
    line_re = _RATIOS_LINE_RE(marker)
    lines = text.splitlines()
    if not lines:
        return (False, False)
    first_ok = bool(line_re.match(lines[0].rstrip()))
    last_ok = False
    for raw in reversed(lines):
        if raw.strip() == "":
            continue
        last_ok = bool(line_re.match(raw.rstrip()))
        break
    return (first_ok, last_ok)


def walk_tree(
    root: Path,
    block_name: str,
    *,
    skip: Iterable[str] | None = None,
    extensions: Iterable[str] | None = None,
) -> tuple[list[tuple[Path, list[dict]]], list[Path]]:
    """Walk ``root`` and partition source files into (annotated, untested).

    ``annotated`` is a list of ``(path, entries)`` for every file that
    contains at least one entry of ``block_name``. ``untested`` is every
    other source file (still filtered by extension and skip-dirs) so
    coverage gaps remain observable.
    """
    skip_set = set(skip) if skip is not None else set(_DEFAULT_SKIP)
    ext_set = (
        set(e.lower() if e.startswith(".") else "." + e.lower() for e in extensions)
        if extensions is not None
        else set(_MARKERS.keys())
    )

    def iter_source_files(path: Path) -> Iterable[Path]:
        if path.name in skip_set:
            return
        try:
            children = sorted(path.iterdir())
        except OSError:
            return
        for child in children:
            if child.is_dir():
                if child.name in skip_set:
                    continue
                yield from iter_source_files(child)
            elif child.is_file() and child.suffix.lower() in ext_set:
                yield child

    annotated: list[tuple[Path, list[dict]]] = []
    untested: list[Path] = []
    for path in iter_source_files(root):
        entries = parse_file(path, block_name)
        if entries:
            annotated.append((path, entries))
        else:
            untested.append(path)
    return annotated, untested


# Back-compat aliases for callers that used the previous API
parse = parse_text


def walk(root: Path, block_name: str, exts: tuple[str, ...] = (".py",)):
    """Back-compat iterator API. Prefer walk_tree()."""
    annotated, untested = walk_tree(root, block_name, extensions=exts)
    for p, entries in annotated:
        yield p, entries
    for p in untested:
        yield p, []
# ratios: loc_comments=134:86 imports_exports=4:8 calls_definitions=49:10
