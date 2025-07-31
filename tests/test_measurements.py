#!/usr/bin/env python3
"""
Test script for Measurements endpoints
Tests all CRUD operations and special endpoints for measurements
"""

import requests
import json
import time
from datetime import datetime, date
from decimal import Decimal

# Configuration
BASE_URL = "http://localhost:8001/api/v1"
MEASUREMENTS_URL = f"{BASE_URL}/measurements"

class MeasurementTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.trainer_token = None
        self.created_measurements = []
        self.created_users = []
        self.created_gyms = []
        self.created_plans = []
        
    def print_test_result(self, test_name, success, message=""):
        """Print test result with consistent formatting"""
        status = "[OK]" if success else "[FAIL]"
        print(f"{status} {test_name}")
        if message:
            print(f"    {message}")
        print()

    def login_admin(self):
        """Login as admin"""
        login_data = {
            "email": "admin@test.com",
            "password": "admin123",
            "gym_id": 16
        }
        response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            self.admin_token = response.json()["access_token"]
            return True
        return False

    def login_trainer(self):
        """Login as trainer"""
        login_data = {
            "email": "trainer@test.com", 
            "password": "trainer123",
            "gym_id": 16
        }
        response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            self.trainer_token = response.json()["access_token"]
            return True
        return False

    def create_test_user(self, name="Test User", email=None, gym_id=16):
        """Create a test user for measurements"""
        if not email:
            email = f"user_{int(time.time())}@test.com"
        
        user_data = {
            "full_name": name,
            "email": email,
            "document_id": f"DOC{int(time.time())}",
            "phone": f"+123456789{int(time.time()) % 10000}",
            "birth_date": "1990-01-01",
            "gender": "male",
            "address": "Test Address",
            "emergency_contact": "Emergency Contact",
            "emergency_phone": "+1234567890"
        }
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = self.session.post(f"{BASE_URL}/users/", json=user_data, headers=headers)
        
        if response.status_code == 200:
            user = response.json()
            self.created_users.append(user["id"])
            return user
        else:
            print(f"Failed to create test user: {response.text}")
            return None

    def create_test_measurement(self, user_id, measurement_data=None):
        """Create a test measurement"""
        if not measurement_data:
            measurement_data = {
                "user_id": user_id,
                "height": 175.5,
                "weight": 70.2,
                "chest": 95.0,
                "shoulders": 110.0,
                "biceps_left": 32.5,
                "biceps_right": 32.8,
                "forearms_left": 28.0,
                "forearms_right": 28.2,
                "abdomen": 85.0,
                "hips": 95.0,
                "thighs_left": 55.0,
                "thighs_right": 55.2,
                "calves_left": 35.0,
                "calves_right": 35.1,
                "notes": "Test measurement"
            }
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = self.session.post(MEASUREMENTS_URL, json=measurement_data, headers=headers)
        
        if response.status_code == 200:
            measurement = response.json()
            self.created_measurements.append(measurement["id"])
            return measurement
        else:
            print(f"Failed to create test measurement: {response.text}")
            return None

    def test_login(self):
        """Test admin and trainer login"""
        print("Testing login...")
        
        # Test admin login
        if self.login_admin():
            self.print_test_result("Admin login", True)
        else:
            self.print_test_result("Admin login", False, "Failed to login as admin")
            return False
        
        # Test trainer login
        if self.login_trainer():
            self.print_test_result("Trainer login", True)
        else:
            self.print_test_result("Trainer login", False, "Failed to login as trainer")
            return False
        
        return True

    def test_create_measurement(self):
        """Test creating a measurement"""
        print("Testing create measurement...")
        
        # Create test user
        user = self.create_test_user("Measurement Test User")
        if not user:
            self.print_test_result("Create measurement", False, "Failed to create test user")
            return False
        
        # Create measurement
        measurement_data = {
            "user_id": user["id"],
            "height": 175.5,
            "weight": 70.2,
            "chest": 95.0,
            "shoulders": 110.0,
            "biceps_left": 32.5,
            "biceps_right": 32.8,
            "forearms_left": 28.0,
            "forearms_right": 28.2,
            "abdomen": 85.0,
            "hips": 95.0,
            "thighs_left": 55.0,
            "thighs_right": 55.2,
            "calves_left": 35.0,
            "calves_right": 35.1,
            "notes": "Test measurement"
        }
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = self.session.post(MEASUREMENTS_URL, json=measurement_data, headers=headers)
        
        if response.status_code == 200:
            measurement = response.json()
            self.created_measurements.append(measurement["id"])
            self.print_test_result("Create measurement", True, f"Created measurement ID: {measurement['id']}")
            return True
        else:
            self.print_test_result("Create measurement", False, f"Status: {response.status_code}, Response: {response.text}")
            return False

    def test_create_measurement_trainer(self):
        """Test creating a measurement as trainer"""
        print("Testing create measurement as trainer...")
        
        # Create test user
        user = self.create_test_user("Trainer Measurement User")
        if not user:
            self.print_test_result("Create measurement as trainer", False, "Failed to create test user")
            return False
        
        # Create measurement as trainer
        measurement_data = {
            "user_id": user["id"],
            "height": 180.0,
            "weight": 75.0,
            "chest": 100.0,
            "shoulders": 115.0,
            "notes": "Trainer measurement"
        }
        
        headers = {"Authorization": f"Bearer {self.trainer_token}"}
        response = self.session.post(MEASUREMENTS_URL, json=measurement_data, headers=headers)
        
        if response.status_code == 200:
            measurement = response.json()
            self.created_measurements.append(measurement["id"])
            self.print_test_result("Create measurement as trainer", True, f"Created measurement ID: {measurement['id']}")
            return True
        else:
            self.print_test_result("Create measurement as trainer", False, f"Status: {response.status_code}, Response: {response.text}")
            return False

    def test_create_measurement_invalid_user(self):
        """Test creating a measurement with invalid user ID"""
        print("Testing create measurement with invalid user...")
        
        measurement_data = {
            "user_id": 99999,  # Non-existent user
            "height": 175.5,
            "weight": 70.2
        }
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = self.session.post(MEASUREMENTS_URL, json=measurement_data, headers=headers)
        
        if response.status_code == 404:
            self.print_test_result("Create measurement invalid user", True, "Correctly rejected invalid user")
            return True
        else:
            self.print_test_result("Create measurement invalid user", False, f"Expected 404, got {response.status_code}")
            return False

    def test_read_measurements(self):
        """Test reading all measurements"""
        print("Testing read measurements...")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = self.session.get(MEASUREMENTS_URL, headers=headers)
        
        if response.status_code == 200:
            measurements = response.json()
            self.print_test_result("Read measurements", True, f"Found {len(measurements)} measurements")
            return True
        else:
            self.print_test_result("Read measurements", False, f"Status: {response.status_code}, Response: {response.text}")
            return False

    def test_read_measurements_with_filters(self):
        """Test reading measurements with filters"""
        print("Testing read measurements with filters...")
        
        # Create test user and measurements
        user = self.create_test_user("Filter Test User")
        if not user:
            self.print_test_result("Read measurements with filters", False, "Failed to create test user")
            return False
        
        # Create two measurements with different dates
        measurement1_data = {
            "user_id": user["id"],
            "weight": 70.0,
            "measurement_date": "2024-01-01T10:00:00Z"
        }
        
        measurement2_data = {
            "user_id": user["id"],
            "weight": 72.0,
            "measurement_date": "2024-02-01T10:00:00Z"
        }
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Create measurements
        response1 = self.session.post(MEASUREMENTS_URL, json=measurement1_data, headers=headers)
        response2 = self.session.post(MEASUREMENTS_URL, json=measurement2_data, headers=headers)
        
        if response1.status_code == 200 and response2.status_code == 200:
            measurement1 = response1.json()
            measurement2 = response2.json()
            self.created_measurements.extend([measurement1["id"], measurement2["id"]])
            
            # Test filter by user_id
            response = self.session.get(f"{MEASUREMENTS_URL}?user_id={user['id']}", headers=headers)
            if response.status_code == 200:
                measurements = response.json()
                if len(measurements) >= 2:
                    self.print_test_result("Read measurements with user filter", True, f"Found {len(measurements)} measurements for user")
                else:
                    self.print_test_result("Read measurements with user filter", False, f"Expected at least 2 measurements, found {len(measurements)}")
                    return False
            else:
                self.print_test_result("Read measurements with user filter", False, f"Status: {response.status_code}")
                return False
            
            # Test filter by date range
            response = self.session.get(f"{MEASUREMENTS_URL}?start_date=2024-01-15&end_date=2024-02-15", headers=headers)
            if response.status_code == 200:
                measurements = response.json()
                self.print_test_result("Read measurements with date filter", True, f"Found {len(measurements)} measurements in date range")
                return True
            else:
                self.print_test_result("Read measurements with date filter", False, f"Status: {response.status_code}")
                return False
        else:
            self.print_test_result("Read measurements with filters", False, "Failed to create test measurements")
            return False

    def test_read_user_measurements(self):
        """Test reading measurements for a specific user"""
        print("Testing read user measurements...")
        
        # Create test user and measurement
        user = self.create_test_user("User Measurements Test")
        if not user:
            self.print_test_result("Read user measurements", False, "Failed to create test user")
            return False
        
        measurement = self.create_test_measurement(user["id"])
        if not measurement:
            self.print_test_result("Read user measurements", False, "Failed to create test measurement")
            return False
        
        # Read user measurements
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = self.session.get(f"{MEASUREMENTS_URL}/user/{user['id']}", headers=headers)
        
        if response.status_code == 200:
            measurements = response.json()
            if len(measurements) >= 1:
                self.print_test_result("Read user measurements", True, f"Found {len(measurements)} measurements for user")
                return True
            else:
                self.print_test_result("Read user measurements", False, "No measurements found for user")
                return False
        else:
            self.print_test_result("Read user measurements", False, f"Status: {response.status_code}, Response: {response.text}")
            return False

    def test_get_latest_measurement(self):
        """Test getting the latest measurement for a user"""
        print("Testing get latest measurement...")
        
        # Create test user and measurements
        user = self.create_test_user("Latest Measurement Test")
        if not user:
            self.print_test_result("Get latest measurement", False, "Failed to create test user")
            return False
        
        # Create two measurements with different dates
        measurement1_data = {
            "user_id": user["id"],
            "weight": 70.0,
            "measurement_date": "2024-01-01T10:00:00Z"
        }
        
        measurement2_data = {
            "user_id": user["id"],
            "weight": 72.0,
            "measurement_date": "2024-02-01T10:00:00Z"
        }
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Create measurements
        response1 = self.session.post(MEASUREMENTS_URL, json=measurement1_data, headers=headers)
        response2 = self.session.post(MEASUREMENTS_URL, json=measurement2_data, headers=headers)
        
        if response1.status_code == 200 and response2.status_code == 200:
            measurement1 = response1.json()
            measurement2 = response2.json()
            self.created_measurements.extend([measurement1["id"], measurement2["id"]])
            
            # Get latest measurement
            response = self.session.get(f"{MEASUREMENTS_URL}/user/{user['id']}/latest", headers=headers)
            
            if response.status_code == 200:
                latest = response.json()
                if latest["weight"] == 72.0:  # Should be the newer measurement
                    self.print_test_result("Get latest measurement", True, f"Latest measurement weight: {latest['weight']}")
                    return True
                else:
                    self.print_test_result("Get latest measurement", False, f"Expected weight 72.0, got {latest['weight']}")
                    return False
            else:
                self.print_test_result("Get latest measurement", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        else:
            self.print_test_result("Get latest measurement", False, "Failed to create test measurements")
            return False

    def test_get_user_progress(self):
        """Test getting user progress"""
        print("Testing get user progress...")
        
        # Create test user and measurements
        user = self.create_test_user("Progress Test User")
        if not user:
            self.print_test_result("Get user progress", False, "Failed to create test user")
            return False
        
        # Create measurements with different weights to show progress
        measurement1_data = {
            "user_id": user["id"],
            "weight": 80.0,
            "chest": 100.0,
            "measurement_date": "2024-01-01T10:00:00Z"
        }
        
        measurement2_data = {
            "user_id": user["id"],
            "weight": 75.0,
            "chest": 95.0,
            "measurement_date": "2024-02-01T10:00:00Z"
        }
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Create measurements
        response1 = self.session.post(MEASUREMENTS_URL, json=measurement1_data, headers=headers)
        response2 = self.session.post(MEASUREMENTS_URL, json=measurement2_data, headers=headers)
        
        if response1.status_code == 200 and response2.status_code == 200:
            measurement1 = response1.json()
            measurement2 = response2.json()
            self.created_measurements.extend([measurement1["id"], measurement2["id"]])
            
            # Get progress
            response = self.session.get(f"{MEASUREMENTS_URL}/user/{user['id']}/progress", headers=headers)
            
            if response.status_code == 200:
                progress = response.json()
                if "progress" in progress and "weight" in progress["progress"]:
                    weight_progress = progress["progress"]["weight"]
                    if weight_progress["change"] == -5.0:  # 75.0 - 80.0
                        self.print_test_result("Get user progress", True, f"Weight change: {weight_progress['change']}kg")
                        return True
                    else:
                        self.print_test_result("Get user progress", False, f"Expected weight change -5.0, got {weight_progress['change']}")
                        return False
                else:
                    self.print_test_result("Get user progress", False, "No progress data found")
                    return False
            else:
                self.print_test_result("Get user progress", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        else:
            self.print_test_result("Get user progress", False, "Failed to create test measurements")
            return False

    def test_read_measurement(self):
        """Test reading a specific measurement"""
        print("Testing read measurement...")
        
        # Create test user and measurement
        user = self.create_test_user("Read Measurement Test")
        if not user:
            self.print_test_result("Read measurement", False, "Failed to create test user")
            return False
        
        measurement = self.create_test_measurement(user["id"])
        if not measurement:
            self.print_test_result("Read measurement", False, "Failed to create test measurement")
            return False
        
        # Read specific measurement
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = self.session.get(f"{MEASUREMENTS_URL}/{measurement['id']}", headers=headers)
        
        if response.status_code == 200:
            retrieved_measurement = response.json()
            if retrieved_measurement["id"] == measurement["id"]:
                self.print_test_result("Read measurement", True, f"Retrieved measurement ID: {retrieved_measurement['id']}")
                return True
            else:
                self.print_test_result("Read measurement", False, "Retrieved wrong measurement")
                return False
        else:
            self.print_test_result("Read measurement", False, f"Status: {response.status_code}, Response: {response.text}")
            return False

    def test_read_measurement_not_found(self):
        """Test reading a non-existent measurement"""
        print("Testing read measurement not found...")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = self.session.get(f"{MEASUREMENTS_URL}/99999", headers=headers)
        
        if response.status_code == 404:
            self.print_test_result("Read measurement not found", True, "Correctly returned 404")
            return True
        else:
            self.print_test_result("Read measurement not found", False, f"Expected 404, got {response.status_code}")
            return False

    def test_update_measurement(self):
        """Test updating a measurement"""
        print("Testing update measurement...")
        
        # Create test user and measurement
        user = self.create_test_user("Update Measurement Test")
        if not user:
            self.print_test_result("Update measurement", False, "Failed to create test user")
            return False
        
        measurement = self.create_test_measurement(user["id"])
        if not measurement:
            self.print_test_result("Update measurement", False, "Failed to create test measurement")
            return False
        
        # Update measurement
        update_data = {
            "weight": 75.5,
            "notes": "Updated measurement"
        }
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = self.session.put(f"{MEASUREMENTS_URL}/{measurement['id']}", json=update_data, headers=headers)
        
        if response.status_code == 200:
            updated_measurement = response.json()
            if updated_measurement["weight"] == 75.5 and updated_measurement["notes"] == "Updated measurement":
                self.print_test_result("Update measurement", True, f"Updated measurement ID: {updated_measurement['id']}")
                return True
            else:
                self.print_test_result("Update measurement", False, "Measurement not updated correctly")
                return False
        else:
            self.print_test_result("Update measurement", False, f"Status: {response.status_code}, Response: {response.text}")
            return False

    def test_update_measurement_not_found(self):
        """Test updating a non-existent measurement"""
        print("Testing update measurement not found...")
        
        update_data = {
            "weight": 75.5
        }
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = self.session.put(f"{MEASUREMENTS_URL}/99999", json=update_data, headers=headers)
        
        if response.status_code == 404:
            self.print_test_result("Update measurement not found", True, "Correctly returned 404")
            return True
        else:
            self.print_test_result("Update measurement not found", False, f"Expected 404, got {response.status_code}")
            return False

    def test_delete_measurement(self):
        """Test deleting a measurement"""
        print("Testing delete measurement...")
        
        # Create test user and measurement
        user = self.create_test_user("Delete Measurement Test")
        if not user:
            self.print_test_result("Delete measurement", False, "Failed to create test user")
            return False
        
        measurement = self.create_test_measurement(user["id"])
        if not measurement:
            self.print_test_result("Delete measurement", False, "Failed to create test measurement")
            return False
        
        # Delete measurement
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = self.session.delete(f"{MEASUREMENTS_URL}/{measurement['id']}", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            if result["message"] == "Measurement deleted successfully":
                self.print_test_result("Delete measurement", True, f"Deleted measurement ID: {measurement['id']}")
                # Remove from created_measurements since it's already deleted
                if measurement["id"] in self.created_measurements:
                    self.created_measurements.remove(measurement["id"])
                return True
            else:
                self.print_test_result("Delete measurement", False, "Unexpected response message")
                return False
        else:
            self.print_test_result("Delete measurement", False, f"Status: {response.status_code}, Response: {response.text}")
            return False

    def test_delete_measurement_not_found(self):
        """Test deleting a non-existent measurement"""
        print("Testing delete measurement not found...")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = self.session.delete(f"{MEASUREMENTS_URL}/99999", headers=headers)
        
        if response.status_code == 404:
            self.print_test_result("Delete measurement not found", True, "Correctly returned 404")
            return True
        else:
            self.print_test_result("Delete measurement not found", False, f"Expected 404, got {response.status_code}")
            return False

    def test_unauthorized_access(self):
        """Test unauthorized access to measurements"""
        print("Testing unauthorized access...")
        
        # Test without token
        response = self.session.get(MEASUREMENTS_URL)
        if response.status_code == 401:
            self.print_test_result("Unauthorized access without token", True, "Correctly rejected access")
        else:
            self.print_test_result("Unauthorized access without token", False, f"Expected 401, got {response.status_code}")
            return False
        
        # Test with invalid token
        headers = {"Authorization": "Bearer invalid_token"}
        response = self.session.get(MEASUREMENTS_URL, headers=headers)
        if response.status_code == 401:
            self.print_test_result("Unauthorized access with invalid token", True, "Correctly rejected invalid token")
            return True
        else:
            self.print_test_result("Unauthorized access with invalid token", False, f"Expected 401, got {response.status_code}")
            return False

    def cleanup_test_data(self):
        """Clean up all created test data"""
        print("Cleaning up test data...")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Delete measurements
        for measurement_id in self.created_measurements:
            try:
                response = self.session.delete(f"{MEASUREMENTS_URL}/{measurement_id}", headers=headers)
                if response.status_code == 200:
                    print(f"    Deleted measurement {measurement_id}")
                else:
                    print(f"    Failed to delete measurement {measurement_id}: {response.status_code}")
            except Exception as e:
                print(f"    Error deleting measurement {measurement_id}: {e}")
        
        # Delete users
        for user_id in self.created_users:
            try:
                response = self.session.delete(f"{BASE_URL}/users/{user_id}", headers=headers)
                if response.status_code == 200:
                    print(f"    Deleted user {user_id}")
                else:
                    print(f"    Failed to delete user {user_id}: {response.status_code}")
            except Exception as e:
                print(f"    Error deleting user {user_id}: {e}")
        
        print("Cleanup completed")

    def run_all_tests(self):
        """Run all measurement tests"""
        print("=" * 60)
        print("MEASUREMENTS ENDPOINTS TEST SUITE")
        print("=" * 60)
        print()
        
        # Login first
        if not self.test_login():
            print("Login failed. Cannot proceed with tests.")
            return
        
        # Run all tests
        tests = [
            self.test_create_measurement,
            self.test_create_measurement_trainer,
            self.test_create_measurement_invalid_user,
            self.test_read_measurements,
            self.test_read_measurements_with_filters,
            self.test_read_user_measurements,
            self.test_get_latest_measurement,
            self.test_get_user_progress,
            self.test_read_measurement,
            self.test_read_measurement_not_found,
            self.test_update_measurement,
            self.test_update_measurement_not_found,
            self.test_delete_measurement,
            self.test_delete_measurement_not_found,
            self.test_unauthorized_access
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                print(f"[ERROR] Test {test.__name__} failed with exception: {e}")
                print()
        
        print("=" * 60)
        print(f"TEST RESULTS: {passed}/{total} tests passed")
        print("=" * 60)
        
        # Cleanup
        self.cleanup_test_data()

if __name__ == "__main__":
    tester = MeasurementTester()
    tester.run_all_tests() 