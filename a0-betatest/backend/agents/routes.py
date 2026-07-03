# ratios: loc_comments=229:75 imports_exports=14:16 calls_definitions=87:19
# === MODULE_BUILD ===
# id: agents_routes
#   module_name: routes
#   module_kind: route
#   summary: /api/instances/* CRUD + /api/chat/instance/{id} mode-aware; surface-3 teacher context preview endpoint
#   owner: Erin Spencer
#   public_surface: router, get_agent_store
#   internal_surface: _AGENT_STORE, _runtime, _get_key
#   auth_boundary: none
#   storage_boundary: write
#   network_boundary: external
#   user_data_boundary: write
#   admin_only: false
#   tests: a0p_skills.contracts.chat_instance_mode_dispatch_holds, a0p_skills.contracts.teacher_curated_context_distinct_from_prompt_holds
#   rollout: default_enabled
#   rollback: detach router; existing agents preserved
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: agents_routes_boundaries
#   summary: /api/instances/* CRUD + /api/chat/instance/{id} mode-aware; surface-3 teacher context preview endpoint
#   auth_boundary: none
#   storage_boundary: write
#   network_boundary: external
#   user_data_boundary: write
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: agents_routes
#   summary: /api/instances/* CRUD + /api/chat/instance/{id} mode-aware; surface-3 teacher context preview endpoint
#   exposes: router, get_agent_store
#   boundaries: auth:none, storage:write, network:external, user_data:write
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: chat_instance_mode_dispatch
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.chat_instance_mode_dispatch_holds
# === END CONTRACTS ===

# === CONTRACTS ===
# id: teacher_curated_context_distinct_from_prompt
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.teacher_curated_context_distinct_from_prompt_holds
# === END CONTRACTS ===
"""Agents CRUD + mode-aware chat-instance route."""
from __future__ import annotations
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict

from .schema import AgentInstance, CharacterSheet, AgentMode
from .store import AgentStore


router = APIRouter()

_AGENT_STORE: Optional[AgentStore] = None


def get_agent_store() -> AgentStore:
    if _AGENT_STORE is None:
        raise RuntimeError("agent store not initialised; call init_routes(mongo_collection)")
    return _AGENT_STORE


async def _resolve_user_id(request: Request, fallback: str = "local") -> str:
    """Derive the acting user id from the auth cookie; fall back when unauth."""
    uid, _ = await _resolve_user(request, fallback)
    return uid


async def _resolve_user(request: Request, fallback: str = "local") -> tuple[str, Optional[str]]:
    """Derive (user_id, username) from the auth cookie; (fallback, None) when unauth."""
    from auth import get_current_user
    try:
        user = await get_current_user(request)
        return user["id"], user.get("username")
    except Exception:
        return fallback, None


def init_routes(mongo_collection, runtime=None, get_key_fn=None):
    """Mount the routes — called from server.py at startup."""
    global _AGENT_STORE
    _AGENT_STORE = AgentStore(mongo_collection)
    if runtime is not None:
        router.runtime = runtime
    if get_key_fn is not None:
        router.get_key_fn = get_key_fn


# ---- request shapes -----------------------------------------------------

class CreateAgentRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    user_id: str = "local"
    sheet: CharacterSheet


class UpdateAgentRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    user_id: str = "local"
    # Either of these may be supplied; `sheet` is the preferred alias.
    patch: Optional[dict[str, Any]] = None
    sheet: Optional[dict[str, Any]] = None

    def merged_patch(self) -> dict[str, Any]:
        if self.sheet is not None and self.patch is not None:
            # Merge — `sheet` wins on key conflict.
            return {**self.patch, **self.sheet}
        return self.sheet or self.patch or {}


class ChatInstanceRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    user_id: str = "local"
    prompt: str
    mode: Optional[AgentMode] = None              # override character-sheet mode for this turn
    transcript: Optional[list[dict]] = None
    teacher_model_id: Optional[str] = None        # override character-sheet teacher
    user_feedback: Optional[Any] = None
    zfae_snapshot: Optional[dict] = None
    override_id: Optional[str] = None             # approved pending-override id (resumes a halted turn)


class TeacherPreviewRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    user_id: str = "local"
    prompt: str
    transcript: Optional[list[dict]] = None


class TrainRequest(BaseModel):
    """Training Room — distill the echo from two or more teacher models."""
    model_config = ConfigDict(protected_namespaces=())
    prompts: list[str]
    teacher_model_ids: list[str]


# ---- CRUD ---------------------------------------------------------------

@router.get("/instances")
async def list_instances(request: Request, user_id: str = "local", include_archived: bool = False):
    store = get_agent_store()
    uid = await _resolve_user_id(request, user_id)
    agents = await store.list(uid, include_archived=include_archived)
    return {"agents": [a.model_dump() for a in agents], "count": len(agents)}


@router.post("/instances")
async def create_instance(body: CreateAgentRequest, request: Request):
    store = get_agent_store()
    uid, uname = await _resolve_user(request, body.user_id)
    agent = await store.create(body.sheet, user_id=uid, username=uname)
    return agent.model_dump()


@router.get("/instances/{agent_id}")
async def get_instance(agent_id: str, request: Request, user_id: str = "local"):
    store = get_agent_store()
    uid = await _resolve_user_id(request, user_id)
    agent = await store.get(agent_id, uid)
    if not agent:
        raise HTTPException(404, f"agent {agent_id} not found")
    # Refresh metrics from on-disk checkpoint
    metrics = await store.refresh_metrics(agent_id, uid)
    if metrics:
        agent.zfae_metrics = metrics
    return agent.model_dump()


@router.patch("/instances/{agent_id}")
async def update_instance(agent_id: str, body: UpdateAgentRequest, request: Request):
    store = get_agent_store()
    patch = body.merged_patch()
    if not patch:
        raise HTTPException(400, "request body must include `sheet` or `patch`")
    uid = await _resolve_user_id(request, body.user_id)
    agent = await store.update_sheet(agent_id, patch, user_id=uid)
    if not agent:
        raise HTTPException(404, f"agent {agent_id} not found")
    return agent.model_dump()


@router.delete("/instances/{agent_id}")
async def delete_instance(agent_id: str, request: Request, user_id: str = "local", purge: bool = False):
    store = get_agent_store()
    uid = await _resolve_user_id(request, user_id)
    ok = await store.delete(agent_id, uid)
    if not ok:
        raise HTTPException(404, f"agent {agent_id} not found")
    if purge:
        await store.purge_filesystem(agent_id)
    return {"ok": True, "purged": purge}


@router.post("/instances/{agent_id}/archive")
async def archive_instance(agent_id: str, request: Request, user_id: str = "local"):
    store = get_agent_store()
    uid = await _resolve_user_id(request, user_id)
    ok = await store.archive(agent_id, uid)
    if not ok:
        raise HTTPException(404, f"agent {agent_id} not found or already archived")
    return {"ok": True, "archived": True}


# ---- mode-aware chat ----------------------------------------------------

@router.post("/chat/instance/{agent_id}")
async def chat_instance(agent_id: str, body: ChatInstanceRequest, request: Request):
    """Mode-aware chat — dispatches to ZFAERuntime in teacher_assisted or zfae_native mode.

    Requires authentication; the chat is always run as the calling user (the body's
    ``user_id`` field is ignored). Legacy ``user_id='local'`` agents were migrated
    on backend startup to the admin account, so the anonymous demo path is closed.
    """
    from auth import get_current_user
    user = await get_current_user(request)
    body.user_id = user["id"]

    store = get_agent_store()
    agent = await store.get(agent_id, body.user_id)
    if not agent:
        raise HTTPException(404, f"agent {agent_id} not found")

    runtime = getattr(router, "runtime", None)
    if runtime is None:
        raise HTTPException(500, "ZFAERuntime not initialised on the agents router")

    mode = body.mode or agent.sheet.mode
    teacher_model_id = body.teacher_model_id or agent.sheet.base_model

    bank = store.load_weight_bank(agent_id)
    if bank is None:
        from interdependent_lib.zfae.weights import A0ZFAEWeightBank
        bank = A0ZFAEWeightBank.fresh(agent_id)

    # Decide runtime mode
    from interdependent_lib.zfae.runtime import RuntimeMode
    if mode == AgentMode.ZFAE_NATIVE:
        rmode = RuntimeMode.ZFAE_NATIVE
    elif mode in (AgentMode.ZFAE_ASSISTED, AgentMode.MODEL_OBSERVED_BY_ZFAE,
                  AgentMode.MODEL_PLUS_CRITIC, AgentMode.MODEL_ONLY,
                  AgentMode.BARE_MODEL):
        rmode = RuntimeMode.TEACHER_ASSISTED
    else:
        rmode = RuntimeMode.ZFAE_NATIVE

    reply = await runtime.reply(
        mode=rmode,
        agent_id=agent_id,
        user_id=body.user_id,
        bank=bank,
        raw_prompt=body.prompt,
        transcript=body.transcript,
        teacher_model_id=teacher_model_id,
        system_prompt=agent.sheet.system_prompt,
        persona=agent.sheet.persona,
        user_feedback=body.user_feedback,
        zfae_snapshot=body.zfae_snapshot,
        sentinel_modes=getattr(agent.sheet, "sentinel_modes", None),
        sentinel_weights=getattr(agent.sheet, "sentinel_weights", None),
        override_id=body.override_id,
        tools_allowed=getattr(agent.sheet, "tools_allowed", None),
        lifted_path_trace=getattr(agent.sheet, "lifted_path_trace", False),
    )

    # Persist weight bank if updated
    if reply.zfae_weights_updated:
        store.save_weight_bank(agent_id, bank)
        await store.refresh_metrics(agent_id, body.user_id)

    response_body = {
        "agent_id": agent_id,
        "mode": mode.value,
        "assistantText": reply.assistantText,
        "reply_source": reply.reply_source,
        "teacher_called": reply.teacher_called,
        "zfae_weights_updated": reply.zfae_weights_updated,
        "nextSnapshot": reply.nextSnapshot,
        "trace": reply.trace,
        "training_record_path": reply.training_record_path,
        "zfae_metrics": reply.zfae_metrics,
        "sentinel_verdict": reply.sentinel_verdict,
        "pending_override_id": reply.pending_override_id,
    }
    if reply.reply_source == "zfae_halted":
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=202, content=response_body)
    return response_body


# ---- training room (multi-teacher distillation) ------------------------

@router.post("/instances/{agent_id}/train")
async def train_instance(agent_id: str, body: TrainRequest, request: Request):
    """Training Room — distill the agent's a0(zfae) echo from TWO OR MORE teacher models.

    Each prompt is answered by every selected teacher; the echo runs one distill
    step per answer (round-robin core/seed) so the weight bank accumulates across
    models. Requires authentication and the calling user's BYOK keys.
    """
    from auth import get_current_user
    user = await get_current_user(request)
    uid = user["id"]

    store = get_agent_store()
    agent = await store.get(agent_id, uid)
    if not agent:
        raise HTTPException(404, f"agent {agent_id} not found")

    prompts = [p for p in (body.prompts or []) if (p or "").strip()]
    if not prompts:
        raise HTTPException(400, "provide at least one prompt to train on")
    teachers = [t for t in (body.teacher_model_ids or []) if (t or "").strip()]
    if len(teachers) < 2:
        raise HTTPException(400, "the training room needs two or more teacher models")

    runtime = getattr(router, "runtime", None)
    if runtime is None:
        raise HTTPException(500, "ZFAERuntime not initialised on the agents router")

    from interdependent_lib.zfae.weights import A0ZFAEWeightBank
    bank = store.load_weight_bank(agent_id) or A0ZFAEWeightBank.fresh(agent_id)
    result = await runtime.train_multi(
        agent_id=agent_id, user_id=uid, bank=bank,
        prompts=prompts, teacher_model_ids=teachers,
        system_prompt=agent.sheet.system_prompt, persona=agent.sheet.persona,
    )
    if result.get("weights_updated"):
        store.save_weight_bank(agent_id, bank)
        await store.refresh_metrics(agent_id, uid)
    result["agent_id"] = agent_id
    return result


@router.post("/instances/{agent_id}/teacher-context-preview")
async def teacher_context_preview(agent_id: str, body: TeacherPreviewRequest, request: Request):
    """Surface-3 preview — return the curated context that would be sent to the teacher.

    Verifies that surface-3 is distinct from surface-1 (raw prompt).
    """
    store = get_agent_store()
    uid = await _resolve_user_id(request, body.user_id)
    agent = await store.get(agent_id, uid)
    if not agent:
        raise HTTPException(404, f"agent {agent_id} not found")

    from interdependent_lib.zfae.teacher import build_curated_context
    messages = build_curated_context(
        system_prompt=agent.sheet.system_prompt,
        persona=agent.sheet.persona,
        transcript=body.transcript,
        prompt=body.prompt,
    )
    return {
        "agent_id": agent_id,
        "surface_1_raw_prompt": body.prompt,
        "surface_3_teacher_context": messages,
        "context_distinct_from_prompt": len(messages) > 1 or (messages and messages[-1].get("content") != body.prompt or messages[0].get("role") != "user"),
    }
# ratios: loc_comments=229:75 imports_exports=14:16 calls_definitions=87:19
