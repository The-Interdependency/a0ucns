# a0p — Architecture Reference

> This file contains the full file-by-file and component-level architecture detail.
> For the short overview, see `replit.md`. For contributor quickstart, see `CLAUDE.md`.

## Python Backend (`python/`)

- `python/main.py` — FastAPI app, mounts all routers, `/api/v1/ui/structure`, heartbeat lifespan
- `python/database.py` — Async SQLAlchemy (asyncpg), sync engine for migrations
- `python/models.py` — SQLAlchemy ORM models for all tables
- `python/engine/pcna.py` — PCNA six-ring engine (53-node topology)
- `python/logger.py` — JSONL append logger (core stream primitives + re-exports)
- `python/logger_ai.py` — AI-transcript and OpenAI-event helpers (split from logger.py per 400-line doctrine)
- `python/agents/zfae.py` — ZFAE agent definition, compose_name(), sub_agent_name()
- `python/services/energy_registry.py` — LLM provider registry (loads `python/config/providers.json`)
- `python/services/inference.py` — Dispatcher + orchestration; delegates outbound API calls to `providers/<name>.py`
- `python/services/providers/` — One file per provider:
  - `_resolver.py` — env > seed route_config > spec model lookup; raises on unresolvable
  - `openai_provider.py` — OpenAI Responses API + tool loop
  - `xai_provider.py` — xAI Grok via native xai-sdk (search + function-tool loop + streaming)
  - `gemini_provider.py` — google-genai SDK (thin wrapper over `gemini_native.py`)
  - `claude_provider.py` — Anthropic SDK + prompt caching
- `python/services/provider_seeds_bootstrap.py` — Lifespan-time idempotent seeding of provider WS modules
- `python/services/heartbeat.py` — Background heartbeat service (30s tick)
- `python/services/bandit.py` — Multi-Armed Bandit (UCB1) service
- `python/services/edcm.py` — EDCM behavioral directives scoring
- `python/services/research.py` — Autonomous research (GitHub, AI social search)
- `python/services/agent_lifecycle.py` — Sub-agent PCNA fork/merge math
- `python/services/spawn_executor.py` — Background poller: atomic claim (UPDATE … FOR UPDATE SKIP LOCKED), PCNA fork→infer→absorb cycle, rich `merge` event logging
- `python/services/zeta_observe.py` — ZFAE observation service
- `python/storage/core.py` — Core CRUD storage (raw SQL via asyncpg)
- `python/storage/domain.py` — Domain-specific storage (heartbeat, memory, PCNA, bandits)

## Route Modules (`python/routes/`)

Each declares `UI_META` (tab config) + `DATA_SCHEMA` (field specs). Registration requires 4 edits to `python/routes/__init__.py`.

- `chat.py` — Conversations and messages
- `agents.py` — Agent listing, sub-agent spawn/merge
- `memory.py` — Memory seeds, projections, tensor snapshots
- `edcm.py` — EDCM metrics and snapshots
- `bandits.py` — Bandit arms and rewards
- `system.py` — System toggles, events, cost metrics, build-info, docs endpoint
- `tools.py` — Custom tools CRUD
- `heartbeat_api.py` — Heartbeat tasks and logs
- `pcna_api.py` — PCNA state and propagation
- `billing.py` — Stripe billing: status, donations, portal, webhook
- `contexts.py` — Prompt contexts CRUD (admin-only write)
- `forge.py` + `forge_archetypes.py` — Character-sheet agent creation

## Frontend (`client/`)

React + Vite + TypeScript, Tailwind CSS, shadcn/ui. Fully metadata-driven console.

- `client/src/hooks/use-ui-structure.ts` — polls GET /api/v1/ui/structure, returns tab tree
- `client/src/components/FieldRenderer.tsx` — field.type → visual (gauge, text, badge, list, timeline, sparkline, json)
- `client/src/components/TabRenderer.tsx` — fetches tab.endpoint, renders fields via FieldRenderer
- `client/src/components/TabShell.tsx` — tab chrome: header, refresh, error boundary
- `client/src/components/console-sidebar.tsx` — navigation from the tab tree
- `client/src/pages/console.tsx` — `CUSTOM_TAB_RENDERERS` map; falls back to `TabRenderer` for schema-driven tabs
- `client/src/pages/chat.tsx` — chat shell with conversation list + message bubbles
- `client/src/components/top-nav.tsx` — nav + agent name + tier badge + skin/theme selector + last-updated widget (ws/admin)
- `client/src/hooks/use-billing-status.ts` — fetches /api/v1/billing/status, exposes tier, isAdmin, isWs
- `client/src/pages/pricing.tsx` — Donations-only support page
- `client/src/pages/docs.tsx` — Markdown viewer for replit.md / CLAUDE.md / copilot.md / README.md
- `client/src/pages/admin-contexts.tsx` — Admin-only prompt context editor

### Console-Tab Regression Guards
- `tests/e2e/console-tabs.spec.ts` — Playwright e2e: logs in, opens every tab, asserts `data-renderer` is never `missing`
- `scripts/check-console-tabs.mjs` — static preflight: parses `CUSTOM_TAB_RENDERERS`, fetches `/api/v1/ui/structure`, fails on uncovered tabs. Run: `node scripts/check-console-tabs.mjs`
- CI: `check-console-tabs` job in `.github/workflows/deploy.yml` and `cloudbuild.yaml` blocks deploy on failure

## Cognitive Engine Stack

### PCNA Engine (`python/engine/pcna.py`)
53-node circular topology with six rings:

| Ring | N | Seed | Role |
|------|---|------|------|
| Phi | 53 | 53 | cognitive substrate |
| Psi | 53 | 43 | self-model |
| Omega | 53 | 47 | autonomy |
| Theta | 29 | — | microkernel gate |
| Memory-L | 19 | 19 | long-term (prime-seed LT) |
| Memory-S | 17 | 17 | short-term (prime-seed ST) |

Six inference steps: Project → Inject → Propagate → PTCA-seed → PTCA-circle → Coherence.

### Prime-Seed PTCA Layer (`python/engine/prime_seeds.py`)
7 independent PTCACore instances (N=3,5,7,11,13,17,19) seeded from sigma tensor slices at boot.

- **Tick** (60s heartbeat task `prime_seeds_tick`): all 7 propagate 5 steps; N=17→memory_s unconditionally; N=19→memory_l when zeta bandit `"lt_promote"` arm decides (coherence_edge + positive avg_reward or first-explore)
- **Persistence**: N=19 (LT) tensor serialized to DB key `prime_seed_lt_v1` on every promotion; restored at startup via `load_lt_checkpoint()`. N=17 (ST) is volatile — regenerates from sigma on each boot.
- **Bandit domain `"prime_seeds"`**: arms `"tick_active"` (rewarded with avg coherence) and `"lt_promote"` (rewarded with LT coherence on promotion)
- **Prompt injection** (via `inference.py:_prepend_doctrine`):
  - LT tag → stable prefix block, after skill manifest, before system_prompt
  - ST tag → spliced into system_prompt after `## Memory\n` marker (volatile block)
  - Format: `[memory:LT N=19 coherence=X hub=Y mean=Z]` / `[memory:ST N=17 ...]`
  - Fail-safe: `_prime_seed_context_lines()` returns `("","")` on any error

### Prompt Caching Strategy
System prompts composed in **stable→volatile** order:
```
1. a0_identity / doctrine    ← global, immutable
2. skill manifest            ← changes only on skill edit
3. LT prime-seed tag         ← changes only on LT promotion
4. system_prompt (identity + base + tier + persona)
   └── ## Memory\n
       ST prime-seed tag     ← refreshed every 60s tick
       memory seeds          ← user edits
```

Anthropic gets two cache breakpoints (before/after `## Memory`). OpenAI/Grok auto-cache on stable prefixes ≥1024 tokens.

| Provider | Cache read | Cache write |
|----------|-----------|-------------|
| openai (gpt-5-mini) | 10% input | n/a (auto) |
| claude sonnet 4.5 | 10% input | 125% input |
| grok 4 fast | 25% input | n/a (auto) |
| gemini 2.5 flash | not wired | requires cachedContents API |

## The Forge

Character-sheet agent creation. `python/routes/forge.py` + `forge_archetypes.py` + `client/src/components/ForgeTab.tsx`.

- 8 archetypes (Sage, Trickster, Paladin, Druid, Engineer, Diplomat, Hacker, Captain)
- Personality: D&D alignment, traits, verbosity 1–10
- Stats: D20 6-stat block (reasoning/speed/resilience/creativity/memory/charisma)
- Self-updating registries: `GET /api/v1/forge/tools` introspects `TOOL_SCHEMAS_CHAT`; `GET /api/v1/forge/models` introspects `energy_registry`
- Per-user namespace: `(owner_id, name)` uniqueness, 409 on collision

**RPG/Combat — STUBBED (DB only):** `agent_instances` has level/xp/hp/wins/losses columns; `agent_matches` table exists. `POST /api/v1/forge/duel` returns 501. Schema locked.

## Explainer Pricing (LOCKED)

- 3 free explanations per user, lifetime (seeded on first read of `/api/v1/transcripts/explainer/credits`)
- $50 = pack of 3 explanations (~$16.67 each)
- Decrement order: free first, then paid
- Stripe Checkout (embedded) via `POST /api/v1/billing/explainer-checkout`
- `checkout.session.completed` webhook calls `storage.add_explanation_credits(uid, packs)` — amount re-derived from `amount_total` to defeat metadata tampering
- `charge.refunded` reverses paid credits (rounded down by $50 increments)
- One explanation per report (UNIQUE on `transcript_explanations.report_id`)
- Model: `openai-5.5` (gpt-5.5). Strict-JSON output (body + citations); citation integrity verified (substring match); fabricated quotes dropped; parse failure refunds credit
- Frontend: `client/src/components/ExplainerCard.tsx` in `client/src/pages/transcripts.tsx`

## Key Concepts

- **UI_META + DATA_SCHEMA**: Every route module declares both; `collect_ui_meta()` aggregates; `/api/v1/ui/structure` serves; frontend has zero hardcoded tabs
- **Heartbeat**: 30s tick — audit, snapshot, propagate, research, prime-seeds
- **Bandits**: UCB1 + EMA decay across tool, model, routing, prime-seeds domains
- **EDCM**: Behavioral directive scoring (CM, DA, DRIFT, DVG, INT, TBF)
- **Sub-agent lifecycle**: fork() at spawn → absorb() on completion → retired
- **Sigma**: filesystem tensor (401 nodes) — encodes workspace structure; seeds prime-seed cores at boot
