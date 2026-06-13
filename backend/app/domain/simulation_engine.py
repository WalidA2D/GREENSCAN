"""Moteur de simulation de scénarios "what-if".

Scénarios supportés :
- baisser_chauffage  : params {"delta_temp": 1}      -> -7%/°C sur le chauffage
- heures_creuses     : params {"shift_pct": 0.25}    -> report d'usages HP -> HC
- panneaux_solaires  : params {"kwc": 3}             -> autoproduction estimée
- reduire_nocturne   : params {"reduction_pct": 0.5} -> baisse de la conso nocturne
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app import models
from app.config import settings
from app.schemas import SimulationOut
from app.services.analytics import period_totals
from app.domain.scoring import night_share

REF_DAYS = 30
AVG_PRICE = (settings.price_hp_eur_per_kwh + settings.price_hc_eur_per_kwh) / 2
CO2 = settings.co2_factor_kg_per_kwh


def run_simulation(db: Session, home: models.Home, scenario: str, params: dict) -> SimulationOut:
    since = datetime.now(timezone.utc) - timedelta(days=REF_DAYS)
    t = period_totals(db, home.id, since)
    baseline = t["kwh"]
    saving_kwh = 0.0
    saving_eur = 0.0
    explanation = ""

    if scenario == "baisser_chauffage":
        delta = float(params.get("delta_temp", 1))
        saving_kwh = t["heating_kwh"] * 0.07 * delta
        saving_eur = saving_kwh * AVG_PRICE
        explanation = (f"Baisser le chauffage de {delta:.0f}°C réduit le poste chauffage "
                       f"de {0.07 * delta * 100:.0f}% (≈ {saving_kwh:.0f} kWh/mois).")

    elif scenario == "heures_creuses":
        shift_pct = float(params.get("shift_pct", 0.25))
        shift = t["hp_kwh"] * shift_pct
        saving_eur = shift * (settings.price_hp_eur_per_kwh - settings.price_hc_eur_per_kwh)
        saving_kwh = 0.0  # même énergie, moins chère
        explanation = (f"Décaler {shift_pct * 100:.0f}% de la conso heures pleines "
                       f"vers les heures creuses économise {saving_eur:.2f} €/mois (énergie inchangée).")

    elif scenario == "panneaux_solaires":
        kwc = float(params.get("kwc", 3))
        # ~ 1100 kWh/an par kWc en France -> /12 par mois, plafonné à la conso.
        prod = min(baseline, kwc * 1100 / 12)
        saving_kwh = prod
        saving_eur = prod * AVG_PRICE
        explanation = (f"Une installation de {kwc:.0f} kWc produit ≈ {prod:.0f} kWh/mois, "
                       f"autant de moins soutiré au réseau.")

    elif scenario == "reduire_nocturne":
        reduction = float(params.get("reduction_pct", 0.5))
        nshare = night_share(db, home.id)
        night_kwh = baseline * nshare
        saving_kwh = night_kwh * reduction
        saving_eur = saving_kwh * settings.price_hc_eur_per_kwh
        explanation = (f"Réduire de {reduction * 100:.0f}% la conso nocturne "
                       f"(actuellement {nshare * 100:.0f}% du total) économise ≈ {saving_kwh:.0f} kWh/mois.")
    else:
        explanation = "Scénario inconnu."

    simulated = max(0.0, baseline - saving_kwh)
    co2_avoided = saving_kwh * CO2
    saving_pct = (saving_kwh / baseline * 100) if baseline else 0.0

    return SimulationOut(
        scenario=scenario, params=params,
        baseline_kwh_month=round(baseline, 1), simulated_kwh_month=round(simulated, 1),
        saving_kwh_month=round(saving_kwh, 1), saving_eur_month=round(saving_eur, 2),
        co2_avoided_kg_month=round(co2_avoided, 1), saving_pct=round(saving_pct, 1),
        explanation=explanation,
    )
