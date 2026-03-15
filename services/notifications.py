from sqlalchemy.orm import Session
import models
from datetime import datetime

def create_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    notif_type: models.NotificationType,
    equipment_id: int = None,
    reference_id: int = None
):
    db_notification = models.Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=notif_type,
        equipment_id=equipment_id,
        reference_id=reference_id
    )
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    
    # Mock Notifications
    send_mock_email(db, user_id, title, message)
    send_mock_whatsapp(db, user_id, message)
    
    return db_notification

def send_mock_email(db: Session, user_id: int, title: str, message: str):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user and user.email_alerts_enabled == 1:
        print(f"\n--- [MOCK EMAIL SENT] ---")
        print(f"To: {user.email}")
        print(f"Subject: {title}")
        print(f"Body: {message}")
        print(f"-------------------------\n")

def send_mock_whatsapp(db: Session, user_id: int, message: str):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user and user.whatsapp_alerts_enabled == 1 and user.phone_number:
        print(f"\n--- [MOCK WHATSAPP SENT] ---")
        print(f"To: {user.phone_number}")
        print(f"Message: {message}")
        print(f"----------------------------\n")

def notify_all_technicians(
    db: Session,
    title: str,
    message: str,
    notif_type: models.NotificationType,
    equipment_id: int = None,
    reference_id: int = None
):
    technicians = db.query(models.User).filter(models.User.role == models.UserRole.technician).all()
    for tech in technicians:
        create_notification(db, tech.id, title, message, notif_type, equipment_id, reference_id)
