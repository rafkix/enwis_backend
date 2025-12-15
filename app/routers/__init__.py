# routers package initializer

from app.routers import auth_router
from app.routers import users_router
from app.routers import reading_router
from app.routers import courses_router
from app.routers import lessons_router
from app.routers import course_category
from app.routers import words_router
from app.routers import daily_vocab
from app.routers import telegram_webapp



__all__ = [
    "auth_router",
    "users_router",
    "reading_router",
    "courses_router",
    "lessons_router",
    "course_category",
    "words_router",
    "daily_vocab",
    "telegram_webapp",
]
