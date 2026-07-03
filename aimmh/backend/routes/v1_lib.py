# ratios: loc_comments=297:55 imports_exports=15:6 calls_definitions=88:14
"""
v1_lib.py — FastAPI routes wrapping lib/ conversation patterns.

Prefix: /api/v1/lib
Auth:   JWT / session / service-account (same as all other v1 routes)
Secrets: current_user.api_keys feeds make_call_fn; EMERGENT_LLM_KEY is the
         server-side fallback handled inside services/llm.py.

Patterns exposed:
    POST /fan-out          — parallel call to N model slots
    POST /daisy-chain      — sequential A→B→C chain
    POST /room-all         — shared room, all models see all responses
    POST /room-synthesized — one synthesizer combines responses each round
    POST /council          — every model synthesizes all responses (incl. own)
    POST /roleplay         — DM + players, initiative, reactions

Each request accepts:
    - slots: list[ModelSlot]       — model + optional context / role_preset
    - verbosity: int 1–10          — pop-culture length scale
    - persist: bool                — opt-in MongoDB thread + message + event log
    - thread_id: str               — use existing thread or auto-generate

sys.path injection at module top puts /home/user/aimmh on the path so
`from lib import ...` resolves alongside the backend's own `services` package.
"""

from __future__ import annotations

import os
import sys
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

# --- put repo root on path so `from lib import ...` resolves ---
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

from aimmh_lib import fan_out, daisy_chain, room_all, room_synthesized, council, roleplay
from aimmh_lib.conversations import ModelResult
from aimmh_lib.adapters import make_call_fn

from db import db
from services.auth import get_current_user
from services.events import emit_event
from models.lib_models import (
    FanOutRequest,
    DaisyChainRequest,
    RoomAllRequest,
    RoomSynthesizedRequest,
    CouncilRequest,
    RoleplayRequest,
    ModelSlot,
    LibResponse,
    LibModelResult,
    ROLE_PRESETS,
    verbosity_instruction,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/lib", tags=["lib"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slot_to_context(slot: ModelSlot, verbosity: Optional[int] = None) -> Optional[str]:
    """Merge role_preset + ModelContextOverride + verbosity into a single system string."""
    parts: list[str] = []

    # 1. Role preset base
    if slot.role_preset:
        preset = ROLE_PRESETS.get(slot.role_preset.lower().strip())
        if preset:
            parts.append(preset)
        else:
            logger.warning("Unknown role_preset %r — ignoring", slot.role_preset)

    # 2. Explicit context overrides (win over preset for the same field)
    if slot.context:
        if slot.context.system_message:
            # If we have a preset AND a system_message, system_message replaces the preset base
            if parts:
                parts = [slot.context.system_message]
            else:
                parts.append(slot.context.system_message)
        if slot.context.role:
            parts.append(f"Your role: {slot.context.role}.")
        if slot.context.prompt_modifier:
            parts.append(slot.context.prompt_modifier)

    # 3. Verbosity suffix
    verb = verbosity_instruction(verbosity)
    if verb:
        parts.append(verb)

    return "\n\n".join(parts) if parts else None


def _slots_to_contexts(slots: list[ModelSlot], verbosity: Optional[int] = None) -> Optional[list[Optional[str]]]:
    """Convert a list of ModelSlot → list[Optional[str]] aligned by index."""
    result = [_slot_to_context(s, verbosity) for s in slots]
    return result if any(r is not None for r in result) else None


def _model_ids(slots: list[ModelSlot]) -> list[str]:
    return [s.model_id for s in slots]


def _to_lib_result(r: ModelResult) -> LibModelResult:
    return LibModelResult(
        model=r.model,
        content=r.content,
        response_time_ms=r.response_time_ms,
        error=r.error,
        round_num=r.round_num,
        step_num=r.step_num,
        initiative=r.initiative,
        role=r.role,
        slot_idx=r.slot_idx,
    )


async def _persist_results(
    user_id: str,
    thread_id: str,
    prompt: str,
    pattern: str,
    results: list[ModelResult],
) -> None:
    """Upsert thread, insert user + assistant messages, emit one lib_pattern event."""
    now = _iso_now()

    # 1. Thread upsert
    await db.threads.update_one(
        {"thread_id": thread_id, "user_id": user_id},
        {
            "$set": {"updated_at": now, "title": prompt[:80]},
            "$setOnInsert": {
                "thread_id": thread_id,
                "user_id": user_id,
                "created_at": now,
                "pattern": pattern,
            },
        },
        upsert=True,
    )

    # 2. User prompt message
    await db.messages.insert_one({
        "message_id": f"msg_{uuid4().hex}",
        "thread_id": thread_id,
        "user_id": user_id,
        "role": "user",
        "content": prompt,
        "model": None,
        "timestamp": now,
        "pattern": pattern,
    })

    # 3. One assistant message per ModelResult
    for r in results:
        await db.messages.insert_one({
            "message_id": f"msg_{uuid4().hex}",
            "thread_id": thread_id,
            "user_id": user_id,
            "role": "assistant",
            "content": r.content,
            "model": r.model,
            "timestamp": _iso_now(),
            "response_time_ms": r.response_time_ms,
            "error": r.error,
            "round_num": r.round_num,
            "step_num": r.step_num,
            "lib_role": r.role,
            "initiative": r.initiative,
            "slot_idx": r.slot_idx,
            "pattern": pattern,
        })

    # 4. Single append-only event for the call
    await emit_event(
        event_type="lib_pattern",
        thread_id=thread_id,
        actor_id=f"user:{user_id}",
        payload={
            "pattern": pattern,
            "model_count": len(results),
            "prompt_preview": prompt[:120],
        },
    )


def _resolve_thread(thread_id: Optional[str]) -> str:
    return thread_id or f"lib_{uuid4().hex}"


def _user_id(user: dict) -> str:
    return str(user.get("user_id") or user.get("id") or "unknown")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/fan-out", response_model=LibResponse, summary="Parallel fan-out to N model slots")
async def lib_fan_out(
    req: FanOutRequest,
    current_user: dict = Depends(get_current_user),
) -> LibResponse:
    """Call all slots in parallel with the same prompt. Returns results in slot order."""
    call = make_call_fn(user=current_user)
    model_ids = _model_ids(req.slots)
    slot_ctxs = _slots_to_contexts(req.slots, req.verbosity)
    messages = [{"role": "user", "content": req.prompt}]

    results = await fan_out(call, model_ids, messages, slot_ctxs)

    thread_id = None
    if req.persist:
        thread_id = _resolve_thread(req.thread_id)
        await _persist_results(_user_id(current_user), thread_id, req.prompt, "fan_out", results)

    return LibResponse(
        results=[_to_lib_result(r) for r in results],
        pattern="fan_out",
        thread_id=thread_id,
    )


@router.post("/daisy-chain", response_model=LibResponse, summary="Sequential chain: slot[0]→slot[1]→…")
async def lib_daisy_chain(
    req: DaisyChainRequest,
    current_user: dict = Depends(get_current_user),
) -> LibResponse:
    """Each model's response becomes the next model's prompt, across N rounds."""
    call = make_call_fn(user=current_user)
    model_ids = _model_ids(req.slots)
    slot_ctxs = _slots_to_contexts(req.slots, req.verbosity)

    results = await daisy_chain(
        call, model_ids, req.prompt,
        rounds=req.rounds,
        slot_contexts=slot_ctxs,
        include_original_prompt=req.include_original_prompt,
        max_history=req.max_history,
    )

    thread_id = None
    if req.persist:
        thread_id = _resolve_thread(req.thread_id)
        await _persist_results(_user_id(current_user), thread_id, req.prompt, "daisy_chain", results)

    return LibResponse(
        results=[_to_lib_result(r) for r in results],
        pattern="daisy_chain",
        thread_id=thread_id,
    )


@router.post("/room-all", response_model=LibResponse, summary="Shared room: all models see all responses")
async def lib_room_all(
    req: RoomAllRequest,
    current_user: dict = Depends(get_current_user),
) -> LibResponse:
    """All models respond in parallel, then see each other's responses and respond again."""
    call = make_call_fn(user=current_user)
    model_ids = _model_ids(req.slots)
    slot_ctxs = _slots_to_contexts(req.slots, req.verbosity)

    results = await room_all(
        call, model_ids, req.prompt,
        rounds=req.rounds,
        slot_contexts=slot_ctxs,
        max_history=req.max_history,
    )

    thread_id = None
    if req.persist:
        thread_id = _resolve_thread(req.thread_id)
        await _persist_results(_user_id(current_user), thread_id, req.prompt, "room_all", results)

    return LibResponse(
        results=[_to_lib_result(r) for r in results],
        pattern="room_all",
        thread_id=thread_id,
    )


@router.post("/room-synthesized", response_model=LibResponse, summary="Synthesis model combines all responses each round")
async def lib_room_synthesized(
    req: RoomSynthesizedRequest,
    current_user: dict = Depends(get_current_user),
) -> LibResponse:
    """All player slots respond in parallel; synthesis_slot combines them; synthesis drives next round.

    Results with step_num=-1 are synthesis outputs.
    Filter player responses: [r for r in results if r.step_num >= 0]
    """
    call = make_call_fn(user=current_user)
    model_ids = _model_ids(req.slots)
    slot_ctxs = _slots_to_contexts(req.slots, req.verbosity)
    synth_ctx = _slot_to_context(req.synthesis_slot, req.verbosity)

    results = await room_synthesized(
        call, model_ids, req.prompt,
        synthesis_model=req.synthesis_slot.model_id,
        rounds=req.rounds,
        synthesis_prompt=req.synthesis_prompt,
        slot_contexts=slot_ctxs,
        synth_slot_context=synth_ctx,
        max_history=req.max_history,
    )

    thread_id = None
    if req.persist:
        thread_id = _resolve_thread(req.thread_id)
        await _persist_results(_user_id(current_user), thread_id, req.prompt, "room_synthesized", results)

    return LibResponse(
        results=[_to_lib_result(r) for r in results],
        pattern="room_synthesized",
        thread_id=thread_id,
    )


@router.post("/council", response_model=LibResponse, summary="Every model synthesizes all responses in parallel")
async def lib_council(
    req: CouncilRequest,
    current_user: dict = Depends(get_current_user),
) -> LibResponse:
    """Each model produces its own synthesis of ALL responses (including its own), concurrently.

    step_num=0 → initial responses; step_num=1 → per-model syntheses.
    """
    call = make_call_fn(user=current_user)
    model_ids = _model_ids(req.slots)
    slot_ctxs = _slots_to_contexts(req.slots, req.verbosity)

    results = await council(
        call, model_ids, req.prompt,
        rounds=req.rounds,
        synthesis_prompt=req.synthesis_prompt,
        slot_contexts=slot_ctxs,
        max_history=req.max_history,
    )

    thread_id = None
    if req.persist:
        thread_id = _resolve_thread(req.thread_id)
        await _persist_results(_user_id(current_user), thread_id, req.prompt, "council", results)

    return LibResponse(
        results=[_to_lib_result(r) for r in results],
        pattern="council",
        thread_id=thread_id,
    )


@router.post("/roleplay", response_model=LibResponse, summary="DM-driven roleplay with initiative and reactions")
async def lib_roleplay(
    req: RoleplayRequest,
    current_user: dict = Depends(get_current_user),
) -> LibResponse:
    """DM narrates, players act in initiative order, optional reactions between turns.

    Filter results:
        players:   [r for r in results if r.role == "player"]
        dm turns:  [r for r in results if r.role == "dm"]
        reactions: [r for r in results if r.role == "reaction"]
    """
    if req.dm_slot and req.dm_rotation:
        raise HTTPException(status_code=422, detail="Provide dm_slot or dm_rotation, not both.")

    call = make_call_fn(user=current_user)
    player_model_ids = _model_ids(req.player_slots)
    player_ctxs = _slots_to_contexts(req.player_slots, req.verbosity)

    dm_model: Optional[str] = None
    dm_ctx: Optional[str] = None
    dm_rotation_ids: Optional[list[str]] = None
    dm_rotation_ctxs: Optional[list[Optional[str]]] = None

    if req.dm_slot:
        dm_model = req.dm_slot.model_id
        dm_ctx = _slot_to_context(req.dm_slot, req.verbosity)
    elif req.dm_rotation:
        dm_rotation_ids = [s.model_id for s in req.dm_rotation]
        dm_rotation_ctxs = [_slot_to_context(s, req.verbosity) for s in req.dm_rotation]

    results = await roleplay(
        call,
        player_models=player_model_ids,
        initial_prompt=req.initial_prompt,
        dm_model=dm_model,
        dm_rotation=dm_rotation_ids,
        rounds=req.rounds,
        slot_contexts=player_ctxs,
        dm_slot_context=dm_ctx,
        dm_rotation_contexts=dm_rotation_ctxs,
        action_word_limit=req.action_word_limit,
        use_initiative=req.use_initiative,
        allow_reactions=req.allow_reactions,
        max_history=req.max_history,
    )

    thread_id = None
    if req.persist:
        thread_id = _resolve_thread(req.thread_id)
        await _persist_results(_user_id(current_user), thread_id, req.initial_prompt, "roleplay", results)

    return LibResponse(
        results=[_to_lib_result(r) for r in results],
        pattern="roleplay",
        thread_id=thread_id,
    )
# ratios: loc_comments=297:55 imports_exports=15:6 calls_definitions=88:14
