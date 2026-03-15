import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

import models
from database import engine, SessionLocal
import auth_utils
import scheduler

def debug_init():
    print("1. Creating tables...")
    models.Base.metadata.create_all(bind=engine)
    print("Tables created.")

    print("2. Creating admin user...")
    db = SessionLocal()
    try:
        if not db.query(models.User).filter(models.User.email == "admin@hospital.com").first():
            print("Hashing password (admin123)...")
            pwd_hash = auth_utils.get_password_hash("admin123")
            print(f"Hash: {pwd_hash[:10]}...")
            admin = models.User(
                name="Admin User", 
                email="admin@hospital.com", 
                role=models.UserRole.admin, 
                email_alerts_enabled=1,
                password_hash=pwd_hash
            )
            db.add(admin)
            db.commit()
            print("Admin user created.")
        else:
            print("Admin user already exists.")
    finally:
        db.close()

    print("3. Starting scheduler (dry run check)...")
    # scheduler.start_scheduler() # Don't actually start the background loop
    print("Startup debug successful.")

if __name__ == "__main__":
    try:
        debug_init()
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
