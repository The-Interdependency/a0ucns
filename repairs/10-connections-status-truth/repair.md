# Repair 10 — Reconcile CONNECTIONS.md with implemented coupling surfaces and evidence status

**Codex handoff:** implementation-ready  
**Priority:** P1 — architecture truth and safe handoff  
**Primary target:** `The-Interdependency/a0ucns`  
**Dependencies:** update after relevant upstream connector/orchestration repairs; can begin independently

## Mission

Turn `CONNECTIONS.md` from a mixture of proposal and implementation history into a source-backed integration manifest. Every coupling must state whether it is proposed, implemented, tested, deployed, or retired and point to the actual current path.

## Audit baseline

- Integration repository: `The-Interdependency/a0ucns`
- Audit head: `0ac2953ff5a12798ac054bfa1d41bb268b99e9b3`
- Mirrored application pin at audit: `The-Interdependency/a0-betatest@4f089d40455e6bca3fac682eeed5ff26694057e5`
- The application mirror is not authoritative. Re-resolve the current upstream `main` before editing.

## Source evidence to confirm on current `main`

- the document describes Coupling A as the external/vendored `aimmh_lib` with six patterns including roleplay and a new adapter to write.
- current `a0-betatest` imports `backend/interdependent_lib/aimmh`, whose exposed implementation in the audited pin contains five patterns and no roleplay export.
- the document describes Odysseus MCP coupling as nearly zero-code.
- current application code includes a custom `tools/odysseus_relay.py` for scoped `/api/codex/*` REST and states that Odysseus does not speak HTTP-MCP for that surface.
- proposed OpenAI-compatible reverse coupling remains unimplemented in the examined source.

## Required invariants

- `declared` and `implemented` claims are distinguished from desired/inferred claims.
- Every implemented coupling lists exact source paths, pin, tests/checks, auth/secret/network boundary, and known limitations.
- Proposed designs remain visibly proposed; no checkmark implies implementation without evidence.
- No theorem/proof/empirical status is transferred by interoperability.
- Mirror source-of-truth and exclusions remain explicit.
- The document does not contain credentials, private carrier data, or deployment secrets.

## Non-goals

- Do not implement missing couplings merely to make the document true; either repair code upstream in a separate handoff or mark the coupling proposed.
- Do not delete valuable design history. Move superseded detail under a clearly labeled historical/proposed section.
- Do not canonize behavior based only on a README example.

## Proposed file plan

| Path | Change | Purpose | Risk | Required tests |
|---|---|---|---|---|
| `CONNECTIONS.md` | major modify | evidence-status manifest and corrected topology | medium | path/status audit |
| `README.md` | modify | concise current integration entry point | low | link check |
| `scripts/check_connections.py` | create | verify pins, paths, status fields, and test references | medium | fixture tests |
| `.github/workflows/integration.yml` | modify via Repair 08 | run connection audit | medium | CI |
| optional `connections.schema.json` or YAML sidecar | create if justified | machine-readable status source | medium | schema validation |

## Implementation sequence

1. Read current upstream heads and the actual mirrored pins. For each coupling A–E, classify:
   - `proposed`
   - `implemented`
   - `test-backed`
   - `deployed`
   - `retired/superseded`
   Multiple statuses may be represented as an evidence ladder, but do not skip rungs.
2. Add a compact status table with fields: direction, current mechanism, source path(s), test/check IDs, boundary summary, pin, and unresolved `hmmm`.
3. Correct Coupling A to reflect the actual embedded orchestration implementation unless/until the external `aimmh_lib` adapter is implemented. State the exact supported pattern set from exports/tests.
4. Correct Odysseus coupling to distinguish generic MCP servers from the implemented `/api/codex/*` REST relay. Document SSRF, token-storage, and sentinel boundaries according to code after Repairs 05–06.
5. Mark the OpenAI-compatible shim proposed until exact routes and checks exist.
6. Preserve the `edit upstream first, re-mirror second` rule and non-committable exclusions.
7. Add a checker that validates referenced paths exist under the pinned mirror, referenced contract/check IDs resolve, required status fields are present, and implemented entries do not point to `hmmm` code paths.
8. Keep qualitative claims such as “zero new code” out unless demonstrated at the current pin.

## Source-owned contracts to add or revise

```text
connections_implemented_status_has_source_evidence
  given: a coupling marked implemented or test-backed
  then: every referenced source path exists at the recorded pin and every test-backed claim names a resolving check
  class: evidence

connections_proposals_are_not_presented_as_runtime
  given: a coupling whose route/module is absent
  then: the document labels it proposed and does not present setup instructions as currently executable
  class: doctrine

connections_boundaries_match_implementation
  given: a coupling with auth, network, storage, or secret effects
  then: the manifest boundary summary agrees with the source BOUNDARIES block or leaves a visible hmmm
  class: doctrine
```

## Test-owned checks

- Parse status rows and verify required fields.
- Resolve every backticked source path against the mirror.
- Resolve named CONTRACTS/CHECKS IDs using the current msdmd parser.
- Fixture-test a false implemented path and an unresolved test ID; checker must fail.
- Manually compare exported AIMMH patterns and Odysseus dispatch kind with the document.

## Validation commands

```bash
cd a0ucns
python scripts/check_connections.py --strict
python scripts/check_mirrors.py --strict  # once Repair 11 exists
```
Review rendered Markdown for topology clarity and stale checkmarks.

## Acceptance criteria

- [ ] Every coupling has an evidence status and exact current mechanism.
- [ ] AIMMH and Odysseus descriptions match implemented code.
- [ ] Missing reverse OpenAI shim remains visibly proposed.
- [ ] Referenced paths/checks are machine-validated.
- [ ] Boundary and non-transfer rules remain intact.
- [ ] No secrets/private material enter documentation.

## Rollback

Revert to the last source-backed status manifest, not to the ambiguous proposal/implementation blend. A checker failure may temporarily mark a coupling `hmmm` rather than suppressing the gap.

## hmmm

- Whether the embedded AIMMH copy is intentionally canonical or temporary pending `aimmh-lib` integration.
- Which couplings are actually deployed versus merely implemented in source; deployment requires external evidence.
- Whether the machine-readable source should be Markdown, YAML, or generated from MODULE_BUILD/CAPABILITIES blocks.

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
