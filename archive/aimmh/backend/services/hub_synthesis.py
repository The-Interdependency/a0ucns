# ratios: loc_comments=123:0 imports_exports=10:3 calls_definitions=31:4
from __future__ import annotations

from typing import List

from fastapi import HTTPException

from aimmh_lib import fan_out
from aimmh_lib.adapters import make_call_fn

from db import db
from models.hub_synthesis import HubSynthesisBatchOut, HubSynthesisOutput, HubSynthesisRequest, SynthesisSourceBlock
from services.auth import get_user_id
from services.hub_runner import _build_slot_context
from services.hub_store import (
    HUB_SYNTHESIS_BATCH_COLLECTION,
    ensure_models_exist,
    ensure_thread,
    get_instance,
    iso_now,
    make_id,
    persist_message,
)


def _build_synthesis_prompt(selected_blocks: List[SynthesisSourceBlock], instruction: str | None) -> str:
    sections = []
    if instruction and instruction.strip():
        sections.append(f"Synthesis instruction:\n{instruction.strip()}")
    sections.append("Selected AIMMH responses to synthesize:")
    for index, block in enumerate(selected_blocks, start=1):
        label = block.source_label or block.instance_name or block.model or block.source_id
        sections.append(
            f"[{index}] {label}\nModel: {block.model or 'unknown'}\nInstance: {block.instance_name or block.instance_id or 'unknown'}\n\n{block.content}"
        )
    sections.append("Produce a faithful synthesis that compares, contrasts, preserves important native formatting where useful, and highlights agreements, disagreements, and actionable next steps.")
    return "\n\n".join(sections)


async def create_synthesis_batch(current_user: dict, req: HubSynthesisRequest) -> HubSynthesisBatchOut:
    user_id = get_user_id(current_user)
    instances = []
    for instance_id in req.synthesis_instance_ids:
        instance = await get_instance(user_id, instance_id, include_archived=False)
        if not instance:
            raise HTTPException(status_code=404, detail=f"Synthesis instance not found: {instance_id}")
        instances.append(instance)

    await ensure_models_exist(user_id, [instance["model_id"] for instance in instances])
    batch_id = make_id("hsynth")
    synthesis_prompt = _build_synthesis_prompt(req.selected_blocks, req.instruction)
    call = make_call_fn(user=current_user)
    slot_contexts = [await _build_slot_context(instance, verbosity=None) for instance in instances]
    raw_results = await fan_out(
        call,
        [instance["model_id"] for instance in instances],
        [{"role": "user", "content": synthesis_prompt}],
        slot_contexts,
    )

    outputs: List[HubSynthesisOutput] = []
    for index, raw in enumerate(raw_results):
        instance = instances[index]
        await ensure_thread(
            instance["thread_id"],
            user_id,
            title=req.label or "Synthesis",
            extra={
                "hub_instance_id": instance["instance_id"],
                "hub_instance_name": instance.get("name"),
                "hub_model_id": instance.get("model_id"),
                "hub_archived": instance.get("archived", False),
            },
        )
        await persist_message(
            thread_id=instance["thread_id"],
            user_id=user_id,
            role="user",
            content=synthesis_prompt,
            model="hub_user",
            extra={
                "hub_synthesis_batch_id": batch_id,
                "hub_instance_id": instance["instance_id"],
                "hub_role": "synthesis_input",
            },
        )
        persisted = await persist_message(
            thread_id=instance["thread_id"],
            user_id=user_id,
            role="assistant",
            content=raw.content,
            model=raw.model,
            extra={
                "hub_synthesis_batch_id": batch_id,
                "hub_instance_id": instance["instance_id"],
                "hub_role": "synthesis_output",
                "response_time_ms": raw.response_time_ms,
                "error": raw.error,
            },
        )
        outputs.append(HubSynthesisOutput(
            synthesis_batch_id=batch_id,
            synthesis_instance_id=instance["instance_id"],
            synthesis_instance_name=instance.get("name") or instance["instance_id"],
            model=raw.model,
            thread_id=instance["thread_id"],
            content=raw.content,
            message_id=persisted["message_id"],
            response_time_ms=raw.response_time_ms,
            error=raw.error,
            created_at=iso_now(),
        ))

    now = iso_now()
    doc = {
        "synthesis_batch_id": batch_id,
        "user_id": user_id,
        "label": req.label,
        "instruction": req.instruction,
        "selected_blocks": [block.model_dump() for block in req.selected_blocks],
        "synthesis_instance_ids": [instance["instance_id"] for instance in instances],
        "synthesis_instance_names": [instance.get("name") or instance["instance_id"] for instance in instances],
        "outputs": [output.model_dump() for output in outputs],
        "created_at": now,
        "updated_at": now,
    }
    await db[HUB_SYNTHESIS_BATCH_COLLECTION].insert_one(doc)
    return HubSynthesisBatchOut(**doc)


async def list_synthesis_batches(user_id: str, limit: int = 100) -> list[dict]:
    return await db[HUB_SYNTHESIS_BATCH_COLLECTION].find({"user_id": user_id}, {"_id": 0}).sort("updated_at", -1).limit(limit).to_list(limit)


async def get_synthesis_batch(user_id: str, synthesis_batch_id: str) -> HubSynthesisBatchOut:
    doc = await db[HUB_SYNTHESIS_BATCH_COLLECTION].find_one({"user_id": user_id, "synthesis_batch_id": synthesis_batch_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Synthesis batch not found")
    return HubSynthesisBatchOut(**doc)
# ratios: loc_comments=123:0 imports_exports=10:3 calls_definitions=31:4
