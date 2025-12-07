from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def password_hash(password: str) -> str:
    # argon2 72-byte limit fix
    safe_password = password[:72]
    return pwd_context.hash(safe_password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Kiritilgan parolni tekshiradi"""
    return pwd_context.verify(plain_password, hashed_password)

def is_hashed(password: str) -> bool:
    """Parol xeshlanganligini tekshiradi"""
    return pwd_context.identify(password) is not None