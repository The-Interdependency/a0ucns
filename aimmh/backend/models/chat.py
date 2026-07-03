# ratios: loc_comments=44:6 imports_exports=3:7 calls_definitions=1:7
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime, timezone


class APIKeyUpdate(BaseModel):
    provider: Literal["gpt", "claude", "gemini", "grok", "deepseek", "perplexity"]
    api_key: Optional[str] = None
    use_universal: bool = False


class APIKeysResponse(BaseModel):
    gpt: Optional[str] = None
    claude: Optional[str] = None
    gemini: Optional[str] = None
    grok: Optional[str] = None
    deepseek: Optional[str] = None
    perplexity: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    models: List[str]
    conversation_id: Optional[str] = None
    # Context semantics
    context_mode: Literal["compartmented", "shared"] = "compartmented"
    shared_room_mode: Literal["parallel_all", "parallel_paired"] = "parallel_all"
    shared_pairs: Optional[Dict[str, List[str]]] = None
    # Context metadata for EDCM/a0
    global_context: Optional[str] = None
    model_roles: Optional[Dict[str, str]] = None
    # If provided, use a model-specific message (prompt properties) instead of `message`
    per_model_messages: Optional[Dict[str, str]] = None
    # For sequential orchestration: avoid duplicating user messages in DB
    persist_user_message: bool = True
    # Optional: limit number of history messages pulled for context
    history_limit: Optional[int] = Field(default=None, ge=0)
    # Optional file/image attachments with targeting controls
    attachments: Optional[List[Dict[str, Any]]] = None


class MessageFeedback(BaseModel):
    message_id: str
    feedback: Literal["up", "down"]


class ConversationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime


class CatchupRequest(BaseModel):
    conversation_id: str
    new_models: List[str]
    message_ids: Optional[List[str]] = None


class SynthesisRequest(BaseModel):
    selected_messages: List[str]
    target_models: List[str]
    synthesis_prompt: str
# ratios: loc_comments=44:6 imports_exports=3:7 calls_definitions=1:7
