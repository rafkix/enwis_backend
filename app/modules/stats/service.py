from datetime import date, timedelta
from app.modules.stats.repository import StatsRepository
from app.modules.stats.schemas import WeeklyActivityItem, DashboardOverview


class StatsService:

    def __init__(self, repo: StatsRepository):
        self.repo = repo

    async def calculate_streak(self, user_id: int) -> int:
        days = await self.repo.get_practice_days(user_id)
        if not days:
            return 0

        streak = 0
        current_day = date.today()

        for d in days:
            if d == current_day:
                streak += 1
                current_day -= timedelta(days=1)
            elif d == current_day - timedelta(days=1):
                streak += 1
                current_day = d - timedelta(days=1)
            else:
                break

        return streak

    async def get_dashboard_overview(self, user_id: int) -> DashboardOverview:
        total_seconds = await self.repo.get_total_seconds(user_id)
        avg_score = await self.repo.get_average_score(user_id)
        streak = await self.calculate_streak(user_id)

        weekly_raw = await self.repo.get_weekly_activity(user_id)

        weekly_activity = [
            WeeklyActivityItem(
                date=row[0],
                minutes=int(row[1] // 60)
            )
            for row in weekly_raw
        ]

        weekly_minutes = sum(item.minutes for item in weekly_activity)

        return DashboardOverview(
            streak_days=streak,
            total_minutes=total_seconds // 60,
            average_score=avg_score,
            weekly_minutes=weekly_minutes,
            weekly_activity=weekly_activity
        )
