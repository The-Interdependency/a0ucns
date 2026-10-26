# AIMMH Hub — Product Requirements Document

## Original Problem Statement
Build a multi-model AI hub using `aimmh_lib`, with isolated model instances, nested orchestration patterns, FastAPI endpoints, and a mobile-first tabbed UI covering registry, model/group instantiation, runs, responses, and chat/synthesis workflows.

## Current Product Shape
The application is now a full-stack AIMMH workspace with:
- persistent isolated model instances
- nested groups and staged orchestration runs
- direct same-prompt multi-instance chat
- selected-response synthesis
- registry + provider verification tools
- Stripe-backed pricing tiers and Hall of Makers flows
- a mobile-first tabbed orchestration UI

## Architecture
- **Frontend:** React, React Router, Tailwind CSS, Shadcn UI, Sonner
- **Backend:** FastAPI, Pydantic, MongoDB via motor
- **Core orchestration library:** local `/app/aimmh_lib`
- **Payments:** Stripe via `/api/v2/payments`
- **Auth:** JWT-based application auth

## Primary Routes
- `/auth` — login and registration
- `/chat` — AIMMH hub workspace
- `/settings` — registry and key management
- `/pricing` — pricing tiers and checkout entry
- `/makers` — public Hall of Makers page

## Implemented Backend Features
- [x] `/api/v1/hub/instances` create/list/update/archive/unarchive/history
- [x] `/api/v1/hub/instances/{instance_id}` delete support for archived instances only
- [x] `/api/v1/hub/groups` nested group management
- [x] `/api/v1/hub/runs` orchestration runs across `fan_out`, `daisy_chain`, `room_all`, `room_synthesized`, `council`, and `roleplay`
- [x] `/api/v1/hub/chat/prompts` direct multi-instance chat
- [x] `/api/v1/hub/chat/synthesize` selected-response synthesis batches
- [x] `/api/v1/registry` developer/model registry with website metadata and verification endpoints
- [x] `/api/v2/payments` pricing catalog, checkout, summary, and Hall of Makers support

## Implemented Frontend Features
- [x] README-style AIMMH splash screen
- [x] Mobile-first tabbed workspace: Registry, Instantiation, Runs, Responses, Chat & Synthesis
- [x] Instance creation/edit/archive flows
- [x] Group creation/edit/archive flows
- [x] Run builder and response workspace
- [x] Prompt-indexed chat responses
- [x] Shared synthesis basket across chat and responses
- [x] Response actions: thumbs up/down, copy, share
- [x] Response formatting preserved via markdown rendering
- [x] Response pane controls/gestures for pane switching and font zoom
- [x] Per-instance archive/delete UX: archive button on cards, undo archive + delete for archived cards
- [x] Bulk instance controls: select-all, archive selected, undo archive selected, delete archived selected
- [x] Response workspace controls: per-response archive/undo, show archived toggle, select-all responses
- [x] Compare popout modal for side-by-side review of 2+ selected responses
- [x] Chat recipients select-all toggle in Chat & Synthesis tab
- [x] Pricing and Hall of Makers pages

## Latest Verified Fixes — 2026-03-28
- [x] Resolved the blocking Chat & Synthesis usability issue: instances now reliably appear after tab switching because the tab interaction itself is reliable
- [x] Reworked hub tab navigation into a responsive grid so long tab labels no longer clip or behave inconsistently
- [x] Added auto-scroll on tab change in `AimmhHubPage.jsx` so switching from a scrolled tab lands users at the correct content anchor
- [x] Added stronger `data-testid` coverage for hub tabs, instance creation, prompt batches, synthesis selection, and synthesis outputs
- [x] Expanded `data-testid` coverage across header actions, group management, run builder controls, run inventory, responses controls, response panes, and carousel controls
- [x] Exposed `hub_prompt_id` and `hub_synthesis_batch_id` through instance history responses in `backend/models/hub.py`
- [x] Curated the universal-key registry to only supported models for OpenAI, Anthropic, and Google
- [x] Added automatic reconciliation so existing user registries are brought back to the curated universal-key model set
- [x] Added registry UI labeling so universal-key-compatible developers and models are visibly marked
- [x] Added backend guardrails preventing unsupported model additions or removals for universal-key-managed developers

## Latest Verified Fixes — 2026-03-29
- [x] Added archived-instance delete endpoint with archive-before-delete guardrail in `backend/routes/v1_hub.py`
- [x] Added instance card actions so every card exposes archive flow, with archived cards showing undo archive + delete
- [x] Added bulk instance controls with select-all plus batch archive/restore/delete actions
- [x] Added response-level archive controls in both stack and pane/carousel views, with show archived filter
- [x] Added select-all responses control and compare popout modal for multi-response side-by-side analysis
- [x] Added recipient select-all control in Chat & Synthesis direct chat recipients list
- [x] Refreshed curated Universal Key model IDs for Anthropic/Google in `backend/services/llm.py` to remove deprecated 3.5/1.5 IDs causing verify/auth failures
- [x] Simplified workspace layout to splash-first flow: splash screen appears briefly, then only top tab selector + current tab content are shown (no persistent README/header chrome)
- [x] Deployment hardening: cleaned corrupted root `.gitignore` and removed environment-file ignore patterns (`*.env`, `*.env.*`) to prevent production deployment config omissions

## Latest Verified Fixes — 2026-04-02
- [x] Added backend readiness endpoint `GET /api/ready` (Mongo ping check; returns 503 when not ready)
- [x] Added backend liveness endpoint `GET /api/health` for simple startup/health probes
- [x] Kept existing `/api/v1/health` intact; readiness/liveness checks verified via curl on preview URL
- [x] Added AI visitor instruction endpoints: `GET /api/ai-instructions`, `GET /api/v1/ai-instructions`, and public text guide at `/ai-instructions.txt`
- [x] Added in-app hybrid AI/Human guidance: splash summary + per-tab guide panel with persistent top-shell “Help for AI” toggle
- [x] Added first-visit guide memory via localStorage key `aimmh-ai-guide-seen-v1`
- [x] Stripe hardening: corrected checkout webhook URL target to `/api/payments/webhook/stripe` in `backend/routes/payments_v2.py`
- [x] Restored in-workspace pricing access after header simplification by adding top-shell `Pricing` button (`data-testid="hub-open-pricing-button"`) linking to `/pricing`
- [x] Added safe Stripe diagnostics endpoint `GET /api/payments/stripe/mode` (auth required) returning only `{ stripe_mode, key_present }` without exposing secret key material
- [x] Hardened Google OAuth callback handling: switched redirect target to `/auth/google`, added callback support for both query/hash `session_id`, and graceful handling for OAuth `error` / invalid-state responses (no raw callback dead-end)
- [x] Tightened workspace tabs to single-row layout (`hub-tabs-row-single-line`) with compact labels for consistent one-line rendering
- [x] Fixed Runs/Rooms numeric inputs so users can clear/delete values while editing; defaults now normalize on blur and payload coercion remains valid on execute
- [x] Added stronger editable ghost-label behavior for run-stage numeric fields using explicit placeholder hints (e.g., default values visible when empty)
- [x] Improved two-finger response-pane gestures: clearer pinch/spread zoom detection, gesture-type locking, larger safe font-scale range (0.85–1.9), and reduced accidental pane switching during zoom
- [x] Security hardening: moved frontend auth from `localStorage` token persistence to secure cookie-first flow (`access_token` HttpOnly cookie set on login/register/google session)
- [x] Backend auth updated to accept JWT from `access_token` cookie in addition to header/session cookie paths
- [x] Removed localStorage token reads from API clients (`hubApi`, `paymentsApi`, `registryApi`) and chat advanced/synthesis fetch calls
- [x] Chat context hardened for unauthenticated state (no background 401 thread fetch spam on `/auth`)
- [x] Restored explicit logout UX button in hub top shell (`hub-logout-button`) and verified end-to-end logout routing
- [x] Hook dependency quality pass for reported legacy pages (`SettingsPage.js`, `ConsolePage.js`, `ChatPage.js`) with stable callbacks/effects
- [x] Backend complexity reduction started in `routes/chat.py`: decomposed streaming flow into helpers (`_validate_chat_request`, `_ensure_conversation_record`, `_create_context_log`, `_persist_base_user_message`, `_build_messages_context`, `_resolve_stream_iterator`, `_stream_chat_response`, `_handle_chat_error`)
- [x] Continued backend decomposition in `routes/agent_zero.py`: extracted ingestion pipeline helpers (`_load_ingest_conversation_and_messages`, `_resolve_ingest_constraints`, `_resolve_ingest_metadata`, `_build_ingest_payload`, `_post_to_a0`) and synthesis helpers (`_normalize_selected_message_ids`, `_normalize_target_models`, `_fetch_synthesis_source_messages`, `_build_synthesis_prompt_message`)
- [x] Ensured Agent Zero route wiring is active in server bootstrap (`server.py` includes `agent_zero_router`)
- [x] Test secret hardening batch: replaced hardcoded test passwords/API-key literals across backend test suites with env-driven shared constants in `backend/tests/test_credentials.py`
- [x] Undefined-variable audit across backend routes/services completed via lint sweep; cleaned remaining route lint blocker in `routes/v1_edcm.py`
- [x] Frontend modularization pass: split `HubResponsesPanel.jsx` into focused components `ResponsesToolbar.jsx` and `ResponsesComparePopout.jsx` while preserving all existing test IDs and behavior
- [x] Frontend modularization pass: split `ConsolePage.js` context tab into `ConsoleLogViewer.jsx` and `ConsoleContextEditor.jsx` components while preserving existing selectors/actions
- [x] Route wiring hardening from regression test: ensured `/console` route is registered in frontend router and backend console router is mounted in `server.py`
- [x] Frontend modularization pass: split `ServiceAccountManager.js` into focused components `ServiceAccountCreateForm.js`, `ServiceAccountList.js`, and `ServiceAccountDetails.js`
- [x] Settings integration hardened: `SettingsPageV2.jsx` now exposes Service Accounts tab with full create/issue/revoke flow verified
- [x] Hub UX update: tab naming shifted to **Response Synthesis** and synthesis queue is now first-class in responses workspace (`SynthesisQueuePanel`) with running token/cost totals
- [x] Chat compare redesign: implemented OpenAI-style two-slot response comparator (`ChatResponseComparator`) with lock-by-model behavior and overflow carousel placement controls
- [x] Registry redesign: replaced card-heavy view with collapsible tree (`RegistryTreeNode`) showing **Provider → Key → Models** branches and per-model default request JSON
- [x] Added canonical backend model-defaults endpoint `GET /api/v1/registry/defaults` (used by frontend registry tree with copy payload controls)
- [x] Backend persistence foundation: added `GET/PUT/DELETE /api/v1/hub/state/{state_key}` for user-scoped workspace state drafts
- [x] Keystroke autosave (backend-backed, silent UX): chat prompt draft + run-builder draft now persist with debounce and restore on reload/tab switching
- [x] Synthesis queue persistence moved to backend state (`synthesis-queue-global`) and restored on workspace reload

## Verified Testing Status
- [x] Frontend end-to-end synthesis workflow passed in preview
- [x] Tab switching reliability passed from a scrolled instantiation state into Chat & Synthesis
- [x] Expanded hub control test-id coverage passed frontend validation with no layout or click-target regressions
- [x] Backend metadata exposure passed for both direct chat and synthesis history messages
- [x] Universal-key registry UI passed frontend validation: correct curated models shown, unsupported models removed, labels present, no visual regressions
- [x] Universal-key registry API passed backend validation: curated model sets returned, unsupported add/remove/delete operations rejected cleanly

## Important File References
- `/app/frontend/src/pages/AimmhHubPage.jsx`
- `/app/frontend/src/hooks/useHubWorkspace.js`
- `/app/frontend/src/components/hub/HubTabsNav.jsx`
- `/app/frontend/src/components/hub/HubMultiChatPanel.jsx`
- `/app/frontend/src/components/hub/HubInstancesPanel.jsx`
- `/app/frontend/src/components/settings/RegistryManager.jsx`
- `/app/frontend/src/components/settings/RegistryDeveloperCard.jsx`
- `/app/backend/models/hub.py`
- `/app/backend/routes/registry.py`
- `/app/backend/routes/v1_hub.py`
- `/app/backend/routes/v1_a0.py`
- `/app/backend/routes/v1_analysis.py`
- `/app/backend/services/hub_chat.py`
- `/app/backend/services/hub_synthesis.py`
- `/app/backend/services/llm.py`
- `/app/backend/services/hub_store.py`

## Prioritized Backlog

### P0 — Resolved
- [x] Chat & Synthesis tab rendering / usability blocker
- [x] Instance history metadata exposure for chat and synthesis
- [x] Universal-key registry cleanup and protection rules

### P1 — Next
- [ ] Deployment/release pass when requested
- [ ] Optional modularization pass for `AimmhHubPage.jsx` and `useHubWorkspace.js`
- [ ] Saved workflow/templates for favorite orchestration setups

### P2 — Important Enhancements
- [x] Mobile response gestures and font scaling refinements (pinch/spread zoom + pane swipe)
- [ ] Save and reuse orchestration workflows
- [ ] Drag-and-drop stage reordering in the runs builder
- [ ] Richer per-instance thread drill-down/history inspection

### P3 — Future Ideas
- [ ] More explicit loading/progress states for long-running syntheses
- [ ] Sharable run/synthesis exports
- [ ] Analytics for prompt, instance, and synthesis usage

## Notes for Next Agent
- Use `frontend/.env` `REACT_APP_BACKEND_URL` as the preview source of truth
- The current synthesis workflow is working in preview after the tab-navigation fix
- If a future report says instances are missing from Chat & Synthesis, first verify the tab actually changed and the page scrolled to the tab anchor
- OpenAI / Anthropic / Google registry entries are now intentionally curated to universal-key-compatible models only; do not reintroduce unsupported models unless universal-key support changes and is re-verified
