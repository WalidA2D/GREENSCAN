"""Orchestration de l'« intelligence » d'un logement.

Recalcule et persiste, pour un logement donné :
- les alertes (moteur de détection)
- les recommandations personnalisées
- le snapshot de KPI

Utilisé par le seed initial et par les endpoints de rafraîchissement.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app import models
from app.domain.alerts_engine import detect_alerts
from app.domain.recommendations_engine import compute_recommendations
from app.domain.kpi_engine import compute_kpis, persist_kpis


def _anomaly_rate(db: Session, home_id: int) -> float | None:
    """Taux d'anomalies via le modèle IsolationForest si disponible, sinon None."""
    try:
        from app.ml.anomaly import anomaly_rate_for_home
        return anomaly_rate_for_home(db, home_id)
    except Exception:
        return None


def refresh_home_intelligence(db: Session, home_id: int) -> dict:
    """Recalcule alertes / recommandations / KPI et les enregistre (sans commit)."""
    home = db.get(models.Home, home_id)
    if home is None:
        return {"alerts": 0, "recommendations": 0, "kpis": 0}

    # Purge des éléments calculés précédents (on régénère un état frais).
    db.query(models.Alert).filter(models.Alert.home_id == home_id).delete()
    db.query(models.Recommendation).filter(models.Recommendation.home_id == home_id).delete()

    alerts = detect_alerts(db, home)
    for a in alerts:
        db.add(a)

    recos = compute_recommendations(db, home)
    for r in recos:
        db.add(r)

    rate = _anomaly_rate(db, home_id)
    kpis = compute_kpis(db, home_id, anomaly_rate=rate)
    persist_kpis(db, home_id, kpis)

    db.flush()
    return {"alerts": len(alerts), "recommendations": len(recos), "kpis": len(kpis)}
