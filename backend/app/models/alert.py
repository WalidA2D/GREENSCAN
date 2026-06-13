"""Alertes intelligentes détectées sur les données."""
from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    home_id: Mapped[int] = mapped_column(ForeignKey("homes.id", ondelete="CASCADE"), index=True)
    room_id: Mapped[int | None] = mapped_column(ForeignKey("rooms.id", ondelete="SET NULL"), nullable=True)
    equipment_id: Mapped[int | None] = mapped_column(
        ForeignKey("equipments.id", ondelete="SET NULL"), nullable=True
    )

    # category : surconsommation, conso_nocturne, chauffage_fenetre, equipement_energivore,
    #            au_dessus_moyenne, derive_consommation
    category: Mapped[str] = mapped_column(String(40), index=True)
    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text)
    # level : info, warning, critical
    level: Mapped[str] = mapped_column(String(10), default="info", index=True)
    recommendation: Mapped[str] = mapped_column(Text, default="")

    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
