"""Génération de données fictives RÉALISTES + seed de la base GreenScan.

Usage (depuis le dossier backend/, avec la DB PostgreSQL démarrée) :

    python -m scripts.generate_data           # 90 jours, profils variés
    python -m scripts.generate_data --days 60

Produit, par logement :
- pièces + équipements (selon archétype)
- relevés météo horaires (saisonniers + cycle jour/nuit)
- consommation 30 min (base + appareils + chauffage(météo) + solaire + VE + anomalies)
- consommation journalière ventilée par pièce
puis génère un premier lot d'alertes / recommandations / KPI via les moteurs métier.

Tout est reproductible (seed aléatoire fixe).
"""
from __future__ import annotations

import argparse
import math
import random
import sys
from datetime import datetime, timedelta, timezone

import numpy as np

# Console Windows : forcer UTF-8 pour les caractères accentués / symboles.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.config import settings
from app.database import SessionLocal, init_db, engine, Base
from app.domain.catalog import (
    EQUIPMENT_CATALOG,
    EQUIPMENT_LABELS,
    HOME_ARCHETYPES,
    ROOM_EQUIPMENT_DEFAULTS,
    DPE_HEATING_FACTOR,
    HEATING_EFFICIENCY,
    HOURLY_USAGE_PROFILE,
    is_off_peak,
)
from app import models

RNG_SEED = 42
random.seed(RNG_SEED)
np.random.seed(RNG_SEED)

STEP_MINUTES = 30
STEPS_PER_DAY = 24 * 60 // STEP_MINUTES  # 48

# Profils d'occupants : multiplicateur global de consommation.
PROFILE_MULT = {"eco": 0.8, "standard": 1.0, "energivore": 1.3}


# --------------------------------------------------------------------------- #
# Définition des foyers de démonstration
# --------------------------------------------------------------------------- #
DEMO_HOMES = [
    {
        "user": ("Camille Martin", "camille.martin@example.com", "eco"),
        "home": dict(name="Studio Lyon Centre", home_type="studio", surface_m2=28,
                     construction_year=2015, dpe="B", orientation="sud", occupants_count=1,
                     heating_type="électrique", contracted_power_kva=6, has_solar_panels=False,
                     has_ev=False, city="Lyon", monthly_budget_eur=55),
    },
    {
        "user": ("Yanis Bernard", "yanis.bernard@example.com", "standard"),
        "home": dict(name="Appartement Paris 11e", home_type="appartement", surface_m2=65,
                     construction_year=1995, dpe="D", orientation="est", occupants_count=3,
                     heating_type="électrique", contracted_power_kva=9, has_solar_panels=False,
                     has_ev=False, city="Paris", monthly_budget_eur=130),
    },
    {
        "user": ("Sophie Dubois", "sophie.dubois@example.com", "standard"),
        "home": dict(name="Maison Nantes Sud", home_type="maison", surface_m2=120,
                     construction_year=2008, dpe="C", orientation="sud", occupants_count=4,
                     heating_type="PAC", contracted_power_kva=12, has_solar_panels=True,
                     has_ev=True, city="Nantes", monthly_budget_eur=180),
    },
    {
        "user": ("Marc Lefebvre", "marc.lefebvre@example.com", "energivore"),
        "home": dict(name="Maison Lille Nord", home_type="maison", surface_m2=140,
                     construction_year=1978, dpe="F", orientation="nord", occupants_count=5,
                     heating_type="électrique", contracted_power_kva=12, has_solar_panels=False,
                     has_ev=True, city="Lille", monthly_budget_eur=260),
    },
]


# --------------------------------------------------------------------------- #
# Météo
# --------------------------------------------------------------------------- #
def seasonal_mean_temp(day: datetime, city_offset: float) -> float:
    """Température moyenne journalière (sinusoïde annuelle + offset ville)."""
    doy = day.timetuple().tm_yday
    # minimum vers mi-janvier (doy ~ 15), maximum vers mi-juillet.
    base = 12 + 9 * math.sin(2 * math.pi * (doy - 105) / 365)
    return base + city_offset


def hourly_temp(mean_temp: float, hour: int) -> float:
    """Cycle journalier : minimum vers 5h, maximum vers 16h."""
    daily = 5.5 * math.sin(2 * math.pi * (hour - 9) / 24)
    return mean_temp + daily + np.random.normal(0, 0.7)


def solar_radiation(hour: int, cloud_cover: float, doy: int) -> float:
    """Rayonnement solaire (W/m²) : cloche diurne atténuée par les nuages."""
    if hour < 6 or hour > 21:
        return 0.0
    peak = 850 * (0.7 + 0.3 * math.sin(2 * math.pi * (doy - 80) / 365))  # plus fort en été
    bell = math.sin(math.pi * (hour - 6) / 15)  # 0 à 6h et 21h, max à ~13h30
    return max(0.0, peak * bell * (1 - 0.7 * cloud_cover / 100))


CITY_TEMP_OFFSET = {"Lille": -2.0, "Paris": 0.0, "Lyon": 0.5, "Nantes": 1.0}


# --------------------------------------------------------------------------- #
# Génération principale
# --------------------------------------------------------------------------- #
def build_rooms_and_equipments(db, home: models.Home) -> list[models.Room]:
    """Crée les pièces + équipements d'un logement selon son archétype."""
    archetype = HOME_ARCHETYPES[home.home_type]
    rooms: list[models.Room] = []
    for name, room_type, surface, floor in archetype["rooms"]:
        room = models.Room(
            home_id=home.id, name=name, room_type=room_type, surface_m2=float(surface),
            floor=floor, usual_occupants=max(1, home.occupants_count // 2),
            target_temperature=19.0 if room_type in ("chambre", "garage", "cave") else 20.5,
        )
        db.add(room)
        db.flush()
        rooms.append(room)

        equip_types = list(ROOM_EQUIPMENT_DEFAULTS.get(room_type, []))
        # Cohérence avec les options du logement.
        if room_type == "garage" and not home.has_ev:
            equip_types = [e for e in equip_types if e != "borne_ve"]
        if home.heating_type == "PAC" and "chauffage" in equip_types:
            equip_types = [e for e in equip_types if e != "chauffage"]
            if room_type == "salon":
                equip_types.append("pompe_a_chaleur")
        for et in equip_types:
            ref = EQUIPMENT_CATALOG[et]
            jitter = np.random.uniform(0.85, 1.15)
            db.add(models.Equipment(
                home_id=home.id, room_id=room.id,
                name=EQUIPMENT_LABELS[et], equipment_type=et,
                rated_power_w=round(ref["rated_power_w"] * jitter, 1),
                daily_usage_hours=round(ref["daily_usage_hours"] * np.random.uniform(0.8, 1.2), 2),
                is_active=True, criticality=ref["criticality"],
            ))
    # Panneaux solaires (équipement "virtuel" rattaché au toit / pièce principale).
    if home.has_solar_panels:
        ref = EQUIPMENT_CATALOG["panneaux_solaires"]
        db.add(models.Equipment(
            home_id=home.id, room_id=rooms[0].id, name=EQUIPMENT_LABELS["panneaux_solaires"],
            equipment_type="panneaux_solaires", rated_power_w=ref["rated_power_w"],
            daily_usage_hours=0.0, is_active=True, criticality=1,
        ))
    db.flush()
    return rooms


def appliance_daily_kwh(db, home: models.Home) -> float:
    """Somme journalière des consommations d'appareils (hors chauffage/solaire)."""
    equips = db.query(models.Equipment).filter(
        models.Equipment.home_id == home.id, models.Equipment.is_active.is_(True)
    ).all()
    total = 0.0
    for e in equips:
        if e.equipment_type in ("chauffage", "pompe_a_chaleur", "panneaux_solaires"):
            continue
        total += (e.rated_power_w / 1000.0) * e.daily_usage_hours
    return total


def generate_timeseries(db, home: models.Home, rooms: list[models.Room], days: int) -> None:
    """Génère météo + consommation 30 min + ventilation journalière par pièce."""
    profile_mult = PROFILE_MULT.get(home.owner.profile, 1.0)
    dpe_factor = DPE_HEATING_FACTOR.get(home.dpe, 1.0)
    heat_eff = HEATING_EFFICIENCY.get(home.heating_type, 1.0)
    city_offset = CITY_TEMP_OFFSET.get(home.city, 0.0)
    app_day = appliance_daily_kwh(db, home)
    profile_sum = sum(HOURLY_USAGE_PROFILE)

    # Poids de ventilation par pièce (pour répartir la conso journalière).
    room_weights = _room_weights(db, home, rooms)

    end = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    start_day = (end - timedelta(days=days)).replace(hour=0)

    consumption_rows: list[models.ConsumptionRecord] = []
    weather_rows: list[models.WeatherRecord] = []
    room_daily_rows: list[models.ConsumptionRecord] = []

    day = start_day
    while day <= end:
        doy = day.timetuple().tm_yday
        mean_t = seasonal_mean_temp(day, city_offset)
        is_weekend = day.weekday() >= 5
        cloud_day = float(np.clip(np.random.normal(50, 25), 0, 100))
        day_total_kwh = 0.0
        day_total_heating = 0.0

        for step in range(STEPS_PER_DAY):
            ts = day + timedelta(minutes=STEP_MINUTES * step)
            if ts > end:
                break
            hour = ts.hour

            # --- Météo (relevé horaire : on n'écrit qu'au step pile à l'heure) ---
            out_t = hourly_temp(mean_t, hour)
            rad = solar_radiation(hour, cloud_day, doy)
            if step % 2 == 0:
                weather_rows.append(models.WeatherRecord(
                    home_id=home.id, timestamp=ts, outdoor_temperature=round(out_t, 1),
                    humidity=round(float(np.clip(np.random.normal(65, 12), 25, 99)), 1),
                    wind_speed=round(abs(np.random.normal(12, 6)), 1),
                    solar_radiation=round(rad, 1), cloud_cover=round(cloud_day, 1),
                    weather_condition=_weather_condition(cloud_day, rad),
                ))

            # --- Appareils (profil horaire) ---
            prof = HOURLY_USAGE_PROFILE[hour]
            app_step = app_day * (prof / profile_sum) / 2.0  # /2 : deux pas par heure
            if is_weekend:
                app_step *= 1.12  # plus de présence le week-end
            app_step *= np.random.uniform(0.9, 1.1) * profile_mult

            # --- Chauffage (selon écart de température) ---
            target = 20.0 if (6 <= hour <= 23) else 17.0
            delta = max(0.0, target - out_t)
            heating_step = delta * home.surface_m2 * dpe_factor * heat_eff * 0.00065
            heating_step *= np.random.uniform(0.9, 1.1)
            # En été (delta faible) : un peu de clim si maison équipée et chaud.
            cooling = 0.0
            if out_t > 26 and home.home_type == "maison":
                cooling = (out_t - 26) * 0.05

            # --- Solaire (production, soustraite de la conso réseau) ---
            solar = 0.0
            if home.has_solar_panels and rad > 0:
                solar = (rad / 1000.0) * 3.0 * 0.5 * np.random.uniform(0.85, 1.0)  # 3 kWc, pas 30min

            # --- Véhicule électrique (recharge nocturne en HC) ---
            ev = 0.0
            if home.has_ev and is_off_peak(hour) and np.random.random() < 0.5:
                ev = 7.4 * 0.5 * np.random.uniform(0.4, 1.0)

            gross = app_step + heating_step + cooling + ev
            net = max(0.05, gross - solar)

            # --- Injection d'anomalies réalistes ---
            net = _inject_anomaly(net, hour, ts)

            tariff = "HC" if is_off_peak(hour) else "HP"
            price = settings.price_hc_eur_per_kwh if tariff == "HC" else settings.price_hp_eur_per_kwh
            cost = net * price
            co2 = net * settings.co2_factor_kg_per_kwh
            occ = _occupants_present(home, hour, is_weekend)

            consumption_rows.append(models.ConsumptionRecord(
                home_id=home.id, room_id=None, equipment_id=None, timestamp=ts,
                energy_consumption_kwh=round(net, 4), energy_cost_eur=round(cost, 4),
                tariff_type=tariff, heating_consumption_kwh=round(heating_step, 4),
                solar_production_kwh=round(solar, 4), ev_charging_kwh=round(ev, 4),
                occupants_present=occ, home_presence=occ > 0, co2_kg=round(co2, 4),
            ))
            day_total_kwh += net
            day_total_heating += heating_step

        # --- Ventilation journalière par pièce ---
        for room in rooms:
            w = room_weights[room.id]
            # le chauffage suit la surface ; on ajoute le poids appareils.
            r_kwh = day_total_kwh * w * np.random.uniform(0.95, 1.05)
            r_cost = r_kwh * settings.price_hp_eur_per_kwh
            room_daily_rows.append(models.ConsumptionRecord(
                home_id=home.id, room_id=room.id, equipment_id=None,
                timestamp=day.replace(hour=12),
                energy_consumption_kwh=round(r_kwh, 4), energy_cost_eur=round(r_cost, 4),
                tariff_type="HP", co2_kg=round(r_kwh * settings.co2_factor_kg_per_kwh, 4),
            ))

        day += timedelta(days=1)

    db.bulk_save_objects(weather_rows)
    db.bulk_save_objects(consumption_rows)
    db.bulk_save_objects(room_daily_rows)
    db.flush()
    print(f"   · {home.name}: {len(consumption_rows)} relevés conso, "
          f"{len(weather_rows)} météo, {len(room_daily_rows)} conso/pièce")


def _room_weights(db, home: models.Home, rooms: list[models.Room]) -> dict[int, float]:
    """Poids relatif de chaque pièce (équipements + surface), normalisé à 1."""
    raw: dict[int, float] = {}
    for room in rooms:
        equips = db.query(models.Equipment).filter(models.Equipment.room_id == room.id).all()
        equip_load = sum((e.rated_power_w / 1000.0) * e.daily_usage_hours
                         for e in equips if e.equipment_type != "panneaux_solaires")
        # surface compte pour le chauffage
        raw[room.id] = equip_load + room.surface_m2 * 0.04
    total = sum(raw.values()) or 1.0
    return {rid: v / total for rid, v in raw.items()}


def _occupants_present(home: models.Home, hour: int, is_weekend: bool) -> int:
    if is_weekend:
        return home.occupants_count if 8 <= hour <= 23 else max(0, home.occupants_count)
    if 9 <= hour <= 17:
        return max(0, home.occupants_count - 2)  # travail/école
    if 18 <= hour <= 23 or 6 <= hour <= 8:
        return home.occupants_count
    return home.occupants_count  # nuit : présents (endormis)


def _weather_condition(cloud: float, rad: float) -> str:
    if rad > 400 and cloud < 35:
        return "ensoleillé"
    if cloud > 75:
        return "pluvieux" if np.random.random() < 0.4 else "couvert"
    return "nuageux"


def _inject_anomaly(net: float, hour: int, ts: datetime) -> float:
    """Ajoute ponctuellement des comportements anormaux détectables."""
    # Pic de consommation nocturne (appareil oublié) ~ 1.5% des pas de nuit.
    if hour in (1, 2, 3, 4) and np.random.random() < 0.015:
        return net + np.random.uniform(1.5, 3.0)
    # Surconsommation diurne ponctuelle ~ 0.5%.
    if np.random.random() < 0.005:
        return net * np.random.uniform(2.0, 3.5)
    return net


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def reset_database() -> None:
    print("· Réinitialisation du schéma (drop + create)...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def seed(days: int) -> None:
    init_db()
    reset_database()
    db = SessionLocal()
    home_ids: list[int] = []
    try:
        print(f"· Génération de {len(DEMO_HOMES)} logements sur {days} jours...")
        for spec in DEMO_HOMES:
            full_name, email, profile = spec["user"]
            user = models.User(full_name=full_name, email=email, profile=profile)
            db.add(user)
            db.flush()
            home = models.Home(owner_id=user.id, **spec["home"])
            db.add(home)
            db.flush()
            home.owner = user
            rooms = build_rooms_and_equipments(db, home)
            generate_timeseries(db, home, rooms, days)
            home_ids.append(home.id)
        db.commit()
        print("· Données brutes enregistrées ✔")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    # --- Intelligence : alertes / recommandations / KPI (moteurs métier) ---
    _refresh_intelligence(home_ids)


def _refresh_intelligence(home_ids: list[int]) -> None:
    """Calcule et persiste un premier lot d'alertes / recommandations / KPI."""
    try:
        from app.services.intelligence import refresh_home_intelligence
    except Exception as exc:  # pragma: no cover - si moteurs absents
        print(f"  (intelligence non générée: {exc})")
        return
    db = SessionLocal()
    try:
        for hid in home_ids:
            refresh_home_intelligence(db, hid)
        db.commit()
        print("· Alertes, recommandations et KPI générés ✔")
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Génère les données de démo GreenScan.")
    parser.add_argument("--days", type=int, default=90, help="Nombre de jours d'historique.")
    args = parser.parse_args()
    seed(args.days)
    print("\n✅ Base GreenScan prête. Lance ensuite l'entraînement IA :")
    print("   python -m scripts.train_models")


if __name__ == "__main__":
    main()
