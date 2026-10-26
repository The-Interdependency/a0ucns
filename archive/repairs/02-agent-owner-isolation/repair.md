# Repair 02 — Make all agent CRUD derive ownership exclusively from authenticated identity

**Codex handoff:** implementation-ready  
**Priority:** P0 — release blocker  
**Primary target:** `The-Interdependency/a0-betatest`  
**Dependencies:** coordinate with Repair 01 for inspector ownership; otherwise independent

## Mission

Close the client-selected-user authorization path in `backend/agents/routes.py` and retire or owner-scope the duplicate legacy `/api/agents` surface. Every private agent read or mutation must derive the owner from a verified credential, never from body/query `user_id`.

## Audit baseline

- Integration repository: `The-Interdependency/a0ucns`
- Audit head: `0ac2953ff5a12798ac054bfa1d41bb268b99e9b3`
- Mirrored application pin at audit: `The-Interdependency/a0-betatest@4f089d40455e6bca3fac682eeed5ff26694057e5`
- The application mirror is not authoritative. Re-resolve the current upstream `main` before editing.

## Source evidence to confirm on current `main`

- `backend/agents/routes.py::_resolve_user` catches authentication exceptions and returns a caller-provided fallback.
- list/create/get/update/delete/archive and teacher-context-preview pass body or query `user_id` into that fallback path.
- chat and training routes already use `get_current_user` without a fallback, demonstrating the intended pattern.
- `backend/server.py` also exposes a separate global `agents_col` surface at `/api/agents`, including unauthenticated list, create, manifest, and delete operations keyed by slug.
- `backend/db.py` indexes `agents_col` by global slug, while `agent_instances_col` is owner-oriented.

## Required invariants

- The authenticated principal is the sole source of `user_id` for private agent operations.
- A client-supplied `user_id` is ignored or rejected; it never selects an owner namespace.
- Cross-owner access returns 404 to avoid existence disclosure.
- Create writes the authenticated owner even when a malicious body contains another ID.
- Update payloads cannot alter `user_id`, `_id`, created timestamps, checkpoint paths, or other server-owned fields.
- Deletion/purge may remove files only after owner-scoped database resolution succeeds.
- There is one canonical agent CRUD surface after migration; duplicate legacy behavior is removed or explicitly public/admin with a separate schema and doctrine.

## Non-goals

- Do not change agent naming mathematics or the six-mode lattice except where request schemas carry obsolete ownership fields.
- Do not return 403 with object existence for cross-owner reads when a 404 can preserve non-disclosure.
- Do not keep the legacy `/api/agents` endpoints merely for undocumented compatibility; identify actual callers.

## Proposed file plan

| Path | Change | Purpose | Risk | Required tests |
|---|---|---|---|---|
| `backend/agents/routes.py` | modify | require auth for all private CRUD and preview routes; remove fallback ownership | critical | full two-user CRUD matrix |
| `backend/agents/store.py` | inspect/modify | enforce owner in every query and safe purge ordering | critical | cross-owner no-op/404 |
| `backend/agents/schema.py` | modify if needed | remove client-owned identity fields from request/public models | medium | schema validation |
| `backend/server.py` | modify | retire or migrate duplicate `/api/agents` routes | high | compatibility/410 tests |
| `backend/db.py` | modify if legacy records migrate | indexes for owner-scoped canonical records | high | migration idempotency |
| frontend API callers | modify | stop sending `user_id`; use canonical `/api/instances` | medium | frontend build |
| `backend/tests/test_agent_owner_isolation.py` | create | executable security evidence | critical | CHECKS declarations |

## Implementation sequence

1. Inventory every agent endpoint and frontend caller. Distinguish `AgentInstance` from the older detachable-agent export collection.
2. Replace `_resolve_user(..., fallback)` with a strict authenticated dependency for all private CRUD and teacher preview operations. Prefer route parameters such as `user=Depends(get_current_user)` over manual exception handling.
3. Remove `user_id` from create/update/chat-preview request bodies where backward compatibility permits. If temporarily retained, mark it deprecated and ignore it; add a test proving smuggling fails.
4. Ensure every store query includes both object identity and authenticated owner. Keep 404 behavior for other-owner records.
5. Constrain update fields through a typed patch model or explicit allow-list. Reject attempts to mutate owner/server fields.
6. For purge, first resolve ownership, then derive the server-owned checkpoint directory. Never build a filesystem path directly from an untrusted request field.
7. Resolve the legacy `/api/agents` surface:
   - search frontend and external documentation for callers;
   - migrate any still-needed export/manifest feature behind authenticated ownership and a per-user uniqueness index; or
   - remove it and return an intentional migration response for one release.
   The preferred outcome is one canonical `/api/instances` lifecycle plus an explicit export endpoint on an owned instance.
8. Add an idempotent migration only if live legacy rows must be preserved. Do not fabricate ownership; unresolved owner is `hmmm` and requires operator review.
9. Update metadata blocks to `auth_boundary: read` or `write` as appropriate and add source contracts.

## Source-owned contracts to add or revise

```text
agent_create_uses_authenticated_owner
  given: user A creates an agent while the request body names user B
  then: the stored agent belongs to A and the smuggled owner value is ignored or rejected
  class: security

agent_crud_other_owner_non_disclosure
  given: user B addresses an agent owned by A across get, patch, archive, delete, purge, and teacher preview
  then: every operation returns 404 and leaves database and filesystem state unchanged
  class: security

agent_patch_rejects_server_owned_fields
  given: an update attempts to replace user_id, id, timestamps, or checkpoint location
  then: validation rejects the request and no protected field changes
  class: security

legacy_agent_surface_has_explicit_policy
  given: a request to each former /api/agents route
  then: the route is removed, authenticated/owner-scoped, or intentionally public according to a declared contract; no implicit global mutation remains
  class: doctrine
```

## Test-owned checks

- Build users A and B; exercise every CRUD verb and query/body ownership-smuggling variant.
- Verify database rows, timestamps, archives, and checkpoint files remain unchanged after B attacks A's object.
- Verify A can still perform the same operations.
- Assert anonymous requests fail before store access.
- Search the generated OpenAPI schema and ensure private request models no longer advertise authoritative `user_id` fields.
- Add a migration test if legacy rows are moved; run it twice and assert stable results.

## Validation commands

```bash
cd backend
pytest -q tests/test_agent_owner_isolation.py tests/test_zfae_api_sentinels.py
pytest -q
python -m a0p_skills.test_build_runner --root .
python -m a0p_skills.boundaries_runner --root . --strict
cd ../frontend && npm run build
```
Also grep for `_resolve_user(`, `user_id: str = "local"`, and `/api/agents` to confirm no unreviewed private fallback remains.

## Acceptance criteria

- [ ] No private agent route catches auth failure and substitutes a caller-selected owner.
- [ ] Every read/write/delete is owner-qualified.
- [ ] Cross-owner tests cover database and filesystem effects.
- [ ] The legacy agent surface has been removed or given an explicit authenticated ownership model.
- [ ] Frontend callers no longer rely on body/query ownership.
- [ ] Metadata and evidence graph are current.

## Rollback

Rollback may restore the prior route shape only behind a disabled-by-default compatibility adapter that still derives ownership from authentication. Never restore client-selected owner fallbacks.

## hmmm

- Ownership of pre-auth or historical `agents_col` rows. Do not assign them to the admin automatically without an explicit migration decision.
- Whether any external consumer depends on `/api/agents/{slug}/manifest`; search before removal and document evidence.
- Whether anonymous demo agents remain a desired feature. If yes, they need an isolated synthetic tenant with no access to authenticated records, not a caller-supplied `local` ID.

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
