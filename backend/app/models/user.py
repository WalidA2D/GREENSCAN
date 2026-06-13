"""Utilisateur / foyer propriétaire des logements."""
from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    # Profil comportemental utilisé pour la génération de données / segmentation.
    profile: Mapped[str] = mapped_column(String(40), default="standard")  # eco, standard, energivore
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    homes: Mapped[list["Home"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
