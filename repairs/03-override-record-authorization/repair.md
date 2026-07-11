# Repair 03 — Owner-scope pending override reads and restrict global expiration

**Codex handoff:** implementation-ready  
**Priority:** P0 — release blocker  
**Primary target:** `The-Interdependency/a0-betatest`  
**Dependencies:** Repair 02 authentication pattern should be reused

## Mission

Prevent unauthenticated or other-user access to pending override records, which contain raw requests and sentinel metadata. Ensure approval, rejection, retrieval, retry binding, and expiration all preserve owner and action scope.

## Audit baseline

- Integration repository: `The-Interdependency/a0ucns`
- Audit head: `0ac2953ff5a12798ac054bfa1d41bb268b99e9b3`
- Mirrored application pin at audit: `The-Interdependency/a0-betatest@4f089d40455e6bca3fac682eeed5ff26694057e5`
- The application mirror is not authoritative. Re-resolve the current upstream `main` before editing.

## Source evidence to confirm on current `main`

- `backend/server.py::get_override` calls `zfae_overrides.get(col, override_id)` without authentication or owner filtering.
- `backend/server.py::expire_overrides` globally mutates pending records without authentication.
- `PendingOverride` includes `raw_request`, owner, agent, flagged sentinels, reasons, verdict vector, and decision metadata.
- `approve` and `reject` already filter by `user_id`, but generic `get` does not.
- `backend/tools/gated_invoke.py` and ZFAE runtime use override retrieval during retry/resume; these call sites must remain action-bound as helper signatures tighten.

## Required invariants

- An override record is readable only by its authenticated owner or an explicitly authorized administrator.
- Cross-owner lookup returns 404, not a redacted record and not 403.
- Approvals are single-use or at minimum bound to owner, event kind, agent, and the exact normalized action payload.
- A chat-level approval cannot authorize a different tool call; a tool approval cannot authorize a different tool or parameter set.
- Expiration cannot be triggered by an anonymous caller.
- Raw requests never appear in logs or list responses beyond the owner-authorized surface.

## Non-goals

- Do not weaken sentinel behavior or convert halted actions into automatic rejection.
- Do not expose records to support debugging through a public route.
- Do not compare action payloads through unstable string formatting; use one canonical serialization or digest.

## Proposed file plan

| Path | Change | Purpose | Risk | Required tests |
|---|---|---|---|---|
| `backend/server.py` | modify | authenticate/scoped get; remove or admin-gate expiration route | critical | anonymous and cross-owner tests |
| `backend/interdependent_lib/zfae/overrides.py` | modify | require owner scope for public retrieval; add user-scoped expiration if useful | critical | helper unit tests |
| `backend/interdependent_lib/zfae/runtime.py` | modify | pass owner/action context to override lookup | high | chat retry binding |
| `backend/tools/gated_invoke.py` | modify | pass owner and exact action digest; preserve no-replay behavior | high | tool retry binding |
| `backend/db.py` | modify | add indexes/TTL strategy if selected | medium | index/migration tests |
| `backend/tests/test_override_authorization.py` | create | evidence across lifecycle | critical | CHECKS declarations |

## Implementation sequence

1. Make the route-level retrieval API owner-required. A safe helper shape is `get(col, override_id, *, user_id)`; if truly internal unscoped retrieval is needed, give it a private name and keep it out of route code.
2. Update every call site. Runtime callers already know `user_id`; tool gating must use the authenticated user ID, not infer ownership from a tool name.
3. Add a canonical action fingerprint at override creation, such as BLAKE2b over canonical JSON containing event kind, agent ID, tool, and params. Store the digest; do not use it as a secret.
4. On resume, require owner, approved status, event kind, agent ID, and action fingerprint to match. Decide and document whether approval is consumable once. Prefer transitioning `approved` to `consumed` atomically when the action begins to prevent replay.
5. Change `GET /api/overrides/{id}` to require `get_current_user` and owner-scoped retrieval.
6. Replace public global expiration with one of:
   - internal startup/worker maintenance;
   - owner-scoped lazy expiration during list/get; or
   - explicit administrator-only operation.
   Do not leave it anonymous.
7. Ensure list endpoints cap limits and do not include raw request bodies unless the owner explicitly opens a single record. Consider a summary projection for lists.
8. Add indexes supporting `user_id + status + created_ms/expires_ms`. A Mongo TTL index is acceptable only if deletion, rather than retained `expired` audit status, matches doctrine.
9. Update metadata and contracts.

## Source-owned contracts to add or revise

```text
override_get_requires_owner
  given: anonymous user or user B requests an override owned by A
  then: anonymous receives 401 and B receives 404; raw_request is not disclosed
  class: security

override_resume_exact_action_binding
  given: an approved override for one event/action and a retry with any changed owner, event kind, agent, tool, or params
  then: the approval is rejected and the changed action remains halted
  class: safety

override_approval_not_replayable
  given: one approval has successfully resumed its exact action
  then: a second attempt cannot reuse it unless doctrine explicitly permits and tests bounded idempotency
  class: security

override_expiration_not_publicly_mutable
  given: an anonymous request to the expiration surface
  then: no record changes and the request is rejected or the route does not exist
  class: auth
```

## Test-owned checks

- Full lifecycle for owner A: create, list summary, get detail, approve/reject, resume, expire/consume.
- User B attempts every operation using A's identifier.
- Replay matrix: same ID with changed params, tool, event kind, and agent.
- Concurrent resume attempts: only one atomic consume succeeds if single-use is implemented.
- Assert list responses omit `raw_request`; detail includes it only for the owner if that remains intended.
- Negative test the action fingerprint by changing JSON key order without changing semantics; canonicalization should still match.

## Validation commands

```bash
cd backend
pytest -q tests/test_override_authorization.py tests/test_zfae_three_core_sentinels.py tests/test_tool_use_loop.py
pytest -q
python -m a0p_skills.test_build_runner --root .
python -m a0p_skills.boundaries_runner --root . --strict
```

## Acceptance criteria

- [ ] No unscoped route-level override lookup remains.
- [ ] Expiration is internal, owner-scoped, or admin-only.
- [ ] Resume is bound to exact owner and action.
- [ ] Replay and concurrency behavior is tested and documented.
- [ ] List/detail projections respect raw-request sensitivity.
- [ ] Contracts/CHECKS close with no gaps.

## Rollback

Disable resume/override UI temporarily while preserving halted actions. Never roll back to anonymous detail reads or public expiration mutation.

## hmmm

- Whether approved overrides are intended to be single-use, bounded multi-use, or idempotent for one request ID. Choose explicitly and encode status transitions.
- Whether expired records must remain for audit retention or may be deleted by TTL.
- Whether administrators may inspect raw requests; this requires a separate privacy policy and audit trail.

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
