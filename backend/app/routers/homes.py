"""Routes /api/homes — gestion des logements."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.schemas import HomeOut, HomeCreate, HomeUpdate
from app.routers.deps import get_home_or_404

router = APIRouter(prefix="/api/homes", tags=["homes"])


@router.get("", response_model=list[HomeOut])
def list_homes(db: Session = Depends(get_db)):
    return db.query(models.Home).order_by(models.Home.id).all()


@router.get("/{home_id}", response_model=HomeOut)
def get_home(home_id: int, db: Session = Depends(get_db)):
    return get_home_or_404(home_id, db)


@router.post("", response_model=HomeOut, status_code=201)
def create_home(payload: HomeCreate, db: Session = Depends(get_db)):
    if db.get(models.User, payload.owner_id) is None:
        raise HTTPException(status_code=404, detail="Propriétaire introuvable")
    home = models.Home(**payload.model_dump())
    db.add(home)
    db.commit()
    db.refresh(home)
    return home


@router.patch("/{home_id}", response_model=HomeOut)
def update_home(home_id: int, payload: HomeUpdate, db: Session = Depends(get_db)):
    home = get_home_or_404(home_id, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(home, field, value)
    db.commit()
    db.refresh(home)
    return home
