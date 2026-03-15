from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date, timedelta
import models, schemas
from database import get_db

router = APIRouter()

@router.get("/", response_model=List[schemas.EquipmentOut])
def read_equipment(skip: int = 0, limit: int = 100, status: str = None, department: str = None, db: Session = Depends(get_db)):
    query = db.query(models.Equipment)
    if status:
        query = query.filter(models.Equipment.status == status)
    if department:
        query = query.filter(models.Equipment.department == department)
        
    equipment = query.offset(skip).limit(limit).all()
    return equipment

@router.post("/", response_model=schemas.EquipmentOut)
def create_equipment(equipment: schemas.EquipmentCreate, db: Session = Depends(get_db)):
    # Check if asset_id or serial_number exists
    db_asset = db.query(models.Equipment).filter(models.Equipment.asset_id == equipment.asset_id).first()
    if db_asset:
        raise HTTPException(status_code=400, detail="Asset ID already registered")
        
    db_serial = db.query(models.Equipment).filter(models.Equipment.serial_number == equipment.serial_number).first()
    if db_serial:
        raise HTTPException(status_code=400, detail="Serial Number already registered")

    # Auto-calculate next maintenance date
    next_maint = date.today() + timedelta(days=equipment.maintenance_frequency_days)
    
    db_equipment = models.Equipment(**equipment.model_dump(), next_maintenance_date=next_maint)
    db.add(db_equipment)
    db.commit()
    db.refresh(db_equipment)
    return db_equipment

@router.get("/{equipment_id}", response_model=schemas.EquipmentDetail)
def read_equipment_detail(equipment_id: int, db: Session = Depends(get_db)):
    equipment = db.query(models.Equipment).filter(models.Equipment.id == equipment_id).first()
    if equipment is None:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return equipment

@router.put("/{equipment_id}", response_model=schemas.EquipmentOut)
def update_equipment(equipment_id: int, equipment_update: schemas.EquipmentUpdate, db: Session = Depends(get_db)):
    db_equipment = db.query(models.Equipment).filter(models.Equipment.id == equipment_id).first()
    if not db_equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
        
    update_data = equipment_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_equipment, key, value)
        
    db.commit()
    db.refresh(db_equipment)
    return db_equipment
