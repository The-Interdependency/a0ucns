# ratios: loc_comments=109:0 imports_exports=10:3 calls_definitions=24:3
from __future__ import annotations

from typing import List

from fastapi import HTTPException

from aimmh_lib import fan_out
from aimmh_lib.adapters import make_call_fn

from db import db
from models.hub_chat import HubChatPromptOut, HubChatPromptRequest, HubChatResponseItem
from services.auth import get_user_id
from services.hub_runner import _build_slot_context
from services.hub_store import (
    HUB_CHAT_PROMPT_COLLECTION,
    ensure_models_exist,
    ensure_thread,
    get_instance,
    iso_now,
    make_id,
    persist_message,
)


async def send_chat_prompt(current_user: dict, req: HubChatPromptRequest) -> HubChatPromptOut:
    user_id = get_user_id(current_user)
    instances = []
    for instance_id in req.instance_ids:
        instance = await get_instance(user_id, instance_id, include_archived=False)
        if not instance:
            raise HTTPException(status_code=404, detail=f"Instance not found: {instance_id}")
        instances.append(instance)

    await ensure_models_exist(user_id, [instance["model_id"] for instance in instances])
    prompt_id = make_id("hprompt")
    call = make_call_fn(user=current_user)
    slot_contexts = [await _build_slot_context(instance, verbosity=None) for instance in instances]
    raw_results = await fan_out(
        call,
        [instance["model_id"] for instance in instances],
        [{"role": "user", "content": req.prompt}],
        slot_contexts,
    )

    responses: List[HubChatResponseItem] = []
    for index, raw in enumerate(raw_results):
        instance = instances[index]
        await ensure_thread(
            instance["thread_id"],
            user_id,
            title=instance.get("name") or req.prompt[:80],
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
            content=req.prompt,
            model="hub_user",
            extra={
                "hub_prompt_id": prompt_id,
                "hub_instance_id": instance["instance_id"],
                "hub_role": "input",
            },
        )
        persisted = await persist_message(
            thread_id=instance["thread_id"],
            user_id=user_id,
            role="assistant",
            content=raw.content,
            model=raw.model,
            extra={
                "hub_prompt_id": prompt_id,
                "hub_instance_id": instance["instance_id"],
                "hub_role": "response",
                "response_time_ms": raw.response_time_ms,
                "error": raw.error,
            },
        )
        responses.append(HubChatResponseItem(
            prompt_id=prompt_id,
            instance_id=instance["instance_id"],
            instance_name=instance.get("name") or instance["instance_id"],
            thread_id=instance["thread_id"],
            model=raw.model,
            content=raw.content,
            message_id=persisted["message_id"],
            response_time_ms=raw.response_time_ms,
            error=raw.error,
            created_at=iso_now(),
        ))

    now = iso_now()
    doc = {
        "prompt_id": prompt_id,
        "user_id": user_id,
        "prompt": req.prompt,
        "label": req.label,
        "instance_ids": [instance["instance_id"] for instance in instances],
        "instance_names": [instance.get("name") or instance["instance_id"] for instance in instances],
        "responses": [response.model_dump() for response in responses],
        "created_at": now,
        "updated_at": now,
    }
    await db[HUB_CHAT_PROMPT_COLLECTION].insert_one(doc)
    return HubChatPromptOut(**doc)


async def list_chat_prompts(user_id: str, limit: int = 100) -> list[dict]:
    return await db[HUB_CHAT_PROMPT_COLLECTION].find({"user_id": user_id}, {"_id": 0}).sort("updated_at", -1).limit(limit).to_list(limit)


async def get_chat_prompt(user_id: str, prompt_id: str) -> HubChatPromptOut:
    doc = await db[HUB_CHAT_PROMPT_COLLECTION].find_one({"user_id": user_id, "prompt_id": prompt_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Chat prompt not found")
    return HubChatPromptOut(**doc)
# ratios: loc_comments=109:0 imports_exports=10:3 calls_definitions=24:3
