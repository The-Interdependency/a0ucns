# ratios: loc_comments=113:2 imports_exports=11:7 calls_definitions=49:7
import bcrypt
import jwt
import logging
import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import HTTPException, status, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION_HOURS
from db import db

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def create_access_token(user_id: str) -> str:
    expiration = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "sub": user_id,
        "exp": expiration
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def generate_service_token() -> str:
    return f"sat_{secrets.token_urlsafe(48)}"


def hash_service_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> dict:
    """Support both Google OAuth session tokens (cookie) and JWT tokens (header)"""
    session_token = request.cookies.get("session_token")
    access_cookie_token = request.cookies.get("access_token")

    if session_token:
        session = await db.user_sessions.find_one(
            {"session_token": session_token},
            {"_id": 0}
        )
        if not session:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

        expires_at = session["expires_at"]
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at < datetime.now(timezone.utc):
            await db.user_sessions.delete_one({"session_token": session_token})
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")

        user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return user

    token = credentials.credentials if credentials else access_cookie_token
    if token:
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

            user = await db.users.find_one({"id": user_id}, {"_id": 0})
            if not user:
                user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
            if not user:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
            return user
        except jwt.ExpiredSignatureError:
            jwt_error = "Token expired"
        except jwt.InvalidTokenError:
            jwt_error = "Invalid token"
        else:
            jwt_error = None

        token_hash = hash_service_token(token)
        service_token = await db.service_account_tokens.find_one(
            {"token_hash": token_hash, "revoked": {"$ne": True}},
            {"_id": 0}
        )
        if service_token:
            expires_at = service_token.get("expires_at")
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)
            if expires_at and expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at and expires_at < datetime.now(timezone.utc):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Service token expired")

            service_account = await db.service_accounts.find_one(
                {
                    "id": service_token.get("service_account_id"),
                    "active": {"$ne": False}
                },
                {"_id": 0}
            )
            if not service_account:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Service account not found")

            owner_user_id = service_token.get("owner_user_id") or service_account.get("owner_user_id")
            user = await db.users.find_one({"id": owner_user_id}, {"_id": 0})
            if not user:
                user = await db.users.find_one({"user_id": owner_user_id}, {"_id": 0})
            if not user:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

            await db.service_account_tokens.update_one(
                {"id": service_token.get("id")},
                {"$set": {"last_used_at": datetime.now(timezone.utc).isoformat()}}
            )

            user["auth_type"] = "service_account"
            user["service_account_username"] = service_account.get("username")
            return user

        if jwt_error:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=jwt_error)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


def get_user_id(user: dict) -> str:
    """Get user ID from user dict (supports both old 'id' and new 'user_id' fields)"""
    return user.get("user_id") or user.get("id")
# ratios: loc_comments=113:2 imports_exports=11:7 calls_definitions=49:7
