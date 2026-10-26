---
name: a0p-skills
description: This project's adoption of skill-lib — three msdmd executors (msdmd / test-build / meta-module-build) wired to the FastAPI surface so coverage stays visible during normal product use.
---

# a0p_skills — the three msdmd skill executors

This package is the project-local implementation of the
`The-Interdependency/skill-lib` skills. It does not redefine the
conventions — read those upstream first:

- `skill-lib/msdmd/SKILL.md` — foundational block syntax + parser contract.
- `skill-lib/test-build/SKILL.md` — `CONTRACTS` block + executor that imports `call:` paths.
- `skill-lib/meta-module-build/SKILL.md` — `MODULE_BUILD` block + boundary-field schema.

## Modules

| Module | What it does |
|---|---|
| `interdependent_lib._msdmd.parser` | Canonical parser. Synced line-for-line from `skill-lib/msdmd/parsers/universal.py`. |
| `a0p_skills.test_build_runner` | Reads `CONTRACTS` blocks, imports each `call:`, runs the function. Reports PASS / FAIL / ERROR / SKIP and the untested-modules list. |
| `a0p_skills.module_build_runner` | Reads `MODULE_BUILD` blocks, validates the required schema (including the five boundary fields and `rollout`/`rollback`), groups by `module_kind` and boundary risk, lists modules without a manifest. |
| `a0p_skills.contracts` | Importable test functions referenced from CONTRACTS `call:` paths. |

## CLI

```bash
# CAPABILITIES (deprecated, kept for migration view)
python -m interdependent_lib._msdmd.runner --root /app/backend

# test-build: imports each CONTRACTS `call:` and runs it
python -m a0p_skills.test_build_runner /app/backend

# meta-module-build: validates MODULE_BUILD schema + boundary discipline
python -m a0p_skills.module_build_runner /app/backend
```

Each command exits non-zero on failure / gaps. CI can wire them as-is.

## HTTP

The `/api/skill/<name>/report` routes mirror the CLI output:

| Route | Skill |
|---|---|
| `GET /api/skill/capabilities/report` | CAPABILITIES (deprecated migration view) |
| `GET /api/skill/contracts/report`    | test-build runner |
| `GET /api/skill/module-build/report` | meta-module-build runner |

The Inspector page surfaces a tile per skill so coverage erosion is
visible in normal product use, not buried behind a CLI flag.

## `hmmm` discipline

Per the meta-module-build doctrine: "If a field is not known, write
`hmmm`. Do not guess certainty into the manifest." Every manifest in
this repo follows that rule. Project-level open questions live in
`/app/memory/PRD.md` under the `## hmmm` section.

## Versioning

- The block syntax is upstream-versioned and stable.
- Field-schema additions track the upstream `SKILL.md` files.
- This project's executors are minor-version-bumped independently when
  they change behaviour.
