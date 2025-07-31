import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool
from app.main import app
from app.core.database import get_session
from app.models.user import User, UserRole
from app.models.gym import Gym
from app.models.plan import Plan
from app.core.security import get_password_hash
from datetime import datetime, timezone, timedelta
import os

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def session():
    """Create a new database session for a test."""
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def client(session):
    """Create a test client with a database session."""
    def override_get_session():
        yield session
    
    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def test_gym(session):
    """Create a test gym."""
    gym = Gym(
        name="Test Gym",
        address="123 Test Street",
        is_active=True
    )
    session.add(gym)
    session.commit()
    session.refresh(gym)
    return gym

@pytest.fixture
def test_plan(session, test_gym):
    """Create a test plan."""
    plan = Plan(
        name="Test Plan",
        description="A test plan",
        price=50.0,
        duration_days=30,
        gym_id=test_gym.id,
        is_active=True
    )
    session.add(plan)
    session.commit()
    session.refresh(plan)
    return plan

@pytest.fixture
def admin_user(session, test_gym):
    """Create a test admin user."""
    admin = User(
        email="admin@test.com",
        full_name="Admin User",
        document_id="ADMIN123",
        phone_number="1234567890",
        gym_id=test_gym.id,
        role=UserRole.ADMIN,
        hashed_password=get_password_hash("adminpass123"),
        is_active=True
    )
    session.add(admin)
    session.commit()
    session.refresh(admin)
    return admin

@pytest.fixture
def trainer_user(session, test_gym):
    """Create a test trainer user."""
    trainer = User(
        email="trainer@test.com",
        full_name="Trainer User",
        document_id="TRAINER123",
        phone_number="0987654321",
        gym_id=test_gym.id,
        role=UserRole.TRAINER,
        hashed_password=get_password_hash("trainerpass123"),
        is_active=True
    )
    session.add(trainer)
    session.commit()
    session.refresh(trainer)
    return trainer

@pytest.fixture
def regular_user(session, test_gym):
    """Create a test regular user."""
    user = User(
        email="user@test.com",
        full_name="Regular User",
        document_id="USER123",
        phone_number="5555555555",
        gym_id=test_gym.id,
        role=UserRole.USER,
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@pytest.fixture
def admin_token(client, admin_user):
    """Get admin authentication token."""
    # This would normally come from the auth endpoint
    # For testing, we'll mock this by creating a simple token
    from app.core.security import create_access_token
    token = create_access_token(data={"sub": admin_user.email})
    return token

@pytest.fixture
def trainer_token(client, trainer_user):
    """Get trainer authentication token."""
    from app.core.security import create_access_token
    token = create_access_token(data={"sub": trainer_user.email})
    return token

@pytest.fixture(scope="function")
def client_with_auth(session, admin_user, trainer_user):
    """Create a test client with mocked authentication."""
    def override_get_session():
        yield session
    
    def override_get_current_user_admin():
        return admin_user
    
    def override_get_current_user_trainer():
        return trainer_user
    
    from app.core.deps import get_current_user, require_admin, require_trainer_or_admin
    
    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[require_admin] = override_get_current_user_admin
    app.dependency_overrides[require_trainer_or_admin] = override_get_current_user_trainer
    
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear() 