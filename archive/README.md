# a0ucns — integration workspace

This repository was restructured on 2026-07-03:

- **`archive/`** — the complete previous contents of a0ucns (the a0 platform
  copy), moved intact. Nothing was deleted; git history is preserved as renames.
- **`a0-betatest/`**, **`aimmh/`**, **`odysseus-a0/`** — verbatim mirrors of the
  corresponding The-Interdependency repos (tracked files only; source commits and
  exclusions listed in `CONNECTIONS.md`). They are working copies for integration
  design — the source of truth stays upstream.
- **`CONNECTIONS.md`** — the connection scheme: every seam where aimmh or
  odysseus-a0 couples with a0-betatest (a0p), what exists vs. what needs writing,
  a decision matrix, and the boundary rules. **Start there.**

Quick summary of the scheme (details in `CONNECTIONS.md`):

| # | Coupling | Direction | Status |
|---|---|---|---|
| A | `aimmh_lib` CallFn adapter over a0p `ProviderAdapter.chat` | aimmh → a0p, in-process | ~40-line adapter to write |
| B | aimmh hub HTTP API (`/api/v1/hub/*`) | aimmh → a0p, HTTP | optional, heavier |
| C | odysseus MCP servers via a0p `mcp_relay` + tool registry | odysseus → a0p | registration only |
| D | odysseus REST via scoped API tokens as a0p webhook tools | odysseus → a0p | thin tool defs |
| E | a0p as OpenAI-compatible model endpoint in odysseus | a0p → odysseus | shim to write in a0p |

## License

a0ucns's own content is licensed under the GNU Affero General Public License v3.0
or later (SPDX: `AGPL-3.0-or-later`). The full text is in [`LICENSE`](LICENSE). This
covers the root files, `archive/`, `docs/` and `repairs/`, except the carve-outs
below and the mirrored trees listed further down. The root file is
byte-identical to `archive/LICENSE`, the AGPL text a0ucns inherited from its fork
parent The-Interdependency/a0, which was at the repo root until the 2026-07-03
restructure moved it into `archive/`.

Carve-outs: any file or directory that carries its own LICENSE file or a manifest
license declaration keeps those terms, in the same way `skill-lib/ATTRIBUTION.md`
keeps imported skills under their upstream license. Known carve-outs inside
`archive/`:

| Path | Own terms |
|---|---|
| `archive/.agents/skills/frontend-design/` | Apache-2.0 (`LICENSE.txt`, from anthropics/skills) |
| `archive/.agents/skills/skill-creator/` | Apache-2.0 (`LICENSE.txt`, from anthropics/skills) |
| other third-party skills under `archive/.agents/skills/` listed in `archive/skills-lock.json` (inf-sh, squirrelscan, better-auth, obra/superpowers, browser-use, vercel-labs, nextlevelbuilder) | their upstream terms; several upstreams show no repo-level license (`hmmm`) |
| `archive/skill-lib/` | MPL-2.0 (`archive/skill-lib/LICENSE`) |
| `archive/.agents/skills/msdmd/`, `archive/.agents/skills/meta-module-build/`, `archive/.agents/skills/test-build/` (earlier copies of Erin's own The-Interdependency/skill-lib skills, per `archive/.agents/skills/README.md`) | MPL-2.0 (earlier copies were also published under Apache-2.0; that grant stands) |
| `archive/edcm-org/` | MIT (`archive/edcm-org/pyproject.toml`) |
| `archive/a0python/edcm-org/` | MIT (`archive/a0python/edcm-org/pyproject.toml`) |

Inherited terms are preserved. `archive/` carries a0 history from the fork point.
Versions published at earlier commits keep the terms they were published under:
`package.json` `"license": "MIT"` from 2026-02-26, Apache-2.0 LICENSE from
2026-05-01, an interim BSL notice from 2026-05-26, MIT
from 2026-06-07, and AGPL-3.0 from 2026-06-12. `archive/package.json` and
`archive/pyproject.toml` declare `AGPL-3.0-or-later`.

The mirrored trees keep their own licenses:

| Tree | License |
|---|---|
| `aimmh/` | MPL-2.0 (`aimmh/LICENSE`) |
| `odysseus-a0/` | MIT (`odysseus-a0/LICENSE`, Copyright (c) 2025 Odysseus Contributors) |
| `a0-betatest/` | Mirrored at `4f089d4` (2026-07-09). At that commit a0-betatest had **no root LICENSE**. `backend/pyproject.toml` declared `Apache-2.0` and `_legacy_a0/LICENSE` is an unfinished interim BSL placeholder, not a license. Upstream a0-betatest added its AGPL-3.0-or-later `LICENSE` on 2026-07-10 (`47acbc3`), after this mirror was taken. Re-mirroring would bring it in. |

Usage: to reuse code from this repo, take the license of the tree it lives in, as
listed above. This section is a licensing map, not legal advice.
