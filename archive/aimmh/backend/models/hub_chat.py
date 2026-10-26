# ratios: loc_comments=30:0 imports_exports=3:4 calls_definitions=7:4
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class HubChatPromptRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=12000)
    instance_ids: List[str] = Field(min_length=1)
    label: Optional[str] = Field(default=None, max_length=120)


class HubChatResponseItem(BaseModel):
    prompt_id: str
    instance_id: str
    instance_name: str
    thread_id: str
    model: str
    content: str
    message_id: Optional[str] = None
    response_time_ms: int = 0
    error: Optional[str] = None
    created_at: str


class HubChatPromptOut(BaseModel):
    prompt_id: str
    prompt: str
    label: Optional[str] = None
    instance_ids: List[str] = Field(default_factory=list)
    instance_names: List[str] = Field(default_factory=list)
    created_at: str
    updated_at: str
    responses: List[HubChatResponseItem] = Field(default_factory=list)


class HubChatPromptListResponse(BaseModel):
    prompts: List[HubChatPromptOut] = Field(default_factory=list)
    total: int = 0
# ratios: loc_comments=30:0 imports_exports=3:4 calls_definitions=7:4
