# ratios: loc_comments=41:0 imports_exports=2:5 calls_definitions=2:5
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal


class A0IngestRequest(BaseModel):
    conversation_id: str
    title: Optional[str] = None
    messages: Optional[List[Dict[str, Any]]] = None
    global_context: Optional[str] = None
    model_roles: Optional[Dict[str, str]] = None
    context_mode: Optional[str] = None
    shared_room_mode: Optional[str] = None
    shared_pairs: Optional[Dict[str, List[str]]] = None
    metadata: Optional[Dict[str, Any]] = None


class A0RouteRequest(BaseModel):
    message: str
    models: List[str]


class A0NonUIPromptRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    context_mode: Literal["compartmented", "shared"] = "compartmented"
    shared_room_mode: Literal["parallel_all", "parallel_paired"] = "parallel_all"
    shared_pairs: Optional[Dict[str, List[str]]] = None
    global_context: Optional[str] = None
    model_roles: Optional[Dict[str, str]] = None
    per_model_messages: Optional[Dict[str, str]] = None
    persist_user_message: bool = True
    history_limit: Optional[int] = Field(default=None, ge=0)
    attachments: Optional[List[Dict[str, Any]]] = None


class A0NonUISelectedPromptRequest(A0NonUIPromptRequest):
    models: List[str]


class A0NonUISynthesisRequest(BaseModel):
    conversation_id: str
    selected_message_ids: List[str]
    target_models: List[str]
    synthesis_prompt: Optional[str] = "Synthesize and analyze these AI responses:"
    source_model: Optional[str] = None
    context_mode: Literal["compartmented", "shared"] = "compartmented"
    shared_room_mode: Literal["parallel_all", "parallel_paired"] = "parallel_all"
    shared_pairs: Optional[Dict[str, List[str]]] = None
    global_context: Optional[str] = None
    model_roles: Optional[Dict[str, str]] = None
    history_limit: Optional[int] = Field(default=None, ge=0)
# ratios: loc_comments=41:0 imports_exports=2:5 calls_definitions=2:5
