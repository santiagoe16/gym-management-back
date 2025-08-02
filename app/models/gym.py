from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime, timezone

class GymBase(SQLModel):
    name: str = Field(unique=True, index=True)
    address: str
    is_active: bool = True

class Gym(GymBase, table=True):
    __tablename__ = "gyms"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships
    users: List["User"] = Relationship(back_populates="gym")
    plans: List["Plan"] = Relationship(back_populates="gym")
    products: List["Product"] = Relationship(back_populates="gym")
    sales: List["Sale"] = Relationship(back_populates="gym")
    attendance: List["Attendance"] = Relationship(back_populates="gym")

class GymCreate(GymBase):
    pass

class GymUpdate(SQLModel):
    name: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None
