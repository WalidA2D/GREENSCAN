"""Détection d'anomalies de consommation (IsolationForest)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import joblib
import numpy as np
from sqlalchemy.orm import Session

from app import models
from app.ml.train import anomaly_path
from app.services.analytics import home_level_filter


def _load(home_id: int):
    path = anomaly_path(home_id)
    if not path.exists():
        return None
    try:
        return joblib.load(path)
    except Exception:
        return None


def anomaly_rate_for_home(db: Session, home_id: int, days: int = 30) -> float | None:
    """Proportion de pas 30 min anormaux sur la période récente (0..1)."""
    iso = _load(home_id)
    since = datetime.now(timezone.utc) - timedelta(days=days)
    rows = db.query(
        models.ConsumptionRecord.timestamp,
        models.ConsumptionRecord.energy_consumption_kwh,
    ).filter(home_level_filter(home_id),
             models.ConsumptionRecord.timestamp >= since).all()
    if not rows:
        return None
    X = np.array([[ts.hour, float(kwh)] for ts, kwh in rows])
    if iso is None:
        # Fallback : z-score sur la consommation.
        vals = X[:, 1]
        mean, std = vals.mean(), vals.std() or 1.0
        return float((np.abs(vals - mean) / std > 3).mean())
    preds = iso.predict(X)
    return float((preds == -1).mean())


def detect_anomalies(db: Session, home_id: int, days: int = 30, limit: int = 50) -> list[dict]:
    """Liste des points anormaux récents (timestamp, conso, raison)."""
    iso = _load(home_id)
    since = datetime.now(timezone.utc) - timedelta(days=days)
    rows = db.query(
        models.ConsumptionRecord.timestamp,
        models.ConsumptionRecord.energy_consumption_kwh,
    ).filter(home_level_filter(home_id),
             models.ConsumptionRecord.timestamp >= since).order_by(
        models.ConsumptionRecord.timestamp).all()
    if not rows:
        return []

    X = np.array([[ts.hour, float(kwh)] for ts, kwh in rows])
    vals = X[:, 1]
    mean, std = vals.mean(), vals.std() or 1.0

    if iso is not None:
        flags = iso.predict(X) == -1
    else:
        flags = np.abs(vals - mean) / std > 3

    anomalies = []
    for (ts, kwh), is_anom in zip(rows, flags):
        if not is_anom:
            continue
        z = (float(kwh) - mean) / std
        reason = "Consommation nocturne élevée" if ts.hour < 6 else "Pic de consommation"
        anomalies.append({
            "timestamp": ts.isoformat(),
            "consumption_kwh": round(float(kwh), 3),
            "z_score": round(float(z), 2),
            "hour": ts.hour,
            "reason": reason,
        })
    # Les plus marquants d'abord.
    anomalies.sort(key=lambda a: abs(a["z_score"]), reverse=True)
    return anomalies[:limit]
