
from sqlmodel import Session, select
from app.models.user import User, UserRole
from app.models.gym import Gym
from app.models.user import User
from app.models.read_models import UserPlanRead
from fastapi import HTTPException, status
from datetime import datetime, timezone

def get_last_plan( user: User ) -> UserPlanRead:
    """Get the most recent active and valid plan for a user"""
    if not user.user_plans:
        return None
    
    # Get active plans that haven't expired
    current_time = datetime.now(timezone.utc)
    valid_plans = []
    
    for up in user.user_plans:
        if not up.is_active:
            continue
            
        # Ensure expires_at is timezone-aware
        expires_at = up.expires_at
        if expires_at.tzinfo is None:
            # If timezone-naive, assume UTC
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        if expires_at > current_time:
            valid_plans.append(up)
    
    if not valid_plans:
        return None
    
    # Get the most recent valid plan by purchased_at timestamp
    latest_plan = max(valid_plans, key=lambda up: up.purchased_at)
    
    return latest_plan

def check_gym( session: Session, gym_id: int ):
    gym = session.exec(select(Gym).where(Gym.id == gym_id, Gym.is_active == True)).first()

    if not gym:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gimnasio no encontrado o inactivo"
        )
    
def check_trainer_gym( gym_id: int, user: User, message: str ):
    if user.role == UserRole.TRAINER and gym_id != user.gym_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=message
        )

def check_user_by_document_id_and_gym( session: Session, document_id: str, gym_id: int ):
    user = session.exec(select(User).where(User.document_id == document_id, User.gym_id == gym_id)).first()

    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El número de documento ya está registrado en este gimnasio"
        )

def check_user_by_document_id( session: Session, document_id: str ):
    user = session.exec( select( User ).where( User.document_id == document_id ) ).first()

    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El número de documento ya está registrado"
        )

def check_user_by_email_and_gym( session: Session, email: str, gym_id: int ):
    user = session.exec(select(User).where(User.email == email, User.gym_id == gym_id)).first()

    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya está registrado en este gimnasio"
        )

def check_user_by_email( session: Session, email: str ):
    user = session.exec( select( User ).where( User.email == email ) ).first()

    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya está registrado"
        )

def check_user_by_id_and_gym( session: Session, user_id: int, gym_id: int ):
    user = session.exec(select(User).where(User.id == user_id, User.gym_id == gym_id)).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario no registrado en este gimnasio"
        )

    return user

def check_user_by_id( session: Session, user_id: int ):
    user = session.exec(select(User).where(User.id == user_id)).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario no registrado"
        )

    return user

def get_user_by_document_id( session: Session, document_id: str, gym_id: int ):
    user = session.exec(select(User).where(User.document_id == document_id, User.gym_id == gym_id)).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Número de documento no registrado en este gimnasio"
        )

    return user

def get_user_by_id( session: Session, user_id: int, gym_id: int ):
    user = session.exec(select(User).where(User.id == user_id, User.gym_id == gym_id)).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario no registrado en este gimnasio"
        )

    return user

async def get_user_by_email( session: Session, email: str ):
    user = session.exec( select( User ).where( User.email == email ) ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Correo electrónico o contraseña incorrectos"
        )

    return user

def get_user_by_email_and_gym( session: Session, email: str, gym_id: int ):
    user = session.exec(select(User).where(User.email == email, User.gym_id == gym_id)).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Correo electrónico no registrado en este gimnasio"
        )

    return user
