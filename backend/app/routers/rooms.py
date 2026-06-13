"""Routes /api/rooms — pièces et consommation par pièce."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.schemas import RoomOut, RoomCreate, RoomConsumptionOut
from app.services.analytics import rooms_consumption
from app.routers.deps import resolve_home_id

router = APIRouter(prefix="/api/rooms", tags=["rooms"])


@router.get("", response_model=list[RoomConsumptionOut])
def list_rooms(home_id: int = Depends(resolve_home_id), days: int = Query(30, ge=1, le=365),
               db: Session = Depends(get_db)):
    """Pièces du logement enrichies de leur consommation et de leur niveau (vert/orange/rouge)."""
    return rooms_consumption(db, home_id, days=days)


@router.get("/{room_id}", response_model=RoomOut)
def get_room(room_id: int, db: Session = Depends(get_db)):
    room = db.get(models.Room, room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="Pièce introuvable")
    return room


@router.post("", response_model=RoomOut, status_code=201)
def create_room(payload: RoomCreate, db: Session = Depends(get_db)):
    if db.get(models.Home, payload.home_id) is None:
        raise HTTPException(status_code=404, detail="Logement introuvable")
    room = models.Room(**payload.model_dump())
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


@router.delete("/{room_id}", status_code=204)
def delete_room(room_id: int, db: Session = Depends(get_db)):
    room = db.get(models.Room, room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="Pièce introuvable")
    db.delete(room)
    db.commit()
