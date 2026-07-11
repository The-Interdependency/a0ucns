# Repair 14 — Make EDCM applicability, polarity, and alert semantics metric-specific

**Codex handoff:** implementation-ready  
**Priority:** P2 — research-readout correctness  
**Primary target:** `The-Interdependency/a0-betatest`  
**Dependencies:** frontend/API compatibility review required

## Mission

Prevent the training readout from treating every high value as the same kind of alert and from presenting pairwise divergence/balance metrics as measured when no prior turn exists.

## Audit baseline

- Integration repository: `The-Interdependency/a0ucns`
- Audit head: `0ac2953ff5a12798ac054bfa1d41bb268b99e9b3`
- Mirrored application pin at audit: `The-Interdependency/a0-betatest@4f089d40455e6bca3fac682eeed5ff26694057e5`
- The application mirror is not authoritative. Re-resolve the current upstream `main` before editing.

## Source evidence to confirm on current `main`

- `backend/interdependent_lib/edcm_readout.py::_band` maps all values `>=0.80` to `high` and `<=0.20` to `low` without metric polarity.
- TBF is described as turn-balance fairness, where high balance is ordinarily favorable rather than alarming.
- without `prev_text`, DRIFT is set to 0, TBF to 0.5, and DVG to the current text's type-token ratio, even though no pair exists for divergence/balance.
- CM also changes meaning on a first turn from mismatch to bone sparsity.

## Required invariants

- Every metric declares name, definition, input requirements, range, polarity, and concern thresholds.
- Pairwise metrics are marked not applicable when no prior turn exists; absence is not encoded as an invented neutral or unrelated statistic.
- Alert/status represents concern, not merely numeric magnitude, or the API clearly separates magnitude band from concern.
- The frontend renders `not_applicable` distinctly from zero/healthy.
- Metric definitions remain deterministic and bounded where applicable.
- The readout continues to disclaim full edcmbone metric authority and theorem transfer.

## Non-goals

- Do not claim empirical validation of the heuristic metrics.
- Do not redesign the full EDCM/edcmbone model in this patch.
- Do not preserve backward compatibility by silently lying with placeholder numbers.

## Proposed file plan

| Path | Change | Purpose | Risk | Required tests |
|---|---|---|---|---|
| `backend/interdependent_lib/edcm_readout.py` | major modify | metadata, applicability, polarity-aware concern | high | semantic matrix |
| `backend/api_training.py` | modify if schema changes | serialize N/A and metadata | medium | API tests |
| training frontend page/components | modify | render N/A, concern, definitions | medium | UI tests/build |
| contracts/test module | modify/create | evidence | high | CHECKS declarations |
| docs/living spec metadata | update | honest definitions | low | generated docs check |

## Implementation sequence

1. Introduce a canonical metric-definition mapping, for example fields:
   - `requires_prior`
   - `higher_is` (`concern`, `favorable`, or `descriptive`)
   - thresholds
   - concise definition
   - units/range.
2. Separate metric value from concern status. A robust result shape is:
   ```json
   {"value": 0.83, "applicable": true, "status": "concern", "band": "high"}
   ```
   A smaller compatibility shape may keep `metrics` and add `applicability`, `concern`, and `definitions`, but must not make `alerts["tbf"]="high"` mean danger when balance is favorable.
3. When `prev_text is None`, mark CM/DRIFT/DVG/TBF not applicable unless a metric is explicitly renamed/redefined as a single-turn measure. Do not reuse DVG for TTR under the same label.
4. Keep DA and INT as single-turn metrics. Preserve `raised_field_count` as a separate observation.
5. If single-turn lexical diversity or bone sparsity is useful, expose it under new descriptive names with separate doctrine; do not overload pairwise metric IDs.
6. Update API models and frontend to display em dash/N/A plus tooltip definition.
7. Version the response if external clients require it, or provide a transition field with a deprecation date.
8. Update contracts/tests and generated living spec.

## Source-owned contracts to add or revise

```text
edcm_pair_metrics_are_not_applicable_without_prior
  given: a readout with no prev_text
  then: CM, DRIFT, DVG, and TBF are explicitly not applicable and are not replaced by unrelated or invented values
  class: correctness

edcm_tbf_polarity_is_favorable_when_high
  given: two turns with equal lengths and two turns with extreme imbalance
  then: equal lengths produce high TBF with low concern, while imbalance produces low TBF with elevated concern
  class: correctness

edcm_status_is_metric_specific
  given: equal numeric values across metrics with different polarity
  then: concern/status follows each metric definition rather than one universal band function
  class: correctness
```

## Test-owned checks

- No-prior response: pair metrics N/A; DA/INT still measured.
- Equal-length turns: TBF near 1 and not a concern.
- One empty/one long turn: TBF near 0 and concern.
- High CM/DA/DRIFT/DVG/INT follow declared concern polarity.
- Determinism and `[0,1]` range for applicable values.
- API serialization and frontend snapshot distinguish `null/N/A` from zero.
- Existing consumers either pass compatibility tests or receive a documented version change.

## Validation commands

```bash
cd backend
pytest -q tests/test_edcm_readout.py tests/test_training_room.py
pytest -q
python -m a0p_skills.test_build_runner --root .
cd ../frontend && npm run build
```

## Acceptance criteria

- [ ] Metric definitions and polarity are explicit data, not prose only.
- [ ] No-prior pair metrics are N/A.
- [ ] TBF concern direction is correct.
- [ ] Frontend/API distinguish absence from zero.
- [ ] Any response compatibility change is versioned/documented.
- [ ] No empirical/theorem status is overstated.

## Rollback

Hide or disable the EDCM panel rather than restore semantically misleading values. A legacy response may be temporarily available under an explicitly deprecated version, never as the default truth surface.

## hmmm

- Whether CM should remain pairwise mismatch only or a new single-turn structural-sparsity metric should be added.
- Exact concern thresholds; retain 0.80/0.20 only if they are declared heuristic constants, not empirically validated cutoffs.
- The best compatibility strategy for existing frontend/client code (`null`, nested metric objects, or API version).

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
