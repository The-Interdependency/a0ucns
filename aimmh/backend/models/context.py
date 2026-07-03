# ratios: loc_comments=16:0 imports_exports=2:2 calls_definitions=2:2
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any


class ContextLogUpdateRequest(BaseModel):
    message: Optional[str] = None
    global_context: Optional[str] = None
    model_roles: Optional[Dict[str, str]] = None
    per_model_messages: Optional[Dict[str, str]] = None
    context_mode: Optional[str] = None
    shared_room_mode: Optional[str] = None
    shared_pairs: Optional[Dict[str, List[str]]] = None
    metadata: Optional[Dict[str, Any]] = None


class CostLimitPreferencesRequest(BaseModel):
    enforce_token_limit: bool = False
    enforce_cost_limit: bool = False
    token_limit: int = Field(default=25000, ge=1000, le=5000000)
    cost_limit_usd: float = Field(default=25.0, ge=1.0, le=10000.0)
# ratios: loc_comments=16:0 imports_exports=2:2 calls_definitions=2:2
