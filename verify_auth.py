import requests
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_login():
    print("Testing login with admin@hospital.com / admin123...")
    data = {
        "username": "admin@hospital.com",
        "password": "admin123"
    }
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", data=data)
        if response.status_code == 200:
            token = response.json()["access_token"]
            print(f"Login successful! Token: {token[:20]}...")
            return token
        else:
            print(f"Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error connecting to server: {e}")
        return None

def test_me(token):
    print("Testing /api/auth/me...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
    if response.status_code == 200:
        print(f"Me endpoint works! User: {response.json()['name']} (Role: {response.json()['role']})")
        return True
    else:
        print(f"Me failed: {response.status_code}")
        return False

if __name__ == "__main__":
    token = test_login()
    if token:
        test_me(token)
    else:
        sys.exit(1)
