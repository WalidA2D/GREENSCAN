"""Relevé météo horaire (source API météo)."""
from datetime import datetime

from sqlalchemy import Float, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class WeatherRecord(Base):
    __tablename__ = "weather_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    home_id: Mapped[int] = mapped_column(ForeignKey("homes.id", ondelete="CASCADE"), index=True)

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    outdoor_temperature: Mapped[float] = mapped_column(Float)
    humidity: Mapped[float] = mapped_column(Float, default=60.0)
    wind_speed: Mapped[float] = mapped_column(Float, default=10.0)
    solar_radiation: Mapped[float] = mapped_column(Float, default=0.0)
    cloud_cover: Mapped[float] = mapped_column(Float, default=50.0)
    weather_condition: Mapped[str] = mapped_column(String(20), default="nuageux")

    home: Mapped["Home"] = relationship(back_populates="weather_records")
