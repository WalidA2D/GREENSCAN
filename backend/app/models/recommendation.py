"""Conseils personnalisés générés par le moteur de recommandations."""
from datetime import datetime

from sqlalchemy import String, Text, Float, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(primary_key=True)
    home_id: Mapped[int] = mapped_column(ForeignKey("homes.id", ondelete="CASCADE"), index=True)
    room_id: Mapped[int | None] = mapped_column(ForeignKey("rooms.id", ondelete="SET NULL"), nullable=True)

    # code : baisser_chauffage, heures_creuses, conso_nocturne, comparaison_piece, panneaux_solaires...
    code: Mapped[str] = mapped_column(String(40), index=True)
    action: Mapped[str] = mapped_column(Text)               # action conseillée
    gain_eur_month: Mapped[float] = mapped_column(Float, default=0.0)   # gain estimé (€/mois)
    gain_kwh_month: Mapped[float] = mapped_column(Float, default=0.0)   # gain estimé (kWh/mois)
    co2_avoided_kg_month: Mapped[float] = mapped_column(Float, default=0.0)  # CO2 évité (kg/mois)
    # impact : faible, moyen, élevé   |   difficulty : facile, moyen, difficile
    impact: Mapped[str] = mapped_column(String(10), default="moyen")
    difficulty: Mapped[str] = mapped_column(String(10), default="facile")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
