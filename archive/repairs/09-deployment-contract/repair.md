# Repair 09 — Reconcile Cloud Run configuration with the current FastAPI/Mongo application

**Codex handoff:** implementation-ready  
**Priority:** P1 — production deploy blocker  
**Primary target:** `The-Interdependency/a0-betatest` plus deployment environment configuration  
**Dependencies:** Repairs 07 and 08; do not deploy before P0 fixes

## Mission

Replace inherited/stale deployment assumptions with an explicit, tested container and secret contract for the current application. A successful PR import smoke is not a successful deploy.

## Audit baseline

- Integration repository: `The-Interdependency/a0ucns`
- Audit head: `0ac2953ff5a12798ac054bfa1d41bb268b99e9b3`
- Mirrored application pin at audit: `The-Interdependency/a0-betatest@4f089d40455e6bca3fac682eeed5ff26694057e5`
- The application mirror is not authoritative. Re-resolve the current upstream `main` before editing.

## Source evidence to confirm on current `main`

- the examined workflow deploys Cloud Run with secret names such as `DATABASE_URL`, `SESSION_SECRET`, and Stripe/XAI values associated with the archived application lineage.
- the current backend fails startup/import without `MONGO_URL`, `DB_NAME`, `JWT_SECRET`, and `A0P_KEY_VAULT_SECRET`.
- auth hardening will also require exact frontend/redirect/cookie settings.
- the workflow specifies Cloud Run port `5000`, while the current FastAPI service and container/start command contract was not established by the reviewed workflow evidence.
- the deploy job was skipped on the examined pull request run.

## Required invariants

- The container starts from a clean checkout with only documented runtime inputs.
- The process listens on Cloud Run's `$PORT` contract or an explicitly mapped equivalent.
- Required secrets are named, provisioned, and mounted consistently with application settings.
- Mongo connectivity is tested without exposing credentials.
- Production cookie/OAuth configuration is secure and exact.
- Health/startup smoke proves the deployed revision is serving the current code, not only that an image built.
- Rollout is revisioned and reversible; failed health prevents traffic promotion.

## Non-goals

- Do not preserve obsolete PostgreSQL/Stripe/model-provider secrets unless current code proves they are needed.
- Do not use production credentials in pull-request jobs.
- Do not leave `--allow-unauthenticated` as an accidental default; decide whether the public app requires it and protect private routes at application level regardless.

## Proposed file plan

| Path/system | Change | Purpose | Risk | Required tests |
|---|---|---|---|---|
| root container definition/start script | create/modify after discovery | deterministic current app image and `$PORT` startup | critical | local container smoke |
| `.github/workflows/deploy.yml` | modify | correct secrets, trusted auth, rollout and smoke | critical | workflow run |
| backend settings/config module | modify | one validated runtime contract | high | missing/invalid env tests |
| `.env.example` / deployment docs | modify | exact non-secret configuration inventory | medium | doc review |
| Google Secret Manager / Cloud Run service | operator change | provision and bind current secret names | critical | revision status |
| `scripts/deploy_smoke.py` | create | authenticated/public health and route smoke | high | staging test |

## Implementation sequence

1. Discover the actual container files and process topology on current `main`. Record whether the image serves FastAPI only, frontend static assets plus API, or multiple processes. Do not infer from the old port.
2. Define one typed settings inventory. At minimum reconcile:
   - `MONGO_URL`
   - `DB_NAME`
   - `JWT_SECRET`
   - `A0P_KEY_VAULT_SECRET`
   - CORS/frontend origins
   - GitHub OAuth client/secret and exact redirect if enabled
   - cookie/environment settings from Repair 07
   - admin seed values only if intentionally used
   - storage roots suitable for ephemeral Cloud Run filesystem or external persistence.
3. Make the container command respect `$PORT`; add a local command that builds and runs the exact image with throwaway settings.
4. Decide persistence semantics for checkpoints/audit/traffic logs. Cloud Run local disk is ephemeral. Move durable state to an approved store or explicitly classify these files as ephemeral; do not imply persistence.
5. Update deploy authentication to a least-privilege method. Prefer workload identity federation over long-lived service-account JSON when available; preserve `id-token: write` only for the deploy job.
6. Build by immutable commit SHA, deploy a no-traffic or limited-traffic revision, run smoke, then promote. Keep previous revision available for rollback.
7. Smoke at least health, auth config, one DB-backed non-destructive request, and static frontend delivery if in the same service. Never print secrets.
8. Remove obsolete secret bindings after confirming no current import/runtime reference.
9. Document every operator-side secret/resource action and its rollback.

## Source-owned contracts to add or revise

```text
production_container_starts_with_declared_settings
  given: a clean image and the documented required configuration
  then: the service starts, listens on the platform port, and health succeeds without undeclared environment dependencies
  class: deployment

production_config_missing_secret_fails_closed
  given: any required auth, vault, or database secret is absent or malformed
  then: startup fails before serving traffic with a coarse configuration error
  class: security

deploy_promotes_only_after_smoke
  given: a new revision whose startup or smoke fails
  then: production traffic remains on the previous healthy revision
  class: deployment

ephemeral_storage_is_not_claimed_durable
  given: checkpoint/audit/log paths on Cloud Run local disk
  then: documentation and runtime behavior explicitly treat them as ephemeral or route durable data to an approved store
  class: doctrine
```

## Test-owned checks

- Build/run the exact container locally with throwaway Mongo and secrets.
- Parameterized config tests for missing/invalid Fernet key, JWT secret, Mongo settings, redirect, and production cookie flags.
- Confirm process binds the injected random `$PORT`.
- Staging deploy with no traffic; smoke; intentional failing revision proves no promotion.
- Inspect deployed environment variable names and secret references without revealing values.
- Restart/revision test for any state claimed durable.

## Validation commands

```bash
# adapt to discovered container file
DOCKER_BUILDKIT=1 docker build -t a0p:repair .
docker run --rm -e PORT=18080 --env-file .env.test -p 18080:18080 a0p:repair
curl --fail http://127.0.0.1:18080/api/health

# run deployment smoke against a no-traffic/staging URL
python scripts/deploy_smoke.py --base-url "$STAGING_URL"
```
Report the actual commands and revision IDs.

## Acceptance criteria

- [ ] Container/process topology is documented from source, not assumed.
- [ ] Required current settings and secrets are consistent across code, docs, and workflow.
- [ ] `$PORT` and health work in the exact image.
- [ ] Ephemeral/durable storage semantics are explicit.
- [ ] Failed revisions do not receive production traffic.
- [ ] Obsolete secret bindings are removed only after source verification.

## Rollback

Route traffic to the previous known-good revision and restore the previous secret bindings only if they are still required by that revision. Do not roll back application security fixes merely to satisfy stale deployment configuration.

## hmmm

- The current root container definition was not established by the audit source excerpt; Codex must inspect it before editing.
- Whether the frontend is served by the same Cloud Run service.
- The approved durable store for per-agent safetensors, FIQ audit, and traffic logs.
- Whether public unauthenticated ingress is intentional for the outer app while private routes enforce auth.

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
