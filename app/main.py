from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
from app.database import init_db
from app.routers import auth_router, course_category, courses_router, daily_vocab, lessons_router, users_router, words_router, telegram_webapp

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
]

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


app.include_router(auth_router.router, prefix="/v1/api")
app.include_router(users_router.router, prefix="/v1/api")
app.include_router(lessons_router.router, prefix="/v1/api")
app.include_router(courses_router.router, prefix="/v1/api")
app.include_router(course_category.router, prefix="/v1/api")
app.include_router(words_router.router, prefix="/v1/api")
app.include_router(telegram_webapp.router, prefix="/v1/api")
app.include_router(daily_vocab.router, prefix="/v1/api")
# app.include_router(courses_router.router)
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