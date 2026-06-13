"""Détection d'alertes intelligentes à partir des données de consommation.

Catégories couvertes :
- surconsommation        : journée nettement au-dessus de la moyenne
- conso_nocturne         : consommation nocturne anormale
- chauffage_fenetre      : chauffage actif alors qu'il fait doux dehors
- equipement_energivore  : équipement très consommateur / critique
- au_dessus_moyenne      : intensité supérieure au benchmark du type de logement
- derive_consommation    : dérive haussière sur les derniers jours
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models
from app.services.analytics import home_level_filter, daily_kwh_history, equipment_estimated_kwh_month

# Benchmark d'intensité acceptable (kWh/m²/jour) par type de logement.
INTENSITY_BENCHMARK = {"studio": 0.16, "appartement": 0.14, "maison": 0.13}


def detect_alerts(db: Session, home: models.Home) -> list[models.Alert]:
    alerts: list[models.Alert] = []
    now = datetime.now(timezone.utc)

    # --- Référence : conso journalière sur 30 j ---
    daily = daily_kwh_history(db, home.id, days=30)
    if len(daily) >= 5:
        values = [v for _, v in daily]
        avg = sum(values[:-1]) / max(len(values) - 1, 1)
        last_day, last_val = daily[-1]

        # 1) Surconsommation journalière
        if avg > 0 and last_val > avg * 1.4:
            pct = (last_val / avg - 1) * 100
            alerts.append(models.Alert(
                home_id=home.id, category="surconsommation", level="warning",
                title="Surconsommation détectée",
                description=f"La consommation du {last_day} ({last_val:.1f} kWh) dépasse de "
                            f"{pct:.0f}% votre moyenne ({avg:.1f} kWh).",
                recommendation="Vérifiez les équipements restés allumés et le chauffage.",
            ))

        # 2) Dérive de consommation (3 derniers jours vs 3 précédents)
        if len(values) >= 6:
            recent = sum(values[-3:]) / 3
            previous = sum(values[-6:-3]) / 3
            if previous > 0 and recent > previous * 1.25:
                alerts.append(models.Alert(
                    home_id=home.id, category="derive_consommation", level="info",
                    title="Dérive de consommation",
                    description=f"Votre consommation moyenne a augmenté de "
                                f"{(recent / previous - 1) * 100:.0f}% sur 3 jours.",
                    recommendation="Surveillez vos usages récents pour éviter une facture en hausse.",
                ))

    # --- Conso nocturne anormale (pics 0h-5h sur 14 j) ---
    since = now - timedelta(days=14)
    night_max = db.query(func.max(models.ConsumptionRecord.energy_consumption_kwh)).filter(
        home_level_filter(home.id), models.ConsumptionRecord.timestamp >= since,
        func.extract("hour", models.ConsumptionRecord.timestamp) < 5).scalar() or 0.0
    night_avg = db.query(func.avg(models.ConsumptionRecord.energy_consumption_kwh)).filter(
        home_level_filter(home.id), models.ConsumptionRecord.timestamp >= since,
        func.extract("hour", models.ConsumptionRecord.timestamp) < 5).scalar() or 0.0
    if night_avg and night_max > night_avg * 3:
        alerts.append(models.Alert(
            home_id=home.id, category="conso_nocturne", level="critical",
            title="Consommation nocturne anormale",
            description=f"Un pic de {night_max:.1f} kWh a été mesuré la nuit "
                        f"(moyenne nocturne {night_avg:.2f} kWh).",
            recommendation="Un appareil énergivore reste probablement actif la nuit.",
        ))

    # --- Chauffage actif alors qu'il fait doux (proxy "fenêtre ouverte") ---
    warm_heating = db.query(
        func.count(models.ConsumptionRecord.id)
    ).join(
        models.WeatherRecord,
        func.date_trunc("hour", models.WeatherRecord.timestamp)
        == func.date_trunc("hour", models.ConsumptionRecord.timestamp),
    ).filter(
        home_level_filter(home.id),
        models.WeatherRecord.home_id == home.id,
        models.ConsumptionRecord.timestamp >= since,
        models.ConsumptionRecord.heating_consumption_kwh > 0.5,
        models.WeatherRecord.outdoor_temperature > 21,
    ).scalar() or 0
    if warm_heating > 5:
        alerts.append(models.Alert(
            home_id=home.id, category="chauffage_fenetre", level="warning",
            title="Chauffage actif par temps doux",
            description=f"Le chauffage a fonctionné {warm_heating} fois alors qu'il faisait "
                        f"plus de 21°C dehors.",
            recommendation="Vérifiez qu'aucune fenêtre n'est ouverte et ajustez le thermostat.",
        ))

    # --- Équipement énergivore / critique ---
    equips = db.query(models.Equipment).filter(
        models.Equipment.home_id == home.id, models.Equipment.is_active.is_(True)).all()
    for e in equips:
        est = equipment_estimated_kwh_month(e)
        if e.criticality >= 5 and est > 150:
            alerts.append(models.Alert(
                home_id=home.id, room_id=e.room_id, equipment_id=e.id,
                category="equipement_energivore", level="warning",
                title=f"Équipement très énergivore : {e.name}",
                description=f"{e.name} consommerait environ {est:.0f} kWh/mois "
                            f"(criticité {e.criticality}/5).",
                recommendation="Limitez sa durée d'utilisation ou remplacez-le par un modèle efficient.",
            ))

    # --- Intensité au-dessus du benchmark ---
    kwh30 = sum(v for _, v in daily) if daily else 0.0
    intensity = kwh30 / 30 / max(home.surface_m2, 1.0)
    bench = INTENSITY_BENCHMARK.get(home.home_type, 0.14)
    if intensity > bench * 1.3:
        alerts.append(models.Alert(
            home_id=home.id, category="au_dessus_moyenne", level="info",
            title="Consommation supérieure aux logements similaires",
            description=f"Votre intensité ({intensity:.2f} kWh/m²/j) dépasse la référence "
                        f"{bench:.2f} pour un(e) {home.home_type}.",
            recommendation="Comparez vos pièces et ciblez les plus énergivores.",
        ))

    return alerts
