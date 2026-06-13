"""Prévision de consommation (J+1, J+7) et de facture mensuelle.

Stratégie :
- charge le modèle entraîné du logement si présent ;
- prévision récursive sur 7 jours (les prévisions alimentent les lags) ;
- météo future approximée par la température moyenne récente (pas d'API externe) ;
- fallback statistique (moyenne glissante) si aucun modèle n'est disponible.
"""
from __future__ import annotations

import calendar
import json
from datetime import datetime, timedelta, timezone

import joblib
import numpy as np
from sqlalchemy.orm import Session

from app import models
from app.config import settings
from app.ml.features import build_daily_frame, make_future_row
from app.ml.train import model_path, metrics_path
from app.schemas import PredictionBundle, PredictionPoint

AVG_PRICE = (settings.price_hp_eur_per_kwh + settings.price_hc_eur_per_kwh) / 2


def _load_model(home_id: int):
    path = model_path(home_id)
    if not path.exists():
        return None
    try:
        return joblib.load(path)
    except Exception:
        return None


def _load_metrics(home_id: int) -> dict:
    path = metrics_path(home_id)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8")).get("metrics", {})
        except Exception:
            return {}
    return {}


def predict_bundle(db: Session, home_id: int, horizon: int = 7) -> PredictionBundle:
    home = db.get(models.Home, home_id)
    df = build_daily_frame(db, home_id, days=120).dropna(subset=["kwh"])

    if df.empty:
        return _empty_bundle(home)

    recent_temp = float(df["temp_avg"].tail(7).mean())
    history_vals = df["kwh"].tolist()
    history_days = df["day"].tolist()

    bundle_model = _load_model(home_id)
    metrics = _load_metrics(home_id)

    if bundle_model is not None:
        model = bundle_model["model"]
        model_name = bundle_model["model_name"]
        preds = _forecast_with_model(model, df, recent_temp, horizon)
    else:
        model_name = "MoyenneGlissante (fallback)"
        preds = _forecast_fallback(df, horizon)
        metrics = metrics or {"MAE": None, "RMSE": None, "MAPE": None, "R2": None}

    last_day = history_days[-1]
    forecast_curve = [
        PredictionPoint(date=(last_day + timedelta(days=i + 1)).strftime("%Y-%m-%d"),
                        value=round(float(p), 2))
        for i, p in enumerate(preds)
    ]
    history_curve = [
        PredictionPoint(date=d.strftime("%Y-%m-%d"), value=round(float(v), 2))
        for d, v in zip(history_days[-14:], history_vals[-14:])
    ]

    j1 = float(preds[0])
    j7 = float(sum(preds[:7]))

    # Facture fin de mois : coût du mois en cours + projection des jours restants.
    monthly_bill, budget_risk = _monthly_projection(db, home, df, float(np.mean(preds)))

    return PredictionBundle(
        consumption_j1_kwh=round(j1, 2),
        consumption_j7_kwh=round(j7, 2),
        monthly_bill_eur=round(monthly_bill, 2),
        budget_eur=round(home.monthly_budget_eur, 2),
        budget_overrun_risk=round(budget_risk, 2),
        model_name=model_name,
        metrics=metrics,
        forecast_curve=forecast_curve,
        history_curve=history_curve,
    )


def _forecast_with_model(model, df, recent_temp: float, horizon: int) -> list[float]:
    """Prévision récursive : chaque jour prédit alimente les lags du suivant."""
    kwh = df["kwh"].tolist()
    last_day = df["day"].iloc[-1]
    preds: list[float] = []
    for i in range(horizon):
        target_day = last_day + timedelta(days=i + 1)
        lag1 = preds[-1] if preds else kwh[-1]
        # lag7 : valeur 7 jours avant la cible (historique réel ou prévu).
        idx_back = 7 - (i + 1)
        if idx_back >= 1 and len(kwh) >= idx_back:
            lag7 = kwh[-idx_back]
        else:
            lag7 = preds[i - 7] if i - 7 >= 0 else (preds[-1] if preds else kwh[-1])
        window = (kwh + preds)[-7:]
        roll7 = float(np.mean(window))
        row = make_future_row(df, target_day, recent_temp, lag1, lag7, roll7)
        pred = float(model.predict(row.values)[0])
        preds.append(max(0.0, pred))
    return preds


def _forecast_fallback(df, horizon: int) -> list[float]:
    """Moyenne glissante pondérée par le jour de semaine (sans modèle entraîné)."""
    df = df.copy()
    df["dow"] = df["day"].dt.dayofweek
    overall = float(df["kwh"].tail(14).mean())
    last_day = df["day"].iloc[-1]
    preds = []
    for i in range(horizon):
        target = last_day + timedelta(days=i + 1)
        same_dow = df[df["dow"] == target.dayofweek]["kwh"]
        preds.append(float(same_dow.tail(4).mean()) if len(same_dow) else overall)
    return preds


def _monthly_projection(db: Session, home, df, avg_daily_pred: float) -> tuple[float, float]:
    """Coût du mois en cours + projection -> facture estimée et risque budget (0..1)."""
    now = datetime.now(timezone.utc)
    days_in_month = calendar.monthrange(now.year, now.month)[1]
    # Coût réel cumulé du mois en cours (home-level).
    from app.services.analytics import period_totals
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    mtd = period_totals(db, home.id, month_start)
    remaining_days = days_in_month - now.day
    projected_cost = mtd["cost"] + avg_daily_pred * AVG_PRICE * max(0, remaining_days)

    budget = home.monthly_budget_eur or 1.0
    ratio = projected_cost / budget
    # Risque : 0 si <0.8×budget, 1 si >1.2×budget (transition linéaire).
    risk = float(np.clip((ratio - 0.8) / 0.4, 0.0, 1.0))
    return projected_cost, risk


def _empty_bundle(home) -> PredictionBundle:
    return PredictionBundle(
        consumption_j1_kwh=0.0, consumption_j7_kwh=0.0, monthly_bill_eur=0.0,
        budget_eur=round(home.monthly_budget_eur, 2) if home else 0.0,
        budget_overrun_risk=0.0, model_name="indisponible", metrics={},
        forecast_curve=[], history_curve=[],
    )
