# auth.py
import os
import secrets
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field
from passlib.context import CryptContext
from sqlalchemy.orm import Session as DBSession

from .db import get_db
from .models import User, Session
from .res_models import RegisterIn, LoginIn

# ---- Cookie/session settings ----
SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "session_id")
SESSION_TTL_HOURS = int(os.getenv("SESSION_TTL_HOURS", "24"))

COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"  # True on HTTPS
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "lax")  # lax/strict/none

COOKIE_KWARGS = {
    "httponly": True,
    "secure": COOKIE_SECURE,
    "samesite": COOKIE_SAMESITE,
    "path": "/",
}

# ---- Password hashing ----
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)




# ---- Session helpers ----
def _new_session_id() -> str:
    # 64-char stable length, friendly for DB columns.
    return secrets.token_hex(32)


def _session_expiry() -> datetime:
    return datetime.utcnow() + timedelta(hours=SESSION_TTL_HOURS)


def cleanup_expired_sessions(db: DBSession) -> None:
    db.query(Session).filter(Session.expires_at <= datetime.utcnow()).delete()
    db.commit()


def create_session(db: DBSession, user_id: str) -> str:
    cleanup_expired_sessions(db)
    sid = _new_session_id()
    db.add(Session(id=sid, user_id=user_id, expires_at=_session_expiry()))
    db.commit()
    return sid


def delete_session(db: DBSession, sid: str) -> None:
    db.query(Session).filter(Session.id == sid).delete()
    db.commit()


def set_session_cookie(response: Response, sid: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=sid,
        max_age=SESSION_TTL_HOURS * 60 * 60,
        **COOKIE_KWARGS,
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")


# ---- Dependencies ----
def get_current_user(request: Request, db: DBSession = Depends(get_db)) -> User:
    sid = request.cookies.get(SESSION_COOKIE_NAME)
    if not sid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    sess = (
        db.query(Session)
        .filter(Session.id == sid, Session.expires_at > datetime.utcnow())
        .first()
    )
    if not sess:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")

    user = db.query(User).filter(User.id == sess.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user