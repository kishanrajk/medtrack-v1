import datetime
import models
import auth_utils
from database import SessionLocal, engine

def seed_db():
    print("--- Seeding Process Started ---")
    # Create tables
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # 1. Add Users (Skip if requested, but let's ensure admin exists)
        if not db.query(models.User).filter(models.User.email == "admin@hospital.com").first():
            print("Seeding admin user...")
            admin = models.User(
                name="Admin User",
                email="admin@hospital.com",
                role=models.UserRole.admin,
                password_hash=auth_utils.get_password_hash("admin123"),
                phone_number="+919876543210"
            )
            db.add(admin)
            db.commit()

        # 2. Add Equipment (Check by Asset ID to avoid duplicates)
        print("Seeding diverse equipment...")
        today = datetime.date.today()
        
        equipment_data = [
            {"name": "X-Ray Machine", "asset_id": "XR-001", "manufacturer": "GE", "model": "Optima", "department": "Radiology", "status": models.EquipmentStatus.active, "m_days": 180},
            {"name": "Ventilator", "asset_id": "VNT-002", "manufacturer": "Dräger", "model": "Evita", "department": "ICU", "status": models.EquipmentStatus.active, "m_days": 90},
            {"name": "MRI Scanner", "asset_id": "MRI-003", "manufacturer": "Siemens", "model": "MAG", "department": "Radiology", "status": models.EquipmentStatus.under_repair, "m_days": 365},
            {"name": "Defibrillator", "asset_id": "DEF-004", "manufacturer": "Zoll", "model": "R Series", "department": "ER", "status": models.EquipmentStatus.active, "m_days": 30},
            {"name": "Patient Monitor", "asset_id": "MON-005", "manufacturer": "Philips", "model": "IntelliVue", "department": "ICU", "status": models.EquipmentStatus.active, "m_days": 180},
            {"name": "CT Scanner", "asset_id": "CT-006", "manufacturer": "Canon", "model": "Aquilion", "department": "Radiology", "status": models.EquipmentStatus.active, "m_days": 180},
            {"name": "Infusion Pump", "asset_id": "PMP-007", "manufacturer": "B. Braun", "model": "Infusomat", "department": "General Ward", "status": models.EquipmentStatus.retired, "m_days": 365},
            {"name": "Ultrasound", "asset_id": "ULT-008", "manufacturer": "Samsung", "model": "RS85", "department": "Diagnostics", "status": models.EquipmentStatus.active, "m_days": 180},
            {"name": "ECG Machine", "asset_id": "ECG-009", "manufacturer": "Schiller", "model": "CardioVit", "department": "Cardiology", "status": models.EquipmentStatus.active, "m_days": 90},
            {"name": "Anesthesia Workstation", "asset_id": "ANS-010", "manufacturer": "GE", "model": "Avance", "department": "OT", "status": models.EquipmentStatus.active, "m_days": 90},
            {"name": "Surgical Laser", "asset_id": "LSR-011", "manufacturer": "Lumenis", "model": "AcuPulse", "department": "Surgery", "status": models.EquipmentStatus.active, "m_days": 180},
            {"name": "Blood Gas Analyzer", "asset_id": "BGA-012", "manufacturer": "Radiometer", "model": "ABL90", "department": "Lab", "status": models.EquipmentStatus.active, "m_days": 90}
        ]

        inserted_eqs = []
        for i, eq in enumerate(equipment_data):
            existing = db.query(models.Equipment).filter(models.Equipment.asset_id == eq["asset_id"]).first()
            if not existing:
                m_date = today + datetime.timedelta(days=(i * 10) - 20)
                new_eq = models.Equipment(
                    name=eq["name"],
                    asset_id=eq["asset_id"],
                    serial_number=f"SN-SYS-{eq['asset_id']}",
                    manufacturer=eq["manufacturer"],
                    model=eq["model"],
                    department=eq["department"],
                    status=eq["status"],
                    maintenance_frequency_days=eq["m_days"],
                    next_maintenance_date=m_date,
                    purchase_date=today - datetime.timedelta(days=730)
                )
                db.add(new_eq)
                db.flush()
                inserted_eqs.append(new_eq)
            else:
                inserted_eqs.append(existing)
        
        # 3. Add Historical Maintenance & Repair Records for the Graph
        print("Ensuring 6 months of cost history...")
        
        months_back = 6
        admin = db.query(models.User).filter(models.User.email == "admin@hospital.com").first()
        
        records_added = 0
        for i in range(months_back):
            # Use mid-month dates for history
            record_date = today.replace(day=15) - datetime.timedelta(days=i * 30)
            
            # Maintenance records
            for j in range(2):
                eq = inserted_eqs[(i + j) % len(inserted_eqs)]
                # Add if not already present for this exact eq and date
                existing = db.query(models.MaintenanceRecord).filter(
                    models.MaintenanceRecord.equipment_id == eq.id,
                    models.MaintenanceRecord.maintenance_date == record_date
                ).first()
                if not existing:
                    m_rec = models.MaintenanceRecord(
                        equipment_id=eq.id,
                        maintenance_date=record_date,
                        performed_by="System Auto-Seed",
                        notes="Completed scheduled maintenance.",
                        status=models.MaintenanceStatus.completed,
                        cost=2000 + (i * 200) + (j * 100)
                    )
                    db.add(m_rec)
                    records_added += 1
            
            # Repair records
            for k in range(1):
                eq = inserted_eqs[(i + k + 3) % len(inserted_eqs)]
                existing = db.query(models.RepairRecord).filter(
                    models.RepairRecord.equipment_id == eq.id,
                    models.RepairRecord.repair_date == record_date
                ).first()
                if not existing:
                    r_rec = models.RepairRecord(
                        equipment_id=eq.id,
                        issue_description="Component failure during operation.",
                        repair_date=record_date,
                        status=models.RepairStatus.resolved,
                        technician_notes="Replaced faulty part.",
                        cost=5000 + (i * 500)
                    )
                    db.add(r_rec)
                    records_added += 1

        print(f"Historical records processed. New records added: {records_added}")

        # 4. Add Notifications for Admin
        if admin:
            print("Seeding notifications...")
            alert_data = [
                {"title": "Maintenance Overdue", "msg": "X-Ray Machine (XR-001) maintenance is 20 days overdue.", "type": models.NotificationType.overdue_maintenance},
                {"title": "Repair Completed", "msg": "Ventilator (VNT-002) repair has been finalized.", "type": models.NotificationType.repair_update},
                {"title": "System Update", "msg": "Welcome to MedTrack v1.2. New financial analytics are live!", "type": models.NotificationType.repair_update}
            ]
            for alert in alert_data:
                existing_n = db.query(models.Notification).filter(models.Notification.message == alert["msg"]).first()
                if not existing_n:
                    notif = models.Notification(
                        user_id=admin.id,
                        title=alert["title"],
                        message=alert["msg"],
                        type=alert["type"],
                        created_at=today
                    )
                    db.add(notif)

        db.commit()
        print("Database enriched with success!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
