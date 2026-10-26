---
name: msdmd
description: Module Self-Declared Metadata in Markdown — every source module declares its capabilities, contracts, requirements, and owners in a fenced comment block inside the same file as the code. This package implements: (1) a stdlib-only parser, (2) a tree-walker / coverage runner, (3) a FastAPI surface so the Inspector page can show live coverage. This SKILL.md is the canonical reference for THIS project's adoption of the convention.
---

# msdmd (this project's application)

This file is the application of the upstream
[`The-Interdependency/skill-lib/msdmd`](https://github.com/The-Interdependency/skill-lib/tree/main/msdmd)
doctrine to **this repo**. The doctrine: every cross-cutting fact a
module owns lives **in the same file as the code that implements it**,
in a structured comment block. A walker enforces coverage. Modules
without the block show up as gaps. Coverage is observable, not implicit.

## Block convention used here

Comment marker for `.py` files is `#`. Fence opens with
`# === <BLOCK_NAME> ===` and closes with `# === END <BLOCK_NAME> ===`.
Field lines sit two visible spaces in from the `id` line.

```python
# === CAPABILITIES ===
# id: <stable_unique_id>
#   summary: one-sentence description
#   exposes: comma, separated, public, symbols
#   stability: experimental | stable | deprecated
# === END CAPABILITIES ===
```

Block names used in this repo:

| Block | Required where | Field schema |
|---|---|---|
| `CAPABILITIES` | **every** `.py` file under `/app/backend` | `id`, `summary`, optional `exposes`, optional `stability`, optional `since` |
| `CONTRACTS` | optional — public-facing routes and patterns | `id`, `given`, `then`, `class`, optional `call` |
| `REQUIRES` | optional — explicit dependency edges | `id`, `module`, optional `version` |
| `OWNERS` | optional — humans/agents responsible | `id`, `who`, optional `since` |

Reserved field names per the upstream doctrine: `id`, `class`, `call`,
`summary`, `requires`, `owner`, `since`, `deprecated`.

## Coverage rule (this project)

**CAPABILITIES is mandatory on every `.py` file under `/app/backend`.**
The runner emits two artifacts:

1. A per-file entry table (every CAPABILITIES entry found).
2. A gap list (every `.py` file under the watched root that has NO
   CAPABILITIES block).

Exit code of `python -m interdependent_lib._msdmd.report` is non-zero
when the gap list is non-empty.

## Parser contract

`parse(text: str, block_name: str) -> list[dict]`

- Pure function, stdlib only.
- Returns flat dicts, one per entry, each containing at minimum `id`.
- Concatenates entries from multiple blocks of the same name in the
  same file.
- Returns `[]` when the block does not exist (never raises on missing
  block).

## Runner contract

`walk(root: Path, block_name: str) -> Iterator[(Path, list[dict])]`

`report(root: Path, block_name: str) -> dict` returns:

```json
{
  "block_name": "CAPABILITIES",
  "root": "/app/backend",
  "scanned": 33,
  "covered": 33,
  "gaps_count": 0,
  "gaps": [],
  "by_file": { "<rel path>": [<entries>] }
}
```

## API surface

`GET /api/skill/report?block=CAPABILITIES&root=backend` returns the
same payload as the runner. The Inspector page surfaces the gap
count and the gap list so coverage erosion is visible in normal use,
not buried behind a CLI flag.

## How to add a new module

1. Write the code.
2. Add a CAPABILITIES block at the **top** of the file (before any
   imports). Give it a unique stable id (kebab-case-of-module-path or
   snake_case is fine; ids are global).
3. If the module exposes testable contracts, add a CONTRACTS block
   right above the function each contract describes.
4. Run `python -m interdependent_lib._msdmd.report` to confirm
   coverage is still 100 %.

## Anti-patterns (from upstream, applied here)

- Don't define the contract in a separate yaml/json file. Block lives
  with the code.
- Don't make ids reflect implementation details. `prime_circle_53` is
  fine; `init_array` is not.
- Don't introduce parser dialects. If you need richer syntax, extend
  the upstream parser, do not fork it.
- Don't silently drop gaps. The runner's exit code and the API's
  `gaps` array MUST stay visible.
