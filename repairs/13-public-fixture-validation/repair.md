# Repair 13 — Make public-fixture carrier status reflect successful runtime validation

**Codex handoff:** implementation-ready  
**Priority:** P2 — research-readout truthfulness  
**Primary target:** `The-Interdependency/a0-betatest`  
**Dependencies:** none

## Mission

Stop reporting `public_fixture_carrier: true` merely because fixture imports succeeded. The status must represent an actual successful build/validation for the produced stack.

## Audit baseline

- Integration repository: `The-Interdependency/a0ucns`
- Audit head: `0ac2953ff5a12798ac054bfa1d41bb268b99e9b3`
- Mirrored application pin at audit: `The-Interdependency/a0-betatest@4f089d40455e6bca3fac682eeed5ff26694057e5`
- The application mirror is not authoritative. Re-resolve the current upstream `main` before editing.

## Source evidence to confirm on current `main`

- `backend/interdependent_lib/gonal_stack.py` sets `_PUBLIC_DISK_OK = True` when imports succeed.
- `build_disk_stack` calls `build_public_fixture_disk()` inside `try/except` and silently ignores failures.
- returned `CylindricalDiskStack.public_fixture_carrier` uses the import-time flag, so it can remain true after validation failed.

## Required invariants

- `public_fixture_carrier` is true only after the fixture has been constructed and validated successfully for the current code path.
- A validation exception cannot be swallowed while returning success.
- Degraded mode is explicit and deterministic; it does not expose sensitive exception details to clients.
- Carrier arity remains separately reported and must not be conflated with fixture validation.

## Non-goals

- Do not load or expose the private canonical carrier.
- Do not convert public-fixture validation into proof of UCNS-G geometry or UCNS-A theorem status.

## Proposed file plan

| Path | Change | Purpose | Risk | Required tests |
|---|---|---|---|---|
| `backend/interdependent_lib/gonal_stack.py` | modify | runtime validation result and honest degraded status | medium | monkeypatch failure tests |
| fixture validator module if one exists | inspect/modify | return typed validation result | medium | validator tests |
| training API/frontend | inspect/modify | render degraded state | low | build/snapshot |
| backend test module | modify/create | evidence | medium | CHECKS declarations |

## Implementation sequence

1. Separate “module import available” from “fixture validated.” Use distinct internal values or a typed result.
2. Add a function such as `_validate_public_fixture() -> bool` or a richer result. It must actually call the fixture builder and any canonical public invariant checks.
3. Decide caching. A successful immutable fixture validation may be cached; a failed validation should remain false and produce a coarse internal diagnostic. Tests must be able to reset/inject behavior.
4. In `build_disk_stack`, set `public_fixture_carrier` from the actual validation result. If degraded operation is allowed, continue with the declared fallback carrier arity and return false.
5. If fixture validation is required for correctness, fail the request with a controlled error instead of degraded output. Choose based on existing doctrine and document it.
6. Update docstrings, metadata, API descriptions, and frontend status text.

## Source-owned contracts to add or revise

```text
public_fixture_status_requires_successful_validation
  given: fixture imports succeed but build or invariant validation raises
  then: returned stack does not claim public_fixture_carrier true
  class: correctness

public_fixture_failure_is_explicit_and_safe
  given: fixture validation fails
  then: the API either returns a declared degraded stack with false status or a controlled error, without private material or stack details
  class: safety
```

## Test-owned checks

- Normal fixture success returns true.
- Monkeypatch builder failure after successful import; status is false or controlled failure.
- Invariant validation returns false; status follows it.
- Repeated calls have documented cache behavior.
- API response contains no exception traceback/path/private disk content.

## Validation commands

```bash
cd backend
pytest -q tests/test_gonal_stack.py tests/test_training_room.py
pytest -q
python -m a0p_skills.test_build_runner --root .
```

## Acceptance criteria

- [ ] Import availability and validation success are distinct.
- [ ] No swallowed validation failure can yield `true`.
- [ ] Degraded/fail behavior is declared and tested.
- [ ] UI/API status is honest and safe.

## Rollback

If validation causes instability, return `public_fixture_carrier: false` and disable fixture-dependent claims. Never restore a success flag based only on import.

## hmmm

- Whether degraded output is scientifically useful or the endpoint should fail when fixture validation fails.
- Which exact public invariants constitute successful validation; use the existing carrier validator, not a new guessed criterion.

## Operating rules

1. **Edit upstream first.** Application changes belong in `The-Interdependency/a0-betatest`. Do not implement them first under `a0ucns/a0-betatest/`. After the upstream PR merges and passes its gates, re-mirror tracked files into `a0ucns` and advance the pin in `CONNECTIONS.md`.
2. **Read the current vendored skills before touching code:**
   - `.agents/skills/msdmd/SKILL.md`
   - `.agents/skills/meta-module-build/SKILL.md`
   - `.agents/skills/risk-boundary-build/SKILL.md`
   - `.agents/skills/test-build/SKILL.md`
   - `.agents/skills/canon/SKILL.md` when changing doctrine or integration status
3. **Metadata is part of the patch.** Update every affected `MODULE_BUILD`, `BOUNDARIES`, and `CAPABILITIES` block to describe the behavior after the repair. Do not leave a route claiming `auth_boundary: none` when authentication is required.
4. **Tests follow current skill-lib doctrine.** Source modules own `CONTRACTS`; test modules own executable `CHECKS`. Do not add a new `call:` field to source `CONTRACTS` if the current vendored skill has adopted the CONTRACTS/CHECKS split.
5. **Preserve uncertainty.** Use `hmmm` for an unresolved fact; do not convert an assumption into canon.
6. **No unrelated cleanup.** Keep the repair reviewable and independently revertible.
7. **Do not claim completion from import success alone.** Report the exact tests and runners executed.

## Required final report from Codex

Return:

- files changed and why;
- contracts and checks added;
- commands run with pass/fail results;
- migration or compatibility impact;
- remaining `hmmm` items;
- the exact upstream commit or PR, if one was created;
- whether the `a0ucns` mirror was intentionally left unchanged pending upstream merge.
