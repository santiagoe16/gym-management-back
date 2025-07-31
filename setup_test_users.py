#!/usr/bin/env python3
"""
Script to set up test users in the database for testing
Run this script to create the necessary test users
"""

import sys
import os
from sqlmodel import Session, create_engine, select
from app.models.user import User, UserRole
from app.models.gym import Gym
from app.core.security import get_password_hash
from app.core.config import settings

def setup_test_users():
    """Set up test users in the database"""
    
    # Create database engine
    engine = create_engine(settings.DATABASE_URL)
    
    with Session(engine) as session:
        print("Setting up test users...")
        
        # Check if test gym exists, create if not
        gym = session.exec(select(Gym).where(Gym.name == "Test Gym")).first()
        if not gym:
            print("Creating test gym...")
            gym = Gym(
                name="Test Gym",
                address="123 Test Street",
                is_active=True
            )
            session.add(gym)
            session.commit()
            session.refresh(gym)
            print(f"Created test gym with ID: {gym.id}")
        else:
            print(f"Using existing test gym with ID: {gym.id}")
        
        # Check if admin user exists
        admin_user = session.exec(select(User).where(User.email == "admin@test.com")).first()
        if not admin_user:
            print("Creating admin user...")
            admin_user = User(
                email="admin@test.com",
                full_name="Admin User",
                document_id="ADMIN123",
                phone_number="1234567890",
                gym_id=gym.id,
                role=UserRole.ADMIN,
                hashed_password=get_password_hash("adminpass123"),
                is_active=True
            )
            session.add(admin_user)
            session.commit()
            session.refresh(admin_user)
            print(f"Created admin user with ID: {admin_user.id}")
        else:
            print(f"Admin user already exists with ID: {admin_user.id}")
        
        # Check if trainer user exists
        trainer_user = session.exec(select(User).where(User.email == "trainer@test.com")).first()
        if not trainer_user:
            print("Creating trainer user...")
            trainer_user = User(
                email="trainer@test.com",
                full_name="Trainer User",
                document_id="TRAINER123",
                phone_number="0987654321",
                gym_id=gym.id,
                role=UserRole.TRAINER,
                hashed_password=get_password_hash("trainerpass123"),
                is_active=True
            )
            session.add(trainer_user)
            session.commit()
            session.refresh(trainer_user)
            print(f"Created trainer user with ID: {trainer_user.id}")
        else:
            print(f"Trainer user already exists with ID: {trainer_user.id}")
        
        # Check if regular user exists
        regular_user = session.exec(select(User).where(User.email == "user@test.com")).first()
        if not regular_user:
            print("Creating regular user...")
            regular_user = User(
                email="user@test.com",
                full_name="Regular User",
                document_id="USER123",
                phone_number="5555555555",
                gym_id=gym.id,
                role=UserRole.USER,
                is_active=True
            )
            session.add(regular_user)
            session.commit()
            session.refresh(regular_user)
            print(f"Created regular user with ID: {regular_user.id}")
        else:
            print(f"Regular user already exists with ID: {regular_user.id}")
        
        print("\n✅ Test users setup complete!")
        print("\nTest Users:")
        print(f"  Admin: admin@test.com / adminpass123")
        print(f"  Trainer: trainer@test.com / trainerpass123")
        print(f"  Regular User: user@test.com (no password - regular users don't log in)")
        print(f"\nTest Gym ID: {gym.id}")

def main():
    """Main function"""
    try:
        setup_test_users()
    except Exception as e:
        print(f"❌ Error setting up test users: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 