
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from app.core.database import get_session
from app.core.security import get_password_hash
from app.core.deps import require_admin, require_trainer_or_admin
from app.models.user import User, UserCreateWithPassword, UserCreateWithPlan, UserUpdate, UserRole
from app.models.plan import Plan
from app.models.user_plan import UserPlan
from app.models.sale import Sale
from app.models.measurement import Measurement
from app.models.attendance import Attendance
from datetime import datetime, timedelta
from app.models.read_models import UserPlanRead, UserRead, UserBase
from app.core.methods import get_last_plan, check_gym, check_user_by_document_id, check_user_by_email

import pytz

router = APIRouter()


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
    
    check_gym( session, user.gym_id )
    check_user_by_email( session, user.email )
    check_user_by_document_id( session, user.document_id )
    
    hashed_password = get_password_hash(user.password)
    db_user = User.model_validate(user)
    db_user.hashed_password = hashed_password
    
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
    
    check_user_by_email( session, user.email )
    check_user_by_document_id( session, user.document_id )
    
    # Verify plan exists and is active
    # For admins, allow plans from any gym; for trainers, only allow plans from their gym
    if current_user.role == UserRole.ADMIN:
        plan = session.exec( select( Plan ).where( Plan.id == user.plan_id, Plan.is_active == True ) ).first()
    else:
        plan = session.exec( select( Plan ).where( Plan.id == user.plan_id, Plan.is_active == True, Plan.gym_id == current_user.gym_id ) ).first()

    if not plan:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Plan not found, inactive, or not available in this gym"
        )
    
    user.gym_id = current_user.gym_id
    # Create new user without password (regular users don't log in)
    db_user = User.model_validate(user)
    db_user.hashed_password = None
    
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    
    # Create user plan
    expires_at = datetime.now(pytz.timezone('America/Bogota')) + timedelta(days=plan.duration_days)
    
    user_plan = UserPlan(
        user_id=db_user.id,
        plan_id=plan.id,
        purchased_price=plan.price,
        expires_at=expires_at,
        created_by_id=current_user.id,
        payment_type=user.payment_type,
        duration_days=plan.duration_days,
        days=plan.days
    )
    
    session.add( user_plan )
    session.commit()
    
    user_read = UserRead.model_validate(db_user)
    last_plan = get_last_plan(db_user)
    user_read.active_plan = UserPlanRead.model_validate(last_plan) if last_plan else None

    return user_read

@router.get("/", response_model=List[UserRead])
def read_users(
    skip: int = 0,
    limit: int = 100,
    gym_id: Optional[int] = Query(None, description="Filter by gym ID"),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Get all users - Admin and Trainer access only"""
    query = select( User ).options(
        selectinload( User.gym ),
        selectinload( User.user_plans ).selectinload( UserPlan.plan )
    )
    
    if gym_id:
        query = query.where( User.gym_id == gym_id )
    
    if current_user.role == UserRole.TRAINER:
        query = query.where( User.role == UserRole.USER )
    
    users = session.exec( query.offset( skip ).limit( limit ) ).all()

    user_list = []

    for user in users:
        user_data = UserRead.model_validate(user)
        last_plan = get_last_plan(user)
        user_data.active_plan = UserPlanRead.model_validate(last_plan) if last_plan else None

        if user_data.active_plan:
            created_by_user = session.exec( select( User ).where( User.id == user_data.active_plan.created_by_id ) ).first()
            user_data.active_plan.created_by = UserRead.model_validate(created_by_user) if created_by_user else None

        user_list.append(user_data)

    return user_list

@router.get("/search/document/{document_id}", response_model=UserRead)
def search_user_by_document_id(
    document_id: str,
    gym_id: Optional[int] = Query(None, description="Filter by gym ID"),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Search user by document ID - Admin and Trainer access only"""
    query = select(User).where(User.document_id == document_id).options(
        selectinload(User.gym),
        selectinload(User.user_plans).selectinload(UserPlan.plan)
    )
    
    # Filter by gym if specified
    if gym_id:
        query = query.where(User.gym_id == gym_id)

    if current_user.role == UserRole.TRAINER:
        query = query.where( User.role == UserRole.USER )
    
    user = session.exec(query).first()

    if user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado con este número de documento")
    
    user_data = UserRead.model_validate(user)
    last_plan = get_last_plan(user)
    user_data.active_plan = UserPlanRead.model_validate(last_plan) if last_plan else None

    if user_data.active_plan is not None:
        created_by_user = session.exec( select( User ).where( User.id == user_data.active_plan.created_by_id ) ).first()
        user_data.active_plan.created_by = UserBase.model_validate(created_by_user) if created_by_user else None

    return user_data

@router.get("/search/phone/{phone_number}", response_model=List[UserRead])
def search_users_by_phone(
    phone_number: str,
    gym_id: Optional[int] = Query(None, description="Filter by gym ID"),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Search users by phone number (partial match) - Admin and Trainer access only"""
    query = select(User).where(User.phone_number.contains(phone_number)).options(
        selectinload(User.gym),
        selectinload(User.user_plans).selectinload(UserPlan.plan)
    )
    
    # Filter by gym if specified
    if gym_id:
        query = query.where(User.gym_id == gym_id)
    
    if current_user.role == UserRole.TRAINER:
        query = query.where( User.role == UserRole.USER )
    
    users = session.exec(query).all()

    if not users:
        raise HTTPException(status_code=404, detail="No se encontraron usuarios con este número de teléfono")
    
    user_list = []

    for user in users:
        user_data = UserRead.model_validate(user)
        last_plan = get_last_plan(user)
        user_data.active_plan = UserPlanRead.model_validate(last_plan) if last_plan else None

        if user_data.active_plan is not None:
            created_by_user = session.exec( select( User ).where( User.id == user_data.active_plan.created_by_id ) ).first()
            user_data.active_plan.created_by = UserBase.model_validate(created_by_user) if created_by_user else None

        user_list.append(user_data)

    return user_list

@router.get("/{user_id}", response_model=UserRead)
def read_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Get a specific user - Admin and Trainer access only"""
    query = select( User ).where( User.id == user_id ).options(
        selectinload(User.gym),
        selectinload(User.user_plans).selectinload(UserPlan.plan)
    )

    user = session.exec(query).first()

    if user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if current_user.role == UserRole.TRAINER:
        if user.role != UserRole.USER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Los entrenadores solo pueden ver usuarios regulares"
            )
    
    user_data = UserRead.model_validate(user)

    last_plan = get_last_plan(user)
    user_data.active_plan = UserPlanRead.model_validate(last_plan) if last_plan else None
    
    if user_data.active_plan:
        created_by_user = session.exec( select( User ).where( User.id == user_data.active_plan.created_by_id ) ).first()
        user_data.active_plan.created_by = UserRead.model_validate(created_by_user) if created_by_user else None

    return user_data

@router.get("/trainers/", response_model=List[UserRead])
def read_trainers(
    gym_id: Optional[int] = Query(None, description="Filter by gym ID"),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Get all trainers - Admin and Trainer access only"""
    query = select(User).where(User.role == UserRole.TRAINER).options(
        selectinload(User.gym)
    )
    
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
    query = select(User).where(User.role == UserRole.USER).options(
        selectinload(User.gym),
        selectinload(User.user_plans).selectinload(UserPlan.plan)
    )
    
    # Filter by gym if specified
    if gym_id:
        query = query.where(User.gym_id == gym_id)
    
    users = session.exec( query ).all()

    user_list = []

    for user in users:
        user_data = UserRead.model_validate(user)
        last_plan = get_last_plan(user)
        user_data.active_plan = UserPlanRead.model_validate(last_plan) if last_plan else None
        user_list.append(user_data)

    return user_list 


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
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # If trainer, only allow updating regular users in their gym
    if current_user.role == UserRole.TRAINER:
        if db_user.role != UserRole.USER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Los entrenadores solo pueden actualizar usuarios regulares"
            )
        
        if user_update.role is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Los entrenadores no pueden cambiar roles de usuario"
            )
    
    if user_update.email and user_update.email != db_user.email:
        existing_user = session.exec(select(User).where(User.email == user_update.email)).first()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El correo electrónico ya está registrado"
            )
    
    if user_update.document_id and user_update.document_id != db_user.document_id:
        existing_doc = session.exec(select(User).where(User.document_id == user_update.document_id)).first()

        if existing_doc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El número de documento ya está registrado"
            )
        
    user_data = user_update.model_dump(exclude_unset=True)

    # Handle plan_id separately since it's not a field in the User model
    plan_id = user_data.pop('plan_id', None)

    for key, value in user_data.items():
        setattr(db_user, key, value)
    
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    
    if plan_id:
        # For admins, allow plans from any gym; for trainers, only allow plans from their gym
        if current_user.role == UserRole.ADMIN:
            plan = session.exec( select( Plan ).where( Plan.id == plan_id, Plan.is_active == True ) ).first()
        else:
            plan = session.exec( select( Plan ).where( Plan.id == plan_id, Plan.is_active == True, Plan.gym_id == current_user.gym_id ) ).first()

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan no encontrado, inactivo o no disponible en este gimnasio"
            )
        
        # Create user plan
        expires_at = datetime.now(pytz.timezone('America/Bogota')) + timedelta(days=plan.duration_days)
        
        user_plan = UserPlan(
            user_id=db_user.id,
            plan_id=plan.id,
            purchased_price=plan.price,
            expires_at=expires_at,
            created_by_id=current_user.id,
            payment_type=user_update.payment_type,
            duration_days=plan.duration_days,
            days=plan.days
        )

        session.add(user_plan)
        session.commit()
        
        # Refresh the user and reload with relationships
        session.refresh(db_user)
    
    user_read = UserRead.model_validate(db_user)
    last_plan = get_last_plan(db_user)
    user_read.active_plan = UserPlanRead.model_validate(last_plan) if last_plan else None

    return user_read


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin)
):
    """Delete a user - Admin access only"""
    db_user = session.exec(select(User).where(User.id == user_id)).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Check if user has any related data that would prevent deletion
    
    # Check for related data
    user_plans = session.exec(select(UserPlan).where(UserPlan.user_id == user_id)).all()
    sales = session.exec(select(Sale).where(Sale.sold_by_id == user_id)).all()
    measurements = session.exec(select(Measurement).where(Measurement.user_id == user_id)).all()
    attendance = session.exec(select(Attendance).where(Attendance.user_id == user_id)).all()
    
    # Delete related data first (cascade delete)
    for user_plan in user_plans:
        session.delete(user_plan)
    for sale in sales:
        session.delete(sale)
    for measurement in measurements:
        session.delete(measurement)
    for record in attendance:
        session.delete(record)
    
    # Now delete the user
    session.delete(db_user)
    session.commit()
    return {"message": "Usuario eliminado exitosamente"}
