"""Routes /api/anomalies — détection d'anomalies (IsolationForest)."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.ml.anomaly import detect_anomalies, anomaly_rate_for_home
from app.routers.deps import resolve_home_id

router = APIRouter(prefix="/api/anomalies", tags=["anomalies"])


@router.get("")
def get_anomalies(home_id: int = Depends(resolve_home_id),
                  days: int = Query(30, ge=1, le=180),
                  db: Session = Depends(get_db)):
    """Points de consommation anormaux + taux global d'anomalies."""
    return {
        "home_id": home_id,
        "anomaly_rate": anomaly_rate_for_home(db, home_id, days=days),
        "anomalies": detect_anomalies(db, home_id, days=days),
    }
