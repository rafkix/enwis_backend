import jwt
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from app.core.config import SECRET_KEY, ALGORITHM

def create_access_token(data: dict, expires_minutes: int = 120):
    """Yangi access token yaratadi (Timezone-aware)"""
    to_encode = data.copy()
    # UTC vaqt zonasi bilan ishlash (Eski utcnow o'rniga)
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str):
    """Tokenni tekshiradi va sub (foydalanuvchi) ni qaytaradi"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token tarkibida foydalanuvchi ma'lumoti yo'q"
            )
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Tokenning vaqti o'tgan (Expired)"
        )
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail=f"Token yaroqsiz: {str(e)}"
        )