# ratios: loc_comments=124:0 imports_exports=6:12 calls_definitions=33:12
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Set
from uuid import uuid4

from db import db
from services.llm import DEFAULT_REGISTRY, reconcile_registry_developers

HUB_INSTANCE_COLLECTION = "hub_instances"
HUB_GROUP_COLLECTION = "hub_groups"
HUB_RUN_COLLECTION = "hub_runs"
HUB_RUN_STEP_COLLECTION = "hub_run_steps"
HUB_CHAT_PROMPT_COLLECTION = "hub_chat_prompts"
HUB_SYNTHESIS_BATCH_COLLECTION = "hub_synthesis_batches"


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def without_mongo_id(doc: Optional[dict]) -> Optional[dict]:
    if not doc:
        return doc
    clean = dict(doc)
    clean.pop("_id", None)
    return clean


async def get_registry_doc(user_id: str) -> dict:
    doc = await db.model_registry.find_one({"user_id": user_id}, {"_id": 0})
    if doc:
        developers, changed = reconcile_registry_developers(doc.get("developers", {}))
        if changed:
            updated_at = iso_now()
            doc["developers"] = developers
            doc["updated_at"] = updated_at
            await db.model_registry.update_one(
                {"user_id": user_id},
                {"$set": {"developers": developers, "updated_at": updated_at}},
            )
        return doc
    return {
        "user_id": user_id,
        "developers": reconcile_registry_developers(DEFAULT_REGISTRY)[0],
        "created_at": iso_now(),
        "updated_at": iso_now(),
    }


async def get_registry_model_ids(user_id: str) -> Set[str]:
    registry = await get_registry_doc(user_id)
    developers = registry.get("developers", {}) or {}
    model_ids: Set[str] = set()
    for dev in developers.values():
        for model in dev.get("models", []) or []:
            if isinstance(model, dict):
                model_id = model.get("model_id")
            else:
                model_id = model
            if model_id:
                model_ids.add(model_id)
    return model_ids


async def ensure_models_exist(user_id: str, model_ids: Iterable[str]) -> None:
    valid_ids = await get_registry_model_ids(user_id)
    missing = sorted({m for m in model_ids if m and m not in valid_ids})
    if missing:
        raise ValueError(f"Unknown model(s): {', '.join(missing)}")


async def get_instance(user_id: str, instance_id: str, include_archived: bool = True) -> Optional[dict]:
    query: Dict[str, Any] = {"user_id": user_id, "instance_id": instance_id}
    if not include_archived:
        query["archived"] = {"$ne": True}
    return without_mongo_id(await db[HUB_INSTANCE_COLLECTION].find_one(query, {"_id": 0}))


async def get_group(user_id: str, group_id: str, include_archived: bool = True) -> Optional[dict]:
    query: Dict[str, Any] = {"user_id": user_id, "group_id": group_id}
    if not include_archived:
        query["archived"] = {"$ne": True}
    return without_mongo_id(await db[HUB_GROUP_COLLECTION].find_one(query, {"_id": 0}))


async def ensure_thread(thread_id: str, user_id: str, title: str, extra: Optional[dict] = None) -> None:
    now = iso_now()
    payload = {
        "updated_at": now,
        "title": title[:120],
    }
    if extra:
        payload.update(extra)
    await db.threads.update_one(
        {"thread_id": thread_id, "user_id": user_id},
        {
            "$set": payload,
            "$setOnInsert": {
                "thread_id": thread_id,
                "user_id": user_id,
                "created_at": now,
            },
        },
        upsert=True,
    )


async def persist_message(
    *,
    thread_id: str,
    user_id: str,
    role: str,
    content: str,
    model: Optional[str],
    extra: Optional[dict] = None,
) -> dict:
    doc = {
        "message_id": make_id("msg"),
        "thread_id": thread_id,
        "user_id": user_id,
        "role": role,
        "content": content,
        "model": model,
        "timestamp": iso_now(),
    }
    if extra:
        doc.update(extra)
    await db.messages.insert_one(doc)
    return without_mongo_id(doc)


async def get_thread_messages(user_id: str, thread_id: str, limit: int = 50) -> List[dict]:
    cursor = (
        db.messages.find({"thread_id": thread_id, "user_id": user_id}, {"_id": 0})
        .sort("timestamp", 1)
        .limit(limit)
    )
    return await cursor.to_list(limit)


async def list_docs(collection: str, user_id: str, include_archived: bool = False, limit: int = 200) -> List[dict]:
    query: Dict[str, Any] = {"user_id": user_id}
    if not include_archived:
        query["archived"] = {"$ne": True}
    cursor = db[collection].find(query, {"_id": 0}).sort("updated_at", -1).limit(limit)
    return await cursor.to_list(limit)
# ratios: loc_comments=124:0 imports_exports=6:12 calls_definitions=33:12
