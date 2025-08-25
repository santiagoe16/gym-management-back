from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.core.database import get_session
from app.core.deps import get_current_active_user, require_admin
from app.models.gym import Gym, GymCreate, GymUpdate
from app.models.read_models import GymRead
from app.models.user import User, UserRole

router = APIRouter()

@router.get("/", response_model=List[GymRead])
def read_gyms(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session)
):
    gyms = session.exec( select( Gym ).offset( skip ).limit( limit ) ).all()
    
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
    existing_gym = session.exec( select( Gym ).where( Gym.name == gym.name ) ).first()

    if existing_gym:
        return existing_gym
    
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
        raise HTTPException(status_code=404, detail="Gimnasio no encontrado")
    return gym

@router.put("/{gym_id}", response_model=GymRead)
def update_gym(
    gym_id: int,
    gym_update: GymUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin)
):
    """Update a gym - Admin access only"""
    db_gym = session.exec( select( Gym ).where( Gym.id == gym_id ) ).first()

    if db_gym is None:
        raise HTTPException( status_code = 404, detail = "Gimnasio no encontrado" )
    
    if gym_update.name:
        existing_gym = session.exec( select( Gym ).where( Gym.name == gym_update.name ) ).first()
        
        if existing_gym is None:
            raise HTTPException( status_code = 404, detail=  "Ya existe un gimnasio con este nombre" )
    
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
        raise HTTPException(status_code=404, detail="Gimnasio no encontrado")
    
    # Check if gym has any related data that would prevent deletion
    from app.models.user import User
    from app.models.plan import Plan
    from app.models.product import Product
    from app.models.sale import Sale
    from app.models.attendance import Attendance
    from app.models.user_plan import UserPlan
    from app.models.measurement import Measurement
    
    # Check for related data
    users = session.exec(select(User).where(User.gym_id == gym_id, User.role == UserRole.TRAINER)).all()
    plans = session.exec(select(Plan).where(Plan.gym_id == gym_id)).all()
    products = session.exec(select(Product).where(Product.gym_id == gym_id)).all()
    sales = session.exec(select(Sale).where(Sale.gym_id == gym_id)).all()
    attendance = session.exec(select(Attendance).where(Attendance.gym_id == gym_id)).all()
    
    # Get user plans for users in this gym
    user_plans = []
    for user in users:
        user_plans.extend(session.exec(select(UserPlan).join(Plan).where(Plan.gym_id == gym_id)).all())
    
    # Get measurements for users in this gym
    measurements = []
    for user in users:
        measurements.extend(session.exec(select(Measurement).join(User).where(User.gym_id == gym_id)).all())
    
    # Delete related data first (cascade delete)
    for user_plan in user_plans:
        session.delete(user_plan)
    for measurement in measurements:
        session.delete(measurement)
    for record in attendance:
        session.delete(record)
    for sale in sales:
        session.delete(sale)
    for product in products:
        session.delete(product)
    for plan in plans:
        session.delete(plan)
    for user in users:
        session.delete(user)
    
    # Now delete the gym
    session.delete(db_gym)
    session.commit()
    
    return {"message": "Gimnasio eliminado exitosamente"} 