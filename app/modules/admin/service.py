from app.core.hashing import password_hash

class AdminUserService:
    def __init__(self, db):
        self.db = db

    async def reset_password(self, target_user, new_password: str):
        target_user.password = password_hash(new_password)

    async def change_role(self, target_user, role: str):
        target_user.role = role

    async def block_user(self, target_user):
        target_user.is_active = False

    async def unblock_user(self, target_user):
        target_user.is_active = True

    async def delete_user(self, target_user):
        await self.db.delete(target_user)

