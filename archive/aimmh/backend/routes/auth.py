# ratios: loc_comments=485:6 imports_exports=11:13 calls_definitions=154:14
from fastapi import APIRouter, HTTPException, Depends, Request, Response as FastAPIResponse
from datetime import datetime, timezone, timedelta
import uuid
import os
import httpx
import logging

from db import db
from models.auth import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    GoogleAuthUser,
    ServiceAccountCreateRequest,
    ServiceAccountResponse,
    ServiceAccountTokenRequest,
    ServiceAccountTokenResponse,
    ServiceAccountListResponse,
    ServiceAccountListItem,
    ServiceAccountTokenListResponse,
    ServiceAccountTokenListItem,
    ServiceAccountUpdateRequest,
    ServiceAccountPolicyResponse,
    ServiceAccountPolicyUpdateRequest,
)
from services.auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, get_user_id, generate_service_token, hash_service_token
)
from services.billing_tiers import derive_billing_profile, normalize_tier
from services.audit import append_audit_event

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])


def _set_access_token_cookie(response: FastAPIResponse, token: str) -> None:
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=30 * 24 * 60 * 60,
    )


@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserCreate, response: FastAPIResponse):
    existing_user = await db.users.find_one({"username": user_data.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    user_id = str(uuid.uuid4())
    hashed_pw = hash_password(user_data.password)
    now = datetime.now(timezone.utc)

    user = {
        "id": user_id,
        "username": user_data.username,
        "password": hashed_pw,
        "created_at": now.isoformat(),
        "api_keys": {},
        "billing": {
            "subscription_tier": "free",
            "hide_emergent_badge": False,
            "team_seats": 1,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        },
    }
    await db.users.insert_one(user)

    token = create_access_token(user_id)
    _set_access_token_cookie(response, token)
    billing_profile = derive_billing_profile(user)
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user_id,
            username=user_data.username,
            created_at=now,
            subscription_tier=billing_profile["subscription_tier"],
            hide_emergent_badge=billing_profile["hide_emergent_badge"],
        )
    )


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin, response: FastAPIResponse):
    user = await db.users.find_one({"username": user_data.username})
    if not user or not verify_password(user_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user["id"])
    _set_access_token_cookie(response, token)
    billing_profile = derive_billing_profile(user)
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user["id"],
            username=user["username"],
            created_at=datetime.fromisoformat(user["created_at"]),
            subscription_tier=billing_profile["subscription_tier"],
            hide_emergent_badge=billing_profile["hide_emergent_badge"],
        )
    )


@router.post("/service-account/create", response_model=ServiceAccountResponse)
async def create_service_account(
    payload: ServiceAccountCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a per-user service account for machine/API access."""
    owner_user_id = get_user_id(current_user)
    username = payload.username.strip()
    if not username:
        raise HTTPException(status_code=400, detail="Username is required")

    existing_user = await db.users.find_one({"username": username}, {"_id": 0, "username": 1})
    existing_service_account = await db.service_accounts.find_one({"username": username}, {"_id": 0, "username": 1})
    if existing_user or existing_service_account:
        raise HTTPException(status_code=400, detail="Username already in use")

    now = datetime.now(timezone.utc)
    service_account_id = str(uuid.uuid4())
    service_account_doc = {
        "id": service_account_id,
        "owner_user_id": owner_user_id,
        "username": username,
        "password": hash_password(payload.password),
        "label": payload.label.strip() if payload.label else None,
        "active": True,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    await db.service_accounts.insert_one(service_account_doc)
    await append_audit_event(
        collection="service_account_audit_logs",
        event_type="service_account_created",
        actor_user_id=owner_user_id,
        payload={
            "service_account_id": service_account_id,
            "username": username,
            "label": service_account_doc.get("label"),
        },
    )

    return ServiceAccountResponse(
        id=service_account_id,
        username=username,
        label=service_account_doc.get("label"),
        owner_user_id=owner_user_id,
        active=True,
        created_at=now,
    )


@router.post("/service-account/token", response_model=ServiceAccountTokenResponse)
async def issue_service_account_token(payload: ServiceAccountTokenRequest):
    """Public endpoint: exchange service-account username/password for a long-lived API token."""
    username = payload.username.strip()
    service_account = await db.service_accounts.find_one({"username": username, "active": {"$ne": False}}, {"_id": 0})
    if not service_account or not verify_password(payload.password, service_account["password"]):
        raise HTTPException(status_code=401, detail="Invalid service account credentials")

    owner_user_id = service_account["owner_user_id"]
    owner_user = await db.users.find_one(
        {"$or": [{"id": owner_user_id}, {"user_id": owner_user_id}]},
        {"_id": 0, "service_account_policy": 1}
    )
    policy = owner_user.get("service_account_policy") if owner_user else {}
    one_token_per_bot = bool((policy or {}).get("one_token_per_bot", False))

    if one_token_per_bot:
        revoke_result = await db.service_account_tokens.update_many(
            {
                "service_account_id": service_account["id"],
                "owner_user_id": owner_user_id,
                "revoked": {"$ne": True},
            },
            {
                "$set": {
                    "revoked": True,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
            }
        )
        if revoke_result.modified_count > 0:
            await append_audit_event(
                collection="service_account_audit_logs",
                event_type="service_account_token_rotation_auto_revoke",
                actor_user_id=owner_user_id,
                payload={
                    "service_account_id": service_account["id"],
                    "username": username,
                    "revoked_tokens": revoke_result.modified_count,
                },
            )

    token = generate_service_token()
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=payload.expires_in_days)
    token_doc = {
        "id": str(uuid.uuid4()),
        "service_account_id": service_account["id"],
        "owner_user_id": owner_user_id,
        "token_hash": hash_service_token(token),
        "token_prefix": token[:12],
        "revoked": False,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
        "last_used_at": None,
    }
    await db.service_account_tokens.insert_one(token_doc)
    await append_audit_event(
        collection="service_account_audit_logs",
        event_type="service_account_token_issued",
        actor_user_id=owner_user_id,
        payload={
            "service_account_id": service_account["id"],
            "token_id": token_doc["id"],
            "token_prefix": token_doc["token_prefix"],
            "expires_at": token_doc["expires_at"],
            "one_token_per_bot": one_token_per_bot,
        },
    )

    return ServiceAccountTokenResponse(
        access_token=token,
        expires_at=expires_at,
        service_account_username=username,
    )


@router.get("/service-accounts", response_model=ServiceAccountListResponse)
async def list_service_accounts(current_user: dict = Depends(get_current_user)):
    owner_user_id = get_user_id(current_user)
    cursor = db.service_accounts.find(
        {"owner_user_id": owner_user_id},
        {"_id": 0, "id": 1, "username": 1, "label": 1, "active": 1, "created_at": 1, "updated_at": 1}
    ).sort("created_at", -1)

    items = []
    for account in await cursor.to_list(length=200):
        items.append(
            ServiceAccountListItem(
                id=account["id"],
                username=account["username"],
                label=account.get("label"),
                active=account.get("active", True),
                created_at=account["created_at"],
                updated_at=account.get("updated_at", account["created_at"]),
            )
        )

    return ServiceAccountListResponse(items=items)


@router.get("/service-account/policy", response_model=ServiceAccountPolicyResponse)
async def get_service_account_policy(current_user: dict = Depends(get_current_user)):
    owner_user_id = get_user_id(current_user)
    user_doc = await db.users.find_one(
        {"$or": [{"id": owner_user_id}, {"user_id": owner_user_id}]},
        {"_id": 0, "service_account_policy": 1}
    )
    policy = user_doc.get("service_account_policy") if user_doc else {}
    return ServiceAccountPolicyResponse(
        one_token_per_bot=bool((policy or {}).get("one_token_per_bot", False)),
        updated_at=(policy or {}).get("updated_at"),
    )


@router.put("/service-account/policy", response_model=ServiceAccountPolicyResponse)
async def update_service_account_policy(
    payload: ServiceAccountPolicyUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    owner_user_id = get_user_id(current_user)
    updated_at = datetime.now(timezone.utc).isoformat()
    await db.users.update_one(
        {"$or": [{"id": owner_user_id}, {"user_id": owner_user_id}]},
        {
            "$set": {
                "service_account_policy.one_token_per_bot": bool(payload.one_token_per_bot),
                "service_account_policy.updated_at": updated_at,
            }
        },
    )
    await append_audit_event(
        collection="service_account_audit_logs",
        event_type="service_account_policy_updated",
        actor_user_id=owner_user_id,
        payload={"one_token_per_bot": bool(payload.one_token_per_bot), "updated_at": updated_at},
    )
    return ServiceAccountPolicyResponse(
        one_token_per_bot=bool(payload.one_token_per_bot),
        updated_at=updated_at,
    )


@router.patch("/service-accounts/{service_account_id}", response_model=ServiceAccountResponse)
async def update_service_account(
    service_account_id: str,
    payload: ServiceAccountUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    owner_user_id = get_user_id(current_user)
    service_account = await db.service_accounts.find_one(
        {"id": service_account_id, "owner_user_id": owner_user_id},
        {"_id": 0}
    )
    if not service_account:
        raise HTTPException(status_code=404, detail="Service account not found")

    updates = {}
    if payload.active is not None:
        updates["active"] = payload.active
    if payload.label is not None:
        updates["label"] = payload.label.strip() or None

    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")

    updates["updated_at"] = datetime.now(timezone.utc).isoformat()

    await db.service_accounts.update_one(
        {"id": service_account_id, "owner_user_id": owner_user_id},
        {"$set": updates}
    )
    await append_audit_event(
        collection="service_account_audit_logs",
        event_type="service_account_updated",
        actor_user_id=owner_user_id,
        payload={
            "service_account_id": service_account_id,
            "updates": {k: v for k, v in updates.items() if k != "updated_at"},
        },
    )

    updated = await db.service_accounts.find_one(
        {"id": service_account_id, "owner_user_id": owner_user_id},
        {"_id": 0, "password": 0}
    )
    return ServiceAccountResponse(
        id=updated["id"],
        username=updated["username"],
        label=updated.get("label"),
        owner_user_id=updated["owner_user_id"],
        active=updated.get("active", True),
        created_at=updated["created_at"],
    )


@router.get("/service-accounts/{service_account_id}/tokens", response_model=ServiceAccountTokenListResponse)
async def list_service_account_tokens(
    service_account_id: str,
    current_user: dict = Depends(get_current_user)
):
    owner_user_id = get_user_id(current_user)
    service_account = await db.service_accounts.find_one(
        {"id": service_account_id, "owner_user_id": owner_user_id},
        {"_id": 0, "id": 1}
    )
    if not service_account:
        raise HTTPException(status_code=404, detail="Service account not found")

    cursor = db.service_account_tokens.find(
        {"service_account_id": service_account_id, "owner_user_id": owner_user_id},
        {
            "_id": 0,
            "id": 1,
            "token_prefix": 1,
            "revoked": 1,
            "created_at": 1,
            "expires_at": 1,
            "last_used_at": 1,
        }
    ).sort("created_at", -1)

    items = []
    for token in await cursor.to_list(length=200):
        items.append(
            ServiceAccountTokenListItem(
                id=token["id"],
                token_prefix=token.get("token_prefix", ""),
                revoked=token.get("revoked", False),
                created_at=token["created_at"],
                expires_at=token["expires_at"],
                last_used_at=token.get("last_used_at"),
            )
        )

    return ServiceAccountTokenListResponse(items=items)


@router.post("/service-account/tokens/{token_id}/revoke")
async def revoke_service_account_token(
    token_id: str,
    current_user: dict = Depends(get_current_user)
):
    owner_user_id = get_user_id(current_user)
    token_doc = await db.service_account_tokens.find_one(
        {"id": token_id, "owner_user_id": owner_user_id},
        {"_id": 0, "id": 1, "revoked": 1}
    )
    if not token_doc:
        raise HTTPException(status_code=404, detail="Token not found")

    if token_doc.get("revoked"):
        await append_audit_event(
            collection="service_account_audit_logs",
            event_type="service_account_token_revoke_noop",
            actor_user_id=owner_user_id,
            payload={"token_id": token_id},
        )
        return {"message": "Token already revoked", "token_id": token_id}

    await db.service_account_tokens.update_one(
        {"id": token_id, "owner_user_id": owner_user_id},
        {
            "$set": {
                "revoked": True,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        }
    )
    await append_audit_event(
        collection="service_account_audit_logs",
        event_type="service_account_token_revoked",
        actor_user_id=owner_user_id,
        payload={"token_id": token_id},
    )
    return {"message": "Token revoked", "token_id": token_id}


@router.post("/google/session")
async def process_google_session(request: Request, response: FastAPIResponse):
    """Process Google OAuth session_id from Emergent Auth"""
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        raise HTTPException(status_code=400, detail="No session ID provided")

    auth_service_url = os.environ.get("AUTH_SERVICE_URL")
    if not auth_service_url:
        raise HTTPException(status_code=500, detail="Auth service not configured")

    async with httpx.AsyncClient() as client:
        try:
            auth_response = await client.get(
                f"{auth_service_url}/auth/v1/env/oauth/session-data",
                headers={"X-Session-ID": session_id},
                timeout=10.0
            )
            auth_response.raise_for_status()
            user_data = auth_response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to get session data: {e}")
            raise HTTPException(status_code=401, detail="Invalid session")

    email = user_data.get("email")
    name = user_data.get("name", "")
    picture = user_data.get("picture", "")
    session_token = user_data.get("session_token")

    if not email or not session_token:
        raise HTTPException(status_code=400, detail="Incomplete user data")

    existing_user = await db.users.find_one({"email": email}, {"_id": 0})

    if existing_user:
        user_id = existing_user.get("user_id")
        if not user_id:
            user_id = f"user_{uuid.uuid4().hex[:12]}"
            await db.users.update_one({"email": email}, {"$set": {"user_id": user_id}})
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        user_doc = {
            "user_id": user_id,
            "email": email,
            "name": name,
            "picture": picture,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "api_keys": {}
        }
        await db.users.insert_one(user_doc)

    session_doc = {
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": datetime.now(timezone.utc) + timedelta(days=7),
        "created_at": datetime.now(timezone.utc)
    }
    await db.user_sessions.update_one(
        {"user_id": user_id},
        {"$set": session_doc},
        upsert=True
    )

    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7 * 24 * 60 * 60
    )

    # Also issue JWT so auth works in browsers/environments blocking third-party cookies (e.g., incognito)
    access_token = create_access_token(user_id)
    _set_access_token_cookie(response, access_token)

    return GoogleAuthUser(
        user_id=user_id,
        email=email,
        name=name,
        picture=picture,
        access_token=access_token,
    )


@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user info"""
    billing_profile = derive_billing_profile(current_user)
    return {
        "user_id": current_user.get("user_id") or current_user.get("id"),
        "email": current_user.get("email") or current_user.get("username"),
        "name": current_user.get("name", current_user.get("username", "")),
        "picture": current_user.get("picture"),
        "subscription_tier": normalize_tier((current_user.get("billing") or {}).get("subscription_tier")),
        "hide_emergent_badge": billing_profile["hide_emergent_badge"],
        "team_seats": billing_profile["team_seats"],
    }


@router.post("/logout")
async def logout(
    request: Request,
    response: FastAPIResponse,
    current_user: dict = Depends(get_current_user)
):
    """Logout user (clears session)"""
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
        response.delete_cookie(key="session_token", path="/")
    response.delete_cookie(key="access_token", path="/")
    return {"message": "Logged out successfully"}
# ratios: loc_comments=485:6 imports_exports=11:13 calls_definitions=154:14
