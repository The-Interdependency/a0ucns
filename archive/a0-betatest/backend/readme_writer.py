# ratios: loc_comments=242:62 imports_exports=4:2 calls_definitions=40:4
# === MODULE_BUILD ===
# id: readme_writer
#   module_name: readme_writer
#   module_kind: service
#   summary: regenerates /app/README.md on every backend startup from the living spec (scan_repo_blocks) as a narrative README — an Overview, a per-subsystem Architecture walkthrough (each subsystem gets a prose lead plus its modules' full narratives), and a by-kind module index; deterministic and never raises
#   owner: Erin Spencer
#   public_surface: write_readme
#   internal_surface: _subsystem, _render_modules, _format_kind_index
#   auth_boundary: none
#   storage_boundary: write
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: a0p_skills.contracts.module_imports_cleanly_holds
#   rollout: default_enabled
#   rollback: revert; README.md stops auto-regenerating
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: readme_writer_boundaries
#   summary: read-only spec scan + write to /app/README.md
#   auth_boundary: none
#   storage_boundary: write
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: readme_writer
#   summary: living-spec → README.md
#   exposes: write_readme
#   boundaries: auth:none, storage:write, network:none, user_data:read
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: readme_writer_loads
#   given: module declares its msdmd canon
#   then: the module imports cleanly under the current interpreter
#   class: integration
#   call: a0p_skills.contracts.module_imports_cleanly_holds
# === END CONTRACTS ===
"""Regenerate /app/README.md from the living spec on every backend start.

The README is not hand-written: it is a *projection* of the codebase's own
documentation. Every module carries a ``# === MODULE_BUILD ===`` block whose
``summary`` field is that module's narrative; this writer harvests them via
``living_spec.scan_repo_blocks`` and arranges them into a document that reads
like a README — an Overview, an Architecture walkthrough that introduces each
subsystem in prose before listing its modules' full narratives, and a compact
by-kind index. Deterministic, side-effect-free apart from the single write,
and never raises (a failed scan yields a 0 return, leaving any prior README in
place).
"""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path


# Overview prose — the one-paragraph "what is this" a reader meets first.
_OVERVIEW = (
    "**a0p** is a donation-funded research instrument: a BYOK (bring-your-own-key) "
    "multi-model AI workspace wrapped around a native, deterministic inference "
    "engine — **a0(zfae)** — that is rebuilt-from-spec against The-Interdependency "
    "canon (PTCA / PCTA / PCNA / PCEA). You connect your own provider keys "
    "(OpenAI, Anthropic, Gemini, xAI), instantiate semi-permanent agents from "
    "fully-editable character sheets, and chat through a sentinel-gated runtime "
    "that can call tools mid-thought, distill from multiple teachers in the "
    "Training Room, and audit every state transition on a hash-linked FIQ tape. "
    "The whole codebase is documentation-as-code: every module declares its own "
    "manifest, contracts, boundaries, and line-ratios, and this README is "
    "regenerated from those declarations on every boot."
)

# Ordered subsystem walkthrough. Each entry: (key, title, narrative). The key is
# matched against a module's path by `_subsystem`. Order here is the reading
# order in the Architecture section; any subsystem not listed is appended under
# "Other" so nothing is ever dropped.
_SUBSYSTEMS: list[tuple[str, str, str]] = [
    ("core", "Core service & API surface",
     "The FastAPI application and its REST surfaces — health, BYOK key vault, "
     "per-site env vault, model inventory, sessions, drafts, the AIMMH chat "
     "endpoints, the inspector, the tools/MCP/skills surface, admin-editable "
     "settings, and the living-spec endpoint. MongoDB (Motor) is the only "
     "datastore; credentials are Fernet-encrypted at rest."),
    ("auth", "Authentication",
     "Hybrid identity: custom JWT auth (username + email + ≥16-char passphrase, "
     "bcrypt, httpOnly cookies, brute-force lockout keyed by identifier) plus "
     "Emergent Google and GitHub OAuth. An admin account is idempotently seeded "
     "from the environment on every boot."),
    ("providers", "BYOK provider adapters",
     "Thin, uniform adapters that front each vendor over raw httpx — list models "
     "and run a completion against a key the user supplied. A shared Protocol "
     "keeps OpenAI, Anthropic, Gemini, and xAI behind one calling contract; the "
     "build carries zero runtime dependency on any hosting vendor."),
    ("agents", "Agents — character-sheet instances",
     "Agents are treated as users: semi-permanent, character-sheet-bound "
     "instances that each own their Φ/Ψ/Ω and memory rings plus a per-instance "
     "ZFAE weight bank and archive. The schema covers the full editable surface "
     "(modes, models, persona, tools_allowed, memory seeds, boundaries)."),
    ("zfae", "a0(zfae) — native inference engine",
     "The heart of the instrument: a pure, deterministic symbolic/state engine "
     "with no LLM dependency. It parses a prompt into semantic features, folds "
     "them through Φ/Ψ/Ω ring transitions, and decodes text as a reproducible "
     "function of state (Route A inscribes the continuous field onto a private "
     "per-agent gonal; Route B is the energy-conditioned compositor). It carries "
     "long-term memory of the repo's own living spec, trains by teacher "
     "distillation across a three-core weight bank, and gates every turn through "
     "the 13 sentinels before replying."),
    ("pcea", "PCEA — prime-circular encryption substrate",
     "Prime-circular bijective base encryption over the first 53 primes, keyed "
     "by the previous state. The 'this-state / last-state' cross-cut kernel is "
     "what binds one inference tick to the next and seeds the decoder's "
     "deterministic generation."),
    ("ptca", "PTCA — the seeds layer",
     "The seed stratum of the layered model: prime-indexed tensors and the "
     "'seed-as-tensor' projection upward. The current implementation is the "
     "pre-stratified flat shape; the canon Fiq→Circle→Seed rebuild against "
     "prime_core is tracked as future work."),
    ("pcta", "PCTA — the circle layer",
     "Seven PCNA tensors arranged on a {7/2} heptagram, wrapped in a UCNS "
     "structural mirror, with an aggregate 'circle-as-tensor' projection into "
     "the next layer."),
    ("pcna", "PCNA — six-ring inference engine",
     "The simplified six-ring engine (Φ Ψ Ω Θ Σ Ε): three 157-prime cores plus "
     "scalar ring signals, dual prime-ring memory (LT/ST), phase modulation, and "
     "a substrate-signature observer. The full 61-seed canon topology rebuild is "
     "tracked as future work."),
    ("network", "Network — canonical PCNA binder",
     "The top-level binder that assembles the rings on the layered substrate, "
     "advances ticks with the PCEA cross-cut between heartbeats, sources the Σ "
     "host-integrity observer for tamper-evidence, and hosts the private carrier "
     "disk behind the Θ microkernel."),
    ("fiq", "FIQ — audited motion & sentinels",
     "The boundary law for audited motion between strata: the smallest auditable "
     "gate, the flux equation that meters it, the 3/5/7 tick schedule, the nine "
     "base sentinels plus R0 orchestration root, and an append-only, hash-chained "
     "audit log mirrored to MongoDB and verifiable end-to-end."),
    ("gonal", "Gonal — the 157-gonal carrier",
     "The structural carrier: public invariants (face, chirality, class tags, "
     "adjacency, bones) over a 157-position polygon, a position-reflection mirror, "
     "and a three-gonal registry (default / mirror / private) that resolves an "
     "agent's per-core triplet. Private disk material is only ever loaded behind "
     "the Θ microkernel, never inline."),
    ("aimmh", "AIMMH — multi-model orchestration",
     "Pure-async orchestration patterns over a single ``call_fn(model_id, "
     "messages)`` — single, fan-out, daisy-chain, synthesize, and council — that "
     "power the cross-vendor chat carousel."),
    ("tools", "Tools & MCP",
     "A sentinel-gated tool layer: an in-process registry whose every invocation "
     "is evaluated by the 13 sentinels (a cliff halts and raises a pending "
     "override), built-in native tools, user-registered webhook tools (HMAC-"
     "signed), a provider-agnostic agentic tool-use loop, an outbound MCP relay, "
     "and a0p exposed inbound as an MCP server."),
    ("skills", "Skills",
     "A per-user and global skill catalog with jaccard overlap detection, plus a "
     "one-way sync that pulls canonical skills from The-Interdependency/skill-lib "
     "on GitHub."),
    ("a0p_skills", "a0p_skills — documentation-as-code runners",
     "This project's own msdmd skill executors: they parse and validate every "
     "MODULE_BUILD / CONTRACTS / BOUNDARIES / CAPABILITIES block and the "
     "single-line RATIOS declaration, run each contract's ``call:`` path, and "
     "gate on coverage, drift, and placement. The same runners power the "
     "Inspector page."),
    ("msdmd", "msdmd — the canon parser",
     "The pure-stdlib block parser and single-line RATIOS reader, synced from "
     "the upstream skill-lib, plus the legacy coverage runner."),
    ("interdependent_lib", "interdependent_lib — meta-package",
     "The umbrella package that exposes the pcea / ptca / pcna / aimmh / zfae "
     "substrata."),
    ("pages", "Frontend — pages",
     "The routed screens: Workspace (chat + audit tape + override modal), Agents, "
     "Sentinels, Overrides, Inspector, Inventory, Key & Custom-key vaults, Env "
     "Vault, Drafts, Skills, Tools, MCP, Training Room, Living Spec, plus the "
     "public splash and auth screens."),
    ("components", "Frontend — components",
     "Reusable presentational pieces: the live FIQ audit tape, the fully-editable "
     "character-sheet form, the sentinel verdict ribbon, the override modal, the "
     "navigation shell, and the Markdown+LaTeX renderer."),
    ("lib", "Frontend — libraries",
     "The axios REST clients for every API surface, the auth context / "
     "ProtectedRoute, and the client-side sentinel metadata helpers."),
    ("app", "Frontend — root",
     "The top-level router that wires the AuthProvider, public routes, and "
     "protected routes."),
    ("tests", "Tests",
     "Pytest and end-to-end regression suites covering the tool-use loop, the "
     "Training Room distillation, the three-core sentinel pipeline, and the live "
     "API."),
]
_SUBSYSTEM_ORDER = {key: i for i, (key, _t, _n) in enumerate(_SUBSYSTEMS)}
_SUBSYSTEM_META = {key: (title, narr) for key, title, narr in _SUBSYSTEMS}

# interdependent_lib subpackages that are their own subsystem.
_ILIB_SUBPKGS = {
    "zfae", "pcea", "ptca", "pcta", "pcna", "network", "fiq", "gonal",
    "aimmh", "_msdmd",
}


def _subsystem(path: str) -> str:
    """Map a module path to a subsystem key used to group the Architecture walk."""
    p = path.replace("\\", "/")
    if "frontend/src/pages/" in p:
        return "pages"
    if "frontend/src/components/" in p:
        return "components"
    if "frontend/src/lib/" in p:
        return "lib"
    if "frontend/src/App" in p:
        return "app"
    if "interdependent_lib/" in p:
        tail = p.split("interdependent_lib/", 1)[1]
        seg = tail.split("/", 1)[0]
        if seg.endswith(".py"):
            return "interdependent_lib"
        if seg == "_msdmd":
            return "msdmd"
        if seg in _ILIB_SUBPKGS:
            return seg
        return "interdependent_lib"
    for marker, key in (
        ("backend/providers/", "providers"),
        ("backend/auth/", "auth"),
        ("backend/agents/", "agents"),
        ("backend/tools/", "tools"),
        ("backend/skills/", "skills"),
        ("backend/a0p_skills/", "a0p_skills"),
        ("backend/tests/", "tests"),
    ):
        if marker in p:
            return key
    return "core"


def _render_modules(entries: list[dict], lines: list[str]) -> None:
    """Append each module as a readable bullet — bold name, full narrative, path."""
    for m in sorted(entries, key=lambda x: x.get("module_name") or ""):
        name = (m.get("module_name") or m.get("id") or "?")
        path = m.get("path") or ""
        summ = (m.get("summary") or "_(no narrative declared)_").replace("\n", " ").strip()
        lines.append(f"- **`{name}`** — {summ}  ")
        lines.append(f"  `{path}`")
    lines.append("")


def _format_kind_index(by_kind: dict[str, list[dict]], lines: list[str]) -> None:
    """Append a compact by-kind index table of module names."""
    lines.append("## Module index by kind")
    lines.append("")
    lines.append("| kind | count | modules |")
    lines.append("|---|---|---|")
    for kind in sorted(by_kind):
        entries = sorted(by_kind[kind], key=lambda m: m.get("module_name") or "")
        names = ", ".join(
            f"`{(m.get('module_name') or m.get('id') or '?')}`".replace("|", "\\|")
            for m in entries
        )
        lines.append(f"| {kind} | {len(entries)} | {names} |")
    lines.append("")


def write_readme(path: Path = Path("/app/README.md")) -> int:
    """Write a narrative README.md from the living spec. Returns module count."""
    try:
        from living_spec import scan_repo_blocks
        mods = scan_repo_blocks()
    except Exception:
        return 0

    by_kind: dict[str, list[dict]] = {}
    by_sub: dict[str, list[dict]] = {}
    for m in mods:
        by_kind.setdefault(m.get("module_kind") or "unknown", []).append(m)
        by_sub.setdefault(_subsystem(m.get("path") or ""), []).append(m)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines: list[str] = [
        "# a0p — research instrument",
        "",
        "> _changes constant. refinements welcome._  ",
        "> [wayseer@interdependentway.org](mailto:wayseer@interdependentway.org)",
        "",
        f"_Living spec — auto-regenerated on backend startup at {ts}._  ",
        f"_{len(mods)} modules · {len(by_kind)} kinds · {len(by_sub)} subsystems._",
        "",
        "> This file is generated from the codebase's own documentation. "
        "Don't edit it by hand — edit a module's `# === MODULE_BUILD ===` block "
        "(its `summary` is the narrative you read below) and it regenerates on the "
        "next backend start.",
        "",
        "## Overview",
        "",
        _OVERVIEW,
        "",
        "## Architecture",
        "",
        "The walkthrough below moves from the outer service inward to the "
        "inference substrate, then out to the frontend. Each subsystem opens with "
        "what it is and why it exists, followed by its modules and their "
        "narratives.",
        "",
    ]

    ordered = sorted(
        by_sub.keys(),
        key=lambda k: (_SUBSYSTEM_ORDER.get(k, len(_SUBSYSTEMS)), k),
    )
    for key in ordered:
        entries = by_sub[key]
        title, narrative = _SUBSYSTEM_META.get(key, (key, ""))
        lines.append(f"### {title} · {len(entries)}")
        lines.append("")
        if narrative:
            lines.append(narrative)
            lines.append("")
        _render_modules(entries, lines)

    _format_kind_index(by_kind, lines)

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(mods)


__all__ = ["write_readme"]
# ratios: loc_comments=242:62 imports_exports=4:2 calls_definitions=40:4
