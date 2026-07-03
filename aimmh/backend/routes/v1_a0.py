# ratios: loc_comments=571:67 imports_exports=15:12 calls_definitions=248:20
"""V1 a0 API — Core multi-model hub endpoints.

Endpoints:
  POST /v1/a0/prompt          — Fan-out to N models, streaming SSE or collected
  POST /v1/a0/prompt-single   — Single model call
  POST /v1/a0/synthesize      — Feed responses into other models
  POST /v1/a0/batch           — Sequential prompt chains
  GET  /v1/a0/history         — Thread list
  GET  /v1/a0/thread/{id}     — Thread messages
  GET  /v1/a0/export/{id}     — Full export with events
  POST /v1/a0/feedback        — Thumbs up/down
  GET  /v1/a0/jobs/{id}       — Poll async job status
"""

import asyncio
import json
import math
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sse_starlette.sse import EventSourceResponse

from db import db
from models.v1 import (
    AsyncJobResponse,
    BatchRequest,
    DaisyChainRequest,
    ExportResponse,
    FeedbackRequest,
    JobStatusResponse,
    MessageOut,
    ModelResponse,
    PromptRequest,
    PromptResponse,
    PromptSingleRequest,
    SharedRoomRequest,
    SynthesizeRequest,
    ThreadListResponse,
    ThreadSummary,
)
from services.auth import get_current_user, get_user_id
from services.events import build_provenance, build_sentinel_context, emit_event
from services.llm import DEFAULT_REGISTRY, generate_response, reconcile_registry_developers

router = APIRouter(prefix="/api/v1/a0", tags=["a0"])

# In-memory async job store (keyed by job_id)
_jobs: Dict[str, Dict[str, Any]] = {}


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _estimate_tokens(text: str) -> int:
    return max(1, math.ceil(len(text) / 4)) if text else 0


async def _get_user_registry(user: dict) -> dict:
    """Get the user's model registry, falling back to defaults."""
    uid = get_user_id(user)
    custom = await db.model_registry.find_one({"user_id": uid}, {"_id": 0})
    if custom and custom.get("developers"):
        return reconcile_registry_developers(custom["developers"])[0]
    return reconcile_registry_developers(DEFAULT_REGISTRY)[0]


async def _ensure_thread(thread_id: str, user_id: str, title: str):
    """Ensure thread document exists (upsert)."""
    await db.threads.update_one(
        {"thread_id": thread_id, "user_id": user_id},
        {
            "$set": {"updated_at": _iso_now(), "title": title[:80]},
            "$setOnInsert": {
                "thread_id": thread_id,
                "user_id": user_id,
                "created_at": _iso_now(),
            },
        },
        upsert=True,
    )


async def _persist_message(
    message_id: str,
    thread_id: str,
    user_id: str,
    role: str,
    content: str,
    model: str,
    response_time_ms: int = 0,
    streaming: bool = False,
) -> None:
    """Upsert a message document. Used for chunk-by-chunk persistence."""
    await db.messages.update_one(
        {"message_id": message_id},
        {
            "$set": {
                "content": content,
                "response_time_ms": response_time_ms,
                "streaming": streaming,
                "updated_at": _iso_now(),
            },
            "$setOnInsert": {
                "message_id": message_id,
                "thread_id": thread_id,
                "user_id": user_id,
                "role": role,
                "model": model,
                "timestamp": _iso_now(),
                "feedback": None,
            },
        },
        upsert=True,
    )


async def _run_model(
    model_id: str,
    messages_context: List[dict],
    thread_id: str,
    user_id: str,
    user: dict,
    registry: dict,
) -> ModelResponse:
    """Run a single model call, persist chunk-by-chunk, return final response."""
    message_id = f"msg_{uuid.uuid4().hex[:16]}"
    t_start = time.time()
    full_response = ""

    # Create placeholder message immediately
    await _persist_message(message_id, thread_id, user_id, "assistant", "", model_id, streaming=True)

    async for chunk in generate_response(model_id, messages_context, thread_id, user, registry):
        full_response += chunk
        # Persist every ~500 chars to not overwhelm DB
        if len(full_response) % 500 < len(chunk):
            await _persist_message(message_id, thread_id, user_id, "assistant", full_response, model_id, streaming=True)

    response_time_ms = int((time.time() - t_start) * 1000)

    # Final persist with streaming=False
    await _persist_message(message_id, thread_id, user_id, "assistant", full_response, model_id, response_time_ms, streaming=False)

    error = None
    if full_response.startswith("[ERROR]"):
        error = full_response

    await emit_event(
        "turn",
        thread_id,
        f"model:{model_id}",
        {
            "message_id": message_id,
            "model": model_id,
            "role": "assistant",
            "content_length": len(full_response),
            "response_time_ms": response_time_ms,
            "error": error,
        },
    )

    return ModelResponse(
        model=model_id,
        message_id=message_id,
        content=full_response,
        response_time_ms=response_time_ms,
        error=error,
    )


def _build_context(
    messages: List[dict],
    per_model_prompt: str,
    global_context: str = "",
    system_override: str = "",
    role_override: str = "",
    prompt_modifier: str = "",
) -> List[dict]:
    """Build the messages context list for an LLM call."""
    ctx = []

    # Previous conversation turns
    for msg in messages[-30:]:
        ctx.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})

    # Build the current user message with context additions
    parts = []
    if global_context:
        parts.append(f"[GLOBAL CONTEXT]: {global_context}")
    if role_override:
        parts.append(f"[ROLE]: {role_override}")
    if prompt_modifier:
        parts.append(f"[MODIFIER]: {prompt_modifier}")
    parts.append(per_model_prompt)

    final_msg = "\n\n".join(parts)

    # Replace last user message or append
    if ctx and ctx[-1]["role"] == "user":
        ctx[-1] = {"role": "user", "content": final_msg}
    else:
        ctx.append({"role": "user", "content": final_msg})

    return ctx


# ---- STREAMING ENDPOINT (primary for UI) ----

@router.post("/prompt/stream")
async def prompt_stream(
    request: PromptRequest,
    current_user: dict = Depends(get_current_user),
):
    """Stream responses from multiple models via SSE."""
    async def event_gen():
        user_id = get_user_id(current_user)
        thread_id = request.thread_id or f"thr_{uuid.uuid4().hex[:16]}"
        registry = await _get_user_registry(current_user)

        await _ensure_thread(thread_id, user_id, request.message[:80])

        # Persist user message
        user_msg_id = f"msg_{uuid.uuid4().hex[:16]}"
        await _persist_message(user_msg_id, thread_id, user_id, "user", request.message, "user")
        await emit_event("turn", thread_id, f"user:{user_id}", {
            "message_id": user_msg_id, "role": "user", "content_length": len(request.message),
        })

        # Get conversation history
        history = await db.messages.find(
            {"thread_id": thread_id, "user_id": user_id},
            {"_id": 0},
        ).sort("timestamp", 1).limit(30).to_list(30)

        for model_id in request.models:
            message_id = f"msg_{uuid.uuid4().hex[:16]}"
            t_start = time.time()

            # Build per-model context
            pmc = (request.per_model_context or {}).get(model_id)
            ctx = _build_context(
                history,
                request.message,
                global_context=request.global_context or "",
                role_override=pmc.role if pmc and pmc.role else "",
                prompt_modifier=pmc.prompt_modifier if pmc and pmc.prompt_modifier else "",
            )

            # Create placeholder
            await _persist_message(message_id, thread_id, user_id, "assistant", "", model_id, streaming=True)

            yield {"event": "start", "data": json.dumps({"model": model_id, "message_id": message_id, "thread_id": thread_id})}

            full_response = ""
            async for chunk in generate_response(model_id, ctx, thread_id, current_user, registry):
                full_response += chunk
                yield {"event": "chunk", "data": json.dumps({"model": model_id, "message_id": message_id, "content": chunk})}
                # Persist periodically
                if len(full_response) % 500 < len(chunk):
                    await _persist_message(message_id, thread_id, user_id, "assistant", full_response, model_id, streaming=True)

            response_time_ms = int((time.time() - t_start) * 1000)
            await _persist_message(message_id, thread_id, user_id, "assistant", full_response, model_id, response_time_ms, streaming=False)

            await emit_event("turn", thread_id, f"model:{model_id}", {
                "message_id": message_id, "model": model_id, "response_time_ms": response_time_ms,
                "content_length": len(full_response),
            })

            yield {"event": "complete", "data": json.dumps({"model": model_id, "message_id": message_id, "response_time_ms": response_time_ms})}

        # Update thread
        await db.threads.update_one(
            {"thread_id": thread_id, "user_id": user_id},
            {"$set": {"updated_at": _iso_now()}},
        )

    return EventSourceResponse(
        event_gen(),
        headers={
            "X-Accel-Buffering": "no",
            "Cache-Control": "no-cache, no-transform",
        },
    )


# ---- COLLECTED ENDPOINT (for a0 — returns full responses) ----

@router.post("/prompt", response_model=PromptResponse)
async def prompt_collected(
    request: PromptRequest,
    current_user: dict = Depends(get_current_user),
):
    """Fan-out to N models, collect all responses, return as JSON."""
    user_id = get_user_id(current_user)
    thread_id = request.thread_id or f"thr_{uuid.uuid4().hex[:16]}"
    registry = await _get_user_registry(current_user)

    await _ensure_thread(thread_id, user_id, request.message[:80])

    # Persist user message
    user_msg_id = f"msg_{uuid.uuid4().hex[:16]}"
    await _persist_message(user_msg_id, thread_id, user_id, "user", request.message, "user")
    evt = await emit_event("turn", thread_id, f"user:{user_id}", {
        "message_id": user_msg_id, "role": "user",
    })

    # Get history
    history = await db.messages.find(
        {"thread_id": thread_id, "user_id": user_id}, {"_id": 0},
    ).sort("timestamp", 1).limit(30).to_list(30)

    # If async mode, create job and return immediately
    if request.async_mode:
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        _jobs[job_id] = {"status": "running", "thread_id": thread_id, "responses": [], "event_ids": [evt["event_id"]]}

        async def _run_async():
            for model_id in request.models:
                pmc = (request.per_model_context or {}).get(model_id)
                ctx = _build_context(history, request.message, request.global_context or "",
                                     pmc.role if pmc and pmc.role else "",
                                     pmc.prompt_modifier if pmc and pmc.prompt_modifier else "")
                resp = await _run_model(model_id, ctx, thread_id, user_id, current_user, registry)
                _jobs[job_id]["responses"].append(resp.model_dump())
            _jobs[job_id]["status"] = "completed"

        asyncio.create_task(_run_async())
        return PromptResponse(
            thread_id=thread_id,
            responses=[],
            event_ids=[evt["event_id"]],
            provenance=build_provenance(),
            sentinel_context=build_sentinel_context(),
        )

    # Synchronous: run all models concurrently
    tasks = []
    for model_id in request.models:
        pmc = (request.per_model_context or {}).get(model_id)
        ctx = _build_context(history, request.message, request.global_context or "",
                             pmc.role if pmc and pmc.role else "",
                             pmc.prompt_modifier if pmc and pmc.prompt_modifier else "")
        tasks.append(_run_model(model_id, ctx, thread_id, user_id, current_user, registry))

    responses = await asyncio.gather(*tasks)

    return PromptResponse(
        thread_id=thread_id,
        responses=list(responses),
        event_ids=[evt["event_id"]],
        provenance=build_provenance(),
        sentinel_context=build_sentinel_context(),
    )


@router.post("/prompt-single", response_model=PromptResponse)
async def prompt_single(
    request: PromptSingleRequest,
    current_user: dict = Depends(get_current_user),
):
    """Single model call."""
    user_id = get_user_id(current_user)
    thread_id = request.thread_id or f"thr_{uuid.uuid4().hex[:16]}"
    registry = await _get_user_registry(current_user)

    await _ensure_thread(thread_id, user_id, request.message[:80])

    user_msg_id = f"msg_{uuid.uuid4().hex[:16]}"
    await _persist_message(user_msg_id, thread_id, user_id, "user", request.message, "user")

    history = await db.messages.find(
        {"thread_id": thread_id, "user_id": user_id}, {"_id": 0},
    ).sort("timestamp", 1).limit(30).to_list(30)

    ctx = _build_context(history, request.message, request.global_context or "",
                         system_override=request.system_message or "")
    resp = await _run_model(request.model, ctx, thread_id, user_id, current_user, registry)

    return PromptResponse(
        thread_id=thread_id,
        responses=[resp],
        provenance=build_provenance(model=request.model),
        sentinel_context=build_sentinel_context(),
    )


@router.post("/synthesize", response_model=PromptResponse)
async def synthesize(
    request: SynthesizeRequest,
    current_user: dict = Depends(get_current_user),
):
    """Feed one or more model responses into other models as a new prompt."""
    user_id = get_user_id(current_user)
    registry = await _get_user_registry(current_user)

    # Fetch source messages
    source_msgs = []
    for mid in request.source_message_ids:
        msg = await db.messages.find_one({"message_id": mid, "user_id": user_id}, {"_id": 0})
        if msg:
            source_msgs.append(msg)

    if not source_msgs:
        raise HTTPException(status_code=404, detail="No source messages found")

    # Build synthesis prompt
    response_texts = []
    for msg in source_msgs:
        model_name = msg.get("model", "unknown")
        response_texts.append(f"Response from {model_name}:\n{msg.get('content', '')}")

    combined = f"{request.synthesis_prompt}\n\n" + "\n\n---\n\n".join(response_texts)

    thread_id = request.thread_id or source_msgs[0].get("thread_id", f"thr_{uuid.uuid4().hex[:16]}")
    await _ensure_thread(thread_id, user_id, f"Synthesis: {request.synthesis_prompt[:60]}")

    # Persist synthesis prompt as user message
    user_msg_id = f"msg_{uuid.uuid4().hex[:16]}"
    await _persist_message(user_msg_id, thread_id, user_id, "user", combined, "synthesis")
    await emit_event("turn", thread_id, f"user:{user_id}", {
        "message_id": user_msg_id, "role": "user", "type": "synthesis",
        "source_ids": request.source_message_ids,
    })

    history = await db.messages.find(
        {"thread_id": thread_id, "user_id": user_id}, {"_id": 0},
    ).sort("timestamp", 1).limit(30).to_list(30)

    tasks = []
    for model_id in request.target_models:
        ctx = _build_context(history, combined)
        tasks.append(_run_model(model_id, ctx, thread_id, user_id, current_user, registry))

    responses = await asyncio.gather(*tasks)

    return PromptResponse(
        thread_id=thread_id,
        responses=list(responses),
        provenance=build_provenance(),
        sentinel_context=build_sentinel_context(),
    )


@router.post("/batch", response_model=PromptResponse)
async def batch_chain(
    request: BatchRequest,
    current_user: dict = Depends(get_current_user),
):
    """Sequential prompt chains — same room, individual rooms, or combos."""
    user_id = get_user_id(current_user)
    thread_id = request.thread_id or f"thr_{uuid.uuid4().hex[:16]}"
    registry = await _get_user_registry(current_user)

    await _ensure_thread(thread_id, user_id, f"Batch: {request.steps[0].message[:60]}" if request.steps else "Batch")

    all_responses: List[ModelResponse] = []
    prev_responses: Dict[str, str] = {}  # model -> last response content

    for step_idx, step in enumerate(request.steps):
        # Build message with optional previous responses
        msg = step.message
        if step.feed_responses_to_next and prev_responses:
            feed_text = "\n\n---\n\n".join(
                f"Previous response from {m}:\n{c}" for m, c in prev_responses.items()
            )
            msg = f"{msg}\n\n[PREVIOUS RESPONSES]\n{feed_text}"

        # Persist step's user message
        user_msg_id = f"msg_{uuid.uuid4().hex[:16]}"
        await _persist_message(user_msg_id, thread_id, user_id, "user", msg, "batch")

        history = await db.messages.find(
            {"thread_id": thread_id, "user_id": user_id}, {"_id": 0},
        ).sort("timestamp", 1).limit(30).to_list(30)

        step_responses = []
        for model_id in step.models:
            pmc = (step.per_model_context or {}).get(model_id)
            ctx = _build_context(history, msg, role_override=pmc.role if pmc and pmc.role else "",
                                 prompt_modifier=pmc.prompt_modifier if pmc and pmc.prompt_modifier else "")
            resp = await _run_model(model_id, ctx, thread_id, user_id, current_user, registry)
            step_responses.append(resp)
            prev_responses[model_id] = resp.content

        all_responses.extend(step_responses)

    return PromptResponse(
        thread_id=thread_id,
        responses=all_responses,
        provenance=build_provenance(),
        sentinel_context=build_sentinel_context(),
    )


@router.post("/shared-room", response_model=PromptResponse)
async def shared_room(
    request: SharedRoomRequest,
    current_user: dict = Depends(get_current_user),
):
    """Shared room: models respond, then see each other's responses for N rounds.

    mode="all": each model gets every other model's response
    mode="synthesized": responses are synthesized first, then shared
    """
    user_id = get_user_id(current_user)
    thread_id = request.thread_id or f"thr_{uuid.uuid4().hex[:16]}"
    registry = await _get_user_registry(current_user)

    await _ensure_thread(thread_id, user_id, f"Shared Room: {request.message[:60]}")

    # Persist initial user message
    user_msg_id = f"msg_{uuid.uuid4().hex[:16]}"
    await _persist_message(user_msg_id, thread_id, user_id, "user", request.message, "user")
    await emit_event("turn", thread_id, f"user:{user_id}", {
        "message_id": user_msg_id, "role": "user", "type": "shared_room",
        "mode": request.mode, "rounds": request.rounds,
    })

    all_responses: List[ModelResponse] = []

    for round_num in range(request.rounds):
        if round_num == 0:
            # First round: normal fan-out
            tasks = []
            for model_id in request.models:
                pmc = (request.per_model_context or {}).get(model_id)
                history = await db.messages.find(
                    {"thread_id": thread_id, "user_id": user_id}, {"_id": 0},
                ).sort("timestamp", 1).limit(30).to_list(30)
                ctx = _build_context(
                    history, request.message,
                    global_context=request.global_context or "",
                    role_override=pmc.role if pmc and pmc.role else "",
                    prompt_modifier=pmc.prompt_modifier if pmc and pmc.prompt_modifier else "",
                )
                tasks.append(_run_model(model_id, ctx, thread_id, user_id, current_user, registry))
            round_responses = await asyncio.gather(*tasks)
            all_responses.extend(round_responses)
        else:
            # Subsequent rounds: share previous round's responses
            prev_round = all_responses[-(len(request.models)):]

            if request.mode == "synthesized" and request.synthesis_model:
                # Synthesize first, then share synthesis
                synth_input = "\n\n---\n\n".join(
                    f"Response from {r.model}:\n{r.content}" for r in prev_round if not r.error
                )
                synth_prompt = f"[ROUND {round_num} SYNTHESIS]\nSynthesize these model responses:\n\n{synth_input}"
                synth_msg_id = f"msg_{uuid.uuid4().hex[:16]}"
                await _persist_message(synth_msg_id, thread_id, user_id, "user", synth_prompt, "synthesis")

                synth_history = await db.messages.find(
                    {"thread_id": thread_id, "user_id": user_id}, {"_id": 0},
                ).sort("timestamp", 1).limit(30).to_list(30)
                synth_ctx = _build_context(synth_history, synth_prompt, global_context=request.global_context or "")
                synth_resp = await _run_model(request.synthesis_model, synth_ctx, thread_id, user_id, current_user, registry)
                all_responses.append(synth_resp)

                # Now share synthesis with all models
                share_text = f"[ROUND {round_num + 1} — respond to the synthesis]\n\nSynthesis by {request.synthesis_model}:\n{synth_resp.content}\n\nOriginal prompt: {request.message}"
            else:
                # Share all responses directly
                share_text = f"[ROUND {round_num + 1} — respond after seeing other models' responses]\n\n"
                share_text += "\n\n---\n\n".join(
                    f"Response from {r.model}:\n{r.content}" for r in prev_round if not r.error
                )
                share_text += f"\n\nOriginal prompt: {request.message}"

            share_msg_id = f"msg_{uuid.uuid4().hex[:16]}"
            await _persist_message(share_msg_id, thread_id, user_id, "user", share_text, "shared_room")

            tasks = []
            for model_id in request.models:
                pmc = (request.per_model_context or {}).get(model_id)
                history = await db.messages.find(
                    {"thread_id": thread_id, "user_id": user_id}, {"_id": 0},
                ).sort("timestamp", 1).limit(30).to_list(30)
                ctx = _build_context(
                    history, share_text,
                    global_context=request.global_context or "",
                    role_override=pmc.role if pmc and pmc.role else "",
                    prompt_modifier=pmc.prompt_modifier if pmc and pmc.prompt_modifier else "",
                )
                tasks.append(_run_model(model_id, ctx, thread_id, user_id, current_user, registry))
            round_responses = await asyncio.gather(*tasks)
            all_responses.extend(round_responses)

    return PromptResponse(
        thread_id=thread_id,
        responses=all_responses,
        provenance=build_provenance(),
        sentinel_context=build_sentinel_context(),
    )


@router.post("/daisy-chain", response_model=PromptResponse)
async def daisy_chain(
    request: DaisyChainRequest,
    current_user: dict = Depends(get_current_user),
):
    """Daisy chain: model[0] → model[1] → ... → model[n] for N rounds.

    Each model's response becomes the next model's prompt.
    A round = each model gives one response.
    """
    user_id = get_user_id(current_user)
    thread_id = request.thread_id or f"thr_{uuid.uuid4().hex[:16]}"
    registry = await _get_user_registry(current_user)

    await _ensure_thread(thread_id, user_id, f"Daisy Chain: {request.message[:60]}")

    # Persist initial user message
    user_msg_id = f"msg_{uuid.uuid4().hex[:16]}"
    await _persist_message(user_msg_id, thread_id, user_id, "user", request.message, "user")
    await emit_event("turn", thread_id, f"user:{user_id}", {
        "message_id": user_msg_id, "role": "user", "type": "daisy_chain",
        "rounds": request.rounds, "chain": request.models,
    })

    all_responses: List[ModelResponse] = []
    last_response_content = request.message

    for round_num in range(request.rounds):
        for model_idx, model_id in enumerate(request.models):
            pmc = (request.per_model_context or {}).get(model_id)

            if round_num == 0 and model_idx == 0:
                prompt_text = request.message
            else:
                prev_model = all_responses[-1].model if all_responses else "user"
                prompt_text = f"[Chain Round {round_num + 1}, Step {model_idx + 1}]\n\nPrevious response from {prev_model}:\n{last_response_content}\n\nOriginal prompt: {request.message}"

            chain_msg_id = f"msg_{uuid.uuid4().hex[:16]}"
            await _persist_message(chain_msg_id, thread_id, user_id, "user", prompt_text, "daisy_chain")

            history = await db.messages.find(
                {"thread_id": thread_id, "user_id": user_id}, {"_id": 0},
            ).sort("timestamp", 1).limit(30).to_list(30)

            ctx = _build_context(
                history, prompt_text,
                global_context=request.global_context or "",
                role_override=pmc.role if pmc and pmc.role else "",
                prompt_modifier=pmc.prompt_modifier if pmc and pmc.prompt_modifier else "",
            )
            resp = await _run_model(model_id, ctx, thread_id, user_id, current_user, registry)
            all_responses.append(resp)
            last_response_content = resp.content

    return PromptResponse(
        thread_id=thread_id,
        responses=all_responses,
        provenance=build_provenance(),
        sentinel_context=build_sentinel_context(),
    )


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Poll async job status."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(
        job_id=job_id,
        thread_id=job["thread_id"],
        status=job["status"],
        responses=[ModelResponse(**r) for r in job.get("responses", [])],
        event_ids=job.get("event_ids", []),
        provenance=build_provenance(),
        sentinel_context=build_sentinel_context(),
    )


# ---- History / Export ----

@router.get("/history", response_model=ThreadListResponse)
async def get_history(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """Get thread history with pagination."""
    user_id = get_user_id(current_user)
    total = await db.threads.count_documents({"user_id": user_id})
    threads = await db.threads.find(
        {"user_id": user_id}, {"_id": 0},
    ).sort("updated_at", -1).skip(offset).limit(limit).to_list(limit)

    summaries = []
    for t in threads:
        msg_count = await db.messages.count_documents({"thread_id": t["thread_id"], "user_id": user_id})
        models_used = await db.messages.distinct("model", {"thread_id": t["thread_id"], "user_id": user_id, "role": "assistant"})
        summaries.append(ThreadSummary(
            thread_id=t["thread_id"],
            title=t.get("title", "Untitled"),
            created_at=t.get("created_at", ""),
            updated_at=t.get("updated_at", ""),
            message_count=msg_count,
            models_used=models_used,
        ))

    return ThreadListResponse(threads=summaries, total=total, offset=offset, limit=limit)


@router.get("/thread/{thread_id}")
async def get_thread_messages(
    thread_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get all messages in a thread."""
    user_id = get_user_id(current_user)
    messages = await db.messages.find(
        {"thread_id": thread_id, "user_id": user_id}, {"_id": 0},
    ).sort("timestamp", 1).to_list(1000)
    return messages


@router.get("/export/{thread_id}")
async def export_thread(
    thread_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Full export: messages + events + snapshot."""
    user_id = get_user_id(current_user)
    messages = await db.messages.find(
        {"thread_id": thread_id, "user_id": user_id}, {"_id": 0},
    ).sort("timestamp", 1).to_list(1000)

    from services.events import get_events
    events = await get_events(thread_id, limit=2000)

    return {
        "thread_id": thread_id,
        "events": events,
        "messages": messages,
        "snapshot_id": f"snap_{uuid.uuid4().hex[:16]}",
        "provenance": build_provenance(),
        "sentinel_context": build_sentinel_context(),
    }


@router.post("/feedback")
async def submit_feedback(
    request: FeedbackRequest,
    current_user: dict = Depends(get_current_user),
):
    """Submit thumbs up/down feedback."""
    user_id = get_user_id(current_user)
    result = await db.messages.update_one(
        {"message_id": request.message_id, "user_id": user_id},
        {"$set": {"feedback": request.feedback}},
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Message not found")

    await emit_event("metric", "", f"user:{user_id}", {
        "type": "feedback", "message_id": request.message_id, "feedback": request.feedback,
    })
    return {"message": "Feedback submitted"}
# ratios: loc_comments=571:67 imports_exports=15:12 calls_definitions=248:20
