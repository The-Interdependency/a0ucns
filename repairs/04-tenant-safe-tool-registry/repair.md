# Repair 04 — Namespace the in-process tool registry by owner and enforce ownership at dispatch

**Codex handoff:** implementation-ready  
**Priority:** P0 — release blocker  
**Primary target:** `The-Interdependency/a0-betatest`  
**Dependencies:** Repair 02 for strict identity; coordinate with Repairs 05 and 06

## Mission

Eliminate cross-tenant tool collisions and wrong-owner dispatch. Two users must be able to register the same public tool name without either user's agent resolving or invoking the other user's webhook, MCP server, or Odysseus connection.

## Audit baseline

- Integration repository: `The-Interdependency/a0ucns`
- Audit head: `0ac2953ff5a12798ac054bfa1d41bb268b99e9b3`
- Mirrored application pin at audit: `The-Interdependency/a0-betatest@4f089d40455e6bca3fac682eeed5ff26694057e5`
- The application mirror is not authoritative. Re-resolve the current upstream `main` before editing.

## Source evidence to confirm on current `main`

- Mongo uniqueness is `(user_id, name)` for `user_tools_col`.
- `backend/tools/registry.py` stores all tools in one `_REG: dict[str, Tool]` keyed only by bare name; `register` overwrites an existing entry.
- `lookup(name)` has no `user_id` argument.
- `_hydrate_user_tools` loads one user's records into that process-global bare-name map.
- the teacher tool loop resolves `tools_allowed` through bare-name lookup.
- invocation looks up by bare name and does not perform a final owner check before dispatch.
- built-in collision protection exists, but same-name collisions between ordinary users remain possible.

## Required invariants

- A lookup made for user A can return only A-owned tools or approved global built-ins.
- User B's hydration, registration, refresh, or deletion cannot alter A's registry entries.
- A final owner assertion occurs at invocation, not only at list/schema construction.
- Global built-ins cannot be shadowed by any user tool.
- Same-name user tools are supported safely because provider tool schemas are generated per request/user.
- Registry deletion evicts only the named owner's entry.
- Persistent records and in-process records converge deterministically after hydration.

## Non-goals

- Do not force globally unique human-readable names across all users as the primary fix; that leaks tenancy and creates unnecessary UX constraints.
- Do not trust a provider-returned tool name without resolving it in the authenticated user's namespace.
- Do not put owner IDs into model-visible tool descriptions unless necessary.

## Proposed file plan

| Path | Change | Purpose | Risk | Required tests |
|---|---|---|---|---|
| `backend/tools/registry.py` | major modify | owner-qualified keys, lookup/list/invoke API | critical | registry unit matrix |
| `backend/tools/__init__.py` | modify | re-export new signatures | high | imports |
| `backend/api_tools_mcp_skills.py` | modify | hydrate/register/delete current owner's namespace only | critical | two-user API tests |
| `backend/tools/gated_invoke.py` | modify | preserve owner through dispatch and audit | critical | wrong-owner refusal |
| `backend/interdependent_lib/zfae/runtime.py` | modify | user-qualified tool resolution in teacher/native loops | critical | model tool-call isolation |
| `backend/tools/agent_loop.py` | inspect/modify | ensure executor receives authenticated namespace | high | tool loop tests |
| `backend/tests/test_tool_tenant_isolation.py` | create | same-name end-to-end evidence | critical | CHECKS declarations |

## Implementation sequence

1. Replace the bare-name registry key with an explicit key such as `(owner_user_id, name)`. Reserve `owner_user_id=None` for global built-ins.
2. Define one resolution API, for example `lookup(name, *, user_id, include_globals=True)`, with deterministic precedence: owned tool first only when no global built-in uses that name; otherwise built-in names remain reserved.
3. Make `register`, `unregister`, `user_tool_names`, `list_tools`, and `invoke` owner-aware. Avoid optional owner arguments on private operations where omission could reopen the bug.
4. In `invoke`, resolve using `user["id"]` and assert `tool.owner_user_id in {None, user["id"]}` immediately before sentinel evaluation/dispatch.
5. Update hydration so it reconciles only one user's namespace. Never evict entries owned by another user.
6. Update all schema-building paths in ZFAE runtime to look up tools with the current user ID. A name in `sheet.tools_allowed` is meaningful only inside that owner's namespace.
7. Preserve globally unique generated names for mirrored MCP/Odysseus tools where useful, but do not rely on them as authorization.
8. Add safe migration for any API signature changes. In-process state does not need data migration; restart is acceptable after deployment.
9. Audit every `lookup`, `register`, `unregister`, and `invoke` call with code search. No legacy bare lookup should remain.
10. Add metadata/contracts and two-user regression tests.

## Source-owned contracts to add or revise

```text
tool_lookup_is_owner_namespaced
  given: users A and B each own a tool with the same name
  then: lookup for A returns A's tool and lookup for B returns B's tool
  class: security

tool_hydration_cannot_overwrite_other_owner
  given: A is hydrated, then B registers/refreshes/deletes a same-name tool
  then: A's registry entry and invocation target remain unchanged
  class: security

tool_invoke_enforces_final_owner
  given: an attempt to pass a Tool or name owned by B into an invocation authenticated as A
  then: dispatch is refused before any network or native side effect
  class: security

global_tools_cannot_be_shadowed
  given: a user registers a built-in name
  then: registration fails and the global tool remains unchanged
  class: security
```

## Test-owned checks

- Unit-test registry behavior for global, A-owned, B-owned, same-name, delete, refresh, and restart/hydration cases.
- End-to-end test with two local mock webhook transports; both users register `echo`, invoke through the API and teacher loop, and each transport receives only its owner's payload.
- Test stale Mongo deletion: hydration removes only the acting user's stale entry.
- Test direct wrong-owner `Tool` dispatch cannot bypass name lookup.
- Test concurrent hydration of A and B repeatedly; outcomes must not depend on order.
- Plant the old bare dictionary implementation and verify the same-name check fails.

## Validation commands

```bash
cd backend
pytest -q tests/test_tool_tenant_isolation.py tests/test_tool_use_loop.py tests/test_security.py
pytest -q
python -m a0p_skills.test_build_runner --root .
python -m a0p_skills.boundaries_runner --root . --strict
```
Run a code search for `lookup(` and `_REG[` and review every result manually.

## Acceptance criteria

- [ ] Registry storage and every API are owner-qualified.
- [ ] Final invocation rejects wrong-owner tools before side effects.
- [ ] Same-name two-user test passes through direct API and model tool loop.
- [ ] Built-ins remain unshadowable.
- [ ] Hydration order cannot change ownership resolution.
- [ ] All callers use the new namespace contract.

## Rollback

If the registry refactor must be rolled back, disable user-defined/MCP/Odysseus tools in multi-user mode. Do not restore a shared bare-name registry while those features remain enabled.

## hmmm

- Whether `tools_allowed` should store stable opaque tool IDs rather than owner-local names. Namespacing is sufficient for this repair; opaque IDs may be a later migration.
- Whether multiple worker processes require a registry cache invalidation channel. Correct owner resolution must hold even if hydration is per-process.
- Whether user tools may intentionally override non-security-sensitive globals; current doctrine says no and this handoff preserves it.

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
