#!/usr/bin/env python3
"""
Simple test script for gym endpoints
Run this script to test the gym endpoints manually
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

class GymEndpointTester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.admin_token = None
        self.trainer_token = None
        
        # Track created test data for cleanup
        self.created_gyms = []
        
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
    
    def test_read_gyms_public(self):
        """Test reading gyms without authentication (public endpoint)"""
        print("=== Testing Read Gyms (Public) ===")
        
        try:
            response = requests.get(f"{self.base_url}/gyms/")
            
            success = response.status_code == 200
            gyms = response.json() if success else []
            self.print_test_result("Read Gyms (Public)", success, f"Found {len(gyms)} gyms")
            
            return success
        except Exception as e:
            self.print_test_result("Read Gyms (Public)", False, str(e))
            return False
    
    def test_read_active_gyms_authenticated(self):
        """Test reading active gyms with authentication"""
        print("=== Testing Read Active Gyms (Authenticated) ===")
        
        if not self.admin_token:
            self.print_test_result("Read Active Gyms (Authenticated)", False, "No admin token")
            return False
        
        try:
            response = requests.get(f"{self.base_url}/gyms/active", headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            success = response.status_code == 200
            gyms = response.json() if success else []
            self.print_test_result("Read Active Gyms (Authenticated)", success, f"Found {len(gyms)} active gyms")
            
            return success
        except Exception as e:
            self.print_test_result("Read Active Gyms (Authenticated)", False, str(e))
            return False
    
    def test_create_gym(self):
        """Test creating a gym"""
        print("=== Testing Create Gym ===")
        
        if not self.admin_token:
            self.print_test_result("Create Gym", False, "No admin token")
            return False
        
        gym_data = {
            "name": f"Test Gym {datetime.now().timestamp()}",
            "address": f"Test Address {datetime.now().timestamp()}",
            "is_active": True
        }
        
        try:
            response = requests.post(f"{self.base_url}/gyms/", json=gym_data, headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            success = response.status_code == 200
            if success:
                gym = response.json()
                self.created_gyms.append(gym['id'])
                self.print_test_result("Create Gym", success, f"Created gym ID: {gym['id']}")
                return gym['id']  # Return the gym ID for later tests
            else:
                self.print_test_result("Create Gym", success, response.text)
                return None
        except Exception as e:
            self.print_test_result("Create Gym", False, str(e))
            return None
    
    def test_create_gym_duplicate_name(self):
        """Test creating a gym with duplicate name"""
        print("=== Testing Create Gym (Duplicate Name) ===")
        
        if not self.admin_token:
            self.print_test_result("Create Gym (Duplicate Name)", False, "No admin token")
            return False
        
        gym_data = {
            "name": f"Duplicate Test Gym {datetime.now().timestamp()}",
            "address": "Duplicate Address",
            "is_active": True
        }
        
        try:
            # Create first gym
            response1 = requests.post(f"{self.base_url}/gyms/", json=gym_data, headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            if response1.status_code != 200:
                self.print_test_result("Create Gym (Duplicate Name)", False, "Failed to create first gym")
                return False
            
            gym1 = response1.json()
            self.created_gyms.append(gym1['id'])
            
            # Now try to create second gym with same name
            gym_data["name"] = gym_data["name"]  # Use the same name that was just created
            response2 = requests.post(f"{self.base_url}/gyms/", json=gym_data, headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            success = response2.status_code == 400
            self.print_test_result("Create Gym (Duplicate Name)", success, "Should fail with duplicate name")
            
            return success
        except Exception as e:
            self.print_test_result("Create Gym (Duplicate Name)", False, str(e))
            return False
    
    def test_read_specific_gym(self):
        """Test reading a specific gym"""
        print("=== Testing Read Specific Gym ===")
        
        if not self.admin_token:
            self.print_test_result("Read Specific Gym", False, "No admin token")
            return False
        
        # First create a gym to read
        gym_id = self.test_create_gym()
        if not gym_id:
            self.print_test_result("Read Specific Gym", False, "Failed to create test gym")
            return False
        
        try:
            response = requests.get(f"{self.base_url}/gyms/{gym_id}", headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            success = response.status_code == 200
            if success:
                gym = response.json()
                self.print_test_result("Read Specific Gym", success, f"Found gym: {gym['name']}")
            else:
                self.print_test_result("Read Specific Gym", success, response.text)
            
            return success
        except Exception as e:
            self.print_test_result("Read Specific Gym", False, str(e))
            return False

    def test_read_specific_gym_not_found(self):
        """Test reading a non-existent gym"""
        print("=== Testing Read Specific Gym (Not Found) ===")
        
        if not self.admin_token:
            self.print_test_result("Read Specific Gym (Not Found)", False, "No admin token")
            return False
        
        try:
            response = requests.get(f"{self.base_url}/gyms/99999", headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            success = response.status_code == 404
            if success:
                self.print_test_result("Read Specific Gym (Not Found)", success, "Correctly returned 404")
            else:
                self.print_test_result("Read Specific Gym (Not Found)", success, response.text)
            
            return success
        except Exception as e:
            self.print_test_result("Read Specific Gym (Not Found)", False, str(e))
            return False

    def test_update_gym(self):
        """Test updating a gym"""
        print("=== Testing Update Gym ===")
        
        if not self.admin_token:
            self.print_test_result("Update Gym", False, "No admin token")
            return False
        
        # First create a gym to update
        gym_id = self.test_create_gym()
        if not gym_id:
            self.print_test_result("Update Gym", False, "Failed to create test gym")
            return False
        
        try:
            update_data = {
                "name": f"Updated Test Gym {datetime.now().timestamp()}",
                "address": f"Updated Test Address {datetime.now().timestamp()}"
            }
            
            response = requests.put(f"{self.base_url}/gyms/{gym_id}", json=update_data, headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            success = response.status_code == 200
            if success:
                gym = response.json()
                self.print_test_result("Update Gym", success, f"Updated gym: {gym['name']}")
            else:
                self.print_test_result("Update Gym", success, response.text)
            
            return success
        except Exception as e:
            self.print_test_result("Update Gym", False, str(e))
            return False

    def test_update_gym_not_found(self):
        """Test updating a non-existent gym"""
        print("=== Testing Update Gym (Not Found) ===")
        
        if not self.admin_token:
            self.print_test_result("Update Gym (Not Found)", False, "No admin token")
            return False
        
        try:
            update_data = {
                "name": "Non-existent Gym"
            }
            
            response = requests.put(f"{self.base_url}/gyms/99999", json=update_data, headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            success = response.status_code == 404
            if success:
                self.print_test_result("Update Gym (Not Found)", success, "Correctly returned 404")
            else:
                self.print_test_result("Update Gym (Not Found)", success, response.text)
            
            return success
        except Exception as e:
            self.print_test_result("Update Gym (Not Found)", False, str(e))
            return False

    def test_delete_gym(self):
        """Test deleting a gym"""
        print("=== Testing Delete Gym ===")
        
        if not self.admin_token:
            self.print_test_result("Delete Gym", False, "No admin token")
            return False
        
        # First create a gym to delete
        gym_id = self.test_create_gym()
        if not gym_id:
            self.print_test_result("Delete Gym", False, "Failed to create test gym")
            return False
        
        try:
            response = requests.delete(f"{self.base_url}/gyms/{gym_id}", headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            success = response.status_code == 200
            if success:
                self.print_test_result("Delete Gym", success, f"Successfully deleted gym ID: {gym_id}")
                # Remove from cleanup list since it's already deleted
                if gym_id in self.created_gyms:
                    self.created_gyms.remove(gym_id)
            else:
                self.print_test_result("Delete Gym", success, response.text)
            
            return success
        except Exception as e:
            self.print_test_result("Delete Gym", False, str(e))
            return False

    def test_delete_gym_not_found(self):
        """Test deleting a non-existent gym"""
        print("=== Testing Delete Gym (Not Found) ===")
        
        if not self.admin_token:
            self.print_test_result("Delete Gym (Not Found)", False, "No admin token")
            return False
        
        try:
            response = requests.delete(f"{self.base_url}/gyms/99999", headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            success = response.status_code == 404
            if success:
                self.print_test_result("Delete Gym (Not Found)", success, "Correctly returned 404")
            else:
                self.print_test_result("Delete Gym (Not Found)", success, response.text)
            
            return success
        except Exception as e:
            self.print_test_result("Delete Gym (Not Found)", False, str(e))
            return False

    def test_create_gym_unauthorized(self):
        """Test creating a gym without authentication"""
        print("=== Testing Create Gym (Unauthorized) ===")
        
        gym_data = {
            "name": f"Unauthorized Test Gym {datetime.now().timestamp()}",
            "address": "Unauthorized Address",
            "is_active": True
        }
        
        try:
            response = requests.post(f"{self.base_url}/gyms/", json=gym_data)
            
            success = response.status_code == 401
            if not success:
                # Check if we got a JSON response with authentication error
                try:
                    error_detail = response.json().get("detail", "")
                    success = "Not authenticated" in error_detail or "Could not validate credentials" in error_detail
                except:
                    pass
            
            if success:
                self.print_test_result("Create Gym (Unauthorized)", success, "Correctly returned 401")
            else:
                self.print_test_result("Create Gym (Unauthorized)", success, response.text)
            
            return success
        except Exception as e:
            self.print_test_result("Create Gym (Unauthorized)", False, str(e))
            return False

    def test_pagination(self):
        """Test pagination for gyms"""
        print("=== Testing Pagination ===")
        
        if not self.admin_token:
            self.print_test_result("Pagination", False, "No admin token")
            return False
        
        try:
            response = requests.get(f"{self.base_url}/gyms/?skip=0&limit=5", headers={
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            success = response.status_code == 200
            if success:
                gyms = response.json()
                self.print_test_result("Pagination", success, f"Retrieved {len(gyms)} gyms with pagination")
            else:
                self.print_test_result("Pagination", success, response.text)
            
            return success
        except Exception as e:
            self.print_test_result("Pagination", False, str(e))
            return False

    def run_all_tests(self):
        """Run all tests"""
        print("Starting Gym Endpoints Test Suite")
        print("=" * 50)
        
        # Test authentication first
        if not self.test_authentication():
            print("❌ Authentication failed. Cannot proceed with other tests.")
            return False
        
        # Run all tests
        tests = [
            self.test_read_gyms_public,
            self.test_read_active_gyms_authenticated,
            self.test_create_gym,
            self.test_create_gym_duplicate_name,
            self.test_read_specific_gym,
            self.test_read_specific_gym_not_found,
            self.test_update_gym,
            self.test_update_gym_not_found,
            self.test_delete_gym,
            self.test_delete_gym_not_found,
            self.test_create_gym_unauthorized,
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
    
    print(f"Testing gym endpoints at: {base_url}")
    print("Make sure the server is running on this URL")
    print()
    
    tester = GymEndpointTester(base_url)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 