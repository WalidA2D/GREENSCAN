"""Routes /api/predictions — prévisions IA (J+1, J+7, facture, risque budget)."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import PredictionBundle
from app.ml.predictor import predict_bundle
from app.routers.deps import resolve_home_id

router = APIRouter(prefix="/api/predictions", tags=["predictions"])


@router.get("", response_model=PredictionBundle)
def get_predictions(home_id: int = Depends(resolve_home_id),
                    horizon: int = Query(7, ge=1, le=14),
                    db: Session = Depends(get_db)):
    """Prévisions de consommation et de facture (modèle entraîné ou fallback)."""
    return predict_bundle(db, home_id, horizon=horizon)
