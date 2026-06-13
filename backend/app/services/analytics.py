"""Agrégations analytiques sur les relevés de consommation.

Toutes les fonctions distinguent :
- niveau LOGEMENT : consumption_records.room_id IS NULL  (série 30 min)
- niveau PIÈCE    : consumption_records.room_id IS NOT NULL (agrégat journalier)
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from app import models
from app.schemas import ConsumptionPoint, RoomConsumptionOut


def _now() -> datetime:
    return datetime.now(timezone.utc)


def home_level_filter(home_id: int):
    return and_(
        models.ConsumptionRecord.home_id == home_id,
        models.ConsumptionRecord.room_id.is_(None),
    )


# --------------------------------------------------------------------------- #
# Totaux sur une période
# --------------------------------------------------------------------------- #
def period_totals(db: Session, home_id: int, since: datetime) -> dict:
    """Somme des indicateurs (logement) depuis `since`."""
    row = db.query(
        func.coalesce(func.sum(models.ConsumptionRecord.energy_consumption_kwh), 0.0),
        func.coalesce(func.sum(models.ConsumptionRecord.energy_cost_eur), 0.0),
        func.coalesce(func.sum(models.ConsumptionRecord.co2_kg), 0.0),
        func.coalesce(func.sum(models.ConsumptionRecord.heating_consumption_kwh), 0.0),
        func.coalesce(func.sum(models.ConsumptionRecord.solar_production_kwh), 0.0),
        func.coalesce(func.sum(models.ConsumptionRecord.ev_charging_kwh), 0.0),
    ).filter(home_level_filter(home_id),
             models.ConsumptionRecord.timestamp >= since).one()

    # Répartition HP / HC.
    hp = db.query(func.coalesce(func.sum(models.ConsumptionRecord.energy_consumption_kwh), 0.0)).filter(
        home_level_filter(home_id), models.ConsumptionRecord.timestamp >= since,
        models.ConsumptionRecord.tariff_type == "HP").scalar()
    return {
        "kwh": float(row[0]), "cost": float(row[1]), "co2": float(row[2]),
        "heating_kwh": float(row[3]), "solar_kwh": float(row[4]), "ev_kwh": float(row[5]),
        "hp_kwh": float(hp or 0.0),
    }


def today_consumption(db: Session, home_id: int) -> float:
    start = _now().replace(hour=0, minute=0, second=0, microsecond=0)
    return period_totals(db, home_id, start)["kwh"]


def last_record_ts(db: Session, home_id: int) -> datetime | None:
    return db.query(func.max(models.ConsumptionRecord.timestamp)).filter(
        home_level_filter(home_id)).scalar()


# --------------------------------------------------------------------------- #
# Séries temporelles
# --------------------------------------------------------------------------- #
def consumption_series(db: Session, home_id: int, granularity: str, days: int) -> list[ConsumptionPoint]:
    """Série agrégée (hourly | daily | weekly | monthly) sur les `days` derniers jours."""
    since = _now() - timedelta(days=days)
    rows = db.query(
        models.ConsumptionRecord.timestamp,
        models.ConsumptionRecord.energy_consumption_kwh,
        models.ConsumptionRecord.energy_cost_eur,
        models.ConsumptionRecord.co2_kg,
    ).filter(home_level_filter(home_id),
             models.ConsumptionRecord.timestamp >= since).order_by(
        models.ConsumptionRecord.timestamp).all()

    buckets: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0, 0.0])
    for ts, kwh, cost, co2 in rows:
        key = _bucket_key(ts, granularity)
        buckets[key][0] += float(kwh)
        buckets[key][1] += float(cost)
        buckets[key][2] += float(co2)

    return [
        ConsumptionPoint(period=k, consumption_kwh=round(v[0], 3),
                         cost_eur=round(v[1], 2), co2_kg=round(v[2], 3))
        for k, v in sorted(buckets.items())
    ]


def _bucket_key(ts: datetime, granularity: str) -> str:
    if granularity == "hourly":
        return ts.strftime("%Y-%m-%d %H:00")
    if granularity == "weekly":
        iso = ts.isocalendar()
        return f"{iso.year}-S{iso.week:02d}"
    if granularity == "monthly":
        return ts.strftime("%Y-%m")
    return ts.strftime("%Y-%m-%d")  # daily par défaut


def daily_kwh_history(db: Session, home_id: int, days: int = 60) -> list[tuple[str, float]]:
    """Historique de conso journalière (pour l'IA), liste (date_iso, kwh)."""
    series = consumption_series(db, home_id, "daily", days)
    return [(p.period, p.consumption_kwh) for p in series]


# --------------------------------------------------------------------------- #
# Consommation par pièce
# --------------------------------------------------------------------------- #
def rooms_consumption(db: Session, home_id: int, days: int = 30) -> list[RoomConsumptionOut]:
    """Consommation agrégée par pièce + niveau couleur (vert/orange/rouge)."""
    since = _now() - timedelta(days=days)
    rooms = db.query(models.Room).filter(models.Room.home_id == home_id).all()
    if not rooms:
        return []

    totals: dict[int, tuple[float, float]] = {}
    for room in rooms:
        row = db.query(
            func.coalesce(func.sum(models.ConsumptionRecord.energy_consumption_kwh), 0.0),
            func.coalesce(func.sum(models.ConsumptionRecord.energy_cost_eur), 0.0),
        ).filter(models.ConsumptionRecord.room_id == room.id,
                 models.ConsumptionRecord.timestamp >= since).one()
        totals[room.id] = (float(row[0]), float(row[1]))

    grand_total = sum(v[0] for v in totals.values()) or 1.0
    values = [v[0] for v in totals.values()]
    # Seuils relatifs : tiers haut = rouge, tiers médian = orange.
    hi = max(values) if values else 0.0
    out: list[RoomConsumptionOut] = []
    for room in rooms:
        kwh, cost = totals[room.id]
        share = kwh / grand_total * 100.0
        ratio = kwh / hi if hi else 0.0
        level = "rouge" if ratio >= 0.66 else "orange" if ratio >= 0.33 else "vert"
        equip_count = db.query(func.count(models.Equipment.id)).filter(
            models.Equipment.room_id == room.id).scalar() or 0
        out.append(RoomConsumptionOut(
            id=room.id, home_id=home_id, name=room.name, room_type=room.room_type,
            surface_m2=room.surface_m2, floor=room.floor, usual_occupants=room.usual_occupants,
            target_temperature=room.target_temperature,
            consumption_kwh=round(kwh, 2), cost_eur=round(cost, 2),
            share_pct=round(share, 1), level=level, equipment_count=int(equip_count),
        ))
    return sorted(out, key=lambda r: r.consumption_kwh, reverse=True)


def equipment_estimated_kwh_month(equip: models.Equipment) -> float:
    """Estimation mensuelle d'un équipement : P(kW) × h/jour × 30."""
    if equip.equipment_type == "panneaux_solaires" or not equip.is_active:
        return 0.0
    return round((equip.rated_power_w / 1000.0) * equip.daily_usage_hours * 30.0, 1)
