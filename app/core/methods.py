
from sqlmodel import Session, select
from app.models.user import User, UserRole
from app.models.gym import Gym
from fastapi import HTTPException, status

def get_last_plan( user ):
    """Get the most recent active plan for a user"""
    if not user.user_plans:
        return None
    
    # Get the most recent plan by purchased_at timestamp (matches relationship ordering)
    latest_plan = max(user.user_plans, key=lambda up: up.purchased_at)
    
    return latest_plan

def check_gym( session: Session, gym_id: int ):
    gym = session.exec(select(Gym).where(Gym.id == gym_id, Gym.is_active == True)).first()

    if not gym:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gym not found or inactive"
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
            detail="Document ID already registered in this gym"
        )

def check_user_by_document_id( session: Session, document_id: str ):
    user = session.exec( select( User ).where( User.document_id == document_id ) ).first()

    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document ID already registered"
        )

def check_user_by_email_and_gym( session: Session, email: str, gym_id: int ):
    user = session.exec(select(User).where(User.email == email, User.gym_id == gym_id)).first()

    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered in this gym"
        )

def check_user_by_email( session: Session, email: str ):
    user = session.exec( select( User ).where( User.email == email ) ).first()

    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

def check_user_by_id( session: Session, user_id: int, gym_id: int ):
    user = session.exec(select(User).where(User.id == user_id, User.gym_id == gym_id)).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not registered in this gym"
        )

    return user

def get_user_by_document_id( session: Session, document_id: str, gym_id: int ):
    user = session.exec(select(User).where(User.document_id == document_id, User.gym_id == gym_id)).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document ID not registered on this gym"
        )

    return user

def get_user_by_id( session: Session, user_id: int, gym_id: int ):
    user = session.exec(select(User).where(User.id == user_id, User.gym_id == gym_id)).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not registered in this gym"
        )

    return user

def get_user_by_email( session: Session, email: str, gym_id: int ):
    user = session.exec(select(User).where(User.email == email, User.gym_id == gym_id)).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not registered in this gym"
        )

    return user
