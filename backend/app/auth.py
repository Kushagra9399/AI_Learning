from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from .store import store


SECRET_KEY = os.getenv("JWT_SECRET", "")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
password_hash = PasswordHash.recommended()
DUMMY_HASH = password_hash.hash("invalid-password-placeholder")


def seed_default_users():
    defaults = [
        ("admin", os.getenv("ADMIN_PASSWORD", ""), "admin"),
        ("worker", os.getenv("WORKER_PASSWORD", ""), "worker"),
    ]
    for username, password, role in defaults:
        if password and not store.get_user_by_username(username):
            store.create_user(username, password_hash.hash(password), role)


def create_access_token(user):
    if not SECRET_KEY:
        raise RuntimeError("JWT_SECRET is not configured")
    payload = {
        "sub": str(user["id"]),
        "username": user["username"],
        "role": user["role"],
        "exp": datetime.now(timezone.utc)
        + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def authenticate(username, password):
    user = store.get_user_by_username(username)
    if not user:
        password_hash.verify(password, DUMMY_HASH)
        return None
    if not password_hash.verify(password, user["password_hash"]):
        return None
    return user


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
):
    if not SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT_SECRET is not configured",
        )

    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub", ""))
    except (InvalidTokenError, ValueError, TypeError):
        raise credentials_error

    user = store.get_user(user_id)
    if not user:
        raise credentials_error
    return user


def require_role(role):
    def dependency(current_user=Depends(get_current_user)):
        if current_user["role"] != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return dependency


AdminUser = Annotated[dict, Depends(require_role("admin"))]
WorkerUser = Annotated[dict, Depends(require_role("worker"))]
CurrentUser = Annotated[dict, Depends(get_current_user)]
