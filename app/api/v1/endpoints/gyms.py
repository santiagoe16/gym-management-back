from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.core.database import get_session
from app.core.deps import get_current_active_user, require_admin
from app.models.gym import Gym, GymCreate, GymUpdate
from app.models.read_models import GymRead
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=List[GymRead])
def read_gyms(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Get all gyms - All authenticated users can view"""
    gyms = session.exec(select(Gym).offset(skip).limit(limit)).all()
    return gyms

@router.get("/active", response_model=List[GymRead])
def read_active_gyms(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Get all active gyms - All authenticated users can view"""
    gyms = session.exec(select(Gym).where(Gym.is_active == True)).all()
    return gyms

@router.post("/", response_model=GymRead)
def create_gym(
    gym: GymCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin)
):
    """Create a new gym - Admin access only"""
    # Check if gym already exists
    existing_gym = session.exec(select(Gym).where(Gym.name == gym.name)).first()

    if existing_gym:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gym with this name already exists"
        )
    
    # Create new gym
    db_gym = Gym.model_validate(gym)
    
    session.add(db_gym)
    session.commit()
    session.refresh(db_gym)
    return db_gym

@router.get("/{gym_id}", response_model=GymRead)
def read_gym(
    gym_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific gym - All authenticated users can view"""
    gym = session.exec(select(Gym).where(Gym.id == gym_id)).first()
    if gym is None:
        raise HTTPException(status_code=404, detail="Gym not found")
    return gym

@router.put("/{gym_id}", response_model=GymRead)
def update_gym(
    gym_id: int,
    gym_update: GymUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin)
):
    """Update a gym - Admin access only"""
    db_gym = session.exec(select(Gym).where(Gym.id == gym_id)).first()
    if db_gym is None:
        raise HTTPException(status_code=404, detail="Gym not found")
    
    # Update gym data
    gym_data = gym_update.model_dump(exclude_unset=True)
    for key, value in gym_data.items():
        setattr(db_gym, key, value)
    
    session.add(db_gym)
    session.commit()
    session.refresh(db_gym)
    return db_gym

@router.delete("/{gym_id}")
def delete_gym(
    gym_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin)
):
    """Delete a gym - Admin access only"""
    db_gym = session.exec(select(Gym).where(Gym.id == gym_id)).first()

    if db_gym is None:
        raise HTTPException(status_code=404, detail="Gym not found")
    
    # Check if gym has any users, plans, products, or sales
    users = session.exec(select(User).where(User.gym_id == gym_id)).all()
    users_count = len(users)

    if users_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete gym with existing users. Deactivate it instead."
        )
    
    session.delete(db_gym)
    session.commit()
    
    return {"message": "Gym deleted successfully"} 