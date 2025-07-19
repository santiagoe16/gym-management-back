from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from app.core.database import get_session
from app.core.security import get_password_hash
from app.core.deps import get_current_active_user, require_admin, require_trainer_or_admin
from app.models.user import User, UserCreateWithPassword, UserCreateWithoutPassword, UserCreateWithPlan, UserRead, UserUpdate, UserRole
from app.models.plan import Plan
from app.models.user_plan import UserPlan, UserPlanCreate
from app.models.gym import Gym
from datetime import datetime, timedelta
from decimal import Decimal

router = APIRouter()

@router.get("/", response_model=List[UserRead])
def read_users(
    skip: int = 0,
    limit: int = 100,
    gym_id: Optional[int] = Query(None, description="Filter by gym ID"),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Get all users - Admin and Trainer access only"""
    query = select(User)
    
    # Filter by gym if specified
    if gym_id:
        query = query.where(User.gym_id == gym_id)
    
    # If trainer, only show users from their gym
    if current_user.role == UserRole.TRAINER:
        query = query.where(User.gym_id == current_user.gym_id)
    
    users = session.exec(query.offset(skip).limit(limit)).all()
    return users

@router.post("/admin-trainer", response_model=UserRead)
def create_admin_or_trainer(
    user: UserCreateWithPassword,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin)
):
    """Create a new admin or trainer user - Admin access only"""
    # Only allow creating admin or trainer users
    if user.role == UserRole.USER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Use /with-plan endpoint to create regular users with plans"
        )
    
    # Verify gym exists
    gym = session.exec(select(Gym).where(Gym.id == user.gym_id, Gym.is_active == True)).first()
    if not gym:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gym not found or inactive"
        )
    
    # Check if user already exists by email
    existing_user = session.exec(select(User).where(User.email == user.email)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if document ID already exists
    existing_doc = session.exec(select(User).where(User.document_id == user.document_id)).first()
    if existing_doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document ID already registered"
        )
    
    # Create new user with password
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        full_name=user.full_name,
        document_id=user.document_id,
        phone_number=user.phone_number,
        gym_id=user.gym_id,
        role=user.role,
        hashed_password=hashed_password
    )
    
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user



@router.post("/with-plan", response_model=UserRead)
def create_user_with_plan(
    user: UserCreateWithPlan,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Create a new regular user with plan - Admin and Trainer access"""
    
    # Only allow creating regular users (not admins or trainers)
    if user.role != UserRole.USER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only regular users can be created with plans"
        )
    
    # Verify gym exists
    gym = session.exec(select(Gym).where(Gym.id == user.gym_id, Gym.is_active == True)).first()
    if not gym:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gym not found or inactive"
        )
    
    # If trainer, only allow creating users in their gym
    if current_user.role == UserRole.TRAINER and user.gym_id != current_user.gym_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create users in your own gym"
        )
    
    # Check if user already exists by email
    existing_user = session.exec(select(User).where(User.email == user.email)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if document ID already exists
    existing_doc = session.exec(select(User).where(User.document_id == user.document_id)).first()
    if existing_doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document ID already registered"
        )
    
    # Verify plan exists and is active and belongs to the same gym
    plan = session.exec(select(Plan).where(Plan.id == user.plan_id, Plan.is_active == True, Plan.gym_id == user.gym_id)).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found, inactive, or not available in this gym"
        )
    
    # Create new user without password (regular users don't log in)
    db_user = User(
        email=user.email,
        full_name=user.full_name,
        document_id=user.document_id,
        phone_number=user.phone_number,
        gym_id=user.gym_id,
        role=user.role,
        hashed_password=None  # Regular users don't need passwords
    )
    
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    
    # Create user plan
    purchased_price = Decimal(str(user.purchased_price)) if user.purchased_price else plan.price
    expires_at = datetime.utcnow() + timedelta(days=plan.duration_days)
    
    user_plan = UserPlan(
        user_id=db_user.id,
        plan_id=plan.id,
        purchased_price=purchased_price,
        expires_at=expires_at,
        created_by_id=current_user.id
    )
    
    session.add(user_plan)
    session.commit()
    
    return db_user

@router.get("/search/document/{document_id}", response_model=UserRead)
def search_user_by_document_id(
    document_id: str,
    gym_id: Optional[int] = Query(None, description="Filter by gym ID"),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Search user by document ID - Admin and Trainer access only"""
    query = select(User).where(User.document_id == document_id)
    
    # Filter by gym if specified
    if gym_id:
        query = query.where(User.gym_id == gym_id)
    
    # If trainer, only search in their gym
    if current_user.role == UserRole.TRAINER:
        query = query.where(User.gym_id == current_user.gym_id)
    
    user = session.exec(query).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found with this document ID")
    return user

@router.get("/search/phone/{phone_number}", response_model=List[UserRead])
def search_users_by_phone(
    phone_number: str,
    gym_id: Optional[int] = Query(None, description="Filter by gym ID"),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Search users by phone number (partial match) - Admin and Trainer access only"""
    query = select(User).where(User.phone_number.contains(phone_number))
    
    # Filter by gym if specified
    if gym_id:
        query = query.where(User.gym_id == gym_id)
    
    # If trainer, only search in their gym
    if current_user.role == UserRole.TRAINER:
        query = query.where(User.gym_id == current_user.gym_id)
    
    users = session.exec(query).all()
    if not users:
        raise HTTPException(status_code=404, detail="No users found with this phone number")
    return users

@router.get("/{user_id}", response_model=UserRead)
def read_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Get a specific user - Admin and Trainer access only"""
    user = session.exec(select(User).where(User.id == user_id)).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Update a user - Admin and Trainer access with restrictions"""
    db_user = session.exec(select(User).where(User.id == user_id)).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # If trainer, only allow updating regular users in their gym
    if current_user.role == UserRole.TRAINER:
        # Trainers can only update regular users (not admins or other trainers)
        if db_user.role != UserRole.USER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Trainers can only update regular users"
            )
        
        # Trainers can only update users in their own gym
        if db_user.gym_id != current_user.gym_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update users in your own gym"
            )
        
        # Trainers cannot change user role or gym_id
        if user_update.role is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Trainers cannot change user roles"
            )
        
        if user_update.gym_id is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Trainers cannot change user gym assignment"
            )
    
    # Check for email uniqueness if email is being updated
    if user_update.email and user_update.email != db_user.email:
        existing_user = session.exec(select(User).where(User.email == user_update.email)).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Check for document ID uniqueness if document_id is being updated
    if user_update.document_id and user_update.document_id != db_user.document_id:
        existing_doc = session.exec(select(User).where(User.document_id == user_update.document_id)).first()
        if existing_doc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document ID already registered"
            )
    
    # Update user data
    user_data = user_update.dict(exclude_unset=True)
    for key, value in user_data.items():
        setattr(db_user, key, value)
    
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin)
):
    """Delete a user - Admin access only"""
    db_user = session.exec(select(User).where(User.id == user_id)).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    session.delete(db_user)
    session.commit()
    return {"message": "User deleted successfully"}

@router.get("/trainers/", response_model=List[UserRead])
def read_trainers(
    gym_id: Optional[int] = Query(None, description="Filter by gym ID"),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Get all trainers - Admin and Trainer access only"""
    query = select(User).where(User.role == UserRole.TRAINER)
    
    # Filter by gym if specified
    if gym_id:
        query = query.where(User.gym_id == gym_id)
    
    # If trainer, only show trainers from their gym
    if current_user.role == UserRole.TRAINER:
        query = query.where(User.gym_id == current_user.gym_id)
    
    trainers = session.exec(query).all()
    return trainers

@router.get("/users/", response_model=List[UserRead])
def read_regular_users(
    gym_id: Optional[int] = Query(None, description="Filter by gym ID"),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Get all regular users - Admin and Trainer access only"""
    query = select(User).where(User.role == UserRole.USER)
    
    # Filter by gym if specified
    if gym_id:
        query = query.where(User.gym_id == gym_id)
    
    # If trainer, only show users from their gym
    if current_user.role == UserRole.TRAINER:
        query = query.where(User.gym_id == current_user.gym_id)
    
    users = session.exec(query).all()
    return users 