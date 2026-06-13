"""Moteur de recommandations personnalisées.

Chaque recommandation chiffre : gain €/mois, gain kWh/mois, CO₂ évité, impact, difficulté.
Les gains sont des estimations explicables fondées sur les totaux mesurés.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app import models
from app.config import settings
from app.services.analytics import period_totals, rooms_consumption
from app.domain.scoring import night_share

REF_DAYS = 30
AVG_PRICE = (settings.price_hp_eur_per_kwh + settings.price_hc_eur_per_kwh) / 2
CO2 = settings.co2_factor_kg_per_kwh


def _reco(**kw) -> models.Recommendation:
    return models.Recommendation(**kw)


def compute_recommendations(db: Session, home: models.Home) -> list[models.Recommendation]:
    since = datetime.now(timezone.utc) - timedelta(days=REF_DAYS)
    t = period_totals(db, home.id, since)
    recos: list[models.Recommendation] = []

    heating_kwh = t["heating_kwh"]
    total_kwh = t["kwh"] or 1.0

    # 1) Baisser le chauffage de 1°C (~7 % du chauffage)
    if heating_kwh > 20:
        g_kwh = heating_kwh * 0.07
        recos.append(_reco(
            home_id=home.id, code="baisser_chauffage",
            action="Baisser le chauffage de 1°C",
            gain_kwh_month=round(g_kwh, 1), gain_eur_month=round(g_kwh * AVG_PRICE, 2),
            co2_avoided_kg_month=round(g_kwh * CO2, 1),
            impact="élevé" if g_kwh > 40 else "moyen", difficulty="facile",
        ))

    # 2) Décaler des usages en heures creuses
    hp_kwh = t["hp_kwh"]
    if hp_kwh > total_kwh * 0.55:
        shift = hp_kwh * 0.20  # 20 % de la conso HP décalable (lave-linge, VE, chauffe-eau)
        g_eur = shift * (settings.price_hp_eur_per_kwh - settings.price_hc_eur_per_kwh)
        recos.append(_reco(
            home_id=home.id, code="heures_creuses",
            action="Décaler lave-linge / chauffe-eau / recharge VE en heures creuses",
            gain_kwh_month=0.0, gain_eur_month=round(g_eur, 2),
            co2_avoided_kg_month=0.0, impact="moyen", difficulty="facile",
        ))

    # 3) Réduire la consommation nocturne
    nshare = night_share(db, home.id)
    if nshare > 0.20:
        excess_kwh = total_kwh * (nshare - 0.15)
        recos.append(_reco(
            home_id=home.id, code="conso_nocturne",
            action="Réduire la consommation nocturne (appareils en veille / oubliés)",
            gain_kwh_month=round(excess_kwh, 1), gain_eur_month=round(excess_kwh * AVG_PRICE, 2),
            co2_avoided_kg_month=round(excess_kwh * CO2, 1),
            impact="moyen", difficulty="facile",
        ))

    # 4) Pièce la plus énergivore (conseil comparatif)
    rooms = rooms_consumption(db, home.id, days=REF_DAYS)
    if rooms:
        top = rooms[0]
        recos.append(_reco(
            home_id=home.id, room_id=top.id, code="comparaison_piece",
            action=f"« {top.name} » représente {top.share_pct:.0f}% de votre consommation",
            gain_kwh_month=round(top.consumption_kwh * 0.1, 1),
            gain_eur_month=round(top.cost_eur * 0.1, 2),
            co2_avoided_kg_month=round(top.consumption_kwh * 0.1 * CO2, 1),
            impact="moyen", difficulty="moyen",
        ))

    # 5) Installer des panneaux solaires (si absents et orientation favorable)
    if not home.has_solar_panels and home.home_type == "maison" and home.orientation in ("sud", "est", "ouest", None):
        prod = total_kwh * 0.30  # couverture ~30 %
        recos.append(_reco(
            home_id=home.id, code="panneaux_solaires",
            action="Installer des panneaux solaires (≈ 3 kWc)",
            gain_kwh_month=round(prod, 1), gain_eur_month=round(prod * AVG_PRICE, 2),
            co2_avoided_kg_month=round(prod * CO2, 1),
            impact="élevé", difficulty="difficile",
        ))

    # 6) Améliorer l'isolation (DPE faible)
    if home.dpe in ("E", "F", "G") and heating_kwh > 30:
        g_kwh = heating_kwh * 0.25
        recos.append(_reco(
            home_id=home.id, code="isolation",
            action="Améliorer l'isolation (combles / fenêtres)",
            gain_kwh_month=round(g_kwh, 1), gain_eur_month=round(g_kwh * AVG_PRICE, 2),
            co2_avoided_kg_month=round(g_kwh * CO2, 1),
            impact="élevé", difficulty="difficile",
        ))

    return recos
