from pydantic import BaseModel
from typing import List
from datetime import date


class WeeklyActivityItem(BaseModel):
    date: date
    minutes: int


class DashboardOverview(BaseModel):
    streak_days: int
    total_minutes: int
    average_score: float
    weekly_minutes: int
    weekly_activity: List[WeeklyActivityItem]
