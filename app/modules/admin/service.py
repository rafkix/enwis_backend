from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.modules.users.models import User

ALLOWED_ROLES = {"student", "teacher", "mentor", "admin"}


class AdminUserService:
    def __init__(self, db: AsyncSession, current_admin: User):
        self.db = db
        self.current_admin = current_admin

    # --------------------------------------------------
    # RESET PASSWORD
    # --------------------------------------------------
    async def reset_password(
        self,
        target_user: User,
        new_password: str
    ) -> User:
        if len(new_password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password kamida 6 ta belgidan iborat bo‘lishi kerak"
            )

        target_user.password = hash_password(new_password)
        await self.db.commit()
        await self.db.refresh(target_user)
        return target_user

    # --------------------------------------------------
    # CHANGE ROLE
    # --------------------------------------------------
    async def change_role(
        self,
        target_user: User,
        role: str
    ) -> User:
        if role not in ALLOWED_ROLES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Noto‘g‘ri role"
            )

        # admin o‘z rolini o‘zgartira olmaydi
        if target_user.id == self.current_admin.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="O‘zingizning rolingizni o‘zgartira olmaysiz"
            )

        target_user.role = role
        await self.db.commit()
        await self.db.refresh(target_user)
        return target_user

    # --------------------------------------------------
    # BLOCK USER
    # --------------------------------------------------
    async def block_user(self, target_user: User) -> User:
        if target_user.id == self.current_admin.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="O‘zingizni bloklay olmaysiz"
            )

        if target_user.role == "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin foydalanuvchini bloklab bo‘lmaydi"
            )

        target_user.is_active = False
        await self.db.commit()
        await self.db.refresh(target_user)
        return target_user

    # --------------------------------------------------
    # UNBLOCK USER
    # --------------------------------------------------
    async def unblock_user(self, target_user: User) -> User:
        target_user.is_active = True
        await self.db.commit()
        await self.db.refresh(target_user)
        return target_user

    # --------------------------------------------------
    # DELETE USER
    # --------------------------------------------------
    async def delete_user(self, target_user: User):
        if target_user.id == self.current_admin.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="O‘zingizni o‘chira olmaysiz"
            )

        if target_user.role == "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin foydalanuvchini o‘chirish mumkin emas"
            )

        await self.db.delete(target_user)
        await self.db.commit()
