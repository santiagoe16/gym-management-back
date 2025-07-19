from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

class PlanBase(SQLModel):
    name: str = Field(unique=True, index=True)
    price: Decimal = Field(description="Plan price")
    duration_days: int = Field(gt=0)  # Duration in days
    gym_id: int = Field(foreign_key="gyms.id", description="Gym where this plan is available")
    is_active: bool = True

class Plan(PlanBase, table=True):
    __tablename__ = "plans"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
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

class PlanRead(PlanBase):
    id: int
    created_at: datetime
    updated_at: datetime 