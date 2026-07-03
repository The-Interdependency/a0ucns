# ratios: loc_comments=9:0 imports_exports=3:2 calls_definitions=2:2
from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel, Field


class HubStateUpsertRequest(BaseModel):
    payload: Dict[str, Any] = Field(default_factory=dict)


class HubStateOut(BaseModel):
    state_key: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    updated_at: str
# ratios: loc_comments=9:0 imports_exports=3:2 calls_definitions=2:2
