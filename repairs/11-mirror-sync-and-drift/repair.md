# Repair 11 — Re-mirror authoritative heads reproducibly and fail CI on drift or forbidden material

**Codex handoff:** implementation-ready  
**Priority:** P1 — integration integrity  
**Primary target:** `The-Interdependency/a0ucns`  
**Dependencies:** run after each upstream repair merge; coordinates with Repair 08

## Mission

Replace manual mirror refreshes with a reproducible pin, check, and re-mirror process. Synchronize approved upstream commits without importing excluded or non-committable artifacts.

## Audit baseline

- Integration repository: `The-Interdependency/a0ucns`
- Audit head: `0ac2953ff5a12798ac054bfa1d41bb268b99e9b3`
- Mirrored application pin at audit: `The-Interdependency/a0-betatest@4f089d40455e6bca3fac682eeed5ff26694057e5`
- The mirrors are working copies. Their upstream repositories remain authoritative.

## Source evidence to confirm on current `main`

- `CONNECTIONS.md` records exact mirror pins and the upstream-first rule.
- At audit time, `a0-betatest` and `aimmh` had advanced beyond their recorded mirror pins.
- `storage/agents/` and `_legacy_a0/uploads/` are excluded and represented by marker files.
- Existing refresh history records careful manual checks, but no root-enforced deterministic mirror tool was established.

## Required invariants

- Each mirror matches all tracked files at its recorded full commit SHA, except for a small reviewed exclusion manifest.
- Excluded paths, generated caches, nested repository metadata, checkpoints, upload data, and other non-committable artifacts do not enter the integration tree.
- Every exclusion has a reason, owner, and required marker file.
- Mirror contents and the corresponding pin advance atomically in one reviewable change.
- The checker distinguishes an upstream repository advancing from a mirror differing from its recorded pin.
- Running the same re-mirror command twice at the same pins produces no second diff.

## Non-goals

- Do not fix application defects directly in a mirrored directory.
- Do not advance pins or merge refreshed mirrors without review.
- Do not record branch names as pins; use full commit SHAs.

## Proposed file plan

| Path | Change | Purpose | Risk | Required tests |
|---|---|---|---|---|
| `scripts/remirror.py` | create | deterministic tracked-file staging and replacement | high | fixture and idempotency tests |
| `scripts/check_mirrors.py` | create | compare mirrors with recorded pins and report upstream advancement | high | negative fixtures |
| `mirror-exclusions.yml` | create | machine-readable reviewed exclusions | high | schema checks |
| `CONNECTIONS.md` | modify | advance pins and document the process | medium | connection checker |
| mirrored trees | update | synchronize approved tracked files | high | forbidden-material scan |
| root workflow | modify through Repair 08 | enforce the checker | high | CI |
| `tests/test_mirror_tools.py` | create | executable evidence for the tools | medium | CHECKS declarations where applicable |

## Implementation sequence

1. Resolve the current default-branch head of each upstream repository at execution time. Record the selected full SHAs before staging.
2. Create an exclusion manifest with exact paths or narrowly bounded patterns, reason, owner, and required marker. An unresolved exclusion is `hmmm` and fails strict mode.
3. Build each expected mirror from a tracked-file archive for the selected commit, not from a developer working directory.
4. Stage into a temporary directory, apply reviewed exclusions, verify marker files, then replace the mirror atomically.
5. Validate the staged tree before replacement:
   - paths remain inside the staging root;
   - no nested repository metadata exists;
   - excluded roots contain only their approved markers;
   - no declared checkpoint or upload artifact is present;
   - no extra path exists beyond tracked files and approved markers.
6. Update the pin table from the selected SHAs and commit dates without rewriting unrelated integration narrative.
7. Make `check_mirrors.py` reconstruct expected path sets and byte hashes at the recorded pins. Report newer upstream heads separately; never silently change the pins.
8. Add tests for idempotency, malformed archives, unexpected extra files, missing marker files, one-byte drift, and pin/tree mismatch.
9. Re-mirror only after upstream repair PRs merge and pass. Keep unrelated upstream batches separate.

## Source-owned contracts to add or revise

```text
mirror_matches_recorded_upstream_pin
  given: a mirror directory and its recorded upstream commit
  then: every non-excluded tracked path and byte hash matches, and no unexpected path exists
  class: integrity

remirror_is_idempotent
  given: identical pins and exclusion manifest
  then: two runs produce identical trees and the second run has no diff
  class: idempotency

mirror_exclusions_are_enforced
  given: staged input containing an excluded or non-committable artifact
  then: strict staging refuses it or removes the exact reviewed exclusion and verifies its marker
  class: security

mirror_pin_and_tree_advance_together
  given: a pin update without matching contents or contents without a matching pin
  then: strict checking fails
  class: integrity
```

## Test-owned checks

- Synthetic upstream fixture containing tracked files, excluded paths, unexpected extras, unsafe relative paths, links, and declared non-committable file types.
- Run re-mirror twice and compare complete path and hash inventories.
- Change one mirrored byte and one recorded pin; assert distinct failures.
- Validate the real mirrors at their recorded pins.
- Confirm required markers exist and excluded roots contain nothing else.
- Report upstream advancement without mutating the integration tree.

## Validation commands

```bash
cd a0ucns
python scripts/check_mirrors.py --strict
python scripts/remirror.py --check --all
pytest -q tests/test_mirror_tools.py
```

Run the actual refresh in a clean worktree and inspect the complete path-level diff before committing.

## Acceptance criteria

- [ ] Re-mirror and check commands are deterministic and test-backed.
- [ ] Pins and trees agree exactly modulo reviewed exclusions.
- [ ] Approved current upstream commits are mirrored.
- [ ] Excluded and non-committable artifacts are absent; markers are verified.
- [ ] Root CI enforces mirror integrity.
- [ ] Re-running at identical pins yields no diff.

## Rollback

Revert a pin and its mirror tree together to the previous known-good pair. Never revert only `CONNECTIONS.md` or only the mirrored files. Keep exclusion rules at least as strict during rollback.

## hmmm

- Whether “upstream has advanced” should fail every pull request or create a scheduled report. A mismatch with the recorded pin must always fail.
- The complete organization-wide inventory of excluded artifact types beyond those already declared.
- Whether tracked symbolic links are permitted; reject them until an explicit rule and tests exist.

## Operating rules

1. **Edit upstream first.** Application changes belong in `The-Interdependency/a0-betatest`. After an upstream PR merges and passes, re-mirror its tracked files and advance `CONNECTIONS.md`.
2. **Read the current vendored skills before changing the process:**
   - `.agents/skills/msdmd/SKILL.md`
   - `.agents/skills/meta-module-build/SKILL.md`
   - `.agents/skills/risk-boundary-build/SKILL.md`
   - `.agents/skills/test-build/SKILL.md`
   - `.agents/skills/canon/SKILL.md`
3. Update affected metadata and evidence declarations in the same patch.
4. Source modules own `CONTRACTS`; test modules own executable `CHECKS` under the current vendored doctrine.
5. Preserve unresolved facts as `hmmm`.
6. Keep the refresh independently reviewable and reversible.
7. Report exact commands and results; import success alone is not completion.

## Required final report from Codex

Return:

- selected upstream SHAs and why;
- files added, removed, and changed by mirror;
- exclusions and markers verified;
- contracts and checks added;
- commands run with pass/fail results;
- remaining `hmmm` items;
- the exact integration commit or PR created.
