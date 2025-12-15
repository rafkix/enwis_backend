from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware
import os

from app.database import init_db
from app.routers import (
    auth_router,
    reading_router,
    users_router,
    lessons_router,
    courses_router,
    course_category,
    words_router,
    daily_vocab,
    telegram_webapp,
)

# ------------------------------------------------------------------
# App init
# ------------------------------------------------------------------

app = FastAPI(
    title="Enwis Backend API",
    version="1.0.0",
    description="Enwis — AI-powered language learning platform",
    redoc_url=None,
    docs_url="/my/api/docs",
)

# ------------------------------------------------------------------
# CORS CONFIG (PRODUCTION SAFE)
# ------------------------------------------------------------------

ALLOWED_ORIGINS = [
    # Local
    "http://localhost:3000",
    "http://127.0.0.1:3000",

    # Production
    "https://enwis.uz",
    "https://www.enwis.uz",
    "https://api.enwis.uz",
    "https://app.enwis.uz",

    # Vercel previews
    "https://enwis-dashboard.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "X-Requested-With",
    ],
)

# ------------------------------------------------------------------
# SESSION MIDDLEWARE (COOKIE AUTH)
# ------------------------------------------------------------------

SESSION_SECRET = os.getenv("SESSION_SECRET", "CHANGE_ME")

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    same_site="none",  # required for cross-domain cookies
    https_only=True,   # production only
)

# ------------------------------------------------------------------
# ROUTERS
# ------------------------------------------------------------------

API_PREFIX = "/v1/api"

app.include_router(auth_router.router, prefix=API_PREFIX)
app.include_router(users_router.router, prefix=API_PREFIX)
app.include_router(reading_router.router, prefix=API_PREFIX)
app.include_router(lessons_router.router, prefix=API_PREFIX)
app.include_router(courses_router.router, prefix=API_PREFIX)
app.include_router(course_category.router, prefix=API_PREFIX)
app.include_router(words_router.router, prefix=API_PREFIX)
app.include_router(daily_vocab.router, prefix=API_PREFIX)
app.include_router(telegram_webapp.router, prefix=API_PREFIX)

# ------------------------------------------------------------------
# STARTUP
# ------------------------------------------------------------------

@app.on_event("startup")
async def startup_event():
    await init_db()
    print("✅ Database initialized")

# ------------------------------------------------------------------
# ERROR HANDLERS
# ------------------------------------------------------------------

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "status": exc.status_code,
                "message": exc.detail,
                "path": str(request.url),
            }
        },
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request, exc: Exception
):
    print(f"❌ Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "status": 500,
                "message": "Internal Server Error",
                "path": str(request.url),
            }
        },
    )

# ------------------------------------------------------------------
# HEALTH & ROOT
# ------------------------------------------------------------------

@app.get("/", tags=["System"])
async def root():
    return {
        "status": "running",
        "service": "Enwis Backend API",
        "docs": "/docs",
        "health": "/health",
    }

@app.get("/health", tags=["System"])
async def health():
    return {
        "status": "ok",
        "database": "connected",
    }

# ------------------------------------------------------------------
# LOCAL DEV ONLY
# ------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
