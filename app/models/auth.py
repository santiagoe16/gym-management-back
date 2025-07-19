from sqlmodel import SQLModel
from typing import Optional
from app.models.user import UserRole

class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole

class TokenData(SQLModel):
    email: Optional[str] = None

class LoginRequest(SQLModel):
    email: str
    password: str 