# core/auth/security.py
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt
from pwdlib import PasswordHash

from core.settings import settings as stng

password_hash = PasswordHash.recommended()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return password_hash.hash(password)


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> tuple[str, datetime]:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=stng.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    # Standard Claims (RFC 7519)
    to_encode.update(
        {"exp": expire, "iat": datetime.now(timezone.utc), "jti": str(uuid.uuid4())}
    )

    encoded_jwt = jwt.encode(
        to_encode, stng.JWT_SECRET_KEY, algorithm=stng.JWT_ALGORITHM
    )
    return encoded_jwt, expire
