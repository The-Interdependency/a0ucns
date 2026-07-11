# Repair 07 — Harden cookies and GitHub OAuth redirect/state handling

**Codex handoff:** implementation-ready  
**Priority:** P0 — release blocker for production authentication  
**Primary target:** `The-Interdependency/a0-betatest`  
**Dependencies:** Repair 09 must supply the resulting production configuration

## Mission

Make production cookies transport-secure and bind GitHub OAuth authorization to a fixed configured redirect plus a cryptographically random, expiring, single-use state. Remove trust in the caller-provided `Origin` header.

## Audit baseline

- Integration repository: `The-Interdependency/a0ucns`
- Audit head: `0ac2953ff5a12798ac054bfa1d41bb268b99e9b3`
- Mirrored application pin at audit: `The-Interdependency/a0-betatest@4f089d40455e6bca3fac682eeed5ff26694057e5`
- The application mirror is not authoritative. Re-resolve the current upstream `main` before editing.

## Source evidence to confirm on current `main`

- `backend/auth/__init__.py::_set_cookies` sets access and refresh cookies with `secure=False`.
- the GitHub OAuth start route derives its redirect destination from `request.headers["origin"]` or a fallback.
- the callback request model includes optional `state`, but the callback does not validate it.
- token exchange does not visibly enforce a server-owned redirect URI contract.
- refresh tokens are self-contained JWTs with no explicit rotation/revocation record.

## Required invariants

- Production auth cookies are `HttpOnly`, `Secure`, and use an explicitly chosen `SameSite` policy.
- Cookie behavior is configuration-driven but fails closed in a production environment.
- OAuth redirect URIs come from a server-side exact allow-list/configuration, never arbitrary request headers.
- Every OAuth start generates high-entropy state; callback validates expiry, browser/session binding, provider, redirect, and single use.
- State comparison is constant-time where applicable and consumed atomically.
- OAuth errors returned to clients are coarse and do not include upstream response bodies, tokens, client secrets, or stack traces.
- Existing password auth and bearer-token extraction continue to work.

## Non-goals

- Do not use the OAuth `state` value as an authorization token after callback.
- Do not permit wildcard redirect origins.
- Full refresh-token revocation/rotation may be a separate patch if it materially enlarges scope, but its status must remain explicit rather than implied solved.

## Proposed file plan

| Path | Change | Purpose | Risk | Required tests |
|---|---|---|---|---|
| `backend/auth/__init__.py` | major modify | secure cookie settings; fixed redirect; state create/consume | critical | auth/OAuth tests |
| `backend/auth/oauth_state.py` | create if separation helps | state hashing, persistence, expiry, atomic consume | critical | unit tests |
| `backend/db.py` | modify | OAuth state collection and TTL/unique indexes | high | index tests |
| `backend/models/config` or new settings module | modify/create | typed auth configuration | high | prod fail-closed tests |
| frontend login callback | modify | round-trip state and handle coarse errors | high | frontend tests/build |
| `.env.example` / deployment docs | modify | exact required values, no secrets | medium | config review |
| `backend/tests/test_auth_hardening.py` | create | executable evidence | critical | CHECKS declarations |

## Implementation sequence

1. Introduce typed auth settings for environment name, cookie secure flag/domain, frontend origin(s), and exact GitHub redirect URI. In production, refuse startup if secure cookies or a valid HTTPS redirect are not configured.
2. Set cookies with `httponly=True`, `secure=True` in production, explicit `samesite`, path, and bounded max age. Keep a documented local-development exception only for loopback HTTP.
3. Stop deriving redirect from `Origin`. Use the exact configured redirect URI for authorization and token exchange.
4. Implement OAuth state:
   - generate with `secrets.token_urlsafe`;
   - store only a hash plus provider, redirect URI, creation/expiry, and a browser-bound nonce or HttpOnly state cookie;
   - return/send the raw state only to the initiating browser;
   - validate and atomically consume on callback;
   - reject missing, mismatched, expired, reused, or wrong-provider state.
5. Add TTL cleanup while retaining enough result distinction internally for audit. Avoid revealing whether a particular state existed.
6. Sanitize upstream exceptions. Log coarse classes and correlation IDs, not authorization codes or tokens.
7. Review CSRF on all cookie-authenticated mutations. SameSite is one layer; if cross-site deployment requires `SameSite=None`, add a proper CSRF token mechanism in the same or a follow-up release-blocking patch.
8. Decide refresh-token rotation. At minimum document the current residual risk in `hmmm`; preferably add a token ID, stored rotation record, and one-time refresh.
9. Update metadata/contracts and frontend flow.

## Source-owned contracts to add or revise

```text
production_cookies_are_transport_secure
  given: production configuration and successful login/refresh
  then: access and refresh Set-Cookie values are HttpOnly, Secure, explicitly SameSite, and bounded in scope/lifetime
  class: security

github_oauth_redirect_is_server_owned
  given: arbitrary Origin and Host headers on OAuth start
  then: the returned authorization request uses only the configured exact redirect URI
  class: security

github_oauth_state_is_single_use_and_browser_bound
  given: missing, wrong, expired, cross-browser, or replayed state
  then: callback rejects before token exchange or account linking
  class: security

oauth_error_does_not_disclose_secrets
  given: upstream token/user API failures
  then: client and captured logs contain no code, access token, client secret, or full upstream body
  class: security
```

## Test-owned checks

- Inspect `Set-Cookie` attributes under local and production settings; production misconfiguration must fail startup/config validation.
- Override `Origin`, `Host`, and forwarded headers; redirect URI remains fixed.
- State matrix: valid once, missing, altered, expired, reused, wrong provider, wrong browser nonce.
- Mock GitHub token/user endpoints and assert token exchange occurs only after state validation.
- Capture logs and response bodies for upstream failures; scan for seeded secrets/codes.
- Verify password login, logout, bearer header, and refresh still work.

## Validation commands

```bash
cd backend
pytest -q tests/test_auth_hardening.py tests/test_security.py
pytest -q
python -m a0p_skills.test_build_runner --root .
python -m a0p_skills.boundaries_runner --root . --strict
cd ../frontend && npm run build
```

## Acceptance criteria

- [ ] Production cookies are Secure/HttpOnly with explicit SameSite.
- [ ] Production config fails closed when redirect/cookie security is invalid.
- [ ] OAuth redirect is fixed server-side.
- [ ] State is high-entropy, expiring, browser-bound, atomically single-use, and tested.
- [ ] Errors/logs do not disclose credentials or codes.
- [ ] Existing login/refresh/logout behavior remains tested.

## Rollback

Disable GitHub OAuth while preserving password authentication. Do not roll back to unvalidated state or caller-selected redirects. Local HTTP cookies may remain a documented development-only exception.

## hmmm

- The deployed frontend/backend origin topology and whether cookies require `SameSite=Lax`, `Strict`, or `None`.
- Whether a reverse proxy terminates TLS and how the app reliably detects production without trusting spoofable forwarded headers.
- Whether refresh-token rotation/revocation is included here or tracked as a separately owned P0 item.

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
