from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date, timedelta
import models, schemas
from database import get_db

router = APIRouter()

@router.get("/upcoming", response_model=List[schemas.EquipmentOut])
def get_upcoming_maintenance(days: int = 30, db: Session = Depends(get_db)):
    """Get equipment with maintenance due in the next X days."""
    target_date = date.today() + timedelta(days=days)
    equipment = db.query(models.Equipment).filter(
        models.Equipment.next_maintenance_date <= target_date,
        models.Equipment.status != models.EquipmentStatus.retired
    ).order_by(models.Equipment.next_maintenance_date.asc()).all()
    return equipment

@router.get("/equipment/{equipment_id}", response_model=List[schemas.MaintenanceOut])
def get_equipment_maintenance(equipment_id: int, db: Session = Depends(get_db)):
    records = db.query(models.MaintenanceRecord).filter(models.MaintenanceRecord.equipment_id == equipment_id).order_by(models.MaintenanceRecord.maintenance_date.desc()).all()
    return records

@router.post("/equipment/{equipment_id}", response_model=schemas.MaintenanceOut)
def log_maintenance(equipment_id: int, record: schemas.MaintenanceCreate, db: Session = Depends(get_db)):
    equipment = db.query(models.Equipment).filter(models.Equipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
        
    db_record = models.MaintenanceRecord(**record.model_dump(), equipment_id=equipment_id)
    db.add(db_record)
    
    # Auto-update next maintenance date on equipment if completed
    if record.status == models.MaintenanceStatus.completed:
        equipment.next_maintenance_date = record.maintenance_date + timedelta(days=equipment.maintenance_frequency_days)
    
    db.commit()
    db.refresh(db_record)
    return db_record
