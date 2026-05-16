from datetime import datetime, timedelta, timezone
from uuid import UUID

import bcrypt
from jose import jwt

from app.core.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_access_token(user_id: UUID) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.access_token_expire_days)
    payload = {"sub": str(user_id), "exp": expires_at}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
