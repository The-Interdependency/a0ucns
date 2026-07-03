# Multi-Model Hub — a0 API Reference v1.0.2-S9

Base URL: `{DEPLOYMENT_URL}/api`

## Authentication

All endpoints (except `/v1/health` and `/v1/version`) require authentication.

### Human Users
- **JWT Bearer Token**: `Authorization: Bearer {token}`
- Obtain via `POST /api/auth/login` or `POST /api/auth/register`

### Service Accounts (a0)
- **Service Account Token**: `Authorization: Bearer {sat_token}`
- Create service account: `POST /api/auth/service-account/create`
- Get token: `POST /api/auth/service-account/token`

---

## Core Endpoints

### POST /api/v1/a0/prompt
Fan-out to N models simultaneously. Collects all responses.

```json
{
  "message": "Your prompt text",
  "models": ["gpt-4o", "claude-4-sonnet-20250514", "gemini-2.5-pro"],
  "thread_id": null,           // optional, auto-generated if omitted
  "global_context": "",         // prepended to all model calls
  "per_model_context": {        // per-model overrides
    "gpt-4o": {
      "system_message": "You are a coding assistant",
      "role": "expert coder",
      "prompt_modifier": "Respond with code only",
      "temperature": 0.3
    }
  },
  "async_mode": false           // true → returns job_id for polling
}
```

**Response:**
```json
{
  "thread_id": "thr_abc123",
  "responses": [
    {
      "model": "gpt-4o",
      "message_id": "msg_def456",
      "content": "Full response text...",
      "response_time_ms": 1234,
      "error": null
    }
  ],
  "event_ids": ["evt_abc"],
  "provenance": { "ts": "...", "model": "", "build": "v1.0.2-S9" },
  "sentinel_context": { "S5_context": {...}, "S6_identity": {...}, ... }
}
```

### POST /api/v1/a0/prompt/stream
Same request body as `/prompt`. Returns Server-Sent Events (SSE).

**Events:**
- `start`: `{"model": "gpt-4o", "message_id": "msg_...", "thread_id": "thr_..."}`
- `chunk`: `{"model": "gpt-4o", "message_id": "msg_...", "content": "partial text"}`
- `complete`: `{"model": "gpt-4o", "message_id": "msg_...", "response_time_ms": 1234}`

### POST /api/v1/a0/prompt-single
Single model call.

```json
{
  "message": "Your prompt",
  "model": "gpt-4o",
  "thread_id": null,
  "global_context": "",
  "system_message": "Custom system prompt"
}
```

### POST /api/v1/a0/synthesize
Feed responses from one or more models into other models.

```json
{
  "source_message_ids": ["msg_abc", "msg_def"],
  "target_models": ["claude-4-sonnet-20250514"],
  "synthesis_prompt": "Compare and synthesize these AI responses:",
  "thread_id": null
}
```

### POST /api/v1/a0/batch
Sequential prompt chains with configurable rooms.

```json
{
  "steps": [
    {
      "message": "First prompt",
      "models": ["gpt-4o"],
      "room": "shared",
      "wait_for_completion": true,
      "feed_responses_to_next": true
    },
    {
      "message": "Analyze the above",
      "models": ["claude-4-sonnet-20250514", "gemini-2.5-pro"],
      "room": "individual",
      "feed_responses_to_next": false
    }
  ],
  "thread_id": null,
  "async_mode": false
}
```

### GET /api/v1/a0/jobs/{job_id}
Poll async job status.

**Response:**
```json
{
  "job_id": "job_abc",
  "thread_id": "thr_abc",
  "status": "running|completed|failed",
  "responses": [...],
  "event_ids": [...]
}
```

---

## History & Export

### GET /api/v1/a0/history?offset=0&limit=20
List threads with pagination.

### GET /api/v1/a0/thread/{thread_id}
Get all messages in a thread.

### GET /api/v1/a0/export/{thread_id}
Full export: messages + events + snapshot with provenance.

### POST /api/v1/a0/feedback
```json
{
  "message_id": "msg_abc",
  "feedback": "up"  // or "down"
}
```

---

## EDCM (Energy-Dissonance Circuit Model)

### POST /api/v1/edcm/eval
Run EDCM metrics on a thread window.

```json
{
  "thread_id": "thr_abc",
  "goal_text": "Optional goal description",
  "declared_constraints": ["accuracy", "brevity"],
  "context": { "window": { "W": 32 } }
}
```

**Response (EDCMBONE report):**
```json
{
  "thread_id": "thr_abc",
  "metrics": {
    "CM": { "value": 0.3, "range": [0, 1] },
    "DA": { "value": 0.1, "range": [0, 1] },
    "DRIFT": { "value": 0.2, "range": [0, 1] },
    "DVG": { "value": 0.5, "range": [0, 1] },
    "INT": { "value": 0.0, "range": [0, 1] },
    "TBF": { "value": 0.4, "range": [0, 1] }
  },
  "alerts": [],
  "snapshot_id": "snap_abc"
}
```

### GET /api/v1/edcm/metrics/{thread_id}
Get latest EDCM metric snapshots.

### GET /api/v1/edcm/alerts/{thread_id}
Get current alerts for a thread.

---

## Model Registry

### GET /api/v1/models
List all available developers and models (default registry).

### GET /api/v1/registry
Get user's customized registry.

### POST /api/v1/registry/developer
Add a new developer.

```json
{
  "developer_id": "mistral",
  "name": "Mistral AI",
  "auth_type": "openai_compatible",
  "base_url": "https://api.mistral.ai/v1",
  "models": [{ "model_id": "mistral-large-latest" }]
}
```

### POST /api/v1/registry/developer/{developer_id}/model
Add a model to an existing developer.

### DELETE /api/v1/registry/developer/{developer_id}/model/{model_id}
Remove a model.

### DELETE /api/v1/registry/developer/{developer_id}
Remove a developer.

---

## API Keys

### GET /api/v1/keys
List key status for all developers (never returns full keys).

### POST /api/v1/keys
Set an API key for a developer.

```json
{
  "developer_id": "xai",
  "api_key": "xai-..."
}
```

### DELETE /api/v1/keys/{developer_id}
Remove a key (reverts to universal if applicable).

### GET /api/v1/keys/universal/status
Check universal key validity.

---

## System

### GET /api/v1/health
```json
{ "status": "ok", "build": "v1.0.2-S9" }
```

### GET /api/v1/version
```json
{ "version": "v1.0.2-S9", "spec": "spec.md v1.0.2-S9", "components": ["EDCM", "PTCA", "PCNA"] }
```

### GET /api/v1/ptca/schema
Returns the canonical PTCA tensor schema (53-seed, 9 sentinels, 8 phases, 7 heptagram slots).

---

## Default Model Registry

| Developer | Auth | Models |
|-----------|------|--------|
| OpenAI | Emergent | gpt-4o, gpt-4o-mini, gpt-4.1, gpt-4.1-mini, o3, o3-pro, o4-mini, o1 |
| Anthropic | Emergent | claude-4-sonnet-20250514, claude-4-opus-20250514, claude-sonnet-4-5-20250929, claude-haiku-4-5-20251001, claude-3-5-haiku-20241022 |
| Google | Emergent | gemini-2.5-pro, gemini-2.5-flash, gemini-2.0-flash |
| xAI | User Key | grok-4, grok-3, grok-2 |
| DeepSeek | User Key | deepseek-chat (V3), deepseek-reasoner (R1) |
| Perplexity | User Key | sonar-pro, sonar |

Emergent-supported models use the universal key by default. User can override with their own keys via `/api/v1/keys`.
