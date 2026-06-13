"""Résultats de KPI calculés et historisés (snapshot)."""
from datetime import datetime

from sqlalchemy import String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class KpiResult(Base):
    __tablename__ = "kpi_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    home_id: Mapped[int] = mapped_column(ForeignKey("homes.id", ondelete="CASCADE"), index=True)

    # code : conso_totale, conso_par_occupant, chauffage_pct, hp_hc_pct, autonomie_pct,
    #        facture_estimee, economie_potentielle, co2_emis, green_score, anomaly_score, waste_score...
    code: Mapped[str] = mapped_column(String(40), index=True)
    label: Mapped[str] = mapped_column(String(80))
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(16), default="")

    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
