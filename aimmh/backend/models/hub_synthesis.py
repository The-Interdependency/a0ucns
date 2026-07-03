# ratios: loc_comments=40:0 imports_exports=3:5 calls_definitions=10:5
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class SynthesisSourceBlock(BaseModel):
    source_type: str = Field(default="response_block")
    source_id: str
    source_label: Optional[str] = None
    instance_id: Optional[str] = None
    instance_name: Optional[str] = None
    model: Optional[str] = None
    content: str


class HubSynthesisRequest(BaseModel):
    synthesis_instance_ids: List[str] = Field(min_length=1)
    selected_blocks: List[SynthesisSourceBlock] = Field(min_length=1)
    instruction: Optional[str] = Field(default=None, max_length=4000)
    label: Optional[str] = Field(default=None, max_length=120)


class HubSynthesisOutput(BaseModel):
    synthesis_batch_id: str
    synthesis_instance_id: str
    synthesis_instance_name: str
    model: str
    thread_id: str
    content: str
    message_id: Optional[str] = None
    response_time_ms: int = 0
    error: Optional[str] = None
    created_at: str


class HubSynthesisBatchOut(BaseModel):
    synthesis_batch_id: str
    label: Optional[str] = None
    instruction: Optional[str] = None
    selected_blocks: List[SynthesisSourceBlock] = Field(default_factory=list)
    synthesis_instance_ids: List[str] = Field(default_factory=list)
    synthesis_instance_names: List[str] = Field(default_factory=list)
    outputs: List[HubSynthesisOutput] = Field(default_factory=list)
    created_at: str
    updated_at: str


class HubSynthesisBatchListResponse(BaseModel):
    batches: List[HubSynthesisBatchOut] = Field(default_factory=list)
    total: int = 0
# ratios: loc_comments=40:0 imports_exports=3:5 calls_definitions=10:5
