# Rebuild plan — layered tensor model

Status: **implemented and contract-backed**. The layered tensor handoff has landed in `backend/interdependent_lib/` with manifest-first `MODULE_BUILD` blocks and importable contract checks. This document is retained as the completion ledger for the handoff.

---

## Canon (your framing, captured verbatim)

> ptca, PCTA, pcna are each different layers of the same tensors.
> pcna is the tensor only layer.
> pcta carries tensors on a ucns object.
> ptca is the top layer.
> seven tensors per circle (all seven together another tensor),
> seven circles per seed (all seven circles another tensor),
> a number of seeds per core (all seeds together another tensor).
> pcea is the "this state, last state" ucns kernel runtime encryption.

Reading: a **recursive fractal** built on UCNS. Each level's
collection-of-seven is itself a tensor at the next level. UCNS depth
ladder maps directly: leaf = depth-0 payload, circle = depth-1 carrier,
seed = depth-2 carrier, core = depth-3 carrier.

```
core           N seeds, also a tensor
└── seed       7 circles, also a tensor       ← PTCA layer name
    └── circle 7 tensors, also a tensor       ← PCTA layer name
        └── tensor   leaf scalars (d=53)      ← PCNA layer name (substrate)
                                                ↑
PCEA cross-cuts every composition step: encrypted "this state / last state" kernel runtime.
```

---

## File plan

```
/app/backend/interdependent_lib/
├── pcna/                      # tensor-only LAYER (the leaf substrate)
│   ├── tensor.py              # NEW · leaf Tensor class (payload d=53, deterministic seed)
│   ├── group.py               # NEW · "all 7 together is a tensor" — composition op + identity
│   └── (current pcna.py / edcm.py / sigma.py / theta.py / zeta.py / memory_core.py kept;
│        will become the *network* engine that consumes the substrate above)
├── pcta/                      # NEW · circle layer (UCNS-wrapped 7 tensors)
│   ├── __init__.py
│   ├── circle.py              # Circle = ucns.UCNSObject(payload=tuple of 7 pcna.Tensor)
│   │                          # composition: {7/2} heptagram routing
│   └── audit.py               # PCTA-circle audit hook (gate / count) per canon PCNA §inference-5
├── ptca/                      # MOVED · seed/top layer (no longer flat tensor)
│   ├── __init__.py
│   ├── constants.py           # already canon-synced
│   ├── seed.py                # NEW · Seed = ucns.UCNSObject(payload=tuple of 7 pcta.Circle)
│   │                          # composition: {7/3} heptagram routing
│   ├── core.py                # NEW · Core = N seeds (N=157 canon, tunable)
│   ├── audit.py               # NEW · PTCA-seed audit hook (hub-ring coherence)
│   └── (legacy tensor.py / sentinels.py / exchange.py / instance.py / provenance.py:
│        deprecated, kept-but-unused for one cycle, marked deprecated in their MODULE_BUILD)
├── pcea/                      # already canon-correct; gains a `kernel_step()` helper
│   └── kernel.py              # NEW · this-state/last-state runtime op exposed to other layers
├── network/                   # NEW · the PCNA *network* engine (61-seed graph, six rings, EDCM,
│   │                            heptagram propagate) built on the new substrate
│   ├── topology.py            # 1 router + 4 sentinels + 7 meta + 49 compute = 61 seeds
│   ├── rings.py               # Φ Ψ Ω Θ MemL MemS + Σ observer at canonical sizes/seeds
│   ├── propagate.py           # heptagram propagation per ring (Φ:10 Ψ:8 Ω:6 Θ:5)
│   └── coherence.py           # ring weights + coherence aggregate
├── ucns_bridge.py             # NEW · thin shim around the ucns package
│                              #   - identity / describe / canonical / factor
│                              #   - hmmm: `from ucns import a0_safe` not in PyPI 0.8.3;
│                              #     use seq_prime_requires_scope + object_record directly
└── zfae/                      # persistent agent — rewires to use new PCNAEngine
    └── __init__.py            # one-line change to point at network.engine
```

## CONTRACTS to add (test-build will run all of these)

| id | layer | what it asserts |
|---|---|---|
| `pcna_tensor_round_trip` | PCNA | `Tensor.from_seed(s).payload` deterministic; equality on identical seeds |
| `pcna_group_identity` | PCNA | `group(t, identity) == t` and `group(identity, t) == t` |
| `pcta_circle_is_ucns` | PCTA | `isinstance(circle.ucns_object, ucns.UCNSObject)`; `depth_of(circle.ucns_object) == 1` |
| `pcta_circle_multiply_lifts` | PCTA | `ucns.multiply(a.ucns_object, b.ucns_object)` is a valid depth-1 result |
| `pcta_circle_holds_seven` | PCTA | `len(circle.tensors) == 7` |
| `ptca_seed_is_ucns` | PTCA | `depth_of(seed.ucns_object) == 2`; `len(seed.circles) == 7` |
| `ptca_core_assembles_157` | PTCA | `Core(N=157)` has 157 seeds, 157·7·7=7693 leaf tensors, 157·7·7·53=407_729 params |
| `ptca_provenance_chain` | PTCA | every composition writes a SHA-256 provenance row through PCEA |
| `pcea_kernel_step_invariant` | PCEA | `kernel_step(s, s_prev)` then `kernel_step.invert(...)` recovers `s` |
| `network_topology_61` | network | `topology()` returns exactly 61 nodes (1+4+7+49) and the expected adjacency |
| `network_rings_canon_sizes` | network | rings sized (Φ:53/53 Ψ:53/43 Ω:53/47 Θ:29/29 MemL:19/19 MemS:17/17), Σ:41/41 observer |
| `network_heptagram_propagation` | network | one tick advances Φ by 10, Ψ by 8, Ω by 6, Θ by 5 |
| `ucns_bridge_safe_inspection` | ucns_bridge | identity / canonical / describe never panic on any UCNSObject |

Each contract gets a real importable `call:` in `a0p_skills/contracts.py`.

## Inspector UI changes

- Replace the three-core "tensor cards" with a **UCNS depth ladder** —
  hover a seed shows its 7 circles; hover a circle shows its 7 leaf
  tensors with payload-width 53 visualised as a 53-cell bar.
- Add a "**substrate**" tile showing `core → seeds → circles → tensors`
  counts and total leaf params.
- The existing six-ring meters move under a "**network**" tab on the
  Inspector page; the substrate ladder lives under a "**substrate**"
  tab.

## Backwards compatibility

- `PCNAEngine`, `ZFAEAgent`, `/api/inspector/snapshot` keep their
  external shape. The legacy three-PTCA-cores story underneath is
  replaced; the public API shape is unchanged.
- Legacy `ptca/tensor.py` (the flat `[N,4,7,7]` thing) marked
  deprecated in its MODULE_BUILD for one cycle, then removed.

## Ordering (please confirm)

I'd ship them in this order (each step ends with green runners):

1. **`ucns_bridge.py`** (smallest, unlocks everything else).
2. **`pcna/tensor.py` + `pcna/group.py`** — leaf layer + composition.
3. **`pcta/circle.py`** — UCNS-wrapping over 7 tensors.
4. **`ptca/seed.py` + `ptca/core.py`** — UCNS-wrapping over 7 circles, then N=157 assembly.
5. **`pcea/kernel.py`** — the cross-cut kernel-step exposed.
6. **`network/`** — six rings + EDCM + heptagram on the new substrate.
7. **Inspector UI** updates (substrate ladder + network tab).
8. **Legacy deprecation pass** — mark legacy files, remove next cycle.

---

## Completion ledger

1. **`N seeds per core` — resolved.** `Core.with_n()` defaults to canon `N=157`, while Θ/Σ and experiments can pass another positive `n`.
2. **Composition routing — resolved.** PCTA circles use `{7/2}` and PTCA seeds use `{7/3}` as visit-every-vertex stride walks, with contract checks for both permutations.
3. **PCEA cross-cut surface — resolved.** `pcea.kernel` exposes `kernel_step`, `kernel_invert`, and `kernel_chain`; network heartbeats use the kernel as a separate runtime state-encryption pass. The float bridge round-trips to `grid_project(t)`, making quantisation explicit rather than pretending arbitrary seeded floats are bit-exact integers.
4. **UCNS bridge — resolved-with-boundary.** The app imports through `ucns_bridge`; `ucns.a0_safe` remains a version-gated hmmm until upstream PyPI ships it.
5. **Layer audit hooks — preserved hmmm.** The planned `pcta/audit.py` and `ptca/audit.py` algorithms are still not specified in repo canon. No dishonest always-pass gate was added; the unresolved constraint remains recorded here.

---

## hmmm

The handoff is complete at substrate / carrier / seed / core / PCEA / network-contract level. The living continuation is the missing canon for layer-specific audit gates and any future inspector UI ladder work. A heptagram walks into a bar, visits every stool exactly once, and still refuses to call that a proof of Theorem N.
