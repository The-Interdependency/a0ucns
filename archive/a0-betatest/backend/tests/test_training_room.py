# === MODULE_BUILD ===
# id: test_training_room
#   module_name: test_training_room
#   module_kind: test
#   summary: pytest for ZFAERuntime.train_multi — multi-teacher distillation runs one
#     distill step per (prompt × model), accumulates the weight bank across two or more
#     models, records teachers_used, and surfaces per-step provider errors without
#     aborting the run
#   owner: Erin Spencer
#   public_surface: (pytest test functions)
#   internal_surface: _FakeTeacher
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: self
#   rollout: default_enabled
#   rollback: delete file
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: test_training_room_boundaries
#   summary: pure in-process; no network/storage
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CONTRACTS ===
# id: test_training_room_self
#   given: ZFAERuntime.train_multi with a fake multi-model teacher
#   then: the bank accumulates one distill step per (prompt x model) and errors are per-step
#   class: correctness
#   call: tests.test_training_room
# === END CONTRACTS ===
"""Pytest coverage for the Training Room multi-teacher distillation."""
from __future__ import annotations
import pytest

from interdependent_lib.zfae.runtime import ZFAERuntime
from interdependent_lib.zfae.weights import A0ZFAEWeightBank
from interdependent_lib.zfae.teacher import TeacherInvocation


class _FakeTeacher:
    """Returns a deterministic reply per model, or an error for a flagged model."""
    _registry = {"openai": object(), "anthropic": object()}

    def __init__(self, error_models=()):
        self.error_models = set(error_models)
        self.calls = []

    async def invoke(self, *, user_id, teacher_model_id, messages):
        self.calls.append(teacher_model_id)
        if teacher_model_id in self.error_models:
            return TeacherInvocation(teacher_model_id=teacher_model_id, teacher_reply="",
                                     error="no BYOK key")
        return TeacherInvocation(teacher_model_id=teacher_model_id,
                                 teacher_reply=f"answer from {teacher_model_id}",
                                 usage={"total": 5})


@pytest.mark.asyncio
async def test_train_multi_accumulates_across_two_models():
    teacher = _FakeTeacher()
    rt = ZFAERuntime(teacher_client=teacher)
    bank = A0ZFAEWeightBank.fresh("agent-train")
    start = bank.zfae_training_step

    res = await rt.train_multi(
        agent_id="agent-train", user_id="u1", bank=bank,
        prompts=["explain entropy", "capital of france"],
        teacher_model_ids=["openai:gpt-4o", "anthropic:claude-sonnet-4-5"],
    )
    assert res["weights_updated"] is True
    assert res["ok_steps"] == 4                      # 2 prompts x 2 models
    assert len(res["steps"]) == 4
    assert set(res["teachers_used"]) == {"openai:gpt-4o", "anthropic:claude-sonnet-4-5"}
    assert bank.zfae_training_step == start + 4      # one distill step each
    assert teacher.calls == [
        "openai:gpt-4o", "anthropic:claude-sonnet-4-5",  # prompt 1
        "openai:gpt-4o", "anthropic:claude-sonnet-4-5",  # prompt 2
    ]
    for s in res["steps"]:
        assert s["ok"] is True
        assert "loss" in s and "core" in s and "training_step" in s


@pytest.mark.asyncio
async def test_train_multi_records_per_step_errors_without_aborting():
    teacher = _FakeTeacher(error_models={"anthropic:claude-sonnet-4-5"})
    rt = ZFAERuntime(teacher_client=teacher)
    bank = A0ZFAEWeightBank.fresh("agent-train2")

    res = await rt.train_multi(
        agent_id="agent-train2", user_id="u1", bank=bank,
        prompts=["one prompt"],
        teacher_model_ids=["openai:gpt-4o", "anthropic:claude-sonnet-4-5"],
    )
    assert res["ok_steps"] == 1
    assert len(res["steps"]) == 2
    good = [s for s in res["steps"] if s["ok"]]
    bad = [s for s in res["steps"] if not s["ok"]]
    assert good[0]["teacher_model_id"] == "openai:gpt-4o"
    assert bad[0]["teacher_model_id"] == "anthropic:claude-sonnet-4-5"
    assert "no BYOK key" in bad[0]["error"]
    assert res["teachers_used"] == ["openai:gpt-4o"]


@pytest.mark.asyncio
async def test_train_multi_no_teacher_client():
    rt = ZFAERuntime(teacher_client=None)
    bank = A0ZFAEWeightBank.fresh("agent-train3")
    res = await rt.train_multi(
        agent_id="agent-train3", user_id="u1", bank=bank,
        prompts=["p"], teacher_model_ids=["a:b", "c:d"],
    )
    assert res["weights_updated"] is False
    assert res["ok_steps"] == 0
    assert res.get("error")
