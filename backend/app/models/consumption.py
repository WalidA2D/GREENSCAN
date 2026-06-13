"""Mesure de consommation (granularité 30 min, source Linky).

Table de série temporelle. Les clés room_id / equipment_id sont optionnelles :
- niveau logement  : room_id=NULL, equipment_id=NULL
- ventilation pièce : room_id renseigné
"""
from datetime import datetime

from sqlalchemy import Integer, Float, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ConsumptionRecord(Base):
    __tablename__ = "consumption_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    home_id: Mapped[int] = mapped_column(ForeignKey("homes.id", ondelete="CASCADE"), index=True)
    room_id: Mapped[int | None] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"), nullable=True)
    equipment_id: Mapped[int | None] = mapped_column(
        ForeignKey("equipments.id", ondelete="CASCADE"), nullable=True
    )

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    energy_consumption_kwh: Mapped[float] = mapped_column(Float)
    energy_cost_eur: Mapped[float] = mapped_column(Float, default=0.0)
    # tariff_type : HP (heures pleines) / HC (heures creuses)
    tariff_type: Mapped[str] = mapped_column(String(2), default="HP")

    # Sous-postes (renseignés au niveau logement).
    heating_consumption_kwh: Mapped[float] = mapped_column(Float, default=0.0)
    solar_production_kwh: Mapped[float] = mapped_column(Float, default=0.0)
    ev_charging_kwh: Mapped[float] = mapped_column(Float, default=0.0)

    # Contexte comportemental.
    occupants_present: Mapped[int] = mapped_column(Integer, default=0)
    home_presence: Mapped[bool] = mapped_column(Boolean, default=True)
    co2_kg: Mapped[float] = mapped_column(Float, default=0.0)

    home: Mapped["Home"] = relationship(back_populates="consumption_records")
    room: Mapped["Room"] = relationship(back_populates="consumption_records")


# Index composite pour accélérer les requêtes "logement sur une période".
Index("ix_consumption_home_ts", ConsumptionRecord.home_id, ConsumptionRecord.timestamp)
