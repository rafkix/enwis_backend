import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.database import init_db
from app.modules.auth.router import router as auth_router
from app.modules.users.router import router as user_router
from app.modules.admin.router import router as admin_router
from app.modules.education.daily_vocab.router import router as daily_router
from app.modules.education.course import category, router
from app.modules.education.lesson.router import router as lesson_router
from app.modules.education.words.router import router as words_router
from app.modules.education.tasks.router import router as tasks_router
from app.modules.payment.router import router as payment_router
from app.modules.stats.router import router as stats_router
from app.modules.services.video_shadowing.router import router as video_router
from app.modules.services.audio_writing.router import router as audio_router
from app.modules.services.cefr.reading.router import router as cefr_reading_router
from app.modules.services.cefr.listening.router import router as cefr_listening_router

app = FastAPI(
    title="Enwis Backend API",
    version="1.0.0",
    description=(
        "Enwis is an educational platform created for learning foreign languages using AI. \n"
        "This API manages users, courses, exercises, AI translation, and gamification systems."
    ),
)


origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://enwis.uz",
    "https://app.enwis.uz",
    "https://api.enwis.uz",
    "https://cefr.enwis.uz",
    "https://ielts.enwis.uz"
]

if not os.path.exists("static"):
    os.makedirs("static")

app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key="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"  # o‘zgartir!
)


app.include_router(auth_router, prefix="/v1/api")
app.include_router(user_router, prefix="/v1/api")
app.include_router(admin_router, prefix="/v1/api")
app.include_router(daily_router, prefix="/v1/api")
app.include_router(category.router,prefix="/v1/api")
app.include_router(router.router, prefix="/v1/api")
app.include_router(lesson_router, prefix="/v1/api")
app.include_router(words_router, prefix="/v1/api")
app.include_router(tasks_router, prefix="/v1/api")
app.include_router(payment_router, prefix="/v1/api")
app.include_router(video_router, prefix="/v1/api")
app.include_router(audio_router, prefix="/v1/api")
app.include_router(stats_router, prefix="/v1/api")
app.include_router(cefr_reading_router, prefix="/v1/api")
app.include_router(cefr_listening_router, prefix="/v1/api")

# app.include_router(payments_router.router)
# app.include_router(ai_router.router)


@app.on_event("startup")
async def on_startup():
    await init_db()
    print("✅ Database initialized successfully.")


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "status_code": exc.status_code,
                "detail": exc.detail,
                "path": str(request.url),
            }
        },
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"❌ Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "status_code": 500,
                "detail": "Internal Server Error",
                "path": str(request.url),
            }
        },
    )



@app.get("/", tags=["System"])
async def root():
    return {
        "message": "🚀 Enwis Backend API is running!",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "ok", "database": "connected"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
