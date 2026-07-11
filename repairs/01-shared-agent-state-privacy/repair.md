# Repair 01 — Eliminate cross-user leakage through the process-global inspector agent

**Codex handoff:** implementation-ready  
**Priority:** P0 — release blocker  
**Primary target:** `The-Interdependency/a0-betatest`  
**Dependencies:** none; complete before exposing the service to multiple users

## Mission

Remove every path by which ordinary chat content is written into process-global agent memory and later returned through an inspector endpoint. Preserve useful diagnostics only when they are authenticated, owner-scoped, and free of raw user text.

Treat request-derived prompts, model replies, session text, memory seeds, and tool results as user data. A process-global object is not an acceptable owner boundary.

## Audit baseline

- Integration repository: `The-Interdependency/a0ucns`
- Audit head: `0ac2953ff5a12798ac054bfa1d41bb268b99e9b3`
- Mirrored application pin at audit: `The-Interdependency/a0-betatest@4f089d40455e6bca3fac682eeed5ff26694057e5`
- The application mirror is not authoritative. Re-resolve the current upstream `main` before editing.

## Source evidence to confirm on current `main`

- `backend/server.py` creates one module-global `AGENT = ZFAEAgent(...)`.
- `chat_single`, `chat_fanout`, `chat_daisychain`, and `chat_synthesize` call `AGENT.receive(...)` and/or `AGENT.absorb(...)` with request or response content.
- `backend/interdependent_lib/zfae/__init__.py::ZFAEAgent` wraps a `PCNAEngine`.
- `backend/interdependent_lib/pcna/pcna.py::push_intent` stores an intent prefix in long-term memory; `absorb_response` stores a reply prefix in short-term memory.
- `backend/server.py::inspector_snapshot` returns `AGENT.card()` without an authenticated owner parameter.
- `backend/server.py::inspector_heartbeat` mutates the same shared object.
- `MemoryCore.snapshot()` returns literal `lt` and `st` entries.

## Required invariants

- No request-derived string from user A may become observable to user B through inspector, health, audit, metrics, or another chat route.
- No unauthenticated endpoint may return raw or prefix-truncated chat/memory content.
- No ordinary chat route may mutate process-global state containing user text.
- Diagnostic responses may expose counts, shapes, digests, timestamps, and bounded numerical state, but not raw prompts, responses, API keys, tokens, cookies, or memory entries.
- A requested `agent_id` must be resolved together with the authenticated `user_id`; other-owner access returns 404.
- A native research trace must remain distinguishable from a teacher/model response and must not silently restore the legacy global path.

## Non-goals

- Do not redesign the ZFAE inference engine or its mathematical substrate.
- Do not create a new in-memory dictionary keyed by user and call that durable multi-tenant storage; process memory may be used only for non-sensitive caches with explicit lifecycle semantics.
- Do not retain raw text merely because it is truncated.
- Do not solve this by obscuring inspector identifiers.

## Proposed file plan

| Path | Change | Purpose | Risk | Required tests |
|---|---|---|---|---|
| `backend/server.py` | modify | remove legacy global writes; authenticate and scope inspector routes or retire them | high | two-user HTTP isolation |
| `backend/interdependent_lib/zfae/__init__.py` | modify if retained | separate legacy diagnostic persona from user-data state; add safe snapshot surface | medium | snapshot redaction |
| `backend/interdependent_lib/pcna/memory_core.py` | modify if diagnostics retain it | add an aggregate/redacted snapshot distinct from the internal snapshot | medium | raw values absent |
| `backend/agents/routes.py` / `backend/agents/store.py` | reuse or modify | resolve an explicitly owned agent for diagnostics | high | other-owner 404 |
| `backend/tests/test_tenant_isolation.py` | create | prove no cross-user inspector leakage | high | CHECKS declarations |
| relevant frontend inspector page | modify if route shape changes | require explicit owned agent or show aggregate-only diagnostics | medium | UI build |

## Implementation sequence

1. Search every use of the module-global `AGENT`. Classify each use as user-data-bearing, aggregate-only, or dead legacy behavior.
2. Remove `AGENT.receive(...)` and `AGENT.absorb(...)` from user chat routes. User chat persistence must stay in the already owner-scoped collections and/or owned `AgentInstance` state.
3. Choose one explicit inspector contract:
   - preferred: `GET /api/inspector/snapshot?agent_id=<owned-id>` backed by the owner-scoped agent store and returning a redacted diagnostic shape; or
   - containment fallback: retire the legacy inspector mutation endpoint and return only static/public engine metadata.
4. Require `get_current_user` for any inspector response containing state. Resolve the object with both `agent_id` and `user["id"]`.
5. Introduce a named redaction boundary, for example `public_diagnostics()` or `redacted_snapshot()`. Do not destructively weaken the internal snapshot needed by engine code; make the safe public surface explicit.
6. Ensure the redacted shape excludes `memory.lt`, `memory.st`, sub-cache contents, prompt fragments, response fragments, tool previews, and secrets. Counts and capacities are acceptable.
7. Remove or quarantine the unauthenticated heartbeat mutation route. If heartbeat remains user-visible, bind it to an owned agent and avoid storing raw `intent` text.
8. Update module metadata and frontend callers.
9. Add a regression that inserts unmistakable canary text for user A, exercises every inspector path as user B and anonymously, and asserts the canary never appears in status, body, logs captured by the test, or serialized diagnostics.

## Source-owned contracts to add or revise

```text
inspector_requires_authenticated_owner
  given: an inspector request for an agent owned by another user or no authenticated user
  then: the service returns 404 or 401 without disclosing whether state exists
  class: security

chat_routes_do_not_mutate_global_user_text_state
  given: single, fanout, daisy, and synthesis calls containing a unique canary
  then: no process-global diagnostic snapshot contains the canary or any request/reply prefix
  class: security

public_diagnostics_exclude_raw_memory
  given: an owned agent whose internal memory contains raw strings
  then: the public diagnostic response contains aggregate metadata only and no raw memory values
  class: privacy
```

## Test-owned checks

- Two authenticated users, A and B: write a canary through each legacy chat route as A; query every inspector endpoint as B; assert no canary and no A-owned state.
- Anonymous inspector request: assert 401 for private diagnostics, or verify the explicitly public response is static and contains no memory fields.
- Same-owner request: assert the approved aggregate fields remain available.
- Unit test the redaction function against nested raw strings, including LT, ST, sub-cache, transcript, and tool preview keys.
- Negative test: temporarily reintroduce one `AGENT.receive(canary)` call and verify the isolation check fails before removing the mutation.

## Validation commands

```bash
cd backend
pytest -q tests/test_tenant_isolation.py tests/test_security.py
pytest -q
python -m a0p_skills.test_build_runner --root .  # adapt to the current runner CLI
python -m a0p_skills.boundaries_runner --root . --strict
cd ../frontend && npm run build
```
Use the actual documented runner commands if the current skill copy differs; report any `hmmm` instead of inventing flags.

## Acceptance criteria

- [ ] No user chat route calls a process-global text-bearing agent.
- [ ] All non-static inspector state is authenticated and owner-scoped.
- [ ] Public diagnostics contain no literal memory, prompt, response, or tool-result text.
- [ ] Anonymous and cross-owner tests pass.
- [ ] Source CONTRACTS and test CHECKS reconcile with no gaps.
- [ ] Existing chat behavior and frontend build remain functional.

## Rollback

Revert the inspector feature or disable it behind a default-off feature flag. Do **not** roll back by restoring global raw-text state. If diagnostics must be temporarily unavailable, return 503/404 rather than exposing shared memory.

## hmmm

- Whether the legacy inspector is still used by any deployed frontend route; determine by searching API clients and access logs if available.
- Whether per-agent diagnostics should include hashed state lineage; hashes may still be sensitive correlation identifiers and need an explicit policy.
- Whether a deliberately public shared research agent is desired. That would require a separate consent, retention, redaction, and data-use design; it is not implied by the current code.

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
