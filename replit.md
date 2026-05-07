# a0p — a research instrument

## Identity
**a0p is a research instrument, not a product.** It is the deployed instance of `a0` (this codebase / repository) running publicly. It explores agent / energy-provider / PCNA dynamics in the open. Anyone may read and use it. Code-altering access is restricted to the owner (Erin) and a small set of explicitly-invited collaborators. The instrument is funded by donations; it does not solicit subscribers.

> Naming: `a0` = the project / runtime / repository. `a0p` = the deployed instance (used in user-facing UI copy, billing, splash).

## User Preferences
- Clear and concise explanations. Confirmation before significant changes.
- Iterative development and continuous feedback.
- Detailed logging and transparency into the agent's decision-making process.
- Control over AI model selection and custom tool definitions.
- Mobile-first UI with dark mode by default.
- Full token accounting with per-model, per-stage, per-conversation cost tracking.
- All AI model conversations logged verbatim.
- Data export (transcripts, conversations, credentials list, system config).

## System Architecture

**Three processes:**
- **Express** (:5000, external :80) — auth, session, guest chat, proxies `/api/*` to Python
- **Vite** (:5001) — React frontend, proxied by Express in dev
- **Python/FastAPI** (:8001, internal only) — AI + data backend; all access via Express

**Security:** Express injects `x-a0p-internal` + identity headers on every proxy. Python rejects requests missing the internal header. Session secret via `SESSION_SECRET` env var in production.

**Key entry points:** `server/index.ts`, `python/main.py`, `python/routes/__init__.py`, `client/src/App.tsx`

> Full file-by-file detail: `docs/ARCHITECTURE.md`

## Agent Architecture

**ZFAE** — `a0(zeta fun alpha echo) {EnergyProvider}`. One PCNA instance per agent. Sub-agents fork PCNA, execute, merge back.

**Energy Providers** (LLMs are energy sources, not agents):
- **grok** — xAI Grok-4 Fast | **gemini** — Gemini 2.5 Flash | **gemini3** — Gemini 3 Pro
- **claude** — Claude Sonnet 4.5 | **openai** — GPT-5 mini | **openai-5.5** — GPT-5.5 | **openai-5.5-pro** — GPT-5.5 Pro

**PCNA Engine** — 53-node six-ring pipeline: Phi, Psi, Omega, Theta, Memory-L (N=19), Memory-S (N=17).

**Prime-Seed PTCA Layer** — 7 PTCACore instances (N=3…19) seeded from sigma at boot. N=17→memory_s every 60s tick; N=19→memory_l on bandit promotion (persisted to DB). LT tag injected into prompt cache prefix; ST tag injected after `## Memory` marker. Fail-safe: returns `("","")` on any error.

> Full engine + prompt caching detail: `docs/ARCHITECTURE.md`

## Hard Rules
- No file over 400 lines
- No stubs or TODOs in production code
- Express handles auth/session/guest; Python handles all other API logic
- All API paths go through Express (`/api/*`) — never call Python (port 8001) directly from the frontend
- SQL column names in dynamic UPDATE queries must use an explicit allowlist

## Module Doctrine
Authoritative reference: `.agents/skills/a0p-module-doctrine/SKILL.md`. Load before creating or modifying any route module, service, or component.

- Every `.py`, `.ts`, `.tsx` file opens and closes with `# N:M` / `// N:M`. Run `python scripts/annotate.py` to re-stamp.
- Every new route file must be registered in 4 places in `python/routes/__init__.py`.
- Route naming: `{name}.py` = self-contained handler. `{name}_api.py` = thin delegate to a service.

## Funding
a0p runs on donations. No subscription tier. No perks unlocked by donating.

> "I don't have the cash required for 501c3 status, so I have to report it for taxes, but every tax payer is allowed to claim up to five hundred dollars in charitable donations per year without receipts required."

The single productized service is the **EDCMbone transcript explainer** — $50 for 3 explanations. 3 free lifetime credits per user. See `docs/ARCHITECTURE.md` → Explainer Pricing for full billing detail.

**Runtime tiers:** `free` (default, full read access) | `ws` (interdependentway.org accounts) | `admin` (owner + collaborators). No `supporter` tier in new sign-ups.

## Access Control (two-tier write gating)
1. **Admin** — `users.role = 'admin'` or email in `admin_emails`. Can mutate shared instrument state: prompt contexts, WS modules, provider seeds, custom tools, tier overrides.
2. **Everyone else** — read console, run own chats, manage own Forge agents and transcripts. Cannot reach shared instrument state.

Enforced at the route layer. Contract: `python/tests/contracts/route_gating.py`.

## External Dependencies
- **AI**: Gemini 2.5 Flash (Replit integration), Grok-4 Fast (XAI_API_KEY), Claude Sonnet 4.5, GPT-5 mini
- **Google**: Gmail, Google Drive (Replit connectors)
- **GitHub**: Repository ops (Replit connector)
- **Auth**: Replit Auth (OpenID Connect)
- **Payments**: Stripe (donations + EDCMbone explainer, Replit integration)
- **Database**: PostgreSQL (Replit managed)
