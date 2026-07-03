# ratios: loc_comments=98:55 imports_exports=4:3 calls_definitions=21:7
# === MODULE_BUILD ===
# id: zfae_teacher_client
#   module_name: teacher
#   module_kind: adapter
#   summary: TeacherClient — invokes a configured teacher model via the BYOK provider REGISTRY; emits training records; never substitutes its output as native zfae inference
#   owner: Erin Spencer
#   public_surface: TeacherClient, TeacherInvocation, build_curated_context
#   internal_surface: _coerce_history
#   auth_boundary: none
#   storage_boundary: read
#   network_boundary: external
#   user_data_boundary: read
#   admin_only: false
#   tests: a0p_skills.contracts.zfae_teacher_call_writes_training_record_holds
#   rollout: default_enabled
#   rollback: remove teacher_assisted path; runtime falls back to zfae_native (with proper refusal)
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: zfae_teacher_client_boundaries
#   summary: TeacherClient — invokes a configured teacher model via the BYOK provider REGISTRY; emits training records; never substitutes its output as native zfae inference
#   auth_boundary: none
#   storage_boundary: read
#   network_boundary: external
#   user_data_boundary: read
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: zfae_teacher_client
#   summary: TeacherClient — invokes a configured teacher model via the BYOK provider REGISTRY; emits training records; never substitutes its output as native zfae inference
#   exposes: TeacherClient, TeacherInvocation, build_curated_context
#   boundaries: auth:none, storage:read, network:external, user_data:read
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: zfae_teacher_call_writes_training_record
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.zfae_teacher_call_writes_training_record_holds
# === END CONTRACTS ===
"""TeacherClient — calls an external model as TEACHER, logs the training record."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional

from .archive import append_training_record


@dataclass
class TeacherInvocation:
    teacher_model_id: str             # e.g. "openai:gpt-4o-mini"
    teacher_reply: str
    usage: dict = field(default_factory=dict)
    error: Optional[str] = None


def _coerce_history(transcript: Optional[list[dict]], max_turns: int = 8) -> list[dict]:
    """Take the last max_turns role/content pairs."""
    if not transcript:
        return []
    return list(transcript)[-max_turns:]


def build_curated_context(
    *,
    system_prompt: str = "",
    persona: str = "",
    transcript: Optional[list[dict]] = None,
    prompt: str = "",
    ring_summary: Optional[dict] = None,
    max_history: int = 8,
) -> list[dict]:
    """Surface-3: the context actually sent to the teacher.

    Distinct from both surface-1 (raw prompt) and surface-2 (zfae internal state).
    Default composition: system → optional ring summary → history → prompt.
    User-editable via the character sheet's `teacher_context_template`.
    """
    messages: list[dict] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    if persona:
        messages.append({"role": "system", "content": f"persona: {persona}"})
    if ring_summary:
        sigs = ", ".join(f"{k}={v:+.3f}" if isinstance(v, (int, float)) else f"{k}={v}"
                          for k, v in ring_summary.items())
        messages.append({"role": "system", "content": f"[zfae:ring_summary] {sigs}"})
    for turn in _coerce_history(transcript, max_history):
        messages.append({"role": turn.get("role", "user"), "content": turn.get("content", "")})
    if prompt:
        messages.append({"role": "user", "content": prompt})
    return messages


class TeacherClient:
    """Invokes a teacher model via the BYOK provider REGISTRY.

    The client NEVER claims teacher output as native inference. The caller
    (ZFAERuntime) is responsible for tagging `reply_source="teacher_assisted"`.
    """

    def __init__(self, registry, get_key_fn):
        """`registry` = providers.REGISTRY dict; `get_key_fn(user_id, provider)` → str."""
        self._registry = registry
        self._get_key = get_key_fn

    async def invoke(
        self,
        *,
        user_id: str,
        teacher_model_id: str,
        messages: list[dict],
    ) -> TeacherInvocation:
        """Call the teacher. `teacher_model_id` shape: 'provider:model'."""
        if ":" not in teacher_model_id:
            return TeacherInvocation(
                teacher_model_id=teacher_model_id, teacher_reply="",
                error=f"invalid teacher_model_id {teacher_model_id!r}",
            )
        prov, name = teacher_model_id.split(":", 1)
        if prov not in self._registry:
            return TeacherInvocation(
                teacher_model_id=teacher_model_id, teacher_reply="",
                error=f"unknown provider {prov!r}",
            )
        key = await self._get_key(user_id, prov)
        if not key:
            return TeacherInvocation(
                teacher_model_id=teacher_model_id, teacher_reply="",
                error=f"no BYOK key for {prov!r} (teacher_assisted requires it)",
            )
        adapter = self._registry[prov]
        result = await adapter.chat(key, name, messages, system=None)
        return TeacherInvocation(
            teacher_model_id=teacher_model_id,
            teacher_reply=result.get("content", "") or "",
            usage=result.get("usage", {}) or {},
            error=result.get("error"),
        )

    def write_training_record(
        self,
        *,
        agent_id: str,
        raw_prompt: str,
        transcript_context: list[dict],
        zfae_snapshot_before: dict,
        ring_state_before: dict,
        teacher: TeacherInvocation,
        zfae_snapshot_after: dict,
        user_feedback: Optional[Any] = None,
    ) -> str:
        """Append the canonical training record JSONL row. Returns the file path."""
        rec = {
            "raw_prompt": raw_prompt,
            "transcript_context": transcript_context,
            "zfae_snapshot_before": zfae_snapshot_before,
            "ring_state_before": ring_state_before,
            "teacher_model_id": teacher.teacher_model_id,
            "teacher_reply": teacher.teacher_reply,
            "teacher_usage": teacher.usage,
            "teacher_error": teacher.error,
            "zfae_snapshot_after": zfae_snapshot_after,
            "user_feedback": user_feedback,
        }
        return append_training_record(agent_id, rec)
# ratios: loc_comments=98:55 imports_exports=4:3 calls_definitions=21:7
