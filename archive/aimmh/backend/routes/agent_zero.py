# ratios: loc_comments=442:16 imports_exports=13:16 calls_definitions=131:27
from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime, timezone
from typing import Literal
import os
import httpx
import logging

from db import db
from models.agent_zero import (
    A0IngestRequest,
    A0RouteRequest,
    A0NonUIPromptRequest,
    A0NonUISelectedPromptRequest,
    A0NonUISynthesisRequest,
)
from models.chat import ChatRequest
from models.edcm import A0Config
from services.auth import get_current_user, get_user_id
from routes.chat import chat_stream
from routes.export import export_conversation

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/a0", tags=["agent_zero"])

NON_UI_ALL_MODELS = [
    "gpt-5.2",
    "claude-sonnet-4-5-20250929",
    "gemini-3-flash-preview",
    "grok-3",
    "deepseek-chat",
    "sonar-pro",
]


async def get_a0_connection(user_id: str) -> dict:
    """Get A0 connection details for user, falling back to env defaults"""
    config = await db.a0_config.find_one({"user_id": user_id}, {"_id": 0})
    if config:
        if config.get("mode") == "cloud":
            return {"url": config.get("cloud_url", ""), "key": config.get("api_key", "")}
        else:
            host = config.get("local_url", "http://127.0.0.1")
            port = config.get("local_port", 8787)
            return {"url": f"{host}:{port}", "key": config.get("api_key", "")}
    return {
        "url": os.environ.get("A0_URL", "http://127.0.0.1:8787"),
        "key": os.environ.get("A0_API_KEY", "")
    }


def _validate_a0_connection(conn: dict) -> None:
    if not conn.get("url"):
        raise HTTPException(status_code=503, detail="Agent Zero not configured")


async def _load_ingest_conversation_and_messages(request: A0IngestRequest, uid: str):
    conversation = await db.conversations.find_one(
        {"id": request.conversation_id, "user_id": uid},
        {"_id": 0},
    )

    messages = None
    if conversation:
        cursor = db.messages.find(
            {"conversation_id": request.conversation_id, "user_id": uid},
            {"_id": 0},
        ).sort("timestamp", 1)
        try:
            messages = await cursor.to_list(length=None)
        except TypeError:
            messages = await cursor.to_list(length=2000)

    if not messages and request.messages:
        messages = request.messages

    if not messages:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return conversation, messages


def _resolve_ingest_constraints(request: A0IngestRequest, conversation: dict | None) -> dict:
    return {
        "global_context": request.global_context if request.global_context is not None else (conversation.get("global_context") if conversation else None),
        "model_roles": request.model_roles if request.model_roles is not None else (conversation.get("model_roles") if conversation else None),
        "context_mode": request.context_mode if request.context_mode is not None else (conversation.get("context_mode") if conversation else None),
        "shared_room_mode": request.shared_room_mode if request.shared_room_mode is not None else (conversation.get("shared_room_mode") if conversation else None),
        "shared_pairs": request.shared_pairs if request.shared_pairs is not None else (conversation.get("shared_pairs") if conversation else None),
    }


def _resolve_ingest_metadata(request: A0IngestRequest, conversation: dict | None) -> dict:
    metadata = request.metadata or {}
    if conversation:
        metadata = {
            **metadata,
            "conversation_meta": {
                "title": conversation.get("title"),
                "created_at": conversation.get("created_at"),
                "updated_at": conversation.get("updated_at"),
            },
        }
    return metadata


def _build_ingest_payload(request: A0IngestRequest, uid: str, conversation: dict | None, messages: list, constraints: dict, metadata: dict) -> dict:
    title = request.title or (conversation.get("title") if conversation else "Conversation")
    return {
        "source": "multi-ai-hub",
        "conversation_id": request.conversation_id,
        "title": title,
        "user_id": uid,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "messages": messages,
        "constraints": constraints,
        "metadata": metadata,
    }


async def _post_to_a0(conn: dict, path: str, payload: dict, timeout: float = 10.0) -> dict:
    headers = {"Content-Type": "application/json"}
    if conn.get("key"):
        headers["X-A0-Key"] = conn["key"]

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            f"{conn['url']}{path}",
            json=payload,
            headers=headers,
        )
        response.raise_for_status()
    return response.json()


def _normalize_selected_message_ids(selected_message_ids: list[str]) -> list[str]:
    selected_ids = [mid for mid in selected_message_ids if isinstance(mid, str) and mid]
    if not selected_ids:
        raise HTTPException(status_code=400, detail="selected_message_ids must include at least one ID")
    return selected_ids


def _normalize_target_models(target_models: list[str]) -> list[str]:
    models = [model.strip() for model in target_models if isinstance(model, str) and model.strip()]
    if not models:
        raise HTTPException(status_code=400, detail="target_models must include at least one model")
    return list(dict.fromkeys(models))


async def _fetch_synthesis_source_messages(
    conversation_id: str,
    uid: str,
    selected_ids: list[str],
    source_model: str | None,
) -> list[dict]:
    selected_messages = await db.messages.find(
        {
            "conversation_id": conversation_id,
            "user_id": uid,
            "role": "assistant",
            "id": {"$in": selected_ids},
        },
        {"_id": 0},
    ).to_list(5000)

    if source_model:
        selected_messages = [msg for msg in selected_messages if msg.get("model") == source_model]

    if not selected_messages:
        raise HTTPException(status_code=404, detail="No matching assistant responses found for synthesis")

    selected_messages.sort(key=lambda msg: msg.get("timestamp", ""))
    return selected_messages


def _build_synthesis_prompt_message(synthesis_prompt: str | None, selected_messages: list[dict]) -> str:
    prompt = synthesis_prompt or "Synthesize and analyze these AI responses:"
    responses_text = [
        f"Response #{idx} from {msg.get('model', 'unknown')}:\n{msg.get('content', '')}"
        for idx, msg in enumerate(selected_messages, start=1)
    ]
    return f"{prompt}\n\n" + "\n\n".join(responses_text)


@router.get("/config")
async def get_a0_config(current_user: dict = Depends(get_current_user)):
    """Get user's A0 connection config"""
    uid = get_user_id(current_user)
    config = await db.a0_config.find_one({"user_id": uid}, {"_id": 0})
    if not config:
        return {
            "mode": "local",
            "local_name": "local-device",
            "local_url": "http://192.168.1.1",
            "local_port": 8787,
            "cloud_url": "",
            "api_key": "",
            "route_via_a0": False,
            "auto_ingest": False
        }
    config.pop("user_id", None)
    return config


@router.put("/config")
async def update_a0_config(
    config: A0Config,
    current_user: dict = Depends(get_current_user)
):
    """Save user's A0 connection config"""
    uid = get_user_id(current_user)
    doc = config.model_dump()
    doc["user_id"] = uid
    doc["updated_at"] = datetime.now(timezone.utc).isoformat()

    await db.a0_config.update_one(
        {"user_id": uid},
        {"$set": doc},
        upsert=True
    )
    return {"message": "A0 config saved"}


@router.post("/ingest")
async def ingest_to_agent_zero(
    request: A0IngestRequest,
    current_user: dict = Depends(get_current_user)
):
    """Send conversation to Agent Zero for EDCM analysis"""
    uid = get_user_id(current_user)
    conn = await get_a0_connection(uid)
    _validate_a0_connection(conn)

    try:
        conversation, messages = await _load_ingest_conversation_and_messages(request, uid)
        constraints = _resolve_ingest_constraints(request, conversation)
        metadata = _resolve_ingest_metadata(request, conversation)
        edcm_payload = _build_ingest_payload(request, uid, conversation, messages, constraints, metadata)
        a0_response = await _post_to_a0(conn, "/ingest/transcript", edcm_payload)
        return {"message": "Ingested to Agent Zero", "a0_response": a0_response}

    except httpx.HTTPError as e:
        logger.error(f"Agent Zero ingestion failed: {e}")
        raise HTTPException(status_code=503, detail=f"Agent Zero unreachable: {str(e)}")


@router.post("/route")
async def route_via_agent_zero(
    request: A0RouteRequest,
    current_user: dict = Depends(get_current_user)
):
    """Route request through Agent Zero for TIW policy + logging"""
    uid = get_user_id(current_user)
    conn = await get_a0_connection(uid)
    _validate_a0_connection(conn)

    try:
        payload = {
            "message": request.message,
            "models": request.models,
            "user_id": uid,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        return await _post_to_a0(conn, "/route", payload)

    except httpx.HTTPError as e:
        logger.error(f"Agent Zero routing failed: {e}")
        raise HTTPException(status_code=503, detail=f"Agent Zero unreachable: {str(e)}")


@router.get("/health")
async def check_agent_zero_health(current_user: dict = Depends(get_current_user)):
    """Check if Agent Zero is reachable using user's config"""
    uid = get_user_id(current_user)
    conn = await get_a0_connection(uid)

    if not conn["url"]:
        return {"status": "not_configured"}

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(f"{conn['url']}/health")
            return {
                "status": "connected" if response.status_code == 200 else "error",
                "a0_url": conn["url"],
                "response": response.json() if response.status_code == 200 else None
            }
    except Exception as e:
        return {
            "status": "unreachable",
            "a0_url": conn["url"],
            "error": str(e)
        }


@router.get("/non-ui/options")
async def get_non_ui_options(current_user: dict = Depends(get_current_user)):
    """Expose all prompt/response options for Agent Zero non-UI orchestration."""
    return {
        "input_options": {
            "context_mode": ["compartmented", "shared"],
            "shared_room_modes": ["parallel_all", "parallel_paired"],
            "supports_global_context": True,
            "supports_model_roles": True,
            "supports_per_model_messages": True,
            "supports_attachments": True,
            "supports_shared_pairs": True,
            "supports_persist_user_message_toggle": True,
            "supports_history_limit": True,
            "attachment_target_modes": ["all", "selected"]
        },
        "output_options": {
            "streaming": "SSE",
            "conversation_transcript": True,
            "response_time_ms": True,
            "edcm_dashboard": True,
            "export_formats": ["json", "txt", "pdf"]
        },
        "available_models": {
            "gpt": ["gpt-5.2", "gpt-5.1", "gpt-4o", "o3", "o3-pro", "o4-mini"],
            "claude": ["claude-sonnet-4-5-20250929", "claude-opus-4-5-20251101", "claude-haiku-4-5-20251001", "claude-4-sonnet-20250514"],
            "gemini": ["gemini-3-flash-preview", "gemini-3-pro-preview", "gemini-2.5-pro", "gemini-2.5-flash"],
            "grok": ["grok-3", "grok-4", "grok-2-latest"],
            "deepseek": ["deepseek-chat", "deepseek-reasoner"],
            "perplexity": ["sonar-pro", "sonar-deep-research"]
        },
        "non_ui_endpoints": {
            "chat_stream": "/api/a0/non-ui/chat/stream",
            "prompt_all": "/api/a0/non-ui/prompt/all",
            "prompt_selected": "/api/a0/non-ui/prompt/selected",
            "synthesis": "/api/a0/non-ui/synthesis",
            "options": "/api/a0/non-ui/options",
            "transcript": "/api/a0/non-ui/transcript/{conversation_id}",
            "history": "/api/a0/non-ui/history/{conversation_id}",
            "conversations": "/api/a0/non-ui/conversations",
            "conversations_search": "/api/a0/non-ui/conversations/search?q=term&offset=0&limit=20",
            "export": "/api/a0/non-ui/conversations/{conversation_id}/export?format=json|txt|pdf"
        }
    }


@router.post("/non-ui/chat/stream")
async def a0_non_ui_chat_stream(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """Non-UI alias for full chat streaming, accessible by Agent Zero."""
    return await chat_stream(request=request, current_user=current_user)


def _build_chat_request(
    base_request: A0NonUIPromptRequest,
    models: list[str],
) -> ChatRequest:
    return ChatRequest(
        message=base_request.message,
        models=models,
        conversation_id=base_request.conversation_id,
        context_mode=base_request.context_mode,
        shared_room_mode=base_request.shared_room_mode,
        shared_pairs=base_request.shared_pairs,
        global_context=base_request.global_context,
        model_roles=base_request.model_roles,
        per_model_messages=base_request.per_model_messages,
        persist_user_message=base_request.persist_user_message,
        history_limit=base_request.history_limit,
        attachments=base_request.attachments,
    )


@router.post("/non-ui/prompt/all")
async def a0_non_ui_prompt_all(
    request: A0NonUIPromptRequest,
    current_user: dict = Depends(get_current_user)
):
    """Dispatch one prompt to all supported model families for non-UI orchestration."""
    chat_request = _build_chat_request(request, NON_UI_ALL_MODELS)
    return await chat_stream(request=chat_request, current_user=current_user)


@router.post("/non-ui/prompt/selected")
async def a0_non_ui_prompt_selected(
    request: A0NonUISelectedPromptRequest,
    current_user: dict = Depends(get_current_user)
):
    """Dispatch one prompt to selected models only for non-UI orchestration."""
    selected_models = [model.strip() for model in request.models if isinstance(model, str) and model.strip()]
    if not selected_models:
        raise HTTPException(status_code=400, detail="At least one target model is required")

    deduped_models = list(dict.fromkeys(selected_models))
    chat_request = _build_chat_request(request, deduped_models)
    return await chat_stream(request=chat_request, current_user=current_user)


@router.post("/non-ui/synthesis")
async def a0_non_ui_synthesis(
    request: A0NonUISynthesisRequest,
    current_user: dict = Depends(get_current_user)
):
    """One-off synthesis endpoint for Agent Zero: selected assistant responses => target models."""
    uid = get_user_id(current_user)
    selected_ids = _normalize_selected_message_ids(request.selected_message_ids)
    target_models = _normalize_target_models(request.target_models)
    selected_messages = await _fetch_synthesis_source_messages(
        conversation_id=request.conversation_id,
        uid=uid,
        selected_ids=selected_ids,
        source_model=request.source_model,
    )
    synthesis_message = _build_synthesis_prompt_message(request.synthesis_prompt, selected_messages)

    chat_request = ChatRequest(
        message=synthesis_message,
        models=target_models,
        conversation_id=request.conversation_id,
        context_mode=request.context_mode,
        shared_room_mode=request.shared_room_mode,
        shared_pairs=request.shared_pairs,
        global_context=request.global_context,
        model_roles=request.model_roles,
        persist_user_message=True,
        history_limit=request.history_limit,
    )
    return await chat_stream(request=chat_request, current_user=current_user)


@router.get("/non-ui/conversations")
async def get_non_ui_conversations(
    limit: int = Query(default=100, ge=1, le=500),
    current_user: dict = Depends(get_current_user)
):
    """List user conversations for Agent Zero programmatic access."""
    uid = get_user_id(current_user)
    conversations = await db.conversations.find(
        {"user_id": uid},
        {"_id": 0}
    ).sort("updated_at", -1).limit(limit).to_list(limit)

    return {"conversations": conversations}


@router.get("/non-ui/conversations/search")
async def search_non_ui_conversations(
    q: str = Query(default="", max_length=120),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Search conversation titles for Agent Zero programmatic retrieval."""
    uid = get_user_id(current_user)
    title_query = (q or "").strip()

    base_filter = {"user_id": uid}
    if title_query:
        base_filter["title"] = {"$regex": title_query, "$options": "i"}

    total = await db.conversations.count_documents(base_filter)
    conversations = await db.conversations.find(
        base_filter,
        {"_id": 0}
    ).sort("updated_at", -1).skip(offset).limit(limit).to_list(limit)

    return {
        "query": title_query,
        "offset": offset,
        "limit": limit,
        "total": total,
        "conversations": conversations,
    }


@router.get("/non-ui/history/{conversation_id}")
async def get_non_ui_history(
    conversation_id: str,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=200, ge=1, le=1000),
    current_user: dict = Depends(get_current_user)
):
    """Return paginated message history for one conversation."""
    uid = get_user_id(current_user)

    conversation = await db.conversations.find_one(
        {"id": conversation_id, "user_id": uid},
        {"_id": 0, "id": 1, "title": 1, "created_at": 1, "updated_at": 1},
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    total_messages = await db.messages.count_documents({"conversation_id": conversation_id, "user_id": uid})
    messages = await db.messages.find(
        {"conversation_id": conversation_id, "user_id": uid},
        {"_id": 0},
    ).sort("timestamp", 1).skip(offset).limit(limit).to_list(limit)

    return {
        "conversation": conversation,
        "offset": offset,
        "limit": limit,
        "total_messages": total_messages,
        "messages": messages,
    }


@router.get("/non-ui/transcript/{conversation_id}")
async def get_non_ui_transcript(
    conversation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Return full transcript and metadata for Agent Zero non-UI ingestion."""
    uid = get_user_id(current_user)

    conversation = await db.conversations.find_one(
        {"id": conversation_id, "user_id": uid},
        {"_id": 0}
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = await db.messages.find(
        {"conversation_id": conversation_id, "user_id": uid},
        {"_id": 0}
    ).sort("timestamp", 1).to_list(5000)

    return {
        "conversation": conversation,
        "messages": messages,
        "message_count": len(messages)
    }


@router.get("/non-ui/conversations/{conversation_id}/export")
async def get_non_ui_export(
    conversation_id: str,
    format: Literal["json", "txt", "pdf"] = "json",
    current_user: dict = Depends(get_current_user)
):
    """Non-UI export endpoint proxying core conversation export formats."""
    return await export_conversation(
        conversation_id=conversation_id,
        format=format,
        current_user=current_user,
    )
# ratios: loc_comments=442:16 imports_exports=13:16 calls_definitions=131:27
