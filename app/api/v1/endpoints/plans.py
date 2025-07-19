from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.core.database import get_session
from app.core.deps import get_current_active_user, require_admin
from app.models.user import User
from app.models.plan import Plan, PlanCreate, PlanRead, PlanUpdate
from decimal import Decimal

router = APIRouter()

@router.get("/", response_model=List[PlanRead])
def read_plans(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Get all plans - Admin and Trainer access"""
    plans = session.exec(select(Plan).offset(skip).limit(limit)).all()
    return plans

@router.get("/active", response_model=List[PlanRead])
def read_active_plans(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Get all active plans - Admin and Trainer access"""
    plans = session.exec(select(Plan).where(Plan.is_active == True)).all()
    return plans

@router.post("/", response_model=PlanRead)
def create_plan(
    plan: PlanCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin)
):
    """Create a new plan - Admin access only"""
    # Check if plan with same name already exists
    existing_plan = session.exec(select(Plan).where(Plan.name == plan.name)).first()
    if existing_plan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Plan with this name already exists"
        )
    
    db_plan = Plan(
        name=plan.name,
        description=plan.description,
        base_price=plan.base_price,
        duration_days=plan.duration_days,
        is_active=plan.is_active
    )
    
    session.add(db_plan)
    session.commit()
    session.refresh(db_plan)
    return db_plan

@router.get("/{plan_id}", response_model=PlanRead)
def read_plan(
    plan_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific plan - Admin and Trainer access"""
    plan = session.exec(select(Plan).where(Plan.id == plan_id)).first()
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan

@router.put("/{plan_id}", response_model=PlanRead)
def update_plan(
    plan_id: int,
    plan_update: PlanUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin)
):
    """Update a plan - Admin access only"""
    db_plan = session.exec(select(Plan).where(Plan.id == plan_id)).first()
    if db_plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Update plan data
    plan_data = plan_update.dict(exclude_unset=True)
    for key, value in plan_data.items():
        setattr(db_plan, key, value)
    
    session.add(db_plan)
    session.commit()
    session.refresh(db_plan)
    return db_plan

@router.delete("/{plan_id}")
def delete_plan(
    plan_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin)
):
    """Delete a plan - Admin access only"""
    db_plan = session.exec(select(Plan).where(Plan.id == plan_id)).first()
    if db_plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    session.delete(db_plan)
    session.commit()
    return {"message": "Plan deleted successfully"} 