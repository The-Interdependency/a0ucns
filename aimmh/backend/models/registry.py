# ratios: loc_comments=36:0 imports_exports=3:3 calls_definitions=3:3
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

VerificationScope = Literal["model", "developer", "registry"]
VerificationStatus = Literal[
    "verified",
    "verified_via_provider",
    "missing_key",
    "auth_failed",
    "model_missing",
    "rate_limited",
    "connection_error",
    "error",
]
VerificationMode = Literal["strict", "light"]


class VerifyModelRequest(BaseModel):
    developer_id: str = Field(min_length=1, max_length=120)
    model_id: str = Field(min_length=1, max_length=200)
    mode: VerificationMode = "strict"


class VerificationResult(BaseModel):
    scope: VerificationScope
    developer_id: str
    developer_name: Optional[str] = None
    model_id: Optional[str] = None
    status: VerificationStatus
    message: str
    verification_mode: VerificationMode = "strict"
    website: Optional[str] = None
    base_url: Optional[str] = None
    latency_ms: Optional[int] = None


class VerificationResponse(BaseModel):
    scope: VerificationScope
    verification_mode: VerificationMode
    verified_count: int = 0
    total_count: int = 0
    results: List[VerificationResult] = Field(default_factory=list)
# ratios: loc_comments=36:0 imports_exports=3:3 calls_definitions=3:3
