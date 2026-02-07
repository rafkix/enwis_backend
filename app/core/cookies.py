from fastapi import Response
from app.core.config import COOKIE_DOMAIN

def set_auth_cookies(response: Response, access: str, refresh: str):
    response.set_cookie(
        key="access_token",
        value=access,
        domain=COOKIE_DOMAIN,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=60 * 15,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh,
        domain=COOKIE_DOMAIN,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=60 * 60 * 24 * 30,
    )


def clear_auth_cookies(response: Response):
    response.delete_cookie("access_token", domain=COOKIE_DOMAIN)
    response.delete_cookie("refresh_token", domain=COOKIE_DOMAIN)
