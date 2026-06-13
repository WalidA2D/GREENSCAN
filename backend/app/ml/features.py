"""Construction des features pour la prévision de consommation.

Granularité journalière. Variables (alignées sur la feuille Variables_IA) :
- calendaires : jour de semaine, week-end, mois, jour de l'année
- météo       : température moyenne / min / max du jour
- historique  : lag J-1, lag J-7, moyenne glissante 7 j
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models
from app.services.analytics import home_level_filter

FEATURE_COLUMNS = [
    "dow", "is_weekend", "month", "doy",
    "temp_avg", "temp_min", "temp_max",
    "lag1", "lag7", "roll7",
]


def _daily_consumption(db: Session, home_id: int, days: int) -> pd.DataFrame:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    day = func.date_trunc("day", models.ConsumptionRecord.timestamp)
    rows = db.query(
        day.label("day"),
        func.sum(models.ConsumptionRecord.energy_consumption_kwh).label("kwh"),
        func.sum(models.ConsumptionRecord.energy_cost_eur).label("cost"),
    ).filter(home_level_filter(home_id),
             models.ConsumptionRecord.timestamp >= since).group_by("day").order_by("day").all()
    df = pd.DataFrame(rows, columns=["day", "kwh", "cost"])
    if not df.empty:
        df["day"] = pd.to_datetime(df["day"]).dt.tz_localize(None).dt.normalize()
    return df


def _daily_weather(db: Session, home_id: int, days: int) -> pd.DataFrame:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    day = func.date_trunc("day", models.WeatherRecord.timestamp)
    rows = db.query(
        day.label("day"),
        func.avg(models.WeatherRecord.outdoor_temperature).label("temp_avg"),
        func.min(models.WeatherRecord.outdoor_temperature).label("temp_min"),
        func.max(models.WeatherRecord.outdoor_temperature).label("temp_max"),
    ).filter(models.WeatherRecord.home_id == home_id,
             models.WeatherRecord.timestamp >= since).group_by("day").order_by("day").all()
    df = pd.DataFrame(rows, columns=["day", "temp_avg", "temp_min", "temp_max"])
    if not df.empty:
        df["day"] = pd.to_datetime(df["day"]).dt.tz_localize(None).dt.normalize()
    return df


def build_daily_frame(db: Session, home_id: int, days: int = 120) -> pd.DataFrame:
    """Retourne un DataFrame journalier prêt pour l'entraînement / la prévision."""
    cons = _daily_consumption(db, home_id, days)
    wx = _daily_weather(db, home_id, days)
    if cons.empty:
        return pd.DataFrame(columns=["day", "kwh", "cost", *FEATURE_COLUMNS])

    df = cons.merge(wx, on="day", how="left")
    df = df.sort_values("day").reset_index(drop=True)

    # Météo manquante -> remplissage par interpolation puis valeur médiane.
    for col in ("temp_avg", "temp_min", "temp_max"):
        df[col] = df[col].astype(float).interpolate().bfill().ffill()
        if df[col].isna().all():
            df[col] = 15.0

    df["dow"] = df["day"].dt.dayofweek
    df["is_weekend"] = (df["dow"] >= 5).astype(int)
    df["month"] = df["day"].dt.month
    df["doy"] = df["day"].dt.dayofyear
    df["lag1"] = df["kwh"].shift(1)
    df["lag7"] = df["kwh"].shift(7)
    df["roll7"] = df["kwh"].rolling(7, min_periods=1).mean().shift(1)

    df[["lag1", "lag7", "roll7"]] = df[["lag1", "lag7", "roll7"]].bfill()
    return df


def make_future_row(history: pd.DataFrame, target_day, temp_avg: float,
                     lag1: float, lag7: float, roll7: float) -> pd.DataFrame:
    """Construit une ligne de features pour un jour futur (prévision récursive)."""
    ts = pd.Timestamp(target_day)
    row = {
        "dow": ts.dayofweek,
        "is_weekend": int(ts.dayofweek >= 5),
        "month": ts.month,
        "doy": ts.dayofyear,
        "temp_avg": temp_avg,
        "temp_min": temp_avg - 4,
        "temp_max": temp_avg + 4,
        "lag1": lag1,
        "lag7": lag7,
        "roll7": roll7,
    }
    return pd.DataFrame([row])[FEATURE_COLUMNS]
