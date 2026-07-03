# ratios: loc_comments=161:0 imports_exports=4:21 calls_definitions=34:21
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from models.v1 import ModelContextOverride

HubPattern = Literal[
    "fan_out",
    "daisy_chain",
    "room_all",
    "room_synthesized",
    "council",
    "roleplay",
]

HubSourceType = Literal["instance", "group"]
HubStageInputMode = Literal["root_prompt", "previous_outputs", "root_plus_previous"]


class HubInstanceBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    model_id: str = Field(min_length=1, max_length=200)
    role_preset: Optional[str] = Field(default=None, max_length=80)
    context: Optional[ModelContextOverride] = None
    instance_prompt: Optional[str] = Field(default=None, max_length=8000)
    history_window_messages: int = Field(default=12, ge=0, le=100)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class HubInstanceCreateRequest(HubInstanceBase):
    archived: bool = False


class HubInstanceUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    model_id: Optional[str] = Field(default=None, min_length=1, max_length=200)
    role_preset: Optional[str] = Field(default=None, max_length=80)
    context: Optional[ModelContextOverride] = None
    instance_prompt: Optional[str] = Field(default=None, max_length=8000)
    history_window_messages: Optional[int] = Field(default=None, ge=0, le=100)
    metadata: Optional[Dict[str, Any]] = None
    archived: Optional[bool] = None


class HubInstanceOut(HubInstanceBase):
    instance_id: str
    thread_id: str
    archived: bool = False
    archived_at: Optional[str] = None
    created_at: str
    updated_at: str


class HubInstanceListResponse(BaseModel):
    instances: List[HubInstanceOut]
    total: int


class HubMemberRef(BaseModel):
    member_type: HubSourceType
    member_id: str
    alias: Optional[str] = Field(default=None, max_length=120)


class HubGroupCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=1000)
    members: List[HubMemberRef] = Field(default_factory=list)
    archived: bool = False


class HubGroupUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=1000)
    members: Optional[List[HubMemberRef]] = None
    archived: Optional[bool] = None


class HubGroupOut(BaseModel):
    group_id: str
    name: str
    description: Optional[str] = None
    members: List[HubMemberRef] = Field(default_factory=list)
    archived: bool = False
    archived_at: Optional[str] = None
    created_at: str
    updated_at: str


class HubGroupListResponse(BaseModel):
    groups: List[HubGroupOut]
    total: int


class HubStageParticipant(BaseModel):
    source_type: HubSourceType
    source_id: str


class HubStageRequest(BaseModel):
    pattern: HubPattern
    name: Optional[str] = Field(default=None, max_length=120)
    prompt: Optional[str] = Field(default=None, max_length=12000)
    input_mode: HubStageInputMode = "root_plus_previous"
    participants: List[HubStageParticipant] = Field(default_factory=list)
    rounds: int = Field(default=1, ge=1, le=10)
    max_history: int = Field(default=30, ge=1, le=200)
    verbosity: Optional[int] = Field(default=None, ge=1, le=10)
    include_original_prompt: bool = True
    synthesis_prompt: Optional[str] = Field(default=None, max_length=4000)
    synthesis_instance_id: Optional[str] = None
    synthesis_group_id: Optional[str] = None
    player_participants: List[HubStageParticipant] = Field(default_factory=list)
    dm_instance_id: Optional[str] = None
    dm_group_id: Optional[str] = None
    action_word_limit: Optional[int] = Field(default=None, ge=10, le=2000)
    use_initiative: bool = True
    allow_reactions: bool = False


class HubRunRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=12000)
    label: Optional[str] = Field(default=None, max_length=120)
    stages: List[HubStageRequest] = Field(min_length=1)
    persist_instance_threads: bool = True


class HubRunResult(BaseModel):
    run_step_id: str
    run_id: str
    stage_index: int
    stage_name: Optional[str] = None
    pattern: HubPattern
    instance_id: Optional[str] = None
    instance_name: Optional[str] = None
    thread_id: Optional[str] = None
    message_id: Optional[str] = None
    model: str
    content: str
    response_time_ms: int = 0
    error: Optional[str] = None
    feedback: Optional[str] = None
    round_num: int = 0
    step_num: int = 0
    initiative: int = 0
    role: str = "player"
    slot_idx: int = 0
    created_at: str


class HubStageSummary(BaseModel):
    stage_index: int
    stage_name: Optional[str] = None
    pattern: HubPattern
    prompt_used: str
    participants: List[str] = Field(default_factory=list)
    result_count: int = 0


class HubRunOut(BaseModel):
    run_id: str
    label: Optional[str] = None
    prompt: str
    status: str
    archived: bool = False
    archived_at: Optional[str] = None
    stage_summaries: List[HubStageSummary] = Field(default_factory=list)
    created_at: str
    updated_at: str


class HubRunDetailResponse(HubRunOut):
    results: List[HubRunResult] = Field(default_factory=list)


class HubRunListResponse(BaseModel):
    runs: List[HubRunOut]
    total: int


class HubHistoryMessage(BaseModel):
    message_id: str
    thread_id: str
    role: str
    content: str
    model: Optional[str] = None
    timestamp: str
    hub_run_id: Optional[str] = None
    hub_stage_index: Optional[int] = None
    hub_pattern: Optional[str] = None
    hub_instance_id: Optional[str] = None
    hub_prompt_id: Optional[str] = None
    hub_synthesis_batch_id: Optional[str] = None
    hub_role: Optional[str] = None


class HubInstanceHistoryResponse(BaseModel):
    instance_id: str
    thread_id: str
    messages: List[HubHistoryMessage] = Field(default_factory=list)


class HubConnectionsResponse(BaseModel):
    fastapi_connections: Dict[str, Dict[str, str]]
    patterns: List[str]
    supports: Dict[str, bool]
# ratios: loc_comments=161:0 imports_exports=4:21 calls_definitions=34:21
