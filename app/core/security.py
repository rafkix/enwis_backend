import jwt
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from passlib.context import CryptContext
from app.core.config import (
    SECRET_KEY, ALGORITHM, AUDIENCE,
    ACCESS_TOKEN_MINUTES, REFRESH_TOKEN_DAYS
)

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)

# =====================
# PASSWORD
# =====================
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

# =====================
# JWT
# =====================
def create_access_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "type": "access",
        "aud": AUDIENCE,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc)
        + timedelta(minutes=ACCESS_TOKEN_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "aud": AUDIENCE,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc)
        + timedelta(days=REFRESH_TOKEN_DAYS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str, token_type: str) -> int:
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            audience=AUDIENCE,
        )

        if payload.get("type") != token_type:
            raise HTTPException(401, "Token turi noto‘g‘ri")

        return int(payload["sub"])

    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token muddati tugagan")
    except Exception:
        raise HTTPException(401, "Token yaroqsiz")
