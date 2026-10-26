# ratios: loc_comments=674:7 imports_exports=14:7 calls_definitions=151:24
from fastapi import APIRouter, HTTPException, Depends, Query
from sse_starlette.sse import EventSourceResponse
from datetime import datetime, timezone
from typing import List, Dict, Any
import json
import uuid
import time
import logging
import math

from db import db
from models.chat import ChatRequest, MessageFeedback, ConversationResponse, CatchupRequest
from services.auth import get_current_user, get_user_id
from services.llm import get_api_key_for_developer, stream_emergent, stream_openai_compatible
from services.secrets import SecretDecryptionError
from services.audit import append_audit_event

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["chat"])

MODEL_RATE_PER_1K_TOKENS = {
    "gpt": 0.012,
    "claude": 0.011,
    "gemini": 0.007,
    "grok": 0.014,
    "deepseek": 0.004,
    "perplexity": 0.010,
    "default": 0.010,
}


def _estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, math.ceil(len(text) / 4))


def _model_rate(model_spec: str) -> float:
    lower = (model_spec or "").lower()
    if "gpt" in lower or lower.startswith("o"):
        return MODEL_RATE_PER_1K_TOKENS["gpt"]
    if "claude" in lower:
        return MODEL_RATE_PER_1K_TOKENS["claude"]
    if "gemini" in lower:
        return MODEL_RATE_PER_1K_TOKENS["gemini"]
    if "grok" in lower:
        return MODEL_RATE_PER_1K_TOKENS["grok"]
    if "deepseek" in lower:
        return MODEL_RATE_PER_1K_TOKENS["deepseek"]
    if "perplexity" in lower or "sonar" in lower:
        return MODEL_RATE_PER_1K_TOKENS["perplexity"]
    return MODEL_RATE_PER_1K_TOKENS["default"]


def _normalize_attachments(attachments: List[Dict[str, Any]] | None) -> List[Dict[str, Any]]:
    normalized = []
    for item in attachments or []:
        if not isinstance(item, dict):
            continue

        target_mode = item.get("target_mode", "all")
        if target_mode not in {"all", "selected"}:
            target_mode = "all"

        target_models = item.get("target_models") or []
        if not isinstance(target_models, list):
            target_models = []

        normalized.append({
            "id": item.get("id") or str(uuid.uuid4()),
            "name": item.get("name") or "attachment",
            "mime_type": item.get("mime_type") or "application/octet-stream",
            "kind": item.get("kind") or "file",
            "size": item.get("size") or 0,
            "content": (item.get("content") or "")[:12000],
            "target_mode": target_mode,
            "target_models": [m for m in target_models if isinstance(m, str)],
        })

    return normalized


def _attachment_matches_model(attachment: Dict[str, Any], model: str) -> bool:
    if attachment.get("target_mode") == "all":
        return True
    return model in (attachment.get("target_models") or [])


def _build_attachment_context(attachments: List[Dict[str, Any]], model: str) -> str:
    chunks = []
    for att in attachments:
        if not _attachment_matches_model(att, model):
            continue

        name = att.get("name", "attachment")
        kind = att.get("kind", "file")
        mime_type = att.get("mime_type", "application/octet-stream")
        size = att.get("size", 0)
        content = (att.get("content") or "").strip()
        snippet = content[:3000]

        if snippet:
            chunks.append(
                f"- {name} ({kind}, {mime_type}, {size} bytes)\n"
                f"  Content excerpt:\n{snippet}"
            )
        else:
            chunks.append(f"- {name} ({kind}, {mime_type}, {size} bytes)")

    return "\n\n".join(chunks)


def _normalize_shared_pairs(shared_pairs: Dict[str, List[str]] | None, models: List[str]) -> Dict[str, List[str]]:
    normalized: Dict[str, List[str]] = {model: [] for model in models}
    if not isinstance(shared_pairs, dict):
        return normalized

    valid_models = set(models)
    for model, peers in shared_pairs.items():
        if model not in valid_models or not isinstance(peers, list):
            continue
        normalized[model] = [peer for peer in peers if isinstance(peer, str) and peer in valid_models and peer != model]
    return normalized


def _validate_chat_request(request: ChatRequest) -> None:
    if not (request.message or "").strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    if not request.models:
        raise HTTPException(status_code=400, detail="At least one model is required")


async def _ensure_conversation_record(
    conversation_id: str,
    user_id: str,
    request: ChatRequest,
) -> None:
    now_iso = datetime.now(timezone.utc).isoformat()
    await db.conversations.update_one(
        {"id": conversation_id, "user_id": user_id},
        {
            "$set": {
                "title": request.message[:50],
                "updated_at": now_iso,
                "context_mode": request.context_mode,
                "shared_room_mode": request.shared_room_mode,
            },
            "$setOnInsert": {
                "id": conversation_id,
                "user_id": user_id,
                "created_at": now_iso,
            },
        },
        upsert=True,
    )


async def _create_context_log(
    conversation_id: str,
    user_id: str,
    request: ChatRequest,
    shared_pairs: Dict[str, List[str]],
    normalized_attachments: List[Dict[str, Any]],
) -> None:
    context_log = {
        "id": str(uuid.uuid4()),
        "conversation_id": conversation_id,
        "user_id": user_id,
        "message": request.message,
        "models": request.models,
        "context_mode": request.context_mode,
        "shared_room_mode": request.shared_room_mode,
        "shared_pairs": shared_pairs,
        "global_context": request.global_context,
        "model_roles": request.model_roles,
        "per_model_messages": request.per_model_messages,
        "attachments": normalized_attachments,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.context_logs.insert_one(context_log)
    await append_audit_event(
        collection="chat_event_logs",
        event_type="chat_prompt_received",
        actor_user_id=user_id,
        payload={
            "conversation_id": conversation_id,
            "models": request.models,
            "context_mode": request.context_mode,
            "shared_room_mode": request.shared_room_mode,
            "attachments_count": len(normalized_attachments),
            "persist_user_message": request.persist_user_message,
        },
    )


async def _persist_base_user_message(
    request: ChatRequest,
    conversation_id: str,
    user_id: str,
    normalized_attachments: List[Dict[str, Any]],
) -> None:
    if not request.persist_user_message:
        return
    user_msg = {
        "id": str(uuid.uuid4()),
        "conversation_id": conversation_id,
        "role": "user",
        "content": request.message,
        "model": "user",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
    }
    if normalized_attachments:
        user_msg["attachments"] = normalized_attachments
    await db.messages.insert_one(user_msg)


async def _load_history(conversation_id: str, user_id: str, history_limit: int) -> List[Dict[str, Any]]:
    if history_limit <= 0:
        return []
    cursor = db.messages.find(
        {"conversation_id": conversation_id, "user_id": user_id},
        {"_id": 0},
    ).sort("timestamp", 1).limit(history_limit)
    return await cursor.to_list(history_limit)


def _build_messages_context(
    request: ChatRequest,
    model_spec: str,
    history: List[Dict[str, Any]],
    per_model_prompt: str,
    shared_pairs: Dict[str, List[str]],
) -> List[Dict[str, str]]:
    messages_context: List[Dict[str, str]] = []
    for msg in history[-30:]:
        if msg["role"] == "assistant":
            if request.context_mode == "compartmented" and msg.get("model") != model_spec:
                continue
            if request.context_mode == "shared":
                if request.shared_room_mode == "parallel_paired":
                    allowed_models = set(shared_pairs.get(model_spec, []))
                    allowed_models.add(model_spec)
                    if msg.get("model") not in allowed_models:
                        continue
                messages_context.append({
                    "role": "assistant",
                    "content": f"[{msg.get('model', 'unknown')}] {msg.get('content', '')}",
                })
            else:
                messages_context.append({"role": "assistant", "content": msg.get("content", "")})
        elif msg["role"] == "user":
            messages_context.append({"role": "user", "content": msg.get("content", "")})

    if request.persist_user_message:
        if messages_context and messages_context[-1]["role"] == "user":
            messages_context[-1] = {"role": "user", "content": per_model_prompt}
        else:
            messages_context.append({"role": "user", "content": per_model_prompt})
    else:
        messages_context.append({"role": "user", "content": per_model_prompt})
    return messages_context


def _resolve_stream_iterator(current_user: dict, model_spec: str, messages_context: List[Dict[str, str]], conversation_id: str):
    model_lower = model_spec.lower()
    try:
        if "gpt" in model_lower or model_lower.startswith("o"):
            api_key = get_api_key_for_developer(current_user, "gpt")
            if not api_key:
                return None, "No API key configured"
            return stream_emergent(api_key, model_spec, "openai", messages_context, conversation_id), None
        if "claude" in model_lower:
            api_key = get_api_key_for_developer(current_user, "claude")
            if not api_key:
                return None, "No API key configured"
            return stream_emergent(api_key, model_spec, "anthropic", messages_context, conversation_id), None
        if "gemini" in model_lower:
            api_key = get_api_key_for_developer(current_user, "gemini")
            if not api_key:
                return None, "No API key configured"
            return stream_emergent(api_key, model_spec, "gemini", messages_context, conversation_id), None
        if "grok" in model_lower:
            api_key = get_api_key_for_developer(current_user, "grok")
            if not api_key:
                return None, "No API key configured"
            return stream_openai_compatible("https://api.x.ai/v1", api_key, model_spec, messages_context), None
        if "deepseek" in model_lower:
            api_key = get_api_key_for_developer(current_user, "deepseek")
            if not api_key:
                return None, "No API key configured"
            return stream_openai_compatible("https://api.deepseek.com", api_key, model_spec, messages_context), None
        if "perplexity" in model_lower or "sonar" in model_lower:
            api_key = get_api_key_for_developer(current_user, "perplexity")
            if not api_key:
                return None, "No API key configured"
            return stream_openai_compatible("https://api.perplexity.ai", api_key, model_spec, messages_context), None
    except SecretDecryptionError:
        # Return the structured (None, message) shape the caller already cleans
        # up, instead of raising past the placeholder-message setup.
        return None, "Stored API key could not be decrypted; re-enter it or fix API_KEY_ENCRYPTION_KEY"
    return None, f"Unsupported model '{model_spec}'"


async def _insert_streaming_message(message_id: str, conversation_id: str, user_id: str, model_spec: str) -> None:
    await db.messages.insert_one({
        "id": message_id,
        "conversation_id": conversation_id,
        "role": "assistant",
        "content": "",
        "model": model_spec,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "feedback": None,
        "response_time_ms": None,
        "streaming": True,
    })


async def _handle_chat_error(
    *,
    user_id: str,
    conversation_id: str,
    message_id: str,
    model_spec: str,
    error_text: str,
    t_start: float,
    prompt_tokens_est: int,
) -> Dict[str, Any]:
    response_time_ms = int((time.time() - t_start) * 1000)
    completion_tokens_est = _estimate_tokens(error_text)
    total_tokens_est = prompt_tokens_est + completion_tokens_est
    estimated_cost_usd = round((total_tokens_est / 1000.0) * _model_rate(model_spec), 6)
    await db.messages.update_one(
        {"id": message_id, "user_id": user_id},
        {
            "$set": {
                "conversation_id": conversation_id,
                "role": "assistant",
                "content": error_text,
                "model": model_spec,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "feedback": None,
                "response_time_ms": response_time_ms,
                "streaming": False,
                "prompt_tokens_est": prompt_tokens_est,
                "completion_tokens_est": completion_tokens_est,
                "total_tokens_est": total_tokens_est,
                "estimated_cost_usd": estimated_cost_usd,
            },
            "$setOnInsert": {
                "id": message_id,
                "user_id": user_id,
            },
        },
        upsert=True,
    )
    await append_audit_event(
        collection="chat_event_logs",
        event_type="assistant_stream_error",
        actor_user_id=user_id,
        payload={
            "conversation_id": conversation_id,
            "message_id": message_id,
            "model": model_spec,
            "error": error_text,
            "response_time_ms": response_time_ms,
        },
    )
    return {
        "response_time_ms": response_time_ms,
        "prompt_tokens_est": prompt_tokens_est,
        "completion_tokens_est": completion_tokens_est,
        "total_tokens_est": total_tokens_est,
        "estimated_cost_usd": estimated_cost_usd,
    }


async def _stream_chat_response(
    *,
    current_user: dict,
    request: ChatRequest,
    conversation_id: str,
    user_id: str,
    model_spec: str,
    history: List[Dict[str, Any]],
    normalized_attachments: List[Dict[str, Any]],
    shared_pairs: Dict[str, List[str]],
):
    message_id = str(uuid.uuid4())
    t_start = time.time()

    per_model_prompt = (request.per_model_messages or {}).get(model_spec) or request.message
    attachment_context = _build_attachment_context(normalized_attachments, model_spec)
    if attachment_context:
        per_model_prompt = f"{per_model_prompt}\n\n[ATTACHMENTS]\n{attachment_context}"

    messages_context = _build_messages_context(
        request=request,
        model_spec=model_spec,
        history=history,
        per_model_prompt=per_model_prompt,
        shared_pairs=shared_pairs,
    )

    prompt_tokens_est = _estimate_tokens(per_model_prompt)
    full_response = ""

    await _insert_streaming_message(message_id, conversation_id, user_id, model_spec)
    await append_audit_event(
        collection="chat_event_logs",
        event_type="assistant_stream_started",
        actor_user_id=user_id,
        payload={
            "conversation_id": conversation_id,
            "message_id": message_id,
            "model": model_spec,
        },
    )

    stream_iter, setup_error = _resolve_stream_iterator(current_user, model_spec, messages_context, conversation_id)
    if setup_error:
        full_response = f"[ERROR] {setup_error}"
        metrics = await _handle_chat_error(
            user_id=user_id,
            conversation_id=conversation_id,
            message_id=message_id,
            model_spec=model_spec,
            error_text=full_response,
            t_start=t_start,
            prompt_tokens_est=prompt_tokens_est,
        )
        yield {"type": "chunk", "chunk": full_response, "message_id": message_id}
        yield {
            "type": "done",
            "message_id": message_id,
            "response_time_ms": metrics["response_time_ms"],
            "prompt_tokens_est": metrics["prompt_tokens_est"],
            "completion_tokens_est": metrics["completion_tokens_est"],
            "total_tokens_est": metrics["total_tokens_est"],
            "estimated_cost_usd": metrics["estimated_cost_usd"],
        }
        return

    async for chunk in stream_iter:
        if not chunk:
            continue
        full_response += chunk
        await db.messages.update_one(
            {"id": message_id, "user_id": user_id},
            {"$set": {"content": full_response, "streaming": True}},
        )
        yield {"type": "chunk", "chunk": chunk, "message_id": message_id}

    response_time_ms = int((time.time() - t_start) * 1000)
    completion_tokens_est = _estimate_tokens(full_response)
    total_tokens_est = prompt_tokens_est + completion_tokens_est
    estimated_cost_usd = round((total_tokens_est / 1000.0) * _model_rate(model_spec), 6)
    await db.messages.update_one(
        {"id": message_id, "user_id": user_id},
        {
            "$set": {
                "content": full_response,
                "response_time_ms": response_time_ms,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "streaming": False,
                "prompt_tokens_est": prompt_tokens_est,
                "completion_tokens_est": completion_tokens_est,
                "total_tokens_est": total_tokens_est,
                "estimated_cost_usd": estimated_cost_usd,
            }
        },
    )
    await append_audit_event(
        collection="chat_event_logs",
        event_type="assistant_stream_completed",
        actor_user_id=user_id,
        payload={
            "conversation_id": conversation_id,
            "message_id": message_id,
            "model": model_spec,
            "response_time_ms": response_time_ms,
            "total_tokens_est": total_tokens_est,
            "estimated_cost_usd": estimated_cost_usd,
        },
    )

    yield {
        "type": "done",
        "message_id": message_id,
        "response_time_ms": response_time_ms,
        "prompt_tokens_est": prompt_tokens_est,
        "completion_tokens_est": completion_tokens_est,
        "total_tokens_est": total_tokens_est,
        "estimated_cost_usd": estimated_cost_usd,
    }


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """Stream responses from multiple AI models"""
    _validate_chat_request(request)

    async def event_generator():
        conversation_id = request.conversation_id or str(uuid.uuid4())
        user_id = get_user_id(current_user)
        normalized_attachments = _normalize_attachments(request.attachments)
        shared_pairs = _normalize_shared_pairs(request.shared_pairs, request.models)

        await _ensure_conversation_record(conversation_id, user_id, request)
        await _create_context_log(
            conversation_id=conversation_id,
            user_id=user_id,
            request=request,
            shared_pairs=shared_pairs,
            normalized_attachments=normalized_attachments,
        )
        await _persist_base_user_message(
            request=request,
            conversation_id=conversation_id,
            user_id=user_id,
            normalized_attachments=normalized_attachments,
        )

        history_limit = request.history_limit if request.history_limit is not None else 30
        history = await _load_history(conversation_id, user_id, history_limit)

        for model_spec in request.models:
            try:
                message_id = str(uuid.uuid4())

                yield {
                    "event": "start",
                    "data": json.dumps({"model": model_spec, "message_id": message_id})
                }
                stream_result = _stream_chat_response(
                    current_user=current_user,
                    request=request,
                    conversation_id=conversation_id,
                    user_id=user_id,
                    model_spec=model_spec,
                    history=history,
                    normalized_attachments=normalized_attachments,
                    shared_pairs=shared_pairs,
                )
                async for part in stream_result:
                    if part["type"] == "chunk":
                        yield {
                            "event": "chunk",
                            "data": json.dumps({
                                "model": model_spec,
                                "message_id": part["message_id"],
                                "content": part["chunk"],
                            }),
                        }
                    elif part["type"] == "done":
                        message_id = part["message_id"]
                        yield {
                            "event": "complete",
                            "data": json.dumps({
                                "model": model_spec,
                                "message_id": message_id,
                                "response_time_ms": part["response_time_ms"],
                            }),
                        }
            except Exception as e:
                logger.error(f"Error streaming from {model_spec}: {str(e)}")
                err_message_id = str(uuid.uuid4())
                err_text = f"[ERROR] {str(e)}"
                metrics = await _handle_chat_error(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    message_id=err_message_id,
                    model_spec=model_spec,
                    error_text=err_text,
                    t_start=time.time(),
                    prompt_tokens_est=0,
                )
                yield {
                    "event": "chunk",
                    "data": json.dumps({"model": model_spec, "message_id": err_message_id, "content": err_text}),
                }
                yield {
                    "event": "complete",
                    "data": json.dumps({
                        "model": model_spec,
                        "message_id": err_message_id,
                        "response_time_ms": metrics["response_time_ms"],
                    }),
                }

        update_fields = {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "title": request.message[:50],
            "context_mode": request.context_mode,
            "shared_room_mode": request.shared_room_mode
        }
        if request.shared_pairs is not None:
            update_fields["shared_pairs"] = shared_pairs
        if request.global_context is not None:
            update_fields["global_context"] = request.global_context
        if request.model_roles is not None:
            update_fields["model_roles"] = request.model_roles

        await db.conversations.update_one(
            {"id": conversation_id, "user_id": user_id},
            {
                "$set": update_fields,
                "$setOnInsert": {
                    "id": conversation_id,
                    "user_id": user_id,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            },
            upsert=True
        )

    return EventSourceResponse(event_generator())


@router.post("/chat/feedback")
async def submit_feedback(
    feedback: MessageFeedback,
    current_user: dict = Depends(get_current_user)
):
    """Submit thumbs up/down feedback for a message"""
    result = await db.messages.update_one(
        {"id": feedback.message_id, "user_id": get_user_id(current_user)},
        {"$set": {"feedback": feedback.feedback}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Message not found")
    await append_audit_event(
        collection="chat_event_logs",
        event_type="message_feedback_submitted",
        actor_user_id=get_user_id(current_user),
        payload={"message_id": feedback.message_id, "feedback": feedback.feedback},
    )
    return {"message": "Feedback submitted"}


@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(current_user: dict = Depends(get_current_user)):
    """Get user's conversation history"""
    conversations = await db.conversations.find(
        {"user_id": get_user_id(current_user)},
        {"_id": 0}
    ).sort("updated_at", -1).limit(50).to_list(50)

    return [
        ConversationResponse(
            id=conv["id"],
            user_id=conv["user_id"],
            title=conv.get("title", "New Conversation"),
            created_at=datetime.fromisoformat(conv["created_at"]),
            updated_at=datetime.fromisoformat(conv["updated_at"])
        )
        for conv in conversations
    ]


@router.get("/conversations/search")
async def search_conversations(
    q: str = Query(default="", max_length=120),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Search conversation titles with pagination for older thread retrieval."""
    uid = get_user_id(current_user)

    title_query = (q or "").strip()
    base_filter: Dict[str, Any] = {"user_id": uid}
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


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get messages from a conversation"""
    messages = await db.messages.find(
        {"conversation_id": conversation_id, "user_id": get_user_id(current_user)},
        {"_id": 0}
    ).sort("timestamp", 1).to_list(1000)
    return messages


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a conversation and its messages"""
    uid = get_user_id(current_user)
    conversation_delete = await db.conversations.delete_one({"id": conversation_id, "user_id": uid})
    messages_delete = await db.messages.delete_many({"conversation_id": conversation_id, "user_id": uid})
    await append_audit_event(
        collection="chat_event_logs",
        event_type="conversation_deleted",
        actor_user_id=uid,
        payload={
            "conversation_id": conversation_id,
            "conversation_deleted": conversation_delete.deleted_count,
            "messages_deleted": messages_delete.deleted_count,
        },
    )
    return {"message": "Conversation deleted"}


@router.post("/chat/catchup")
async def catchup_models(
    request: CatchupRequest,
    current_user: dict = Depends(get_current_user)
):
    """Catch up new models with conversation history"""
    if request.message_ids:
        messages = []
        for msg_id in request.message_ids:
            msg = await db.messages.find_one(
                {"id": msg_id, "user_id": get_user_id(current_user)},
                {"_id": 0}
            )
            if msg:
                messages.append(msg)
        messages.sort(key=lambda x: x['timestamp'])
    else:
        messages = await db.messages.find(
            {"conversation_id": request.conversation_id, "user_id": get_user_id(current_user)},
            {"_id": 0}
        ).sort("timestamp", 1).to_list(1000)

    if not messages:
        raise HTTPException(status_code=404, detail="No messages found")

    catchup_parts = ["Here is the conversation history to catch you up:\n"]
    for msg in messages:
        if msg['role'] == 'user':
            catchup_parts.append(f"User: {msg['content']}")
        elif msg['role'] == 'assistant':
            catchup_parts.append(f"{msg['model']}: {msg['content']}")
    catchup_parts.append("\nYou are now caught up. Please acknowledge that you understand the conversation context.")

    return {
        "message": "Catchup initiated",
        "models": request.new_models,
        "message_count": len(messages)
    }
# ratios: loc_comments=674:7 imports_exports=14:7 calls_definitions=151:24
