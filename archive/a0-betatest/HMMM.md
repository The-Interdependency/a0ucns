# hmmm — a0p open boundary

> Per the `The-Interdependency` doctrine, every deliverable carries an
> explicit `hmmm` boundary section. This is the project-level one.
> Module-level `hmmm` lives in each module's `MODULE_BUILD` block.

## Architecture (open)

### Layered tensor model — handoff completed

The user's canon framing (confirmed turn 2026-06-02):

```
PCNA  = pure tensor layer (leaves; scalar payloads, d = 53)
PCTA  = tensors-on-UCNS-objects layer
        7 tensors per circle, the circle itself is also a tensor
PTCA  = top / seed layer
        7 circles per seed, the seed itself is also a tensor
core  = N seeds, the core itself is also a tensor
PCEA  = "this state, last state" UCNS kernel runtime encryption
        — cross-cuts every layer
```

Recursive fractal: each layer's whole-of-seven is itself a tensor at
its level. Substrate is UCNS — depth-d objects carry depth-(d-1)
payloads.

The handoff is now implemented under `backend/interdependent_lib/`: PCNA leaf tensors and 7-way aggregation, PCTA circles, PTCA seeds/cores, PCEA kernel-state encryption, and the PCNA network engine. `PCNAEngine` now acts as a compatibility facade over `NetworkEngine`, so legacy inspector/ZFAE callers advance the canonical network handoff without losing their existing response shape. Legacy `ptca/tensor.py` remains for compatibility, but the layered handoff path is the contract-backed path.

### The `9` axis — closed, was misremembered

Canon `prime_core/constants.py` defines `[SEED_COUNT=157,
CIRCLES_PER_SEED=7, TENSORS_PER_CIRCLE=7, TENSOR_DIM=53]`. The
"9-axis" from an earlier design conversation has no presence in the
upstream constants or the corrected layer model. Marking closed.

## UCNS surface (open)

- `ucns >= 1.0` ships `ucns.a0_safe` (the A0-facing inspection facade
  with `identity / describe / canonical / factor`). Pinned in this
  build via `git+https://github.com/The-Interdependency/ucns.git`.
  The PyPI 0.8.3 stable release does **not** ship `a0_safe` yet — when
  it does, switch to a PyPI pin.
- UCNS-A (factorization algebra) is `DEFENDED + ORACLE-COMPLETE` at
  depths the catalogue covers. UCNS-G (metric geometry) is unproven.
  Per `interdependent-lib/docs/handoffs/v2-ucns-metric-geometry.md`:
  *"Theorem N proof status is not transferred by shared name."* Any
  a0p-facing claim that uses geometric coordinates must route through
  the bridge layer, not the algebra.
- `SEQ-PRIME` is absolute only inside `ucns.VERIFIED_DOMAIN_LABELS`.
  A0-facing consumers (this app counts) should consult
  `domain_status_metadata` and treat `SEQ-PRIME` outside verified
  domains as non-absolute.

## Platform / runtime (closed in this turn)

- **Emergent dependency removed.** `emergentintegrations` uninstalled;
  `EmergentProvider` deleted; `EMERGENT_LLM_KEY` removed from `.env`;
  Workspace's "emergent routing" toggles removed. Chat now requires
  the user to supply BYOK keys via the Key Vault.
- Deployment surface: the app still runs on the Emergent preview
  hosting URL (`REACT_APP_BACKEND_URL`), but the *application code* has
  no runtime dependency on Emergent software.

## Skill canon (closed in prior turn)

- `msdmd` parser synced line-for-line from
  `The-Interdependency/skill-lib/msdmd/parsers/universal.py`.
- `meta-module-build` runner — 42/42 covered, 0 gaps, 0 invalid.
- `test-build` runner — 4 contracts, 4 PASS, 0 FAIL, 0 ERROR.

## Rebuild plan (completed ledger)

Single coordinated rebuild against the layered model. Replaces the
"PTCA stratified rebuild" + "PCNA canon-topology rebuild" tasks (those
were mutually exclusive, since they describe the same data at
different layers).

Proposed file layout, manifest-first per the meta-module-build skill:

```
interdependent_lib/
├── pcna/
│   ├── tensor.py        # leaf tensor: scalar payload of width d=53
│   ├── group.py         # "all 7 together is a tensor" — pcna-internal
│   │                    # composition op + identity
│   └── (existing memory_core / edcm / sigma / theta / zeta retained)
├── pcta/
│   ├── circle.py        # Circle = UCNS object carrying 7 PCNA tensors
│   │                    # composition op: {7/2} heptagram
│   └── audit.py         # PCTA-circle audit hooks (gate, count) per
│                        # canon PCNA §inference-step-5
├── ptca/
│   ├── seed.py          # Seed = UCNS object carrying 7 PCTA circles
│   │                    # composition op: {7/3} heptagram
│   ├── core.py          # Core = N seeds (N=157 canon; tunable)
│   ├── constants.py     # SEED_COUNT / CIRCLES_PER_SEED / ... (synced)
│   └── audit.py         # PTCA-seed audit hooks (hub-ring coherence)
└── network/             # canonical PCNA-network engine (61-seed
    │                    # graph, six rings, EDCM, heptagram propagate)
    ├── topology.py
    ├── rings.py
    ├── propagate.py
    └── coherence.py
```

PCEA cross-cuts through `pcea.kernel`: runtime state transitions can be encrypted with `kernel_step` / `kernel_chain`, and network heartbeats use that separate cross-cut instead of hiding encryption inside every aggregate projection.

## Completed order

1. **PCNA `tensor.py`** — leaf tensor, payload arithmetic, group op.
   Contract: round-trip + composition associativity.
2. **PCTA `circle.py`** — UCNS-wrapped circle of 7 tensors. Contract:
   `ucns.a0_safe.identity(circle)` is stable across equivalent
   circles; `multiply(circle_a, circle_b)` lifts to a circle.
3. **PTCA `seed.py`** + `core.py` — UCNS-wrapped seed of 7 circles;
   core assembly of N=157 seeds. Contract: `prime_core` shape +
   provenance hash agreement.
4. **`network/`** — canon PCNA-network engine on the substrate. Six
   rings + Σ observer + EDCM + heptagram propagate. Contract:
   determinism over a fixed input.
5. **Inspector UI** — render the layered structure (was a tensor card,
   now a UCNS-depth ladder).

## PCNA facade handoff (closed in this turn)

- `interdependent_lib.pcna.PCNAEngine` now delegates heartbeat state to the canonical `NetworkEngine`.
- Legacy `ring_signals`, `cores`, memory, EDCM, and ZFAE persona calls remain available for compatibility.
- Contract: `a0p_skills.contracts.pcna_engine_uses_network_handoff_holds`.

## hmmm — still open

- Carrier widening (UCNS `FRONTIER`).
- UCNS-G metric geometry claims.
- Theorem N proof transfer across the prime-quartet boundary.
