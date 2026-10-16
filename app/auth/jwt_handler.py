from datetime import datetime, timedelta, timezone

from jose import jwt

from app.config import (ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM,
                        REFRESH_TOKEN_EXPIRE_DAYS, SECRET_KEY)


def create_access_token(user_id: int, role: str) -> str:
    """Короткоживучий токен доступу: sub, role, exp, type=access."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "role": role, "exp": expire, "type": "access"}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    """Довгоживучий токен оновлення: мінімум даних (sub, exp, type=refresh)."""
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": str(user_id), "exp": expire, "type": "refresh"}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    """Перевіряє підпис та exp. Піднімає JWTError, якщо токен недійсний.
    algorithms=[...] — СПИСОК: захист від атаки alg=none / algorithm confusion."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
