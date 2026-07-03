# ratios: loc_comments=164:7 imports_exports=3:28 calls_definitions=12:28
"""V1 API Pydantic models for the Multi-Model Hub."""

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime


# ---- Model Registry ----

class ModelDef(BaseModel):
    model_id: str
    display_name: Optional[str] = None
    enabled: bool = True


class DeveloperDef(BaseModel):
    developer_id: str
    name: str
    auth_type: str = "emergent"  # emergent | openai_compatible
    base_url: Optional[str] = None
    website: Optional[str] = None
    models: List[ModelDef] = Field(default_factory=list)


class RegistryResponse(BaseModel):
    developers: List[DeveloperDef]


class AddDeveloperRequest(BaseModel):
    developer_id: str
    name: str
    auth_type: str = "openai_compatible"
    base_url: str
    website: Optional[str] = None
    models: List[ModelDef] = Field(default_factory=list)


class AddModelRequest(BaseModel):
    model_id: str
    display_name: Optional[str] = None


# ---- a0 Prompt ----

class ModelContextOverride(BaseModel):
    system_message: Optional[str] = None
    role: Optional[str] = None
    prompt_modifier: Optional[str] = None
    temperature: Optional[float] = None


class PromptRequest(BaseModel):
    message: str
    models: List[str]  # e.g. ["gpt-4o", "claude-4-sonnet-20250514"]
    thread_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None  # S5 context override
    global_context: Optional[str] = None
    per_model_context: Optional[Dict[str, ModelContextOverride]] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    async_mode: bool = False  # if True, return job_id for polling


class PromptSingleRequest(BaseModel):
    message: str
    model: str
    thread_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    global_context: Optional[str] = None
    system_message: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None


class SynthesizeRequest(BaseModel):
    source_message_ids: List[str]
    target_models: List[str]
    synthesis_prompt: Optional[str] = "Synthesize and analyze these AI responses:"
    thread_id: Optional[str] = None


class BatchStep(BaseModel):
    message: str
    models: List[str]
    room: str = "shared"  # "shared" | "individual" | model name
    per_model_context: Optional[Dict[str, ModelContextOverride]] = None
    wait_for_completion: bool = True
    feed_responses_to_next: bool = False


class BatchRequest(BaseModel):
    steps: List[BatchStep]
    thread_id: Optional[str] = None
    async_mode: bool = False


class SharedRoomRequest(BaseModel):
    message: str
    models: List[str]
    rounds: int = 1  # number of discussion rounds
    mode: str = "all"  # "all" = each sees all others | "synthesized" = each sees synthesis
    synthesis_model: Optional[str] = None  # required if mode="synthesized"
    thread_id: Optional[str] = None
    global_context: Optional[str] = None
    per_model_context: Optional[Dict[str, ModelContextOverride]] = None


class DaisyChainRequest(BaseModel):
    message: str
    models: List[str]  # ordered chain: model[0] → model[1] → ...
    rounds: int = 1  # how many times to cycle through all models
    thread_id: Optional[str] = None
    global_context: Optional[str] = None
    per_model_context: Optional[Dict[str, ModelContextOverride]] = None


# ---- Responses ----

class ModelResponse(BaseModel):
    model: str
    message_id: str
    content: str
    response_time_ms: int = 0
    error: Optional[str] = None


class PromptResponse(BaseModel):
    thread_id: str
    responses: List[ModelResponse]
    event_ids: List[str] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    sentinel_context: Dict[str, Any] = Field(default_factory=dict)


class AsyncJobResponse(BaseModel):
    job_id: str
    thread_id: str
    status: str = "running"
    provenance: Dict[str, Any] = Field(default_factory=dict)


class JobStatusResponse(BaseModel):
    job_id: str
    thread_id: str
    status: str  # running | completed | failed
    responses: Optional[List[ModelResponse]] = None
    event_ids: List[str] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    sentinel_context: Dict[str, Any] = Field(default_factory=dict)


# ---- History / Export ----

class ThreadSummary(BaseModel):
    thread_id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int = 0
    models_used: List[str] = Field(default_factory=list)


class ThreadListResponse(BaseModel):
    threads: List[ThreadSummary]
    total: int
    offset: int
    limit: int


class MessageOut(BaseModel):
    message_id: str
    thread_id: str
    role: str
    content: str
    model: str
    timestamp: str
    response_time_ms: Optional[int] = None
    feedback: Optional[str] = None


class ExportResponse(BaseModel):
    thread_id: str
    events: List[Dict[str, Any]]
    messages: List[MessageOut]
    snapshot_id: str
    provenance: Dict[str, Any]


# ---- EDCM ----

class EdcmEvalRequest(BaseModel):
    thread_id: str
    goal_text: Optional[str] = ""
    declared_constraints: Optional[List[str]] = None
    context: Optional[Dict[str, Any]] = None


class EdcmMetricValue(BaseModel):
    value: float
    range: List[float] = [0, 1]


class EdcmAlert(BaseModel):
    name: str
    severity: str
    value: float
    threshold: float


class EdcmBoneReport(BaseModel):
    thread_id: str
    used_context: Dict[str, Any]
    metrics: Dict[str, EdcmMetricValue]
    alerts: List[EdcmAlert]
    recommendations: List[Dict[str, Any]]
    snapshot_id: str
    provenance: Dict[str, Any] = Field(default_factory=dict)
    sentinel_context: Dict[str, Any] = Field(default_factory=dict)


# ---- Keys ----

class SetKeyRequest(BaseModel):
    developer_id: str
    api_key: str


class KeyStatusResponse(BaseModel):
    developer_id: str
    status: str  # configured | missing | universal
    masked_key: Optional[str] = None


class FeedbackRequest(BaseModel):
    message_id: str
    feedback: str  # "up" | "down"
# ratios: loc_comments=164:7 imports_exports=3:28 calls_definitions=12:28
