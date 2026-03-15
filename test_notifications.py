import requests
import datetime
import time
from database import SessionLocal
import models
from scheduler import check_maintenance_alerts

BASE_URL = "http://127.0.0.1:8000"

def wait_for_server():
    print("Waiting for server to be ready...")
    for _ in range(10):
        try:
            response = requests.get(f"{BASE_URL}/api/auth/me")
            if response.status_code in [200, 401]: # 401 means it's up but needs auth
                print("Server is up!")
                return True
        except:
            pass
        time.sleep(1)
    print("Server failed to start.")
    return False

def test_maintenance_alerts():
    print("\n--- Testing Maintenance Alerts ---")
    db = SessionLocal()
    try:
        today = datetime.date.today()
        # 1. Setup XR-001 for Upcoming (7 days from now)
        xr = db.query(models.Equipment).filter(models.Equipment.asset_id == "XR-001").first()
        xr.next_maintenance_date = today + datetime.timedelta(days=7)
        
        # 2. Setup VNT-002 for Overdue (Yesterday)
        vnt = db.query(models.Equipment).filter(models.Equipment.asset_id == "VNT-002").first()
        vnt.next_maintenance_date = today - datetime.timedelta(days=1)
        
        db.commit()
        print("Equipment dates updated. Triggering scheduler check...")
        
        # Manually trigger the check
        check_maintenance_alerts()
        
        # Verify in DB
        notifs = db.query(models.Notification).order_by(models.Notification.id.desc()).limit(5).all()
        print(f"Latest Notifications in DB:")
        for n in notifs:
            print(f"- [{n.type}] {n.title}: {n.message[:50]}...")
            
    finally:
        db.close()

def test_repair_alerts():
    print("\n--- Testing Repair API Alerts ---")
    # 1. Login
    login_data = {"username": "admin@hospital.com", "password": "admin123"}
    resp = requests.post(f"{BASE_URL}/api/auth/login", data=login_data)
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        return
    
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Report Repair
    print("Reporting new repair for XR-001 (Equip ID 1)...")
    repair_data = {
        "issue_description": "Screen is flickering during operation",
        "repair_date": str(datetime.date.today())
    }
    resp = requests.post(f"{BASE_URL}/api/repairs/equipment/1", json=repair_data, headers=headers)
    if resp.status_code == 200:
        repair_id = resp.json()["id"]
        print(f"Repair reported! ID: {repair_id}")
        
        # 3. Update Repair
        print(f"Updating repair {repair_id} to 'in_progress'...")
        update_data = {"status": "in_progress", "technician_notes": "Ordered replacement screen."}
        requests.put(f"{BASE_URL}/api/repairs/{repair_id}", json=update_data, headers=headers)
        print("Repair updated.")
    else:
        print(f"Repair report failed: {resp.status_code} - {resp.text}")

if __name__ == "__main__":
    if wait_for_server():
        test_maintenance_alerts()
        test_repair_alerts()
        print("\nNotification tests completed. Check server logs for Mock Email output.")
