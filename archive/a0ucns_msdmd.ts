import { defineMsdmdCollection } from "./.agents/skills/msdmd/collection";

export default defineMsdmdCollection({
  "declarations": [
    {
      "block": "CONTRACTS",
      "fields": {
        "call": "python.tests.contracts.route_gating.test_every_write_route_is_gated",
        "class": "security",
        "given": "every @router.{post,patch,delete,put} handler in",
        "then": "the handler body must reference at least one gating sentinel"
      },
      "file": "archive/python/routes/__init__.py",
      "id": "routes_write_endpoints_gated"
    },
    {
      "block": "CONTRACTS",
      "fields": {
        "call": "python.tests.contracts.billing.test_webhook_replay_is_idempotent",
        "class": "idempotency",
        "given": "same Stripe event id POSTed twice to the webhook (via the",
        "then": "first call returns {received: True}; replay returns"
      },
      "file": "archive/python/routes/billing.py",
      "id": "billing_webhook_replay_idempotent"
    },
    {
      "block": "CONTRACTS",
      "fields": {
        "call": "python.tests.contracts.chat.test_delete_other_owner_404",
        "class": "security",
        "given": "DELETE /api/v1/conversations/{id} with x-user-id != row.user_id",
        "then": "404; the row remains intact for the real owner"
      },
      "file": "archive/python/routes/chat.py",
      "id": "chat_delete_other_owner_404"
    },
    {
      "block": "CONTRACTS",
      "fields": {
        "call": "python.tests.contracts.chat.test_get_other_owner_404",
        "class": "security",
        "given": "GET /api/v1/conversations/{id} with x-user-id != row.user_id",
        "then": "404 (existence non-disclosure, never 403 or 200)"
      },
      "file": "archive/python/routes/chat.py",
      "id": "chat_get_other_owner_404"
    },
    {
      "block": "CONTRACTS",
      "fields": {
        "call": "python.tests.contracts.chat.test_unknown_body_model_400",
        "class": "correctness",
        "given": "POST /api/v1/conversations/{id}/messages with body.model that",
        "then": "400 with a detail naming the unknown id (no silent fallback to"
      },
      "file": "archive/python/routes/chat.py",
      "id": "chat_unknown_body_model_400"
    },
    {
      "block": "CONTRACTS",
      "fields": {
        "call": "python.tests.contracts.energy.test_providers_list_public_read",
        "class": "correctness",
        "given": "GET /api/energy/providers with any signed-in user",
        "then": "200 with a non-empty list of providers, each entry shaped"
      },
      "file": "archive/python/routes/energy.py",
      "id": "energy_providers_list_public_read"
    },
    {
      "block": "CONTRACTS",
      "fields": {
        "call": "python.tests.contracts.energy.test_seed_patch_requires_admin",
        "class": "security",
        "given": "PATCH /api/energy/providers/{id}/seed without x-user-role=admin",
        "then": "403 for every payload shape (enabled, disabled_models,"
      },
      "file": "archive/python/routes/energy.py",
      "id": "energy_seed_patch_admin_only"
    },
    {
      "block": "CONTRACTS",
      "fields": {
        "call": "python.tests.contracts.spawn_executor.test_count_live_for_parent_filters",
        "class": "correctness",
        "given": "two registry entries under different parent_run_ids",
        "then": "count_live_for_parent returns 1 for each parent and 0 for an"
      },
      "file": "archive/python/services/agent_lifecycle.py",
      "id": "agent_lifecycle_count_live_for_parent_filters"
    },
    {
      "block": "CONTRACTS",
      "fields": {
        "call": "python.tests.contracts.spawn_executor.test_registry_is_singleton",
        "class": "correctness",
        "given": "a fresh process boot",
        "then": "routes.agents._sub_agents is the SAME object as"
      },
      "file": "archive/python/services/agent_lifecycle.py",
      "id": "agent_lifecycle_registry_is_singleton"
    },
    {
      "block": "CONTRACTS",
      "fields": {
        "call": "python.tests.contracts.spawn_executor.test_bandit_select_arm_handles_negative_rewards",
        "class": "correctness",
        "given": "every enabled arm has been pulled at least once and all",
        "then": "select_arm() still returns the highest-scoring arm rather"
      },
      "file": "archive/python/services/bandit.py",
      "id": "bandit_select_arm_handles_negative_rewards"
    },
    {
      "block": "CONTRACTS",
      "fields": {
        "call": "python.tests.contracts.transcripts_explainer.test_no_credits_returns_none",
        "class": "pricing",
        "given": "a user with free_remaining=0, paid_remaining=0",
        "then": "consume_explanation_credit returns None (route layer converts"
      },
      "file": "archive/python/services/edcmbone_explainer.py",
      "id": "explainer_402_when_no_credits"
    },
    {
      "block": "CONTRACTS",
      "fields": {
        "call": "python.tests.contracts.transcripts_explainer.test_explainer_call_surfaces_in_learning_summary",
        "class": "correctness",
        "given": "an explainer_call event is emitted by the explainer service",
        "then": "it persists with event='explainer_call' (not silently rewritten"
      },
      "file": "archive/python/services/edcmbone_explainer.py",
      "id": "explainer_call_surfaces_in_learning_summary"
    },
    {
      "block": "CONTRACTS",
      "fields": {
        "call": "python.tests.contracts.transcripts_explainer.test_decrements_free_then_paid",
        "class": "pricing",
        "given": "a user with free_remaining=1, paid_remaining=3",
        "then": "consume_explanation_credit returns 'free' and free_remaining"
      },
      "file": "archive/python/services/edcmbone_explainer.py",
      "id": "explainer_decrements_free_first"
    },
    {
      "block": "CONTRACTS",
      "fields": {
        "call": "python.tests.contracts.transcripts_explainer.test_idempotent_no_double_charge",
        "class": "idempotency",
        "given": "an explanation already exists for (report_id, user_id)",
        "then": "a second explain_report() call returns the cached row, does NOT"
      },
      "file": "archive/python/services/edcmbone_explainer.py",
      "id": "explainer_explanation_is_idempotent"
    },
    {
      "block": "CONTRACTS",
      "fields": {
        "call": "python.tests.contracts.transcripts_explainer.test_refund_after_failure",
        "class": "failure_recovery",
        "given": "a credit was consumed (bucket='paid'), then the model failed",
        "then": "refund_explanation_credit('paid') restores paid_remaining to"
      },
      "file": "archive/python/services/edcmbone_explainer.py",
      "id": "explainer_refund_restores_balance"
    },
    {
      "block": "CONTRACTS",
      "fields": {
        "call": "python.tests.contracts.transcripts_explainer.test_rejects_fabricated_citations",
        "class": "correctness",
        "given": "model output contains citations whose quoted spans do not",
        "then": "_parse_explainer_output drops the fabricated quotes and, if"
      },
      "file": "archive/python/services/edcmbone_explainer.py",
      "id": "explainer_rejects_fabricated_citations"
    },
    {
      "block": "CONTRACTS",
      "fields": {
        "call": "python.tests.contracts.gating.test_allowlist_entries_correspond_to_real_routes",
        "class": "security",
        "given": "every entry in OWNER_OR_PUBLIC_WRITES",
        "then": "the (file, method, path) corresponds to a real"
      },
      "file": "archive/python/services/gating.py",
      "id": "gating_allowlist_entries_are_real_routes"
    },
    {
      "block": "CONTRACTS",
      "fields": {
        "call": "python.tests.contracts.gating.test_every_write_route_is_gated_or_allowlisted",
        "class": "security",
        "given": "every @router.{post,patch,put,delete} in python/routes/",
        "then": "the handler body within ~80 lines either calls a recognized"
      },
      "file": "archive/python/services/gating.py",
      "id": "gating_every_write_route_is_admin_or_allowlisted"
    },
    {
      "block": "CONTRACTS",
      "fields": {
        "call": "python.tests.contracts.gating.test_instrument_mutation_files_have_all_writes_gated",
        "class": "security",
        "given": "every @router.{post,patch,put,delete} inside a",
        "then": "the handler body visibly calls require_admin (or another"
      },
      "file": "archive/python/services/gating.py",
      "id": "gating_instrument_files_all_writes_gated"
    },
    {
      "block": "CONTRACTS",
      "fields": {
        "call": "python.tests.contracts.gating.test_instrument_mutation_files_are_never_allowlisted",
        "class": "security",
        "given": "FORBIDDEN_ALLOWLIST_FILES (agents.py, bandits.py, edcm.py,",
        "then": "no entry in OWNER_OR_PUBLIC_WRITES references any of these files"
      },
      "file": "archive/python/services/gating.py",
      "id": "gating_instrument_files_never_allowlisted"
    },
    {
      "block": "CONTRACTS",
      "fields": {
        "call": "python.tests.contracts.spawn_executor.test_bandit_round_trip",
        "class": "correctness",
        "given": "a parent PCNA with empty bandit_state and the 'bandit' sentinel",
        "then": "_resolve_provider picks an auto-selectable arm onto"
      },
      "file": "archive/python/services/spawn_executor.py",
      "id": "spawn_executor_bandit_round_trip"
    },
    {
      "block": "CONTRACTS",
      "fields": {
        "call": "python.tests.contracts.spawn_executor.test_bandit_skips_human_only",
        "class": "security",
        "given": "a candidate pool containing only a human-only provider id",
        "then": "_resolve_provider raises ValueError \u2014 the cost gate prevents"
      },
      "file": "archive/python/services/spawn_executor.py",
      "id": "spawn_executor_bandit_skips_human_only"
    },
    {
      "block": "CONTRACTS",
      "fields": {
        "call": "python.tests.contracts.spawn_executor.test_bandit_state_round_trips_through_checkpoint",
        "class": "correctness",
        "given": "a bandit arm with a datetime last_pulled field",
        "then": "_arm_to_json / _arm_from_json round-trip cleanly so PCNA's"
      },
      "file": "archive/python/services/spawn_executor.py",
      "id": "spawn_executor_bandit_state_round_trips_through_checkpoint"
    },
    {
      "block": "CONTRACTS",
      "fields": {
        "call": "python.tests.contracts.spawn_executor.test_claim_atomic",
        "class": "idempotency",
        "given": "a single 'running' agent_runs row exists",
        "then": "two concurrent _claim_one_pending() calls succeed once and"
      },
      "file": "archive/python/services/spawn_executor.py",
      "id": "spawn_executor_claim_atomic"
    },
    {
      "block": "CONTRACTS",
      "fields": {
        "call": "python.tests.contracts.spawn_executor.test_concurrent_live_cap",
        "class": "security",
        "given": "20 live registry entries under a single parent_run_id (admin",
        "then": "check_can_spawn raises SpawnCapExceeded with cap='concurrent_live'"
      },
      "file": "archive/python/services/spawn_executor.py",
      "id": "spawn_executor_concurrent_live_cap"
    },
    {
      "block": "CONTRACTS",
      "fields": {
        "call": "python.tests.contracts.spawn_executor.test_heartbeat_advances",
        "class": "correctness",
        "given": "an 'executing' agent_runs row and the _heartbeat_loop running",
        "then": "last_heartbeat_at strictly advances after a few interval ticks;"
      },
      "file": "archive/python/services/spawn_executor.py",
      "id": "spawn_executor_heartbeat_advances"
    },
    {
      "block": "CONTRACTS",
      "fields": {
        "call": "python.tests.contracts.spawn_executor.test_marks_failed_on_exception",
        "class": "correctness",
        "given": "a claimed row whose providers list resolves to an unknown id",
        "then": "_execute_one raises no exception, the row's final status is"
      },
      "file": "archive/python/services/spawn_executor.py",
      "id": "spawn_executor_marks_failed_on_exception"
    },
    {
      "block": "CONTRACTS",
      "fields": {
        "call": "python.tests.contracts.spawn_executor.test_merge_helpers_tolerate_no_pcna",
        "class": "correctness",
        "given": "a missing primary PCNA (cold-start or test bootstrap)",
        "then": "_try_get_primary_pcna returns None and _retire_fork_quietly"
      },
      "file": "archive/python/services/spawn_executor.py",
      "id": "spawn_executor_merge_helpers_tolerate_no_pcna"
    },
    {
      "block": "CONTRACTS",
      "fields": {
        "call": "python.tests.contracts.spawn_executor.test_no_orphan_invariant",
        "class": "correctness",
        "given": "a registry entry whose run_id has no DB row, AND a DB",
        "then": "check_no_orphan_invariant flags both as orphans and reports"
      },
      "file": "archive/python/services/spawn_executor.py",
      "id": "spawn_executor_no_orphan_invariant"
    },
    {
      "block": "CONTRACTS",
      "fields": {
        "call": "python.tests.contracts.spawn_executor.test_resolve_provider_rejects_empty",
        "class": "correctness",
        "given": "an empty list or malformed providers value",
        "then": "_resolve_provider raises ValueError (no silent default-to-active)"
      },
      "file": "archive/python/services/spawn_executor.py",
      "id": "spawn_executor_resolve_provider_rejects_empty"
    },
    {
      "block": "CONTRACTS",
      "fields": {
        "call": "python.tests.contracts.spawn_executor.test_retry_default_none",
        "class": "correctness",
        "given": "retry_policy='none' OR a non-transient exception under",
        "then": "_maybe_schedule_retry returns False \u2014 the failure remains"
      },
      "file": "archive/python/services/spawn_executor.py",
      "id": "spawn_executor_retry_default_none"
    },
    {
      "block": "CONTRACTS",
      "fields": {
        "call": "python.tests.contracts.spawn_executor.test_retry_once_on_transient",
        "class": "correctness",
        "given": "a row with retry_policy='once_on_transient', retry_count=0,",
        "then": "_maybe_schedule_retry returns True, the row goes back to"
      },
      "file": "archive/python/services/spawn_executor.py",
      "id": "spawn_executor_retry_once_on_transient"
    },
    {
      "block": "CONTRACTS",
      "fields": {
        "call": "python.tests.contracts.spawn_executor.test_skips_non_running",
        "class": "correctness",
        "given": "an agent_runs row with status='completed' (or 'failed', 'merged')",
        "then": "_claim_one_pending() does not return it"
      },
      "file": "archive/python/services/spawn_executor.py",
      "id": "spawn_executor_skips_non_running"
    },
    {
      "block": "CONTRACTS",
      "fields": {
        "call": "python.tests.contracts.spawn_executor.test_snapshot_pcna_shape",
        "class": "correctness",
        "given": "a primary-shaped PCNAEngine instance",
        "then": "_snapshot_pcna returns the four delta-tracked floats/ints"
      },
      "file": "archive/python/services/spawn_executor.py",
      "id": "spawn_executor_snapshot_pcna_shape"
    },
    {
      "block": "CONTRACTS",
      "fields": {
        "call": "python.tests.contracts.spawn_executor.test_stale_sweep_marks_worker_lost",
        "class": "correctness",
        "given": "an 'executing' row with last_heartbeat_at older than 2\u00d7 the",
        "then": "_reap_stale_claims marks ONLY the stale row failed/worker_lost;"
      },
      "file": "archive/python/services/spawn_executor.py",
      "id": "spawn_executor_stale_sweep_marks_worker_lost"
    },
    {
      "block": "CONTRACTS",
      "fields": {
        "call": "python.tests.contracts.chat.test_create_anonymous_owner_null",
        "class": "security",
        "given": "POST /api/v1/conversations with no x-user-id header",
        "then": "row lands with user_id=NULL (owner_user_id kwarg defaults to"
      },
      "file": "archive/python/storage/core.py",
      "id": "storage_anonymous_owner_null"
    },
    {
      "block": "CONTRACTS",
      "fields": {
        "call": "python.tests.contracts.chat.test_create_owner_isolation",
        "class": "security",
        "given": "create_conversation called via POST /api/v1/conversations with",
        "then": "stored row.user_id == \"legit\"; smuggled value is dropped by"
      },
      "file": "archive/python/storage/core.py",
      "id": "storage_create_owner_isolation"
    }
  ],
  "edges": [
    {
      "from": "agent_lifecycle_count_live_for_parent_filters",
      "kind": "calls",
      "source_block": "CONTRACTS",
      "source_id": "agent_lifecycle_count_live_for_parent_filters",
      "to": "python.tests.contracts.spawn_executor.test_count_live_for_parent_filters"
    },
    {
      "from": "agent_lifecycle_registry_is_singleton",
      "kind": "calls",
      "source_block": "CONTRACTS",
      "source_id": "agent_lifecycle_registry_is_singleton",
      "to": "python.tests.contracts.spawn_executor.test_registry_is_singleton"
    },
    {
      "from": "bandit_select_arm_handles_negative_rewards",
      "kind": "calls",
      "source_block": "CONTRACTS",
      "source_id": "bandit_select_arm_handles_negative_rewards",
      "to": "python.tests.contracts.spawn_executor.test_bandit_select_arm_handles_negative_rewards"
    },
    {
      "from": "billing_webhook_replay_idempotent",
      "kind": "calls",
      "source_block": "CONTRACTS",
      "source_id": "billing_webhook_replay_idempotent",
      "to": "python.tests.contracts.billing.test_webhook_replay_is_idempotent"
    },
    {
      "from": "chat_delete_other_owner_404",
      "kind": "calls",
      "source_block": "CONTRACTS",
      "source_id": "chat_delete_other_owner_404",
      "to": "python.tests.contracts.chat.test_delete_other_owner_404"
    },
    {
      "from": "chat_get_other_owner_404",
      "kind": "calls",
      "source_block": "CONTRACTS",
      "source_id": "chat_get_other_owner_404",
      "to": "python.tests.contracts.chat.test_get_other_owner_404"
    },
    {
      "from": "chat_unknown_body_model_400",
      "kind": "calls",
      "source_block": "CONTRACTS",
      "source_id": "chat_unknown_body_model_400",
      "to": "python.tests.contracts.chat.test_unknown_body_model_400"
    },
    {
      "from": "energy_providers_list_public_read",
      "kind": "calls",
      "source_block": "CONTRACTS",
      "source_id": "energy_providers_list_public_read",
      "to": "python.tests.contracts.energy.test_providers_list_public_read"
    },
    {
      "from": "energy_seed_patch_admin_only",
      "kind": "calls",
      "source_block": "CONTRACTS",
      "source_id": "energy_seed_patch_admin_only",
      "to": "python.tests.contracts.energy.test_seed_patch_requires_admin"
    },
    {
      "from": "explainer_402_when_no_credits",
      "kind": "calls",
      "source_block": "CONTRACTS",
      "source_id": "explainer_402_when_no_credits",
      "to": "python.tests.contracts.transcripts_explainer.test_no_credits_returns_none"
    },
    {
      "from": "explainer_call_surfaces_in_learning_summary",
      "kind": "calls",
      "source_block": "CONTRACTS",
      "source_id": "explainer_call_surfaces_in_learning_summary",
      "to": "python.tests.contracts.transcripts_explainer.test_explainer_call_surfaces_in_learning_summary"
    },
    {
      "from": "explainer_decrements_free_first",
      "kind": "calls",
      "source_block": "CONTRACTS",
      "source_id": "explainer_decrements_free_first",
      "to": "python.tests.contracts.transcripts_explainer.test_decrements_free_then_paid"
    },
    {
      "from": "explainer_explanation_is_idempotent",
      "kind": "calls",
      "source_block": "CONTRACTS",
      "source_id": "explainer_explanation_is_idempotent",
      "to": "python.tests.contracts.transcripts_explainer.test_idempotent_no_double_charge"
    },
    {
      "from": "explainer_refund_restores_balance",
      "kind": "calls",
      "source_block": "CONTRACTS",
      "source_id": "explainer_refund_restores_balance",
      "to": "python.tests.contracts.transcripts_explainer.test_refund_after_failure"
    },
    {
      "from": "explainer_rejects_fabricated_citations",
      "kind": "calls",
      "source_block": "CONTRACTS",
      "source_id": "explainer_rejects_fabricated_citations",
      "to": "python.tests.contracts.transcripts_explainer.test_rejects_fabricated_citations"
    },
    {
      "from": "gating_allowlist_entries_are_real_routes",
      "kind": "calls",
      "source_block": "CONTRACTS",
      "source_id": "gating_allowlist_entries_are_real_routes",
      "to": "python.tests.contracts.gating.test_allowlist_entries_correspond_to_real_routes"
    },
    {
      "from": "gating_every_write_route_is_admin_or_allowlisted",
      "kind": "calls",
      "source_block": "CONTRACTS",
      "source_id": "gating_every_write_route_is_admin_or_allowlisted",
      "to": "python.tests.contracts.gating.test_every_write_route_is_gated_or_allowlisted"
    },
    {
      "from": "gating_instrument_files_all_writes_gated",
      "kind": "calls",
      "source_block": "CONTRACTS",
      "source_id": "gating_instrument_files_all_writes_gated",
      "to": "python.tests.contracts.gating.test_instrument_mutation_files_have_all_writes_gated"
    },
    {
      "from": "gating_instrument_files_never_allowlisted",
      "kind": "calls",
      "source_block": "CONTRACTS",
      "source_id": "gating_instrument_files_never_allowlisted",
      "to": "python.tests.contracts.gating.test_instrument_mutation_files_are_never_allowlisted"
    },
    {
      "from": "routes_write_endpoints_gated",
      "kind": "calls",
      "source_block": "CONTRACTS",
      "source_id": "routes_write_endpoints_gated",
      "to": "python.tests.contracts.route_gating.test_every_write_route_is_gated"
    },
    {
      "from": "spawn_executor_bandit_round_trip",
      "kind": "calls",
      "source_block": "CONTRACTS",
      "source_id": "spawn_executor_bandit_round_trip",
      "to": "python.tests.contracts.spawn_executor.test_bandit_round_trip"
    },
    {
      "from": "spawn_executor_bandit_skips_human_only",
      "kind": "calls",
      "source_block": "CONTRACTS",
      "source_id": "spawn_executor_bandit_skips_human_only",
      "to": "python.tests.contracts.spawn_executor.test_bandit_skips_human_only"
    },
    {
      "from": "spawn_executor_bandit_state_round_trips_through_checkpoint",
      "kind": "calls",
      "source_block": "CONTRACTS",
      "source_id": "spawn_executor_bandit_state_round_trips_through_checkpoint",
      "to": "python.tests.contracts.spawn_executor.test_bandit_state_round_trips_through_checkpoint"
    },
    {
      "from": "spawn_executor_claim_atomic",
      "kind": "calls",
      "source_block": "CONTRACTS",
      "source_id": "spawn_executor_claim_atomic",
      "to": "python.tests.contracts.spawn_executor.test_claim_atomic"
    },
    {
      "from": "spawn_executor_concurrent_live_cap",
      "kind": "calls",
      "source_block": "CONTRACTS",
      "source_id": "spawn_executor_concurrent_live_cap",
      "to": "python.tests.contracts.spawn_executor.test_concurrent_live_cap"
    },
    {
      "from": "spawn_executor_heartbeat_advances",
      "kind": "calls",
      "source_block": "CONTRACTS",
      "source_id": "spawn_executor_heartbeat_advances",
      "to": "python.tests.contracts.spawn_executor.test_heartbeat_advances"
    },
    {
      "from": "spawn_executor_marks_failed_on_exception",
      "kind": "calls",
      "source_block": "CONTRACTS",
      "source_id": "spawn_executor_marks_failed_on_exception",
      "to": "python.tests.contracts.spawn_executor.test_marks_failed_on_exception"
    },
    {
      "from": "spawn_executor_merge_helpers_tolerate_no_pcna",
      "kind": "calls",
      "source_block": "CONTRACTS",
      "source_id": "spawn_executor_merge_helpers_tolerate_no_pcna",
      "to": "python.tests.contracts.spawn_executor.test_merge_helpers_tolerate_no_pcna"
    },
    {
      "from": "spawn_executor_no_orphan_invariant",
      "kind": "calls",
      "source_block": "CONTRACTS",
      "source_id": "spawn_executor_no_orphan_invariant",
      "to": "python.tests.contracts.spawn_executor.test_no_orphan_invariant"
    },
    {
      "from": "spawn_executor_resolve_provider_rejects_empty",
      "kind": "calls",
      "source_block": "CONTRACTS",
      "source_id": "spawn_executor_resolve_provider_rejects_empty",
      "to": "python.tests.contracts.spawn_executor.test_resolve_provider_rejects_empty"
    },
    {
      "from": "spawn_executor_retry_default_none",
      "kind": "calls",
      "source_block": "CONTRACTS",
      "source_id": "spawn_executor_retry_default_none",
      "to": "python.tests.contracts.spawn_executor.test_retry_default_none"
    },
    {
      "from": "spawn_executor_retry_once_on_transient",
      "kind": "calls",
      "source_block": "CONTRACTS",
      "source_id": "spawn_executor_retry_once_on_transient",
      "to": "python.tests.contracts.spawn_executor.test_retry_once_on_transient"
    },
    {
      "from": "spawn_executor_skips_non_running",
      "kind": "calls",
      "source_block": "CONTRACTS",
      "source_id": "spawn_executor_skips_non_running",
      "to": "python.tests.contracts.spawn_executor.test_skips_non_running"
    },
    {
      "from": "spawn_executor_snapshot_pcna_shape",
      "kind": "calls",
      "source_block": "CONTRACTS",
      "source_id": "spawn_executor_snapshot_pcna_shape",
      "to": "python.tests.contracts.spawn_executor.test_snapshot_pcna_shape"
    },
    {
      "from": "spawn_executor_stale_sweep_marks_worker_lost",
      "kind": "calls",
      "source_block": "CONTRACTS",
      "source_id": "spawn_executor_stale_sweep_marks_worker_lost",
      "to": "python.tests.contracts.spawn_executor.test_stale_sweep_marks_worker_lost"
    },
    {
      "from": "storage_anonymous_owner_null",
      "kind": "calls",
      "source_block": "CONTRACTS",
      "source_id": "storage_anonymous_owner_null",
      "to": "python.tests.contracts.chat.test_create_anonymous_owner_null"
    },
    {
      "from": "storage_create_owner_isolation",
      "kind": "calls",
      "source_block": "CONTRACTS",
      "source_id": "storage_create_owner_isolation",
      "to": "python.tests.contracts.chat.test_create_owner_isolation"
    }
  ],
  "gaps": [
    {
      "file": "a0-betatest/, aimmh/, odysseus-a0/",
      "missing": [
        "mirrored sibling trees excluded"
      ],
      "reason": "Verbatim upstream mirrors; source of truth stays upstream per CONNECTIONS.md. Own content is archive/ and repairs/."
    }
  ],
  "repo": "The-Interdependency/a0ucns"
});
