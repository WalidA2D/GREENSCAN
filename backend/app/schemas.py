"""Schémas Pydantic (validation entrée + sérialisation sortie de l'API)."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# Modèle de base : autorise la lecture depuis les objets ORM.
ORM = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# User
# --------------------------------------------------------------------------- #
class UserOut(BaseModel):
    model_config = ORM
    id: int
    full_name: str
    email: EmailStr
    profile: str


# --------------------------------------------------------------------------- #
# Home
# --------------------------------------------------------------------------- #
class HomeBase(BaseModel):
    name: str
    home_type: str
    surface_m2: float
    construction_year: int | None = None
    dpe: str = "D"
    orientation: str | None = None
    occupants_count: int = 2
    heating_type: str = "électrique"
    contracted_power_kva: float = 9.0
    has_solar_panels: bool = False
    has_ev: bool = False
    city: str = "Paris"
    monthly_budget_eur: float = 120.0


class HomeCreate(HomeBase):
    owner_id: int


class HomeUpdate(BaseModel):
    name: str | None = None
    dpe: str | None = None
    occupants_count: int | None = None
    heating_type: str | None = None
    monthly_budget_eur: float | None = None
    has_solar_panels: bool | None = None
    has_ev: bool | None = None


class HomeOut(HomeBase):
    model_config = ORM
    id: int
    owner_id: int


# --------------------------------------------------------------------------- #
# Room
# --------------------------------------------------------------------------- #
class RoomBase(BaseModel):
    name: str
    room_type: str
    surface_m2: float = 12.0
    floor: int = 0
    usual_occupants: int = 1
    target_temperature: float = 20.0


class RoomCreate(RoomBase):
    home_id: int


class RoomOut(RoomBase):
    model_config = ORM
    id: int
    home_id: int


class RoomConsumptionOut(RoomOut):
    """Pièce enrichie de sa consommation agrégée et de son niveau (vert/orange/rouge)."""
    consumption_kwh: float = 0.0
    cost_eur: float = 0.0
    share_pct: float = 0.0
    level: str = "vert"  # vert | orange | rouge
    equipment_count: int = 0


# --------------------------------------------------------------------------- #
# Equipment
# --------------------------------------------------------------------------- #
class EquipmentBase(BaseModel):
    name: str
    equipment_type: str
    rated_power_w: float = 100.0
    daily_usage_hours: float = 2.0
    is_active: bool = True
    criticality: int = Field(default=2, ge=1, le=5)


class EquipmentCreate(EquipmentBase):
    home_id: int
    room_id: int


class EquipmentUpdate(BaseModel):
    is_active: bool | None = None
    daily_usage_hours: float | None = None
    criticality: int | None = Field(default=None, ge=1, le=5)


class EquipmentOut(EquipmentBase):
    model_config = ORM
    id: int
    home_id: int
    room_id: int
    estimated_kwh_month: float = 0.0  # calculé : puissance × usage × 30


# --------------------------------------------------------------------------- #
# Consumption
# --------------------------------------------------------------------------- #
class ConsumptionPoint(BaseModel):
    """Point agrégé d'une série temporelle (jour / heure / mois)."""
    period: str
    consumption_kwh: float
    cost_eur: float
    co2_kg: float = 0.0


class ConsumptionSeriesOut(BaseModel):
    granularity: str  # hourly | daily | weekly | monthly
    points: list[ConsumptionPoint]


# --------------------------------------------------------------------------- #
# KPI
# --------------------------------------------------------------------------- #
class KpiOut(BaseModel):
    code: str
    label: str
    value: float
    unit: str = ""


# --------------------------------------------------------------------------- #
# Prediction
# --------------------------------------------------------------------------- #
class PredictionPoint(BaseModel):
    date: str
    value: float


class PredictionOut(BaseModel):
    kind: str
    value: float
    unit: str
    model_name: str
    metrics: dict | None = None
    detail: list[PredictionPoint] | None = None


class PredictionBundle(BaseModel):
    """Réponse complète de /api/predictions/{home_id}."""
    consumption_j1_kwh: float
    consumption_j7_kwh: float
    monthly_bill_eur: float
    budget_eur: float
    budget_overrun_risk: float  # 0..1
    model_name: str
    metrics: dict
    forecast_curve: list[PredictionPoint]   # réel récent + prévision
    history_curve: list[PredictionPoint]


# --------------------------------------------------------------------------- #
# Alert
# --------------------------------------------------------------------------- #
class AlertOut(BaseModel):
    model_config = ORM
    id: int
    home_id: int
    room_id: int | None
    equipment_id: int | None
    category: str
    title: str
    description: str
    level: str
    recommendation: str
    detected_at: datetime
    is_resolved: bool


# --------------------------------------------------------------------------- #
# Recommendation
# --------------------------------------------------------------------------- #
class RecommendationOut(BaseModel):
    model_config = ORM
    id: int
    home_id: int
    room_id: int | None
    code: str
    action: str
    gain_eur_month: float
    gain_kwh_month: float
    co2_avoided_kg_month: float
    impact: str
    difficulty: str


# --------------------------------------------------------------------------- #
# Simulation
# --------------------------------------------------------------------------- #
class SimulationRequest(BaseModel):
    scenario: str  # baisser_chauffage | heures_creuses | panneaux_solaires | reduire_nocturne
    params: dict = Field(default_factory=dict)


class SimulationOut(BaseModel):
    scenario: str
    params: dict
    baseline_kwh_month: float
    simulated_kwh_month: float
    saving_kwh_month: float
    saving_eur_month: float
    co2_avoided_kg_month: float
    saving_pct: float
    explanation: str


# --------------------------------------------------------------------------- #
# Dashboard
# --------------------------------------------------------------------------- #
class DashboardOut(BaseModel):
    home: HomeOut
    kpis: list[KpiOut]
    consumption_today_kwh: float
    consumption_daily: list[ConsumptionPoint]
    consumption_weekly: list[ConsumptionPoint]
    consumption_monthly: list[ConsumptionPoint]
    predictions: PredictionBundle
    top_rooms: list[RoomConsumptionOut]
    recent_alerts: list[AlertOut]
    quick_recommendations: list[RecommendationOut]
