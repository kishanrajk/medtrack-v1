from database import SessionLocal
import models

db = SessionLocal()
equipment = db.query(models.Equipment).all()
print("--- Diagnostic Output ---")
for eq in equipment:
    print(f"Name: {eq.name}, Freq: {eq.maintenance_frequency_days}, Next Maint: {eq.next_maintenance_date}")
db.close()
