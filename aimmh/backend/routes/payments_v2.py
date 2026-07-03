# ratios: loc_comments=403:0 imports_exports=13:8 calls_definitions=104:13
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict
import logging
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionRequest

from db import db
from models.payments_v2 import (
    CatalogPriceV2,
    CatalogResponseV2,
    CheckoutCreateRequestV2,
    CheckoutCreateResponseV2,
    HallMakerEntry,
    HallOfMakersResponse,
    HallProfileUpdateRequest,
    PaymentSummaryResponseV2,
    PaymentStatusResponseV2,
)
from services.audit import append_audit_event
from services.auth import get_current_user, get_user_id
from services.billing_tiers import derive_billing_profile, get_user_doc, iso_now, merge_tier

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/payments", tags=["payments_v2"])

PACKAGES: Dict[str, Dict[str, Any]] = {
    "supporter_monthly": {
        "name": "Supporter — $5 / month",
        "amount": 5.00,
        "currency": "usd",
        "billing_type": "monthly",
        "category": "supporter",
        "description": "Support the AIMMH project and unlock supporter perks.",
        "grants_tier": "supporter",
        "features": [
            "15 persistent instances",
            "30 runs per month",
            "Remove Made with Emergent badge",
            "Hall of Makers eligibility",
            "Early feature voting",
            "Private thank-you channel",
        ],
    },
    "supporter_coffee": {
        "name": "Coffee — $5 one-time",
        "amount": 5.00,
        "currency": "usd",
        "billing_type": "one_time",
        "category": "supporter",
        "description": "One-time supporter donation.",
        "grants_tier": "supporter",
        "features": [
            "Supporter perks",
            "Hall of Makers eligibility",
            "One-time donation",
        ],
    },
    "supporter_builder": {
        "name": "Builder — $25 one-time",
        "amount": 25.00,
        "currency": "usd",
        "billing_type": "one_time",
        "category": "supporter",
        "description": "Builder-level one-time supporter donation.",
        "grants_tier": "supporter",
        "features": [
            "Supporter perks",
            "Hall of Makers eligibility",
            "Builder donation tier",
        ],
    },
    "supporter_patron": {
        "name": "Patron — $50 one-time",
        "amount": 50.00,
        "currency": "usd",
        "billing_type": "one_time",
        "category": "supporter",
        "description": "Patron-level one-time supporter donation.",
        "grants_tier": "supporter",
        "features": [
            "Supporter perks",
            "Hall of Makers eligibility",
            "Patron donation tier",
        ],
    },
    "pro_monthly": {
        "name": "Pro — $19 / month",
        "amount": 19.00,
        "currency": "usd",
        "billing_type": "monthly",
        "category": "pro",
        "description": "Unlimited AIMMH access with advanced synthesis and priority support.",
        "grants_tier": "pro",
        "features": [
            "Unlimited instances",
            "Unlimited runs",
            "Advanced synthesis",
            "Priority support",
            "All supporter perks",
        ],
    },
    "pro_yearly": {
        "name": "Pro — $149 / year",
        "amount": 149.00,
        "currency": "usd",
        "billing_type": "yearly",
        "category": "pro",
        "description": "Yearly Pro access at a discount.",
        "grants_tier": "pro",
        "features": [
            "Unlimited instances",
            "Unlimited runs",
            "Advanced synthesis",
            "Priority support",
            "All supporter perks",
        ],
    },
    "team_monthly": {
        "name": "Team — $49 / month (3 seats)",
        "amount": 49.00,
        "currency": "usd",
        "billing_type": "monthly",
        "category": "team",
        "description": "Team base plan with 3 seats and shared workspace foundation.",
        "grants_tier": "team",
        "team_seat_delta": 3,
        "features": [
            "Unlimited instances",
            "Unlimited runs",
            "3 seats included",
            "Shared workspace foundation",
            "Admin controls foundation",
            "All supporter perks",
        ],
    },
    "team_extra_seat_monthly": {
        "name": "Team extra seat — $15 / month",
        "amount": 15.00,
        "currency": "usd",
        "billing_type": "monthly",
        "category": "team_addon",
        "description": "Add an extra team seat to an existing Team plan.",
        "grants_tier": "team",
        "team_seat_delta": 1,
        "features": ["Adds 1 extra team seat"],
    },
}


def _stripe_key() -> str:
    return os.environ["STRIPE_API_KEY"]


def _stripe_mode() -> str:
    key = os.environ.get("STRIPE_API_KEY", "")
    if not key:
        return "missing"
    if key.startswith("sk_live_") or key.startswith("rk_live_"):
        return "live"
    if key.startswith("sk_test_") or key.startswith("rk_test_"):
        return "test"
    return "unknown"


def _build_checkout(request: Request) -> StripeCheckout:
    host_url = str(request.base_url).rstrip("/")
    webhook_url = f"{host_url}/api/payments/webhook/stripe"
    return StripeCheckout(api_key=_stripe_key(), webhook_url=webhook_url)


async def _ensure_catalog_seeded() -> None:
    for package_id, package in PACKAGES.items():
        await db.payment_catalog.update_one(
            {"package_id": package_id},
            {
                "$set": {
                    "package_id": package_id,
                    **package,
                    "updated_at": iso_now(),
                },
                "$setOnInsert": {"created_at": iso_now()},
            },
            upsert=True,
        )


async def _fulfill_transaction_once(session_id: str) -> None:
    tx = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
    if not tx:
        return
    lock_result = await db.payment_transactions.update_one(
        {"session_id": session_id, "fulfilled": {"$ne": True}},
        {"$set": {"fulfilled": True, "fulfilled_at": iso_now(), "updated_at": iso_now()}},
    )
    if lock_result.modified_count == 0:
        return

    user_id = tx.get("user_id")
    if not user_id:
        return
    package = PACKAGES.get(tx.get("package_id"))
    if not package:
        return

    user_doc = await get_user_doc(user_id)
    current_billing = (user_doc or {}).get("billing", {}) or {}
    next_tier = merge_tier(current_billing.get("subscription_tier", "free"), package.get("grants_tier", "free"))

    inc_fields: Dict[str, Any] = {
        "billing.total_paid_usd": float(package["amount"]),
    }
    set_fields: Dict[str, Any] = {
        "billing.subscription_tier": next_tier,
        "billing.hide_emergent_badge": next_tier in {"supporter", "pro", "team"},
        "billing.supporter_eligible": next_tier in {"supporter", "pro", "team"},
        "billing.updated_at": iso_now(),
    }

    category = package["category"]
    if category == "supporter":
        inc_fields["billing.total_supporter_usd"] = float(package["amount"])
        inc_fields["billing.total_donation_usd"] = float(package["amount"])
    elif category == "pro":
        inc_fields["billing.total_pro_usd"] = float(package["amount"])
    elif category in {"team", "team_addon"}:
        inc_fields["billing.total_team_usd"] = float(package["amount"])
        inc_fields["billing.team_seats"] = int(package.get("team_seat_delta") or 0)
        if category == "team" and not current_billing.get("team_seats"):
            set_fields["billing.team_seats"] = 3

    await db.users.update_one(
        {"$or": [{"id": user_id}, {"user_id": user_id}]},
        {"$inc": inc_fields, "$set": set_fields},
    )

    await append_audit_event(
        collection="payment_audit_logs",
        event_type="aimmh_payment_fulfillment_applied",
        actor_user_id=user_id,
        payload={
            "session_id": session_id,
            "package_id": tx.get("package_id"),
            "category": category,
            "amount": float(package["amount"]),
            "tier": next_tier,
        },
    )


@router.get("/catalog", response_model=CatalogResponseV2)
async def get_catalog(current_user: dict = Depends(get_current_user)):
    await _ensure_catalog_seeded()
    user_id = get_user_id(current_user)
    profile = await get_user_doc(user_id)
    billing_profile = derive_billing_profile(profile)
    rows = await db.payment_catalog.find({"package_id": {"$in": list(PACKAGES.keys())}}, {"_id": 0}).to_list(200)
    catalog_map = {row["package_id"]: row for row in rows}
    prices = [CatalogPriceV2(
        package_id=package_id,
        name=package["name"],
        amount=float(package["amount"]),
        currency=package["currency"],
        billing_type=package["billing_type"],
        category=package["category"],
        description=package["description"],
        features=package.get("features", []),
        stripe_price_id=catalog_map.get(package_id, {}).get("stripe_price_id"),
        grants_tier=package.get("grants_tier"),
    ) for package_id, package in PACKAGES.items()]
    return CatalogResponseV2(prices=prices, current_tier=billing_profile["subscription_tier"])


@router.post("/checkout/session", response_model=CheckoutCreateResponseV2)
async def create_checkout_session(checkout_data: CheckoutCreateRequestV2, request: Request, current_user: dict = Depends(get_current_user)):
    package = PACKAGES.get(checkout_data.package_id)
    if not package:
        raise HTTPException(status_code=400, detail="Invalid package")
    if not checkout_data.origin_url.startswith("http://") and not checkout_data.origin_url.startswith("https://"):
        raise HTTPException(status_code=400, detail="Invalid origin URL")

    await _ensure_catalog_seeded()
    price_doc = await db.payment_catalog.find_one({"package_id": checkout_data.package_id}, {"_id": 0})
    if not price_doc:
        raise HTTPException(status_code=500, detail="Payment catalog unavailable for selected package")

    user_id = get_user_id(current_user)
    user_email = current_user.get("email") or current_user.get("username") or ""
    base_url = checkout_data.origin_url.rstrip("/")
    success_url = f"{base_url}/pricing?session_id={{CHECKOUT_SESSION_ID}}&checkout=success"
    cancel_url = f"{base_url}/pricing?checkout=cancel"
    metadata = {
        "user_id": str(user_id),
        "email": str(user_email),
        "package_id": checkout_data.package_id,
        "billing_type": package["billing_type"],
        "category": package["category"],
        "grants_tier": package.get("grants_tier", "free"),
    }

    stripe_checkout = _build_checkout(request)
    stripe_price_id = price_doc.get("stripe_price_id")
    checkout_request = CheckoutSessionRequest(
        stripe_price_id=stripe_price_id,
        quantity=1,
        success_url=success_url,
        cancel_url=cancel_url,
        metadata=metadata,
    ) if stripe_price_id else CheckoutSessionRequest(
        amount=float(package["amount"]),
        currency=package["currency"],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata=metadata,
    )
    try:
        session = await stripe_checkout.create_checkout_session(checkout_request)
    except Exception as exc:
        logger.error("Stripe checkout session creation failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"Stripe checkout initialization failed: {exc}")

    tx_doc = {
        "id": str(uuid.uuid4()),
        "session_id": session.session_id,
        "payment_id": None,
        "package_id": checkout_data.package_id,
        "user_id": user_id,
        "email": user_email,
        "amount": float(package["amount"]),
        "currency": package["currency"],
        "category": package["category"],
        "billing_type": package["billing_type"],
        "status": "initiated",
        "payment_status": "pending",
        "metadata": metadata,
        "stripe_price_id": stripe_price_id,
        "created_at": iso_now(),
        "updated_at": iso_now(),
        "fulfilled": False,
    }
    await db.payment_transactions.update_one({"session_id": session.session_id}, {"$set": tx_doc}, upsert=True)
    return CheckoutCreateResponseV2(url=session.url, session_id=session.session_id)


@router.get("/checkout/status/{session_id}", response_model=PaymentStatusResponseV2)
async def get_checkout_status(session_id: str, request: Request, current_user: dict = Depends(get_current_user)):
    _ = current_user
    stripe_checkout = _build_checkout(request)
    try:
        status = await stripe_checkout.get_checkout_status(session_id)
    except Exception as exc:
        logger.error("Stripe checkout status fetch failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"Stripe status check failed: {exc}")

    amount_total = float(status.amount_total) / 100.0 if status.amount_total else 0.0
    metadata = status.metadata or {}
    package_id = metadata.get("package_id")
    await db.payment_transactions.update_one(
        {"session_id": session_id},
        {"$set": {"status": status.status, "payment_status": status.payment_status, "amount_total": amount_total, "currency": status.currency, "metadata": metadata, "updated_at": iso_now()}},
    )
    if status.payment_status == "paid":
        await _fulfill_transaction_once(session_id)
    return PaymentStatusResponseV2(session_id=session_id, status=status.status, payment_status=status.payment_status, amount_total=amount_total, currency=status.currency, package_id=package_id)


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    stripe_checkout = _build_checkout(request)
    body = await request.body()
    signature = request.headers.get("Stripe-Signature")
    try:
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
    except Exception as exc:
        logger.error("Stripe webhook processing failed: %s", exc)
        raise HTTPException(status_code=400, detail=f"Invalid Stripe webhook: {exc}")
    session_id = webhook_response.session_id
    if session_id:
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": {"event_type": webhook_response.event_type, "event_id": webhook_response.event_id, "payment_status": webhook_response.payment_status or "pending", "status": webhook_response.event_type, "metadata": webhook_response.metadata or {}, "updated_at": iso_now()}},
        )
        if webhook_response.payment_status == "paid":
            await _fulfill_transaction_once(session_id)
    return {"ok": True}


@router.get("/summary", response_model=PaymentSummaryResponseV2)
async def get_payments_summary(current_user: dict = Depends(get_current_user)):
    user_id = get_user_id(current_user)
    user_doc = await get_user_doc(user_id)
    billing_profile = derive_billing_profile(user_doc)
    billing = (user_doc or {}).get("billing", {}) or {}
    return PaymentSummaryResponseV2(
        current_tier=billing_profile["subscription_tier"],
        hide_emergent_badge=billing_profile["hide_emergent_badge"],
        max_instances=billing_profile["max_instances"],
        max_runs_per_month=billing_profile["max_runs_per_month"],
        total_paid_usd=float(billing.get("total_paid_usd") or 0.0),
        total_supporter_usd=float(billing.get("total_supporter_usd") or 0.0),
        total_pro_usd=float(billing.get("total_pro_usd") or 0.0),
        total_team_usd=float(billing.get("total_team_usd") or 0.0),
        total_donation_usd=float(billing.get("total_donation_usd") or 0.0),
        team_seats=int(billing.get("team_seats") or billing_profile["team_seats"]),
    )


@router.get("/stripe/mode")
async def get_stripe_mode(current_user: dict = Depends(get_current_user)):
    _ = current_user
    mode = _stripe_mode()
    return {
        "stripe_mode": mode,
        "key_present": mode != "missing",
    }


@router.put("/hall-of-makers/profile")
async def update_hall_profile(payload: HallProfileUpdateRequest, current_user: dict = Depends(get_current_user)):
    user_id = get_user_id(current_user)
    user_doc = await get_user_doc(user_id)
    billing_profile = derive_billing_profile(user_doc)
    if not billing_profile["supporter_eligible"]:
        raise HTTPException(status_code=403, detail="Paid supporter tier required")
    doc = {
        "user_id": user_id,
        "display_name": payload.display_name,
        "link": str(payload.link) if payload.link else None,
        "tier": billing_profile["subscription_tier"],
        "opt_in": payload.opt_in,
        "updated_at": iso_now(),
    }
    await db.hall_of_makers.update_one({"user_id": user_id}, {"$set": doc, "$setOnInsert": {"created_at": iso_now()}}, upsert=True)
    return {"message": "Hall of Makers profile updated"}


@router.get("/hall-of-makers", response_model=HallOfMakersResponse)
async def get_hall_of_makers():
    cursor = db.hall_of_makers.find({"opt_in": True}, {"_id": 0}).sort("created_at", 1)
    docs = await cursor.to_list(500)
    return HallOfMakersResponse(entries=[HallMakerEntry(**doc) for doc in docs])
# ratios: loc_comments=403:0 imports_exports=13:8 calls_definitions=104:13
