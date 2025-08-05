#!/usr/bin/env python3
"""
Simple test script for user endpoints
Run this script to test the user endpoints manually
"""

from time import sleep
import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8001/api/v1"
ADMIN_EMAIL = "admin@test.com"
ADMIN_PASSWORD = "adminpass123"
TRAINER_EMAIL = "trainer@test.com"
TRAINER_PASSWORD = "trainerpass123"

class UserEndpointTester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.admin_token = None
        self.trainer_token = None
        self.test_gym_id = None
        self.test_plan_id = None
        
        # Track created test data for cleanup
        self.created_users = []
        self.created_plans = []
        self.created_gyms = []
        
    def print_test_result(self, test_name, success, message=""):
        """Print test result with formatting"""
        status = "PASS" if success else "FAIL"
        print(f"{status} {test_name}")
        if message and not success:
            print(f"   Error: {message}")
        print()
    
    def login(self, email, password, gym_id=1):
        """Login and get access token"""
        try:
            response = requests.post(f"{self.base_url}/auth/login", json={
                "email": email,
                "password": password,
                "gym_id": gym_id
            })
            if response.status_code == 200:
                return response.json()["access_token"]
            else:
                print(f"Login failed for {email}: {response.text}")
                return None
        except Exception as e:
            print(f"Login error for {email}: {str(e)}")
            return None
    
    def setup_test_data(self):
        """Setup test data (gym, plan) if needed"""
        print("Setting up test data...")
        
        # First, try to get existing gyms to find one we can use
        try:
            response = requests.get(f"{self.base_url}/gyms/", headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            if response.status_code == 200:
                gyms = response.json()
                if gyms:
                    # Use the first available gym
                    self.test_gym_id = gyms[0]["id"]
                    print(f"Using existing gym with ID: {self.test_gym_id}")
                else:
                    # No gyms exist, try to create one
                    gym_data = {
                        "name": f"Test Gym {datetime.now().timestamp()}",
                        "address": "123 Test Street",
                        "is_active": True
                    }
                    
                    response = requests.post(f"{self.base_url}/gyms/", json=gym_data, headers={
                        "Authorization": f"Bearer {self.admin_token}"
                    })
                    if response.status_code == 200:
                        self.test_gym_id = response.json()["id"]
                        self.created_gyms.append(self.test_gym_id)
                        print(f"Created test gym with ID: {self.test_gym_id}")
                    else:
                        print(f"Failed to create gym: {response.text}")
                        return
            else:
                print(f"Failed to get gyms: {response.text}")
                return
        except Exception as e:
            print(f"Error setting up gym: {str(e)}")
            return
        
        # Now try to get existing plans or create one
        try:
            response = requests.get(f"{self.base_url}/plans/", headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            if response.status_code == 200:
                plans = response.json()
                # Look for a plan in the same gym as the admin user (gym 16)
                for plan in plans:
                    if plan.get("gym_id") == 16:
                        self.test_plan_id = plan["id"]
                        print(f"Using existing plan in gym 16 with ID: {self.test_plan_id}")
                        break
                
                # If no plan found in gym 16, use any available plan
                if not self.test_plan_id and plans:
                    self.test_plan_id = plans[0]["id"]
                    print(f"Using existing plan with ID: {self.test_plan_id}")
                
                # If still no plan, create one
                if not self.test_plan_id:
                    plan_data = {
                        "name": f"Test Plan {datetime.now().timestamp()}",
                        "description": "A test plan for testing",
                        "price": 50.0,
                        "duration_days": 30,
                        "gym_id": 16,  # Use gym 16 to match admin user's gym
                        "is_active": True
                    }
                    
                    response = requests.post(f"{self.base_url}/plans/", json=plan_data, headers={
                        "Authorization": f"Bearer {self.admin_token}"
                    })
                    if response.status_code == 200:
                        self.test_plan_id = response.json()["id"]
                        self.created_plans.append(self.test_plan_id)
                        print(f"Created test plan with ID: {self.test_plan_id}")
                    else:
                        print(f"Failed to create plan: {response.text}")
            else:
                print(f"Failed to get plans: {response.text}")
        except Exception as e:
            print(f"Error setting up plan: {str(e)}")
        
        # Verify we have the required data
        if not self.test_gym_id:
            print("ERROR: Could not set up test gym")
        if not self.test_plan_id:
            print("ERROR: Could not set up test plan")
        if self.test_gym_id and self.test_plan_id:
            print(f"Test data setup complete: Gym ID {self.test_gym_id}, Plan ID {self.test_plan_id}")
    
    def cleanup_test_data(self):
        """Clean up all test data created during tests"""
        print("\n[Cleanup] Cleaning up test data...")
        
        # Clean up users first (they reference plans and gyms)
        for user_id in self.created_users:
            try:
                response = requests.delete(f"{self.base_url}/users/{user_id}", headers={
                    "Authorization": f"Bearer {self.admin_token}"
                })
                if response.status_code == 200:
                    print(f"[OK] Deleted test user ID: {user_id}")
                else:
                    print(f"[WARN] Failed to delete test user ID: {user_id} - {response.text}")
            except Exception as e:
                print(f"[WARN] Error deleting test user ID: {user_id}: {str(e)}")
        
        # Clean up plans
        for plan_id in self.created_plans:
            try:
                response = requests.delete(f"{self.base_url}/plans/{plan_id}", headers={
                    "Authorization": f"Bearer {self.admin_token}"
                })
                if response.status_code == 200:
                    print(f"[OK] Deleted test plan ID: {plan_id}")
                else:
                    print(f"[WARN] Failed to delete test plan ID: {plan_id} - {response.text}")
            except Exception as e:
                print(f"[WARN] Error deleting test plan ID: {plan_id}: {str(e)}")
        
        # Clean up gyms
        for gym_id in self.created_gyms:
            try:
                response = requests.delete(f"{self.base_url}/gyms/{gym_id}", headers={
                    "Authorization": f"Bearer {self.admin_token}"
                })
                if response.status_code == 200:
                    print(f"[OK] Deleted test gym ID: {gym_id}")
                else:
                    print(f"[WARN] Failed to delete test gym ID: {gym_id} - {response.text}")
            except Exception as e:
                print(f"[WARN] Error deleting test gym ID: {gym_id}: {str(e)}")
        
        print("[Cleanup] Test data cleanup completed")
    
    def test_authentication(self):
        """Test authentication endpoints"""
        print("=== Testing Authentication ===")
        
        # Test admin login
        self.admin_token = self.login(ADMIN_EMAIL, ADMIN_PASSWORD, gym_id=16)
        success = self.admin_token is not None
        self.print_test_result("Admin Login", success)
        
        # Test trainer login
        self.trainer_token = self.login(TRAINER_EMAIL, TRAINER_PASSWORD, gym_id=16)
        success = self.trainer_token is not None
        self.print_test_result("Trainer Login", success)
        
        return self.admin_token is not None and self.trainer_token is not None
    
    def test_read_users(self):
        """Test reading users endpoint"""
        print("=== Testing Read Users ===")
        
        if not self.admin_token:
            self.print_test_result("Read Users (Admin)", False, "No admin token")
            return False
        
        try:
            response = requests.get(f"{self.base_url}/users/", headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            success = response.status_code == 200
            users = response.json() if success else []
            self.print_test_result("Read Users (Admin)", success, f"Found {len(users)} users")
            
            return success
        except Exception as e:
            self.print_test_result("Read Users (Admin)", False, str(e))
            return False
    
    def test_create_admin_user(self):
        """Test creating an admin user"""
        print("=== Testing Create Admin User ===")
        
        if not self.admin_token or not self.test_gym_id:
            self.print_test_result("Create Admin User", False, "Missing token or gym")
            return False
        
        user_data = {
            "email": f"newadmin{datetime.now().timestamp()}@test.com",
            "full_name": "New Admin User",
            "document_id": f"ADMIN{datetime.now().timestamp()}",
            "phone_number": "1111111111",
            "gym_id": self.test_gym_id,
            "role": "admin",
            "password": "newadminpass123"
        }
        
        try:
            response = requests.post(f"{self.base_url}/users/admin-trainer", json=user_data, headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            success = response.status_code == 200
            if success:
                user = response.json()
                self.created_users.append(user['id'])
                self.print_test_result("Create Admin User", success, f"Created user ID: {user['id']}")
            else:
                self.print_test_result("Create Admin User", success, response.text)
            
            return success
        except Exception as e:
            self.print_test_result("Create Admin User", False, str(e))
            return False
    
    def test_create_trainer_user(self):
        """Test creating a trainer user"""
        print("=== Testing Create Trainer User ===")
        
        if not self.admin_token or not self.test_gym_id:
            self.print_test_result("Create Trainer User", False, "Missing token or gym")
            return False
        
        user_data = {
            "email": f"newtrainer{datetime.now().timestamp()}@test.com",
            "full_name": "New Trainer User",
            "document_id": f"TRAINER{datetime.now().timestamp()}",
            "phone_number": "2222222222",
            "gym_id": self.test_gym_id,
            "role": "trainer",
            "password": "newtrainerpass123",
            "schedule_start": "8",
            "schedule_end": "12"
        }
        
        try:
            response = requests.post(f"{self.base_url}/users/admin-trainer", json=user_data, headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            success = response.status_code == 200
            if success:
                user = response.json()
                self.created_users.append(user['id'])
                self.print_test_result("Create Trainer User", success, f"Created user ID: {user['id']}")
            else:
                self.print_test_result("Create Trainer User", success, response.text)
            
            return success
        except Exception as e:
            self.print_test_result("Create Trainer User", False, str(e))
            return False
    
    def test_create_regular_user_with_plan(self):
        """Test creating a regular user with plan"""
        print("=== Testing Create Regular User with Plan ===")
        
        if not self.admin_token or not self.test_gym_id or not self.test_plan_id:
            self.print_test_result("Create Regular User with Plan", False, "Missing token, gym, or plan")
            return False
        
        user_data = {
            "email": f"newuser{datetime.now().timestamp()}@test.com",
            "full_name": "New Regular User",
            "document_id": f"USER{datetime.now().timestamp()}",
            "phone_number": "3333333333",
            "role": "user",
            "plan_id": self.test_plan_id
        }
        
        try:
            response = requests.post(f"{self.base_url}/users/with-plan", json=user_data, headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            success = response.status_code == 200
            if success:
                user = response.json()
                self.created_users.append(user['id'])
                self.print_test_result("Create Regular User with Plan", success, f"Created user ID: {user['id']}")
            else:
                self.print_test_result("Create Regular User with Plan", success, response.text)
            
            return success
        except Exception as e:
            self.print_test_result("Create Regular User with Plan", False, str(e))
            return False
    
    def test_search_user_by_document_id(self):
        """Test searching user by document ID"""
        print("=== Testing Search User by Document ID ===")
        
        if not self.admin_token:
            self.print_test_result("Search User by Document ID", False, "No admin token")
            return False
        
        # First create a user to search for
        user_data = {
            "email": f"searchuser{datetime.now().timestamp()}@test.com",
            "full_name": "Search Test User",
            "document_id": f"SEARCH{datetime.now().timestamp()}",
            "phone_number": "4444444444",
            "role": "user",
            "plan_id": self.test_plan_id
        }
        
        try:
            # Create user with plan
            create_response = requests.post(f"{self.base_url}/users/with-plan", json=user_data, headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            if create_response.status_code != 200:
                self.print_test_result("Search User by Document ID", False, "Failed to create test user")
                return False
            
            created_user = create_response.json()
            self.created_users.append(created_user['id'])
            
            # Search for the user
            search_response = requests.get(f"{self.base_url}/users/search/document/{user_data['document_id']}", headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            success = search_response.status_code == 200
            if success:
                found_user = search_response.json()
                self.print_test_result("Search User by Document ID", success, f"Found user: {found_user['email']}")
            else:
                self.print_test_result("Search User by Document ID", success, search_response.text)
            
            return success
        except Exception as e:
            self.print_test_result("Search User by Document ID", False, str(e))
            return False
    
    def test_search_users_by_phone(self):
        """Test searching users by phone number"""
        print("=== Testing Search Users by Phone ===")
        
        if not self.admin_token:
            self.print_test_result("Search Users by Phone", False, "No admin token")
            return False
        
        try:
            # Search with a partial phone number
            response = requests.get(f"{self.base_url}/users/search/phone/123", headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            success = response.status_code == 200
            if success:
                users = response.json()
                self.print_test_result("Search Users by Phone", success, f"Found {len(users)} users")
            else:
                self.print_test_result("Search Users by Phone", success, response.text)
            
            return success
        except Exception as e:
            self.print_test_result("Search Users by Phone", False, str(e))
            return False
    
    def test_read_trainers(self):
        """Test reading trainers endpoint"""
        print("=== Testing Read Trainers ===")
        
        if not self.admin_token:
            self.print_test_result("Read Trainers", False, "No admin token")
            return False
        
        try:
            response = requests.get(f"{self.base_url}/users/trainers/", headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            success = response.status_code == 200
            if success:
                trainers = response.json()
                self.print_test_result("Read Trainers", success, f"Found {len(trainers)} trainers")
            else:
                self.print_test_result("Read Trainers", success, response.text)
            
            return success
        except Exception as e:
            self.print_test_result("Read Trainers", False, str(e))
            return False
    
    def test_read_regular_users(self):
        """Test reading regular users"""
        print("=== Testing Read Regular Users ===")
        
        if not self.admin_token:
            self.print_test_result("Read Regular Users", False, "No admin token")
            return False
        
        try:
            response = requests.get(f"{self.base_url}/users/users/", headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            success = response.status_code == 200
            if success:
                users = response.json()
                self.print_test_result("Read Regular Users", success, f"Found {len(users)} regular users")
            else:
                self.print_test_result("Read Regular Users", success, response.text)
            
            return success
        except Exception as e:
            self.print_test_result("Read Regular Users", False, str(e))
            return False

    def test_update_user_basic(self):
        """Test basic user update functionality"""
        print("=== Testing Update User (Basic) ===")
        
        if not self.admin_token or not self.test_gym_id:
            self.print_test_result("Update User (Basic)", False, "Missing token or gym")
            return False
        
        # First create a user to update
        user_data = {
            "email": f"updateuser{datetime.now().timestamp()}@test.com",
            "full_name": "Update Test User",
            "document_id": f"UPDATE{datetime.now().timestamp()}",
            "phone_number": "5555555555",
            "role": "user",
            "plan_id": self.test_plan_id
        }
        
        try:
            # Create user
            create_response = requests.post(f"{self.base_url}/users/with-plan", json=user_data, headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            if create_response.status_code != 200:
                self.print_test_result("Update User (Basic)", False, "Failed to create test user")
                return False
            
            created_user = create_response.json()
            user_id = created_user['id']
            self.created_users.append(user_id)
            
            # Update the user
            update_data = {
                "full_name": "Updated Test User",
                "phone_number": "6666666666"
            }
            
            update_response = requests.put(f"{self.base_url}/users/{user_id}", json=update_data, headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            success = update_response.status_code == 200
            if success:
                updated_user = update_response.json()
                self.print_test_result("Update User (Basic)", success, f"Updated user: {updated_user['full_name']}")
            else:
                self.print_test_result("Update User (Basic)", success, update_response.text)
            
            return success
        except Exception as e:
            self.print_test_result("Update User (Basic)", False, str(e))
            return False

    def test_update_user_with_new_plan(self):
        """Test updating user with basic info (plan assignment tested separately)"""
        print("=== Testing Update User with Basic Info ===")
        
        if not self.admin_token or not self.test_gym_id or not self.test_plan_id:
            self.print_test_result("Update User with Basic Info", False, "Missing token, gym, or plan")
            return False
        
        # First create a user with a plan (we'll update it later)
        user_data = {
            "email": f"planuser{datetime.now().timestamp()}@test.com",
            "full_name": "Plan Test User",
            "document_id": f"PLAN{datetime.now().timestamp()}",
            "phone_number": "7777777777",
            "role": "user",
            "plan_id": self.test_plan_id
        }
        
        try:
            # Create user with plan
            create_response = requests.post(f"{self.base_url}/users/with-plan", json=user_data, headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            if create_response.status_code != 200:
                self.print_test_result("Update User with Basic Info", False, "Failed to create test user")
                return False
            
            created_user = create_response.json()
            user_id = created_user['id']
            self.created_users.append(user_id)
            
            # Update the user with basic info (not plan, since user already has this plan)
            update_data = {
                "full_name": "Updated Plan Test User"
            }
            
            update_response = requests.put(f"{self.base_url}/users/{user_id}", json=update_data, headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            success = update_response.status_code == 200
            if success:
                updated_user = update_response.json()
                self.print_test_result("Update User with Basic Info", success, 
                                     f"Updated user: {updated_user['full_name']}")
            else:
                self.print_test_result("Update User with Basic Info", success, update_response.text)
            
            return success
        except Exception as e:
            self.print_test_result("Update User with Basic Info", False, str(e))
            return False

    def test_update_user_plan_not_found(self):
        """Test updating user with non-existent plan"""
        print("=== Testing Update User with Non-existent Plan ===")
        
        if not self.admin_token:
            self.print_test_result("Update User with Non-existent Plan", False, "Missing token")
            return False
        
        try:
            # Try to update an existing user (admin user ID 1) with non-existent plan
            update_data = {
                "plan_id": 99999  # Non-existent plan ID
            }
            
            update_response = requests.put(f"{self.base_url}/users/1", json=update_data, headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            success = update_response.status_code == 404
            if success:
                self.print_test_result("Update User with Non-existent Plan", success, "Correctly rejected non-existent plan")
            else:
                self.print_test_result("Update User with Non-existent Plan", success, update_response.text)
            
            return success
        except Exception as e:
            self.print_test_result("Update User with Non-existent Plan", False, str(e))
            return False

    def test_update_user_duplicate_email(self):
        """Test updating user with duplicate email"""
        print("=== Testing Update User with Duplicate Email ===")
        
        if not self.admin_token or not self.test_gym_id:
            self.print_test_result("Update User with Duplicate Email", False, "Missing token or gym")
            return False
        
        # Create two users with plans
        user1_data = {
            "email": f"user1{datetime.now().timestamp()}@test.com",
            "full_name": "User One",
            "document_id": f"USER1{datetime.now().timestamp()}",
            "phone_number": "1111111111",
            "role": "user",
            "plan_id": self.test_plan_id
        }
        
        user2_data = {
            "email": f"user2{datetime.now().timestamp()}@test.com",
            "full_name": "User Two",
            "document_id": f"USER2{datetime.now().timestamp()}",
            "phone_number": "2222222222",
            "role": "user",
            "plan_id": self.test_plan_id
        }
        
        try:
            # Create first user
            create1_response = requests.post(f"{self.base_url}/users/with-plan", json=user1_data, headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            # Create second user
            create2_response = requests.post(f"{self.base_url}/users/with-plan", json=user2_data, headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            if create1_response.status_code != 200 or create2_response.status_code != 200:
                self.print_test_result("Update User with Duplicate Email", False, "Failed to create test users")
                return False
            
            user1 = create1_response.json()
            user2 = create2_response.json()
            self.created_users.extend([user1['id'], user2['id']])
            
            # Try to update user2 with user1's email
            update_data = {
                "email": user1_data['email']
            }
            
            update_response = requests.put(f"{self.base_url}/users/{user2['id']}", json=update_data, headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            success = update_response.status_code == 400
            if success:
                self.print_test_result("Update User with Duplicate Email", success, "Correctly rejected duplicate email")
            else:
                self.print_test_result("Update User with Duplicate Email", success, update_response.text)
            
            return success
        except Exception as e:
            self.print_test_result("Update User with Duplicate Email", False, str(e))
            return False

    def test_update_user_not_found(self):
        """Test updating non-existent user"""
        print("=== Testing Update User (Not Found) ===")
        
        if not self.admin_token:
            self.print_test_result("Update User (Not Found)", False, "No admin token")
            return False
        
        try:
            update_data = {
                "full_name": "Non-existent User"
            }
            
            response = requests.put(f"{self.base_url}/users/99999", json=update_data, headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            success = response.status_code == 404
            if success:
                self.print_test_result("Update User (Not Found)", success, "Correctly returned 404")
            else:
                self.print_test_result("Update User (Not Found)", success, response.text)
            
            return success
        except Exception as e:
            self.print_test_result("Update User (Not Found)", False, str(e))
            return False

    def test_update_user_unauthorized(self):
        """Test updating user without authentication"""
        print("=== Testing Update User (Unauthorized) ===")
        
        try:
            update_data = {
                "full_name": "Unauthorized Update"
            }
            
            response = requests.put(f"{self.base_url}/users/1", json=update_data)
            
            success = response.status_code == 401
            if not success:
                # Check if we got a JSON response with authentication error
                try:
                    error_detail = response.json().get("detail", "")
                    success = "Not authenticated" in error_detail or "Could not validate credentials" in error_detail
                except:
                    pass
            
            if success:
                self.print_test_result("Update User (Unauthorized)", success, "Correctly returned 401")
            else:
                self.print_test_result("Update User (Unauthorized)", success, response.text)
            
            return success
        except Exception as e:
            self.print_test_result("Update User (Unauthorized)", False, str(e))
            return False

    def test_delete_user(self):
        """Test deleting a user"""
        print("=== Testing Delete User ===")
        
        if not self.admin_token or not self.test_gym_id:
            self.print_test_result("Delete User", False, "Missing token or gym")
            return False
        
        # First create a user to delete
        user_data = {
            "email": f"deleteuser{datetime.now().timestamp()}@test.com",
            "full_name": "Delete Test User",
            "document_id": f"DELETE{datetime.now().timestamp()}",
            "phone_number": "9999999999",
            "role": "user",
            "plan_id": self.test_plan_id
        }
        
        try:
            # Create user
            create_response = requests.post(f"{self.base_url}/users/with-plan", json=user_data, headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            if create_response.status_code != 200:
                self.print_test_result("Delete User", False, "Failed to create test user")
                return False
            
            created_user = create_response.json()
            user_id = created_user['id']
            
            # Delete the user
            delete_response = requests.delete(f"{self.base_url}/users/{user_id}", headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            success = delete_response.status_code == 200
            if success:
                self.print_test_result("Delete User", success, f"Successfully deleted user ID: {user_id}")
            else:
                self.print_test_result("Delete User", success, delete_response.text)
            
            return success
        except Exception as e:
            self.print_test_result("Delete User", False, str(e))
            return False

    def test_delete_user_not_found(self):
        """Test deleting non-existent user"""
        print("=== Testing Delete User (Not Found) ===")
        
        if not self.admin_token:
            self.print_test_result("Delete User (Not Found)", False, "No admin token")
            return False
        
        try:
            response = requests.delete(f"{self.base_url}/users/99999", headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            success = response.status_code == 404
            if success:
                self.print_test_result("Delete User (Not Found)", success, "Correctly returned 404")
            else:
                self.print_test_result("Delete User (Not Found)", success, response.text)
            
            return success
        except Exception as e:
            self.print_test_result("Delete User (Not Found)", False, str(e))
            return False

    def test_unauthorized_access(self):
        """Test unauthorized access to endpoints"""
        print("=== Testing Unauthorized Access ===")
        
        try:
            response = requests.get(f"{self.base_url}/users/")
            success = response.status_code == 401
            if not success:
                # Check if we got a JSON response with authentication error
                try:
                    error_detail = response.json().get("detail", "")
                    success = "Not authenticated" in error_detail or "Could not validate credentials" in error_detail
                except:
                    pass
            self.print_test_result("Unauthorized Access to Users", success)
            return success
        except Exception as e:
            self.print_test_result("Unauthorized Access to Users", False, str(e))
            return False

    def test_trainer_can_only_view_regular_users(self):
        """Test that trainers can only view regular users, not admins or other trainers"""
        print("=== Testing Trainer Can Only View Regular Users ===")
        
        if not self.trainer_token:
            self.print_test_result("Trainer Can Only View Regular Users", False, "No trainer token")
            return False
        
        try:
            # Get users as trainer
            response = requests.get(f"{self.base_url}/users/", headers={
                "Authorization": f"Bearer {self.trainer_token}"
            })
            
            success = response.status_code == 200
            if success:
                users = response.json()
                # Check that all returned users are regular users (role == "user")
                all_regular_users = all(user.get("role") == "user" for user in users)
                self.print_test_result("Trainer Can Only View Regular Users", all_regular_users, 
                                     f"Found {len(users)} users, all should be regular users")
                return all_regular_users
            else:
                self.print_test_result("Trainer Can Only View Regular Users", success, response.text)
                return False
        except Exception as e:
            self.print_test_result("Trainer Can Only View Regular Users", False, str(e))
            return False

    def test_update_user_plan_modification(self):
        """Test comprehensive plan modification via update_user endpoint"""
        print("=== Testing Update User Plan Modification ===")
        
        if not self.admin_token or not self.test_gym_id or not self.test_plan_id:
            self.print_test_result("Update User Plan Modification", False, "Missing token, gym, or plan")
            return False
        
        # First create a user to test with
        user_data = {
            "email": f"planmoduser{datetime.now().timestamp()}@test.com",
            "full_name": "Plan Modification Test User",
            "document_id": f"PLANMOD{datetime.now().timestamp()}",
            "phone_number": "8888888888",
            "role": "user",
            "plan_id": self.test_plan_id
        }
        
        try:
            # Create user with initial plan
            create_response = requests.post(f"{self.base_url}/users/with-plan", json=user_data, headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            if create_response.status_code != 200:
                self.print_test_result("Update User Plan Modification", False, "Failed to create test user")
                return False
            
            created_user = create_response.json()
            user_id = created_user['id']
            self.created_users.append(user_id)
            
            sleep(1)

            # Create a second plan for testing plan changes
            plan2_data = {
                "name": f"Test Plan 2 {datetime.now().timestamp()}",
                "description": "Second test plan for plan modification testing",
                "price": 75.0,
                "duration_days": 60,
                "gym_id": self.test_gym_id,
                "is_active": True
            }
            
            plan2_response = requests.post(f"{self.base_url}/plans/", json=plan2_data, headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            if plan2_response.status_code != 200:
                self.print_test_result("Update User Plan Modification", False, "Failed to create second test plan")
                return False
            
            plan2 = plan2_response.json()
            plan2_id = plan2['id']
            self.created_plans.append(plan2_id)
            
            # Test 1: Update user with new plan
            update_data = {
                "plan_id": plan2_id
            }
            
            update_response = requests.put(f"{self.base_url}/users/{user_id}", json=update_data, headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            success = update_response.status_code == 200
            if success:
                updated_user = update_response.json()
                active_plan = updated_user.get('active_plan')
                if active_plan and active_plan.get('plan_id') == plan2_id:
                    self.print_test_result("Update User Plan Modification", success, 
                                         f"Successfully updated user plan to Plan ID: {plan2_id}")
                else:
                    self.print_test_result("Update User Plan Modification", False, 
                                         "Plan was not properly updated in response")
                    return False
            else:
                self.print_test_result("Update User Plan Modification", success, update_response.text)
                return False
            
            return True
            
        except Exception as e:
            self.print_test_result("Update User Plan Modification", False, str(e))
            return False

    def test_trainer_update_user_plan(self):
        """Test that trainers can update regular user plans"""
        print("=== Testing Trainer Update User Plan ===")
        
        if not self.trainer_token or not self.test_plan_id:
            self.print_test_result("Trainer Update User Plan", False, "Missing trainer token or plan")
            return False
        
        # First create a regular user
        user_data = {
            "email": f"trainerplanuser{datetime.now().timestamp()}@test.com",
            "full_name": "Trainer Plan Test User",
            "document_id": f"TRAINERPLAN{datetime.now().timestamp()}",
            "phone_number": "7777777777",
            "role": "user",
            "plan_id": self.test_plan_id
        }
        
        try:
            # Create user with admin token (trainers can't create users)
            create_response = requests.post(f"{self.base_url}/users/with-plan", json=user_data, headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            if create_response.status_code != 200:
                self.print_test_result("Trainer Update User Plan", False, "Failed to create test user")
                return False
            
            created_user = create_response.json()
            user_id = created_user['id']
            self.created_users.append(user_id)

            sleep(1)
            
            # Create a new plan for the trainer to assign
            # Use gym_id=16 since that's where the trainer is from
            plan_data = {
                "name": f"Trainer Plan {datetime.now().timestamp()}",
                "description": "Plan created by trainer",
                "price": 80.0,
                "duration_days": 45,
                "gym_id": 16,  # Use gym 16 to match trainer's gym
                "is_active": True
            }
            
            plan_response = requests.post(f"{self.base_url}/plans/", json=plan_data, headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            if plan_response.status_code != 200:
                self.print_test_result("Trainer Update User Plan", False, "Failed to create test plan")
                return False
            
            plan = plan_response.json()
            plan_id = plan['id']
            self.created_plans.append(plan_id)
            
            # Test: Trainer updates user plan
            update_data = {
                "plan_id": plan_id
            }
            
            update_response = requests.put(f"{self.base_url}/users/{user_id}", json=update_data, headers={
                "Authorization": f"Bearer {self.trainer_token}"
            })
            
            success = update_response.status_code == 200
            if success:
                updated_user = update_response.json()
                active_plan = updated_user.get('active_plan')
                if active_plan and active_plan.get('plan_id') == plan_id:
                    self.print_test_result("Trainer Update User Plan", success, 
                                         f"Trainer successfully updated user plan to Plan ID: {plan_id}")
                else:
                    self.print_test_result("Trainer Update User Plan", False, 
                                         "Plan was not properly updated by trainer")
                    return False
            else:
                self.print_test_result("Trainer Update User Plan", success, update_response.text)
                return False
            
            return True
            
        except Exception as e:
            self.print_test_result("Trainer Update User Plan", False, str(e))
            return False

    def test_plan_modification_active_plan_detection(self):
        """Test that newly added plans are correctly detected as active plans"""
        print("=== Testing Plan Modification Active Plan Detection ===")
        
        if not self.admin_token or not self.test_gym_id or not self.test_plan_id:
            self.print_test_result("Plan Modification Active Plan Detection", False, "Missing token, gym, or plan")
            return False
        
        # First create a user with initial plan
        user_data = {
            "email": f"activeplanuser{datetime.now().timestamp()}@test.com",
            "full_name": "Active Plan Test User",
            "document_id": f"ACTIVEPLAN{datetime.now().timestamp()}",
            "phone_number": "8888888888",
            "role": "user",
            "plan_id": self.test_plan_id
        }
        
        try:
            # Create user with initial plan
            create_response = requests.post(f"{self.base_url}/users/with-plan", json=user_data, headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            if create_response.status_code != 200:
                self.print_test_result("Plan Modification Active Plan Detection", False, "Failed to create test user")
                return False
            
            created_user = create_response.json()
            user_id = created_user['id']
            self.created_users.append(user_id)
            
            # Verify initial plan is active
            initial_active_plan = created_user.get('active_plan')
            if not initial_active_plan or initial_active_plan.get('plan_id') != self.test_plan_id:
                self.print_test_result("Plan Modification Active Plan Detection", False, "Initial plan not properly set as active")
                return False
            
            sleep(1)
            
            # Create a second plan
            plan2_data = {
                "name": f"Second Plan {datetime.now().timestamp()}",
                "description": "Second plan for active plan testing",
                "price": 75.0,
                "duration_days": 60,
                "gym_id": self.test_gym_id,
                "is_active": True
            }
            
            plan2_response = requests.post(f"{self.base_url}/plans/", json=plan2_data, headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            if plan2_response.status_code != 200:
                self.print_test_result("Plan Modification Active Plan Detection", False, "Failed to create second test plan")
                return False
            
            plan2 = plan2_response.json()
            plan2_id = plan2['id']
            self.created_plans.append(plan2_id)
            
            # Update user with new plan
            update_data = {
                "plan_id": plan2_id
            }
            
            update_response = requests.put(f"{self.base_url}/users/{user_id}", json=update_data, headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            success = update_response.status_code == 200
            if success:
                updated_user = update_response.json()
                new_active_plan = updated_user.get('active_plan')
                
                if new_active_plan and new_active_plan.get('plan_id') == plan2_id:
                    self.print_test_result("Plan Modification Active Plan Detection", success, 
                                         f"New plan correctly detected as active: Plan ID {plan2_id}")
                else:
                    self.print_test_result("Plan Modification Active Plan Detection", False, 
                                         f"New plan not detected as active. Expected Plan ID {plan2_id}, got {new_active_plan.get('plan_id') if new_active_plan else 'None'}")
                    return False
            else:
                self.print_test_result("Plan Modification Active Plan Detection", success, update_response.text)
                return False
            
            return True
            
        except Exception as e:
            self.print_test_result("Plan Modification Active Plan Detection", False, str(e))
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("Starting User Endpoints Test Suite")
        print("=" * 50)
        
        # Test authentication first
        if not self.test_authentication():
            print("❌ Authentication failed. Cannot proceed with other tests.")
            return False
        
        # Setup test data
        self.setup_test_data()
        
        # Run all tests
        tests = [
            self.test_read_users,
            self.test_create_admin_user,
            self.test_create_trainer_user,
            self.test_create_regular_user_with_plan,
            self.test_search_user_by_document_id,
            self.test_search_users_by_phone,
            self.test_read_trainers,
            self.test_read_regular_users,
            self.test_update_user_basic,
            self.test_update_user_with_new_plan,
            self.test_update_user_plan_not_found,
            self.test_update_user_duplicate_email,
            self.test_update_user_not_found,
            self.test_update_user_unauthorized,
            self.test_delete_user,
            self.test_delete_user_not_found,
            self.test_unauthorized_access,
            self.test_trainer_can_only_view_regular_users,
            self.test_update_user_plan_modification,
            self.test_trainer_update_user_plan,
            self.test_plan_modification_active_plan_detection,
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                print(f"❌ Test {test.__name__} failed with exception: {str(e)}")
        
        print("=" * 50)
        print(f"Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("All tests passed!")
        else:
            print("Some tests failed. Check the output above for details.")
        
        # Clean up test data at the end
        self.cleanup_test_data()
        
        return passed == total

def main():
    """Main function"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = BASE_URL
    
    print(f"Testing user endpoints at: {base_url}")
    print("Make sure the server is running on this URL")
    print()
    
    tester = UserEndpointTester(base_url)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 