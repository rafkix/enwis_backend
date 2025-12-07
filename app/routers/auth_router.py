from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models.user_model import User
from app.schemas.auth_schema import UserCreate, UserResponse
from app.utils.hashing import password_hash, verify_password
from app.utils.jwt_handler import create_access_token, decode_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@router.post("/register", response_model=dict)
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # username tekshirish
    existing = await db.execute(select(User).where(User.username == user.username))
    if existing.scalars().first():
        raise HTTPException(400, "Username already exists")

    hashed_pw = password_hash(user.password)

    new_user = User(
        full_name=user.full_name,
        username=user.username,
        email=user.email,
        phone=user.phone,
        age=user.age,
        password=hashed_pw,
        level=user.level or "beginner",
        bio=user.bio or "",
        profile_image="default.png",
        role=user.role or "student",
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    token = create_access_token({"user_id": new_user.id})

    return {
        "message": "User registered successfully",
        "access_token": token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(new_user)
    }


# --------------------------
# LOGIN
# --------------------------
@router.post("/login")
async def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalars().first()

    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    username = decode_access_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user
        

@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user