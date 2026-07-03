---
name: ratios
description: Self-declaring module composition ratios built on msdmd. Each module records its own ratios (lines of code to lines commented, imports to exports, and calls to definitions) in a `# === RATIOS ===` block that bookends the file — first line and last line — and a runner recomputes each recorded ratio from the source and fails on drift, while reporting visible coverage gaps. Load this when recording a module's composition ratios, when authoring or extending the ratio registry, or when wiring ratio verification into CI.
---

# ratios — Module composition ratios on msdmd

`ratios` is an application of [msdmd](../msdmd/SKILL.md). The foundational
skill defines the comment-block convention, the universal parser, and the
gap-reporting requirement; this skill applies the convention to a module's
own composition ratios and defines the executor contract.

A ratio is a fact a module owns about its own shape. Like a contract, it
belongs in the file it describes, not in a side report that can drift out
of sync. Unlike a contract, it is not asserted by a human — it is
*recomputed from the source*, so a recorded ratio that no longer matches
the file is a build failure, not a stale comment nobody noticed.

## The block, and the bookend rule

Every module records its ratios in a `RATIOS` block placed at **both
boundaries of the file** — the block is the literal first line and the
literal last line.

```python
# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 141:40
#   basis: N = non-blank non-comment code lines; M = strict hash-comment + docstring lines; RATIOS block lines excluded
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 8:5
#   basis: imports = lines matching ^(import |from \S+ import); exports = top-level def/class with no leading underscore + 1 if __all__ present; RATIOS block lines excluded
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 34:12
#   basis: definitions = top-level def + class lines; calls = non-definition lines containing a call expression \w+\(; RATIOS block lines excluded
# === END RATIOS ===
```

## Field schema

Required:

| Field | Meaning |
|---|---|
| `id` | Ratio identifier, stable across refactors. Must match a computer in the registry to be *verified*. |
| `value` | The recorded ratio as `A:B`, or `hmmm` if the ratio is declared-but-not-yet-resolved. |

Optional:

| Field | Meaning |
|---|---|
| `summary` | One-sentence human description. |
| `basis` | The counting rule used, in-band, so the recorded value is reproducible. |
| `class` | Free-text tag (`composition`, `coverage`, `complexity`). |
| `since` | Version or date the ratio was added. |
| `deprecated` | If present, the runner skips and reports the entry as deprecated. |

## The three ratios

### 1. `loc_comments` — lines of code to lines commented

- **N (lines of code)**: physical lines carrying a code token — not blank, not a pure comment, not a docstring-only line.
- **M (lines commented)**: strict `#`-comment lines plus docstring lines (`"""` / `'''` blocks).
- **self-exclusion**: lines inside any `=== RATIOS ===` ... `=== END RATIOS ===` fence are excluded from both counts.

### 2. `imports_exports` — import statements to public exports

- **import_count**: lines whose stripped content matches `^(import |from \S+ import)`.
- **export_count**: count of top-level `def` and `class` declarations with no leading underscore + 1 if `__all__` appears anywhere.
- **self-exclusion**: RATIOS block lines excluded from both counts.

### 3. `calls_definitions` — call sites to definitions

- **definition_count**: top-level `def` and `class` lines. Nested `def` inside a class counts. Closures (def inside def) do not.
- **call_count**: non-definition, non-comment, non-blank lines containing at least one `\w+\(`. Each physical line counts once.
- **self-exclusion**: RATIOS block lines excluded from both counts.

## The runner

```bash
python ratios_check.py path/to/module.py
python ratios_check.py --root .
python ratios_check.py --root . --strict
```

Exit codes: `0` all recorded ratios match (gaps allowed unless `--strict`);
`1` a ratio drifted from source, or — under `--strict` — a coverage gap.

## Anti-patterns

- Recording a ratio by hand instead of recomputing it. The point is that the file measures itself; a hand-typed value is a contract that drifts.
- Placing the block anywhere but the file boundaries. The bookend is the convention.
- Counting the RATIOS block in its own ratio. Always self-exclude.
- Inventing ratio ids whose computer does not exist and recording a number for them. Record `hmmm` until a computer is registered.

## Completion criteria

A run is complete when it produces either a SKILL-only declaration (the
convention, before any executor) or an executor plus a registry with all
three computers (`loc_comments`, `imports_exports`, `calls_definitions`)
registered and a passing self-verification on the files it covers.

## hmmm

- whether the bookend blocks must be byte-identical or may differ in whitespace
- whether ratios verification joins CI beside the MODULE_BUILD check
- calls_definitions: whether lambda assignments count as definitions
- imports_exports: whether re-exported names from `__init__.py` aggregate files count once or per-name
