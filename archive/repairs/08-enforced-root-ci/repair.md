# Repair 08 — Add enforced root CI for the integration repo and full behavioral gates upstream

**Codex handoff:** implementation-ready  
**Priority:** P1 — required before declaring repairs test-backed  
**Primary target:** both `The-Interdependency/a0-betatest` and `The-Interdependency/a0ucns`  
**Dependencies:** tests from Repairs 01–07 should be included as they land

## Mission

Ensure GitHub actually runs the build, security, contract, and mirror-integrity checks for the repository receiving a change. Nested mirrored workflows do not protect `a0ucns`; import smoke alone does not establish behavioral correctness.

## Audit baseline

- Integration repository: `The-Interdependency/a0ucns`
- Audit head: `0ac2953ff5a12798ac054bfa1d41bb268b99e9b3`
- Mirrored application pin at audit: `The-Interdependency/a0-betatest@4f089d40455e6bca3fac682eeed5ff26694057e5`
- The application mirror is not authoritative. Re-resolve the current upstream `main` before editing.

## Source evidence to confirm on current `main`

- workflow files inspected under `a0-betatest/.github/workflows/` run for the upstream application repo, not as root workflows for `a0ucns`.
- the upstream build workflow installs dependencies, builds the frontend, and imports backend modules.
- the examined workflow does not run the documented pytest suite or the complete skill evidence graph.
- pull-request validation skipped the deploy job, so no container/deployment contract was exercised.
- the integration head had no attached workflow runs in the examined connector response.

## Required invariants

- Every PR to `a0-betatest` runs frontend build, backend unit/security/contract tests, metadata runners, and a container/import/startup smoke appropriate to the changed surface.
- Every PR to `a0ucns` runs a root workflow that validates mirrors, exclusions, pins, docs, and at least the mirrored application's clean build.
- CI uses lockfiles or otherwise detects dependency drift; it does not silently install an unreviewed dependency graph.
- A failed security contract blocks merge.
- Runners visibly report gaps and exit nonzero in strict mode.
- No CI secret is printed or exposed to pull-request code from untrusted forks.

## Non-goals

- Do not make deployment from `a0ucns`; it is an integration workspace unless doctrine changes.
- Do not mark flaky tests green by blanket retries or `continue-on-error`.
- Do not equate code coverage percentage with security evidence.

## Proposed file plan

| Repo/path | Change | Purpose | Risk | Required tests |
|---|---|---|---|---|
| `a0-betatest/.github/workflows/ci.yml` or existing workflows | modify | full application gates | high | action syntax + local command parity |
| `a0-betatest/frontend/package-lock.json` | create/update if absent | deterministic frontend install | medium | `npm ci` |
| `a0-betatest/backend/tests/` | extend | all repair evidence | critical | pytest |
| `a0-betatest/scripts/ci/` | create if useful | stable reusable commands | medium | shell tests |
| `a0ucns/.github/workflows/integration.yml` | create | root-recognized integration gates | high | mirror validation |
| `a0ucns/scripts/check_mirrors.py` | create or reuse Repair 11 | pins/exclusions/drift | high | fixture tests |
| branch protection settings | operator action | require named checks | critical | screenshot/API confirmation in PR notes |

## Implementation sequence

1. In upstream `a0-betatest`, consolidate CI into explicit jobs:
   - manifest/skill sync audit;
   - Python dependency install from an authoritative lock/requirements contract;
   - source CONTRACTS ↔ test CHECKS audit;
   - full pytest, including security and tenant-isolation suites;
   - frontend `npm ci` and production build;
   - backend import and real ASGI/container startup smoke;
   - optional static analysis only when configured and non-decorative.
2. Use a Mongo service container or a deliberately isolated test substitute for integration tests. Do not point CI at production services.
3. Seed throwaway secrets through job environment. Redact output and keep permissions read-only by default.
4. In `a0ucns`, add a root workflow. It should:
   - validate `CONNECTIONS.md` pins;
   - compare mirrored tracked files to pinned upstream archives;
   - enforce excluded paths/marker files and zero `.safetensors`/upload blobs;
   - run the mirrored app's same build/test command where practical;
   - verify docs status references resolve.
5. Add workflow concurrency/cancellation and explicit timeouts.
6. Keep deploy in a separate trusted push/environment job after all checks pass.
7. Configure branch protection to require exact check names. Record this operator action in the handoff report because it is not captured by repository code alone.
8. Negative-test the gates: introduce a failing owner-isolation check and a forbidden `.safetensors` fixture on a temporary branch/worktree; confirm CI scripts fail before removing them.

## Source-owned contracts to add or revise

```text
upstream_ci_executes_behavioral_security_suite
  given: a pull request to a0-betatest
  then: all declared security CHECKS and full pytest execute and any failure blocks the required CI check
  class: evidence

integration_ci_runs_from_repository_root
  given: a pull request to a0ucns
  then: a root workflow validates pins, mirror contents, exclusions, and the mirrored build
  class: evidence

ci_gap_runner_fails_closed
  given: an orphan CONTRACT, unknown CHECK target, missing required boundary, or mirror drift
  then: the corresponding job exits nonzero and reports the visible gap
  class: doctrine

ci_does_not_expose_secrets_to_untrusted_code
  given: a fork-origin pull request
  then: deploy credentials and protected environment secrets are unavailable
  class: security
```

## Test-owned checks

- Local execution of every script invoked by Actions.
- YAML/action validation where available.
- Fixture tests for mirror checker and evidence graph.
- Temporary negative tests proving failures are detected.
- Confirm PR workflow has read-only default permissions.
- Confirm deploy job triggers only on trusted branch/environment after required checks.

## Validation commands

```bash
# upstream
cd a0-betatest
npm ci --prefix frontend
npm run build --prefix frontend
python -m pip install -r backend/requirements.txt
cd backend && pytest -q
# run current skill audit/strict commands exactly as documented

# integration
cd a0ucns
python scripts/check_mirrors.py --strict
# run root integration command locally
```
After push, verify the named GitHub checks appear on the PR and branch protection requires them.

## Acceptance criteria

- [ ] Upstream PRs execute full tests, not import smoke alone.
- [ ] `a0ucns` has a root-recognized workflow.
- [ ] Mirror/exclusion/evidence gaps fail closed.
- [ ] Container or real ASGI startup is exercised.
- [ ] Dependency installation is deterministic enough to detect drift.
- [ ] Required checks are enforced by branch protection.

## Rollback

A broken CI refactor may be reverted to the last working enforced gate, but never to no required security tests. If a specific check is temporarily quarantined, make the gap visible and assign an owner/date; do not mark it successful.

## hmmm

- The current canonical CLI for the latest vendored msdmd/test-build runners; inspect rather than guessing flags.
- Whether frontend lockfile exists and is authoritative.
- Which tests require a live Mongo service and whether they are deterministic in Actions.
- Branch-protection changes require repository administrator action outside the patch.

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
