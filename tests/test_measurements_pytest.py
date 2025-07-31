"""
Pytest tests for Measurements endpoints
Tests all CRUD operations and special endpoints for measurements
"""

import pytest
import httpx
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Any

# Test data
@pytest.fixture
def measurement_data() -> Dict[str, Any]:
    """Sample measurement data for testing"""
    return {
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

@pytest.fixture
def measurement_update_data() -> Dict[str, Any]:
    """Sample measurement update data for testing"""
    return {
        "weight": 75.5,
        "notes": "Updated measurement"
    }

class TestMeasurements:
    """Test class for measurements endpoints"""

    def test_create_measurement(self, client: httpx.Client, admin_headers: Dict[str, str], test_user: Dict[str, Any], measurement_data: Dict[str, Any]):
        """Test creating a measurement"""
        measurement_data["user_id"] = test_user["id"]
        
        response = client.post("/measurements/", json=measurement_data, headers=admin_headers)
        
        assert response.status_code == 200
        measurement = response.json()
        assert measurement["user_id"] == test_user["id"]
        assert measurement["height"] == 175.5
        assert measurement["weight"] == 70.2
        assert measurement["recorded_by_id"] is not None

    def test_create_measurement_trainer(self, client: httpx.Client, trainer_headers: Dict[str, str], test_user: Dict[str, Any]):
        """Test creating a measurement as trainer"""
        measurement_data = {
            "user_id": test_user["id"],
            "height": 180.0,
            "weight": 75.0,
            "chest": 100.0,
            "shoulders": 115.0,
            "notes": "Trainer measurement"
        }
        
        response = client.post("/measurements/", json=measurement_data, headers=trainer_headers)
        
        assert response.status_code == 200
        measurement = response.json()
        assert measurement["user_id"] == test_user["id"]
        assert measurement["weight"] == 75.0

    def test_create_measurement_invalid_user(self, client: httpx.Client, admin_headers: Dict[str, str], measurement_data: Dict[str, Any]):
        """Test creating a measurement with invalid user ID"""
        measurement_data["user_id"] = 99999  # Non-existent user
        
        response = client.post("/measurements/", json=measurement_data, headers=admin_headers)
        
        assert response.status_code == 404

    def test_read_measurements(self, client: httpx.Client, admin_headers: Dict[str, str]):
        """Test reading all measurements"""
        response = client.get("/measurements/", headers=admin_headers)
        
        assert response.status_code == 200
        measurements = response.json()
        assert isinstance(measurements, list)

    def test_read_measurements_with_user_filter(self, client: httpx.Client, admin_headers: Dict[str, str], test_user: Dict[str, Any], measurement_data: Dict[str, Any]):
        """Test reading measurements with user filter"""
        # Create measurement first
        measurement_data["user_id"] = test_user["id"]
        create_response = client.post("/measurements/", json=measurement_data, headers=admin_headers)
        assert create_response.status_code == 200
        
        # Test filter by user_id
        response = client.get(f"/measurements/?user_id={test_user['id']}", headers=admin_headers)
        
        assert response.status_code == 200
        measurements = response.json()
        assert isinstance(measurements, list)
        if len(measurements) > 0:
            assert all(m["user_id"] == test_user["id"] for m in measurements)

    def test_read_measurements_with_date_filter(self, client: httpx.Client, admin_headers: Dict[str, str], test_user: Dict[str, Any]):
        """Test reading measurements with date filter"""
        # Create measurements with specific dates
        measurement1_data = {
            "user_id": test_user["id"],
            "weight": 70.0,
            "measurement_date": "2024-01-01T10:00:00Z"
        }
        
        measurement2_data = {
            "user_id": test_user["id"],
            "weight": 72.0,
            "measurement_date": "2024-02-01T10:00:00Z"
        }
        
        # Create measurements
        client.post("/measurements/", json=measurement1_data, headers=admin_headers)
        client.post("/measurements/", json=measurement2_data, headers=admin_headers)
        
        # Test filter by date range
        response = client.get("/measurements/?start_date=2024-01-15&end_date=2024-02-15", headers=admin_headers)
        
        assert response.status_code == 200
        measurements = response.json()
        assert isinstance(measurements, list)

    def test_read_user_measurements(self, client: httpx.Client, admin_headers: Dict[str, str], test_user: Dict[str, Any], measurement_data: Dict[str, Any]):
        """Test reading measurements for a specific user"""
        # Create measurement first
        measurement_data["user_id"] = test_user["id"]
        create_response = client.post("/measurements/", json=measurement_data, headers=admin_headers)
        assert create_response.status_code == 200
        
        # Read user measurements
        response = client.get(f"/measurements/user/{test_user['id']}", headers=admin_headers)
        
        assert response.status_code == 200
        measurements = response.json()
        assert isinstance(measurements, list)
        assert len(measurements) >= 1
        assert all(m["user_id"] == test_user["id"] for m in measurements)

    def test_get_latest_measurement(self, client: httpx.Client, admin_headers: Dict[str, str], test_user: Dict[str, Any]):
        """Test getting the latest measurement for a user"""
        # Create two measurements with different dates
        measurement1_data = {
            "user_id": test_user["id"],
            "weight": 70.0,
            "measurement_date": "2024-01-01T10:00:00Z"
        }
        
        measurement2_data = {
            "user_id": test_user["id"],
            "weight": 72.0,
            "measurement_date": "2024-02-01T10:00:00Z"
        }
        
        # Create measurements
        client.post("/measurements/", json=measurement1_data, headers=admin_headers)
        client.post("/measurements/", json=measurement2_data, headers=admin_headers)
        
        # Get latest measurement
        response = client.get(f"/measurements/user/{test_user['id']}/latest", headers=admin_headers)
        
        assert response.status_code == 200
        latest = response.json()
        assert latest["weight"] == 72.0  # Should be the newer measurement

    def test_get_user_progress(self, client: httpx.Client, admin_headers: Dict[str, str], test_user: Dict[str, Any]):
        """Test getting user progress"""
        # Create measurements with different weights to show progress
        measurement1_data = {
            "user_id": test_user["id"],
            "weight": 80.0,
            "chest": 100.0,
            "measurement_date": "2024-01-01T10:00:00Z"
        }
        
        measurement2_data = {
            "user_id": test_user["id"],
            "weight": 75.0,
            "chest": 95.0,
            "measurement_date": "2024-02-01T10:00:00Z"
        }
        
        # Create measurements
        client.post("/measurements/", json=measurement1_data, headers=admin_headers)
        client.post("/measurements/", json=measurement2_data, headers=admin_headers)
        
        # Get progress
        response = client.get(f"/measurements/user/{test_user['id']}/progress", headers=admin_headers)
        
        assert response.status_code == 200
        progress = response.json()
        assert "progress" in progress
        assert "weight" in progress["progress"]
        
        weight_progress = progress["progress"]["weight"]
        assert weight_progress["change"] == -5.0  # 75.0 - 80.0

    def test_get_user_progress_insufficient_data(self, client: httpx.Client, admin_headers: Dict[str, str], test_user: Dict[str, Any]):
        """Test getting user progress with insufficient data"""
        response = client.get(f"/measurements/user/{test_user['id']}/progress", headers=admin_headers)
        
        assert response.status_code == 200
        progress = response.json()
        assert "message" in progress
        assert "Need at least 2 measurements to calculate progress" in progress["message"]

    def test_read_measurement(self, client: httpx.Client, admin_headers: Dict[str, str], test_user: Dict[str, Any], measurement_data: Dict[str, Any]):
        """Test reading a specific measurement"""
        # Create measurement first
        measurement_data["user_id"] = test_user["id"]
        create_response = client.post("/measurements/", json=measurement_data, headers=admin_headers)
        assert create_response.status_code == 200
        created_measurement = create_response.json()
        
        # Read specific measurement
        response = client.get(f"/measurements/{created_measurement['id']}", headers=admin_headers)
        
        assert response.status_code == 200
        measurement = response.json()
        assert measurement["id"] == created_measurement["id"]
        assert measurement["user_id"] == test_user["id"]

    def test_read_measurement_not_found(self, client: httpx.Client, admin_headers: Dict[str, str]):
        """Test reading a non-existent measurement"""
        response = client.get("/measurements/99999", headers=admin_headers)
        
        assert response.status_code == 404

    def test_update_measurement(self, client: httpx.Client, admin_headers: Dict[str, str], test_user: Dict[str, Any], measurement_data: Dict[str, Any], measurement_update_data: Dict[str, Any]):
        """Test updating a measurement"""
        # Create measurement first
        measurement_data["user_id"] = test_user["id"]
        create_response = client.post("/measurements/", json=measurement_data, headers=admin_headers)
        assert create_response.status_code == 200
        created_measurement = create_response.json()
        
        # Update measurement
        response = client.put(f"/measurements/{created_measurement['id']}", json=measurement_update_data, headers=admin_headers)
        
        assert response.status_code == 200
        updated_measurement = response.json()
        assert updated_measurement["weight"] == 75.5
        assert updated_measurement["notes"] == "Updated measurement"

    def test_update_measurement_not_found(self, client: httpx.Client, admin_headers: Dict[str, str], measurement_update_data: Dict[str, Any]):
        """Test updating a non-existent measurement"""
        response = client.put("/measurements/99999", json=measurement_update_data, headers=admin_headers)
        
        assert response.status_code == 404

    def test_delete_measurement(self, client: httpx.Client, admin_headers: Dict[str, str], test_user: Dict[str, Any], measurement_data: Dict[str, Any]):
        """Test deleting a measurement"""
        # Create measurement first
        measurement_data["user_id"] = test_user["id"]
        create_response = client.post("/measurements/", json=measurement_data, headers=admin_headers)
        assert create_response.status_code == 200
        created_measurement = create_response.json()
        
        # Delete measurement
        response = client.delete(f"/measurements/{created_measurement['id']}", headers=admin_headers)
        
        assert response.status_code == 200
        result = response.json()
        assert result["message"] == "Measurement deleted successfully"
        
        # Verify it's deleted
        get_response = client.get(f"/measurements/{created_measurement['id']}", headers=admin_headers)
        assert get_response.status_code == 404

    def test_delete_measurement_not_found(self, client: httpx.Client, admin_headers: Dict[str, str]):
        """Test deleting a non-existent measurement"""
        response = client.delete("/measurements/99999", headers=admin_headers)
        
        assert response.status_code == 404

    def test_unauthorized_access(self, client: httpx.Client):
        """Test unauthorized access to measurements"""
        # Test without token
        response = client.get("/measurements/")
        assert response.status_code == 401
        
        # Test with invalid token
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/measurements/", headers=headers)
        assert response.status_code == 401

    def test_trainer_access_measurements(self, client: httpx.Client, trainer_headers: Dict[str, str]):
        """Test that trainers can access measurements"""
        response = client.get("/measurements/", headers=trainer_headers)
        
        assert response.status_code == 200
        measurements = response.json()
        assert isinstance(measurements, list)

    def test_measurement_with_all_fields(self, client: httpx.Client, admin_headers: Dict[str, str], test_user: Dict[str, Any]):
        """Test creating a measurement with all possible fields"""
        complete_measurement_data = {
            "user_id": test_user["id"],
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
            "notes": "Complete measurement test",
            "measurement_date": "2024-01-15T10:00:00Z"
        }
        
        response = client.post("/measurements/", json=complete_measurement_data, headers=admin_headers)
        
        assert response.status_code == 200
        measurement = response.json()
        assert measurement["height"] == 175.5
        assert measurement["weight"] == 70.2
        assert measurement["chest"] == 95.0
        assert measurement["shoulders"] == 110.0
        assert measurement["biceps_left"] == 32.5
        assert measurement["biceps_right"] == 32.8
        assert measurement["forearms_left"] == 28.0
        assert measurement["forearms_right"] == 28.2
        assert measurement["abdomen"] == 85.0
        assert measurement["hips"] == 95.0
        assert measurement["thighs_left"] == 55.0
        assert measurement["thighs_right"] == 55.2
        assert measurement["calves_left"] == 35.0
        assert measurement["calves_right"] == 35.1
        assert measurement["notes"] == "Complete measurement test"

    def test_measurement_with_minimal_fields(self, client: httpx.Client, admin_headers: Dict[str, str], test_user: Dict[str, Any]):
        """Test creating a measurement with minimal fields"""
        minimal_measurement_data = {
            "user_id": test_user["id"],
            "weight": 70.0
        }
        
        response = client.post("/measurements/", json=minimal_measurement_data, headers=admin_headers)
        
        assert response.status_code == 200
        measurement = response.json()
        assert measurement["user_id"] == test_user["id"]
        assert measurement["weight"] == 70.0
        assert measurement["recorded_by_id"] is not None

    def test_measurement_pagination(self, client: httpx.Client, admin_headers: Dict[str, str], test_user: Dict[str, Any]):
        """Test measurement pagination"""
        # Create multiple measurements
        for i in range(5):
            measurement_data = {
                "user_id": test_user["id"],
                "weight": 70.0 + i,
                "notes": f"Measurement {i+1}"
            }
            client.post("/measurements/", json=measurement_data, headers=admin_headers)
        
        # Test pagination
        response = client.get("/measurements/?skip=0&limit=3", headers=admin_headers)
        assert response.status_code == 200
        measurements = response.json()
        assert len(measurements) <= 3
        
        # Test second page
        response = client.get("/measurements/?skip=3&limit=3", headers=admin_headers)
        assert response.status_code == 200
        measurements = response.json()
        assert len(measurements) <= 3

    def test_user_measurements_pagination(self, client: httpx.Client, admin_headers: Dict[str, str], test_user: Dict[str, Any]):
        """Test user measurements pagination"""
        # Create multiple measurements for the user
        for i in range(5):
            measurement_data = {
                "user_id": test_user["id"],
                "weight": 70.0 + i,
                "notes": f"User measurement {i+1}"
            }
            client.post("/measurements/", json=measurement_data, headers=admin_headers)
        
        # Test pagination
        response = client.get(f"/measurements/user/{test_user['id']}?skip=0&limit=3", headers=admin_headers)
        assert response.status_code == 200
        measurements = response.json()
        assert len(measurements) <= 3
        assert all(m["user_id"] == test_user["id"] for m in measurements)
        
        # Test second page
        response = client.get(f"/measurements/user/{test_user['id']}?skip=3&limit=3", headers=admin_headers)
        assert response.status_code == 200
        measurements = response.json()
        assert len(measurements) <= 3
        assert all(m["user_id"] == test_user["id"] for m in measurements) 