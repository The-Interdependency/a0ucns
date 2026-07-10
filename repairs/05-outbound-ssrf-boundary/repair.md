# Repair 05 — Apply one fail-closed SSRF and redirect boundary to all outbound connectors

**Codex handoff:** implementation-ready  
**Priority:** P0 — release blocker  
**Primary target:** `The-Interdependency/a0-betatest`  
**Dependencies:** coordinate with Repair 06 credential migration; independent of registry internals

## Mission

Prevent webhooks, generic MCP registrations, and any related server-side fetch from reaching loopback, private, link-local, metadata, reserved, or redirect-selected internal targets. Reuse and generalize the strongest logic already present in the Odysseus relay.

## Audit baseline

- Integration repository: `The-Interdependency/a0ucns`
- Audit head: `0ac2953ff5a12798ac054bfa1d41bb268b99e9b3`
- Mirrored application pin at audit: `The-Interdependency/a0-betatest@4f089d40455e6bca3fac682eeed5ff26694057e5`
- The application mirror is not authoritative. Re-resolve the current upstream `main` before editing.

## Source evidence to confirm on current `main`

- webhook registration validates only an `http://` or `https://` prefix.
- `backend/tools/webhook.py` performs a server-side POST and follows redirects.
- MCP registration similarly accepts an arbitrary HTTP(S) URL.
- `backend/tools/mcp_relay.py` posts with `follow_redirects=True` and has no host/IP guard.
- `backend/tools/odysseus_relay.py` already resolves hosts, rejects non-global addresses by default, checks IPv4 embedded in IPv6/NAT64 forms, pins paths, and disables redirects.

## Required invariants

- Every egress target is validated at registration and again immediately before connection to reduce DNS-rebinding exposure.
- Only HTTP and HTTPS are accepted; URL userinfo, malformed ports, fragments, and connector-inappropriate queries are rejected.
- All resolved addresses are checked; one unsafe answer rejects the host.
- Loopback, private, link-local, multicast, unspecified, reserved, and cloud-metadata addresses are blocked by default across IPv4 and IPv6 encodings.
- Redirects are disabled. If a connector requires redirects, each hop is manually resolved and validated with a strict hop limit.
- Ordinary users cannot enable unrestricted private-network access with a boolean.
- Error responses do not reflect internal hostnames, IPs, tokens, stack traces, or full upstream bodies.

## Non-goals

- Sentinel keyword matching is not an SSRF control and must not be used as one.
- Do not validate only the URL string while skipping DNS results.
- Do not allow private targets merely because the product is sometimes self-hosted. Private egress needs an operator-controlled allow-list and explicit deployment mode.

## Proposed file plan

| Path | Change | Purpose | Risk | Required tests |
|---|---|---|---|---|
| `backend/tools/outbound_guard.py` | create | canonical URL/DNS/IP/redirect policy | critical | exhaustive pure/mocked tests |
| `backend/tools/odysseus_relay.py` | refactor | consume shared guard without weakening existing behavior | high | regression suite |
| `backend/tools/webhook.py` | modify | guarded POST, redirects off, bounded response | critical | SSRF matrix |
| `backend/tools/mcp_relay.py` | modify | guarded JSON-RPC POST, redirects off, bounded response | critical | SSRF matrix |
| `backend/api_tools_mcp_skills.py` | modify | validate registration; remove ordinary-user private opt-in | critical | route tests |
| `backend/tests/test_outbound_guard.py` | create | resolver and redirect evidence | critical | CHECKS declarations |
| `backend/tests/test_connector_ssrf.py` | create | webhook/MCP/Odysseus integration with MockTransport | critical | no real network |

## Implementation sequence

1. Extract the Odysseus host-resolution logic into a dependency-light `outbound_guard` module with a clear `MODULE_BUILD` and `BOUNDARIES` declaration.
2. Define a parsed target object so validation and URL construction do not drift. Validate scheme, netloc, hostname, port, userinfo, query/fragment policy, and normalized path.
3. Resolve DNS in a bounded worker thread. Check every result and embedded IPv4 representation (mapped, 6to4, Teredo, NAT64). Refuse on timeout or ambiguity.
4. Re-run resolution immediately before the request. For stronger rebinding defense, connect to the validated IP while preserving the Host/SNI identity only if the HTTP stack supports this safely; otherwise document residual risk as `hmmm` and keep short DNS-to-connect time.
5. Set `follow_redirects=False` for webhook, MCP, and Odysseus clients. Treat 3xx as a controlled error unless a manually validated redirect policy is implemented.
6. Add response byte limits for webhook and MCP comparable to Odysseus. Bound error previews and never echo full internal URLs.
7. Decide private-network policy:
   - multi-tenant default: disallow;
   - optional self-hosted mode: operator-configured exact host/CIDR allow-list, not a user-controlled wildcard;
   - any admin exception must be audited and represented in metadata.
8. Validate on registration for fast feedback and on every call for security.
9. Replace duplicated Odysseus guard logic only after parity tests demonstrate no regression.
10. Update connector schemas/UI to explain refusal without exposing internal details.

## Source-owned contracts to add or revise

```text
outbound_connector_rejects_non_global_targets
  given: a webhook, MCP, or Odysseus target resolving to loopback, private, link-local, metadata, reserved, or embedded private IPv4
  then: registration or invocation is refused before network egress
  class: security

outbound_connector_validates_every_dns_answer
  given: a hostname with mixed global and non-global resolution results
  then: the entire target is rejected
  class: security

outbound_redirect_cannot_escape_guard
  given: a validated global endpoint responds with a redirect to an unsafe target
  then: the client does not follow it and no second request is made
  class: security

outbound_guard_runs_at_invocation
  given: a hostname was safe at registration but resolves unsafe at call time
  then: invocation is refused
  class: security
```

## Test-owned checks

- Parameterized IP matrix: IPv4/IPv6 loopback, RFC1918, link-local, multicast, unspecified, documentation/reserved ranges, metadata addresses, v4-mapped IPv6, 6to4, Teredo, and NAT64 wrappers.
- Mock `socket.getaddrinfo`; no test should rely on public DNS.
- MockTransport tests prove zero request calls on rejection and one call on a safe target.
- Redirect test proves no follow-up request.
- Malformed URL tests: userinfo, invalid port, scheme confusion, encoded traversal where paths are pinned, query/fragment in base URLs.
- Self-hosted allow-list test, only if that mode is implemented, proves ordinary users cannot grant themselves broader access.

## Validation commands

```bash
cd backend
pytest -q tests/test_outbound_guard.py tests/test_connector_ssrf.py
pytest -q tests/test_tool_use_loop.py tests/test_security.py
pytest -q
python -m a0p_skills.test_build_runner --root .
python -m a0p_skills.boundaries_runner --root . --strict
```

## Acceptance criteria

- [ ] Webhook, MCP, and Odysseus use one tested guard.
- [ ] Validation occurs at registration and invocation.
- [ ] Redirects cannot change the destination silently.
- [ ] Unsafe address matrix is blocked without real network calls.
- [ ] Ordinary users cannot opt into arbitrary private egress.
- [ ] Response/error sizes and secret exposure are bounded.

## Rollback

Disable affected connector kinds or restrict them to an operator allow-list. Never roll back by restoring arbitrary user-controlled egress.

## hmmm

- The exact production egress topology and whether a network-layer firewall already exists. Application controls remain required even if one does.
- Whether legitimate self-hosted MCP/Odysseus deployments need private targets. If yes, define an operator-owned allow-list and threat model.
- Whether HTTPX can safely pin the validated address while preserving TLS SNI in the deployed version; document residual DNS-rebinding risk if not.

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
