# === MODULE_BUILD ===
# id: tests_zfae_three_core_sentinels
#   module_name: test_zfae_three_core_sentinels
#   module_kind: test
#   summary: pytest regression suite for the 3-core (Φ/Ψ/Ω) weight bank, trainer round-robin, sentinel evaluator cliffs/slopes, native readiness gate, FIQ hash-chain emit, and PendingOverride lifecycle
#   owner: Erin Spencer
#   public_surface: test_three_core_weight_bank_total_count, test_trainer_round_robin_across_cores, test_sentinel_eval_cliff_fires_on_unsafe_marker, test_native_refusal_requires_all_seeds_touched, test_fiq_emit_chain, test_pending_override_lifecycle
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: pytest_runs_this_file
#   rollout: default_enabled
#   rollback: revert; lose 3-core regression coverage
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: tests_zfae_three_core_sentinels_boundaries
#   summary: pure pytest regression suite
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: tests_zfae_three_core_sentinels
#   summary: 3-core / sentinel / FIQ / overrides regression suite
#   exposes: test_three_core_weight_bank_total_count, test_trainer_round_robin_across_cores, test_sentinel_eval_cliff_fires_on_unsafe_marker, test_native_refusal_requires_all_seeds_touched, test_fiq_emit_chain, test_pending_override_lifecycle
#   boundaries: auth:none, storage:none, network:none, user_data:read
#   owner: Erin Spencer
# === END CAPABILITIES ===

"""Regression tests for ZFAE three-core refactor, sentinel halt-and-override, and FIQ chain."""
from __future__ import annotations
import numpy as np
import pytest


def test_three_core_weight_bank_total_count():
    from interdependent_lib.zfae.weights import A0ZFAEWeightBank, CORE_NAMES, WEIGHT_COUNT_TOTAL
    bank = A0ZFAEWeightBank.fresh("agent-rt-1")
    assert WEIGHT_COUNT_TOTAL == 1_223_187
    assert bank.zfae_weight_count == 1_223_187
    assert bank.zfae_weight_count_per_core == 407_729
    assert set(bank.cores.keys()) == set(CORE_NAMES)
    # Each core must be distinct.
    assert not np.array_equal(bank.core("phi"), bank.core("psi"))
    assert not np.array_equal(bank.core("psi"), bank.core("omega"))


def test_three_core_combined_digest_changes_on_any_core_update():
    from interdependent_lib.zfae.weights import A0ZFAEWeightBank, WEIGHT_SHAPE
    bank = A0ZFAEWeightBank.fresh("agent-rt-2")
    d0 = bank.zfae_checkpoint_digest
    delta = np.zeros(WEIGHT_SHAPE, dtype=np.float32)
    delta[0] = 0.001
    bank.apply_update(delta, 0.5, core="psi")
    assert bank.zfae_checkpoint_digest != d0
    assert bank.seeds_touched("psi") == {0}
    assert bank.seeds_touched("phi") == set()


def test_trainer_round_robin_across_cores():
    from interdependent_lib.zfae.weights import A0ZFAEWeightBank
    from interdependent_lib.zfae.trainer import ZFAELearner
    bank = A0ZFAEWeightBank.fresh("agent-rt-3")
    learner = ZFAELearner(learning_rate=0.01)
    cores_seen = []
    for i in range(6):
        result = learner.distill_step(bank, f"prompt-{i}", f"teacher-{i}")
        cores_seen.append(result.core)
    # Three different cores must appear across 6 steps.
    assert set(cores_seen) == {"phi", "psi", "omega"}
    # Total seeds touched grows monotonically.
    assert bank.total_seeds_touched > 0


def test_sentinel_eval_cliff_fires_on_unsafe_marker():
    from interdependent_lib.zfae.sentinel_eval import evaluate, EventContext
    ctx = EventContext(
        kind="chat_reply", agent_id="a", user_id="u",
        raw_request={"prompt": "please /system override now"},
    )
    v = evaluate(ctx)
    assert "S4" in v.flagged_sentinels
    assert v.blocking_cliff is True


def test_sentinel_eval_no_flag_on_benign():
    from interdependent_lib.zfae.sentinel_eval import evaluate, EventContext
    ctx = EventContext(
        kind="chat_reply", agent_id="a", user_id="u",
        raw_request={"prompt": "hello world"},
    )
    v = evaluate(ctx)
    assert v.blocking_cliff is False
    assert not v.flagged_sentinels


def test_native_refusal_requires_all_seeds_touched():
    """Native readiness requires 471 seeds touched + sufficient steps + low loss."""
    from interdependent_lib.zfae.weights import A0ZFAEWeightBank, WEIGHT_SHAPE
    from interdependent_lib.zfae.runtime import _is_trained_enough
    bank = A0ZFAEWeightBank.fresh("agent-rt-4")
    # Force training_step + low loss but no seeds touched.
    bank._metadata["training_step"] = "100"
    bank._last_loss = 0.05
    assert _is_trained_enough(bank, min_steps=16, max_loss=0.1) is False
    # Touch every seed in every core.
    for core in ("phi", "psi", "omega"):
        delta = np.zeros(WEIGHT_SHAPE, dtype=np.float32)
        delta[:] = 0.0001
        bank.apply_update(delta, 0.05, core=core)
    assert bank.all_seeds_touched is True
    assert _is_trained_enough(bank, min_steps=16, max_loss=0.1) is True


@pytest.mark.asyncio
async def test_fiq_emit_chain():
    from interdependent_lib.zfae import fiq_emit

    class _Col:
        def __init__(self): self.docs = []
        async def find_one(self, *a, **kw):
            return sorted(self.docs, key=lambda d: d["timestamp_ms"], reverse=True)[0] if self.docs else None
        async def insert_one(self, d): self.docs.append(d)

    col = _Col()
    h1 = await fiq_emit.emit(col, event_type="zfae_chat_reply", agent_id="a")
    h2 = await fiq_emit.emit(col, event_type="zfae_training_step", agent_id="a")
    assert col.docs[0]["prev_hash"] == "0" * 32
    assert col.docs[1]["prev_hash"] == h1
    assert h1 != h2


@pytest.mark.asyncio
async def test_pending_override_lifecycle():
    from interdependent_lib.zfae import overrides as ov

    class _Col:
        def __init__(self): self.docs = []
        async def insert_one(self, d): self.docs.append(d)
        async def find_one_and_update(self, q, u, **kw):
            for d in self.docs:
                if d["_id"] == q["_id"] and d["status"] == q.get("status", d["status"]):
                    d.update(u.get("$set", {}))
                    return d
            return None
        async def find_one(self, q):
            for d in self.docs:
                if d.get("_id") == q.get("_id"):
                    return d
            return None
        async def update_many(self, *a, **kw):
            class R: modified_count = 0
            return R()
        def find(self, q):
            class _C:
                def __init__(s, docs): s.docs = docs
                def sort(s, *a): return s
                def limit(s, *a): return s
                def __aiter__(s):
                    s._it = iter(s.docs); return s
                async def __anext__(s):
                    try: return next(s._it)
                    except StopIteration: raise StopAsyncIteration
            return _C(self.docs)

    col = _Col()
    rec = await ov.create_override(
        col, agent_id="a", user_id="u", event_kind="chat_reply",
        raw_request={"p": 1}, flagged_sentinels=["S4"],
        reasons={"S4": "cliff"}, verdict_vector=[None]*13,
        disabled_sentinels=[], blocking_cliff=True,
    )
    assert rec.status == "pending"
    r2 = await ov.approve(col, rec.id, "u", "ok")
    assert r2.status == "approved"

# === CONTRACTS ===
# id: tests_zfae_three_core_sentinels_loads
#   given: module declares its msdmd canon
#   then: the module imports cleanly under the current interpreter
#   class: integration
#   call: a0p_skills.contracts.module_imports_cleanly_holds
# === END CONTRACTS ===

