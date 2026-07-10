# a0ucns repair handoffs

This package converts the source examination of `The-Interdependency/a0ucns` into self-contained Codex handoffs. Each numbered directory contains a file named exactly `repair.md`.

## Audit baseline

- Integration repository: `The-Interdependency/a0ucns`
- Audit head: `0ac2953ff5a12798ac054bfa1d41bb268b99e9b3`
- Mirrored application pin at audit: `The-Interdependency/a0-betatest@4f089d40455e6bca3fac682eeed5ff26694057e5`
- The application mirror is not authoritative. Re-resolve the current upstream `main` before editing.

The baseline identifies the code examined; it is **not** permission to edit the mirror. Codex must re-resolve current upstream heads and inspect current source before applying a handoff.

## Execution doctrine

- Application repairs land in `The-Interdependency/a0-betatest` first.
- Integration-document, mirror, and root-CI repairs land in `The-Interdependency/a0ucns`.
- After upstream repairs merge and pass, perform one reproducible re-mirror and advance `CONNECTIONS.md`.
- Current `The-Interdependency/skill-lib` applies to every build. Read the vendored current copies before implementation.
- Source modules own `CONTRACTS`; test modules own executable `CHECKS` under current test-build doctrine.
- Unknown facts remain `hmmm`.

## Recommended order

1. Complete P0 repairs 01–07. Repairs 01–03 and 04–06 can be parallelized carefully; Repair 07 feeds deployment configuration.
2. Land Repair 08 so all later changes are enforced by CI.
3. Reconcile deployment with Repair 09 only after P0 checks are green.
4. Update integration truth and mirroring through Repairs 10–11.
5. Correct research readouts with Repairs 12–15; these can run in parallel except where shared API snapshots require coordination.

## Handoff index

| ID | Priority | Repair | Primary target |
|---:|---|---|---|
| 01 | P0 — release blocker | [Eliminate cross-user leakage through the process-global inspector agent](01-shared-agent-state-privacy/repair.md) | `The-Interdependency/a0-betatest` |
| 02 | P0 — release blocker | [Make all agent CRUD derive ownership exclusively from authenticated identity](02-agent-owner-isolation/repair.md) | `The-Interdependency/a0-betatest` |
| 03 | P0 — release blocker | [Owner-scope pending override reads and restrict global expiration](03-override-record-authorization/repair.md) | `The-Interdependency/a0-betatest` |
| 04 | P0 — release blocker | [Namespace the in-process tool registry by owner and enforce ownership at dispatch](04-tenant-safe-tool-registry/repair.md) | `The-Interdependency/a0-betatest` |
| 05 | P0 — release blocker | [Apply one fail-closed SSRF and redirect boundary to all outbound connectors](05-outbound-ssrf-boundary/repair.md) | `The-Interdependency/a0-betatest` |
| 06 | P0 — release blocker | [Encrypt connector tokens and webhook secrets at rest with an idempotent migration](06-connector-secret-encryption/repair.md) | `The-Interdependency/a0-betatest` |
| 07 | P0 — release blocker for production authentication | [Harden cookies and GitHub OAuth redirect/state handling](07-session-oauth-hardening/repair.md) | `The-Interdependency/a0-betatest` |
| 08 | P1 — required before declaring repairs test-backed | [Add enforced root CI for the integration repo and full behavioral gates upstream](08-enforced-root-ci/repair.md) | both `The-Interdependency/a0-betatest` and `The-Interdependency/a0ucns` |
| 09 | P1 — production deploy blocker | [Reconcile Cloud Run configuration with the current FastAPI/Mongo application](09-deployment-contract/repair.md) | `The-Interdependency/a0-betatest` plus deployment environment configuration |
| 10 | P1 — architecture truth and safe handoff | [Reconcile CONNECTIONS.md with implemented coupling surfaces and evidence status](10-connections-status-truth/repair.md) | `The-Interdependency/a0ucns` |
| 11 | P1 — integration integrity | [Re-mirror authoritative heads reproducibly and fail CI on drift or forbidden material](11-mirror-sync-and-drift/repair.md) | `The-Interdependency/a0ucns` |
| 12 | P2 — research-readout correctness | [Use a circular mean for unit-circle phase readouts](12-circular-phase-mean/repair.md) | `The-Interdependency/a0-betatest` |
| 13 | P2 — research-readout truthfulness | [Make public-fixture carrier status reflect successful runtime validation](13-public-fixture-validation/repair.md) | `The-Interdependency/a0-betatest` |
| 14 | P2 — research-readout correctness | [Make EDCM applicability, polarity, and alert semantics metric-specific](14-edcm-metric-semantics/repair.md) | `The-Interdependency/a0-betatest` |
| 15 | P2 — structural correctness | [Reject incompatible phase embeddings instead of silently truncating composition](15-phase-compose-compatibility/repair.md) | `The-Interdependency/a0-betatest` |

## Cross-repair release gate

Do not describe the application as multi-user production-ready until all of the following are true:

- Repairs 01–07 have passing security checks.
- Repair 08 is enforced by branch protection.
- Repair 09 has a successful no-traffic/staging deploy smoke and rollback proof.
- Repair 11 confirms mirror/pin integrity and forbidden-material exclusion.

## Suggested branch/PR granularity

Use one upstream PR per P0 repair unless two repairs require the same atomic schema migration. Keep mirror updates separate from application implementation. A typical sequence is:

```text
a0-betatest: repair/<id>-<slug> -> tests -> merge
a0ucns:      chore/remirror-<upstream-sha> -> mirror checks -> merge
```

Do not push or open PRs unless the operator has requested publishing. A Codex run may prepare a clean local patch and final report first.

## Package integrity

`manifest.json` lists every handoff path. `SHA256SUMS` covers the Markdown handoffs and index so a later transfer can detect accidental mutation.

## hmmm

The exact ownership of deployed infrastructure, historical data retention, and external consumers was not established by source alone. Each repair preserves those unresolved constraints locally rather than converting them into assumptions.
