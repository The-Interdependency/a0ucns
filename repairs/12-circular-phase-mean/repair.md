# Repair 12 — Use a circular mean for unit-circle phase readouts

**Codex handoff:** implementation-ready  
**Priority:** P2 — research-readout correctness  
**Primary target:** `The-Interdependency/a0-betatest`  
**Dependencies:** none; coordinate API snapshots with Repair 14

## Mission

Correct the gonal stack's mean-phase calculation so wrap-around phases are treated as neighbors on the unit circle rather than distant scalar values.

## Audit baseline

- Integration repository: `The-Interdependency/a0ucns`
- Audit head: `0ac2953ff5a12798ac054bfa1d41bb268b99e9b3`
- Mirrored application pin at audit: `The-Interdependency/a0-betatest@4f089d40455e6bca3fac682eeed5ff26694057e5`
- The application mirror is not authoritative. Re-resolve the current upstream `main` before editing.

## Source evidence to confirm on current `main`

- `backend/interdependent_lib/gonal_stack.py::_mean_phase` currently computes the arithmetic mean of quantized angles divided by 65536.
- angles near `0.99` and `0.01` therefore produce approximately `0.50`, even though their circular mean lies near zero/one.
- `_grain_gonal` uses this value as the displayed `phi` phase for each disk.

## Required invariants

- Mean phase is computed from the vector average of unit-circle points using sine/cosine and `atan2`.
- Result is normalized to `[0, 1)` turns.
- Empty input returns a documented deterministic value and does not divide by zero.
- Antipodal/near-zero resultant behavior is explicit; it is not falsely presented as a well-defined direction.
- No UCNS-A theorem/proof status is inferred from this numerical correction.

## Non-goals

- Do not change embedding generation, phase composition, or carrier arity in this repair.
- Do not rename `phi` or alter unrelated geometry doctrine without a separate decision.

## Proposed file plan

| Path | Change | Purpose | Risk | Required tests |
|---|---|---|---|---|
| `backend/interdependent_lib/gonal_stack.py` | modify | circular mean and explicit resultant handling | medium | wrap/antipodal tests |
| `backend/tests/test_gonal_stack.py` or current contract test module | modify/create | numerical evidence | medium | CHECKS declarations |
| frontend readout labels | inspect | ensure phase units/undefined state render honestly | low | build/snapshot |

## Implementation sequence

1. Replace scalar averaging with:
   - convert each `angle_bits` value to radians;
   - average cosine and sine components;
   - compute `atan2(mean_sin, mean_cos)`;
   - normalize negative angles by adding `2π`;
   - divide by `2π` for turns.
2. Compute resultant magnitude. If it is below a small documented epsilon, do not imply a reliable direction. Preferred: expose `phi_defined` and/or `phi_resultant`; compatibility fallback may return `0.0` while explicitly marking undefined.
3. Preserve deterministic rounding only at serialization, not during internal calculation.
4. Update docstrings and metadata summary to say circular mean.
5. Add canonical wrap-around, identical, quadrant, empty, and antipodal cases.

## Source-owned contracts to add or revise

```text
gonal_mean_phase_respects_wraparound
  given: phase lanes centered near 0.99 and 0.01 turns
  then: the reported circular mean is near 0/1 and not near 0.5
  class: correctness

gonal_mean_phase_reports_undefined_resultant
  given: exactly or nearly antipodal phases with negligible resultant magnitude
  then: the readout marks direction undefined according to the declared schema rather than claiming a meaningful phase
  class: correctness
```

## Test-owned checks

- `[0.99, 0.01]` mean near `0.0` modulo one.
- identical phases return that phase.
- `[0.25, 0.25]` returns 0.25.
- empty lanes follow documented behavior.
- `[0.0, 0.5]` triggers undefined/near-zero resultant handling.
- property test: rotating every lane by `δ` rotates mean by `δ` modulo one when resultant is defined.

## Validation commands

```bash
cd backend
pytest -q tests/test_gonal_stack.py
pytest -q
python -m a0p_skills.test_build_runner --root .
```

## Acceptance criteria

- [ ] Arithmetic angle averaging is gone.
- [ ] Wrap-around and antipodal behavior is tested.
- [ ] Serialization remains bounded and deterministic.
- [ ] UI/API communicates undefined direction if the schema supports it.
- [ ] Metadata/docs make no inflated theorem claim.

## Rollback

Disable the affected phase readout rather than restoring mathematically incorrect scalar averaging. Preserve the prior field only as a clearly deprecated legacy value if compatibility requires a transition.

## hmmm

- The preferred API representation for undefined circular direction (`null`, `phi_defined`, or a separate resultant field).
- The epsilon threshold appropriate for quantized 16-bit phases; choose from numerical analysis and tests, not intuition alone.

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
