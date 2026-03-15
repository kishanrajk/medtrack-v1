import requests
import datetime

BASE_URL = "http://127.0.0.1:8000"

def demo_cost_entry():
    # 1. Login as Admin
    print("Logging in...")
    login_data = {"username": "admin@hospital.com", "password": "admin123"}
    resp = requests.post(f"{BASE_URL}/api/auth/login", data=login_data)
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Resolve a Repair with Cost (Repair ID 1 from seeding)
    print("\nAttempting to resolve Repair ID 1 with cost 15000...")
    repair_update = {
        "status": "resolved",
        "technician_notes": "Main cable replaced. Full testing passed.",
        "cost": 15000
    }
    resp = requests.put(f"{BASE_URL}/api/repairs/1", json=repair_update, headers=headers)
    if resp.status_code == 200:
        print(f"SUCCESS: Repair 1 resolved. Cost: {resp.json().get('cost')}")
    else:
        print(f"FAILED: {resp.text}")

    # 3. Log a Completed Maintenance with Cost (Equipment ID 1)
    print("\nLogging a completed maintenance for Equipment 1 with cost 2500...")
    maint_data = {
        "maintenance_date": str(datetime.date.today()),
        "performed_by": "John Tech",
        "notes": "Annual certification and filter replacement.",
        "status": "completed",
        "cost": 2500
    }
    resp = requests.post(f"{BASE_URL}/api/maintenance/equipment/1", json=maint_data, headers=headers)
    if resp.status_code == 200:
        print(f"SUCCESS: Maintenance logged. Cost: {resp.json().get('cost')}")
    else:
        print(f"FAILED: {resp.text}")

if __name__ == "__main__":
    demo_cost_entry()
