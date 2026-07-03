# ratios: loc_comments=500:0 imports_exports=11:5 calls_definitions=148:13
from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import HTTPException

from aimmh_lib import council, daisy_chain, fan_out, roleplay, room_all, room_synthesized
from aimmh_lib.adapters import make_call_fn

from models.hub import HubRunRequest, HubRunResult, HubRunDetailResponse, HubStageSummary
from models.lib_models import ROLE_PRESETS, verbosity_instruction
from services.auth import get_user_id
from services.events import emit_event
from services.hub_store import (
    HUB_GROUP_COLLECTION,
    HUB_INSTANCE_COLLECTION,
    HUB_RUN_COLLECTION,
    HUB_RUN_STEP_COLLECTION,
    ensure_models_exist,
    ensure_thread,
    get_group,
    get_instance,
    get_thread_messages,
    iso_now,
    list_docs,
    make_id,
    persist_message,
)
from db import db


def _compose_context(*parts: Optional[str]) -> Optional[str]:
    values = [part.strip() for part in parts if part and str(part).strip()]
    return "\n\n".join(values) if values else None


async def _expand_group_instances(user_id: str, group_id: str, visited: Optional[set[str]] = None) -> List[dict]:
    visited = visited or set()
    if group_id in visited:
        raise HTTPException(status_code=400, detail=f"Circular group nesting detected at {group_id}")
    visited.add(group_id)

    group = await get_group(user_id, group_id, include_archived=False)
    if not group:
        raise HTTPException(status_code=404, detail=f"Group not found: {group_id}")

    instances: List[dict] = []
    for member in group.get("members", []) or []:
        member_type = member.get("member_type")
        member_id = member.get("member_id")
        if member_type == "instance":
            instance = await get_instance(user_id, member_id, include_archived=False)
            if not instance:
                raise HTTPException(status_code=404, detail=f"Instance not found: {member_id}")
            instances.append(instance)
        elif member_type == "group":
            instances.extend(await _expand_group_instances(user_id, member_id, visited=set(visited)))
        else:
            raise HTTPException(status_code=422, detail=f"Unsupported group member type: {member_type}")
    return instances


async def _expand_participants(user_id: str, participants: list) -> List[dict]:
    instances: List[dict] = []
    for participant in participants:
        source_type = participant.source_type if hasattr(participant, "source_type") else participant.get("source_type")
        source_id = participant.source_id if hasattr(participant, "source_id") else participant.get("source_id")
        if source_type == "instance":
            instance = await get_instance(user_id, source_id, include_archived=False)
            if not instance:
                raise HTTPException(status_code=404, detail=f"Instance not found: {source_id}")
            instances.append(instance)
        elif source_type == "group":
            instances.extend(await _expand_group_instances(user_id, source_id))
        else:
            raise HTTPException(status_code=422, detail=f"Unsupported participant type: {source_type}")
    return instances


def _history_block(messages: List[dict], limit: int) -> Optional[str]:
    if limit <= 0 or not messages:
        return None
    tail = messages[-limit:]
    lines = []
    for message in tail:
        role = message.get("role", "unknown")
        content = (message.get("content") or "").strip()
        if not content:
            continue
        lines.append(f"{role.upper()}: {content}")
    if not lines:
        return None
    return "Your private instance thread history:\n" + "\n\n".join(lines)


async def _build_slot_context(instance: dict, verbosity: Optional[int]) -> Optional[str]:
    role_preset = instance.get("role_preset")
    preset_text = ROLE_PRESETS.get(role_preset.lower().strip()) if role_preset else None
    ctx = instance.get("context") or {}
    explicit_system = ctx.get("system_message")
    role_line = f"Your role: {ctx.get('role')}." if ctx.get("role") else None
    modifier = ctx.get("prompt_modifier")
    instance_prompt = instance.get("instance_prompt")
    thread_history = await get_thread_messages(
        instance["user_id"],
        instance["thread_id"],
        limit=max(1, int(instance.get("history_window_messages", 12) or 0)) if int(instance.get("history_window_messages", 12) or 0) > 0 else 1,
    ) if int(instance.get("history_window_messages", 12) or 0) > 0 else []
    history_block = _history_block(thread_history, int(instance.get("history_window_messages", 12) or 0))
    verbosity_text = verbosity_instruction(verbosity)
    return _compose_context(
        explicit_system or preset_text,
        role_line,
        modifier,
        f"Persistent instance prompt:\n{instance_prompt}" if instance_prompt else None,
        history_block,
        verbosity_text,
    )


def _outputs_text(results: List[HubRunResult]) -> str:
    lines = []
    for item in results:
        label = item.instance_name or item.model
        lines.append(f"[{label}] {item.content}")
    return "\n\n".join(lines)


def _stage_prompt(root_prompt: str, prior_results: List[HubRunResult], stage) -> str:
    stage_prompt = (stage.prompt or "").strip()
    if not prior_results:
        return stage_prompt or root_prompt

    prior_text = _outputs_text(prior_results)
    if stage.input_mode == "root_prompt":
        return stage_prompt or root_prompt
    if stage.input_mode == "previous_outputs":
        if stage_prompt:
            return f"{stage_prompt}\n\nPrevious stage outputs:\n{prior_text}"
        return prior_text

    pieces = []
    if stage_prompt:
        pieces.append(stage_prompt)
    else:
        pieces.append(root_prompt)
    pieces.append(f"Previous stage outputs:\n{prior_text}")
    return "\n\n".join(pieces)


async def _persist_instance_results(
    user_id: str,
    stage_prompt: str,
    stage_index: int,
    stage,
    instances_by_slot: Dict[int, dict],
    results: List[HubRunResult],
    persist_instance_threads: bool,
    run_id: str,
) -> Dict[str, str]:
    message_map: Dict[str, str] = {}
    if not persist_instance_threads:
        return message_map

    touched = set()
    for slot_idx, instance in instances_by_slot.items():
        touched.add(instance["instance_id"])
        await ensure_thread(
            instance["thread_id"],
            user_id,
            title=instance.get("name") or stage_prompt[:80],
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
            content=stage_prompt,
            model="hub_user",
            extra={
                "hub_run_id": run_id,
                "hub_stage_index": stage_index,
                "hub_pattern": stage.pattern,
                "hub_instance_id": instance["instance_id"],
                "hub_role": "input",
            },
        )

    for result in results:
        instance = instances_by_slot.get(result.slot_idx)
        if not instance and result.instance_id:
            instance = await get_instance(user_id, result.instance_id)
        if not instance:
            continue
        if instance["instance_id"] not in touched:
            touched.add(instance["instance_id"])
            await ensure_thread(
                instance["thread_id"],
                user_id,
                title=instance.get("name") or stage_prompt[:80],
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
                content=stage_prompt,
                model="hub_user",
                extra={
                    "hub_run_id": run_id,
                    "hub_stage_index": stage_index,
                    "hub_pattern": stage.pattern,
                    "hub_instance_id": instance["instance_id"],
                    "hub_role": "input",
                },
            )
        persisted = await persist_message(
            thread_id=instance["thread_id"],
            user_id=user_id,
            role="assistant",
            content=result.content,
            model=result.model,
            extra={
                "hub_run_id": run_id,
                "hub_stage_index": stage_index,
                "hub_pattern": stage.pattern,
                "hub_instance_id": instance["instance_id"],
                "hub_role": result.role,
                "response_time_ms": result.response_time_ms,
                "error": result.error,
                "round_num": result.round_num,
                "step_num": result.step_num,
                "slot_idx": result.slot_idx,
                "initiative": result.initiative,
            },
        )
        message_map[result.run_step_id] = persisted["message_id"]

    return message_map


async def execute_hub_run(current_user: dict, req: HubRunRequest) -> HubRunDetailResponse:
    user_id = get_user_id(current_user)
    run_id = make_id("hrun")
    now = iso_now()

    run_doc = {
        "run_id": run_id,
        "user_id": user_id,
        "label": req.label,
        "prompt": req.prompt,
        "status": "running",
        "archived": False,
        "archived_at": None,
        "stage_summaries": [],
        "created_at": now,
        "updated_at": now,
    }
    await db[HUB_RUN_COLLECTION].insert_one(run_doc)

    all_results: List[HubRunResult] = []
    stage_summaries: List[HubStageSummary] = []
    prior_stage_results: List[HubRunResult] = []
    call = make_call_fn(user=current_user)

    try:
        for stage_index, stage in enumerate(req.stages):
            prompt_used = _stage_prompt(req.prompt, prior_stage_results, stage)
            stage_results: List[HubRunResult] = []
            stage_name = stage.name or f"Stage {stage_index + 1}"
            stage_result_docs = []
            instances_by_slot: Dict[int, dict] = {}

            if stage.pattern == "roleplay":
                player_instances = await _expand_participants(user_id, stage.player_participants)
                if not player_instances:
                    raise HTTPException(status_code=422, detail=f"Stage {stage_index + 1} roleplay requires player_participants")
                dm_instances: List[dict] = []
                if stage.dm_instance_id:
                    dm_instance = await get_instance(user_id, stage.dm_instance_id, include_archived=False)
                    if not dm_instance:
                        raise HTTPException(status_code=404, detail=f"DM instance not found: {stage.dm_instance_id}")
                    dm_instances = [dm_instance]
                elif stage.dm_group_id:
                    dm_instances = await _expand_group_instances(user_id, stage.dm_group_id)
                    if not dm_instances:
                        raise HTTPException(status_code=422, detail=f"DM group has no active instances: {stage.dm_group_id}")

                await ensure_models_exist(
                    user_id,
                    [instance["model_id"] for instance in player_instances + dm_instances],
                )
                player_contexts = [await _build_slot_context(instance, stage.verbosity) for instance in player_instances]

                dm_model = dm_instances[0]["model_id"] if len(dm_instances) == 1 else None
                dm_rotation = [instance["model_id"] for instance in dm_instances] if len(dm_instances) > 1 else None
                dm_slot_context = await _build_slot_context(dm_instances[0], stage.verbosity) if len(dm_instances) == 1 else None
                dm_rotation_contexts = [await _build_slot_context(instance, stage.verbosity) for instance in dm_instances] if len(dm_instances) > 1 else None

                raw_results = await roleplay(
                    call,
                    player_models=[instance["model_id"] for instance in player_instances],
                    initial_prompt=prompt_used,
                    dm_model=dm_model,
                    dm_rotation=dm_rotation,
                    rounds=stage.rounds,
                    slot_contexts=player_contexts,
                    dm_slot_context=dm_slot_context,
                    dm_rotation_contexts=dm_rotation_contexts,
                    action_word_limit=stage.action_word_limit,
                    use_initiative=stage.use_initiative,
                    allow_reactions=stage.allow_reactions,
                    max_history=stage.max_history,
                )

                for idx, instance in enumerate(player_instances):
                    instances_by_slot[idx] = instance
                if len(dm_instances) == 1:
                    instances_by_slot[len(player_instances)] = dm_instances[0]

                for raw in raw_results:
                    mapped_instance = instances_by_slot.get(raw.slot_idx)
                    if raw.role == "dm" and len(dm_instances) > 1:
                        mapped_instance = dm_instances[raw.round_num % len(dm_instances)]
                    result = HubRunResult(
                        run_step_id=make_id("hrstep"),
                        run_id=run_id,
                        stage_index=stage_index,
                        stage_name=stage_name,
                        pattern=stage.pattern,
                        instance_id=mapped_instance.get("instance_id") if mapped_instance else None,
                        instance_name=mapped_instance.get("name") if mapped_instance else None,
                        thread_id=mapped_instance.get("thread_id") if mapped_instance else None,
                        model=raw.model,
                        content=raw.content,
                        response_time_ms=raw.response_time_ms,
                        error=raw.error,
                        round_num=raw.round_num,
                        step_num=raw.step_num,
                        initiative=raw.initiative,
                        role=raw.role,
                        slot_idx=raw.slot_idx,
                        created_at=iso_now(),
                    )
                    stage_results.append(result)
            else:
                if not stage.participants:
                    raise HTTPException(status_code=422, detail=f"Stage {stage_index + 1} requires participants")
                instances = await _expand_participants(user_id, stage.participants)
                if not instances:
                    raise HTTPException(status_code=422, detail=f"Stage {stage_index + 1} has no active instances")
                await ensure_models_exist(user_id, [instance["model_id"] for instance in instances])
                model_ids = [instance["model_id"] for instance in instances]
                slot_contexts = [await _build_slot_context(instance, stage.verbosity) for instance in instances]
                for idx, instance in enumerate(instances):
                    instances_by_slot[idx] = instance

                if stage.pattern == "fan_out":
                    raw_results = await fan_out(call, model_ids, [{"role": "user", "content": prompt_used}], slot_contexts)
                elif stage.pattern == "daisy_chain":
                    raw_results = await daisy_chain(
                        call,
                        model_ids,
                        prompt_used,
                        rounds=stage.rounds,
                        slot_contexts=slot_contexts,
                        include_original_prompt=stage.include_original_prompt,
                        max_history=stage.max_history,
                    )
                elif stage.pattern == "room_all":
                    raw_results = await room_all(
                        call,
                        model_ids,
                        prompt_used,
                        rounds=stage.rounds,
                        slot_contexts=slot_contexts,
                        max_history=stage.max_history,
                    )
                elif stage.pattern == "room_synthesized":
                    synth_instances: List[dict] = []
                    if stage.synthesis_instance_id:
                        synth = await get_instance(user_id, stage.synthesis_instance_id, include_archived=False)
                        if not synth:
                            raise HTTPException(status_code=404, detail=f"Synthesis instance not found: {stage.synthesis_instance_id}")
                        synth_instances = [synth]
                    elif stage.synthesis_group_id:
                        synth_instances = await _expand_group_instances(user_id, stage.synthesis_group_id)
                    if len(synth_instances) != 1:
                        raise HTTPException(status_code=422, detail=f"Stage {stage_index + 1} room_synthesized requires exactly one synthesis instance or single-member group")
                    synth_instance = synth_instances[0]
                    await ensure_models_exist(user_id, [synth_instance["model_id"]])
                    instances_by_slot[len(instances)] = synth_instance
                    raw_results = await room_synthesized(
                        call,
                        model_ids,
                        prompt_used,
                        synthesis_model=synth_instance["model_id"],
                        rounds=stage.rounds,
                        synthesis_prompt=stage.synthesis_prompt or "Synthesize and analyze these AI responses:",
                        slot_contexts=slot_contexts,
                        synth_slot_context=await _build_slot_context(synth_instance, stage.verbosity),
                        max_history=stage.max_history,
                    )
                elif stage.pattern == "council":
                    raw_results = await council(
                        call,
                        model_ids,
                        prompt_used,
                        rounds=stage.rounds,
                        synthesis_prompt=stage.synthesis_prompt or "Synthesize and analyze all model responses including your own:",
                        slot_contexts=slot_contexts,
                        max_history=stage.max_history,
                    )
                else:
                    raise HTTPException(status_code=422, detail=f"Unsupported pattern: {stage.pattern}")

                for raw in raw_results:
                    mapped_instance = instances_by_slot.get(raw.slot_idx)
                    result = HubRunResult(
                        run_step_id=make_id("hrstep"),
                        run_id=run_id,
                        stage_index=stage_index,
                        stage_name=stage_name,
                        pattern=stage.pattern,
                        instance_id=mapped_instance.get("instance_id") if mapped_instance else None,
                        instance_name=mapped_instance.get("name") if mapped_instance else None,
                        thread_id=mapped_instance.get("thread_id") if mapped_instance else None,
                        model=raw.model,
                        content=raw.content,
                        response_time_ms=raw.response_time_ms,
                        error=raw.error,
                        round_num=raw.round_num,
                        step_num=raw.step_num,
                        initiative=raw.initiative,
                        role=raw.role,
                        slot_idx=raw.slot_idx,
                        created_at=iso_now(),
                    )
                    stage_results.append(result)

            message_map = await _persist_instance_results(
                user_id=user_id,
                stage_prompt=prompt_used,
                stage_index=stage_index,
                stage=stage,
                instances_by_slot=instances_by_slot,
                results=stage_results,
                persist_instance_threads=req.persist_instance_threads,
                run_id=run_id,
            )

            for item in stage_results:
                if item.run_step_id in message_map:
                    item.message_id = message_map[item.run_step_id]
                step_doc = item.model_dump()
                step_doc["user_id"] = user_id
                stage_result_docs.append(step_doc)
            if stage_result_docs:
                await db[HUB_RUN_STEP_COLLECTION].insert_many(stage_result_docs)

            participant_names = [instance.get("name") or instance.get("instance_id") for _, instance in sorted(instances_by_slot.items(), key=lambda pair: pair[0])]
            stage_summary = HubStageSummary(
                stage_index=stage_index,
                stage_name=stage_name,
                pattern=stage.pattern,
                prompt_used=prompt_used,
                participants=participant_names,
                result_count=len(stage_results),
            )
            stage_summaries.append(stage_summary)
            prior_stage_results = stage_results
            all_results.extend(stage_results)

            await emit_event(
                event_type="hub_stage_completed",
                thread_id=f"hub_run:{run_id}",
                actor_id=f"user:{user_id}",
                payload={
                    "run_id": run_id,
                    "stage_index": stage_index,
                    "pattern": stage.pattern,
                    "result_count": len(stage_results),
                },
            )

        await db[HUB_RUN_COLLECTION].update_one(
            {"run_id": run_id, "user_id": user_id},
            {
                "$set": {
                    "status": "completed",
                    "stage_summaries": [summary.model_dump() for summary in stage_summaries],
                    "updated_at": iso_now(),
                }
            },
        )
    except HTTPException:
        await db[HUB_RUN_COLLECTION].update_one(
            {"run_id": run_id, "user_id": user_id},
            {"$set": {"status": "failed", "updated_at": iso_now()}},
        )
        raise
    except Exception as exc:
        await db[HUB_RUN_COLLECTION].update_one(
            {"run_id": run_id, "user_id": user_id},
            {"$set": {"status": "failed", "updated_at": iso_now(), "error": str(exc)}} ,
        )
        raise HTTPException(status_code=500, detail=f"Hub run failed: {exc}") from exc

    run_doc = await db[HUB_RUN_COLLECTION].find_one({"run_id": run_id, "user_id": user_id}, {"_id": 0})
    return HubRunDetailResponse(
        **run_doc,
        results=all_results,
    )


async def get_hub_run_detail(user_id: str, run_id: str) -> HubRunDetailResponse:
    run_doc = await db[HUB_RUN_COLLECTION].find_one({"run_id": run_id, "user_id": user_id}, {"_id": 0})
    if not run_doc:
        raise HTTPException(status_code=404, detail="Hub run not found")
    step_docs = await db[HUB_RUN_STEP_COLLECTION].find({"run_id": run_id, "user_id": user_id}, {"_id": 0}).sort([
        ("stage_index", 1),
        ("round_num", 1),
        ("step_num", 1),
        ("created_at", 1),
    ]).to_list(5000)
    return HubRunDetailResponse(
        **run_doc,
        results=[HubRunResult(**doc) for doc in step_docs],
    )


async def list_hub_runs(user_id: str, include_archived: bool = False, limit: int = 100) -> list[dict]:
    query = {"user_id": user_id}
    if not include_archived:
        query["archived"] = {"$ne": True}
    return await db[HUB_RUN_COLLECTION].find(query, {"_id": 0}).sort("updated_at", -1).limit(limit).to_list(limit)


async def list_hub_instances(user_id: str, include_archived: bool = False, limit: int = 200) -> list[dict]:
    return await list_docs(HUB_INSTANCE_COLLECTION, user_id, include_archived=include_archived, limit=limit)


async def list_hub_groups(user_id: str, include_archived: bool = False, limit: int = 200) -> list[dict]:
    return await list_docs(HUB_GROUP_COLLECTION, user_id, include_archived=include_archived, limit=limit)
# ratios: loc_comments=500:0 imports_exports=11:5 calls_definitions=148:13
