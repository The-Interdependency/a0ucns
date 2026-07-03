# ratios: loc_comments=72:0 imports_exports=3:16 calls_definitions=3:16
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone


class UserCreate(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    created_at: datetime
    subscription_tier: str = "free"
    hide_emergent_badge: bool = False


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class GoogleAuthUser(BaseModel):
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    access_token: Optional[str] = None
    token_type: str = "bearer"


class ServiceAccountCreateRequest(BaseModel):
    username: str
    password: str
    label: Optional[str] = None


class ServiceAccountResponse(BaseModel):
    id: str
    username: str
    label: Optional[str] = None
    owner_user_id: str
    active: bool
    created_at: datetime


class ServiceAccountTokenRequest(BaseModel):
    username: str
    password: str
    expires_in_days: int = Field(default=90, ge=1, le=365)


class ServiceAccountTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    service_account_username: str


class ServiceAccountListItem(BaseModel):
    id: str
    username: str
    label: Optional[str] = None
    active: bool
    created_at: datetime
    updated_at: datetime


class ServiceAccountListResponse(BaseModel):
    items: list[ServiceAccountListItem] = Field(default_factory=list)


class ServiceAccountTokenListItem(BaseModel):
    id: str
    token_prefix: str
    revoked: bool
    created_at: datetime
    expires_at: datetime
    last_used_at: Optional[datetime] = None


class ServiceAccountTokenListResponse(BaseModel):
    items: list[ServiceAccountTokenListItem] = Field(default_factory=list)


class ServiceAccountUpdateRequest(BaseModel):
    active: Optional[bool] = None
    label: Optional[str] = None


class ServiceAccountPolicyResponse(BaseModel):
    one_token_per_bot: bool
    updated_at: Optional[datetime] = None


class ServiceAccountPolicyUpdateRequest(BaseModel):
    one_token_per_bot: bool
# ratios: loc_comments=72:0 imports_exports=3:16 calls_definitions=3:16
