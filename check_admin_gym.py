import requests
import json

BASE_URL = "http://localhost:8001/api/v1"

def check_admin_gym():
    """Check what gym the admin user is from"""
    
    # Login as admin
    login_data = {
        "email": "admin@test.com",
        "password": "adminpass123",
        "gym_id": 16
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"Login failed: {response.text}")
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get current user info
    response = requests.get(f"{BASE_URL}/users/me", headers=headers)
    if response.status_code == 200:
        user = response.json()
        print(f"Admin user gym_id: {user.get('gym_id')}")
        print(f"Admin user gym: {user.get('gym')}")
    else:
        print(f"Failed to get user info: {response.text}")
    
    # Get plans in gym 16
    response = requests.get(f"{BASE_URL}/plans/", headers=headers)
    if response.status_code == 200:
        plans = response.json()
        print(f"Plans in gym 16:")
        for plan in plans:
            if plan.get('gym_id') == 16:
                print(f"  Plan ID: {plan['id']}, Name: {plan['name']}, Gym ID: {plan['gym_id']}")
    else:
        print(f"Failed to get plans: {response.text}")

if __name__ == "__main__":
    check_admin_gym() 