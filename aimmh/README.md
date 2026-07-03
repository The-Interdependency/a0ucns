# Emergent — Multi-Model AI Hub

[![Live App](https://img.shields.io/badge/live-emergentapp.interdependentway.org-blue)](https://emergentapp.interdependentway.org)
[![PyPI](https://img.shields.io/pypi/v/aimmh-lib)](https://pypi.org/project/aimmh-lib/)
[![License: MPL-2.0](https://img.shields.io/badge/License-MPL--2.0-blue.svg)](LICENSE)

> Chat with GPT, Claude, Gemini, Grok, DeepSeek, and Perplexity **in parallel**.
> Compare, synthesize, and chain their responses — all in one interface.

---

## Try it live

**[emergentapp.interdependentway.org](https://emergentapp.interdependentway.org)**

| Tier | Price | What you get |
|------|-------|--------------|
| **Free** | $0 | 5 instances, 10 runs/month, basic responses and chat |
| **Supporter** | $5/month | 15 instances, 30 runs/month, removes "Made with Emergent" badge, Hall of Makers eligibility, early feature voting, private thank-you channel |
| **Coffee** | $5 one-time | Supporter perks + Hall of Makers eligibility |
| **Builder** | $25 one-time | Supporter perks + Hall of Makers eligibility (Builder tier) |
| **Patron** | $50 one-time | Supporter perks + Hall of Makers eligibility (Patron tier) |
| **Pro** | $19/month or $149/year | Unlimited instances & runs, advanced synthesis, priority support, all supporter perks |
| **Team** | $49/month (3 seats) | Unlimited instances & runs, shared workspace, admin controls, all supporter perks |
| **Team extra seat** | $15/month | Adds 1 extra seat to an existing Team plan |

---

## What is this?

Emergent is a multi-model AI hub that lets you send one prompt to multiple LLMs simultaneously and work with their responses together. Instead of copy-pasting between chat tabs, you get a single interface with color-coded, side-by-side or stacked responses from every model you care about.

Beyond simple fan-out, Emergent supports structured interaction patterns — synthesis (feed multiple responses into one model for analysis), shared rooms (models that see and respond to each other), daisy chains (A→B→C sequential pipelines), council mode, and roleplay scenarios. The EDCM engine analyzes conversation transcripts across six cognitive metrics and surfaces actionable insights.

---

## Interaction Patterns

| Pattern | What it does |
|---------|-------------|
| **Fan-out** | Send one prompt to N models in parallel |
| **Synthesis** | Select responses, send to a synthesis model for analysis |
| **Shared Room (All)** | All models see each other's responses and reply in rounds |
| **Shared Room (Synthesized)** | Responses synthesized first, then drive the next round |
| **Daisy Chain** | Model A → B → C sequentially, each seeing the previous response |
| **Council** | Each model synthesizes all responses including its own |
| **Roleplay** | DM-driven roleplay with initiative ordering and reactions |

---

## Self-hosting

### Backend (FastAPI + MongoDB)

```bash
cd backend
pip install -r requirements.txt

# Required env vars
export MONGO_URI="mongodb://localhost:27017"
export JWT_SECRET="your-secret"
export STRIPE_SECRET_KEY="sk_..."        # optional: for payments
export STRIPE_WEBHOOK_SECRET="whsec_..." # optional: for webhooks

uvicorn server:app --reload
```

### Frontend (React)

```bash
cd frontend
npm install
npm start
```

The frontend expects the backend at `http://localhost:8000` by default.

---

## aimmh-lib — the open-source core

The orchestration patterns are extracted into a standalone, **zero-dependency** Python library.

```bash
pip install aimmh-lib
```

### Functional API

```python
import asyncio
from aimmh_lib import fan_out

async def call_model(model_id: str, messages: list[dict]) -> str:
    # plug in any model backend here
    return f"Response from {model_id}"

async def main():
    results = await fan_out(
        call_fn=call_model,
        model_ids=["gpt-4o", "claude-sonnet-4-6", "gemini-2.0-flash"],
        messages=[{"role": "user", "content": "What is the best programming language?"}],
    )
    for r in results:
        print(f"{r.model_id}: {r.content}")

asyncio.run(main())
```

### Instantiation API

Bind a backend once and call any pattern as a method:

```python
from aimmh_lib import MultiModelHub

hub = MultiModelHub(call_model)

results = await hub.fan_out(["gpt-4o", "claude-sonnet-4-6"], messages)
results = await hub.daisy_chain(["gpt-4o", "claude-sonnet-4-6", "gemini-2.0-flash"], "Explain gravity")
results = await hub.council(["gpt-4o", "claude-sonnet-4-6"], "What is consciousness?")
```

### Stateful single-model conversations

```python
from aimmh_lib import ModelInstance

gpt = ModelInstance(call_model, "gpt-4o", system_context="You are a Socratic tutor.")
r1 = await gpt.send("What is entropy?")
r2 = await gpt.send("Give me an example.")  # history carries over automatically
print(gpt.history)
gpt.clear()  # reset to fresh state
```

All six patterns available: `fan_out`, `daisy_chain`, `room_all`, `room_synthesized`, `council`, `roleplay`.

[PyPI →](https://pypi.org/project/aimmh-lib/)

---

## Tech Stack

**Backend:** FastAPI · Motor (async MongoDB) · asyncio · Stripe · Google OAuth · JWT

**Frontend:** React · Tailwind CSS · Shadcn UI · React Router

**Library:** Pure Python 3.11+ · zero runtime dependencies

---

## Repository Structure

```
aimmh_lib/   # pip install aimmh-lib — zero-dep async orchestration library
backend/     # FastAPI service (auth, multi-model chat, payments, EDCM)
frontend/    # React UI
```

---

## License

This project is licensed under the Mozilla Public License 2.0 (MPL-2.0). See `LICENSE`. Relicensed from MIT to MPL-2.0 — weak copyleft: embed anywhere, but changes to these files must be published. (Earlier history: AGPL-3.0-or-later + commercial, then MIT.)
