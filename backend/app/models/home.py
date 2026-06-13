"""Logement. Attributs issus du patrimoine (type_logement, DPE, orientation...)."""
from sqlalchemy import String, Integer, Float, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Home(Base):
    __tablename__ = "homes"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    name: Mapped[str] = mapped_column(String(120))
    # type_logement : studio, appartement, maison
    home_type: Mapped[str] = mapped_column(String(40))
    surface_m2: Mapped[float] = mapped_column(Float)
    construction_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # DPE : performance énergétique (A..G)
    dpe: Mapped[str] = mapped_column(String(2), default="D")
    orientation: Mapped[str | None] = mapped_column(String(20), nullable=True)  # sud, nord, est, ouest
    occupants_count: Mapped[int] = mapped_column(Integer, default=2)

    # type_chauffage : gaz, PAC (pompe à chaleur), électrique
    heating_type: Mapped[str] = mapped_column(String(30), default="électrique")
    contracted_power_kva: Mapped[float] = mapped_column(Float, default=9.0)
    has_solar_panels: Mapped[bool] = mapped_column(Boolean, default=False)
    has_ev: Mapped[bool] = mapped_column(Boolean, default=False)

    city: Mapped[str] = mapped_column(String(80), default="Paris")
    # Budget mensuel cible (€) pour le KPI "risque de dépassement budget".
    monthly_budget_eur: Mapped[float] = mapped_column(Float, default=120.0)

    owner: Mapped["User"] = relationship(back_populates="homes")
    rooms: Mapped[list["Room"]] = relationship(back_populates="home", cascade="all, delete-orphan")
    equipments: Mapped[list["Equipment"]] = relationship(back_populates="home", cascade="all, delete-orphan")
    consumption_records: Mapped[list["ConsumptionRecord"]] = relationship(
        back_populates="home", cascade="all, delete-orphan"
    )
    weather_records: Mapped[list["WeatherRecord"]] = relationship(
        back_populates="home", cascade="all, delete-orphan"
    )
