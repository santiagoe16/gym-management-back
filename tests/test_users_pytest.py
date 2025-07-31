import pytest
from fastapi import status
from sqlmodel import Session, select
from app.models.user import User, UserRole, UserCreateWithPassword, UserCreateWithPlan
from app.models.plan import Plan
from app.models.user_plan import UserPlan
from datetime import datetime, timezone, timedelta

class TestUserEndpoints:
    """Test suite for user endpoints"""

    def test_read_users_admin_access(self, client, admin_token, admin_user, trainer_user, regular_user):
        """Test getting all users with admin access"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/users/", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        users = response.json()
        assert len(users) == 3  # admin, trainer, regular user
        
        # Check that all users are returned
        user_emails = [user["email"] for user in users]
        assert admin_user.email in user_emails
        assert trainer_user.email in user_emails
        assert regular_user.email in user_emails

    def test_read_users_trainer_access(self, client, trainer_token, admin_user, trainer_user, regular_user):
        """Test getting users with trainer access (should only see regular users)"""
        headers = {"Authorization": f"Bearer {trainer_token}"}
        response = client.get("/api/v1/users/", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        users = response.json()
        
        # Trainer should only see regular users (role == "user")
        for user in users:
            assert user["role"] == "user"

    def test_read_users_unauthorized(self, client):
        """Test getting users without authentication"""
        response = client.get("/api/v1/users/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_admin_user(self, client, admin_token, test_gym):
        """Test creating an admin user"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        user_data = {
            "email": "newadmin@test.com",
            "full_name": "New Admin",
            "document_id": "NEWADMIN123",
            "phone_number": "1111111111",
            "gym_id": test_gym.id,
            "role": "admin",
            "password": "newadminpass123"
        }
        
        response = client.post("/api/v1/users/admin-trainer", json=user_data, headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        user = response.json()
        assert user["email"] == user_data["email"]
        assert user["role"] == "admin"
        assert user["gym_id"] == test_gym.id

    def test_create_trainer_user(self, client, admin_token, test_gym):
        """Test creating a trainer user"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        user_data = {
            "email": "newtrainer@test.com",
            "full_name": "New Trainer",
            "document_id": "NEWTRAINER123",
            "phone_number": "2222222222",
            "gym_id": test_gym.id,
            "role": "trainer",
            "password": "newtrainerpass123",
            "schedule_start": "09:00:00",
            "schedule_end": "17:00:00"
        }
        
        response = client.post("/api/v1/users/admin-trainer", json=user_data, headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        user = response.json()
        assert user["email"] == user_data["email"]
        assert user["role"] == "trainer"
        assert user["schedule_start"] == "09:00:00"
        assert user["schedule_end"] == "17:00:00"

    def test_create_regular_user_with_plan(self, client, admin_token, test_gym, test_plan):
        """Test creating a regular user with a plan"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        user_data = {
            "email": "newuser@test.com",
            "full_name": "New User",
            "document_id": "NEWUSER123",
            "phone_number": "3333333333",
            "role": "user",
            "plan_id": test_plan.id
        }
        
        response = client.post("/api/v1/users/with-plan", json=user_data, headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        user = response.json()
        assert user["email"] == user_data["email"]
        assert user["role"] == "user"
        assert user["gym_id"] == test_gym.id  # Should be automatically assigned

    def test_create_user_with_duplicate_email(self, client, admin_token, test_gym, admin_user):
        """Test creating a user with duplicate email"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        user_data = {
            "email": admin_user.email,  # Duplicate email
            "full_name": "Duplicate User",
            "document_id": "DUPLICATE123",
            "phone_number": "4444444444",
            "role": "admin",
            "password": "duplicatepass123"
        }
        
        response = client.post("/api/v1/users/admin-trainer", json=user_data, headers=headers)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already registered" in response.json()["detail"]

    def test_create_user_with_duplicate_document_id(self, client, admin_token, test_gym, admin_user):
        """Test creating a user with duplicate document ID"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        user_data = {
            "email": "unique@test.com",
            "full_name": "Duplicate User",
            "document_id": admin_user.document_id,  # Duplicate document ID
            "phone_number": "5555555555",
            "role": "admin",
            "password": "duplicatepass123"
        }
        
        response = client.post("/api/v1/users/admin-trainer", json=user_data, headers=headers)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already registered" in response.json()["detail"]

    def test_create_regular_user_with_invalid_plan(self, client, admin_token, test_gym):
        """Test creating a regular user with non-existent plan"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        user_data = {
            "email": "newuser@test.com",
            "full_name": "New User",
            "document_id": "NEWUSER123",
            "phone_number": "3333333333",
            "role": "user",
            "plan_id": 999  # Non-existent plan
        }
        
        response = client.post("/api/v1/users/with-plan", json=user_data, headers=headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Plan not found" in response.json()["detail"]

    def test_search_user_by_document_id(self, client, admin_token, regular_user):
        """Test searching for a user by document ID"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(f"/api/v1/users/search/document/{regular_user.document_id}", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        user = response.json()
        assert user["document_id"] == regular_user.document_id
        assert user["email"] == regular_user.email

    def test_search_user_by_document_id_not_found(self, client, admin_token):
        """Test searching for a user with non-existent document ID"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/users/search/document/NONEXISTENT", headers=headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "User not found" in response.json()["detail"]

    def test_search_users_by_phone(self, client, admin_token, regular_user):
        """Test searching for users by phone number"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        # Search with partial phone number
        partial_phone = regular_user.phone_number[:5]
        response = client.get(f"/api/v1/users/search/phone/{partial_phone}", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        users = response.json()
        assert len(users) > 0
        assert any(user["phone_number"] == regular_user.phone_number for user in users)

    def test_search_users_by_phone_not_found(self, client, admin_token):
        """Test searching for users with non-existent phone number"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/users/search/phone/9999999999", headers=headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "No users found" in response.json()["detail"]

    def test_trainer_search_only_regular_users(self, client, trainer_token, admin_user, trainer_user, regular_user):
        """Test that trainers can only search for regular users"""
        headers = {"Authorization": f"Bearer {trainer_token}"}
        
        # Search for admin user (should fail)
        response = client.get(f"/api/v1/users/search/document/{admin_user.document_id}", headers=headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Trainers can only view regular users" in response.json()["detail"]
        
        # Search for trainer user (should fail)
        response = client.get(f"/api/v1/users/search/document/{trainer_user.document_id}", headers=headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Trainers can only view regular users" in response.json()["detail"]
        
        # Search for regular user (should succeed)
        response = client.get(f"/api/v1/users/search/document/{regular_user.document_id}", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        user = response.json()
        assert user["role"] == "user"

    def test_read_specific_user(self, client, admin_token, regular_user):
        """Test getting a specific user by ID"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(f"/api/v1/users/{regular_user.id}", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        user = response.json()
        assert user["id"] == regular_user.id
        assert user["email"] == regular_user.email

    def test_read_specific_user_not_found(self, client, admin_token):
        """Test getting a non-existent user"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/users/999", headers=headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "User not found" in response.json()["detail"]

    def test_trainer_read_specific_user_restrictions(self, client, trainer_token, admin_user, trainer_user, regular_user):
        """Test that trainers can only read specific regular users"""
        headers = {"Authorization": f"Bearer {trainer_token}"}
        
        # Try to read admin user (should fail)
        response = client.get(f"/api/v1/users/{admin_user.id}", headers=headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Trainers can only view regular users" in response.json()["detail"]
        
        # Try to read trainer user (should fail)
        response = client.get(f"/api/v1/users/{trainer_user.id}", headers=headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Trainers can only view regular users" in response.json()["detail"]
        
        # Try to read regular user (should succeed)
        response = client.get(f"/api/v1/users/{regular_user.id}", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        user = response.json()
        assert user["role"] == "user"

    def test_update_user(self, client, admin_token, regular_user):
        """Test updating a user"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        update_data = {
            "full_name": "Updated Name",
            "phone_number": "9876543210"
        }
        
        response = client.put(f"/api/v1/users/{regular_user.id}", json=update_data, headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        user = response.json()
        assert user["full_name"] == "Updated Name"
        assert user["phone_number"] == "9876543210"

    def test_update_user_not_found(self, client, admin_token):
        """Test updating a non-existent user"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        update_data = {"full_name": "Non-existent User"}
        
        response = client.put("/api/v1/users/999", json=update_data, headers=headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "User not found" in response.json()["detail"]

    def test_update_user_with_duplicate_email(self, client, admin_token, admin_user, regular_user):
        """Test updating user with duplicate email"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        update_data = {"email": admin_user.email}  # Duplicate email
        
        response = client.put(f"/api/v1/users/{regular_user.id}", json=update_data, headers=headers)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already registered" in response.json()["detail"]

    def test_trainer_update_admin_user_forbidden(self, client, trainer_token, admin_user):
        """Test that trainers cannot update admin users"""
        headers = {"Authorization": f"Bearer {trainer_token}"}
        update_data = {"full_name": "Updated Name"}
        
        response = client.put(f"/api/v1/users/{admin_user.id}", json=update_data, headers=headers)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Trainers can only view regular users" in response.json()["detail"]

    def test_trainer_update_user_role_forbidden(self, client, trainer_token, regular_user):
        """Test that trainers cannot change user roles"""
        headers = {"Authorization": f"Bearer {trainer_token}"}
        update_data = {"role": "admin"}
        
        response = client.put(f"/api/v1/users/{regular_user.id}", json=update_data, headers=headers)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Trainers cannot change user roles" in response.json()["detail"]

    def test_update_user_with_new_plan(self, client, admin_token, regular_user, test_plan):
        """Test updating user with a new plan assignment"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        update_data = {"plan_id": test_plan.id}
        
        response = client.put(f"/api/v1/users/{regular_user.id}", json=update_data, headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        user = response.json()
        assert user["active_plan"] is not None
        assert user["active_plan"]["plan_id"] == test_plan.id

    def test_update_user_with_invalid_plan(self, client, admin_token, regular_user):
        """Test updating user with non-existent plan"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        update_data = {"plan_id": 99999}  # Non-existent plan
        
        response = client.put(f"/api/v1/users/{regular_user.id}", json=update_data, headers=headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Plan not found" in response.json()["detail"]

    def test_update_user_with_inactive_plan(self, client, admin_token, regular_user, test_gym):
        """Test updating user with inactive plan"""
        # Create an inactive plan
        inactive_plan_data = {
            "name": "Inactive Plan",
            "description": "Test inactive plan",
            "price": 50.0,
            "duration_days": 30,
            "gym_id": test_gym.id,
            "is_active": False
        }
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        plan_response = client.post("/api/v1/plans/", json=inactive_plan_data, headers=headers)
        inactive_plan = plan_response.json()
        
        # Try to assign inactive plan to user
        update_data = {"plan_id": inactive_plan["id"]}
        response = client.put(f"/api/v1/users/{regular_user.id}", json=update_data, headers=headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "inactive" in response.json()["detail"]

    def test_update_user_with_plan_from_different_gym(self, client, admin_token, regular_user, test_gym):
        """Test updating user with plan from different gym"""
        # Create a plan for a different gym
        different_gym_plan_data = {
            "name": "Different Gym Plan",
            "description": "Plan from different gym",
            "price": 60.0,
            "duration_days": 30,
            "gym_id": test_gym.id + 1,  # Different gym ID
            "is_active": True
        }
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        plan_response = client.post("/api/v1/plans/", json=different_gym_plan_data, headers=headers)
        different_gym_plan = plan_response.json()
        
        # Try to assign plan from different gym to user
        update_data = {"plan_id": different_gym_plan["id"]}
        response = client.put(f"/api/v1/users/{regular_user.id}", json=update_data, headers=headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not available in this gym" in response.json()["detail"]

    def test_update_user_plan_creates_user_plan_record(self, client, admin_token, regular_user, test_plan):
        """Test that updating user with plan creates a UserPlan record"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        update_data = {"plan_id": test_plan.id}
        
        response = client.put(f"/api/v1/users/{regular_user.id}", json=update_data, headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        user = response.json()
        
        # Check that active_plan is properly set
        assert user["active_plan"] is not None
        assert user["active_plan"]["plan_id"] == test_plan.id
        assert user["active_plan"]["purchased_price"] == test_plan.price
        assert user["active_plan"]["expires_at"] is not None
        assert user["active_plan"]["created_by_id"] is not None

    def test_update_user_plan_modification_comprehensive(self, client, admin_token, regular_user, test_gym):
        """Test comprehensive plan modification scenarios"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create multiple plans for testing
        plan1_data = {
            "name": "Basic Plan",
            "description": "Basic monthly plan",
            "price": 50.0,
            "duration_days": 30,
            "gym_id": test_gym.id,
            "is_active": True
        }
        
        plan2_data = {
            "name": "Premium Plan", 
            "description": "Premium monthly plan",
            "price": 100.0,
            "duration_days": 30,
            "gym_id": test_gym.id,
            "is_active": True
        }
        
        plan3_data = {
            "name": "Annual Plan",
            "description": "Annual plan",
            "price": 500.0,
            "duration_days": 365,
            "gym_id": test_gym.id,
            "is_active": True
        }
        
        # Create plans
        plan1_response = client.post("/api/v1/plans/", json=plan1_data, headers=headers)
        plan2_response = client.post("/api/v1/plans/", json=plan2_data, headers=headers)
        plan3_response = client.post("/api/v1/plans/", json=plan3_data, headers=headers)
        
        assert plan1_response.status_code == status.HTTP_200_OK
        assert plan2_response.status_code == status.HTTP_200_OK
        assert plan3_response.status_code == status.HTTP_200_OK
        
        plan1 = plan1_response.json()
        plan2 = plan2_response.json()
        plan3 = plan3_response.json()
        
        # Test 1: Assign first plan
        response = client.put(f"/api/v1/users/{regular_user.id}", 
                             json={"plan_id": plan1["id"]}, headers=headers)
        assert response.status_code == status.HTTP_200_OK
        user = response.json()
        assert user["active_plan"]["plan_id"] == plan1["id"]
        assert user["active_plan"]["purchased_price"] == plan1["price"]
        
        # Test 2: Upgrade to premium plan
        response = client.put(f"/api/v1/users/{regular_user.id}", 
                             json={"plan_id": plan2["id"]}, headers=headers)
        assert response.status_code == status.HTTP_200_OK
        user = response.json()
        assert user["active_plan"]["plan_id"] == plan2["id"]
        assert user["active_plan"]["purchased_price"] == plan2["price"]
        
        # Test 3: Upgrade to annual plan
        response = client.put(f"/api/v1/users/{regular_user.id}", 
                             json={"plan_id": plan3["id"]}, headers=headers)
        assert response.status_code == status.HTTP_200_OK
        user = response.json()
        assert user["active_plan"]["plan_id"] == plan3["id"]
        assert user["active_plan"]["purchased_price"] == plan3["price"]
        
        # Test 4: Downgrade back to basic plan
        response = client.put(f"/api/v1/users/{regular_user.id}", 
                             json={"plan_id": plan1["id"]}, headers=headers)
        assert response.status_code == status.HTTP_200_OK
        user = response.json()
        assert user["active_plan"]["plan_id"] == plan1["id"]
        assert user["active_plan"]["purchased_price"] == plan1["price"]

    def test_update_user_plan_with_basic_info(self, client, admin_token, regular_user, test_plan):
        """Test updating user plan along with basic information"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        update_data = {
            "plan_id": test_plan.id,
            "full_name": "Updated User Name",
            "phone_number": "9876543210"
        }
        
        response = client.put(f"/api/v1/users/{regular_user.id}", json=update_data, headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        user = response.json()
        
        # Check plan was updated
        assert user["active_plan"]["plan_id"] == test_plan.id
        
        # Check basic info was updated
        assert user["full_name"] == "Updated User Name"
        assert user["phone_number"] == "9876543210"

    def test_trainer_update_user_plan_success(self, client, trainer_token, regular_user, test_plan):
        """Test that trainers can update regular user plans"""
        headers = {"Authorization": f"Bearer {trainer_token}"}
        update_data = {"plan_id": test_plan.id}
        
        response = client.put(f"/api/v1/users/{regular_user.id}", json=update_data, headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        user = response.json()
        assert user["active_plan"]["plan_id"] == test_plan.id

    def test_trainer_update_admin_plan_forbidden(self, client, trainer_token, admin_user, test_plan):
        """Test that trainers cannot update admin user plans"""
        headers = {"Authorization": f"Bearer {trainer_token}"}
        update_data = {"plan_id": test_plan.id}
        
        response = client.put(f"/api/v1/users/{admin_user.id}", json=update_data, headers=headers)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Trainers can only view regular users" in response.json()["detail"]

    def test_update_user_plan_expiration_calculation(self, client, admin_token, regular_user, test_gym):
        """Test that plan expiration is calculated correctly"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a plan with specific duration
        plan_data = {
            "name": "Test Duration Plan",
            "description": "Plan to test duration calculation",
            "price": 75.0,
            "duration_days": 60,  # 60 days
            "gym_id": test_gym.id,
            "is_active": True
        }
        
        plan_response = client.post("/api/v1/plans/", json=plan_data, headers=headers)
        assert plan_response.status_code == status.HTTP_200_OK
        plan = plan_response.json()
        
        # Assign plan to user
        response = client.put(f"/api/v1/users/{regular_user.id}", 
                             json={"plan_id": plan["id"]}, headers=headers)
        assert response.status_code == status.HTTP_200_OK
        user = response.json()
        
        # Check expiration date
        from datetime import datetime, timezone, timedelta
        expires_at = user["active_plan"]["expires_at"]
        expires_date = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        
        # Expiration should be approximately 60 days from now
        expected_expiry = now + timedelta(days=60)
        time_diff = abs((expires_date - expected_expiry).total_seconds())
        
        # Allow 5 minutes tolerance for test execution time
        assert time_diff < 300  # 5 minutes in seconds

    def test_plan_modification_active_plan_detection(self, client, admin_token, test_gym, test_plan):
        """Test that newly added plans are correctly detected as active plans"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a user with initial plan
        user_data = {
            "email": "activeplanuser@test.com",
            "full_name": "Active Plan Test User",
            "document_id": "ACTIVEPLAN123",
            "phone_number": "8888888888",
            "role": "user",
            "plan_id": test_plan.id
        }
        
        # Create user with initial plan
        create_response = client.post("/api/v1/users/with-plan", json=user_data, headers=headers)
        assert create_response.status_code == status.HTTP_200_OK
        created_user = create_response.json()
        
        # Verify initial plan is active
        initial_active_plan = created_user.get("active_plan")
        assert initial_active_plan is not None
        assert initial_active_plan["plan_id"] == test_plan.id
        
        # Create a second plan
        plan2_data = {
            "name": "Second Plan",
            "description": "Second plan for active plan testing",
            "price": 75.0,
            "duration_days": 60,
            "gym_id": test_gym.id,
            "is_active": True
        }
        
        plan2_response = client.post("/api/v1/plans/", json=plan2_data, headers=headers)
        assert plan2_response.status_code == status.HTTP_200_OK
        plan2 = plan2_response.json()
        
        # Update user with new plan
        update_data = {"plan_id": plan2["id"]}
        update_response = client.put(f"/api/v1/users/{created_user['id']}", json=update_data, headers=headers)
        assert update_response.status_code == status.HTTP_200_OK
        
        updated_user = update_response.json()
        new_active_plan = updated_user.get("active_plan")
        
        # Verify new plan is correctly detected as active
        assert new_active_plan is not None
        assert new_active_plan["plan_id"] == plan2["id"]
        assert new_active_plan["plan_id"] != test_plan.id  # Should be different from initial plan

    def test_delete_user(self, client, admin_token, regular_user):
        """Test deleting a user"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.delete(f"/api/v1/users/{regular_user.id}", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        assert "User deleted successfully" in response.json()["message"]

    def test_delete_user_not_found(self, client, admin_token):
        """Test deleting a non-existent user"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.delete("/api/v1/users/999", headers=headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "User not found" in response.json()["detail"]

    def test_delete_user_trainer_forbidden(self, client, trainer_token, regular_user):
        """Test that trainers cannot delete users"""
        headers = {"Authorization": f"Bearer {trainer_token}"}
        response = client.delete(f"/api/v1/users/{regular_user.id}", headers=headers)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Admin access required" in response.json()["detail"]

    def test_read_trainers(self, client, admin_token, admin_user, trainer_user):
        """Test getting all trainers"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/users/trainers/", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        trainers = response.json()
        assert len(trainers) == 1
        assert trainers[0]["role"] == "trainer"
        assert trainers[0]["email"] == trainer_user.email

    def test_read_regular_users(self, client, admin_token, admin_user, trainer_user, regular_user):
        """Test getting all regular users"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/users/users/", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        users = response.json()
        assert len(users) == 1
        assert users[0]["role"] == "user"
        assert users[0]["email"] == regular_user.email

    def test_filter_users_by_gym(self, client, admin_token, test_gym, regular_user):
        """Test filtering users by gym ID"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(f"/api/v1/users/?gym_id={test_gym.id}", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        users = response.json()
        for user in users:
            assert user["gym_id"] == test_gym.id

    def test_pagination(self, client, admin_token):
        """Test pagination for users list"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/users/?skip=0&limit=2", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        users = response.json()
        assert len(users) <= 2

    def test_create_regular_user_admin_forbidden(self, client, admin_token, test_gym, test_plan):
        """Test that admin endpoint doesn't allow creating regular users"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        user_data = {
            "email": "newuser@test.com",
            "full_name": "New User",
            "document_id": "NEWUSER123",
            "phone_number": "3333333333",
            "gym_id": test_gym.id,
            "role": "user",  # Regular user
            "password": "newuserpass123"
        }
        
        response = client.post("/api/v1/users/admin-trainer", json=user_data, headers=headers)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Use /with-plan endpoint" in response.json()["detail"]

    def test_create_admin_with_plan_forbidden(self, client, admin_token, test_gym, test_plan):
        """Test that plan endpoint doesn't allow creating admin users"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        user_data = {
            "email": "newadmin@test.com",
            "full_name": "New Admin",
            "document_id": "NEWADMIN123",
            "phone_number": "1111111111",
            "role": "admin",  # Admin user
            "plan_id": test_plan.id
        }
        
        response = client.post("/api/v1/users/with-plan", json=user_data, headers=headers)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Only regular users can be created with plans" in response.json()["detail"]

    def test_trainer_create_user_success(self, client, trainer_token, test_plan):
        """Test that trainers can create regular users (automatically assigned to their gym)"""
        headers = {"Authorization": f"Bearer {trainer_token}"}
        user_data = {
            "email": "trainercreated@test.com",
            "full_name": "Trainer Created User",
            "document_id": "TRAINER123",
            "phone_number": "3333333333",
            "role": "user",
            "plan_id": test_plan.id
        }
        
        response = client.post("/api/v1/users/with-plan", json=user_data, headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        user = response.json()
        assert user["email"] == user_data["email"]
        assert user["role"] == "user"
        # User should be automatically assigned to trainer's gym
        assert user["gym_id"] is not None 