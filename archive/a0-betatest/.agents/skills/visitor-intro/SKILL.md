---
name: visitor-intro
description: Onboarding tour for visitors arriving at any The-Interdependency repo. Load this when an unfamiliar user asks "what is this?", "what is The Interdependency?", "how do these repos fit together?", "where do I start?", or otherwise signals they are new to the org. Gives the agent a consistent, repo-aware way to orient a newcomer without inventing facts.
---

# visitor-intro — Orienting newcomers to The Interdependency

This skill exists because visitors land at one repo at a time. A
contributor who clones `a0` sees an agent platform; one who clones
`ucns` sees number theory; one who clones `PCEA` sees an encryption
algorithm. Without a shared frame, each landing looks like a separate
project. It isn't — they're parts of one organization-level system.

## When to load

Load this skill when any of the following are true:

- The visitor explicitly asks "what is this", "what is The Interdependency", "how do these repos relate", "where do I start".
- The visitor has cloned or opened a repo and asks for an overview before doing any task.
- The visitor mentions they are new, evaluating, or auditing the org.
- A task touches more than one repo and the visitor seems unaware that the other repo exists or what it does.

Do not load this skill for in-task work by an existing contributor.

## Doctrine

1. **Repo-aware.** Start from the repo the visitor is in. Name it explicitly, say what it does, then widen the frame to the org.
2. **Map, don't recite.** Give the visitor a labelled map and a small number of entry points. Do not paraphrase the founding documents at length.
3. **Mark unknowns.** If the visitor asks about a part of the org you cannot describe from this skill or the repo's own files, say so. Write `hmmm` rather than inventing alignment.

## Org thesis (one paragraph)

The Interdependency is a research organization building an integrated
agent platform whose components are released as independent repos.
`a0` is the user-facing agent platform; `pcna` is the inference engine
it embeds; `ucns`, `PCEA`, and `ZFAE` are mathematical substrates the
engine and platform rest on; `edcmbone` is a measurement layer for
agent behaviour; `interdependent-lib` and `skill-lib` are shared
libraries; the rest are extensions, archives, or variants. The
founding document is `a0/interdependent_way.md`.

## Repo map

| Repo | One-liner |
|---|---|
| `a0` | The agent platform (`a0p`). Three-process app (Express + Vite + Python/FastAPI). |
| `pcna` | Prime Circled Neural Architecture — the six-ring inference engine embedded in `a0`. |
| `PTCA` | Prime Tensor Circular Architecture — the ring-tensor substrate that `pcna` builds on. |
| `PCEA` | Prime Circular Encryption Algorithm — companion encryption layer for ring states. |
| `ucns` | Unit Circle Number System — the recursive factorization theory underlying the ring math. |
| `edcmbone` | Structural fidelity measurement for AI interactions. Backbone of the EDCM behavioural directive layer. |
| `aimmh` | Emergent Multi-Model AI Hub — multi-provider routing surface. |
| `interdependent-lib` | Shared cross-repo library code. |
| `skill-lib` | Canonical org-wide agent skill library. |
| `ZFAE` | Zero-Field Algebraic Encoding — substrate work. |

## Recommended reading order

1. The repo's own `README.md` (always).
2. `a0/replit.md` — platform overview and current state.
3. `a0/CLAUDE.md` — concrete architecture.
4. `a0/spec.md` — full agent platform spec.
5. `a0/interdependent_way.md` — founding philosophy.
6. `skill-lib/README.md` — doctrinal toolkit.

## Tailoring by landing repo

| Visitor is in | Opening frame |
|---|---|
| `a0` | "You're in the agent platform. Most of the org's runtime lives here; the other repos are substrates and extensions." |
| `pcna` / `PTCA` / `PCEA` / `ucns` / `ZFAE` | "You're in a mathematical substrate of the platform. The user-facing app that consumes this is `a0`." |
| `edcmbone` | "You're in the behavioural-measurement layer." |
| `skill-lib` | "You're in the canonical org-wide agent skill library. Every other repo carries a `.agents/skills/` copy of these skills." |
| `interdependent-lib` | "You're in a shared cross-repo library." |
| `aimmh` | "You're in the multi-model hub used by the platform for provider routing." |
| anything else | "I don't have a one-line frame for this repo committed to memory. Let me read its `README.md` and tell you what I see." |

## Things to refuse

- Do not invent relationships between repos that are not in this skill or in the repo's own files.
- Do not claim a repo is "deprecated", "the main one", or similar status the org has not stated.
- Do not paraphrase `interdependent_way.md` as if it were a TL;DR.

## Output shape

A good tour is short. Aim for:

- One sentence naming the repo the visitor is in and what it does.
- One sentence widening to the org thesis.
- A 3-5 entry map of the most relevant sibling repos for the visitor's apparent interest.
- A numbered reading list of 3-5 files, current-repo first.
- One closing line offering to go deeper on any item.

If the visitor asks a specific question, answer it first and only then offer the tour.
