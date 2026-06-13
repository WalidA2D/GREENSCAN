"""Pièce d'un logement. Structure RELATIONNELLE dynamique (pas de colonne par pièce)."""
from sqlalchemy import String, Integer, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(primary_key=True)
    home_id: Mapped[int] = mapped_column(ForeignKey("homes.id", ondelete="CASCADE"), index=True)

    name: Mapped[str] = mapped_column(String(80))
    # room_type : salon, cuisine, chambre, salle_de_bain, garage, cave, bureau, piece_principale...
    room_type: Mapped[str] = mapped_column(String(40))
    surface_m2: Mapped[float] = mapped_column(Float, default=12.0)
    floor: Mapped[int] = mapped_column(Integer, default=0)
    usual_occupants: Mapped[int] = mapped_column(Integer, default=1)
    target_temperature: Mapped[float] = mapped_column(Float, default=20.0)

    home: Mapped["Home"] = relationship(back_populates="rooms")
    equipments: Mapped[list["Equipment"]] = relationship(
        back_populates="room", cascade="all, delete-orphan"
    )
    consumption_records: Mapped[list["ConsumptionRecord"]] = relationship(back_populates="room")
