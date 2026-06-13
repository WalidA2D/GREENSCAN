"""Équipement énergétique rattaché à une pièce."""
from sqlalchemy import String, Integer, Float, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Equipment(Base):
    __tablename__ = "equipments"

    id: Mapped[int] = mapped_column(primary_key=True)
    home_id: Mapped[int] = mapped_column(ForeignKey("homes.id", ondelete="CASCADE"), index=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"), index=True)

    name: Mapped[str] = mapped_column(String(80))
    # equipment_type : chauffage, television, ordinateur, four, refrigerateur, lave_linge,
    # eclairage, chauffe_eau, borne_ve, pompe_a_chaleur, panneaux_solaires, climatisation
    equipment_type: Mapped[str] = mapped_column(String(40))
    rated_power_w: Mapped[float] = mapped_column(Float, default=100.0)  # puissance estimée (W)
    # Heures d'utilisation moyennes par jour (fréquence d'utilisation).
    daily_usage_hours: Mapped[float] = mapped_column(Float, default=2.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # Niveau de criticité énergétique : 1 (faible) .. 5 (très énergivore).
    criticality: Mapped[int] = mapped_column(Integer, default=2)

    home: Mapped["Home"] = relationship(back_populates="equipments")
    room: Mapped["Room"] = relationship(back_populates="equipments")
