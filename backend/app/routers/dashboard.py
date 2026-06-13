"""Route /api/dashboard — agrégat complet pour la page d'accueil."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.schemas import DashboardOut, HomeOut, AlertOut, RecommendationOut
from app.services.analytics import consumption_series, today_consumption, rooms_consumption
from app.domain.kpi_engine import compute_kpis
from app.ml.predictor import predict_bundle
from app.ml.anomaly import anomaly_rate_for_home
from app.routers.deps import resolve_home_id, get_home_or_404

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardOut)
def get_dashboard(home_id: int = Depends(resolve_home_id), db: Session = Depends(get_db)):
    """Tout ce qu'il faut pour afficher le tableau de bord en un seul appel."""
    home = get_home_or_404(home_id, db)
    rate = anomaly_rate_for_home(db, home_id)

    kpis = compute_kpis(db, home_id, anomaly_rate=rate)
    predictions = predict_bundle(db, home_id, horizon=7)

    top_rooms = rooms_consumption(db, home_id, days=30)[:5]
    recent_alerts = db.query(models.Alert).filter(models.Alert.home_id == home_id).order_by(
        models.Alert.detected_at.desc()).limit(5).all()
    quick_recos = db.query(models.Recommendation).filter(
        models.Recommendation.home_id == home_id).order_by(
        models.Recommendation.gain_eur_month.desc()).limit(3).all()

    return DashboardOut(
        home=HomeOut.model_validate(home),
        kpis=kpis,
        consumption_today_kwh=round(today_consumption(db, home_id), 2),
        consumption_daily=consumption_series(db, home_id, "daily", 30),
        consumption_weekly=consumption_series(db, home_id, "weekly", 84),
        consumption_monthly=consumption_series(db, home_id, "monthly", 365),
        predictions=predictions,
        top_rooms=top_rooms,
        recent_alerts=[AlertOut.model_validate(a) for a in recent_alerts],
        quick_recommendations=[RecommendationOut.model_validate(r) for r in quick_recos],
    )
