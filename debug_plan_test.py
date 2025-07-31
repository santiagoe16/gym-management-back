import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8001/api/v1"

def login_admin():
    """Login as admin"""
    # Try different admin credentials
    admin_credentials = [
        {"email": "admin@test.com", "password": "admin123", "gym_id": 1},
        {"email": "admin@test.com", "password": "admin123", "gym_id": 16},  # From test output
        {"email": "admin@gym.com", "password": "admin123", "gym_id": 1},
        {"email": "admin@gym.com", "password": "admin123", "gym_id": 16},
    ]
    
    for creds in admin_credentials:
        print(f"Trying login with: {creds['email']}, gym_id: {creds['gym_id']}")
        response = requests.post(f"{BASE_URL}/auth/login", json=creds)
        if response.status_code == 200:
            print(f"Login successful with: {creds['email']}, gym_id: {creds['gym_id']}")
            return response.json()["access_token"]
        else:
            print(f"Login failed: {response.text}")
    
    return None

def get_available_plans(token):
    """Get available plans in gym 1"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/plans/", headers=headers)
    
    if response.status_code == 200:
        plans = response.json()
        print("Available plans:")
        for plan in plans:
            print(f"  Plan ID: {plan['id']}, Name: {plan['name']}, Gym ID: {plan['gym_id']}")
        return plans
    else:
        print(f"Failed to get plans: {response.text}")
        return []

def test_plan_modification():
    """Test plan modification with debug output"""
    token = login_admin()
    if not token:
        print("Failed to login")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get available plans
    plans = get_available_plans(token)
    if not plans:
        print("No plans available")
        return
    
    # Use the first available plan
    initial_plan_id = plans[0]['id']
    print(f"Using initial plan ID: {initial_plan_id}")
    
    # Create a user with initial plan
    user_data = {
        "email": f"debuguser{datetime.now().timestamp()}@test.com",
        "full_name": "Debug Test User",
        "document_id": f"DEBUG{datetime.now().timestamp()}",
        "phone_number": "1234567890",
        "role": "user",
        "plan_id": initial_plan_id
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
    
    # Create a new plan
    plan_data = {
        "name": f"Debug Plan {datetime.now().timestamp()}",
        "description": "Debug plan for testing",
        "price": 100.0,
        "duration_days": 30,
        "gym_id": 1,
        "is_active": True
    }
    
    print("Creating new plan...")
    plan_response = requests.post(f"{BASE_URL}/plans/", json=plan_data, headers=headers)
    
    if plan_response.status_code != 200:
        print(f"Failed to create plan: {plan_response.text}")
        return
    
    new_plan = plan_response.json()
    new_plan_id = new_plan['id']
    print(f"Created new plan with ID: {new_plan_id}")
    
    # Update user with new plan
    update_data = {
        "plan_id": new_plan_id
    }
    
    print("Updating user with new plan...")
    update_response = requests.put(f"{BASE_URL}/users/{user_id}", json=update_data, headers=headers)
    
    if update_response.status_code != 200:
        print(f"Failed to update user: {update_response.text}")
        return
    
    updated_user = update_response.json()
    print(f"Updated user response:")
    print(f"Active plan ID: {updated_user.get('active_plan', {}).get('plan_id')}")
    print(f"Expected: {new_plan_id}")

if __name__ == "__main__":
    test_plan_modification() 