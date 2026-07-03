# CONNECTIONS.md — Coupling scheme: a0-betatest ⟷ aimmh ⟷ odysseus-a0

Purpose of this document: a formatted connection scheme showing every point where
**aimmh** or **odysseus-a0** can couple meaningfully with **a0-betatest (a0p)**, so
that either or both can be used *from within* a0-betatest. Each coupling names the
exact seam on both sides, what already exists vs. what needs to be written, and the
boundary rules that must hold.

---

## Mirrored sources in this repo

The three trees at this repo's root are verbatim mirrors (tracked files only) of
their source repos at the commits below. They are **not** the source of truth —
edit upstream first, re-mirror second.

| Directory | Source repo | Commit | Date | Exclusions |
|---|---|---|---|---|
| `a0-betatest/` | The-Interdependency/a0-betatest | `cf7d3a18fbd85418972a37b15e00f03f1139868d` | 2026-06-30 | `storage/agents/` (per-agent ZFAE `zfae_core.safetensors` checkpoints — non-committable per a0-betatest doctrine), `_legacy_a0/uploads/` (~142M upload blobs) |
| `aimmh/` | The-Interdependency/aimmh | `54031028538b06fe1c0e0716015fb23e0f93a552` | 2026-06-30 | none |
| `odysseus-a0/` | The-Interdependency/odysseus-a0 | `6fdbd55199973020eefafe6487a1d03f75c4a6b7` | 2026-06-06 | none |

The previous full contents of `a0ucns` live under `archive/` (moved intact, history
preserved as git renames).

---

## The three systems in one line each

| System | What it is | Its coupling surfaces |
|---|---|---|
| **a0-betatest (a0p)** | Donation-funded BYOK multi-model workspace + native a0(ZFAE) inference on the prime-tensor stack; FastAPI backend | `backend/providers/base.py` → `ProviderAdapter.chat(...) -> ChatResult` (BYOK provider protocol); `backend/tools/registry.py` → `Tool` registry with `TOOL_KIND_MCP` (`"mcp"`), sentinel-gated via `gated_invoke`; `backend/tools/mcp_relay.py` → JSON-RPC MCP client (`tools/list`, `tools/call`, optional bearer token); `backend/tools/mcp_server.py` → a0p's own MCP server surface; `backend/agents/` → per-user `AgentInstance` CRUD |
| **aimmh** | Multi-model hub. `aimmh_lib` = zero-dependency asyncio orchestration core; `backend/` = FastAPI hub service | `aimmh_lib.conversations` → `CallFn = async (model_id, messages) -> str` seam + patterns `fan_out`, `daisy_chain`, `room_all`, `room_synthesized`, `council`, `roleplay`, plus `MultiModelHub` / `ModelInstance`; `backend/routes/v1_hub.py` → persistent hub instances/groups over HTTP (JWT) |
| **odysseus-a0** | Self-hosted local-first AI workspace (chat, agent, memory, RAG, email, calendar, tasks, deep research) | `mcp_servers/` → ready-made MCP servers: `memory_server`, `rag_server`, `email_server`, `image_gen_server`; `routes/api_token_routes.py` → scoped bearer API tokens for its REST surface; `routes/model_routes.py` → *consumes* OpenAI-compatible endpoints (vLLM/llama.cpp/Ollama/OpenRouter/…) |

---

## Topology

```
                        ┌────────────────────────────────────────────┐
                        │            a0-betatest (a0p)               │
                        │  FastAPI :8001 (internal), ZFAE native     │
                        │                                            │
   [A] in-process       │  providers/           tools/registry       │
  ┌────────────────────►│  ProviderAdapter ◄─┐  (kind="mcp",         │
  │                     │  .chat()           │   gated_invoke)       │
  │                     └────────┬───────────┴────────┬──────────────┘
  │                              │ CallFn adapter     │ JSON-RPC
  │                              ▼ (new, ~40 loc)     │ tools/list · tools/call
┌─┴──────────────┐      ┌────────────────────┐        │  [C]
│   aimmh_lib    │      │ fan_out · council  │        ▼
│  (zero-dep,    │      │ daisy_chain · room │   ┌──────────────────────┐
│   vendored or  │      │ roleplay · rooms   │   │     odysseus-a0      │
│   pip install) │      └────────────────────┘   │  mcp_servers/        │
└────────────────┘                               │   memory · rag ·     │
        │  [B] HTTP (optional, heavier)          │   email · image_gen  │
        ▼                                        │  REST + api tokens ◄─┼── [D]
┌────────────────┐                               │  model endpoints ◄───┼── [E] a0p as
│ aimmh backend  │                               │  (OpenAI-compat)     │      OpenAI-compat
│ /api/v1/hub/*  │                               └──────────────────────┘      endpoint
└────────────────┘
```

---

## Coupling A — aimmh_lib in-process inside a0-betatest  ✅ recommended first

**What it gives you:** all six aimmh orchestration patterns (`fan_out`,
`daisy_chain`, `room_all`, `room_synthesized`, `council`, `roleplay`) running
natively inside a0p's comparison tool, driven by a0p's own BYOK providers — no
second service, no new keys, no network hop.

**Why it fits:** `aimmh_lib` is deliberately zero-dependency; its only contract is
`CallFn = async (model_id: str, messages: list[dict]) -> str`. a0p's
`ProviderAdapter.chat()` already returns a `ChatResult` with `content`. The
adapter is a thin glue function.

**What exists:** both sides fully; only the adapter is new.

**What to write (in a0-betatest, `backend/providers/aimmh_adapter.py`, ~40 loc + msdmd blocks):**

```python
from aimmh_lib import MultiModelHub  # vendored or pip install aimmh-lib

def make_a0p_call_fn(user: dict, resolve_provider) -> "CallFn":
    """Bind aimmh_lib's CallFn seam to a0p's BYOK ProviderAdapter registry.

    user: a0p user record (holds BYOK keys, already decrypted server-side)
    resolve_provider: model_id -> (ProviderAdapter, api_key)
    """
    async def call(model_id: str, messages: list[dict]) -> str:
        adapter, api_key = resolve_provider(user, model_id)
        result = await adapter.chat(api_key, model_id, messages)
        if result.get("error"):
            return f"[ERROR] {result['error']}"   # aimmh_lib error convention
        return result.get("content", "")
    return call

hub = MultiModelHub(make_a0p_call_fn(user, resolve_provider))
results = await hub.council(["grok-4", "claude-sonnet-4-5", "gpt-5-mini"], prompt)
```

**Rules that must hold:**
- Preserve the `[ERROR]`-prefix convention — aimmh_lib patterns detect errors by it.
- `ModelResult.step_num == -1` marks synthesis/DM steps; filter with `step_num >= 0`.
- **Energy-provider doctrine:** these patterns are *comparison-tool* surface, never
  the agent's voice. `zfae_native` mode must not silently route through them —
  ZFAE refuses LLM fallback by design.
- License: `aimmh_lib` is MPL-2.0 (file-level copyleft) inside Apache-2.0 a0p —
  fine to vendor; changes to the vendored files must stay published.
- Vendor at `backend/aimmh_lib/` **or** add `aimmh-lib>=1.1.0` to
  `backend/pyproject.toml`; do not do both.

---

## Coupling B — aimmh backend over HTTP (optional, heavier)

**What it gives you:** persistent hub *instances* and *groups* with history
(`aimmh/backend/routes/v1_hub.py`: create/list/patch/archive instances, groups,
history) — useful only if you want hub state to live outside a0p, or want the
aimmh UI alongside a0p.

**Seam:** aimmh `/api/v1/hub/*` (JWT-gated) ⟷ a0p `httpx` client, registered as a
webhook-kind tool or a small service in `backend/`.

**Cost:** a running aimmh deployment (MongoDB, `EMERGENT_LLM_KEY` or its own keys),
auth wiring, and duplicate model-registry semantics. **Skip unless you specifically
need shared hub state.** Coupling A gives the same orchestration without the service.

---

## Coupling C — odysseus-a0 MCP servers as a0p tools  ✅ recommended first

**What it gives you:** odysseus's persistent **memory** (ChromaDB + fastembed
vector/keyword retrieval), **RAG**, **email triage**, and **image-gen** become
callable tools inside a0p agents — with a0p's sentinel gating (`gated_invoke`)
still in front of every call.

**Why it fits:** this is the one coupling where *zero new code* is plausible.
a0p's tool registry already defines `TOOL_KIND_MCP = "mcp"`; MCP-kind tools carry
`mcp_server_id` + `remote_name` and dispatch through `tools.mcp_relay.invoke`,
which speaks JSON-RPC (`tools/list`, `tools/call`) over HTTP with an optional
bearer token. Odysseus ships the servers in `odysseus-a0/mcp_servers/`.

**Recipe:**
1. Run odysseus (`docker compose up -d`, web UI on :7000) with its MCP servers enabled.
2. In a0p, register the server record `{url, token}` for each odysseus MCP server.
3. `mcp_relay.ping_server(url)` → `list_remote_tools(...)` discovers the remote
   tools; register each as a `Tool(kind="mcp", mcp_server_id=..., remote_name=...)`.
4. Invocations flow: a0p agent → `gated_invoke` (sentinel evaluation, S4/S12 halt) →
   `mcp_relay.invoke` → odysseus server → result.

**Rules that must hold:**
- Keep the sentinel gate in front — never bypass `gated_invoke` for relayed tools.
- Odysseus binds to `127.0.0.1` by default; if a0p runs in another container/host,
  set `APP_BIND` deliberately and use a scoped token (Coupling D tokens work here).
- Memory written via odysseus belongs to odysseus's store; it is *tool state*, not
  a0p `MemoryCore` state — don't conflate the two memory systems.

---

## Coupling D — odysseus REST via scoped API tokens

**What it gives you:** everything odysseus exposes that is *not* an MCP server —
notes, tasks/cron, calendar (CalDAV), contacts, deep-research runs, document
editor, cookbook (hardware-aware model serving) — driven from a0p as tools.

**Seam:** odysseus `routes/api_token_routes.py` issues scoped bearer tokens
(`POST /api/tokens`, with scope profiles; write scopes imply their read scopes).
a0p registers webhook-kind tools (`tools/webhook.py`, HMAC/bearer) pointed at the
odysseus REST routes you want.

**What to write:** one small tool-definition module in a0p per odysseus capability
you expose (a few lines each: route, method, scope, schema). Start with tasks +
deep research; add calendar/email later.

**Rules:** mint least-scope tokens per capability; store them in a0p's crypto vault
(`backend/crypto_vault.py`), never in code or the repo.

---

## Coupling E — a0p as a model endpoint *inside* odysseus (reverse direction)

**What it gives you:** chat with **ZFAE native inference** (and any a0p-routed
model) from the odysseus UI, Compare tab, and agent — odysseus treats a0p as just
another model endpoint.

**Why it fits:** odysseus's `routes/model_routes.py` auto-probes and consumes any
OpenAI-compatible endpoint (`/v1/chat/completions` — vLLM, llama.cpp, Ollama,
OpenRouter…). a0p does **not** yet expose an OpenAI-compatible shim.

**What to write (in a0-betatest):** a small router, e.g.
`backend/openai_compat.py`, exposing `POST /v1/chat/completions` +
`GET /v1/models`, translating to a0p's internal inference (mode-aware: model id
`a0p/zfae-native` routes to ZFAE; `a0p/<provider>/<model>` routes BYOK). Gate it
with a bearer token; keep it off the public proxy unless intended.

**Then in odysseus:** Settings → add endpoint `http://<a0p-host>:8001/v1` + token;
models are probed and appear in chat/compare.

**Rule:** `zfae_native` refuses LLM fallback — surface that as an explicit error in
the shim, not a silent provider swap.

---

## Composite: all three at once

With A + C in place, a single a0p agent turn can:
`council()` across BYOK frontier models (aimmh_lib patterns) **while** reading and
writing odysseus memory/RAG as gated tools — and with E, odysseus users get ZFAE
answers back in their own UI. aimmh_lib can even fan out *over* odysseus-served
local models by adding one more branch to the Coupling-A `resolve_provider`
(an OpenAI-compatible client pointed at odysseus's served endpoints).

---

## Decision matrix

| You want… | Use coupling | New code? |
|---|---|---|
| Multi-model fan-out / council / daisy-chain inside a0p's comparison tool | **A** | ~40-line adapter |
| Persistent hub instances/groups with their own UI | B | service client + a running aimmh |
| Odysseus memory / RAG / email / image-gen as a0p agent tools | **C** | ~none (registration only) |
| Odysseus tasks, calendar, deep research, cookbook from a0p | D | thin webhook tool defs |
| ZFAE (or a0p-routed models) inside odysseus chat/compare | E | OpenAI-compat shim in a0p |

**Suggested order: A → C → D → E (B only if a concrete need appears).**

---

## Boundary rules (apply to every coupling)

1. **Non-committable material** stays out of every repo: BYOK keys, per-agent ZFAE
   checkpoints (`zfae_core.safetensors`), PCEA `last_state` key material, the
   157-gonal carrier disk, odysseus API tokens.
2. **Energy-provider doctrine:** LLMs (and aimmh patterns over them) supply
   computational energy; the agent remains a0(ZFAE). Comparison surfaces must be
   explicitly invoked, never the agent's default voice.
3. **No theorem/status transfer:** interoperability between these repos moves no
   theorem, proof, or empirical status (UCNS non-transfer rule applies).
4. **Sentinel gating is load-bearing:** all external effects from a0p route
   through `gated_invoke`; relayed MCP and webhook tools are not exceptions.
5. **Module doctrine:** every new module above starts with a `MODULE_BUILD` block;
   unknown fields are marked `hmmm`, not guessed; ratios bookends per repo
   convention.
6. **Edit upstream first.** The mirrors here are working copies for integration
   design; changes to a0-betatest/aimmh/odysseus-a0 code land in their own repos.
