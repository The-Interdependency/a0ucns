# Repair 06 — Encrypt connector tokens and webhook secrets at rest with an idempotent migration

**Codex handoff:** implementation-ready  
**Priority:** P0 — release blocker  
**Primary target:** `The-Interdependency/a0-betatest`  
**Dependencies:** coordinate field/schema changes with Repairs 04 and 05

## Mission

Bring webhook, MCP, and Odysseus credentials under the same authenticated-encryption boundary already used for BYOK and custom keys. Remove plaintext credential fields from Mongo documents and avoid retaining decrypted values in the process-global tool registry.

## Audit baseline

- Integration repository: `The-Interdependency/a0ucns`
- Audit head: `0ac2953ff5a12798ac054bfa1d41bb268b99e9b3`
- Mirrored application pin at audit: `The-Interdependency/a0-betatest@4f089d40455e6bca3fac682eeed5ff26694057e5`
- The application mirror is not authoritative. Re-resolve the current upstream `main` before editing.

## Source evidence to confirm on current `main`

- `backend/crypto_vault.py` encrypts BYOK values with Fernet.
- `backend/api_extensions.py` encrypts custom-key values with the same secret.
- webhook registration currently stores `webhook_secret` directly in `user_tools_col`.
- MCP and Odysseus registration currently store bearer `token` directly in their server documents.
- hydration copies webhook secrets into long-lived `Tool` objects.
- `CONNECTIONS.md` itself says Odysseus tokens belong in the crypto vault.

## Required invariants

- No newly written connector credential is plaintext at the application document layer.
- Existing plaintext rows are migrated idempotently and plaintext fields are removed after successful encryption.
- Decryption occurs only at the narrow invocation boundary and plaintext is not stored in process-global registry state.
- List/get APIs expose only `has_secret`/`has_token` and safe metadata.
- Logs, exceptions, audits, and test snapshots never include plaintext or ciphertext values.
- Invalid/tampered ciphertext causes a controlled connector error, not a fallback to an empty or plaintext value.
- Key rotation/version metadata is represented even if rotation tooling is deferred.

## Non-goals

- Do not implement a public reveal endpoint for connector secrets.
- Do not consider database-provider encryption alone sufficient; the application must not write plaintext fields.
- Do not silently discard a credential that fails migration; surface a coarse repair-required state.

## Proposed file plan

| Path | Change | Purpose | Risk | Required tests |
|---|---|---|---|---|
| `backend/connector_vault.py` | create or extend `crypto_vault.py` | purpose-scoped encrypt/decrypt/version API | critical | round-trip/tamper tests |
| `backend/api_tools_mcp_skills.py` | modify | encrypt writes, migrate reads, omit secrets from projections | critical | API/migration tests |
| `backend/tools/webhook.py` | modify | decrypt secret immediately before signing | critical | HMAC integration |
| `backend/tools/mcp_relay.py` | modify | decrypt token immediately before request | critical | bearer integration |
| `backend/tools/odysseus_relay.py` | modify | decrypt token immediately before request | critical | bearer integration |
| `backend/tools/registry.py` | modify | store credential reference/ciphertext, not plaintext | high | registry inspection |
| `backend/db.py` | modify if migration state/index needed | safe rollout metadata | medium | index tests |
| `backend/migrations/migrate_connector_secrets.py` | create | idempotent backfill and `$unset` | critical | run-twice fixture |
| `backend/tests/test_connector_secret_storage.py` | create | evidence | critical | CHECKS declarations |

## Implementation sequence

1. Define one connector-vault API. Include a version and purpose/domain in the encrypted payload, for example `webhook-signing`, `mcp-bearer`, or `odysseus-bearer`, so ciphertext cannot be accidentally swapped across credential classes without detection at the application layer.
2. New document fields should be explicit, such as `webhook_secret_enc`, `token_enc`, and `secret_version`. Stop writing plaintext immediately.
3. Do not hydrate decrypted secrets into `_REG`. Store only the record identifier and non-secret metadata; fetch the owner-scoped record and decrypt within the connector invocation.
4. Implement dual-read for one migration window only: prefer encrypted; if plaintext exists, encrypt it, atomically write ciphertext, then `$unset` plaintext. Never return the plaintext through an API.
5. Provide a standalone/idempotent migration command for operators. It must:
   - scan only expected collections/fields;
   - skip already encrypted rows;
   - validate encryption before unsetting plaintext;
   - report counts without values;
   - fail nonzero on unresolved rows;
   - be safe to run repeatedly.
6. Decide startup behavior. Avoid doing an unbounded migration synchronously on every boot; a bounded compatibility read is acceptable while the operator migration is pending.
7. On decrypt failure, mark the connector unusable with a coarse error such as `credential unavailable; reconnect required`. Do not log the token, ciphertext, or target URL.
8. Update API list projections and frontend forms. A secret update must rotate ciphertext and increment non-sensitive rotation metadata.
9. Add contracts/checks, including database inspection that proves known plaintext canaries are absent.

## Source-owned contracts to add or revise

```text
connector_credentials_are_encrypted_at_rest
  given: webhook, MCP, and Odysseus credentials are registered
  then: persisted documents contain ciphertext/version fields and no plaintext credential fields or values
  class: security

connector_secret_migration_is_idempotent
  given: a mix of plaintext, encrypted, missing, and malformed legacy rows
  then: two migration runs produce the same resolved state, never erase an unresolved secret, and exit nonzero for rows requiring operator action
  class: migration

connector_decrypt_is_invocation_scoped
  given: registry hydration and tool listing
  then: no decrypted credential is retained in registry objects or returned by an API
  class: security

connector_ciphertext_tamper_fails_closed
  given: modified ciphertext
  then: invocation performs no outbound request and returns a coarse reconnect-required error
  class: security
```

## Test-owned checks

- Register each connector with a unique plaintext canary; inspect raw Mongo fixtures and serialized registry objects; assert the canary is absent.
- Verify actual HMAC/bearer behavior through MockTransport after narrow decryption.
- Run migration twice over mixed fixtures and compare snapshots.
- Tamper ciphertext and assert zero network calls and no secret-bearing error text.
- Capture logs during registration, migration, hydration, and invocation; assert neither plaintext nor ciphertext appears.
- Verify API/OpenAPI responses have no secret fields beyond booleans.

## Validation commands

```bash
cd backend
pytest -q tests/test_connector_secret_storage.py tests/test_security.py
pytest -q tests/test_tool_use_loop.py tests/test_connector_ssrf.py
pytest -q
python -m a0p_skills.test_build_runner --root .
python -m a0p_skills.boundaries_runner --root . --strict
```
Run the migration in dry-run and fixture-backed apply modes; include counts in the PR report, never values.

## Acceptance criteria

- [ ] All connector credential writes are encrypted.
- [ ] Registry objects contain no decrypted secrets.
- [ ] Migration is idempotent and preserves unresolved rows.
- [ ] Plaintext fields are removed after verified migration.
- [ ] Tamper fails closed before egress.
- [ ] APIs/logs expose neither plaintext nor ciphertext.

## Rollback

Retain dual-read compatibility for encrypted and legacy plaintext rows only during a tightly bounded rollback window, but keep new writes encrypted. Never mass-decrypt records to roll back. If code rollback is unavoidable, disable connectors whose runtime cannot read encrypted records.

## hmmm

- Key-rotation schedule and whether a second secret/key ID is already available in deployment.
- Whether old database backups containing plaintext can be re-encrypted or must be expired under retention policy.
- Whether a cloud KMS should replace the environment-held Fernet key. This repair can establish a versioned abstraction without blocking on KMS adoption.

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
