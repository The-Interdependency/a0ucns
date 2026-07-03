# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## What this repo is

`a0ucns` is the agent-platform codebase for **a0** — the runtime/project — whose deployed public instance is **a0p** (a research instrument at `replit.interdependentway.org`). It is a 3-process autonomous AI agent platform with a metadata-driven console UI.

- **Languages:** TypeScript (Express server + React/Vite client) and Python 3.12 (FastAPI backend + cognitive engine).
- **Key deps:** FastAPI, uvicorn, SQLAlchemy (async) + Drizzle ORM, React 18 + Vite, Stripe, and the private engine packages `pcea` (git), `aimmh-lib`, `edcmbone`. LLM SDKs: `anthropic`, `openai`/`openai-agents`, `google-genai`, `xai-sdk`.
- **License:** AGPL-3.0-or-later — consistent across `package.json`, Python `pyproject.toml`, and the `LICENSE` file (relicensed from MIT; network copyleft so any hosted fork must publish source). Vendored `skill-lib/` retains its upstream MPL-2.0 license.

> **Naming:** `a0` = the project / runtime / repository. `a0p` = the deployed instance (used in user-facing UI copy and billing).

### Relationship to `a0` and `ucns`

- **`a0`** (sibling repo `/home/user/a0`) is the canonical platform repo. This `a0ucns` tree is a near-identical copy of it — same 3-process platform, same engine stack — so platform conventions documented here mirror `a0`.
- **`ucns`** (sibling repo `/home/user/ucns`) is an unrelated research-stage Python package: the Unit Circle Number System (recursive factorization theory). It is **not** vendored or imported by this codebase; do not conflate the math library with this agent platform.

---

## Commands

```bash
# Development — starts all 3 processes (Python/FastAPI :8001, Vite :5001, Express :5000)
bash scripts/start-dev.sh

# Production build (Vite → dist/public/, esbuild → dist/index.cjs)
npm run build            # = tsx script/build.ts

# Run the production build (Express only — dist/index.cjs on :5000)
npm start                # = NODE_ENV=production node dist/index.cjs

# Run both production processes (Express :5000 + uvicorn :8001) — what the container uses
bash scripts/start-prod.sh

# TypeScript type checking
npm run check            # = tsc

# Push Drizzle schema to PostgreSQL
npm run db:push          # = drizzle-kit push

# Re-stamp all files with N:M ratio annotation (required after edits)
python scripts/annotate.py [file ...]
```

`scripts/start-dev.sh` generates an ephemeral shared `INTERNAL_API_SECRET` for the dev session if one is not already exported, and clears stale processes on ports 5000/5001/5002/8001 before boot.

### Tests

```bash
# Python smoke + unit tests (auto-skips live-server suite if :5000 is down)
uv run pytest tests/ -v
uv run pytest tests/ -v --ignore=tests/test_live_server.py    # offline only

# Server-free gating contract tests (static AST scanners) — what CI runs
python -m pytest python/tests/contracts/route_gating.py python/tests/contracts/gating.py -v

# Playwright e2e (requires dev server on :5000)
npx playwright install chromium        # first time only
npx playwright test                    # testDir = tests/e2e
npx playwright test tests/e2e/console-tabs.spec.ts

# Console-tab regression guard (needs a running backend; uses API_BASE)
API_BASE=http://localhost:5000 node scripts/check-console-tabs.mjs

# Static website pages smoke test
node --test tests/website-smoke.mjs
```

`run_tests.py` is a pytest wrapper that pre-caches stdlib `logging` (the local `a0/logging.py` would otherwise shadow it). Caveat: it hardcodes the stdlib path `/usr/lib/python3.11/logging/__init__.py`, so it is brittle on non-3.11 hosts even though the repo otherwise targets Python 3.12.

---

## CI

Three workflows in `.github/workflows/`:

| Workflow | What it does |
|----------|--------------|
| `ci.yml` | `npm run check` (Node type check) + server-free gating contract tests (`python/tests/contracts/`). Runs on push to `main` and all PRs. |
| `clean-build-check.yml` | Builds without `REPL_ID` and fails if any `@replit` reference leaks into the client bundle; runs `tests/website-smoke.mjs`. |
| `deploy.yml` | Console-tab regression guard (boots Python backend against an ephemeral Postgres, runs `scripts/check-console-tabs.mjs`), then builds the Docker image and deploys to Cloud Run (`a0p`, region `us-central1`) on push to `main`. |

---

## Architecture

```
Browser → Express (:5000) → [proxy /api/*] → Python/FastAPI (:8001, internal only)
                         ↘ [dev] Vite (:5001)
```

- **Express** (`server/`) — Auth, sessions, guest-chat rate limiting, static serving. The only public entry point; adds `x-a0p-internal: <INTERNAL_API_SECRET>` and identity headers (`x-user-id`, `x-user-email`, `x-user-role`) to every proxied request. Never expose the Python port directly. Entry: `server/index.ts`.
- **Python/FastAPI** (`python/`) — All AI orchestration, the cognitive engine stack, agent lifecycle, billing, heartbeat scheduler. Validates `x-a0p-internal` on every request. App: `python.main:app`.
- **Vite** — Dev only; proxied by Express.

### The agent

ZFAE (`a0(zeta fun alpha echo)`) is the single persistent agent. LLMs (Grok 4 Fast, GPT-5 mini, Gemini 2.5 Flash, Claude Sonnet 4.5) are treated as **energy providers** — they supply compute per response but are not the agent. Sub-agents (`a0(zeta{n})`) fork the PCNA instance, run in parallel, and merge results back.

### Cognitive engine stack (`python/engine/`)

| Component | File | Role |
|-----------|------|------|
| **PCNA** | `pcna.py` | Six-ring inference pipeline (Φ/Ψ/Ω/Θ/Memory-L/Memory-S); steps: Project → Inject → Propagate → PTCA-seed → PTCA-circle → Coherence |
| **PTCA** | `ptca_core.py` | Prime-ring tensor context, shape `[N, 4, 7, 7]` (node/dim/phase/heptagram) |
| **Sigma** | `sigma.py` | Encodes the workspace filesystem as a prime-ring tensor; companion to the Ψ ring; has its own console tab |
| **Theta** | `theta.py` | Θ ring |
| **Zeta** | `zeta.py` | Memory injection layer (LT→prompt cache, ST→after cache, sub-agent→volatile) |
| **Memory / Merge / Registry** | `memory_core.py`, `merge.py`, `module_registry.py`, `prime_seeds.py` | Memory checkpointing, sub-agent merge, module + seed registries |

### Key Python services (`python/services/`)

- `inference.py` / `inference_modes.py` — Orchestrate LLM calls across registered energy providers; inject tier-specific `prompt_context`.
- `heartbeat.py` — 30-second tick: audit snapshots, memory checkpoints, PCNA propagation, sub-agent cleanup.
- `tool_executor.py` — Tool invocation with approval gates.
- `edcm.py` — Behavioral directive scoring (CM, DA, DRIFT, DVG, INT, TBF); fires corrective actions and guides LLM selection.
- `bandit.py` — UCB1 multi-armed bandit for tool / model / routing selection.
- `agent_instance.py`, `agent_lifecycle.py`, `spawn_executor.py`, `swarm.py` — Agent and sub-agent lifecycle.
- `stripe_service.py`, `edcmbone_explainer.py` — Billing/donations and the paid transcript explainer.

### Frontend (metadata-driven console)

`client/src/hooks/use-ui-structure.ts` polls `GET /api/v1/ui/structure`, which aggregates `UI_META` from every Python route module. `client/src/pages/console.tsx` renders tabs from this structure:

- Tabs in `CUSTOM_TAB_RENDERERS` → custom React component.
- All others → generic `TabRenderer` (schema-driven via `DATA_SCHEMA`).

The console-tab regression guard (`scripts/check-console-tabs.mjs`) and e2e test (`tests/e2e/console-tabs.spec.ts`) enforce that every API-declared tab has either a custom renderer or sections. CI (`deploy.yml`) blocks deploy on failure.

### Python route modules (`python/routes/`)

Each route file is self-declaring: it exports a FastAPI `router` and defines `UI_META`/`DATA_SCHEMA` plus `# DOC ...` headers. **Adding a new route requires editing `python/routes/__init__.py`:**

1. Import the router.
2. Add it to `ALL_ROUTERS`.
3. Add the module name to the `modules` list in `collect_ui_meta()`.
4. Add the file to the list in `collect_doc_meta()`.

Naming: `{name}.py` = self-contained module; `{name}_api.py` = thin delegate to a service in `python/services/`.

### Database

Schema source of truth is `shared/schema.ts` (Drizzle ORM), applied via `npm run db:push`. Python accesses the same PostgreSQL DB via SQLAlchemy async (`python/database.py`, `python/models.py`).

### Auth & tiers

Auth is handled entirely by Express (`server/auth/`). On login/signup it fires a non-fatal call to the Python internal endpoint `POST /api/v1/billing/internal/promote-ws` (`tryPromoteWs` in `server/auth/routes.ts`), which promotes `@interdependentway.org` accounts to the operator (`ws`) tier. Owner-only ("admin") write endpoints govern mutations to shared instrument state; per-user CRUD is not admin-gated. The static gating contract lives in `python/tests/contracts/gating.py` / `route_gating.py`.

### Standalone `a0` CLI package

The top-level `a0/` package (with `a0python/`, `requirements.txt`, `run.sh`) is a separate terminal client/runtime (`python -m a0.a0`, adapters in `a0/adapters/`) distinct from the `python/` FastAPI backend. `scripts/a0-cli.sh` is the shell client that talks to the deployed platform using an `A0_KEY` generated from the Console → CLI Keys tab.

### Skills system

`.agents/skills/` holds agent-specific skill definitions (`SKILL.md` per skill). `skills/` + `skills-lock.json` implement a plugin-style skill registry. Consult `.agents/skills/a0p-module-doctrine/SKILL.md` and `.agents/skills/a0p-self-declaring-modules/SKILL.md` for authoritative module conventions before adding route modules.

---

## Conventions

- **File annotation** — Every file opens/closes with `// N:M` or `# N:M` (code:comment ratio). Run `python scripts/annotate.py` after edits.
- **Python route DOC blocks** — Each route file includes `# DOC module:`, `# DOC label:`, `# DOC description:`, `# DOC tier:`, `# DOC endpoint:` headers.
- **No file over 400 lines** — Keep modules under this limit; `scripts/annotate.py` warns when exceeded (CI does not block on this rule).
- **All frontend `/api/*` calls go through Express on :5000** — never call Python :8001 directly.
- **Dynamic SQL UPDATE** — use the column-allowlist pattern already established in the codebase.
- **Clean build** — keep `@replit` packages out of the client bundle (`clean-build-check.yml` enforces this).
- **Unknown fields** — when building a `MODULE_BUILD` block, mark unknowns `hmmm`; do not guess.

---

## Key files

| File | Purpose |
|------|---------|
| `replit.md` | Platform overview and user preferences |
| `DEPLOYMENT.md` | GCP / Cloud Run setup and secrets |
| `spec.md` | Full agent platform spec (PCNA, EDCM, sentinel channels) |
| `script/build.ts` | Production build orchestrator (Vite + esbuild) |
| `python/main.py` | FastAPI app entry (`python.main:app`) |
| `python/routes/__init__.py` | Module registration (edit when adding routes) |
| `client/src/pages/console.tsx` | `CUSTOM_TAB_RENDERERS` map and tab rendering logic |
| `.agents/skills/a0p-module-doctrine/SKILL.md` | Authoritative module conventions |
| `.github/workflows/deploy.yml` | CI deploy pipeline (regression guard → Cloud Run) |

---

## Environment variables

Required in production (dev has safe fallbacks except where noted). Note: `.env.example` only covers model selection + LLM/adapter keys (`A0_MODEL`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, `GROK_API_KEY`, `DEEPSEEK_API_KEY`, `GITHUB_TOKEN`, Google Cloud) — it does **not** list the core platform vars below (`SESSION_SECRET`, `INTERNAL_API_SECRET`, `DATABASE_URL`, `XAI_API_KEY`, Stripe secrets), which must be set separately.

| Variable | Purpose |
|----------|---------|
| `SESSION_SECRET` | Express session encryption (no fallback in prod) |
| `INTERNAL_API_SECRET` | Express→Python shared secret (auto-generated by `start-dev.sh` in dev) |
| `DATABASE_URL` | PostgreSQL connection string |
| `XAI_API_KEY` | Grok (primary energy provider) |
| `ANTHROPIC_API_KEY` | Claude |
| `GEMINI_API_KEY` | Gemini |
| `OPENAI_API_KEY` | GPT / OpenAI agents |
| `STRIPE_SECRET_KEY` | Stripe (donations + EDCMbone explainer) |
| `STRIPE_PUBLISHABLE_KEY` | Stripe embedded checkout |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook HMAC validation |
| `ADMIN_USER_ID` / `ADMIN_EMAIL` | Seed admin access |

---

## Git workflow

- Main branch: `main`.
- Feature branches: `feat/<description>`, `fix/<description>`, `docs/<description>`, `chore/<description>` (e.g., `claude/add-feature-abc`).
- Commit style: Conventional Commits (`feat(console):`, `fix(pcna):`, etc.).
- Do not commit secrets, tokens, private keys, or credentials.

## Agent module-build doctrine

Before adding a new module, route, service, adapter, schema, worker, engine, UI panel, migration, or experiment, read:

`./.agents/skills/meta-module-build/SKILL.md`

New module work should start with a `MODULE_BUILD` block. Unknown fields must be marked `hmmm`, not guessed.
