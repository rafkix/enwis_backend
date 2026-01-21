import os
import uuid
from fastapi import UploadFile

from app.core.hashing import verify_password, password_hash
from app.modules.users.repository import UserRepository
from app.modules.users.models import User


class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def update_profile(self, user: User, data):
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        await self.repo.save(user) # type: ignore
        return user

    async def change_password(self, user: User, data):
        if not verify_password(data.old_password, user.password):
            raise ValueError("Old password incorrect")
        user.password = password_hash(data.new_password)
        await self.repo.save(user)
        return user

    async def delete_self(self, user: User):
        await self.repo.delete(user)

    async def delete_user_by_admin(self, current_user: User, target_user: User):
        if current_user.role not in ("admin", "mentor"):
            raise PermissionError("Not enough permissions")
        await self.repo.delete(target_user)

    # ✅ MUAMMONI YECHADIGAN METOD
    async def save_profile_photo(self, user: User, file: UploadFile) -> str:
        upload_dir = "static/avatars"
        os.makedirs(upload_dir, exist_ok=True)

        ext = file.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        path = os.path.join(upload_dir, filename)

        with open(path, "wb") as f:
            f.write(await file.read())

        # 🔴 MODEL NOMI BILAN MOS QIL
        user.profile_image = path   # type: ignore

        await self.repo.save(user)
        return path
