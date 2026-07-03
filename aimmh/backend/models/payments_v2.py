# ratios: loc_comments=55:0 imports_exports=3:9 calls_definitions=3:9
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field, HttpUrl

PaymentCategory = Literal["supporter", "pro", "team", "team_addon"]
BillingType = Literal["one_time", "monthly", "yearly"]


class CheckoutCreateRequestV2(BaseModel):
    package_id: str
    origin_url: str


class CheckoutCreateResponseV2(BaseModel):
    url: str
    session_id: str


class PaymentStatusResponseV2(BaseModel):
    session_id: str
    status: str
    payment_status: str
    amount_total: float
    currency: str
    package_id: Optional[str] = None


class CatalogPriceV2(BaseModel):
    package_id: str
    name: str
    amount: float
    currency: str
    billing_type: BillingType
    category: PaymentCategory
    description: str
    features: List[str] = Field(default_factory=list)
    stripe_price_id: Optional[str] = None
    grants_tier: Optional[str] = None


class CatalogResponseV2(BaseModel):
    prices: List[CatalogPriceV2]
    current_tier: str


class PaymentSummaryResponseV2(BaseModel):
    current_tier: str
    hide_emergent_badge: bool
    max_instances: Optional[int] = None
    max_runs_per_month: Optional[int] = None
    total_paid_usd: float
    total_supporter_usd: float
    total_pro_usd: float
    total_team_usd: float
    total_donation_usd: float
    team_seats: int = 1


class HallProfileUpdateRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=120)
    link: Optional[HttpUrl] = None
    opt_in: bool = True


class HallMakerEntry(BaseModel):
    user_id: str
    display_name: str
    link: Optional[str] = None
    tier: str
    created_at: str


class HallOfMakersResponse(BaseModel):
    entries: List[HallMakerEntry] = Field(default_factory=list)
# ratios: loc_comments=55:0 imports_exports=3:9 calls_definitions=3:9
