"""Security utilities: password hashing, JWT."""
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str | int, expires_minutes: int | None = None, **extra: Any) -> str:
    expires_minutes = expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    expire = datetime.now(tz=timezone.utc) + timedelta(minutes=expires_minutes)
    payload = {"sub": str(subject), "exp": expire, "iat": datetime.now(tz=timezone.utc), **extra}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None
