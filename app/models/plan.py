from enum import Enum
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from app.models.enums import PlanRole
import pytz

class PlanBase(SQLModel):
    name: str = Field(unique=True, index=True)
    price: Decimal = Field(description="Plan price")
    duration_days: int = Field(gt=0)  # Duration in days
    gym_id: int = Field(foreign_key="gyms.id", description="Gym where this plan is available")
    role: PlanRole = PlanRole.REGULAR
    is_active: bool = True

class Plan(PlanBase, table=True):
    __tablename__ = "plans"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(pytz.timezone('America/Bogota')))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(pytz.timezone('America/Bogota')))
    
    # Relationships
    gym: "Gym" = Relationship(back_populates="plans")
    user_plans: List["UserPlan"] = Relationship(back_populates="plan")

class PlanCreate(PlanBase):
    pass

class PlanUpdate(SQLModel):
    name: Optional[str] = None
    price: Optional[Decimal] = None
    duration_days: Optional[int] = None
    gym_id: Optional[int] = None
    is_active: Optional[bool] = None
    