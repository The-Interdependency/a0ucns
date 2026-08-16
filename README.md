# a0ucns

Status: **DEPRECATED as a verbatim-mirror and current coupling authority**.

The 2026-08-16 exact-tree audit falsified the claim that the embedded
`a0-betatest/`, `aimmh/`, and `odysseus-a0/` trees are verbatim copies of the
commits named in `CONNECTIONS.md`. The first comparison alone found one missing
tracked blob, one target-only blob, and six changed blobs outside the declared
directory exclusions; testing then stopped.

Use the three upstream repositories at exact commits as source authorities.
This repository remains historical integration design and does not transfer
current implementation, security, or evidence status.

## Replacement

- `The-Interdependency/a0-betatest`
- `The-Interdependency/aimmh`
- `The-Interdependency/odysseus-a0`

Resolve each at an explicit commit. Do not use the embedded trees as mirrors.

## hmmm

The modified snapshots have no machine-readable divergence manifest. Until one
exists, they are historical working copies, not reproducible integration input.
