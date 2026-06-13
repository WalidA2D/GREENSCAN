"""Routes /api/alerts — alertes intelligentes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.schemas import AlertOut
from app.domain.alerts_engine import detect_alerts
from app.routers.deps import resolve_home_id, get_home_or_404

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertOut])
def list_alerts(home_id: int = Depends(resolve_home_id),
                level: str | None = Query(default=None, pattern="^(info|warning|critical)$"),
                db: Session = Depends(get_db)):
    q = db.query(models.Alert).filter(models.Alert.home_id == home_id)
    if level:
        q = q.filter(models.Alert.level == level)
    return q.order_by(models.Alert.detected_at.desc()).all()


@router.post("/refresh", response_model=list[AlertOut])
def refresh_alerts(home_id: int = Depends(resolve_home_id), db: Session = Depends(get_db)):
    """Recalcule les alertes du logement à partir des données récentes."""
    home = get_home_or_404(home_id, db)
    db.query(models.Alert).filter(models.Alert.home_id == home_id).delete()
    alerts = detect_alerts(db, home)
    for a in alerts:
        db.add(a)
    db.commit()
    return db.query(models.Alert).filter(models.Alert.home_id == home_id).order_by(
        models.Alert.detected_at.desc()).all()


@router.patch("/{alert_id}/resolve", response_model=AlertOut)
def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.get(models.Alert, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alerte introuvable")
    alert.is_resolved = True
    db.commit()
    db.refresh(alert)
    return alert
