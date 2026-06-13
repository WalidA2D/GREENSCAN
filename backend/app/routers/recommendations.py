"""Routes /api/recommendations — conseils personnalisés chiffrés."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.schemas import RecommendationOut
from app.domain.recommendations_engine import compute_recommendations
from app.routers.deps import resolve_home_id, get_home_or_404

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


@router.get("", response_model=list[RecommendationOut])
def list_recommendations(home_id: int = Depends(resolve_home_id), db: Session = Depends(get_db)):
    return db.query(models.Recommendation).filter(
        models.Recommendation.home_id == home_id).order_by(
        models.Recommendation.gain_eur_month.desc()).all()


@router.post("/refresh", response_model=list[RecommendationOut])
def refresh_recommendations(home_id: int = Depends(resolve_home_id), db: Session = Depends(get_db)):
    """Régénère les recommandations à partir des données récentes."""
    home = get_home_or_404(home_id, db)
    db.query(models.Recommendation).filter(models.Recommendation.home_id == home_id).delete()
    recos = compute_recommendations(db, home)
    for r in recos:
        db.add(r)
    db.commit()
    return db.query(models.Recommendation).filter(
        models.Recommendation.home_id == home_id).order_by(
        models.Recommendation.gain_eur_month.desc()).all()
