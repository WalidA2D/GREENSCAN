"""Scénarios de simulation "what-if" et leurs résultats."""
from datetime import datetime

from sqlalchemy import String, Float, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Simulation(Base):
    __tablename__ = "simulations"

    id: Mapped[int] = mapped_column(primary_key=True)
    home_id: Mapped[int] = mapped_column(ForeignKey("homes.id", ondelete="CASCADE"), index=True)

    # scenario : baisser_chauffage, heures_creuses, panneaux_solaires, reduire_nocturne
    scenario: Mapped[str] = mapped_column(String(40), index=True)
    # Paramètres d'entrée du scénario (ex : {"delta_temp": 1}).
    params: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    baseline_kwh_month: Mapped[float] = mapped_column(Float, default=0.0)
    simulated_kwh_month: Mapped[float] = mapped_column(Float, default=0.0)
    saving_eur_month: Mapped[float] = mapped_column(Float, default=0.0)
    saving_kwh_month: Mapped[float] = mapped_column(Float, default=0.0)
    co2_avoided_kg_month: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
