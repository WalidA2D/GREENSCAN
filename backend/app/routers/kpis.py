"""Routes /api/kpis — KPI énergétiques, financiers, écologiques, IA."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import KpiOut
from app.domain.kpi_engine import compute_kpis
from app.ml.anomaly import anomaly_rate_for_home
from app.routers.deps import resolve_home_id

router = APIRouter(prefix="/api/kpis", tags=["kpis"])


@router.get("", response_model=list[KpiOut])
def get_kpis(home_id: int = Depends(resolve_home_id), db: Session = Depends(get_db)):
    """Calcule les KPI à la volée (frais) à partir des données du logement."""
    rate = anomaly_rate_for_home(db, home_id)
    return compute_kpis(db, home_id, anomaly_rate=rate)
