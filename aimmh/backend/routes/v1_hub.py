# ratios: loc_comments=346:0 imports_exports=13:28 calls_definitions=159:29
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query

from db import db
from models.hub import (
    HubConnectionsResponse,
    HubGroupCreateRequest,
    HubGroupListResponse,
    HubGroupOut,
    HubGroupUpdateRequest,
    HubInstanceCreateRequest,
    HubInstanceHistoryResponse,
    HubInstanceListResponse,
    HubInstanceOut,
    HubInstanceUpdateRequest,
    HubRunDetailResponse,
    HubRunListResponse,
    HubRunOut,
    HubRunRequest,
)
from models.hub_chat import HubChatPromptListResponse, HubChatPromptOut, HubChatPromptRequest
from models.hub_synthesis import HubSynthesisBatchListResponse, HubSynthesisBatchOut, HubSynthesisRequest
from services.auth import get_current_user, get_user_id
from services.billing_tiers import current_month_start_iso, get_user_billing_profile
from services.hub_chat import get_chat_prompt, list_chat_prompts, send_chat_prompt
from services.hub_synthesis import create_synthesis_batch, get_synthesis_batch, list_synthesis_batches
from services.hub_runner import execute_hub_run, get_hub_run_detail, list_hub_groups, list_hub_instances, list_hub_runs
from services.hub_store import (
    HUB_CHAT_PROMPT_COLLECTION,
    HUB_GROUP_COLLECTION,
    HUB_INSTANCE_COLLECTION,
    HUB_RUN_COLLECTION,
    HUB_RUN_STEP_COLLECTION,
    ensure_models_exist,
    get_group,
    get_instance,
    get_thread_messages,
    iso_now,
    make_id,
)

router = APIRouter(prefix="/api/v1/hub", tags=["hub"])


def _connections_payload() -> HubConnectionsResponse:
    return HubConnectionsResponse(
        fastapi_connections={
            "instances": {
                "list": "/api/v1/hub/instances",
                "create": "/api/v1/hub/instances",
                "detail": "/api/v1/hub/instances/{instance_id}",
                "update": "/api/v1/hub/instances/{instance_id}",
                "archive": "/api/v1/hub/instances/{instance_id}/archive",
                "unarchive": "/api/v1/hub/instances/{instance_id}/unarchive",
                "delete": "/api/v1/hub/instances/{instance_id}",
                "history": "/api/v1/hub/instances/{instance_id}/history",
            },
            "groups": {
                "list": "/api/v1/hub/groups",
                "create": "/api/v1/hub/groups",
                "detail": "/api/v1/hub/groups/{group_id}",
                "update": "/api/v1/hub/groups/{group_id}",
                "archive": "/api/v1/hub/groups/{group_id}/archive",
                "unarchive": "/api/v1/hub/groups/{group_id}/unarchive",
            },
            "runs": {
                "execute": "/api/v1/hub/runs",
                "list": "/api/v1/hub/runs",
                "detail": "/api/v1/hub/runs/{run_id}",
                "archive": "/api/v1/hub/runs/{run_id}/archive",
                "unarchive": "/api/v1/hub/runs/{run_id}/unarchive",
                "delete": "/api/v1/hub/runs/{run_id}",
            },
            "chat_prompts": {
                "broadcast": "/api/v1/hub/chat/prompts",
                "list": "/api/v1/hub/chat/prompts",
                "detail": "/api/v1/hub/chat/prompts/{prompt_id}",
            },
            "synthesis": {
                "create": "/api/v1/hub/chat/synthesize",
                "list": "/api/v1/hub/chat/syntheses",
                "detail": "/api/v1/hub/chat/syntheses/{synthesis_batch_id}",
            },
            "lib_patterns": {
                "fan_out": "/api/v1/lib/fan-out",
                "daisy_chain": "/api/v1/lib/daisy-chain",
                "room_all": "/api/v1/lib/room-all",
                "room_synthesized": "/api/v1/lib/room-synthesized",
                "council": "/api/v1/lib/council",
                "roleplay": "/api/v1/lib/roleplay",
            },
        },
        patterns=["fan_out", "daisy_chain", "room_all", "room_synthesized", "council", "roleplay"],
        supports={
            "single_model_multiple_instances": True,
            "nested_groups": True,
            "pattern_pipelines": True,
            "instance_archival": True,
            "instance_private_thread_history": True,
            "run_archival": True,
            "same_prompt_multi_instance_chat": True,
            "selected_response_synthesis": True,
        },
    )


@router.get("/options", response_model=HubConnectionsResponse)
async def get_hub_options(current_user: dict = Depends(get_current_user)):
    return _connections_payload()


@router.get("/fastapi-connections", response_model=HubConnectionsResponse)
async def get_hub_fastapi_connections(current_user: dict = Depends(get_current_user)):
    return _connections_payload()


@router.post("/instances", response_model=HubInstanceOut)
async def create_instance(req: HubInstanceCreateRequest, current_user: dict = Depends(get_current_user)):
    user_id = get_user_id(current_user)
    billing_profile = await get_user_billing_profile(user_id)
    max_instances = billing_profile.get("max_instances")
    if max_instances is not None:
        active_instance_count = await db[HUB_INSTANCE_COLLECTION].count_documents({"user_id": user_id, "archived": {"$ne": True}})
        if active_instance_count >= int(max_instances):
            raise HTTPException(status_code=403, detail=f"Your {billing_profile['subscription_tier']} tier allows up to {max_instances} active instances. Archive an instance or upgrade to continue.")
    await ensure_models_exist(user_id, [req.model_id])
    now = iso_now()
    doc = req.model_dump()
    doc.update(
        {
            "instance_id": make_id("hubi"),
            "thread_id": make_id("hubthr"),
            "user_id": user_id,
            "created_at": now,
            "updated_at": now,
            "archived_at": now if req.archived else None,
        }
    )
    await db[HUB_INSTANCE_COLLECTION].insert_one(doc)
    doc.pop("user_id", None)
    return HubInstanceOut(**doc)


@router.get("/instances", response_model=HubInstanceListResponse)
async def get_instances(
    include_archived: bool = Query(default=False),
    limit: int = Query(default=200, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
):
    user_id = get_user_id(current_user)
    docs = await list_hub_instances(user_id, include_archived=include_archived, limit=limit)
    return HubInstanceListResponse(instances=[HubInstanceOut(**doc) for doc in docs], total=len(docs))


@router.get("/instances/{instance_id}", response_model=HubInstanceOut)
async def get_instance_detail(instance_id: str, current_user: dict = Depends(get_current_user)):
    user_id = get_user_id(current_user)
    doc = await get_instance(user_id, instance_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Instance not found")
    return HubInstanceOut(**doc)


@router.patch("/instances/{instance_id}", response_model=HubInstanceOut)
async def update_instance(instance_id: str, req: HubInstanceUpdateRequest, current_user: dict = Depends(get_current_user)):
    user_id = get_user_id(current_user)
    existing = await get_instance(user_id, instance_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Instance not found")

    update = req.model_dump(exclude_none=True)
    if "model_id" in update:
        await ensure_models_exist(user_id, [update["model_id"]])
    if "archived" in update:
        update["archived_at"] = iso_now() if update["archived"] else None
    update["updated_at"] = iso_now()

    await db[HUB_INSTANCE_COLLECTION].update_one(
        {"user_id": user_id, "instance_id": instance_id},
        {"$set": update},
    )
    doc = await get_instance(user_id, instance_id)
    return HubInstanceOut(**doc)


@router.post("/instances/{instance_id}/archive", response_model=HubInstanceOut)
async def archive_instance(instance_id: str, current_user: dict = Depends(get_current_user)):
    return await update_instance(instance_id, HubInstanceUpdateRequest(archived=True), current_user)


@router.post("/instances/{instance_id}/unarchive", response_model=HubInstanceOut)
async def unarchive_instance(instance_id: str, current_user: dict = Depends(get_current_user)):
    return await update_instance(instance_id, HubInstanceUpdateRequest(archived=False), current_user)


@router.delete("/instances/{instance_id}")
async def delete_instance(instance_id: str, current_user: dict = Depends(get_current_user)):
    user_id = get_user_id(current_user)
    existing = await db[HUB_INSTANCE_COLLECTION].find_one(
        {"user_id": user_id, "instance_id": instance_id},
        {"_id": 0, "instance_id": 1, "thread_id": 1, "archived": 1},
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Instance not found")
    if not existing.get("archived"):
        raise HTTPException(status_code=400, detail="Archive the instance before deleting it")

    await db[HUB_INSTANCE_COLLECTION].delete_one({"user_id": user_id, "instance_id": instance_id, "archived": True})

    thread_id = existing.get("thread_id")
    if thread_id:
        await db.threads.delete_one({"user_id": user_id, "thread_id": thread_id})
        await db.messages.delete_many({"user_id": user_id, "thread_id": thread_id})

    await db[HUB_GROUP_COLLECTION].update_many(
        {"user_id": user_id},
        {
            "$pull": {"members": {"member_type": "instance", "member_id": instance_id}},
            "$set": {"updated_at": iso_now()},
        },
    )

    return {"message": f"Archived instance {instance_id} deleted"}


@router.get("/instances/{instance_id}/history", response_model=HubInstanceHistoryResponse)
async def get_instance_history(
    instance_id: str,
    limit: int = Query(default=200, ge=1, le=2000),
    current_user: dict = Depends(get_current_user),
):
    user_id = get_user_id(current_user)
    doc = await get_instance(user_id, instance_id, include_archived=True)
    if not doc:
        raise HTTPException(status_code=404, detail="Instance not found")
    messages = await get_thread_messages(user_id, doc["thread_id"], limit=limit)
    return HubInstanceHistoryResponse(instance_id=instance_id, thread_id=doc["thread_id"], messages=messages)


@router.post("/groups", response_model=HubGroupOut)
async def create_group(req: HubGroupCreateRequest, current_user: dict = Depends(get_current_user)):
    user_id = get_user_id(current_user)
    now = iso_now()
    doc = req.model_dump()
    doc.update(
        {
            "group_id": make_id("hubg"),
            "user_id": user_id,
            "created_at": now,
            "updated_at": now,
            "archived_at": now if req.archived else None,
        }
    )
    await db[HUB_GROUP_COLLECTION].insert_one(doc)
    doc.pop("user_id", None)
    return HubGroupOut(**doc)


@router.get("/groups", response_model=HubGroupListResponse)
async def get_groups(
    include_archived: bool = Query(default=False),
    limit: int = Query(default=200, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
):
    user_id = get_user_id(current_user)
    docs = await list_hub_groups(user_id, include_archived=include_archived, limit=limit)
    return HubGroupListResponse(groups=[HubGroupOut(**doc) for doc in docs], total=len(docs))


@router.get("/groups/{group_id}", response_model=HubGroupOut)
async def get_group_detail(group_id: str, current_user: dict = Depends(get_current_user)):
    user_id = get_user_id(current_user)
    doc = await get_group(user_id, group_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Group not found")
    return HubGroupOut(**doc)


@router.patch("/groups/{group_id}", response_model=HubGroupOut)
async def update_group(group_id: str, req: HubGroupUpdateRequest, current_user: dict = Depends(get_current_user)):
    user_id = get_user_id(current_user)
    existing = await get_group(user_id, group_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Group not found")

    update = req.model_dump(exclude_none=True)
    if "archived" in update:
        update["archived_at"] = iso_now() if update["archived"] else None
    update["updated_at"] = iso_now()

    await db[HUB_GROUP_COLLECTION].update_one(
        {"user_id": user_id, "group_id": group_id},
        {"$set": update},
    )
    doc = await get_group(user_id, group_id)
    return HubGroupOut(**doc)


@router.post("/groups/{group_id}/archive", response_model=HubGroupOut)
async def archive_group(group_id: str, current_user: dict = Depends(get_current_user)):
    return await update_group(group_id, HubGroupUpdateRequest(archived=True), current_user)


@router.post("/groups/{group_id}/unarchive", response_model=HubGroupOut)
async def unarchive_group(group_id: str, current_user: dict = Depends(get_current_user)):
    return await update_group(group_id, HubGroupUpdateRequest(archived=False), current_user)


@router.post("/runs", response_model=HubRunDetailResponse)
async def create_hub_run(req: HubRunRequest, current_user: dict = Depends(get_current_user)):
    user_id = get_user_id(current_user)
    billing_profile = await get_user_billing_profile(user_id)
    max_runs = billing_profile.get("max_runs_per_month")
    if max_runs is not None:
        run_count = await db[HUB_RUN_COLLECTION].count_documents({"user_id": user_id, "created_at": {"$gte": current_month_start_iso()}})
        if run_count >= int(max_runs):
            raise HTTPException(status_code=403, detail=f"Your {billing_profile['subscription_tier']} tier allows {max_runs} runs per month. Upgrade to continue.")
    return await execute_hub_run(current_user, req)


@router.get("/runs", response_model=HubRunListResponse)
async def get_runs(
    include_archived: bool = Query(default=False),
    limit: int = Query(default=100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
):
    user_id = get_user_id(current_user)
    docs = await list_hub_runs(user_id, include_archived=include_archived, limit=limit)
    return HubRunListResponse(runs=[HubRunOut(**doc) for doc in docs], total=len(docs))


@router.post("/runs/{run_id}/archive", response_model=HubRunOut)
async def archive_run(run_id: str, current_user: dict = Depends(get_current_user)):
    user_id = get_user_id(current_user)
    await db[HUB_RUN_COLLECTION].update_one(
        {"user_id": user_id, "run_id": run_id},
        {"$set": {"archived": True, "archived_at": iso_now(), "updated_at": iso_now()}},
    )
    doc = await db[HUB_RUN_COLLECTION].find_one({"user_id": user_id, "run_id": run_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Run not found")
    return HubRunOut(**doc)


@router.post("/runs/{run_id}/unarchive", response_model=HubRunOut)
async def unarchive_run(run_id: str, current_user: dict = Depends(get_current_user)):
    user_id = get_user_id(current_user)
    await db[HUB_RUN_COLLECTION].update_one(
        {"user_id": user_id, "run_id": run_id},
        {"$set": {"archived": False, "archived_at": None, "updated_at": iso_now()}},
    )
    doc = await db[HUB_RUN_COLLECTION].find_one({"user_id": user_id, "run_id": run_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Run not found")
    return HubRunOut(**doc)


@router.delete("/runs/{run_id}")
async def delete_run(run_id: str, current_user: dict = Depends(get_current_user)):
    user_id = get_user_id(current_user)
    result = await db[HUB_RUN_COLLECTION].delete_one({"user_id": user_id, "run_id": run_id, "archived": True})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Archived run not found")
    await db[HUB_RUN_STEP_COLLECTION].delete_many({"user_id": user_id, "run_id": run_id})
    return {"message": f"Archived run {run_id} deleted"}


@router.get("/runs/{run_id}", response_model=HubRunDetailResponse)
async def get_run_detail(run_id: str, current_user: dict = Depends(get_current_user)):
    user_id = get_user_id(current_user)
    return await get_hub_run_detail(user_id, run_id)

@router.post("/chat/synthesize", response_model=HubSynthesisBatchOut)
async def create_chat_synthesis(req: HubSynthesisRequest, current_user: dict = Depends(get_current_user)):
    return await create_synthesis_batch(current_user, req)


@router.get("/chat/syntheses", response_model=HubSynthesisBatchListResponse)
async def get_chat_syntheses(
    limit: int = Query(default=100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
):
    user_id = get_user_id(current_user)
    docs = await list_synthesis_batches(user_id, limit=limit)
    return HubSynthesisBatchListResponse(batches=[HubSynthesisBatchOut(**doc) for doc in docs], total=len(docs))


@router.get("/chat/syntheses/{synthesis_batch_id}", response_model=HubSynthesisBatchOut)
async def get_chat_synthesis_detail(synthesis_batch_id: str, current_user: dict = Depends(get_current_user)):
    user_id = get_user_id(current_user)
    return await get_synthesis_batch(user_id, synthesis_batch_id)



@router.post("/chat/prompts", response_model=HubChatPromptOut)
async def create_chat_prompt(req: HubChatPromptRequest, current_user: dict = Depends(get_current_user)):
    return await send_chat_prompt(current_user, req)


@router.get("/chat/prompts", response_model=HubChatPromptListResponse)
async def get_chat_prompts(
    limit: int = Query(default=100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
):
    user_id = get_user_id(current_user)
    docs = await list_chat_prompts(user_id, limit=limit)
    return HubChatPromptListResponse(prompts=[HubChatPromptOut(**doc) for doc in docs], total=len(docs))


@router.get("/chat/prompts/{prompt_id}", response_model=HubChatPromptOut)
async def get_chat_prompt_detail(prompt_id: str, current_user: dict = Depends(get_current_user)):
    user_id = get_user_id(current_user)
    return await get_chat_prompt(user_id, prompt_id)
# ratios: loc_comments=346:0 imports_exports=13:28 calls_definitions=159:29
