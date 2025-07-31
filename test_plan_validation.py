import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8001/api/v1"

def test_plan_validation():
    """Test plan validation in update_user endpoint"""
    
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
    
    # Create a user with initial plan
    user_data = {
        "email": f"testuser{datetime.now().timestamp()}@test.com",
        "full_name": "Test User",
        "document_id": f"TEST{datetime.now().timestamp()}",
        "phone_number": "1234567890",
        "role": "user",
        "plan_id": 5  # Use existing plan in gym 16
    }
    
    print("Creating user with initial plan...")
    create_response = requests.post(f"{BASE_URL}/users/with-plan", json=user_data, headers=headers)
    
    if create_response.status_code != 200:
        print(f"Failed to create user: {create_response.text}")
        return
    
    created_user = create_response.json()
    user_id = created_user['id']
    print(f"Created user with ID: {user_id}")
    print(f"Initial active plan: {created_user.get('active_plan', {}).get('plan_id')}")
    
    # Try to update user with a new plan (plan 121 from gym 16)
    update_data = {
        "plan_id": 121
    }
    
    print("Updating user with new plan...")
    update_response = requests.put(f"{BASE_URL}/users/{user_id}", json=update_data, headers=headers)
    
    if update_response.status_code != 200:
        print(f"Failed to update user: {update_response.text}")
        return
    
    updated_user = update_response.json()
    print(f"Updated user response:")
    print(f"Active plan ID: {updated_user.get('active_plan', {}).get('plan_id')}")
    print(f"Expected: 121")

if __name__ == "__main__":
    test_plan_validation() 