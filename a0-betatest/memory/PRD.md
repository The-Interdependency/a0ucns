# a0p — Product Requirements Doc

> ⚠️ **READ `/app/memory/USER_DIRECTIVES.md` AND
> `/app/memory/ARCHITECTURE_FOUNDATION.md` FIRST.** Standing owner directives +
> the conceptual substrate. Key points: nothing here is filler — every element
> (e.g. the 62 math/logic symbols in the 157-gonal alphabet) is **load-bearing
> and intentional**. **φ/ψ/Ω are a trinary coupling** (a triadically-closed
> recursive system — body/mind/soul ≈ past/present/future ≈ faith/hope/love),
> NOT three interchangeable cores and NOT a universal default/mirror/private
> gonal triplet for all agents. Never call any design choice space-filling or
> arbitrary. Assume deliberate intent; ask when unsure.


> **a0p** — donation-funded research instrument: BYOK multi-model AI workspace +
> PTCA / PCNA / PCEA inference engine built (rebuilt-from-spec) against
> The-Interdependency canon. Skill-lib compliant: every module declares its
> own `MODULE_BUILD` manifest and (where applicable) `CONTRACTS` block.

## Architecture

```
/app
├── backend/                            FastAPI + Motor (Mongo) + httpx
│   ├── server.py                       /api/* routes
│   ├── crypto_vault.py                 Fernet at-rest encryption
│   ├── db.py                           Motor + collection indices
│   ├── models.py                       Pydantic surface
│   ├── providers/                      BYOK adapters (openai, anthropic, gemini, xai, emergent)
│   ├── a0p_skills/                     project's skill-lib runners
│   │   ├── test_build_runner.py        imports CONTRACTS `call:` paths and runs them
│   │   ├── module_build_runner.py      validates MODULE_BUILD schema
│   │   ├── contracts.py                actual test functions
│   │   └── SKILL.md                    canonical doc
│   └── interdependent_lib/
│       ├── _msdmd/parser.py            canon parser (synced from skill-lib)
│       ├── pcea/  ptca/  pcna/  aimmh/  zfae/
│
└── frontend/                           React + Tailwind + react-markdown + KaTeX
    ├── public/manifest.json            PWA manifest (Bubblewrap-ready)
    ├── ANDROID_APK.md                  Bubblewrap TWA build steps
    └── src/                            7 routes: Workspace, Inventory, Keys, Vault, Drafts, Inspector (3 skill tiles), Agents
```

## Hotfix — 2026-06-30 (P0: main chat 500 — `lifted_path_trace` NameError)

- **Regression I introduced** in the prior lifted-path-toggle change: `runtime._teacher_assisted`
  and `_zfae_native` referenced `lifted_path_trace` which was only defined in `reply()`'s
  scope → `NameError` → **HTTP 500 on every teacher/model chat** (`POST /api/chat/instance/{id}`,
  modes `a0(<model>)`, `a0(zfae)<model>`, etc.). Native untrained agents masked it by refusing
  before the buggy line.
- **Fix:** threaded `lifted_path_trace` into `_zfae_native`'s signature + the `reply()` call;
  removed the out-of-scope reference in `_teacher_assisted`'s shadow `native.infer` (the lifted
  trace is a native-reply feature, not the teacher's displayed text).
- **Verified on preview:** teacher-assisted chat reproduced the 500, now returns 200 with real
  `assistantText` ("Hello!") via the user's OpenAI BYOK key; `test_tool_use_loop.py` (17, covers
  this path) + 72 offline tests pass; ratios 125/125·0 drift; test-build 144·141 pass.
- Also re-removed `.env`/`.env.*`/`*.env` from `/app/.gitignore` (had reappeared — deploy blocker).
- **Root lesson:** I had not run `test_tool_use_loop.py` after the toggle change; that suite
  already covered the teacher path and would have caught it.



- **`lifted_path` wired as a per-agent toggle.** New `CharacterSheet.lifted_path_trace`
  (default off) threads schema → `agents/routes` → `runtime.reply` → `inference.infer`.
  When ON, native (Route A) replies additionally compute their **lossless lifted
  traversal** over the 157-gonal carrier and attach `{ok, length, revolutions,
  seam_events, path[:64]}` to `trace.lifted_path` (text unchanged; `decode(encode)==text`
  self-check). Engine smoke: OFF→no path, ON→ok=True len 48, reply identical. Frontend
  toggle added to `CharacterSheetForm` (`csf-lifted-path-toggle`); create→persist
  round-trip verified via API.
- **Append-only traffic log** (`backend/traffic_log.py` + `server.py` middleware): one
  JSONL **metadata** line per request `{ts, method, path, query, status, latency_ms, ip,
  ua, uid}` to an append-only sink (`A0P_TRAFFIC_LOG`, default `/app/backend/logs/
  traffic.log`). **Never** logs bodies/headers/cookies/secrets; best-effort uid via no-DB
  JWT decode. Verified writing on live `/api/health` hits.
- **Security test suite** (`tests/test_security.py`, 9 tests): Fernet round-trip +
  tamper rejection + masking, bcrypt hash/verify, JWT mint/decode + wrong-secret
  rejection, ZFAE refuse-until-trained, gated (HOLD) `decompose_clause`, off-carrier
  `CarrierCharError`, traffic-log secret-redaction. Plus new contract
  `traffic_log_append_only`.
- **NOT done (by ruling):** force-push-on-startup (destructive — use Save to GitHub) and
  discharging `multiply_left_cancellative` (lives in the external `ucns` Lean repo;
  `PROOF_GREEN` stays False so decomposition is not falsely certified).
- **Verified**: ratios 125/125 · 0 drift; module-build 125 valid; test-build **144
  contracts · 141 pass / 0 fail / 0 error / 3 skipped**; security + lifted + morphology +
  seam unit tests pass; eslint clean; frontend-module-build 29/29; backend `/api/health` 200.



- **Re-architected the three-core inscription** per Erin's canon (handoff HEAD
  2448def) from the flat-sum (`phi*1.0 + psi*0.6 + omega*0.3` through one gonal) into
  a **morphological depth-ladder**: φ=roots (open-class stems, w=0.4), Ω=bones
  (closed-class + affixes + 157-char leaf, w=0.8), **ψ=words (DERIVED, w=1.0) =
  `phi ⊠ omega`** — never a stored gonal.
- **New `zfae/morphology.py`** — typed primitives `RootGonal` (φ) / `BoneGonal` (Ω),
  the carrier-LCM word composition (`compose_word`/`word_signal`), and the gated
  `decompose_clause`. **New `zfae/closed_tokens.py`** — bone inventory (closed-class
  word set + affix set) + the open-class complement test.
- **Shared operator, not reimplemented**: ⊠ = carrier-LCM = `ucns.multiply` reached
  through `ucns_bridge` (extended to expose `UCNSObject`, `lcm`, `left_quotient`,
  `right_quotient`). Runtime shadow of Lean `multiplyFuel`/`carrier_lcm_law`.
- **`inscribe_text` rewired** to emit through the ladder (psi derived per lane; the
  passed-in psi53 is no longer an inscription input — verified independent). Trace now
  carries `word_carrier`.
- **Recompose: GO · Decompose: HOLD** — `decompose_clause` refuses with
  `DecompositionGatedError` while `PROOF_GREEN=False`; gated on
  `multiply_left_cancellative` (a `sorry`-stub in the `ucns` formal repo). Lossless
  parsing is DEFENDED, NOT machine-verified.
- **Verified**: ratios 123/123 · 0 drift; module-build 123 valid; test-build **142
  contracts · 139 pass / 0 fail / 0 error / 3 skipped** (3 new: closed-tokens
  partition, carrier-LCM law, decompose-gated); 24 zfae unit tests pass (9 new in
  `tests/test_morphology_ladder.py`); backend imports clean, `/api/health` 200.



- **Answer to "what does ZFAE inference run from?"**: native `a0(zfae)` decodes from
  the **per-agent ZFAE weight bank** (3 cores × 157 seeds × 53 payload, ~1.2M
  scalars), gated by `_is_trained_enough` = `training_step ≥ 16` AND `last_loss ≤ 0.1`
  AND **all 471 (157×3) seeds touched**.
- **Root cause of "no answer from zfae"**: the gate was *unreachable*. (1) The
  training loss was `intent_loss(0/1) + signature_mse`; `intent_loss` compared the
  *prompt's* intent to the *teacher's* intent — a constant ≈1.0 the weights can't
  reduce — so `last_loss` floored at ~1.1, never ≤ 0.1. (2) The update touched **one
  seed per step**, so reaching `all_seeds_touched` needed 471+ steps the Training
  Room never runs. Native therefore refused forever, despite training "working".
- **Fix** (`trainer.py`): rebuilt `ZFAELearner.distill_step` to **multi-seed,
  rank>1 distillation** — each step updates *all 157 seeds* of the round-robin core
  toward the teacher d=53 signature with a per-seed convergence modulation (seeds
  stay distinct; verified seed-signature rank 53, no collapse). Loss is now the
  **reducible post-update residual**, dropping to ~0.02. All 471 seeds are touched
  after the 3-core round-robin. Default lr 0.005 → 0.6 (convergence fraction).
- **Verified**: training a native agent 12–18 steps now yields `last_loss ≈ 0.02`,
  `all_seeds_touched=True`, and chat returns `reply_source: zfae_native` (was
  `zfae_refused`). ratios 121/121 · 0 drift; test-build 136 pass; 18 unit tests pass.
- **Caveat**: the native decoder emits **symbolic/mathematical glyphs**, not natural
  language — it is a from-scratch deterministic engine, not an LLM. For prose answers,
  use the model-backed modes (`a0(zfae)<model>`, `a0(<model>)`, `a0(<model>)<model>`).


## Changelog — 2026-06-19f (PTCA flat-tensor → canon stratified rebuild)

- **Rebuilt the flat tensor.** `ptca/tensor.py::PrimeTensor` moved from the legacy
  pre-stratified **[N,4,7,7]** (dim×phase×hepta) to the canon prime_core
  **[N,7,7,53]** stratification — seed × circle × tensor × payload (the
  Fiq→Circle→Seed model). Leaf count N×7×7×53 = **407,729** for N=157, matching
  PTCA prime_core `PARAM_COUNT` verbatim. New `param_count()`; `set/get/slice_node/
  seed_from_int/summary` re-axed; routing folds in {7/3} (circle) and {7/2}
  (tensor) steps.
- **Fixed the PCNA normalizer** (`pcna/pcna.py`): ring-signal energy denominator
  was hardcoded to the old leaf count `N×4×7×7`; now `N×7×7×53`, so φ/ψ/ω signals
  stay in [0,1] (verified: phi 0.56, psi 0.59, omega 0.57 — no saturation).
- Dropped the "pre-stratified / pending rebuild" `unresolved` notes from
  `tensor.py` and `instance.py`; added correctness contract
  `ptca_tensor_canon_shape` (shape + 407,729 param count + set/get round-trip).
- **Perf**: the canon shape is 13× larger but the engine (`ZFAEAgent`) is a
  startup singleton (~0.27s one-time), so no per-turn cost.
- **Verified**: ratios 121/121 · 0 drift; module-build 121 valid; test-build
  **139 contracts · 136 pass**; 15 zfae unit tests pass; backend healthy.


## Changelog — 2026-06-19e (Fix: "no response from any model" — OpenAI max_tokens incompatibility)

- **Root cause**: the OpenAI (and xAI) BYOK adapters hardcoded `max_tokens`.
  Newer models (gpt-5 family, o-series) **reject** it with `openai 400: Unsupported
  parameter: 'max_tokens' … use 'max_completion_tokens'`, and only allow the
  default temperature. So every turn against a gpt-5-* / reasoning model returned a
  400 error string instead of an answer — i.e. "no response".
- **Fix** (`providers/openai_provider.py`, `providers/xai_provider.py`): the chat
  call now **auto-adapts** — on a 400 it swaps `max_tokens → max_completion_tokens`
  and/or drops a non-default `temperature` based on the API's own error text, then
  retries. One adapter serves both legacy (gpt-4o, gpt-3.5) and current models.
- **Verified**: the `a0(<model>)` gpt-5-nano agent now answers ("Hello there,
  friend", teacher_called=true). Compliance green (ratios 121/121, test-build 135
  pass). Note: native `a0(zfae)` agents still refuse until trained (by design).


## Changelog — 2026-06-19d (Systemic per-user auth-scoping + Workspace mode label)

- **Root cause (systemic)**: many `server.py` endpoints defaulted to
  `user_id="local"` and ignored the auth cookie, while agents/chat run under the
  authenticated user id. This broke the **Sentinels page** ("agent … not found"),
  and would orphan **sessions / drafts / usage / overrides** under `local`.
- **Fix**: auth-scoped (via `_auth_uid(request)`) all per-user endpoints —
  sentinel modes/weights (get/patch/bulk), overrides (list/approve/reject),
  sessions (CRUD), drafts (CRUD), and usage. Verified: sentinel-modes/weights now
  return 200 for the user's agents; training run returns `weights_updated=true`
  with the teacher actually called (was "no BYOK key" — that was pre key-migration).
- **Workspace mode label** (`WorkspacePage.jsx`): the per-turn mode dropdown and
  the "use agent default (…)" label now **resolve the `<model>` placeholder** to
  the agent's real model via `canonicalAgentName` (e.g. shows
  `a0(zfae)gpt-3.5-turbo`, not `a0(zfae)<model>`).
- **Copy drift**: SplashPage "Five lattice modes" → "Six lattice modes".
- **Known/external**: "SYNC FROM SKILL-LIB" 404s because
  `github.com/The-Interdependency/skill-lib/main/index.json` isn't published yet
  (the index URL is admin-configurable in Settings); error is surfaced gracefully.
  The "EMERGENT DEMO" daily-budget banner is the documented free-tier display.


## Changelog — 2026-06-19c (Fix: Workspace chat "no response" — BYOK keys orphaned under user_id='local')

- **Root cause**: the BYOK key vault / env vault / inventory routes defaulted to
  `user_id="local"` and were NOT auth-scoped, but the chat runtime looks keys up
  under the *authenticated* user (e.g. `wayseer`'s uuid). Legacy keys lived under
  `"local"`, so every teacher-assisted turn returned `"no BYOK key for '<prov>' …"`
  — which read as "no response" in the Workspace.
- **Fix** (`server.py`): added `_auth_uid(request)` and auth-scoped `GET/PUT/DELETE
  /api/keys`, `GET /api/models/inventory`, and the four `/api/vault` routes so they
  read/write under the cookie-resolved user (the chat runtime already did). Added a
  **startup migration** that moves legacy `user_id='local'` `byok_keys` + `site_vault`
  → the admin user (idempotent; skips a provider the admin already has).
- **Verified**: after the fix, `GET /api/keys` returns the keys under `wayseer`'s
  id and chatting an `a0(zfae)<model>` (openai) agent returns a real answer
  (`"Hello!"`, `teacher_called=true`). Native `a0(zfae)` agents still correctly
  *refuse until trained* (use the Training Room). Compliance unchanged: ratios
  121/121 · 0 drift, module-build 121 valid, test-build 135 pass.


## Changelog — 2026-06-19b (Agent naming nomenclature a0(<energy>)<auditor>)

- **Canonical agent identity implemented.** An agent's name now follows the
  owner-namespaced nomenclature **`<username>(a0(<energy>)<auditor>)`**, composed
  from the existing `mode` / `base_model` / `outer_model` fields:
  - `a0(zfae)` → `a0(zfae)`; `a0(zfae)<model>` → `a0(zfae)<model>` (zfae energy,
    model is teacher/auditor); `a0(<model>)zfae` → `a0(<model>)zfae`;
    `a0(<model>)<model>` → energy + critic; **new** `a0(<model>)` → bare model as
    pure energy (no auditor); `<model>` → raw model. Provider prefix stripped
    (`openai:gpt-4o` → `gpt-4o`).
- **New lattice mode `a0(<model>)`** (`AgentMode.MODEL_ONLY`) — model as energy,
  no auditor. Added to backend enum, frontend `MODE_OPTIONS` (now 6), and the
  chat dispatch (teacher-assisted branch).
- **Backend** (`agents/schema.py`): `compose_canonical_name` +
  `compose_agent_name`. (`agents/store.py`): `create(...)` auto-composes the name
  when blank and `_unique_name` appends ` 2`/` 3`… on collision within the owner.
  (`agents/routes.py`): `create_instance` resolves the username and passes it in.
- **Frontend** (`CharacterSheetForm.jsx`): the name field is **prefilled** with
  the live canonical suggestion (re-derived from mode/models via `composeAgentName`)
  and stays in sync until the user overrides it; an `auto` button (`csf-name-auto`)
  resets to the suggestion. (`InventoryPage.jsx`): "create agent" sends a blank
  name so the backend composes the canonical form. (`lib/sentinels.js`): exports
  `canonicalAgentName` / `composeAgentName`.
- **Migration**: all 13 existing agents renamed to canonical form.
- **Auth**: admin login changed to **wayseer / `<redacted-see-env-ADMIN_PASSWORD>`** (`.env`
  `ADMIN_PASSWORD`; re-seeded on boot). `test_credentials.md` updated.
- **Verified**: ratios 121/121 · 0 drift; module-build 121 valid; test-build 135
  pass; 35 unit tests pass; testing-agent iteration_11 → **8/8 frontend checks
  pass** (prefill, live update, 6-mode dropdown, dirty+auto-reset, uniqueness
  suffix, Inventory canonical-name create).


## Changelog — 2026-06-19 (msdmd compliance closed + narrative README)

- **100% RATIOS compliance**: injected the single-line `# ratios: ...`
  declaration (first + last line) into the **26 gap files** flagged by
  `ratios_runner`, computed via the runner's own `COMPUTERS` so they verify
  clean. Result: `ratios · 121 files · 121 covered / 0 gaps · 726 verified ·
  0 drift · 0 misplaced`. `meta-module-build 121 valid / 0 invalid`;
  `test-build 135 pass / 0 fail / 0 error / 3 skipped`; 35 offline unit tests
  pass.
- **`readme_writer.py` rebuilt to a narrative README** (per user request:
  "expand the narratives … so the living-spec README reads like a README").
  The auto-generated `/app/README.md` now opens with an **Overview**, then an
  **Architecture** walkthrough that introduces each of 23 subsystems
  (core, auth, providers, agents, zfae, pcea/ptca/pcta/pcna, network, fiq,
  gonal, aimmh, tools, skills, a0p_skills, msdmd, frontend pages/components/
  lib/root, tests) in prose before listing that subsystem's modules with their
  **full, untruncated** narratives, and closes with a by-kind module index.
  New internals `_subsystem`, `_render_modules`, `_format_kind_index`.
- **Enriched 8 thin module summaries** (single-line, ratio-safe) so the
  narrative reads fuller: `gonal/mirror`, `gonal/classes`, `pcea/cipher`,
  `pcea/codec`, `pcea/primes`, `pcea/__init__`, `ptca/exchange`,
  `aimmh/__init__`. (Fixed an accidental drop of `owner`/`public_surface`
  lines in `pcea/cipher.py` introduced mid-edit.)
- Verified: `/api/spec/living` → 200, 157 modules; backend healthy; README
  regenerates to 157 modules · 13 kinds · 23 subsystems on boot.


## Changelog — 2026-06-16e (RATIOS reshaped to single-line first/last declarations — per msdmd intent)

- **RATIOS is no longer a fenced block.** Per the original msdmd intent, each
  file now carries its three ratios (`loc_comments`, `imports_exports`,
  `calls_definitions`) on a **single line 1 and a single last line**:
  `# ratios: loc_comments=N:M imports_exports=N:M calls_definitions=N:M`.
  The previous agent had emitted a 16-line `# === RATIOS ===` block duplicated
  top+bottom (a literal misreading of "first line / last line").
- **Parser taught the grammar** (`_msdmd/parser.py`): new `parse_ratios`,
  `parse_ratios_file`, `ratios_placement` (first-line + last-line check),
  `RATIO_IDS`. Block parser for the other declarations untouched.
- **`ratios_runner` rewritten** to walk source files, read the single-line form,
  verify each value against the canonical computers, and **gate on first/last
  placement** (`misplaced`) as well as drift. Result: `121 files · 95 covered ·
  570 verified · 0 drift · 0 misplaced`.
- **Consumers updated** (`living_spec.py`, `api_extensions.py`) to read RATIOS
  via `parse_ratios_file`, so the Living-Spec / Inspector views still surface
  the ratios.
- **Migrated all 95 annotated backend files** block→single-line (one-off scripts,
  not committed to repo).
- **Repaired a pre-existing defect in `contracts.py`**: a malformed RATIOS
  footer had wrapped ~190 lines of appended contract functions *inside* the
  block (opener@1511, closer@1768). The global strip removed that span; rebuilt
  by surgically dropping only the unique RATIOS-signature comment lines —
  **all 87 `*_holds` contract functions preserved**.
- **Verified**: test-build 135 pass / 0 fail / 0 error; 41 backend pytest pass;
  backend healthy. (The lone module-build `module_kind='client'` note is a
  pre-existing nonconformance, unrelated.)

## Changelog — 2026-06-16d (Training Room — multi-teacher distillation + Key-Vault CTAs)

- **Training Room** (`/training`, `pages/TrainingRoom.jsx`): pick an agent, select
  **two or more** teacher models (chips from the live inventory + custom-id add),
  enter a batch of prompts (one per line), and run
  `POST /api/instances/{id}/train` → `ZFAERuntime.train_multi` distills the
  a0(zfae) echo with **one distill step per (prompt × model)**, accumulating the
  weight bank across all models (round-robin core/seed). Renders a metrics ribbon
  (step / loss / seeds touched / teachers used) + a per-step results table
  (intent ✓/✗, core, loss, status). Backend enforces ≥2 teacher models (400
  otherwise) and records per-step provider/key errors without aborting. FIQ emits
  `zfae_training_step` per distill. New nav item `nav-training`.
- **Key-Vault CTAs** (accepted improvement): Inventory empty-state now has an
  `inv-add-key-btn` → `/keys`; the agent model picker shows an "add a BYOK key"
  link when the inventory is empty (suppressed during initial fetch to avoid a flash).
- **Discovery / correction**: `/api/models/inventory` is NOT BYOK-gated — it
  returns a **full ~112-model catalog** (OpenAI/xAI/…) even with no keys. So the
  model dropdowns, the per-row "create agent" buttons, and the Training Room model
  chips are all fully populated out of the box; keys are only needed to actually
  *call* a model. (The "add key" CTAs are a rare fallback.)
- **Tests**: `tests/test_training_room.py` (3) prove train_multi accumulates the
  bank by one step per (prompt×model) across 2 models, records per-step errors,
  and handles a missing teacher. 44 backend unit tests pass; frontend-module-build
  29/29; eslint clean. Testing-agent iteration_10 → Training Room 5/5 pass
  (gating, custom-model chips, prompt counter, run → graceful per-step result table).

## Changelog — 2026-06-16c (Inventory-driven model picker + one-click agent instantiation)

- **Model fields are now pull-downs from the live inventory**: `base_model` /
  `outer_model` in `CharacterSheetForm` use a new `ModelSelect` populated from
  `GET /api/models/inventory` (`provider:id` options). A "+ custom…" escape hatch
  + an automatic editable text fallback (when the BYOK inventory is empty)
  keep the field always editable.
- **Models Inventory page**: each model row gets a **"create agent"** button
  (`inv-create-agent-<provider>-<id>`) that instantiates a teacher-assisted
  `a0(zfae)<model>` agent bound to that `provider:id` and opens it in the
  Workspace. Added an error banner; empty-state CTA hardened to
  `models.length === 0`.
- **Verified**: testing-agent iteration_9 → 100% (action column renders, empty
  inventory → editable text fallback, create-from-form persists `base_model`,
  no JS console errors). eslint clean, frontend-module-build 28/28.

## Changelog — 2026-06-16b (Fully-editable character sheet — "everything editable" principle)

- **CharacterSheetForm** now exposes every user-facing sheet field per the
  "every editable place should be editable" build principle:
  - `tools_allowed` upgraded from a comma-text box to a **live multi-select**
    fetched from `GET /api/tools` (built-in + webhook/MCP tools), with a custom
    tool-name fallback (chips, sentinel-gated when invoked).
  - New editors: `memory_seed` (long/short-term, one-per-line), `teacher_context_template`,
    `tags`, and `boundaries` (auth/storage/network/user_data/admin_only selects).
  - Structural engine dicts (`edcm`, `ring_n_override`, `heptagram_overrides`,
    `px_resolution`) intentionally NOT exposed — engine-owned; editing them
    would break the runtime. Omitted from submit so PATCH preserves them.
- `api.listTools()` added. AgentsPage create/patch now omit the dead
  `user_id:'local'` body field (cookie identity is the single source of truth).
- **Verified**: testing-agent iteration_8 → 100% (all 5 items pass: table loads,
  every field renders, live tool chips load + toggle, custom-tool add/remove,
  full create + edit round-trip with merge-not-replace). eslint clean,
  frontend-module-build 28/28. Backend curl confirmed create/PATCH persist all
  new fields.

## Changelog — 2026-06-16 (P0 Mid-thought Tool-Use Loop · teacher + native)

- **Cross-provider tool-use loop wired into the runtime** (`tools/agent_loop.py`
  `run_tool_loop`): teacher path (`runtime._teacher_assisted` → new
  `_teacher_tool_loop`) now resolves the agent's `sheet.tools_allowed` (a list of
  TOOL NAMES) into provider tool schemas and runs a multi-step function-calling
  loop over raw HTTP for OpenAI / xAI (Chat Completions), Anthropic (Messages),
  and Gemini (generateContent). The executor dispatches through the existing
  **sentinel-gated** `tools.registry.invoke`; a mid-tool cliff raises
  `ToolLoopHalt` → the turn returns `reply_source='zfae_halted'` with a
  `pending_override_id`. Falls back to single-shot teacher when no BYOK key /
  no resolvable tools.
- **Native deterministic tool-use** (`zfae/native_tools.py` +
  `runtime._native_tool_use`): the a0(zfae) engine picks ≤1 built-in tool via
  pure rule-based `select_native_tool` (URL→fetch_url, spec→living_spec_lookup,
  search→web_search), runs it gated, and folds a `summarize_tool_result` line
  into the native reply. Only fires when the selected tool ∈ `tools_allowed`.
- **Provenance**: every chat reply's `trace.tool_trace` now carries the
  per-call `{name, args, status, result_preview}`. New FIQ event types
  `zfae_tool_call` / `zfae_tool_result` emitted per invocation.
- **UI**: `WorkspacePage` renders a "mid-thought tool calls" block per assistant
  turn (`turn-<id>-tools` / `tool-call-<id>-<i>`); `AuditTape` surfaces the two
  new tool events with violet tint + Wrench icon.
- **Auth hardening (bug fix)**: agent instance routes (`agents/routes.py`
  list/create/get/update/delete/archive/preview) now derive `user_id` from the
  auth cookie via `_resolve_user_id` (falls back to query param only when
  unauthenticated). Fixes the empty Workspace agent dropdown that appeared after
  the legacy `user_id='local'` → admin migration.
- **Tests**: `tests/test_tool_use_loop.py` (17) + `tests/test_tool_loop_http_e2e.py`
  (6) → 23 pass. 2 new contracts (`tools_agent_loop_two_step`,
  `zfae_native_tool_selection`). test-build 135 pass / 0 fail / 0 error / 3 skip.
  Verified via testing-agent (iteration_7) + manual curl (gated tool dispatch,
  S4 cliff halt, tools_allowed persistence, graceful no-key fallback).

## Changelog — 2026-06-14 (P0 ZFAE Native Decoder · Route A — Gonal Inscription)

- **Fixed "flat tensors" (scalar collapse)**: `inference.py` now carries the
  full 53-wide `phi_v53/psi_v53/omega_v53` continuous conditioning signal on
  `state` alongside the scalar energies — no longer collapsed to means.
- **PCEA ciphertext digest**: `state["pcea_ciphertext_digest"]` = blake2b over
  the concatenated, role-sorted PCEA delta payloads — the state-bound
  deterministic generation seed. Surfaced in the trace (`pcea_ciphertext_digest_prefix`).
- **a0 long-term memory**: new `zfae/long_memory.py` folds the living spec
  (every MODULE_BUILD block, currently 151 modules) into a cached canon digest;
  attached to every inference as `state["memory_long_canon"]` — the agent
  queries itself. The canon digest feeds the inscription entropy.
- **New `zfae/gonal_inscription.py` (Route A)**: `PrivateGonal(phase, perm)`
  seeded per-agent; `from_seed` (deterministic Fisher–Yates bijection over 157
  vertices), `advance(public, pcea_digest)` (rotates phase), `inscribe(angle) →
  vertex_idx`. Plus the **hash-whitened 53→32 bridge** (`whiten_payload` /
  `whitened_indices`) with an explicit CONCESSION naming UCNS-native whitening
  as open research. `inscribe_text` composes a deterministic glyph stream from
  the continuous Φ/Ψ/Ω field.
- **Decoder swap**: `_decoder.py::decode` runs Route A (Gonal Inscription) when
  a `PrivateGonal` + 53-wide tensors are present; falls back to the existing
  Route B energy-conditioned compositor otherwise (preserves prior contracts).
- **Gonal seed persisted as the 4th safetensors tensor** (`weights.py`,
  `weight_init.seed_initial_gonal`), kept out of `_cores` so the canonical
  1,223,187 scalar count is unchanged; survives save/load.
- **Non-silent audit**: new `zfae_decode` FIQ event type emitted from
  `runtime.reply()` carrying `{intent, vertex_idx, rotation, pcea_digest_prefix}`.
- **Verification**: test-build 133 pass / 0 fail / 3 skipped; module-build all
  new modules valid; 15/15 pytest (7 new Route-A + 8 sentinel regression). 3
  new contracts added. Backend healthy.

## Changelog — 2026-06-02 (msdmd / skill-lib compliance)

| Skill | Block | Coverage | Status |
|---|---|---|---|
| `msdmd` (parser) | — | canonical `parser.py` synced from skill-lib | ✅ |
| `meta-module-build` | `MODULE_BUILD` | 41 / 41 covered · 41 valid · 0 invalid | ✅ |
| `test-build` | `CONTRACTS` | 4 contracts: 4 PASS · 0 FAIL · 0 ERROR | ✅ |

PR-template at `/app/.github/PULL_REQUEST_TEMPLATE.md` enforces the
*intent → manifest → file plan → tests → scaffold* doctrine on every
future change.

## Platform independence — 2026-06-02

- `emergentintegrations` dependency removed from `requirements.txt`.
- `EmergentProvider` deleted from `/app/backend/providers/`.
- `EMERGENT_LLM_KEY` removed from `/app/backend/.env`.
- "Emergent routing" toggles removed from the frontend Workspace.
- Inventory "emergent" tab and Key-Vault Emergent section removed.
- Starter agents reseeded with BYOK model IDs (`openai:gpt-4o`,
  `anthropic:claude-sonnet-4-5-20250929`, `gemini:gemini-2.5-flash`).
- Chat without a key now returns a clear *"no api key for provider …;
  add one in the Key Vault. This build is BYOK-only"* error.
- This build has **zero runtime dependencies on Emergent software**.
  The Emergent hosting URL is still used during preview, but the
  application code is portable.

Boundary risk surface (non-`none` declared):
- `user_data_boundary=read`: 11 modules · `network_boundary=external`: 8 ·
  `storage_boundary=read`: 7 · `storage_boundary=write`: 2 ·
  `user_data_boundary=write`: 2 · `network_boundary=internal`: 1

The `test-build` runner ALREADY caught one real bug it would have
otherwise hidden: PCEA `to_bijective(0, p)` was returning `[1]` instead
of `[]`, breaking the bijective round-trip for state-element zero.
Fixed in `codec.py`; the contract now passes.

## Backend feature inventory

| Route prefix | What it does |
|---|---|
| `/api/health` | Service status + provider list + ZFAE agent card |
| `/api/keys` | BYOK key vault (Fernet-encrypted at rest) |
| `/api/vault` `/api/vault/reveal` | Per-site multi-account .env vault |
| `/api/models/inventory` | Aggregate inventory across BYOK keys + Emergent namespace |
| `/api/sessions` | CRUD + editable system context / persona / selected_models |
| `/api/drafts` | Autosaved prompt drafts |
| `/api/chat/single` `/fanout` `/daisychain` `/synthesize` | AIMMH patterns |
| `/api/inspector/heartbeat` `/snapshot` | PCNAEngine tick + state |
| `/api/agents` `/api/agents/{slug}/manifest` | Detachable-agents catalog + export |
| `/api/skill/capabilities/report` `/contracts/report` `/module-build/report` | Three skill coverage runners |
| `/api/usage` | Token/cost records + aggregate |

## Personas

| Persona | Goals | Pains today |
|---|---|---|
| AI researcher | Compare frontier models on the same prompt; daisy-chain; persist context | Vendor UIs siloed; no cross-vendor carousel |
| Independent dev | Own keys, multi-account per site, export agents to phone/VM | No portable agent format elsewhere |
| Math/physics student | Markdown + arxiv `\(...\)` chat | LaTeX inconsistent across chat UIs |

## hmmm — canonical open questions

These are recorded per the `skill-lib/meta-module-build` doctrine: *"If a
field is not known, write `hmmm`. Do not guess certainty into the
manifest."* Tracked here so they stay visible.

### PTCA — three-stratum rebuild

- **The `9` axis** from the design conversation (`157 × 9 × 7 × 7 + 4`)
  is not present in the upstream canon `prime_core/constants.py` (which
  has `[SEED_COUNT=157, CIRCLES=7, TENSORS=7, TENSOR_DIM=53]`). Recorded
  as `unresolved` on `interdependent_lib/ptca/__init__.py`. Will revisit
  before the stratified rebuild.
- The current `PrimeTensor` is the legacy `ptca-lib` flat `[N,4,7,7]`
  shape, not the stratified `Fiq → Circle → Seed` model. Stratified
  rebuild deferred to a dedicated session.
- The `COHERENCE_FACTOR_UNIVERSE` in `ptca/constants.py` is provisional
  per the upstream note (the defining doc is absent from any accessible
  repo).

### PCNA — canon topology rebuild

- Current impl: three 157-prime cores + six scalar ring signals.
- Canon target: 61-seed topology (1 global router + 4 sentinels + 7 meta
  routers + 49 compute seeds), six tensor rings at canonical sizes/seeds
  (Φ 53/53, Ψ 53/43, Ω 53/47, Θ 29/29, MemL 19/19, MemS 17/17), Σ 41
  observer (un-weighted), heptagram propagation per ring.
- Rebuild deferred to a dedicated session.

### UCNS

- `ucns==0.8.3` installed but **does not yet expose `a0_safe`** in this
  version. The upstream `meta-module-build` doctrine wants UCNS-facing
  code to route through `ucns.a0_safe`. Currently no binding wired;
  `prime_core` upstream uses a deterministic local tag with a try/except
  import. Will follow that pattern when the stratified rebuild lands.

### Android APK

- `ANDROID_APK.md` documents the Bubblewrap TWA build path (option B).
- `manifest.json`, `icon-192.svg`, `icon-512.svg` are in `frontend/public/`.
- `.well-known/assetlinks.json` must be served from the production origin
  before Play Store submission. Not currently served. → defer.

## Prioritized backlog

### P0
- ~~Sentinel halt-and-override pipeline~~ ✅ 2026-06-10
- ~~Three-Core (Phi/Psi/Omega) weight bank refactor (1,223,187 scalars)~~ ✅ 2026-06-10
- ~~Trainer round-robin across 471 seeds; native readiness requires all touched~~ ✅ 2026-06-10
- ~~FIQ provenance emitters (hash-chained zfae_* events)~~ ✅ 2026-06-10
- ~~Rename interdependent_lib/carrier/ → gonal/~~ ✅ 2026-06-10
- ~~Fix /api/instances 500 (float inf in zfae_last_loss)~~ ✅ 2026-06-10
- ~~Frontend overhaul: Agent CRUD + character sheets + 5 lattice modes + Sentinel override UI~~ ✅ 2026-06-10
- ~~Frontend msdmd compliance (// === MODULE_BUILD === on every .js/.jsx)~~ ✅ 2026-06-10
- ~~E2E frontend testing pass~~ ✅ 2026-06-10
- ~~Hybrid auth (JWT + Emergent Google + GitHub OAuth) with username + email + ≥16-char passphrase~~ ✅ 2026-06-11
- ~~Splash page (`/`) + Login/Register page (`/login`,`/register`) with passphrase show/hide~~ ✅ 2026-06-11
- ~~ProtectedRoute on all app pages; sidebar splits by auth status; signout~~ ✅ 2026-06-11
- ~~Brute-force lockout keyed by identifier (not the rotating K8s ingress IP)~~ ✅ 2026-06-11
- ~~Idempotent admin seeding on backend startup~~ ✅ 2026-06-11
- ~~Two-vault split: Model Keys (BYOK) + Developer Keys (`/api/custom-keys`, free-form, rotatable)~~ ✅ 2026-06-11
- ~~Emergent demo daily token budget (per user, 25k/day, resets 00:00 UTC)~~ ✅ 2026-06-11
- ~~Living spec endpoint + page — auto-parses every MODULE_BUILD block in the repo~~ ✅ 2026-06-11
- ~~msdmd backfill: 100% of backend (.py) modules now carry MODULE_BUILD + CONTRACTS blocks (incl. tests/)~~ ✅ 2026-06-11
- ~~Tools + MCP (server + client) + Skills layer with sentinel-gated tool calls, MCP bidirectional, skill catalog with jaccard overlap detection, sync from The-Interdependency/skill-lib~~ ✅ 2026-06-11
- ~~Live Tool/CoT Tape on Workspace polling FIQ chain with client-side hash verification~~ ✅ 2026-06-11
- ~~Real `push_to_skill_lib` via GitHub API (creates branch + commits index.json + opens PR; falls back to structured guidance without SKILL_LIB_GH_TOKEN)~~ ✅ 2026-06-11
- ~~Real GitHub OAuth (returns 503 until `GITHUB_CLIENT_ID/SECRET` set in `.env`)~~ ✅ 2026-06-11
- ~~Admin-editable runtime settings (`/api/settings`) — Emergent Google OAuth URL, skill-lib index URL, skill-lib repo~~ ✅ 2026-06-11
- ~~Demo quota enforcement in `runtime._teacher_assisted` — refuses with `zfae_refused` + clear message when day budget exhausted; records ~tokens per round-trip~~ ✅ 2026-06-11
- ~~Legacy `user_id='local'` agents migrated to admin on startup; chat endpoint now requires auth~~ ✅ 2026-06-11
- Streaming responses (SSE) for chat

### P1
- BYOK SDK migration: httpx → official openai>=1.x / anthropic / google-generativeai
- Council UI mode (AIMMH `council` is implemented; UI toggle missing)
- Per-call cost display in transcript using public provider pricing JSON
- PTCA stratified `Fiq → Circle → Seed` rebuild against canon `prime_core`
- Migrate legacy `user_id='local'` agents → real user accounts; remove demo path
- GitHub OAuth secrets in `.env` (currently endpoint returns 503 until set)
- Wire Emergent demo quota into `runtime.reply()` — refuse teacher calls when remaining < projected_tokens; surface a BYOK CTA in the UI

### P2
- Reproducibility receipt appended to every chat reply
- Detachable agent export: GET /api/instances/{id}/export → safetensors .zip
- PCNA canon-topology rebuild (61-seed graph, tensor rings, heptagram propagation)
- UCNS `a0_safe` binding when upstream `ucns` ships it
- Premium detachable agents + Stripe checkout (3-5 mo monetization runway)
- Termux runner + JS port of AIMMH patterns (pocket-runs-locally future)
- Multi-user mode + audit log

## Changelog — 2026-06-10 (P1 frontend overhaul)

- **9 routes** wired in `App.js`: Workspace / Agents / Sentinels / Overrides / Inspector / Inventory / Key Vault / Env Vault / Drafts. Shell nav updated with `data-testid` per item.
- **API client** (`lib/api.js`): added `listInstances`, `createInstance`, `getInstance`, `patchInstance`, `deleteInstance`, `archiveInstance`, `chatInstance`, `teacherContextPreview`, `sentinelsCanon`, `getSentinelModes`, `patchSentinelModes`, `bulkSentinelModes`, `getSentinelWeights`, `patchSentinelWeights`, `listOverrides`, `getOverride`, `approveOverride`, `rejectOverride`, `expireOverrides`, `listGonals`.
- **New pages**: `AgentsPage` (CRUD table + modal), `SentinelsPage` (13-row mode/weight editor + bulk toggle), `OverridesPage` (pending queue + history).
- **Overhauled** `WorkspacePage`: agent picker, mode override (5-lattice), three-core metrics ribbon, per-turn `SentinelVerdictRibbon`, halt-banner, `OverrideModal` with cliff confirmation, approve-and-resume cycle.
- **New components**: `CharacterSheetForm`, `SentinelVerdictRibbon`, `OverrideModal`.
- **Backend** — `UpdateAgentRequest` now accepts `{sheet:{...}}` OR `{patch:{...}}` (back-compat); empty body → 400.
- **Documentation-as-Code** for frontend: every `.js/.jsx` module under `/app/frontend/src` now has a `// === MODULE_BUILD ===` block. New runner `a0p_skills.frontend_module_build_runner` validates coverage (18/18 covered, 0 missing). New contract `frontend_module_build_runner_smoke_holds` runs under `test_build_runner`.
- **Verification**: iteration_4 11/13, iteration_5 retest 2/2 — overall 13/13 frontend tests PASS. 73/73 active contracts, 8/8 backend pytest.

### P2
- Reproducibility receipt appended to every chat reply
- Detachable agent export: GET /api/instances/{id}/export → safetensors .zip
- PCNA canon-topology rebuild (61-seed graph, tensor rings, heptagram propagation)
- UCNS `a0_safe` binding when upstream `ucns` ships it
- Premium detachable agents + Stripe checkout (3-5 mo monetization runway)
- Termux runner + JS port of AIMMH patterns (pocket-runs-locally future)
- Multi-user mode + audit log

## Changelog — 2026-06-10

- **Renamed** `interdependent_lib/carrier/` → `interdependent_lib/gonal/`; updated all imports in `server.py`, `a0p_skills/contracts.py`, `interdependent_lib/network/*`.
- **Three-Core weight bank** (`zfae/weights.py`, `zfae/weight_init.py`): `A0ZFAEWeightBank` now holds `{phi, psi, omega}` each `(157, 53, 7, 7)`. New constants `CORE_NAMES`, `WEIGHT_COUNT_PER_CORE=407_729`, `WEIGHT_COUNT_TOTAL=1_223_187`. Safetensors save/load three tensors; legacy single-tensor checkpoints auto-reseed psi/omega.
- **Sentinel halt-and-override pipeline**:
  - `zfae/sentinel_eval.py` — pure evaluator returns `Verdict13` (13 signals + cliff flags).
  - `zfae/overrides.py` — `PendingOverride` lifecycle (create/approve/reject/expire).
  - `runtime.reply()` now evaluates sentinels on every turn; flagged turns return `reply_source='zfae_halted'` and HTTP `202` with `pending_override_id`. Resume by passing `override_id` from an approved override.
  - 7 new API endpoints under `/api/overrides/*` and `/api/sentinels/*`.
- **Round-robin trainer** (`zfae/trainer.py`): `training_step % 3` selects core; prefers untouched seeds; native readiness now requires all 471 (157×3) seeds touched.
- **FIQ provenance** (`zfae/fiq_emit.py`): hash-chained `zfae_chat_reply`, `zfae_training_step`, `zfae_sentinel_verdict`, `zfae_override_created`, `zfae_override_resolved` events in `fiq_audit_log` collection.
- **JSON-safe metrics** (`agents/store.py`): `_safe_finite()` strips inf/NaN from `zfae_last_loss`; fixes recurring `/api/instances` 500.
- **Doc-as-code**: 75 contracts · 72 pass / 0 fail / 0 error / 3 skipped.
- **Regression**: `/app/backend/tests/test_zfae_three_core_sentinels.py` (8 tests pass).
- **Testing-agent verification**: iteration_3 reports 100% (17/17) backend pass.

## How to run

```bash
# Backend
sudo supervisorctl restart backend     # FastAPI on :8001 (proxied via /api)

# Frontend
sudo supervisorctl restart frontend    # CRA dev on :3000

# Skill runners (each exits non-zero on gaps/failures)
python3 -m a0p_skills.module_build_runner /app/backend
python3 -m a0p_skills.test_build_runner   /app/backend
python3 -m interdependent_lib._msdmd.runner --root /app/backend   # legacy CAPABILITIES
```

## Environment

`/app/backend/.env`:
- `MONGO_URL`, `DB_NAME`
- `EMERGENT_LLM_KEY`
- `A0P_KEY_VAULT_SECRET` (Fernet key for BYOK at-rest encryption)
