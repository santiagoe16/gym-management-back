import pytest
from fastapi.testclient import TestClient
from app.models.user import User, UserRole
from app.models.gym import Gym
from app.core.security import get_password_hash


class TestAuthEndpoints:
    """Test authentication endpoints"""
    
    def test_login_success_admin(self, client, admin_user):
        """Test successful admin login"""
        response = client.post("/api/v1/auth/login", json={
            "email": admin_user.email,
            "password": "adminpass123",
            "gym_id": admin_user.gym_id
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == admin_user.email
        assert data["user"]["role"] == "admin"
    
    def test_login_success_trainer(self, client, trainer_user):
        """Test successful trainer login"""
        response = client.post("/api/v1/auth/login", json={
            "email": trainer_user.email,
            "password": "trainerpass123",
            "gym_id": trainer_user.gym_id
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == trainer_user.email
        assert data["user"]["role"] == "trainer"
    
    def test_login_invalid_credentials(self, client, admin_user):
        """Test login with invalid password"""
        response = client.post("/api/v1/auth/login", json={
            "email": admin_user.email,
            "password": "wrongpassword",
            "gym_id": admin_user.gym_id
        })
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Correo electrónico o contraseña incorrectos" in data["detail"]
    
    def test_login_user_not_found(self, client, test_gym):
        """Test login with non-existent user"""
        response = client.post("/api/v1/auth/login", json={
            "email": "nonexistent@test.com",
            "password": "anypassword",
            "gym_id": test_gym.id
        })
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Correo electrónico no registrado en este gimnasio" in data["detail"]
    
    def test_login_inactive_user(self, client, test_gym):
        """Test login with inactive user"""
        # Create an inactive user
        inactive_user = User(
            email="inactive@test.com",
            full_name="Inactive User",
            document_id="INACTIVE123",
            phone_number="1111111111",
            gym_id=test_gym.id,
            role=UserRole.ADMIN,
            hashed_password=get_password_hash("password123"),
            is_active=False
        )
        
        # Add to session
        from app.core.database import get_session
        session = next(get_session())
        session.add(inactive_user)
        session.commit()
        session.refresh(inactive_user)
        
        response = client.post("/api/v1/auth/login", json={
            "email": inactive_user.email,
            "password": "password123",
            "gym_id": inactive_user.gym_id
        })
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Correo electrónico no registrado en este gimnasio" in data["detail"]
        
        # Cleanup
        session.delete(inactive_user)
        session.commit()
    
    def test_login_wrong_gym(self, client, admin_user, test_gym):
        """Test login with wrong gym_id"""
        # Create another gym with unique name
        other_gym = Gym(
            name="Other Gym Wrong",
            address="456 Other Street",
            is_active=True
        )
        
        from app.core.database import get_session
        session = next(get_session())
        session.add(other_gym)
        session.commit()
        session.refresh(other_gym)
        
        response = client.post("/api/v1/auth/login", json={
            "email": admin_user.email,
            "password": "adminpass123",
            "gym_id": other_gym.id  # Wrong gym
        })
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Correo electrónico no registrado en este gimnasio" in data["detail"]
        
        # Cleanup
        session.delete(other_gym)
        session.commit()
    
    def test_login_missing_fields(self, client):
        """Test login with missing required fields"""
        # Missing email
        response = client.post("/api/v1/auth/login", json={
            "password": "password123",
            "gym_id": 1
        })
        assert response.status_code == 422
        
        # Missing password
        response = client.post("/api/v1/auth/login", json={
            "email": "test@test.com",
            "gym_id": 1
        })
        assert response.status_code == 422
        
        # Missing gym_id
        response = client.post("/api/v1/auth/login", json={
            "email": "test@test.com",
            "password": "password123"
        })
        assert response.status_code == 422
    
    def test_login_invalid_email_format(self, client, test_gym):
        """Test login with invalid email format"""
        response = client.post("/api/v1/auth/login", json={
            "email": "invalid-email",
            "password": "password123",
            "gym_id": test_gym.id
        })
        
        assert response.status_code == 400
    
    def test_regular_user_cannot_login(self, client, regular_user):
        """Test that regular users cannot login (they don't have passwords)"""
        response = client.post("/api/v1/auth/login", json={
            "email": regular_user.email,
            "password": "anypassword",
            "gym_id": regular_user.gym_id
        })
        
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data
        assert "Los usuarios no pueden iniciar sesión en el sistema" in data["detail"]
    
    def test_token_validation(self, client, admin_user):
        """Test that generated token is valid and can be used"""
        # Login to get token
        login_response = client.post("/api/v1/auth/login", json={
            "email": admin_user.email,
            "password": "adminpass123",
            "gym_id": admin_user.gym_id
        })
        
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Use token to access protected endpoint
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/users/", headers=headers)
        
        assert response.status_code == 200
    
    def test_invalid_token(self, client):
        """Test access with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/users/", headers=headers)
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "No se pudieron validar las credenciales" in data["detail"]
    
    def test_missing_token(self, client):
        """Test access without token"""
        response = client.get("/api/v1/users/")
        
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data
        assert "Not authenticated" in data["detail"]
    
    def test_expired_token(self, client, admin_user):
        """Test access with expired token"""
        from app.core.security import create_access_token
        from datetime import timedelta
        
        # Create an expired token
        expired_token = create_access_token(
            data={"sub": admin_user.email},
            expires_delta=timedelta(seconds=-1)  # Expired 1 second ago
        )
        
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/api/v1/users/", headers=headers)
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "No se pudieron validar las credenciales" in data["detail"] 