# CLAUDE.md — aimmh (AI Multimodel Multimodal Hub)

## What this repo is

aimmh is a multi-model AI hub: a **FastAPI backend** + **React frontend** that lets users send a single prompt to multiple LLMs at once and work with their combined responses (fan-out, synthesis, shared rooms, daisy chains, council, roleplay). The `aimmh_lib/` directory is a standalone, **zero-dependency** Python library extracted from the backend's orchestration patterns — it is what gets published to PyPI as `aimmh-lib`.

- **Languages:** Python 3.11+ (backend + library), JavaScript/JSX (React frontend)
- **Backend:** FastAPI · Motor (async MongoDB) · asyncio · Stripe · Google OAuth + JWT · emergentintegrations
- **Frontend:** React 19 · Create React App via CRACO · Tailwind CSS · Shadcn/Radix UI · React Router 7 · Axios
- **Library:** pure stdlib + asyncio, zero runtime dependencies
- **License:** **MPL-2.0** (see `LICENSE`). Relicensed from MIT to MPL-2.0 — weak copyleft: embed anywhere, but changes to these files must be published. (Earlier history: AGPL-3.0-or-later + commercial, then MIT.)
- **PyPI package:** `aimmh-lib`, version **1.1.0**
- **Repo:** https://github.com/The-Interdependency/aimmh

---

## Repository layout

```
aimmh_lib/            # pip install aimmh-lib — zero-dep async orchestration core (MPL-2.0)
  __init__.py         # public API surface (re-exports from conversations.py)
  conversations.py    # all orchestration logic, ModelResult, CallFn, MultiModelHub, ModelInstance
  adapters.py         # bridge to the backend (make_call_fn); NOT imported by __init__

backend/              # FastAPI service
  server.py           # module-level app = FastAPI(...) (not a factory fn), router wiring, health/AI-instruction endpoints
  config.py           # JWT_SECRET / algorithm / expiry constants
  db.py               # Motor client (reads MONGO_URL, DB_NAME)
  requirements.txt    # pinned backend deps (includes pytest, black, flake8, isort, mypy)
  routes/             # APIRouter modules (auth, agent_zero, v1_a0/edcm/system/analysis/lib/hub/hub_state,
                      #   registry, keys, payments_v2, console; chat/export/payments present but unmounted)
  models/             # Pydantic schemas (hub, hub_chat, hub_state, hub_synthesis, edcm, chat,
                      #   payments, payments_v2, registry, agent_zero, context, lib_models, v1)
  services/           # business logic (llm, edcm, hub_chat/runner/store/synthesis, auth,
                      #   billing_tiers, audit, events, registry_verifier, ai_instructions)
  tests/              # pytest suites (mostly live-server integration tests, see below)

frontend/             # React app (CRACO + Tailwind + Shadcn)
  src/
    pages/            # ChatPage, HubPage, AuthPage, SettingsPage(V2), PricingPage(V2), ...
    components/       # ModelSelector, A0Settings, ui/ (Shadcn primitives)
    contexts/         # AuthContext, ChatContext
    hooks/, lib/      # useHubWorkspace, hubApi, paymentsApi, registryApi, ...
  package.json        # CRA scripts via craco (start/build/test)

tests/                # root pytest package marker (empty __init__.py)
*_test.py, *test*.py  # root-level live-server validation scripts (a0_validation_test.py,
                      #   backend_test.py, backend_validation_test.py, service_account_auth_test.py, ...)
test_reports/         # captured JSON + JUnit XML test artifacts (historical)
memory/               # PRD.md and working notes
.agents/skills/       # repo-local agent skills (meta-module-build, msdmd, test-build)

pyproject.toml        # aimmh-lib packaging (setuptools; excludes backend/ + frontend/)
README.md             # public-facing project README
LICENSE               # MPL-2.0
```

---

## Build / test / lint / run commands

All commands are verified against the current tree. There is **no CI workflow** (`.github/` only holds `FUNDING.yml`) and **no Makefile**.

### Library (`aimmh_lib`)

```bash
pip install -e .            # editable install from repo root
pip install build twine     # (or: pip install -e ".[dev]")
python -m build             # build sdist + wheel into dist/
twine upload dist/*         # publish to PyPI
```

Packaging only includes `aimmh_lib*`; `backend/` and `frontend/` are excluded.

### Backend

```bash
cd backend
pip install -r requirements.txt

# Required env vars
export MONGO_URL="mongodb://localhost:27017"
export DB_NAME="aimmh"
export CORS_ORIGINS="http://localhost:3000"  # REQUIRED — explicit comma-separated origins; server.py raises if unset OR if it contains '*' (wildcard cannot combine with credentialed cookies)
export JWT_SECRET="your-secret"          # REQUIRED — no default; config.py raises at startup if unset
export API_KEY_ENCRYPTION_KEY="..."      # REQUIRED for BYOK key storage — Fernet key (python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"); POST /api/v1/keys returns 503 until set
export EMERGENT_LLM_KEY="..."            # managed LLM access for openai/anthropic/google
export STRIPE_API_KEY="sk_..."           # optional: payments
export AUTH_SERVICE_URL="..."            # optional: external auth service

uvicorn server:app --reload              # run from inside backend/ (imports are flat: routes, services, db)
```

`MONGO_URL` and `DB_NAME` are read at import time in `db.py` (no defaults); `CORS_ORIGINS`
(must be an explicit allowlist, not `*`) and `JWT_SECRET` (no default) are required at startup
in `server.py` / `config.py` — all must be set or the app fails fast. `API_KEY_ENCRYPTION_KEY`
is required only to store BYOK provider keys (`POST /api/v1/keys` returns 503 until it is set);
existing plaintext keys remain readable and are re-encrypted on next save.

API surface is mounted under `/api/...`; the modern surface is versioned under `/api/v1/...`.
`server.py` wires these routers: auth, agent_zero, v1_a0, v1_edcm, v1_system, registry, keys,
v1_analysis, v1_lib, v1_hub, v1_hub_state, **payments_v2**, console. Liveness/readiness:
`/health`, `/api/health`, `/ready`, `/api/ready` (readiness pings MongoDB), plus `/api/v1/health` (from `routes/v1_system.py`, mounted at prefix `/api/v1`). Note: `routes/chat.py`,
`routes/export.py`, and `routes/payments.py` exist in the tree but are **not** mounted in `server.py`.

### Backend tests

`backend/requirements.txt` pins `pytest`. Most suites in `backend/tests/` and the root
`*_test.py` scripts are **integration tests that call a running deployment** via
`REACT_APP_BACKEND_URL` (or a hardcoded preview URL) — they are NOT pure unit tests and
will skip/fail without a live backend.

```bash
cd backend
export REACT_APP_BACKEND_URL="http://localhost:8000"   # point at a running server
python -m pytest tests/                                  # run backend integration suites
```

There is no committed `pytest.ini`/`conftest.py`; `pytest-asyncio` is not pinned, so async
test files rely on plain `requests` against the live URL rather than in-process async fixtures.

### Lint / format (backend, tools are installed via requirements.txt)

```bash
black backend/        # formatter
isort backend/        # import sorting
flake8 backend/       # lint
mypy backend/         # type check
```

### Frontend

```bash
cd frontend
yarn install          # packageManager is yarn 1.22; npm install also works
yarn start            # craco start (dev server)
yarn build            # craco build (production bundle)
yarn test             # craco test (CRA/Jest test runner)
```

The frontend talks to the backend via `REACT_APP_BACKEND_URL` (defaults toward `http://localhost:8000`).

---

## aimmh_lib public API

### Types
- `CallFn` — `async (model_id: str, messages: list[dict]) -> str`. The single abstraction decoupling the library from any backend. On error the call returns a string starting with `[ERROR]`.
- `ModelResult` — dataclass returned by every pattern. Fields: `model`, `content`, `response_time_ms`, `error`, `round_num`, `step_num`, `initiative`, `role`, `slot_idx`. (The field is `model`, not `model_id`.)

### Functional API — pass `call` positionally as the first argument
| Function | Description |
|---|---|
| `fan_out(call, model_ids, messages, ...)` | Parallel call to N models via `asyncio.gather` — the async building block |
| `daisy_chain(call, model_ids, prompt, ...)` | A→B→C sequential; each model sees the previous response |
| `room_all(call, model_ids, prompt, ...)` | All respond, then each sees all, responds again in rounds |
| `room_synthesized(call, model_ids, prompt, synthesis_model, ...)` | Fan-out → synthesizer → next round |
| `council(call, model_ids, prompt, ...)` | Each model synthesizes all responses (incl. its own) in parallel |
| `roleplay(call, player_models, initial_prompt, ...)` | DM-driven roleplay with initiative ordering + reactions |

### Instantiation API (bind `call` once)
- `MultiModelHub(call)` — all six patterns as methods, `call` bound at construction.
- `ModelInstance(call, model_id, system_context=...)` — stateful single model with `.send()`, `.history`, `.clear()`.

### Adapters (explicit import only)
```python
import sys; sys.path.insert(0, "/path/to/aimmh/backend")
from aimmh_lib.adapters import make_call_fn
call = make_call_fn(user={"api_keys": {}})   # uses EMERGENT_LLM_KEY env for managed providers
```
`adapters.py` is intentionally **not** re-exported from `__init__.py` so the default install stays zero-dependency. It requires backend `services/` on `sys.path`.

---

## Architecture & key concepts

- **CallFn is the seam.** The library never imports HTTP/DB code; it only invokes `call(model_id, messages)`. Backends are plugged in via an adapter that satisfies the contract.
- **`slot_contexts`** — a list aligned by index with `model_ids` (or `player_models`), letting the same model appear multiple times with different system prompts. `ModelResult.slot_idx` carries the position back.
- **`step_num == -1`** is a sentinel for synthesis/DM steps that sit between rounds. Filter player responses with `[r for r in results if r.step_num >= 0]`.
- **Backend = thin routing + services.** `server.py` only wires routers and health endpoints; logic lives in `services/` and schemas in `models/`. New endpoints are added as a router module under `routes/` and included in `server.py`.
- **`services/llm.py`** provides `generate_response()` (async generator, streaming) and `DEFAULT_REGISTRY` (model ID → provider mapping). The adapter consumes both.
- **EDCM** = **Energy-Dissonance Circuit Model** (`services/edcm.py`), a deterministic engine computing six metrics over conversation transcripts: CM (Constraint Mismatch), DA (Dissonance Accumulation), DRIFT, DVG (Divergence), INT (Intensity), TBF (Turn Balance Fairness), with 0.80/0.20 alert thresholds.
- **Persistence** is MongoDB via Motor (`db.py`, configured by `MONGO_URL` + `DB_NAME`).

---

## Conventions & gotchas

- **Backend imports are flat** (`from routes.auth import ...`, `from db import client`). Run/uvicorn from inside `backend/`, not the repo root.
- **Env var names matter:** the database uses `MONGO_URL` (not `MONGO_URI`) and `DB_NAME`; Stripe uses `STRIPE_API_KEY`. Do not invent `MONGO_URI`/`STRIPE_SECRET_KEY`.
- **Backend tests are integration tests** against a deployed URL; treat them as smoke/regression checks, not local unit tests.
- **`aimmh_lib` must stay dependency-free.** Anything needing fastapi/motor/emergentintegrations belongs under `[project.optional-dependencies].backend`, never in the core lib.
- **License is MPL-2.0.** Keep license claims consistent across files when editing docs.
- Frontend build uses **CRACO** (`craco.config.js`), not raw `react-scripts`; custom dev/webpack plugins live in `frontend/plugins/`.

---

## Git & contribution workflow

- **Main branch:** `main` (stable; mirrors PyPI for `aimmh_lib`).
- **Feature branches:** `feat/<desc>`, `fix/<desc>`, `docs/<desc>`, and `claude/*` working branches — PR into `main`.
- **Commit style:** Conventional Commits (`feat(aimmh):`, `fix(adapters):`, `docs:`).
- **Author:** Erin Patrick Spencer (wayseer@interdependentway.org).

---

## Agent module-build doctrine

Before adding a new module, route, service, adapter, schema, worker, engine, UI panel,
migration, or experiment, read:

`./.agents/skills/meta-module-build/SKILL.md`

New module work should start with a `MODULE_BUILD` block. Unknown fields must be marked
`hmmm`, not guessed.
