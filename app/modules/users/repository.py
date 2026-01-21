from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.users.models import User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save(self, user):
        self.db.add(user)
        await self.db.flush()  # 🔥 MUHIM

    async def delete(self, user: User):
        self.db.delete(user) # type: ignore
        await self.db.flush()  # 🔥 MUHIM
