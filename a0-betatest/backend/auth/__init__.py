# ratios: loc_comments=358:79 imports_exports=21:17 calls_definitions=147:29
# === MODULE_BUILD ===
# id: auth_routes
#   module_name: routes
#   module_kind: route
#   summary: hybrid JWT auth + OAuth (Emergent Google, GitHub) — /api/auth/{register,login,logout,me,refresh,oauth/*}; username (unique) + email (unique) + ≥16-char passphrase; bcrypt; httpOnly cookies; brute-force lockout
#   owner: Erin Spencer
#   public_surface: router, get_current_user, get_current_user_or_demo, init_auth, seed_admin
#   internal_surface: _hash_password, _verify_password, _make_tokens, _record_attempt, _is_locked, _link_oauth_user
#   auth_boundary: bearer
#   storage_boundary: write
#   network_boundary: external
#   user_data_boundary: write
#   admin_only: false
#   tests: a0p_skills.contracts.auth_register_login_round_trip_holds
#   rollout: default_enabled
#   rollback: revert; multi-tenancy collapses to user_id='local' anonymous mode
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: auth_routes_boundaries
#   summary: auth endpoints + OAuth callbacks; reads/writes users, login_attempts, password_reset_tokens
#   auth_boundary: bearer
#   storage_boundary: write
#   network_boundary: external
#   user_data_boundary: write
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: auth_routes
#   summary: hybrid JWT + OAuth endpoints
#   exposes: router, get_current_user, get_current_user_or_demo, init_auth, seed_admin
#   boundaries: auth:bearer, storage:write, network:external, user_data:write
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: auth_register_login_round_trip
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.auth_register_login_round_trip_holds
# === END CONTRACTS ===
"""Hybrid auth — JWT + Emergent Google + GitHub OAuth.

User schema (in `users` collection):
    {
      _id: <uuid>,
      username: <unique, [a-z0-9_-]{3,32}>,
      email: <unique, lowercased>,
      password_hash: <bcrypt> or null,
      auth_methods: ["password" | "google" | "github" | ...],
      oauth_subjects: {"google": "<sub>", "github": "<id>"},
      role: "user" | "admin",
      created_at_ms: <int>,
      last_login_at_ms: <int>,
    }
"""
from __future__ import annotations
import os
import re
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt as pyjwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, Field, ConfigDict


router = APIRouter(prefix="/api/auth", tags=["auth"])

_JWT_ALG = "HS256"
_ACCESS_TTL = timedelta(minutes=120)  # 2h access
_REFRESH_TTL = timedelta(days=14)
_USERNAME_RE = re.compile(r"^[a-z0-9_-]{3,32}$")
_MAX_FAILS = 5
_LOCK_MIN = 15


def _jwt_secret() -> str:
    return os.environ["JWT_SECRET"]


def _now_ms() -> int:
    return int(time.time() * 1000)


def _hash_password(plain: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")


def _verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def _make_tokens(user_id: str, email: str) -> tuple[str, str]:
    now = datetime.now(timezone.utc)
    access = pyjwt.encode(
        {"sub": user_id, "email": email, "type": "access", "iat": int(now.timestamp()),
         "exp": int((now + _ACCESS_TTL).timestamp())},
        _jwt_secret(), algorithm=_JWT_ALG,
    )
    refresh = pyjwt.encode(
        {"sub": user_id, "type": "refresh", "iat": int(now.timestamp()),
         "exp": int((now + _REFRESH_TTL).timestamp())},
        _jwt_secret(), algorithm=_JWT_ALG,
    )
    return access, refresh


def _set_cookies(resp: Response, access: str, refresh: str) -> None:
    resp.set_cookie("access_token", access, httponly=True, secure=False,
                    samesite="lax", max_age=int(_ACCESS_TTL.total_seconds()), path="/")
    resp.set_cookie("refresh_token", refresh, httponly=True, secure=False,
                    samesite="lax", max_age=int(_REFRESH_TTL.total_seconds()), path="/")


def _clear_cookies(resp: Response) -> None:
    resp.delete_cookie("access_token", path="/")
    resp.delete_cookie("refresh_token", path="/")


# ---- Pydantic request bodies ---------------------------------------------
class RegisterBody(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    username: str = Field(..., min_length=3, max_length=32)
    email: EmailStr
    passphrase: str = Field(..., min_length=16, max_length=256)


class LoginBody(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    identifier: str  # email or username
    passphrase: str = Field(..., min_length=1, max_length=256)


class OAuthGoogleBody(BaseModel):
    """Body for /oauth/google-session — accepts an Emergent session_id."""
    session_id: str


class OAuthGithubCodeBody(BaseModel):
    """Body for /oauth/github/callback — accepts a GitHub authorization code."""
    code: str
    state: Optional[str] = None


# ---- Auth dependencies ---------------------------------------------------
async def _get_user_by_token(token: str) -> Optional[dict]:
    try:
        payload = pyjwt.decode(token, _jwt_secret(), algorithms=[_JWT_ALG])
    except pyjwt.PyJWTError:
        return None
    if payload.get("type") != "access":
        return None
    from db import users_col
    user = await users_col.find_one({"_id": payload["sub"]})
    if not user:
        return None
    user.pop("password_hash", None)
    user["id"] = user.pop("_id")
    return user


def _extract_token(request: Request) -> Optional[str]:
    tok = request.cookies.get("access_token")
    if tok:
        return tok
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return None


async def get_current_user(request: Request) -> dict:
    """Require an authenticated user. Raises 401 if not."""
    tok = _extract_token(request)
    if not tok:
        raise HTTPException(401, "Not authenticated")
    user = await _get_user_by_token(tok)
    if not user:
        raise HTTPException(401, "Invalid or expired token")
    return user


async def get_current_user_or_demo(request: Request) -> dict:
    """Return current user OR a synthetic 'demo' user (user_id='local').

    Lets legacy endpoints keep working without auth while we migrate.
    """
    tok = _extract_token(request)
    if tok:
        user = await _get_user_by_token(tok)
        if user:
            return user
    return {
        "id": "local",
        "username": "demo",
        "email": "demo@local",
        "role": "demo",
        "auth_methods": [],
    }


# ---- Brute force ---------------------------------------------------------
async def _record_attempt(identifier: str, ok: bool) -> None:
    from db import login_attempts_col
    if ok:
        await login_attempts_col.delete_many({"identifier": identifier})
        return
    await login_attempts_col.insert_one(
        {"identifier": identifier, "ts_ms": _now_ms()}
    )


async def _is_locked(identifier: str) -> bool:
    from db import login_attempts_col
    cutoff = _now_ms() - _LOCK_MIN * 60 * 1000
    n = await login_attempts_col.count_documents(
        {"identifier": identifier, "ts_ms": {"$gte": cutoff}}
    )
    return n >= _MAX_FAILS


# ---- Endpoints ----------------------------------------------------------
@router.post("/register")
async def register(body: RegisterBody, response: Response):
    from db import users_col
    username = body.username.lower()
    if not _USERNAME_RE.match(username):
        raise HTTPException(400, "username must be 3–32 chars, [a-z0-9_-]")
    email = body.email.lower()
    if await users_col.find_one({"$or": [{"email": email}, {"username": username}]}):
        raise HTTPException(409, "username or email already in use")
    user = {
        "_id": str(uuid.uuid4()),
        "username": username,
        "email": email,
        "password_hash": _hash_password(body.passphrase),
        "auth_methods": ["password"],
        "oauth_subjects": {},
        "role": "user",
        "created_at_ms": _now_ms(),
        "last_login_at_ms": _now_ms(),
    }
    await users_col.insert_one(user)
    access, refresh = _make_tokens(user["_id"], email)
    _set_cookies(response, access, refresh)
    return {"user": _public(user), "access_token": access}


@router.post("/login")
async def login(body: LoginBody, response: Response, request: Request):
    from db import users_col
    ident = body.identifier.strip().lower()
    # Lockout key: by identifier (username/email). Client-host alone is the K8s
    # ingress proxy IP that rotates between requests on the same flow.
    lock_id = f"ident:{ident}"
    if await _is_locked(lock_id):
        raise HTTPException(429, f"too many attempts — try again in {_LOCK_MIN} minutes")
    user = await users_col.find_one({"$or": [{"email": ident}, {"username": ident}]})
    if not user or not user.get("password_hash"):
        await _record_attempt(lock_id, False)
        raise HTTPException(401, "invalid credentials")
    if not _verify_password(body.passphrase, user["password_hash"]):
        await _record_attempt(lock_id, False)
        raise HTTPException(401, "invalid credentials")
    await _record_attempt(lock_id, True)
    await users_col.update_one({"_id": user["_id"]}, {"$set": {"last_login_at_ms": _now_ms()}})
    access, refresh = _make_tokens(user["_id"], user["email"])
    _set_cookies(response, access, refresh)
    return {"user": _public(user), "access_token": access}


@router.post("/logout")
async def logout(response: Response):
    _clear_cookies(response)
    return {"ok": True}


@router.get("/me")
async def me(user=Depends(get_current_user)):
    return {"user": user}


@router.post("/refresh")
async def refresh_token(request: Request, response: Response):
    from db import users_col
    tok = request.cookies.get("refresh_token")
    if not tok:
        raise HTTPException(401, "missing refresh token")
    try:
        payload = pyjwt.decode(tok, _jwt_secret(), algorithms=[_JWT_ALG])
    except pyjwt.PyJWTError:
        raise HTTPException(401, "invalid refresh token")
    if payload.get("type") != "refresh":
        raise HTTPException(401, "wrong token type")
    user = await users_col.find_one({"_id": payload["sub"]})
    if not user:
        raise HTTPException(401, "user not found")
    access, refresh = _make_tokens(user["_id"], user["email"])
    _set_cookies(response, access, refresh)
    return {"ok": True}


# ---- OAuth: Emergent Google ---------------------------------------------
@router.post("/oauth/google-session")
async def oauth_google(body: OAuthGoogleBody, response: Response):
    """Exchange an Emergent session_id (issued by the Emergent Google auth flow)
    for a server-side JWT cookie. The Emergent auth widget posts the session_id
    to this endpoint after a successful Google sign-in.

    Resolves to a user record by email; creates one if it doesn't exist.
    """
    import httpx
    async with httpx.AsyncClient(timeout=10) as cli:
        try:
            r = await cli.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers={"X-Session-ID": body.session_id},
            )
            r.raise_for_status()
            sess = r.json()
        except Exception as e:
            raise HTTPException(400, f"emergent session lookup failed: {e}")
    email = (sess.get("email") or "").lower()
    if not email:
        raise HTTPException(400, "emergent session did not return an email")
    user = await _link_oauth_user(
        provider="google",
        subject=str(sess.get("id") or email),
        email=email,
        name=sess.get("name"),
        picture=sess.get("picture"),
    )
    access, refresh = _make_tokens(user["_id"], user["email"])
    _set_cookies(response, access, refresh)
    return {"user": _public(user), "access_token": access}


# ---- OAuth: GitHub ------------------------------------------------------
@router.get("/oauth/github/start")
async def oauth_github_start(request: Request):
    cid = os.environ.get("GITHUB_CLIENT_ID")
    if not cid:
        raise HTTPException(503, "GITHUB_CLIENT_ID not configured")
    origin = request.headers.get("origin") or os.environ.get("FRONTEND_URL", "")
    redirect = f"{origin}/login?github_callback=1"
    url = (
        "https://github.com/login/oauth/authorize"
        f"?client_id={cid}&scope=read:user%20user:email&redirect_uri={redirect}"
    )
    return {"url": url}


@router.post("/oauth/github/callback")
async def oauth_github_callback(body: OAuthGithubCodeBody, response: Response):
    import httpx
    cid = os.environ.get("GITHUB_CLIENT_ID")
    cs = os.environ.get("GITHUB_CLIENT_SECRET")
    if not cid or not cs:
        raise HTTPException(503, "GitHub OAuth not configured")
    async with httpx.AsyncClient(timeout=10) as cli:
        tok_resp = await cli.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={"client_id": cid, "client_secret": cs, "code": body.code},
        )
        tok_resp.raise_for_status()
        tok = tok_resp.json().get("access_token")
        if not tok:
            raise HTTPException(400, "github token exchange failed")
        u_resp = await cli.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {tok}", "Accept": "application/json"},
        )
        u_resp.raise_for_status()
        gh = u_resp.json()
        # email may be private — pull from /user/emails
        email = gh.get("email")
        if not email:
            e_resp = await cli.get(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"Bearer {tok}", "Accept": "application/json"},
            )
            if e_resp.status_code == 200:
                primaries = [e["email"] for e in e_resp.json() if e.get("primary") and e.get("verified")]
                email = primaries[0] if primaries else None
        if not email:
            raise HTTPException(400, "no verified email on github account")
    user = await _link_oauth_user(
        provider="github",
        subject=str(gh.get("id")),
        email=str(email).lower(),
        name=gh.get("name") or gh.get("login"),
        picture=gh.get("avatar_url"),
    )
    access, refresh = _make_tokens(user["_id"], user["email"])
    _set_cookies(response, access, refresh)
    return {"user": _public(user), "access_token": access}


# ---- helpers -------------------------------------------------------------
async def _link_oauth_user(*, provider: str, subject: str, email: str,
                            name: Optional[str], picture: Optional[str]) -> dict:
    from db import users_col
    existing = await users_col.find_one({"email": email})
    if existing:
        update = {
            "$addToSet": {"auth_methods": provider},
            "$set": {
                f"oauth_subjects.{provider}": subject,
                "last_login_at_ms": _now_ms(),
                "name": existing.get("name") or name,
                "picture": existing.get("picture") or picture,
            },
        }
        await users_col.update_one({"_id": existing["_id"]}, update)
        return await users_col.find_one({"_id": existing["_id"]})

    # New user — derive a username from email local-part.
    base = re.sub(r"[^a-z0-9_-]", "-", email.split("@", 1)[0].lower())[:24] or "user"
    candidate = base
    i = 0
    while await users_col.find_one({"username": candidate}):
        i += 1
        candidate = f"{base}-{i}"[:32]
    user = {
        "_id": str(uuid.uuid4()),
        "username": candidate,
        "email": email,
        "password_hash": None,
        "auth_methods": [provider],
        "oauth_subjects": {provider: subject},
        "name": name, "picture": picture,
        "role": "user",
        "created_at_ms": _now_ms(),
        "last_login_at_ms": _now_ms(),
    }
    await users_col.insert_one(user)
    return user


def _public(user: dict) -> dict:
    return {
        "id": user["_id"],
        "username": user.get("username"),
        "email": user.get("email"),
        "role": user.get("role", "user"),
        "auth_methods": user.get("auth_methods", []),
        "name": user.get("name"),
        "picture": user.get("picture"),
    }


# ---- seed admin (idempotent) --------------------------------------------
async def seed_admin() -> Optional[dict]:
    from db import users_col
    email = os.environ.get("ADMIN_EMAIL")
    username = (os.environ.get("ADMIN_USERNAME") or "admin").lower()
    pw = os.environ.get("ADMIN_PASSWORD")
    if not email or not pw:
        return None
    existing = await users_col.find_one({"email": email.lower()})
    if existing:
        if existing.get("password_hash") and not _verify_password(pw, existing["password_hash"]):
            await users_col.update_one(
                {"_id": existing["_id"]},
                {"$set": {"password_hash": _hash_password(pw),
                          "role": "admin",
                          "username": existing.get("username") or username}},
            )
        elif existing.get("role") != "admin":
            await users_col.update_one(
                {"_id": existing["_id"]}, {"$set": {"role": "admin"}}
            )
        return existing
    user = {
        "_id": str(uuid.uuid4()),
        "username": username, "email": email.lower(),
        "password_hash": _hash_password(pw),
        "auth_methods": ["password"],
        "oauth_subjects": {},
        "role": "admin",
        "created_at_ms": _now_ms(),
        "last_login_at_ms": _now_ms(),
    }
    await users_col.insert_one(user)
    return user


def init_auth(app) -> None:
    """Attach the auth router to the FastAPI app."""
    app.include_router(router)


__all__ = [
    "router", "init_auth", "seed_admin",
    "get_current_user", "get_current_user_or_demo",
]
# ratios: loc_comments=358:79 imports_exports=21:17 calls_definitions=147:29
