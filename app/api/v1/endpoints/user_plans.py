from time import timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select
from app.core.database import get_session
from app.core.deps import require_admin, require_trainer_or_admin
from app.models.user import User, UserRole
from app.models.plan import Plan
from app.models.user_plan import UserPlan, UserPlanUpdate
from datetime import datetime, timezone
from app.models.read_models import UserPlanRead

router = APIRouter()

@router.get("/", response_model=List[UserPlanRead])
def read_user_plans(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    gym_id: Optional[int] = Query(None, description="Filter by gym ID"),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Get all user plans - Admin and Trainer access only"""
    query = select(UserPlan).options(selectinload(UserPlan.user), selectinload(UserPlan.plan), selectinload(UserPlan.created_by))
    
    # Filter by user if specified
    if user_id:
        query = query.where(UserPlan.user_id == user_id)
    
    # Filter by gym if specified
    if gym_id:
        query = query.join(User, UserPlan.user_id == User.id).where(User.gym_id == gym_id)
    
    # If trainer, only show user plans from their gym
    if current_user.role == UserRole.TRAINER:
        query = query.join(User, UserPlan.user_id == User.id).where(User.gym_id == current_user.gym_id)
    
    user_plans = session.exec(query.offset(skip).limit(limit)).all()
    return user_plans

@router.get("/user/{user_id}", response_model=List[UserPlanRead])
def read_user_plans_by_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Get all plans for a specific user - Admin and Trainer access only"""
    # Get the user
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # If trainer, only allow access to users in their gym
    if current_user.role == UserRole.TRAINER and user.gym_id != current_user.gym_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access users in your own gym"
        )
    
    user_plans = session.exec(select(UserPlan).options(selectinload(UserPlan.user), selectinload(UserPlan.plan), selectinload(UserPlan.created_by)).where(UserPlan.user_id == user_id)).all()
    return user_plans

@router.get("/user/{user_id}/active", response_model=UserPlanRead)
def read_user_active_plan(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Get the active plan for a specific user - Admin and Trainer access only"""
    # Get the user
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # If trainer, only allow access to users in their gym
    if current_user.role == UserRole.TRAINER and user.gym_id != current_user.gym_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access users in your own gym"
        )
    
    # Get the active plan
    active_plan = session.exec(
        select(UserPlan).options(selectinload(UserPlan.user), selectinload(UserPlan.plan), selectinload(UserPlan.created_by))
        .where(UserPlan.user_id == user_id, UserPlan.is_active == True)
        .order_by(UserPlan.expires_at.desc())
    ).first()
    
    if not active_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active plan found for this user"
        )
    
    return active_plan

@router.put("/{user_plan_id}", response_model=UserPlanRead)
def update_user_plan(
    user_plan_id: int,
    user_plan_update: UserPlanUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Update a user plan - Admin and Trainer access with restrictions"""
    # Get the user plan
    db_user_plan = session.exec(select(UserPlan).where(UserPlan.id == user_plan_id)).first()
    if not db_user_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User plan not found"
        )
    
    # Get the user
    user = session.exec(select(User).where(User.id == db_user_plan.user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # If trainer, only allow updating plans for users in their gym
    if current_user.role == UserRole.TRAINER and user.gym_id != current_user.gym_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update plans for users in your own gym"
        )
    
    # Check if trainer is trying to modify a plan
    if current_user.role == UserRole.TRAINER:
        # Get current plan details
        current_plan = session.exec(select(Plan).where(Plan.id == db_user_plan.plan_id)).first()
        
        # Check if plan is expired
        is_expired = db_user_plan.expires_at < datetime.now(timezone.utc)
        
        # Check if it's an upgrade (new plan has longer duration or higher price)
        is_upgrade = False
        if user_plan_update.plan_id:
            new_plan = session.exec(select(Plan).where(Plan.id == user_plan_update.plan_id)).first()
            if new_plan:
                # Check if new plan has longer duration
                if new_plan.duration_days > current_plan.duration_days:
                    is_upgrade = True
                # Check if new plan has higher price (indicating premium features)
                elif new_plan.price > current_plan.price:
                    is_upgrade = True
        
        # Trainers can only modify if plan is expired or it's an upgrade
        if not is_expired and not is_upgrade:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Trainers can only modify user plans if the current plan has expired or if upgrading to a better plan"
            )
    
    # Update the user plan
    update_data = user_plan_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user_plan, field, value)
    
    db_user_plan.updated_at = datetime.now(timezone.utc)
    session.add(db_user_plan)
    session.commit()
    session.refresh(db_user_plan)
    return db_user_plan

@router.delete("/{user_plan_id}")
def delete_user_plan(
    user_plan_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin)
):
    """Delete a user plan - Admin access only"""
    # Get the user plan
    db_user_plan = session.exec(select(UserPlan).where(UserPlan.id == user_plan_id)).first()
    if not db_user_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User plan not found"
        )
    
    session.delete(db_user_plan)
    session.commit()
    return {"message": "User plan deleted successfully"} 