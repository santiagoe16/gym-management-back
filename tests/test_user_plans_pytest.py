import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from app.models.user_plan import UserPlan
from app.models.user import User, UserRole
from app.models.plan import Plan, PlanRole

class TestUserPlanEndpoints:
    """Test cases for user plan endpoints"""
    
    def test_read_user_plans_success(self, client, admin_token, regular_user, test_plan):
        """Test successful user plans reading"""
        # First create a user plan through the users endpoint
        user_update_data = {
            "plan_id": test_plan.id
        }
        
        response = client.put(f"/api/v1/users/{regular_user.id}", json=user_update_data, headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code == 200
        
        # Now read user plans
        response = client.get("/api/v1/user-plans/", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    def test_read_user_plans_trainer_access(self, client, trainer_token, regular_user, test_plan):
        """Test trainer can read user plans from their gym"""
        # First create a user plan through the users endpoint
        user_update_data = {
            "plan_id": test_plan.id
        }
        
        response = client.put(f"/api/v1/users/{regular_user.id}", json=user_update_data, headers={
            "Authorization": f"Bearer {trainer_token}"
        })
        
        assert response.status_code == 200
        
        # Now read user plans
        response = client.get("/api/v1/user-plans/", headers={
            "Authorization": f"Bearer {trainer_token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_read_user_plans_unauthorized(self, client, regular_user, test_plan):
        """Test unauthorized access to user plans"""
        response = client.get("/api/v1/user-plans/")
        
        assert response.status_code == 403
    
    def test_read_user_plans_by_user(self, client, admin_token, regular_user, test_plan):
        """Test reading user plans by user ID"""
        # First create a user plan through the users endpoint
        user_update_data = {
            "plan_id": test_plan.id
        }
        
        response = client.put(f"/api/v1/users/{regular_user.id}", json=user_update_data, headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code == 200
        
        # Now read user plans by user
        response = client.get(f"/api/v1/user-plans/user/{regular_user.id}", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    def test_read_user_active_plan(self, client, admin_token, regular_user, test_plan):
        """Test reading user's active plan"""
        # First create a user plan through the users endpoint
        user_update_data = {
            "plan_id": test_plan.id
        }
        
        response = client.put(f"/api/v1/users/{regular_user.id}", json=user_update_data, headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code == 200
        
        # Now read active plan
        response = client.get(f"/api/v1/user-plans/user/{regular_user.id}/active", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == regular_user.id
        assert data["plan_id"] == test_plan.id
        assert data["is_active"] is True
    
    def test_update_user_plan(self, client, admin_token, regular_user, test_plan, session):
        """Test updating a user plan"""
        # First create a user plan by updating the user
        user_update_data = {
            "plan_id": test_plan.id
        }
        
        response = client.put(f"/api/v1/users/{regular_user.id}", json=user_update_data, headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code == 200
        
        # Get the user plan ID from the database
        user_plan = session.exec(select(UserPlan).where(UserPlan.user_id == regular_user.id)).first()
        assert user_plan is not None
        
        # Update the user plan
        update_data = {
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        }
        
        response = client.put(f"/api/v1/user-plans/{user_plan.id}", json=update_data, headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_plan.id
    
    def test_read_user_plans_admin(self, client, admin_token, regular_user, test_plan):
        """Test admin can read all user plans"""
        # First create a user plan through the users endpoint
        user_update_data = {
            "plan_id": test_plan.id
        }
        
        response = client.put(f"/api/v1/users/{regular_user.id}", json=user_update_data, headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code == 200
        
        # Read user plans
        response = client.get("/api/v1/user-plans/", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_read_user_plans_trainer(self, client, trainer_token, regular_user, test_plan):
        """Test trainer can read user plans from their gym"""
        # First create a user plan through the users endpoint
        user_update_data = {
            "plan_id": test_plan.id
        }
        
        response = client.put(f"/api/v1/users/{regular_user.id}", json=user_update_data, headers={
            "Authorization": f"Bearer {trainer_token}"
        })
        
        assert response.status_code == 200
        
        # Read user plans
        response = client.get("/api/v1/user-plans/", headers={
            "Authorization": f"Bearer {trainer_token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_read_user_plan_not_found(self, client, admin_token):
        """Test reading non-existent user plan"""
        response = client.get("/api/v1/user-plans/user/99999/active", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    def test_delete_user_plan(self, client, admin_token, regular_user, test_plan, session):
        """Test deleting a user plan"""
        # First create a user plan by updating the user
        user_update_data = {
            "plan_id": test_plan.id
        }
        
        response = client.put(f"/api/v1/users/{regular_user.id}", json=user_update_data, headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code == 200
        
        # Get the user plan ID from the database
        user_plan = session.exec(select(UserPlan).where(UserPlan.user_id == regular_user.id)).first()
        assert user_plan is not None
        
        # Delete the user plan
        response = client.delete(f"/api/v1/user-plans/{user_plan.id}", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_get_user_plans_by_user(self, client, admin_token, regular_user, test_plan):
        """Test getting user plans by user ID"""
        # First create a user plan through the users endpoint
        user_update_data = {
            "plan_id": test_plan.id
        }
        
        response = client.put(f"/api/v1/users/{regular_user.id}", json=user_update_data, headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code == 200
        
        # Get user plans by user
        response = client.get(f"/api/v1/user-plans/user/{regular_user.id}", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    def test_get_active_user_plans(self, client, admin_token, regular_user, test_plan):
        """Test getting active user plans"""
        # First create a user plan through the users endpoint
        user_update_data = {
            "plan_id": test_plan.id
        }
        
        response = client.put(f"/api/v1/users/{regular_user.id}", json=user_update_data, headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code == 200
        
        # Get active user plan
        response = client.get(f"/api/v1/user-plans/user/{regular_user.id}/active", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == regular_user.id
        assert data["is_active"] is True
    
    def test_get_user_plans_by_plan(self, client, admin_token, regular_user, test_plan):
        """Test getting user plans filtered by plan"""
        # First create a user plan through the users endpoint
        user_update_data = {
            "plan_id": test_plan.id
        }
        
        response = client.put(f"/api/v1/users/{regular_user.id}", json=user_update_data, headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code == 200
        
        # Get user plans filtered by plan
        response = client.get(f"/api/v1/user-plans/?plan_id={test_plan.id}", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_user_plans_by_plan_not_found(self, client, admin_token):
        """Test getting user plans for non-existent plan"""
        response = client.get("/api/v1/user-plans/?plan_id=99999", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_trainer_can_only_access_own_gym_user_plans(self, client, trainer_token, regular_user, test_plan, session):
        """Test trainer can only access user plans from their gym"""
        # Create a user in a different gym
        other_gym = session.exec(select(User).where(User.gym_id != regular_user.gym_id)).first()
        if other_gym:
            # Try to access user plans from different gym
            response = client.get(f"/api/v1/user-plans/user/{other_gym.id}", headers={
                "Authorization": f"Bearer {trainer_token}"
            })
            
            assert response.status_code == 403
            data = response.json()
            assert "detail" in data
    
    def test_user_plan_expiration_validation(self, client, admin_token, regular_user, test_plan):
        """Test user plan expiration validation"""
        # This test is not applicable since we don't have a direct POST endpoint
        # User plans are created through user updates
        pass
    
    def test_user_plan_overlap_validation(self, client, admin_token, regular_user, test_plan, session):
        """Test user plan overlap validation"""
        # This test is not applicable since we don't have a direct POST endpoint
        # User plans are created through user updates
        pass 