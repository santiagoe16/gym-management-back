from enum import Enum
from sqlmodel import SQLModel
from typing import Optional
from app.models.user import UserBase

class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"
    user: UserBase

class TokenData(SQLModel):
    email: Optional[str] = None

class LoginRequest(SQLModel):
    email: str
    gym_id: int
    password: str 