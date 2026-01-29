from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from core.settings import settings as stng

password_hash = PasswordHash.recommended()


def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password):
    return password_hash.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, stng.JWT_SECRET_KEY, algorithm=stng.JWT_ALGORITHM)


def decode_token(token: str):
    return jwt.decode(token, stng.JWT_SECRET_KEY, algorithms=[stng.JWT_ALGORITHM])
