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

License note: this repo is AGPL-3.0-or-later; the mirrored trees retain their own
licenses (a0-betatest: Apache-2.0; aimmh: MPL-2.0; odysseus-a0: per its LICENSE).
