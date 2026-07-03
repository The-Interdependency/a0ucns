# msdmd compliance — odysseus-a0

> **msdmd** = *Module Self-Declared Metadata in Markdown*. Every cross-cutting
> fact a module owns — its purpose, public surface, risk boundaries,
> composition ratios — lives in a fenced comment block **inside the same file
> as the code**. A runner walks the tree, parses every block, and reports
> coverage + drift. Delete the code, delete the block in the same diff: the
> contract can't rot out of sync.

This fork carries a vendored msdmd toolchain and a **single action** that makes
the whole Python tree self-declaring in one command.

## The single action

```bash
python -m a0p_skills.msdmd_refactor .            # whole tree
python -m a0p_skills.msdmd_refactor core --dry-run   # preview one dir
python -m a0p_skills.msdmd_refactor . --report test_reports/msdmd.json
```

One run inserts, into every in-scope Python module:

| Block | What the action fills in |
|---|---|
| `RATIOS` (head + tail bookend) | `loc_comments`, `imports_exports`, `calls_definitions` — computed mechanically, **green by construction** (the writer uses the same `COMPUTERS` the checker validates with). |
| `MODULE_BUILD` | `module_name`, `public_surface`, `internal_surface` (from the AST), `summary` (module docstring), a path-inferred `module_kind`; everything a machine can't honestly know → `hmmm`. |
| `BOUNDARIES` | schema-complete skeleton; all risk fields → `hmmm`. |
| `CAPABILITIES` | `summary` + `exposes` (public surface). |

`hmmm` is doctrine, not laziness — per the `canon` skill it is an **explicit
boundary object** ("not yet known"), never a guessed value. The follow-up
*broad shallow passes* replace each `hmmm` with a source-backed fact.

### Guarantees

- **Idempotent.** `MODULE_BUILD` / `BOUNDARIES` / `CAPABILITIES` are inserted
  only when absent — a human/agent edit is never clobbered. `RATIOS` is
  re-normalized each run (purely mechanical).
- **Non-destructive.** Only comment blocks are added; code is untouched. Every
  Python file still compiles after a run.
- **Verifiable.** The four read-only checkers score the result:

```bash
python -m a0p_skills.ratios_runner .
python -m a0p_skills.module_build_runner .
python -m a0p_skills.boundaries_runner .
python -m a0p_skills.capabilities_runner .
```

## Current state

First full run (Python phase):

```
ratios            · 386 files · 229 covered / 157 gaps · 1374 verified · 0 drift
meta-module-build · 386 files · 229 covered / 157 gaps · 229 valid / 0 invalid
risk-boundary-build · 386 files · 229 covered / 157 gaps · 229 valid / 0 invalid · 1105 hmmm fields
cap-build         · 386 files · 229 covered / 157 gaps · 229 valid / 0 invalid
```

- **Python coverage: 229 / 229 = 100%**, 0 drift, 0 invalid manifests.
- The **157 gaps are non-Python** (149 `.js` + 8 `.sh`) — deferred (see below).
- **1105 `hmmm` boundary fields** are the honest backlog for the deeper passes.

## Roadmap

1. **Broad shallow passes (in progress).** Walk the `hmmm` fields module by
   module and replace them with source-backed values — `owner`,
   `auth/storage/network/user_data` boundaries, `admin_only`, `tests`,
   `rollout`, `rollback`. This is the comprehension pass: declaring a module's
   real boundaries forces you to read it.
2. **JS / shell phase.** The writer is Python-only today (the RATIOS computers
   and surface extraction assume Python; the ratios fence-strip assumes the `#`
   marker). Covering the 149 `.js` + 8 `.sh` files needs JS-aware ratio
   computers, a `//`-marker-aware strip, and a JS surface extractor.
3. **DOCS / CONTRACTS blocks.** Added once real docs/tests exist to point at.
4. **Self-verifying CI.** Wire the checkers into CI so coverage can only go up.

## Toolchain layout

```
interdependent_lib/_msdmd/parser.py   # vendored msdmd parser (pure stdlib)
a0p_skills/ratios_runner.py           # RATIOS checker + the COMPUTERS
a0p_skills/module_build_runner.py     # MODULE_BUILD checker
a0p_skills/boundaries_runner.py       # BOUNDARIES checker
a0p_skills/capabilities_runner.py     # CAPABILITIES checker
a0p_skills/msdmd_refactor.py          # the single-action writer
```

The parser and checkers are vendored from `The-Interdependency/a0-betatest`
(themselves synced from `skill-lib`). The `msdmd_refactor` writer is new here.
