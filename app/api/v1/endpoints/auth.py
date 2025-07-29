from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.core.database import get_session
from app.core.security import verify_password, create_access_token
from app.models.auth import Token, LoginRequest
from app.models.user import User, UserRole
from app.core.deps import get_current_active_user
from app.core.methods import get_user_by_email

router = APIRouter()

@router.post("/login", response_model=Token)
def login(login_data: LoginRequest, session: Session = Depends(get_session)):
    # Debug breakpoint - uncomment the next line to pause execution
    # import pdb; pdb.set_trace()
    
    user = get_user_by_email( session, login_data.email, login_data.gym_id )
    
    if user.role == UserRole.USER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Users cannot login to the system"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.role == UserRole.TRAINER and user.gym_id != login_data.gym_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not belong to this gym"
        )
    
    # Create access token without expiration - user stays logged in until logout
    access_token = create_access_token(data={"sub": user.email})

    return Token( access_token = access_token, token_type = "bearer", user = user)

@router.get("/me")
def read_users_me(current_user: User = Depends(get_current_active_user)):
    user_data = {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "is_active": current_user.is_active
    }

    if current_user.role == UserRole.TRAINER:
        user_data["schedule_start"] = current_user.schedule_start
        user_data["schedule_end"] = current_user.schedule_end

    return user_data