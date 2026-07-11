# Repair 15 — Reject incompatible phase embeddings instead of silently truncating composition

**Codex handoff:** implementation-ready  
**Priority:** P2 — structural correctness  
**Primary target:** `The-Interdependency/a0-betatest`  
**Dependencies:** coordinate shape fields with Repairs 12–13

## Mission

Make `phase_compose` a strict structural operation. Embeddings with different carriers, lane counts, or inconsistent internal tuple lengths must fail visibly instead of composing only the shorter prefix and inheriting one operand's carrier.

## Audit baseline

- Integration repository: `The-Interdependency/a0ucns`
- Audit head: `0ac2953ff5a12798ac054bfa1d41bb268b99e9b3`
- Mirrored application pin at audit: `The-Interdependency/a0-betatest@4f089d40455e6bca3fac682eeed5ff26694057e5`
- The application mirror is not authoritative. Re-resolve the current upstream `main` before editing.

## Source evidence to confirm on current `main`

- `backend/interdependent_lib/ucns_embed.py::phase_compose` sets `n = min(a.lanes, b.lanes)`.
- it composes only that prefix and returns `carrier=a.carrier` without checking `b.carrier`.
- chirality and tuple lengths are not validated against declared lane counts.
- this behavior can hide incompatible shapes in chapter folding.

## Required invariants

- Composition requires equal carrier, equal declared lanes, and tuple lengths consistent with those lanes.
- Incompatibility raises a named, deterministic error before producing output.
- No silent truncation, padding, coercion, or carrier inheritance occurs.
- Valid composition remains ordered, deterministic, modulo one turn, and recompose-only.
- `build_disk_stack` surfaces an internal invariant failure safely rather than returning a partial chapter.

## Non-goals

- Do not add decomposition/inversion.
- Do not create an implicit projection between carrier spaces. A future projection must be a separately named operation with doctrine and tests.
- Do not change valid canonical hash behavior without an explicit reason.

## Proposed file plan

| Path | Change | Purpose | Risk | Required tests |
|---|---|---|---|---|
| `backend/interdependent_lib/ucns_embed.py` | modify | strict validation and named error | medium | shape matrix |
| `backend/interdependent_lib/gonal_stack.py` | modify if needed | safe handling/propagation in chapter fold | medium | stack failure test |
| API error mapping | inspect/modify | controlled 4xx/5xx without internals if user-reachable | low | API test |
| embedding/stack tests | modify/create | evidence | medium | CHECKS declarations |

## Implementation sequence

1. Add a named exception such as `EmbeddingShapeError(ValueError)`.
2. Add a validation helper checking:
   - `carrier` equality and positive value;
   - `lanes` equality and positive/nonnegative doctrine;
   - `len(angle_bits) == lanes` for both;
   - `len(chirality) == lanes` for both;
   - angle ranges and chirality values if constructors can receive external data.
3. Call validation before composition. Remove `min(...)`; iterate exactly `lanes`.
4. Preserve modulo-65536 angle addition and recomputed chirality for valid inputs.
5. Decide how canonical hashes encode operation/version. Current fixed-length hashes make concatenation unambiguous, but add an operation/domain separator if changing the hash contract, and test it.
6. Ensure chapter reduction cannot mix incompatible embeddings. Since all canonical `embed_text` results share shape, an incompatibility indicates corruption/programmer error and should fail clearly.
7. Update contracts/docstrings/export list if the exception is public.

## Source-owned contracts to add or revise

```text
phase_compose_requires_equal_embedding_shape
  given: embeddings with different carriers, lane counts, or tuple lengths
  then: phase_compose raises EmbeddingShapeError and returns no partial result
  class: correctness

phase_compose_valid_result_preserves_shape
  given: two valid equal-shape embeddings
  then: result has the same carrier and lane count, every angle is modulo one turn, and chirality length equals lanes
  class: correctness

chapter_fold_rejects_corrupt_embedding
  given: one incompatible embedding in a session fold
  then: disk-stack construction fails explicitly rather than truncating the chapter representation
  class: correctness
```

## Test-owned checks

- Carrier mismatch.
- Declared lane mismatch.
- Angle tuple shorter/longer than lanes.
- Chirality tuple shorter/longer or invalid values.
- Valid composition exact expected angle arithmetic.
- Associativity test for equal-shape angle addition, limited to the representation/hash semantics actually promised.
- Disk-stack failure injection.

## Validation commands

```bash
cd backend
pytest -q tests/test_ucns_embed.py tests/test_gonal_stack.py tests/test_training_room.py
pytest -q
python -m a0p_skills.test_build_runner --root .
```

## Acceptance criteria

- [ ] No `min(a.lanes, b.lanes)` or equivalent silent prefix composition remains.
- [ ] Shape/carrier validation is centralized and tested.
- [ ] Valid output preserves shape and deterministic arithmetic.
- [ ] Corrupt chapter folding fails explicitly.
- [ ] No projection/decomposition claim is introduced.

## Rollback

Disable cross-object composition if compatibility errors surface unexpectedly. Do not restore silent truncation. Investigate and repair the producer of incompatible embeddings.

## hmmm

- Whether zero-lane embeddings are valid; current canonical generation uses 53 lanes, so reject unless an existing contract proves otherwise.
- Whether to domain-separate composition hashes in this patch or preserve the current hash contract for compatibility.

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
