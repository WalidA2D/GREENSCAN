"""Prédictions IA persistées (J+1, J+7, facture mensuelle...)."""
from datetime import datetime

from sqlalchemy import Float, String, DateTime, ForeignKey, func, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(primary_key=True)
    home_id: Mapped[int] = mapped_column(ForeignKey("homes.id", ondelete="CASCADE"), index=True)

    # kind : predicted_consumption_24h, predicted_consumption_7d, predicted_monthly_bill
    kind: Mapped[str] = mapped_column(String(40), index=True)
    target_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(10), default="kWh")

    model_name: Mapped[str] = mapped_column(String(40), default="RandomForest")
    # Métriques d'évaluation du modèle (MAE, RMSE, MAPE, R2) au moment de l'entraînement.
    metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Courbe détaillée (ex : 7 points pour J+7) sérialisée.
    detail: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
