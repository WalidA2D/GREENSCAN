"""Dépendances partagées des routers."""
from fastapi import Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models
from app.database import get_db


def resolve_home_id(home_id: int | None = Query(default=None), db: Session = Depends(get_db)) -> int:
    """Retourne le home_id demandé, ou le premier logement disponible par défaut.

    Permet d'appeler les endpoints sans préciser home_id en mode démo mono-foyer.
    """
    if home_id is not None:
        if db.get(models.Home, home_id) is None:
            raise HTTPException(status_code=404, detail=f"Logement {home_id} introuvable")
        return home_id
    first = db.query(models.Home.id).order_by(models.Home.id).first()
    if first is None:
        raise HTTPException(status_code=404, detail="Aucun logement. Lancez scripts.generate_data.")
    return first[0]


def get_home_or_404(home_id: int, db: Session) -> models.Home:
    home = db.get(models.Home, home_id)
    if home is None:
        raise HTTPException(status_code=404, detail=f"Logement {home_id} introuvable")
    return home
