from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.users.models import User
from app.modules.stats.repository import StatsRepository
from app.modules.stats.service import StatsService
from app.modules.stats.schemas import DashboardOverview

router = APIRouter(prefix="/stats", tags=["Stats"])


@router.get("/dashboard", response_model=DashboardOverview)
async def student_dashboard_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = StatsRepository(db)
    service = StatsService(repo)
    return await service.get_dashboard_overview(user.id) # type: ignore
