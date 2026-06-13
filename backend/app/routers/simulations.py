"""Routes /api/simulations — scénarios "what-if"."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.schemas import SimulationRequest, SimulationOut
from app.domain.simulation_engine import run_simulation
from app.routers.deps import resolve_home_id, get_home_or_404

router = APIRouter(prefix="/api/simulations", tags=["simulations"])

SCENARIOS = [
    {"scenario": "baisser_chauffage", "label": "Baisser le chauffage de 1°C",
     "params": {"delta_temp": 1}},
    {"scenario": "heures_creuses", "label": "Passer 25% des usages en heures creuses",
     "params": {"shift_pct": 0.25}},
    {"scenario": "panneaux_solaires", "label": "Ajouter 3 kWc de panneaux solaires",
     "params": {"kwc": 3}},
    {"scenario": "reduire_nocturne", "label": "Réduire de 50% la consommation nocturne",
     "params": {"reduction_pct": 0.5}},
]


@router.get("/scenarios")
def list_scenarios():
    """Catalogue des scénarios disponibles (pour alimenter l'UI)."""
    return SCENARIOS


@router.post("", response_model=SimulationOut)
def simulate(payload: SimulationRequest, home_id: int = Depends(resolve_home_id),
             db: Session = Depends(get_db)):
    """Exécute un scénario et persiste le résultat."""
    home = get_home_or_404(home_id, db)
    result = run_simulation(db, home, payload.scenario, payload.params)
    db.add(models.Simulation(
        home_id=home_id, scenario=result.scenario, params=result.params,
        baseline_kwh_month=result.baseline_kwh_month, simulated_kwh_month=result.simulated_kwh_month,
        saving_eur_month=result.saving_eur_month, saving_kwh_month=result.saving_kwh_month,
        co2_avoided_kg_month=result.co2_avoided_kg_month,
    ))
    db.commit()
    return result
