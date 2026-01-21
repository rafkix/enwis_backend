from app.core.jwt_handler import create_access_token, decode_access_token

def create_user_token(user):
    return create_access_token({"sub": user.username})

def decode_token(token: str):
    return decode_access_token(token)
