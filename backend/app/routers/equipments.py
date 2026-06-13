"""Routes /api/equipments — équipements par pièce."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.schemas import EquipmentOut, EquipmentCreate, EquipmentUpdate
from app.services.analytics import equipment_estimated_kwh_month
from app.routers.deps import resolve_home_id

router = APIRouter(prefix="/api/equipments", tags=["equipments"])


def _to_out(e: models.Equipment) -> EquipmentOut:
    out = EquipmentOut.model_validate(e)
    out.estimated_kwh_month = equipment_estimated_kwh_month(e)
    return out


@router.get("", response_model=list[EquipmentOut])
def list_equipments(home_id: int = Depends(resolve_home_id),
                    room_id: int | None = Query(default=None),
                    db: Session = Depends(get_db)):
    q = db.query(models.Equipment).filter(models.Equipment.home_id == home_id)
    if room_id is not None:
        q = q.filter(models.Equipment.room_id == room_id)
    return [_to_out(e) for e in q.order_by(models.Equipment.criticality.desc()).all()]


@router.post("", response_model=EquipmentOut, status_code=201)
def create_equipment(payload: EquipmentCreate, db: Session = Depends(get_db)):
    if db.get(models.Room, payload.room_id) is None:
        raise HTTPException(status_code=404, detail="Pièce introuvable")
    equip = models.Equipment(**payload.model_dump())
    db.add(equip)
    db.commit()
    db.refresh(equip)
    return _to_out(equip)


@router.patch("/{equipment_id}", response_model=EquipmentOut)
def update_equipment(equipment_id: int, payload: EquipmentUpdate, db: Session = Depends(get_db)):
    equip = db.get(models.Equipment, equipment_id)
    if equip is None:
        raise HTTPException(status_code=404, detail="Équipement introuvable")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(equip, field, value)
    db.commit()
    db.refresh(equip)
    return _to_out(equip)


@router.delete("/{equipment_id}", status_code=204)
def delete_equipment(equipment_id: int, db: Session = Depends(get_db)):
    equip = db.get(models.Equipment, equipment_id)
    if equip is None:
        raise HTTPException(status_code=404, detail="Équipement introuvable")
    db.delete(equip)
    db.commit()
