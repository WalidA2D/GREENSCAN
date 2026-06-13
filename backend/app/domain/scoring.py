"""Scores synthétiques : Green Score, Waste Score, Anomaly Score (0-100).

Heuristiques transparentes et explicables (le détail ML d'anomalie vient en
complément via app/ml/anomaly.py). Toutes les valeurs sont bornées 0..100.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models
from app.domain.catalog import DPE_HEATING_FACTOR
from app.services.analytics import home_level_filter


def _clip(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return float(max(lo, min(hi, x)))


def night_share(db: Session, home_id: int, days: int = 30) -> float:
    """Part de la consommation réalisée la nuit (0h-6h) — proxy de gaspillage."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    total = db.query(func.coalesce(func.sum(models.ConsumptionRecord.energy_consumption_kwh), 0.0)).filter(
        home_level_filter(home_id), models.ConsumptionRecord.timestamp >= since).scalar() or 0.0
    night = db.query(func.coalesce(func.sum(models.ConsumptionRecord.energy_consumption_kwh), 0.0)).filter(
        home_level_filter(home_id), models.ConsumptionRecord.timestamp >= since,
        func.extract("hour", models.ConsumptionRecord.timestamp) < 6).scalar() or 0.0
    return float(night) / float(total) if total else 0.0


def compute_scores(db: Session, home: models.Home, totals: dict, anomaly_rate: float | None = None) -> dict:
    """Calcule green/waste/anomaly score à partir des totaux 30 j et du logement.

    `totals` : sortie de analytics.period_totals (kwh, heating_kwh, solar_kwh...).
    `anomaly_rate` : taux d'anomalies détecté par l'IA (0..1), optionnel.
    """
    kwh = totals["kwh"] or 1.0
    days = 30.0
    intensity = kwh / days / max(home.surface_m2, 1.0)  # kWh/m²/jour
    autonomy = (totals["solar_kwh"] / kwh) if kwh else 0.0
    heating_pct = (totals["heating_kwh"] / kwh) if kwh else 0.0
    nshare = night_share(db, home.id)
    dpe_pen = (DPE_HEATING_FACTOR.get(home.dpe, 1.0) - 0.45) * 18  # 0 (A) .. ~32 (G)

    # --- Green Score : 100 = très performant ---
    green = 100.0
    green -= _clip((intensity - 0.12) * 250, 0, 45)   # pénalité intensité
    green -= dpe_pen                                   # pénalité isolation
    green -= _clip(nshare * 60, 0, 18)                 # conso nocturne
    green += _clip(autonomy * 40, 0, 20)               # bonus autoproduction
    green = _clip(green)

    # --- Waste Score : 100 = beaucoup de gaspillage ---
    waste = 0.0
    waste += _clip((intensity - 0.12) * 200, 0, 40)
    waste += _clip((nshare - 0.18) * 180, 0, 30)
    waste += _clip((heating_pct - 0.35) * 80, 0, 20)
    if anomaly_rate is not None:
        waste += _clip(anomaly_rate * 100, 0, 25)
    waste = _clip(waste)

    # --- Anomaly Score : proportion d'anomalies récentes ---
    if anomaly_rate is None:
        anomaly = _clip(nshare * 120 + (intensity - 0.12) * 100)
    else:
        anomaly = _clip(anomaly_rate * 100)

    return {
        "green_score": round(green, 1),
        "waste_score": round(waste, 1),
        "anomaly_score": round(anomaly, 1),
        "night_share": round(nshare, 3),
        "intensity_kwh_m2_day": round(intensity, 4),
        "autonomy_pct": round(autonomy * 100, 1),
        "heating_pct": round(heating_pct * 100, 1),
    }
