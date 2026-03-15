from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import models, schemas
from database import get_db

router = APIRouter()

@router.get("/", response_model=List[schemas.NotificationOut])
def read_notifications(unread_only: bool = False, db: Session = Depends(get_db)):
    # In a real app, we'd filter by current_user.id
    # For MVP, we'll assume User ID 1 is the active user
    query = db.query(models.Notification).filter(models.Notification.user_id == 1)
    if unread_only:
        query = query.filter(models.Notification.is_read == 0)
    
    return query.order_by(models.Notification.created_at.desc()).all()

@router.put("/{notification_id}/read", response_model=schemas.NotificationOut)
def mark_read(notification_id: int, db: Session = Depends(get_db)):
    db_notif = db.query(models.Notification).filter(models.Notification.id == notification_id).first()
    if not db_notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    db_notif.is_read = 1
    db.commit()
    db.refresh(db_notif)
    return db_notif

@router.put("/read-all")
def mark_all_read(db: Session = Depends(get_db)):
    db.query(models.Notification).filter(models.Notification.user_id == 1, models.Notification.is_read == 0).update({"is_read": 1})
    db.commit()
    return {"message": "All marked as read"}

@router.get("/user/preferences", response_model=schemas.UserOut)
def get_user_preferences(db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == 1).first()
    if not user:
        # Create default user if not exists for MVP demo
        user = models.User(name="Admin", email="admin@hospital.com", role=models.UserRole.technician, email_alerts_enabled=1)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

@router.put("/user/preferences")
def update_preferences(enabled: bool, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == 1).first()
    if not user:
         raise HTTPException(status_code=404, detail="User not found")
    
    user.email_alerts_enabled = 1 if enabled else 0
    db.commit()
    return {"status": "success", "email_alerts_enabled": user.email_alerts_enabled}
