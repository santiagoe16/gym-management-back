from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime, timezone
from decimal import Decimal

from app.models.auth import PaymentType

class UserPlanBase(SQLModel):
    user_id: int = Field(foreign_key="users.id")
    plan_id: int = Field(foreign_key="plans.id")
    purchased_price: Decimal = Field(description="Price paid for this plan")
    purchased_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime
    created_by_id: int = Field(foreign_key="users.id")  # Admin or Trainer who created this
    payment_type: PaymentType = Field(default=PaymentType.CASH)

class UserPlan(UserPlanBase, table=True):
    __tablename__ = "user_plans"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user: Optional["User"] = Relationship(back_populates="user_plans", sa_relationship_kwargs={"foreign_keys": "[UserPlan.user_id]"})
    plan: Optional["Plan"] = Relationship(back_populates="user_plans")
    created_by: Optional["User"] = Relationship(back_populates="created_user_plans", sa_relationship_kwargs={"foreign_keys": "[UserPlan.created_by_id]"})

class UserPlanCreate(SQLModel):
    user_id: int
    plan_id: int
    purchased_price: Decimal
    expires_at: datetime

class UserPlanUpdate(SQLModel):
    plan_id: Optional[int] = None
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None
