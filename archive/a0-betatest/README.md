# a0p — research instrument

> _changes constant. refinements welcome._  
> [wayseer@interdependentway.org](mailto:wayseer@interdependentway.org)

_Living spec — auto-regenerated on backend startup at 2026-06-30 17:38:47 UTC._  
_164 modules · 14 kinds · 23 subsystems._

> This file is generated from the codebase's own documentation. Don't edit it by hand — edit a module's `# === MODULE_BUILD ===` block (its `summary` is the narrative you read below) and it regenerates on the next backend start.

## Overview

**a0p** is a donation-funded research instrument: a BYOK (bring-your-own-key) multi-model AI workspace wrapped around a native, deterministic inference engine — **a0(zfae)** — that is rebuilt-from-spec against The-Interdependency canon (PTCA / PCTA / PCNA / PCEA). You connect your own provider keys (OpenAI, Anthropic, Gemini, xAI), instantiate semi-permanent agents from fully-editable character sheets, and chat through a sentinel-gated runtime that can call tools mid-thought, distill from multiple teachers in the Training Room, and audit every state transition on a hash-linked FIQ tape. The whole codebase is documentation-as-code: every module declares its own manifest, contracts, boundaries, and line-ratios, and this README is regenerated from those declarations on every boot.

## Architecture

The walkthrough below moves from the outer service inward to the inference substrate, then out to the frontend. Each subsystem opens with what it is and why it exists, followed by its modules and their narratives.

### Core service & API surface · 10

The FastAPI application and its REST surfaces — health, BYOK key vault, per-site env vault, model inventory, sessions, drafts, the AIMMH chat endpoints, the inspector, the tools/MCP/skills surface, admin-editable settings, and the living-spec endpoint. MongoDB (Motor) is the only datastore; credentials are Fernet-encrypted at rest.

- **`api_tools_mcp_skills`** — REST surface for the tools / MCP-client / skills layer — /api/tools (list, register user-webhook tool, invoke), /api/mcp/servers (CRUD external MCP servers, refresh their tools), /api/skills (list, register w/ overlap warning, delete, sync from skill-lib)  
  `backend/api_tools_mcp_skills.py`
- **`app_settings`** — admin-editable runtime settings — single Mongo doc with key/value overrides for non-secret URLs (Emergent Google OAuth widget URL, etc.); /api/settings GET for everyone, PATCH for admin only; values shadow env vars at runtime  
  `backend/app_settings.py`
- **`crypto_vault`** — Fernet encrypt/decrypt + mask for at-rest BYOK credentials  
  `backend/crypto_vault.py`
- **`db`** — Motor async client + collection accessors + index ensurance  
  `backend/db.py`
- **`extensions`** — post-auth API extensions — custom keys vault (user-defined GitHub/GCP/AWS-style keys), Emergent demo quota (per-user daily token budget), living spec endpoint (auto-parses MODULE_BUILD/BOUNDARIES/CAPABILITIES/CONTRACTS/RATIOS blocks from the repo and serves them as JSON), audit feed (hash-chained FIQ events for the Tool/CoT Tape)  
  `backend/api_extensions.py`
- **`living_spec`** — pure scanner over the repo that returns every msdmd block as JSON; no DB / network dependencies; used by the /api/spec/living endpoint and by contract tests  
  `backend/living_spec.py`
- **`models`** — Pydantic surface for the public API (BYOK keys, vault, sessions, drafts, chat, agents)  
  `backend/models.py`
- **`readme_writer`** — regenerates /app/README.md on every backend startup from the living spec (scan_repo_blocks) as a narrative README — an Overview, a per-subsystem Architecture walkthrough (each subsystem gets a prose lead plus its modules' full narratives), and a by-kind module index; deterministic and never raises  
  `backend/readme_writer.py`
- **`server`** — FastAPI app — keys, vault, inventory, sessions, drafts, chat (single/fanout/daisy/synth), inspector, agents, usage, skill report  
  `backend/server.py`
- **`traffic_log`** — append-only traffic logger — an ASGI middleware that records one JSONL line of request METADATA per HTTP call (ts, method, path, status, latency_ms, client ip, user-agent, best-effort user id) to an append-only sink; never logs request/response bodies, headers, cookies, or any secret material  
  `backend/traffic_log.py`

### Authentication · 1

Hybrid identity: custom JWT auth (username + email + ≥16-char passphrase, bcrypt, httpOnly cookies, brute-force lockout keyed by identifier) plus Emergent Google and GitHub OAuth. An admin account is idempotently seeded from the environment on every boot.

- **`routes`** — hybrid JWT auth + OAuth (Emergent Google, GitHub) — /api/auth/{register,login,logout,me,refresh,oauth/*}; username (unique) + email (unique) + ≥16-char passphrase; bcrypt; httpOnly cookies; brute-force lockout  
  `backend/auth/__init__.py`

### BYOK provider adapters · 6

Thin, uniform adapters that front each vendor over raw httpx — list models and run a completion against a key the user supplied. A shared Protocol keeps OpenAI, Anthropic, Gemini, and xAI behind one calling contract; the build carries zero runtime dependency on any hosting vendor.

- **`anthropic_provider`** — Anthropic BYOK adapter — list models, messages via httpx  
  `backend/providers/anthropic_provider.py`
- **`base`** — common Protocol + TypedDict contract for BYOK LLM provider adapters  
  `backend/providers/base.py`
- **`gemini_provider`** — Google Gemini BYOK adapter — list models, generateContent via httpx  
  `backend/providers/gemini_provider.py`
- **`openai_provider`** — OpenAI BYOK adapter — list models, chat completion via httpx  
  `backend/providers/openai_provider.py`
- **`providers`** — BYOK adapter registry — openai, anthropic, gemini, xai (Emergent removed; build is platform-free)  
  `backend/providers/__init__.py`
- **`xai_provider`** — xAI Grok BYOK adapter — OpenAI-compatible /v1 via httpx  
  `backend/providers/xai_provider.py`

### Agents — character-sheet instances · 4

Agents are treated as users: semi-permanent, character-sheet-bound instances that each own their Φ/Ψ/Ω and memory rings plus a per-instance ZFAE weight bank and archive. The schema covers the full editable surface (modes, models, persona, tools_allowed, memory seeds, boundaries).

- **`agents`** — per-agent CRUD; semi-permanent character-sheet-bound instances; each owns Φ/Ψ/Ω/MemL/MemS + per-instance ZFAE weight bank + archive  
  `backend/agents/__init__.py`
- **`routes`** — /api/instances/* CRUD + /api/chat/instance/{id} mode-aware; surface-3 teacher context preview endpoint  
  `backend/agents/routes.py`
- **`schema`** — Pydantic models — AgentInstance, CharacterSheet, AgentMode (the 6-lattice modes incl. bare a0(<model>)), PXResolution; plus the canonical agent-name composer (a0(<energy>)<auditor>, owner-namespaced)  
  `backend/agents/schema.py`
- **`store`** — full CRUD over MongoDB metadata + filesystem per-agent checkpoint dir; agents treated as users (persistent semi-permanent instances)  
  `backend/agents/store.py`

### a0(zfae) — native inference engine · 23

The heart of the instrument: a pure, deterministic symbolic/state engine with no LLM dependency. It parses a prompt into semantic features, folds them through Φ/Ψ/Ω ring transitions, and decodes text as a reproducible function of state (Route A inscribes the continuous field onto a private per-agent gonal; Route B is the energy-conditioned compositor). It carries long-term memory of the repo's own living spec, trains by teacher distillation across a three-core weight bank, and gates every turn through the 13 sentinels before replying.

- **`_decoder`** — native energy-conditioned decoder — composes assistantText as a deterministic function of (intent, features, Φ/Ψ/Ω/θ/σ energy state); RNG seeded from blake2b(state) so identical state → identical text; render() retained as named single-sentence fallback; no LLM dependency  
  `backend/interdependent_lib/zfae/_decoder.py`
- **`_intent`** — deterministic intent selector — maps (SemanticFeatures, ZFAE state) → one of a small fixed intent label set; pure function  
  `backend/interdependent_lib/zfae/_intent.py`
- **`_parser`** — deterministic prompt parser — token stats, intent surfaces (question, greeting, command, reflection), semantic load  
  `backend/interdependent_lib/zfae/_parser.py`
- **`_transition`** — ZFAE transition rules — folds semantic features into Φ/Ψ/Ω ring snapshots via PCEA kernel cross-cut; produces nextSnapshot  
  `backend/interdependent_lib/zfae/_transition.py`
- **`archive`** — ZFAE archive — per-agent training records JSONL + per-session ephemeral chat archive with char-compress output shape  
  `backend/interdependent_lib/zfae/archive.py`
- **`closed_tokens`** — morphological bone inventory — the closed-class word set + bound-morpheme (affix) set the BoneGonal (omega) sources its structural vertices from; the open-class test is the complement used by the RootGonal (phi)  
  `backend/interdependent_lib/zfae/closed_tokens.py`
- **`fiq_emit`** — ZFAE-level provenance emitter — appends hash-chained zfae_* events (training_step, chat_reply, sentinel_verdict, override_created, override_resolved) to fiq_audit_log  
  `backend/interdependent_lib/zfae/fiq_emit.py`
- **`gonal_inscription`** — ZFAE Native Decoder Route A — Gonal Inscription. A per-agent PrivateGonal (secret phase + permutation, seeded at instantiation) inscribes the continuous Φ/Ψ/Ω tensor field onto polygon vertices to compose a deterministic glyph stream; includes the hash-whitened 53→32 bridge  
  `backend/interdependent_lib/zfae/gonal_inscription.py`
- **`inference`** — a0(ZFAE) inference engine — native deterministic symbolic/state engine; no LLM dependency; returns {assistantText, nextSnapshot, trace}  
  `backend/interdependent_lib/zfae/inference.py`
- **`long_memory`** — a0 long-term memory canon — folds the repo's living spec (every MODULE_BUILD block) into a cached deterministic summary the ZFAE engine carries on every inference, so the agent "queries itself"  
  `backend/interdependent_lib/zfae/long_memory.py`
- **`morphology`** — morphological depth-ladder for the ZFAE three-core gonal inscription — two typed primitive gonals (BoneGonal=omega/structural, RootGonal=phi/content) composed by the carrier-LCM operator (UCNS multiply) into the derived psi=word layer; psi is NOT stored, it is lcm(phi,omega) recomputed at every rung; decomposition is scaffolded but GATED behind the multiply_left_cancellative proof  
  `backend/interdependent_lib/zfae/morphology.py`
- **`native_tools`** — deterministic native tool-use — maps a raw prompt to at most one built-in tool call (fetch_url / web_search / living_spec_lookup) using pure rule-based detection so the a0(zfae) native engine can trigger a tool mid-thought without any LLM; the selection is reproducible and the result is summarised into a compact deterministic line folded back into the native reply  
  `backend/interdependent_lib/zfae/native_tools.py`
- **`overrides`** — PendingOverride dataclass + lifecycle helpers for sentinel halt-and-override; backed by MongoDB pending_overrides_col  
  `backend/interdependent_lib/zfae/overrides.py`
- **`runtime`** — ZFAERuntime — dispatches teacher_assisted vs zfae_native; never silently substitutes teacher output as native inference; carries reply_source + teacher_called + zfae_weights_updated flags  
  `backend/interdependent_lib/zfae/runtime.py`
- **`sentinel_eval`** — per-event evaluator for the 13 sentinels — returns a Verdict13 from agent character-sheet modes/weights + the raw event payload; pure, deterministic, never raises on user input. S4 (safety) and S12 (reversibility) cliffs are currently INTERIM string-match against an additive marker set — bypassable by paraphrase; semantic detection is deferred to the pen-test/classifier track. hmmm: cliff broadening is additive-only; do not shrink the marker set.  
  `backend/interdependent_lib/zfae/sentinel_eval.py`
- **`sentinel_modes`** — per-agent sentinel mode resolution — observe/flag/off — with canonical defaults (7 flag + 6 observe + 0 off; flags = S1 S2 S3 S4 S8 S9 S12)  
  `backend/interdependent_lib/zfae/sentinel_modes.py`
- **`sentinel_weights`** — per-agent sentinel weight resolution — default 0.90 attention budget distributed across 13 sentinels; user-editable; under-budget reverts to inference channel  
  `backend/interdependent_lib/zfae/sentinel_weights.py`
- **`sentinels`** — the 13 canonical sentinels per ZFAE core view — verbatim job descriptions; 6 cliff/structural flag + 7 slope observe by default; halt-and-override authority when in flag mode  
  `backend/interdependent_lib/zfae/sentinels.py`
- **`teacher`** — TeacherClient — invokes a configured teacher model via the BYOK provider REGISTRY; emits training records; never substitutes its output as native zfae inference  
  `backend/interdependent_lib/zfae/teacher.py`
- **`trainer`** — ZFAELearner — multi-seed (rank>1) teacher distillation; each step updates all 157 seeds of a round-robin core toward the teacher d=53 signature with per-seed modulation, producing a reducible post-update residual loss that lets training unlock native readiness  
  `backend/interdependent_lib/zfae/trainer.py`
- **`weight_init`** — deterministic seed init for fresh ZFAE weights; three cores phi/psi/omega each shape (157, 53, 7, 7); per-agent reproducible  
  `backend/interdependent_lib/zfae/weight_init.py`
- **`weights`** — A0ZFAEWeightBank — three-core (phi, psi, omega) safetensors load/save, per-core checkpoint digest, training-step counter, seeds-touched tracking; exposes canonical 1_223_187 scalar count  
  `backend/interdependent_lib/zfae/weights.py`
- **`zfae`** — a0(ZFAE) — the inference provider, not an agent label. Exposes A0ZFAEInferenceEngine (native deterministic), plus the legacy ZFAEAgent persona for backward-compat with prior PCNAEngine wiring  
  `backend/interdependent_lib/zfae/__init__.py`

### PCEA — prime-circular encryption substrate · 6

Prime-circular bijective base encryption over the first 53 primes, keyed by the previous state. The 'this-state / last-state' cross-cut kernel is what binds one inference tick to the next and seeds the decoder's deterministic generation.

- **`cipher`** — PCEA core cipher — prime-circular bijective encrypt/decrypt where each state element is recoded in bijective base-p (p the i-th of the first 53 primes) and circularly shifted by key digits derived from the previous state, so the transform is keyed entirely by last_state and is exactly invertible  
  `backend/interdependent_lib/pcea/cipher.py`
- **`codec`** — bijective base-p codec — encodes an integer into digits drawn from {1..p} (the bijective numeration that has no leading-zero ambiguity) and back, plus the key-digit stream PCEA shifts by; this is the reversible number representation the cipher operates on  
  `backend/interdependent_lib/pcea/codec.py`
- **`instance`** — stateful PCEA instance — auto-advances last_state per call  
  `backend/interdependent_lib/pcea/instance.py`
- **`kernel`** — PCEA cross-cut — "this state, last state" kernel runtime encryption operating on Tensor payloads at any layer of the layered model  
  `backend/interdependent_lib/pcea/kernel.py`
- **`pcea`** — PCEA — prime-circular bijective base encryption over the first 53 primes, keyed by the previous state (the 'this-state / last-state' cross-cut); the substrate that binds one inference tick to the next and seeds the decoder's deterministic generation  
  `backend/interdependent_lib/pcea/__init__.py`
- **`primes`** — the first 53 primes — the fixed prime circle PCEA indexes into, one prime per state position, defining the per-digit modulus for the bijective base-p codec  
  `backend/interdependent_lib/pcea/primes.py`

### PTCA — the seeds layer · 10

The seed stratum of the layered model: prime-indexed tensors and the 'seed-as-tensor' projection upward. The current implementation is the pre-stratified flat shape; the canon Fiq→Circle→Seed rebuild against prime_core is tracked as future work.

- **`constants`** — canon PTCA composition counts — synced from The-Interdependency/PTCA/prime_core/constants.py  
  `backend/interdependent_lib/ptca/constants.py`
- **`core`** — PTCA Core — N PTCA Seeds (N=157 canon for Φ/Ψ/Ω; tunable for Θ/Σ) plus aggregate-as-tensor projection upward; param count is N × 7 × 7 × 53  
  `backend/interdependent_lib/ptca/core.py`
- **`exchange`** — deterministic prime-circular state-exchange protocol — advances a PTCA state against a counterpart using the prime circle so two engines can hand state back and forth reproducibly, with no randomness and a verifiable round-trip  
  `backend/interdependent_lib/ptca/exchange.py`
- **`instance`** — PTCA engine — binds the canon stratified [N,7,7,53] PrimeTensor with sentinel channels + lineage hashing  
  `backend/interdependent_lib/ptca/instance.py`
- **`primes`** — prime generator + first-N prime cache (default capacity 200, supports PTCA N=157)  
  `backend/interdependent_lib/ptca/primes.py`
- **`provenance`** — deterministic SHA-256 provenance hashing for tensor ops + lineage chains  
  `backend/interdependent_lib/ptca/provenance.py`
- **`ptca`** — seeds-layer wrapper — re-exports current PTCAInstance plus prime utilities (canon stratified prime_core rebuild pending)  
  `backend/interdependent_lib/ptca/__init__.py`
- **`seed`** — PTCA Seed — 7 PCTA circles on a {7/3} heptagram with a UCNS opaque-host shape and an aggregate "seed-as-tensor" projection upward  
  `backend/interdependent_lib/ptca/seed.py`
- **`sentinels`** — tagged signal lanes with priority ordering — SentinelChannel + SentinelMessage  
  `backend/interdependent_lib/ptca/sentinels.py`
- **`tensor`** — canon stratified prime-indexed tensor — shape [N,7,7,53] (seed × circle × tensor × payload); the Fiq→Circle→Seed model from prime_core, N×7×7×53 leaves (407,729 for N=157) matching PTCA prime_core PARAM_COUNT  
  `backend/interdependent_lib/ptca/tensor.py`

### PCTA — the circle layer · 2

Seven PCNA tensors arranged on a {7/2} heptagram, wrapped in a UCNS structural mirror, with an aggregate 'circle-as-tensor' projection into the next layer.

- **`circle`** — PCTA Circle — 7 PCNA tensors on a {7/2} heptagram with a UCNS structural mirror and an aggregate "circle-as-tensor" projection upward  
  `backend/interdependent_lib/pcta/circle.py`
- **`pcta`** — PCTA — circle layer of the layered model; 7 PCNA tensors arranged on a {7/2} heptagram, wrapped in a UCNS structural mirror  
  `backend/interdependent_lib/pcta/__init__.py`

### PCNA — six-ring inference engine · 9

The simplified six-ring engine (Φ Ψ Ω Θ Σ Ε): three 157-prime cores plus scalar ring signals, dual prime-ring memory (LT/ST), phase modulation, and a substrate-signature observer. The full 61-seed canon topology rebuild is tracked as future work.

- **`edcm`** — Energy Dissonance Circuit Model — CM/DA/DRIFT/DVG/INT/TBF per-tick scoring (canon directives pending wiring)  
  `backend/interdependent_lib/pcna/edcm.py`
- **`group`** — "all seven together is a tensor" — aggregate composition op that lifts 7 Tensors to 1 Tensor (the 8th referent, the projection upward into the next layer)  
  `backend/interdependent_lib/pcna/group.py`
- **`memory_core`** — dual prime-ring memory — LT N=19, ST N=17, plus volatile sub-agent caches  
  `backend/interdependent_lib/pcna/memory_core.py`
- **`pcna`** — six-ring inference engine (Φ Ψ Ω Θ Σ Ε) — current impl is simplified; canon topology (61 seeds, six scored rings + Σ observer) rebuild pending  
  `backend/interdependent_lib/pcna/__init__.py`
- **`pcna`** — current PCNAEngine impl — three 157-prime cores + six scalar ring signals (canon target is full 61-seed topology + tensor rings)  
  `backend/interdependent_lib/pcna/pcna.py`
- **`sigma`** — substrate signature encoder — deterministic blake2b digest + band mapping (canon Σ is N=41 observer ring; current impl is scalar shim)  
  `backend/interdependent_lib/pcna/sigma.py`
- **`tensor`** — leaf Tensor — d=53 scalar payload, deterministic from a (seed, label) pair; the substrate of the layered (PCNA leaf → PCTA circle → PTCA seed → core) model  
  `backend/interdependent_lib/pcna/tensor.py`
- **`theta`** — phase-modulation ring — bounded sinusoidal map over 7 phase bands (canon Θ is N=29 microkernel gate; pending tensor lift)  
  `backend/interdependent_lib/pcna/theta.py`
- **`zeta`** — zeta-injection ring — harmonic LT/ST/SUB memory mix + alpha-echo resonance  
  `backend/interdependent_lib/pcna/zeta.py`

### Network — canonical PCNA binder · 9

The top-level binder that assembles the rings on the layered substrate, advances ticks with the PCEA cross-cut between heartbeats, sources the Σ host-integrity observer for tamper-evidence, and hosts the private carrier disk behind the Θ microkernel.

- **`_theta_private_loader`** — loads the canon CarrierDisk from Θ's private path; raises CarrierDiskUnavailable if not configured; NEVER falls back  
  `backend/interdependent_lib/network/_theta_private_loader.py`
- **`coherence`** — EDCM-style coherence scoring — weights each scored ring's aggregate energy, sums to a total; tracks Σ digest drift as tamper signal (pen-test resistance)  
  `backend/interdependent_lib/network/coherence.py`
- **`engine`** — NetworkEngine — top-level binder for the canonical PCNA inference engine; holds rings, tick state, tamper watcher; supports per-ring N override for tests  
  `backend/interdependent_lib/network/engine.py`
- **`network`** — canonical PCNA inference engine — 5 rings (Φ Ψ Ω Θ Σ) + 2 memory rings on the layered substrate, with PCEA cross-cut and Σ host-integrity observer  
  `backend/interdependent_lib/network/__init__.py`
- **`propagate`** — tick advancement — runs one heartbeat across all rings, applies PCEA `kernel_step` cross-cut between ticks, holds last-state keys  
  `backend/interdependent_lib/network/propagate.py`
- **`rings`** — ring assembly — builds a PTCA Core per RingSpec; Σ ring uses host-integrity-derived tensors; supports per-ring N override and lazy construction  
  `backend/interdependent_lib/network/rings.py`
- **`sigma_source`** — Σ ring data source — read-only host-integrity digest over OS files + installed program manifests; provides tamper-evidence baseline (pen-test resistance)  
  `backend/interdependent_lib/network/sigma_source.py`
- **`theta_microkernel`** — Θ microkernel — hosts the canon carrier disk via private loader; public callers get CarrierDisk or CarrierDiskUnavailable, never inline canon material  
  `backend/interdependent_lib/network/theta_microkernel.py`
- **`topology`** — ring topology spec — names, per-ring N (Φ Ψ Ω 157, Θ 29, Σ 53, MemL 19, MemS 17), heptagram routing slots (lock-step avoidance via unique step+direction), ring weights for coherence scoring  
  `backend/interdependent_lib/network/topology.py`

### FIQ — audited motion & sentinels · 8

The boundary law for audited motion between strata: the smallest auditable gate, the flux equation that meters it, the 3/5/7 tick schedule, the nine base sentinels plus R0 orchestration root, and an append-only, hash-chained audit log mirrored to MongoDB and verifiable end-to-end.

- **`audit`** — append-only JSONL fiq audit log at /app/storage/fiq_audit/YYYY-MM-DD.jsonl + MongoDB mirror; prev_hash chain verifiable end-to-end  
  `backend/interdependent_lib/fiq/audit.py`
- **`events`** — FIQ_TRANSFER / FIQ_BUFFERED / FIQ_BLOCKED event dataclasses; blake2b prev_hash chain  
  `backend/interdependent_lib/fiq/events.py`
- **`ficks`** — ficks — gradient term D_r(Φ_a − Φ_b) in the fiq flux equation; named after Fick's law of diffusion; resolves "tics-per-tok" framing as the gradient of fiq tics per LLM token  
  `backend/interdependent_lib/fiq/ficks.py`
- **`fiq`** — fiq motion canon — boundary law for audited motion between PCNA/PCTA/PTCA strata; tick schedule (3/5/7); χ indicators; FIQ_TRANSFER/BUFFERED/BLOCKED events; sentinels S1-S9, R0, fiques_time  
  `backend/interdependent_lib/fiq/__init__.py`
- **`gate`** — FiqGate — the smallest auditable boundary gate r = (a, b, S, mode); not motion, the law that permits/blocks/meters motion  
  `backend/interdependent_lib/fiq/gate.py`
- **`motion`** — core fiq flux equation F = χ_route · χ_audit · χ_support · χ_attention · P_ab · D_r(Φ_a − Φ_b); pure functions  
  `backend/interdependent_lib/fiq/motion.py`
- **`sentinels`** — 9 sentinels (S1-S9) + R0 orchestration root + fiques_time probe; each enforces a χ indicator family or governs an outbound policy  
  `backend/interdependent_lib/fiq/sentinels.py`
- **`tick_schedule`** — ψ/φ/ω consciousness-prime tick constants (3/5/7); orthogonal stratum + core attention axes; logical default with optional real-time toggle  
  `backend/interdependent_lib/fiq/tick_schedule.py`

### Gonal — the 157-gonal carrier · 11

The structural carrier: public invariants (face, chirality, class tags, adjacency, bones) over a 157-position polygon, a position-reflection mirror, and a three-gonal registry (default / mirror / private) that resolves an agent's per-core triplet. Private disk material is only ever loaded behind the Θ microkernel, never inline.

- **`adjacency`** — hard invariants on the carrier — no L-L adjacent, no N-N adjacent; works against any CarrierDisk implementation  
  `backend/interdependent_lib/gonal/adjacency.py`
- **`bones`** — face-crossing detection over a bone's constituent positions; measurable structural property, not a violation  
  `backend/interdependent_lib/gonal/bones.py`
- **`carrier`** — 157-gonal carrier — public structural invariants (face, chirality, class tags, adjacency, bones); private disk material loaded only via theta_microkernel  
  `backend/interdependent_lib/gonal/__init__.py`
- **`classes`** — public type-class enumeration (L literal, N aggregate, P, X) for the 157 carrier slots — the distinction between literal-type positions and aggregate-slot positions that the adjacency and face invariants are defined over  
  `backend/interdependent_lib/gonal/classes.py`
- **`disk_protocol`** — CarrierDisk Protocol — what any disk implementation (public fixture or private canon) must provide; CarrierDiskUnavailable error type  
  `backend/interdependent_lib/gonal/disk_protocol.py`
- **`faces`** — face + chirality + adjacency formulas over the 157-gonal carrier; no disk material  
  `backend/interdependent_lib/gonal/faces.py`
- **`gonal`** — builds and validates a gonal character carrier arrangement from a declarative spec (user-provided canonical module)  
  `backend/interdependent_lib/gonal/gonal.py`
- **`lifted_path`** — lossless lifted text traversal over the 157-gonal carrier — encode_text_path lifts a string to an ordered, strictly-monotonic path on the universal cover (vertex = pos mod 157); a repeated character costs a full 157-step revolution; SPACE is the seam at ORIGIN (vertex 0); the digit "0" is an ordinary glyph vertex; decode_text_path is the exact inverse (decode(encode(text)) == text over the carrier alphabet)  
  `backend/interdependent_lib/gonal/lifted_path.py`
- **`mirror`** — position-reflection mirror of a gonal arrangement across the diameter through position 0 — an involution (mirror_of(mirror_of(x)) == x) that inverts upper and lower arcs while preserving every hard adjacency invariant (no L-L / N-N adjacency survives the reflection)  
  `backend/interdependent_lib/gonal/mirror.py`
- **`public_fixture`** — public fixture disk generator — binary-order rule per user spec; deterministic, committable, satisfies hard invariants, NOT the canon  
  `backend/interdependent_lib/gonal/public_fixture.py`
- **`registry`** — three-gonal registry — default (EXAMPLE_157), mirror (mirror_of default), private (per-agent built via build_gonal from spec); resolves an agent's per-core gonal triplet  
  `backend/interdependent_lib/gonal/registry.py`

### AIMMH — multi-model orchestration · 2

Pure-async orchestration patterns over a single ``call_fn(model_id, messages)`` — single, fan-out, daisy-chain, synthesize, and council — that power the cross-vendor chat carousel.

- **`aimmh`** — AIMMH — async multi-model orchestration over a single call_fn(model_id, messages) abstraction; the five patterns (single, fan-out, daisy-chain, synthesize, council) are what let the workspace compare or compose frontier models on one prompt without coupling to any vendor SDK  
  `backend/interdependent_lib/aimmh/__init__.py`
- **`patterns`** — pure-async multi-model orchestration patterns over call_fn(model_id, messages)  
  `backend/interdependent_lib/aimmh/patterns.py`

### Tools & MCP · 8

A sentinel-gated tool layer: an in-process registry whose every invocation is evaluated by the 13 sentinels (a cliff halts and raises a pending override), built-in native tools, user-registered webhook tools (HMAC-signed), a provider-agnostic agentic tool-use loop, an outbound MCP relay, and a0p exposed inbound as an MCP server.

- **`agent_loop`** — provider-agnostic agentic tool-use loop over raw HTTP (BYOK) — normalizes OpenAI/xAI Chat Completions, Anthropic Messages, and Gemini generateContent function-calling into one multi-step loop; advertises tool JSON schema, detects model tool calls, runs an injected executor (sentinel-gated), threads tool results back, and loops until a final answer or max_iters; the network poster is injectable so the loop is fully unit-testable without live keys  
  `backend/tools/agent_loop.py`
- **`builtin`** — register the built-in native tools — living_spec_lookup, vault_get_key, fetch_url, web_search; each one declares its JSON Schema and is sentinel-gated automatically by the registry's invoke  
  `backend/tools/builtin.py`
- **`gated_invoke`** — per-tool-call sentinel gate — evaluates the 13 sentinels against the tool name + serialized params, halts on any flag (creates a PendingOverride and emits zfae_override_created), only proceeds when no flag (or when caller supplied an approved override_id); emits zfae_tool_call + zfae_tool_result FIQ events on every invocation  
  `backend/tools/gated_invoke.py`
- **`mcp_relay`** — relay tool invocations to external MCP servers registered per user — Streamable HTTP JSON-RPC client (Model Context Protocol over HTTP) with bearer-token auth; outbound only, the server-side surface lives in tools.mcp_server  
  `backend/tools/mcp_relay.py`
- **`mcp_server`** — expose a0p AS an MCP server — JSON-RPC 2.0 over HTTP at /api/mcp; methods: initialize, tools/list, tools/call (sentinel-gated), resources/list (living-spec modules), resources/read; bearer-token authenticated against a per-user MCP_PUBLISH_TOKEN  
  `backend/tools/mcp_server.py`
- **`registry`** — in-process Tool registry + invocation surface — Tool, ToolError, register, lookup, list_tools, invoke; every invocation routes through the sentinel evaluator (gated_invoke) so cliff-mode S4/S12 etc. can halt before any side effect; tools may be native (python callable), webhook (user-registered URL with HMAC), or mcp (relayed to a registered MCP server)  
  `backend/tools/registry.py`
- **`tools`** — tools subpackage entry — re-exports the registry public surface and triggers register_builtins() so native tools are available immediately on import  
  `backend/tools/__init__.py`
- **`webhook`** — invoke user-registered webhook tools — POSTs the JSON params to the user's URL with an HMAC-SHA256 signature header (X-A0P-Signature) so the user can verify the call came from a0p  
  `backend/tools/webhook.py`

### Skills · 3

A per-user and global skill catalog with jaccard overlap detection, plus a one-way sync that pulls canonical skills from The-Interdependency/skill-lib on GitHub.

- **`registry`** — per-user + global skill catalog with overlap detection — Skill schema (name, description, prompt_template, tool_bindings[], sentinel_overrides{}, scope_tokens[], logic_set_tokens[], source); jaccard-similarity overlap check against existing skills warns the user when a candidate skill shares logic+scope with one already in the catalog  
  `backend/skills/registry.py`
- **`skills`** — skills subpackage entry — re-exports registry + sync helpers  
  `backend/skills/__init__.py`
- **`sync`** — pulls canonical skills from The-Interdependency/skill-lib GitHub repo — fetches the index.json, validates each entry, upserts global skills (owner_user_id=None); reverse direction (publish-back) is reserved for skills marked as publishable=True  
  `backend/skills/sync.py`

### a0p_skills — documentation-as-code runners · 8

This project's own msdmd skill executors: they parse and validate every MODULE_BUILD / CONTRACTS / BOUNDARIES / CAPABILITIES block and the single-line RATIOS declaration, run each contract's ``call:`` path, and gate on coverage, drift, and placement. The same runners power the Inspector page.

- **`a0p_skills`** — this project's three msdmd skill executors — msdmd / test-build / meta-module-build  
  `backend/a0p_skills/__init__.py`
- **`boundaries_runner`** — risk-boundary-build skill executor — validates BOUNDARIES blocks against canon schema; reports gaps + hmmm  
  `backend/a0p_skills/boundaries_runner.py`
- **`capabilities_runner`** — cap-build skill executor — parses CAPABILITIES blocks, builds capability map, flags duplicates/hmmm/gaps  
  `backend/a0p_skills/capabilities_runner.py`
- **`contracts`** — executable test functions referenced by CONTRACTS `call:` paths across the repo  
  `backend/a0p_skills/contracts.py`
- **`frontend_module_build_runner`** — walks /app/frontend/src/**/*.{js,jsx,ts,tsx} and validates each module has a MODULE_BUILD block; reports COVERED / MISSING / INVALID per file  
  `backend/a0p_skills/frontend_module_build_runner.py`
- **`module_build_runner`** — meta-module-build skill executor — validates MODULE_BUILD schema + gap report  
  `backend/a0p_skills/module_build_runner.py`
- **`ratios_runner`** — ratios skill executor — recomputes loc_comments/imports_exports/calls_definitions and gates on drift + first/last-line placement of the single-line RATIOS declaration  
  `backend/a0p_skills/ratios_runner.py`
- **`test_build_runner`** — test-build skill executor — imports each CONTRACTS `call:` and runs it  
  `backend/a0p_skills/test_build_runner.py`

### msdmd — the canon parser · 3

The pure-stdlib block parser and single-line RATIOS reader, synced from the upstream skill-lib, plus the legacy coverage runner.

- **`_msdmd`** — this project's msdmd application — parser + back-compat runner (canonical executors live in a0p_skills)  
  `backend/interdependent_lib/_msdmd/__init__.py`
- **`parser`** — canonical msdmd block parser + single-line RATIOS reader (loc_comments/imports_exports/calls_definitions on first & last line)  
  `backend/interdependent_lib/_msdmd/parser.py`
- **`runner`** — msdmd CAPABILITIES coverage runner (deprecated in favour of skills.module_build_runner)  
  `backend/interdependent_lib/_msdmd/runner.py`

### interdependent_lib — meta-package · 2

The umbrella package that exposes the pcea / ptca / pcna / aimmh / zfae substrata.

- **`interdependent_lib`** — meta-package exposing pcea, ptca, pcna, aimmh, zfae submodules  
  `backend/interdependent_lib/__init__.py`
- **`ucns_bridge`** — thin A0-safe wrapper around the ucns package — will route through ucns.a0_safe when v1.0 ships on PyPI  
  `backend/interdependent_lib/ucns_bridge.py`

### Frontend — pages · 17

The routed screens: Workspace (chat + audit tape + override modal), Agents, Sentinels, Overrides, Inspector, Inventory, Key & Custom-key vaults, Env Vault, Drafts, Skills, Tools, MCP, Training Room, Living Spec, plus the public splash and auth screens.

- **`AgentsPage`** — agent CRUD — list every instance with zfae metrics, create via CharacterSheetForm, edit existing sheet, archive/delete  
  `frontend/src/pages/AgentsPage.jsx`
- **`CustomKeysPage`** — user-owned developer key vault — name + value (Fernet-encrypted at rest) + kind + label; supports rotation (PUT same name) and reveal (decrypt on demand); for GitHub PATs, GCP service accounts, AWS access keys, anything non-LLM  
  `frontend/src/pages/CustomKeysPage.jsx`
- **`DraftsPage`** — local prompt drafts — list / create / edit / delete; persists via /api/drafts  
  `frontend/src/pages/DraftsPage.jsx`
- **`InspectorPage`** — live inspector for PCNA/PTCA/PCEA skills + msdmd compliance reports (capabilities / module-build / contracts coverage); heartbeat ping  
  `frontend/src/pages/InspectorPage.jsx`
- **`InventoryPage`** — discovered model inventory across providers (openai, anthropic, gemini, xai) — populated from /api/models/inventory; each row has a "create agent" action that instantiates a teacher-assisted a0(zfae) agent bound to that model and opens it in the workspace  
  `frontend/src/pages/InventoryPage.jsx`
- **`KeyVaultPage`** — BYOK key vault — list, upsert (Fernet-encrypted), delete BYOK provider keys (OpenAI/Anthropic/Gemini/XAI)  
  `frontend/src/pages/KeyVaultPage.jsx`
- **`LivingSpecPage`** — renders every msdmd block parsed live from the repo — grouped by module_kind, searchable, expandable per module to show MODULE_BUILD / BOUNDARIES / CAPABILITIES / CONTRACTS / RATIOS in full  
  `frontend/src/pages/LivingSpecPage.jsx`
- **`LoginPage`** — tabbed sign-in / sign-up screen — username or email + ≥16-char passphrase (show/hide toggle) + Emergent Google + GitHub OAuth; auto-resumes the user's intended route after auth  
  `frontend/src/pages/LoginPage.jsx`
- **`MCPPage`** — Model Context Protocol surface — (a) inbound: shows the user's publish token + URL so external Claude Desktop / Cursor / etc. can connect to a0p as an MCP server; (b) outbound: lets the user register external MCP servers (GitHub MCP, Slack MCP, Postgres MCP, ...) and refreshes their tool catalogs into the user's tool registry  
  `frontend/src/pages/MCPPage.jsx`
- **`OverridesPage`** — queue of pending sentinel overrides; approve (with justification) or reject; expired overrides housekeeping; shows flagged sentinels + raw request snippet  
  `frontend/src/pages/OverridesPage.jsx`
- **`SentinelsPage`** — view the 13-sentinel canon + edit per-agent sentinel modes (observe/flag/off) and weights for a selected agent  
  `frontend/src/pages/SentinelsPage.jsx`
- **`SkillsPage`** — skill catalog browser + authoring form with live overlap warning before save (jaccard ≥0.6 over scope ∪ logic tokens against existing user+global skills); admin-style sync button pulls global skills from The-Interdependency/skill-lib  
  `frontend/src/pages/SkillsPage.jsx`
- **`SplashPage`** — public landing — "changes constant. refinements welcome." manifesto + Sign in / Sign up CTAs + email-of-record (wayseer@interdependentway.org); shows demo-mode notice for unauthenticated visitors  
  `frontend/src/pages/SplashPage.jsx`
- **`ToolsPage`** — lists every native + user-webhook + MCP-relay tool the current user can invoke; allows registering new user-webhook tools and invoking any tool with arbitrary JSON params; surfaces sentinel halts as override prompts  
  `frontend/src/pages/ToolsPage.jsx`
- **`TrainingRoom`** — multi-teacher distillation room — pick an agent, select TWO OR MORE teacher models (from the live inventory or custom ids), enter a batch of prompts (one per line), and run POST /api/instances/{id}/train so the a0(zfae) echo learns one distill step per (prompt × model); renders a live metrics ribbon + per-step results table  
  `frontend/src/pages/TrainingRoom.jsx`
- **`VaultPage`** — per-site multi-account env vault — list, reveal (decrypts on demand), upsert, delete  
  `frontend/src/pages/VaultPage.jsx`
- **`WorkspacePage`** — chat workspace bound to one agent instance; sends prompts through /api/chat/instance/{id}; renders per-turn sentinel verdict ribbon; intercepts HTTP 202 sentinel-halts and opens an OverrideModal that resumes the same prompt with override_id on approval  
  `frontend/src/pages/WorkspacePage.jsx`

### Frontend — components · 7

Reusable presentational pieces: the live FIQ audit tape, the fully-editable character-sheet form, the sentinel verdict ribbon, the override modal, the navigation shell, and the Markdown+LaTeX renderer.

- **`AuditTape`** — live polling FIQ-chain tape for the active agent — surfaces tool_call, sentinel_verdict, chat_reply, override_created events with their hash chain (prev_hash → this_hash) so the user can watch chain-of-thought / tool invocations as they happen; collapsible; verifies chain integrity client-side  
  `frontend/src/components/AuditTape.jsx`
- **`CharacterSheetForm`** — fully-editable character-sheet form for an Agent — name, mode (5-lattice), models, system_prompt, persona, live tools_allowed multi-select (fetched from /api/tools with a custom-name fallback), memory seeds (long/short term), teacher_context_template, tags, boundary declarations, native-readiness thresholds, gonal assignment; structural engine dicts (edcm/ring_n_override/heptagram_overrides/px_resolution) are intentionally NOT exposed (engine-owned); emits onSubmit(sheet)  
  `frontend/src/components/CharacterSheetForm.jsx`
- **`MarkdownView`** — render Markdown + GFM tables + LaTeX (incl. arxiv \\(...\\) and \\[...\\] forms) via react-markdown + remark-math + rehype-katex  
  `frontend/src/components/MarkdownView.jsx`
- **`OverrideModal`** — modal that surfaces a pending sentinel-override and asks the user to approve (with justification) or reject (with reason); destructive cliff overrides require typed confirmation  
  `frontend/src/components/OverrideModal.jsx`
- **`Panel`** — shared presentational primitives — Panel section, Pill badge, Stat metric tile, AsciiLoader progress indicator  
  `frontend/src/components/Panel.jsx`
- **`SentinelVerdictRibbon`** — render the 13-sentinel verdict as a horizontal pill ribbon; hover shows full verdict row; click toggles details panel  
  `frontend/src/components/SentinelVerdictRibbon.jsx`
- **`Shell`** — left-rail navigation shell with 9 routes (Workspace, Agents, Sentinels, Overrides, Inspector, Inventory, Key Vault, Env Vault, Drafts) and donation CTA  
  `frontend/src/components/Shell.jsx`

### Frontend — libraries · 4

The axios REST clients for every API surface, the auth context / ProtectedRoute, and the client-side sentinel metadata helpers.

- **`api`** — axios-based REST client for every /api endpoint — health, BYOK keys, env vault, inventory, sessions, drafts, skill reports, fanout/daisy/synthesize chat, inspector, agents+slugs, instances CRUD, chat/instance, sentinels canon+modes+weights, overrides queue, gonals, usage  
  `frontend/src/lib/api.js`
- **`api_tools`** — axios client for the tools / mcp servers / skills REST surface — list/register/invoke tools, MCP server CRUD with refresh, skills CRUD with overlap check, skill-lib sync, MCP publish token  
  `frontend/src/lib/api_tools.js`
- **`auth`** — AuthContext + useAuth hook + ProtectedRoute — manages JWT-cookie session, exposes user/loading/login/register/logout/refresh, redirects unauthenticated traffic to /login while keeping the splash & login routes public  
  `frontend/src/lib/auth.jsx`
- **`sentinels`** — client-side helpers + canonical metadata for the 13 sentinels and the 6 lattice modes, plus the canonical agent-name composer (a0(<energy>)<auditor>, owner-namespaced); pure, no I/O  
  `frontend/src/lib/sentinels.js`

### Frontend — root · 1

The top-level router that wires the AuthProvider, public routes, and protected routes.

- **`App`** — top-level router with AuthProvider — public routes (/, /login, /register, /spec) and protected routes (/workspace, /agents, /sentinels, /overrides, /inspector, /inventory, /keys, /custom-keys, /vault, /drafts)  
  `frontend/src/App.js`

### Tests · 10

Pytest and end-to-end regression suites covering the tool-use loop, the Training Room distillation, the three-core sentinel pipeline, and the live API.

- **`backend_test`** — end-to-end backend regression suite — covers /api/health, BYOK keys CRUD with encryption-at-rest masking, and chat session flows; intended to be executed by the testing-agent harness against the live preview ingress  
  `backend/tests/backend_test.py`
- **`conftest`** — pytest configuration — enables pytest-asyncio plugin in auto mode for the backend test suite  
  `backend/tests/conftest.py`
- **`test_lifted_path`** — pytest round-trip coverage for the lossless lifted traversal over the  
  `backend/tests/test_lifted_path.py`
- **`test_morphology_ladder`** — pytest coverage for the morphological depth-ladder — typed gonal primitives  
  `backend/tests/test_morphology_ladder.py`
- **`test_security`** — security regression suite — Fernet at-rest encryption round-trip + masking,  
  `backend/tests/test_security.py`
- **`test_tool_use_loop`** — pytest coverage for the cross-provider tool-use loop (run_tool_loop), the  
  `backend/tests/test_tool_use_loop.py`
- **`test_training_room`** — pytest for ZFAERuntime.train_multi — multi-teacher distillation runs one  
  `backend/tests/test_training_room.py`
- **`test_zfae_api_sentinels`** — integration tests for the ZFAE three-core + sentinel halt-and-override pipeline, hitting the live FastAPI service via REACT_APP_BACKEND_URL — Tests 1..8 from the review batch  
  `backend/tests/test_zfae_api_sentinels.py`
- **`test_zfae_gonal_inscription`** — regression for ZFAE Route A — PrivateGonal determinism, 53→32 whitening bridge, engine PCEA-digest + non-flat tensors, gonal-seed safetensors persistence  
  `backend/tests/test_zfae_gonal_inscription.py`
- **`test_zfae_three_core_sentinels`** — pytest regression suite for the 3-core (Φ/Ψ/Ω) weight bank, trainer round-robin, sentinel evaluator cliffs/slopes, native readiness gate, FIQ hash-chain emit, and PendingOverride lifecycle  
  `backend/tests/test_zfae_three_core_sentinels.py`

## Module index by kind

| kind | count | modules |
|---|---|---|
| adapter | 12 | `_theta_private_loader`, `anthropic_provider`, `base`, `gemini_provider`, `mcp_relay`, `openai_provider`, `providers`, `sigma_source`, `teacher`, `ucns_bridge`, `webhook`, `xai_provider` |
| client | 2 | `api`, `api_tools` |
| engine | 62 | `_decoder`, `_intent`, `_parser`, `_transition`, `adjacency`, `agent_loop`, `aimmh`, `bones`, `builtin`, `carrier`, `cipher`, `circle`, `codec`, `coherence`, `core`, `edcm`, `engine`, `exchange`, `ficks`, `fiq`, `gated_invoke`, `gonal`, `gonal_inscription`, `group`, `inference`, `instance`, `instance`, `kernel`, `lifted_path`, `memory_core`, `mirror`, `morphology`, `motion`, `native_tools`, `network`, `patterns`, `pcea`, `pcna`, `pcna`, `pcta`, `propagate`, `provenance`, `ptca`, `registry`, `registry`, `rings`, `runtime`, `seed`, `sentinel_eval`, `sentinels`, `sentinels`, `sentinels`, `sigma`, `tensor`, `tensor`, `theta`, `theta_microkernel`, `trainer`, `weight_init`, `weights`, `zeta`, `zfae` |
| experiment | 3 | `contracts`, `public_fixture`, `test_zfae_gonal_inscription` |
| route | 7 | `api_tools_mcp_skills`, `app_settings`, `extensions`, `mcp_server`, `routes`, `routes`, `server` |
| schema | 15 | `classes`, `closed_tokens`, `constants`, `disk_protocol`, `events`, `faces`, `gate`, `models`, `primes`, `primes`, `schema`, `sentinel_modes`, `sentinel_weights`, `tick_schedule`, `topology` |
| service | 15 | `agents`, `archive`, `audit`, `crypto_vault`, `db`, `fiq_emit`, `living_spec`, `long_memory`, `overrides`, `readme_writer`, `registry`, `skills`, `store`, `sync`, `tools` |
| skill | 11 | `_msdmd`, `a0p_skills`, `boundaries_runner`, `capabilities_runner`, `frontend_module_build_runner`, `interdependent_lib`, `module_build_runner`, `parser`, `ratios_runner`, `runner`, `test_build_runner` |
| test | 9 | `backend_test`, `conftest`, `test_lifted_path`, `test_morphology_ladder`, `test_security`, `test_tool_use_loop`, `test_training_room`, `test_zfae_api_sentinels`, `test_zfae_three_core_sentinels` |
| ui_component | 7 | `AuditTape`, `CharacterSheetForm`, `MarkdownView`, `OverrideModal`, `Panel`, `SentinelVerdictRibbon`, `Shell` |
| ui_lib | 2 | `auth`, `sentinels` |
| ui_page | 17 | `AgentsPage`, `CustomKeysPage`, `DraftsPage`, `InspectorPage`, `InventoryPage`, `KeyVaultPage`, `LivingSpecPage`, `LoginPage`, `MCPPage`, `OverridesPage`, `SentinelsPage`, `SkillsPage`, `SplashPage`, `ToolsPage`, `TrainingRoom`, `VaultPage`, `WorkspacePage` |
| ui_root | 1 | `App` |
| worker | 1 | `traffic_log` |

