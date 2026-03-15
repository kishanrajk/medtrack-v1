import datetime
import models
import auth_utils
from database import SessionLocal, engine

def seed_db():
    # Create tables
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # 1. Add Users
        print("Seeding users...")
        users_data = [
            {
                "name": "Admin User",
                "email": "admin@hospital.com",
                "role": models.UserRole.admin,
                "password": "admin123",
                "phone": "+919876543210"
            },
            {
                "name": "John Technician",
                "email": "john@hospital.com",
                "role": models.UserRole.technician,
                "password": "tech123",
                "phone": "+919876543211"
            },
            {
                "name": "Sarah Smith",
                "email": "sarah@hospital.com",
                "role": models.UserRole.technician,
                "password": "tech456",
                "phone": "+919876543212"
            }
        ]
        
        for u in users_data:
            if not db.query(models.User).filter(models.User.email == u["email"]).first():
                new_user = models.User(
                    name=u["name"],
                    email=u["email"],
                    phone_number=u["phone"],
                    role=u["role"],
                    password_hash=auth_utils.get_password_hash(u["password"])
                )
                db.add(new_user)
        db.commit()

        # 2. Add Equipment
        print("Seeding equipment...")
        equipment_data = [
            {
                "name": "X-Ray Machine",
                "asset_id": "XR-001",
                "serial_number": "SN12345",
                "manufacturer": "GE Healthcare",
                "model": "Optima XR646",
                "department": "Radiology",
                "purchase_date": datetime.date(2023, 5, 10),
                "warranty_expiry": datetime.date(2025, 5, 10),
                "status": models.EquipmentStatus.active,
                "maintenance_frequency_days": 180,
                "next_maintenance_date": datetime.date.today() + datetime.timedelta(days=30)
            },
            {
                "name": "Ventilator",
                "asset_id": "VNT-002",
                "serial_number": "SN67890",
                "manufacturer": "Dräger",
                "model": "Evita V500",
                "department": "ICU",
                "purchase_date": datetime.date(2024, 1, 15),
                "warranty_expiry": datetime.date(2026, 1, 15),
                "status": models.EquipmentStatus.active,
                "maintenance_frequency_days": 90,
                "next_maintenance_date": datetime.date.today() - datetime.timedelta(days=5) # Overdue
            },
            {
                "name": "MRI Scanner",
                "asset_id": "MRI-003",
                "serial_number": "SN54321",
                "manufacturer": "Siemens Healthineers",
                "model": "MAGNETOM Lumina",
                "department": "Radiology",
                "purchase_date": datetime.date(2022, 11, 20),
                "warranty_expiry": datetime.date(2024, 11, 20),
                "status": models.EquipmentStatus.under_repair,
                "maintenance_frequency_days": 365,
                "next_maintenance_date": datetime.date.today() + datetime.timedelta(days=120)
            },
            {
                "name": "Defibrillator",
                "asset_id": "DEF-004",
                "serial_number": "SN11223",
                "manufacturer": "Zoll Medical",
                "model": "R Series",
                "department": "Emergency",
                "purchase_date": datetime.date(2023, 8, 25),
                "warranty_expiry": datetime.date(2025, 8, 25),
                "status": models.EquipmentStatus.active,
                "maintenance_frequency_days": 30,
                "next_maintenance_date": datetime.date.today() + datetime.timedelta(days=2)
            }
        ]

        inserted_equipment = []
        for eq in equipment_data:
            existing = db.query(models.Equipment).filter(models.Equipment.asset_id == eq["asset_id"]).first()
            if not existing:
                new_eq = models.Equipment(**eq)
                db.add(new_eq)
                db.flush() # To get ID
                inserted_equipment.append(new_eq)
            else:
                inserted_equipment.append(existing)
        db.commit()

        # 3. Add Maintenance Records
        print("Seeding maintenance records...")
        if inserted_equipment:
            # Add a completed record for X-Ray
            xr = [e for e in inserted_equipment if e.asset_id == "XR-001"][0]
            if not db.query(models.MaintenanceRecord).filter(models.MaintenanceRecord.equipment_id == xr.id).first():
                mr = models.MaintenanceRecord(
                    equipment_id=xr.id,
                    maintenance_date=datetime.date(2023, 11, 15),
                    performed_by="John Technician",
                    notes="Regular checkup done. All good.",
                    status=models.MaintenanceStatus.completed,
                    cost=2500
                )
                db.add(mr)
            
            # Add a scheduled record for Ventilator
            vnt = [e for e in inserted_equipment if e.asset_id == "VNT-002"][0]
            if not db.query(models.MaintenanceRecord).filter(models.MaintenanceRecord.equipment_id == vnt.id).first():
                mr = models.MaintenanceRecord(
                    equipment_id=vnt.id,
                    maintenance_date=vnt.next_maintenance_date,
                    status=models.MaintenanceStatus.scheduled
                )
                db.add(mr)
        
        # 4. Add Repair Records
        print("Seeding repair records...")
        mri = [e for e in inserted_equipment if e.asset_id == "MRI-003"][0]
        if mri and not db.query(models.RepairRecord).filter(models.RepairRecord.equipment_id == mri.id).first():
            rr = models.RepairRecord(
                equipment_id=mri.id,
                issue_description="Artifacts found in imaging.",
                repair_date=datetime.date.today(),
                status=models.RepairStatus.in_progress,
                technician_notes="Waiting for spare parts from Siemens.",
                cost=15000
            )
            db.add(rr)
        
        db.commit()
        print("Database seeded successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
