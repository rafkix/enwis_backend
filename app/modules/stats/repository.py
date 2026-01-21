from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from datetime import datetime, timedelta
from app.modules.stats.models import PracticeAttempt


class StatsRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_total_seconds(self, user_id: int) -> int:
        result = await self.db.execute(
            select(func.coalesce(func.sum(PracticeAttempt.duration_seconds), 0))
            .where(PracticeAttempt.user_id == user_id)
        )
        return result.scalar_one()

    async def get_average_score(self, user_id: int) -> float:
        result = await self.db.execute(
            select(func.avg(PracticeAttempt.overall_score))
            .where(PracticeAttempt.user_id == user_id)
        )
        return round(result.scalar() or 0.0, 1)

    async def get_practice_days(self, user_id: int):
        result = await self.db.execute(
            select(func.date(PracticeAttempt.created_at))
            .where(PracticeAttempt.user_id == user_id)
            .distinct()
            .order_by(func.date(PracticeAttempt.created_at).desc())
        )
        return [row[0] for row in result.all()]

    async def get_weekly_activity(self, user_id: int):
        since = datetime.utcnow() - timedelta(days=6)

        result = await self.db.execute(
            select(
                func.date(PracticeAttempt.created_at),
                func.sum(PracticeAttempt.duration_seconds)
            )
            .where(
                PracticeAttempt.user_id == user_id,
                PracticeAttempt.created_at >= since
            )
            .group_by(func.date(PracticeAttempt.created_at))
            .order_by(func.date(PracticeAttempt.created_at))
        )
        return result.all()
