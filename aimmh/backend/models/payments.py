# ratios: loc_comments=37:0 imports_exports=2:6 calls_definitions=1:6
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Literal


class CheckoutCreateRequest(BaseModel):
    package_id: str
    origin_url: str


class CheckoutCreateResponse(BaseModel):
    url: str
    session_id: str


class PaymentStatusResponse(BaseModel):
    session_id: str
    status: str
    payment_status: str
    amount_total: float
    currency: str
    package_id: Optional[str] = None


class CatalogPrice(BaseModel):
    package_id: str
    name: str
    amount: float
    currency: str
    billing_type: Literal["one_time", "monthly"]
    category: Literal["core", "support", "founder", "credits"]
    description: str
    features: List[str] = Field(default_factory=list)
    stripe_price_id: Optional[str] = None


class CatalogResponse(BaseModel):
    prices: List[CatalogPrice]
    founder_slots_total: int
    founder_slots_remaining: int


class PaymentSummaryResponse(BaseModel):
    total_paid_usd: float
    total_support_usd: float
    total_founder_usd: float
    total_compute_usd: float
    total_core_usd: float
    estimated_usage_cost_usd: float
    total_estimated_tokens: int
# ratios: loc_comments=37:0 imports_exports=2:6 calls_definitions=1:6
