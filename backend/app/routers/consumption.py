"""Routes /api/consumption — séries de consommation agrégées."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ConsumptionSeriesOut
from app.services.analytics import consumption_series
from app.routers.deps import resolve_home_id

router = APIRouter(prefix="/api/consumption", tags=["consumption"])

# Fenêtre par défaut selon la granularité.
DEFAULT_DAYS = {"hourly": 3, "daily": 30, "weekly": 84, "monthly": 365}


@router.get("", response_model=ConsumptionSeriesOut)
def get_consumption(
    home_id: int = Depends(resolve_home_id),
    granularity: str = Query("daily", pattern="^(hourly|daily|weekly|monthly)$"),
    days: int | None = Query(default=None, ge=1, le=730),
    db: Session = Depends(get_db),
):
    window = days or DEFAULT_DAYS.get(granularity, 30)
    points = consumption_series(db, home_id, granularity, window)
    return ConsumptionSeriesOut(granularity=granularity, points=points)
