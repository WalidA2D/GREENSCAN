"""Moteur de calcul des KPI (aligné sur KPI_GREEN_Professionnel.xlsx).

Familles : Énergétiques, Financiers, Écologiques, IA.
Période de référence : 30 derniers jours (assimilés à un mois).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app import models
from app.schemas import KpiOut
from app.services.analytics import period_totals
from app.domain.scoring import compute_scores

REF_DAYS = 30


def compute_kpis(db: Session, home_id: int, anomaly_rate: float | None = None) -> list[KpiOut]:
    home = db.get(models.Home, home_id)
    if home is None:
        return []

    since = datetime.now(timezone.utc) - timedelta(days=REF_DAYS)
    t = period_totals(db, home_id, since)
    scores = compute_scores(db, home, t, anomaly_rate=anomaly_rate)

    kwh = t["kwh"]
    cost = t["cost"]
    occupants = max(home.occupants_count, 1)
    hp_pct = (t["hp_kwh"] / kwh * 100) if kwh else 0.0
    chauffage_pct = (t["heating_kwh"] / kwh * 100) if kwh else 0.0
    autonomie_pct = (t["solar_kwh"] / kwh * 100) if kwh else 0.0

    # Facture estimée fin de mois = coût des 30 derniers jours.
    facture = cost
    # Économie potentielle = part "gaspillage" récupérable de la facture.
    economie = facture * (scores["waste_score"] / 100.0) * 0.5
    co2_evitable = t["co2"] * (scores["waste_score"] / 100.0) * 0.5

    kpis = [
        # --- Énergétiques ---
        KpiOut(code="conso_totale", label="Consommation totale (30j)", value=round(kwh, 1), unit="kWh"),
        KpiOut(code="conso_par_occupant", label="Conso / occupant", value=round(kwh / occupants, 1), unit="kWh"),
        KpiOut(code="chauffage_pct", label="Part chauffage", value=round(chauffage_pct, 1), unit="%"),
        KpiOut(code="hp_hc_pct", label="Heures pleines", value=round(hp_pct, 1), unit="%"),
        KpiOut(code="autonomie_pct", label="Autonomie énergétique", value=round(autonomie_pct, 1), unit="%"),
        # --- Financiers ---
        KpiOut(code="facture_estimee", label="Facture estimée (mois)", value=round(facture, 2), unit="€"),
        KpiOut(code="economie_potentielle", label="Économie potentielle", value=round(economie, 2), unit="€"),
        KpiOut(code="economie_annuelle", label="Économie annuelle projetée", value=round(economie * 12, 2), unit="€"),
        # --- Écologiques ---
        KpiOut(code="co2_emis", label="CO₂ émis (30j)", value=round(t["co2"], 1), unit="kg"),
        KpiOut(code="co2_evitable", label="CO₂ évitable", value=round(co2_evitable, 1), unit="kg"),
        KpiOut(code="green_score", label="Green Score", value=scores["green_score"], unit="/100"),
        # --- IA ---
        KpiOut(code="anomaly_score", label="Anomaly Score", value=scores["anomaly_score"], unit="/100"),
        KpiOut(code="waste_score", label="Waste Score", value=scores["waste_score"], unit="/100"),
    ]
    return kpis


def persist_kpis(db: Session, home_id: int, kpis: list[KpiOut]) -> None:
    """Historise un snapshot des KPI (table kpi_results)."""
    db.query(models.KpiResult).filter(models.KpiResult.home_id == home_id).delete()
    for k in kpis:
        db.add(models.KpiResult(home_id=home_id, code=k.code, label=k.label, value=k.value, unit=k.unit))
