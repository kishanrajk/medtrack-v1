from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from database import SessionLocal
import models
from services import notifications
from datetime import date, timedelta

def check_maintenance_alerts():
    db = SessionLocal()
    try:
        today = date.today()
        seven_days_out = today + timedelta(days=7)
        
        # 1. Check Upcoming (Exactly 7 days away)
        upcoming = db.query(models.Equipment).filter(
            models.Equipment.next_maintenance_date == seven_days_out,
            models.Equipment.status != models.EquipmentStatus.retired
        ).all()
        
        for eq in upcoming:
            notifications.notify_all_technicians(
                db,
                title="Upcoming Maintenance",
                message=f"Equipment {eq.name} ({eq.asset_id}) is due for maintenance in 7 days ({eq.next_maintenance_date}).",
                notif_type=models.NotificationType.upcoming_maintenance,
                equipment_id=eq.id
            )

        # 2. Check Overdue (Passed today)
        overdue = db.query(models.Equipment).filter(
            models.Equipment.next_maintenance_date < today,
            models.Equipment.status != models.EquipmentStatus.retired
        ).all()

        for eq in overdue:
            # Avoid duplicate alerts - check if we already notified for overdue in the last 24h or simple check
            # For MVP, we'll just check if there's an unread "overdue" notification for this equip
            existing = db.query(models.Notification).filter(
                models.Notification.equipment_id == eq.id,
                models.Notification.type == models.NotificationType.overdue_maintenance,
                models.Notification.is_read == 0
            ).first()
            
            if not existing:
                notifications.notify_all_technicians(
                    db,
                    title="OVERDUE Maintenance",
                    message=f"CRITICAL: Equipment {eq.name} ({eq.asset_id}) missed its maintenance date ({eq.next_maintenance_date})!",
                    notif_type=models.NotificationType.overdue_maintenance,
                    equipment_id=eq.id
                )

    finally:
        db.close()

def start_scheduler():
    scheduler = BackgroundScheduler()
    # In production this would be 'cron', but for demo/testing let's check every hour or minute
    scheduler.add_job(check_maintenance_alerts, 'interval', minutes=60) 
    # Also run once on startup
    check_maintenance_alerts()
    scheduler.start()
