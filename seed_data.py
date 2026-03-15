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

        # 2. Check if equipment exists already
        if db.query(models.Equipment).count() > 0:
            print("Equipment already exists. Skipping bulk seeding.")
            return

        print("Seeding diverse equipment...")
        today = datetime.date.today()
        
        equipment_data = [
            {"name": "X-Ray Machine", "asset_id": "XR-001", "manufacturer": "GE", "model": "Optima", "department": "Radiology", "status": models.EquipmentStatus.active, "m_days": 180},
            {"name": "Ventilator", "asset_id": "VNT-002", "manufacturer": "Dräger", "model": "Evita", "department": "ICU", "status": models.EquipmentStatus.active, "m_days": 90},
            {"name": "MRI Scanner", "asset_id": "MRI-003", "manufacturer": "Siemens", "model": "MAG", "department": "Radiology", "status": models.EquipmentStatus.under_repair, "m_days": 365},
            {"name": "Defibrillator", "asset_id": "DEF-004", "manufacturer": "Zoll", "model": "R Series", "department": "ER", "status": models.EquipmentStatus.active, "m_days": 30},
            {"name": "Patient Monitor", "asset_id": "MON-005", "manufacturer": "Philips", "model": "IntelliVue", "department": "ICU", "status": models.EquipmentStatus.active, "m_days": 180},
            {"name": "CT Scanner", "asset_id": "CT-006", "manufacturer": "Canon", "model": "Aquilion", "department": "Radiology", "status": models.EquipmentStatus.active, "m_days": 180},
            {"name": "Infusion Pump", "asset_id": "PMP-007", "manufacturer": "B. Braun", "model": "Infusomat", "department": "General Ward", "status": models.EquipmentStatus.out_of_order, "m_days": 365},
            {"name": "Ultrasound", "asset_id": "ULT-008", "manufacturer": "Samsung", "model": "RS85", "department": "Diagnostics", "status": models.EquipmentStatus.active, "m_days": 180},
            {"name": "ECG Machine", "asset_id": "ECG-009", "manufacturer": "Schiller", "model": "CardioVit", "department": "Cardiology", "status": models.EquipmentStatus.active, "m_days": 90},
            {"name": "Anesthesia Workstation", "asset_id": "ANS-010", "manufacturer": "GE", "model": "Avance", "department": "OT", "status": models.EquipmentStatus.active, "m_days": 90},
        ]

        inserted_eqs = []
        for i, eq in enumerate(equipment_data):
            # Calculate a next maintenance date relative to today
            m_date = today + datetime.timedelta(days=(i * 10) - 20) # Mixture of overdue and upcoming
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
            inserted_eqs.append(new_eq)
        
        db.flush()

        # 3. Add Historical Maintenance & Repair Records for the Graph
        # We need data for Oct 25, Nov 25, Dec 25, Jan 26, Feb 26, Mar 26 (approx)
        print("Seeding cost history for the last 6 months...")
        
        months_back = 6
        for i in range(months_back):
            record_date = today - datetime.timedelta(days=i * 30 + 15)
            # Maintenance records
            for j in range(2):
                eq = inserted_eqs[(i + j) % len(inserted_eqs)]
                m_rec = models.MaintenanceRecord(
                    equipment_id=eq.id,
                    maintenance_date=record_date,
                    performed_by="System Auto-Seed",
                    notes="Completed scheduled maintenance.",
                    status=models.MaintenanceStatus.completed,
                    cost=2000 + (i * 200) + (j * 100)
                )
                db.add(m_rec)
            
            # Repair records
            for k in range(1):
                eq = inserted_eqs[(i + k + 3) % len(inserted_eqs)]
                r_rec = models.RepairRecord(
                    equipment_id=eq.id,
                    issue_description="Component failure during operation.",
                    repair_date=record_date,
                    completion_date=record_date + datetime.timedelta(days=2),
                    status=models.RepairStatus.resolved,
                    technician_notes="Replaced faulty part.",
                    cost=5000 + (i * 500)
                )
                db.add(r_rec)

        db.commit()
        print("Database seeded with rich history!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
