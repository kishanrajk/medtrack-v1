from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date
import models, schemas
from database import get_db
from services import notifications

router = APIRouter()

@router.get("/", response_model=List[schemas.RepairOut])
def get_all_active_repairs(db: Session = Depends(get_db)):
    records = db.query(models.RepairRecord).filter(
        models.RepairRecord.status.in_([models.RepairStatus.reported, models.RepairStatus.in_progress])
    ).order_by(models.RepairRecord.repair_date.desc()).all()
    return records

@router.post("/equipment/{equipment_id}", response_model=schemas.RepairOut)
def report_repair(equipment_id: int, record: schemas.RepairCreate, db: Session = Depends(get_db)):
    equipment = db.query(models.Equipment).filter(models.Equipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
        
    db_record = models.RepairRecord(**record.model_dump(), equipment_id=equipment_id)
    db.add(db_record)
    
    # Auto-change equipment status to under repair
    equipment.status = models.EquipmentStatus.under_repair
    
    db.commit()
    db.refresh(db_record)

    # Trigger Notification
    notifications.notify_all_technicians(
        db,
        title="New Repair Ticket",
        message=f"Equipment {equipment.name} ({equipment.asset_id}) reported: {record.issue_description}",
        notif_type=models.NotificationType.new_repair,
        equipment_id=equipment.id,
        reference_id=db_record.id
    )
    
    return db_record

@router.put("/{repair_id}", response_model=schemas.RepairOut)
def update_repair(repair_id: int, update_data: schemas.RepairUpdate, db: Session = Depends(get_db)):
    db_record = db.query(models.RepairRecord).filter(models.RepairRecord.id == repair_id).first()
    if not db_record:
        raise HTTPException(status_code=404, detail="Repair record not found")
        
    data = update_data.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(db_record, key, value)
        
    # If resolved, set equipment back to active (if it was under repair)
    if 'status' in data and data['status'] == models.RepairStatus.resolved:
        equipment = db.query(models.Equipment).filter(models.Equipment.id == db_record.equipment_id).first()
        if equipment and equipment.status == models.EquipmentStatus.under_repair:
            equipment.status = models.EquipmentStatus.active
            
    db.commit()
    db.refresh(db_record)

    # Trigger Notification for status change
    equipment = db.query(models.Equipment).filter(models.Equipment.id == db_record.equipment_id).first()
    notifications.notify_all_technicians(
        db,
        title="Repair Update",
        message=f"Repair for {equipment.name} is now: {db_record.status.replace('_', ' ')}",
        notif_type=models.NotificationType.repair_update,
        equipment_id=equipment.id,
        reference_id=db_record.id
    )

    return db_record
