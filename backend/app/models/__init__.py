"""Modèles ORM GreenScan.

Schéma relationnel (aligné sur Patrimoine_Donnees_GREEN_Professionnel.xlsx) :

    users 1─* homes 1─* rooms 1─* equipments
    homes 1─* consumption_records   (mesures 30 min, granularité logement)
    homes 1─* weather_records
    homes 1─* predictions / alerts / recommendations / kpi_results / simulations
    rooms / equipments  ─* consumption_records (clés optionnelles pour ventilation)
"""
from app.models.user import User
from app.models.home import Home
from app.models.room import Room
from app.models.equipment import Equipment
from app.models.consumption import ConsumptionRecord
from app.models.weather import WeatherRecord
from app.models.prediction import Prediction
from app.models.alert import Alert
from app.models.recommendation import Recommendation
from app.models.kpi import KpiResult
from app.models.simulation import Simulation

__all__ = [
    "User",
    "Home",
    "Room",
    "Equipment",
    "ConsumptionRecord",
    "WeatherRecord",
    "Prediction",
    "Alert",
    "Recommendation",
    "KpiResult",
    "Simulation",
]
