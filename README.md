# a0ucns — deprecated A0 work

**Deprecated at the owner's request. Retained for historical inspection and reproducibility.** New A0 development and deployment are retired; no replacement A0 runtime is declared.

## Preserved source

The existing archival change moved the complete previous source tree under [archive/](archive/) without changing its contents. This notice leaves that tree intact.

| Evidence | Exact identity |
| --- | --- |
| Source commit before relocation | `6713005c98d8860b9bd50bdd6ec59150b3572545` |
| Preserved source / archive tree | `62a7f21bd1b36912a25b9fdc1b790f6798bac0b8` |
| Archival relocation commit | `09e6b2ddc5938aa0f0eda296a37db5032fb0062b` |
| Preserved tracked files | 3319 |

This is the historical A0 integration workspace, including an earlier A0 copy and provenance-bearing mirrors of a0-betatest, AIMMH, and Odysseus. See [the preserved connection record](archive/CONNECTIONS.md). Those upstream projects retain their own authority and licenses. This notice does not retire the independent UCNS, AIMMH, or Odysseus repositories.

## Usage

Read [the historical README](archive/README.md) as historical documentation. Preserve the licenses and notices within each source tree. For exact historical analysis, check out the source commit above into an isolated worktree; do not use the old deployment or startup instructions against a live environment.

Verify preservation from a fetched clone:

```sh
git rev-parse 6713005c98d8860b9bd50bdd6ec59150b3572545^{tree}
git rev-parse HEAD:archive
```

Both results must equal the preserved tree identity above. Existing commit-pinned references remain historical source references; current-branch consumers must use the preserved path or an explicitly chosen historical commit.

## Retirement boundary

A source archive, GitHub's read-only repository archive flag, and hosted runtime shutdown are separate states. This documentation records source preservation and deprecation only. Database contents, runtime uploads, private checkpoints, credentials, and hosted configuration are outside the tracked-source preservation claim. Keep independent research repositories, shared hosts, and their dependencies intact.

**hmmm:** GitHub archive-flag verification and provider-level runtime/data-retention receipts must be recorded separately before complete operational retirement is claimed.
