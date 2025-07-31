#!/usr/bin/env python3
"""
Simple test script for plan endpoints
Run this script to test the plan endpoints manually
"""

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

class PlanEndpointTester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.admin_token = None
        self.trainer_token = None
        self.test_gym_id = 16  # Use the existing test gym
        
        # Track created test data for cleanup
        self.created_plans = []
        
    def print_test_result(self, test_name, success, message=""):
        """Print test result with formatting"""
        status = "PASS" if success else "FAIL"
        print(f"{status} {test_name}")
        if message and not success:
            print(f"   Error: {message}")
        print()
    
    def login(self, email, password, gym_id=16):
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
    
    def cleanup_test_data(self):
        """Clean up all test data created during tests"""
        print("\n[Cleanup] Cleaning up test data...")
        
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
    
    def test_read_plans_admin(self):
        """Test reading plans with admin access"""
        print("=== Testing Read Plans (Admin) ===")
        
        if not self.admin_token:
            self.print_test_result("Read Plans (Admin)", False, "No admin token")
            return False
        
        try:
            response = requests.get(f"{self.base_url}/plans/", headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            success = response.status_code == 200
            plans = response.json() if success else []
            self.print_test_result("Read Plans (Admin)", success, f"Found {len(plans)} plans")
            
            return success
        except Exception as e:
            self.print_test_result("Read Plans (Admin)", False, str(e))
            return False
    
    def test_read_plans_trainer(self):
        """Test reading plans with trainer access (gym-scoped)"""
        print("=== Testing Read Plans (Trainer) ===")
        
        if not self.trainer_token:
            self.print_test_result("Read Plans (Trainer)", False, "No trainer token")
            return False
        
        try:
            response = requests.get(f"{self.base_url}/plans/", headers={
                "Authorization": f"Bearer {self.trainer_token}"
            })
            
            success = response.status_code == 200
            plans = response.json() if success else []
            self.print_test_result("Read Plans (Trainer)", success, f"Found {len(plans)} plans")
            
            return success
        except Exception as e:
            self.print_test_result("Read Plans (Trainer)", False, str(e))
            return False
    
    def test_read_active_plans(self):
        """Test reading active plans"""
        print("=== Testing Read Active Plans ===")
        
        if not self.admin_token:
            self.print_test_result("Read Active Plans", False, "No admin token")
            return False
        
        try:
            response = requests.get(f"{self.base_url}/plans/active", headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            success = response.status_code == 200
            plans = response.json() if success else []
            self.print_test_result("Read Active Plans", success, f"Found {len(plans)} active plans")
            
            return success
        except Exception as e:
            self.print_test_result("Read Active Plans", False, str(e))
            return False
    
    def test_create_plan(self):
        """Test creating a plan"""
        print("=== Testing Create Plan ===")
        
        if not self.admin_token:
            self.print_test_result("Create Plan", False, "No admin token")
            return False
        
        plan_data = {
            "name": f"Test Plan {datetime.now().timestamp()}",
            "description": f"Test Description {datetime.now().timestamp()}",
            "price": 50.0,
            "duration_days": 30,
            "gym_id": self.test_gym_id,
            "is_active": True
        }
        
        try:
            response = requests.post(f"{self.base_url}/plans/", json=plan_data, headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            success = response.status_code == 200
            if success:
                plan = response.json()
                self.created_plans.append(plan['id'])
                self.print_test_result("Create Plan", success, f"Created plan ID: {plan['id']}")
                return plan['id']  # Return the plan ID for later tests
            else:
                self.print_test_result("Create Plan", success, response.text)
                return None
        except Exception as e:
            self.print_test_result("Create Plan", False, str(e))
            return None
    
    def test_create_plan_duplicate_name(self):
        """Test creating a plan with duplicate name in the same gym"""
        print("=== Testing Create Plan (Duplicate Name) ===")
        
        if not self.admin_token:
            self.print_test_result("Create Plan (Duplicate Name)", False, "No admin token")
            return False
        
        plan_data = {
            "name": f"Duplicate Test Plan {datetime.now().timestamp()}",
            "description": "Duplicate Description",
            "price": 60.0,
            "duration_days": 45,
            "gym_id": self.test_gym_id,
            "is_active": True
        }
        
        try:
            # Create first plan
            response1 = requests.post(f"{self.base_url}/plans/", json=plan_data, headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            if response1.status_code != 200:
                self.print_test_result("Create Plan (Duplicate Name)", False, "Failed to create first plan")
                return False
            
            plan1 = response1.json()
            self.created_plans.append(plan1['id'])
            
            # Now try to create second plan with same name in same gym
            plan_data["name"] = plan_data["name"]  # Use the same name that was just created
            response2 = requests.post(f"{self.base_url}/plans/", json=plan_data, headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            success = response2.status_code == 400
            self.print_test_result("Create Plan (Duplicate Name)", success, "Should fail with duplicate name")
            
            return success
        except Exception as e:
            self.print_test_result("Create Plan (Duplicate Name)", False, str(e))
            return False
    
    def test_read_specific_plan(self):
        """Test reading a specific plan"""
        print("=== Testing Read Specific Plan ===")
        
        if not self.admin_token:
            self.print_test_result("Read Specific Plan", False, "No admin token")
            return False
        
        # First create a plan to read
        plan_id = self.test_create_plan()
        if not plan_id:
            self.print_test_result("Read Specific Plan", False, "Failed to create test plan")
            return False
        
        try:
            response = requests.get(f"{self.base_url}/plans/{plan_id}", headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            success = response.status_code == 200
            if success:
                plan = response.json()
                self.print_test_result("Read Specific Plan", success, f"Found plan: {plan['name']}")
            else:
                self.print_test_result("Read Specific Plan", success, response.text)
            
            return success
        except Exception as e:
            self.print_test_result("Read Specific Plan", False, str(e))
            return False

    def test_read_specific_plan_not_found(self):
        """Test reading a non-existent plan"""
        print("=== Testing Read Specific Plan (Not Found) ===")
        
        if not self.admin_token:
            self.print_test_result("Read Specific Plan (Not Found)", False, "No admin token")
            return False
        
        try:
            response = requests.get(f"{self.base_url}/plans/99999", headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            success = response.status_code == 404
            if success:
                self.print_test_result("Read Specific Plan (Not Found)", success, "Correctly returned 404")
            else:
                self.print_test_result("Read Specific Plan (Not Found)", success, response.text)
            
            return success
        except Exception as e:
            self.print_test_result("Read Specific Plan (Not Found)", False, str(e))
            return False

    def test_update_plan(self):
        """Test updating a plan"""
        print("=== Testing Update Plan ===")
        
        if not self.admin_token:
            self.print_test_result("Update Plan", False, "No admin token")
            return False
        
        # First create a plan to update
        plan_id = self.test_create_plan()
        if not plan_id:
            self.print_test_result("Update Plan", False, "Failed to create test plan")
            return False
        
        try:
            update_data = {
                "name": f"Updated Test Plan {datetime.now().timestamp()}",
                "description": f"Updated Test Description {datetime.now().timestamp()}",
                "price": 75.0
            }
            
            response = requests.put(f"{self.base_url}/plans/{plan_id}", json=update_data, headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            success = response.status_code == 200
            if success:
                plan = response.json()
                self.print_test_result("Update Plan", success, f"Updated plan: {plan['name']}")
            else:
                self.print_test_result("Update Plan", success, response.text)
            
            return success
        except Exception as e:
            self.print_test_result("Update Plan", False, str(e))
            return False

    def test_update_plan_not_found(self):
        """Test updating a non-existent plan"""
        print("=== Testing Update Plan (Not Found) ===")
        
        if not self.admin_token:
            self.print_test_result("Update Plan (Not Found)", False, "No admin token")
            return False
        
        try:
            update_data = {
                "name": "Non-existent Plan"
            }
            
            response = requests.put(f"{self.base_url}/plans/99999", json=update_data, headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            success = response.status_code == 404
            if success:
                self.print_test_result("Update Plan (Not Found)", success, "Correctly returned 404")
            else:
                self.print_test_result("Update Plan (Not Found)", success, response.text)
            
            return success
        except Exception as e:
            self.print_test_result("Update Plan (Not Found)", False, str(e))
            return False

    def test_delete_plan(self):
        """Test deleting a plan"""
        print("=== Testing Delete Plan ===")
        
        if not self.admin_token:
            self.print_test_result("Delete Plan", False, "No admin token")
            return False
        
        # First create a plan to delete
        plan_id = self.test_create_plan()
        if not plan_id:
            self.print_test_result("Delete Plan", False, "Failed to create test plan")
            return False
        
        try:
            response = requests.delete(f"{self.base_url}/plans/{plan_id}", headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            success = response.status_code == 200
            if success:
                self.print_test_result("Delete Plan", success, f"Successfully deleted plan ID: {plan_id}")
                # Remove from cleanup list since it's already deleted
                if plan_id in self.created_plans:
                    self.created_plans.remove(plan_id)
            else:
                self.print_test_result("Delete Plan", success, response.text)
            
            return success
        except Exception as e:
            self.print_test_result("Delete Plan", False, str(e))
            return False

    def test_delete_plan_not_found(self):
        """Test deleting a non-existent plan"""
        print("=== Testing Delete Plan (Not Found) ===")
        
        if not self.admin_token:
            self.print_test_result("Delete Plan (Not Found)", False, "No admin token")
            return False
        
        try:
            response = requests.delete(f"{self.base_url}/plans/99999", headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            success = response.status_code == 404
            if success:
                self.print_test_result("Delete Plan (Not Found)", success, "Correctly returned 404")
            else:
                self.print_test_result("Delete Plan (Not Found)", success, response.text)
            
            return success
        except Exception as e:
            self.print_test_result("Delete Plan (Not Found)", False, str(e))
            return False

    def test_create_plan_unauthorized(self):
        """Test creating a plan without authentication"""
        print("=== Testing Create Plan (Unauthorized) ===")
        
        plan_data = {
            "name": f"Unauthorized Test Plan {datetime.now().timestamp()}",
            "description": "Unauthorized Description",
            "price": 100.0,
            "duration_days": 90,
            "gym_id": self.test_gym_id,
            "is_active": True
        }
        
        try:
            response = requests.post(f"{self.base_url}/plans/", json=plan_data)
            
            success = response.status_code == 401
            if not success:
                # Check if we got a JSON response with authentication error
                try:
                    error_detail = response.json().get("detail", "")
                    success = "Not authenticated" in error_detail or "Could not validate credentials" in error_detail
                except:
                    pass
            
            if success:
                self.print_test_result("Create Plan (Unauthorized)", success, "Correctly returned 401")
            else:
                self.print_test_result("Create Plan (Unauthorized)", success, response.text)
            
            return success
        except Exception as e:
            self.print_test_result("Create Plan (Unauthorized)", False, str(e))
            return False

    def test_pagination(self):
        """Test pagination for plans"""
        print("=== Testing Pagination ===")
        
        if not self.admin_token:
            self.print_test_result("Pagination", False, "No admin token")
            return False
        
        try:
            response = requests.get(f"{self.base_url}/plans/?skip=0&limit=5", headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            success = response.status_code == 200
            if success:
                plans = response.json()
                self.print_test_result("Pagination", success, f"Retrieved {len(plans)} plans with pagination")
            else:
                self.print_test_result("Pagination", success, response.text)
            
            return success
        except Exception as e:
            self.print_test_result("Pagination", False, str(e))
            return False

    def run_all_tests(self):
        """Run all tests"""
        print("Starting Plan Endpoints Test Suite")
        print("=" * 50)
        
        # Test authentication first
        if not self.test_authentication():
            print("❌ Authentication failed. Cannot proceed with other tests.")
            return False
        
        # Run all tests
        tests = [
            self.test_read_plans_admin,
            self.test_read_plans_trainer,
            self.test_read_active_plans,
            self.test_create_plan,
            self.test_create_plan_duplicate_name,
            self.test_read_specific_plan,
            self.test_read_specific_plan_not_found,
            self.test_update_plan,
            self.test_update_plan_not_found,
            self.test_delete_plan,
            self.test_delete_plan_not_found,
            self.test_create_plan_unauthorized,
            self.test_pagination,
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
    
    print(f"Testing plan endpoints at: {base_url}")
    print("Make sure the server is running on this URL")
    print()
    
    tester = PlanEndpointTester(base_url)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 