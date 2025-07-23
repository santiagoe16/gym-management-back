from enum import Enum
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, Annotated
from datetime import datetime, timezone

from app.models.gym import GymRead
from app.models.user_plan import UserPlanRead

class UserRole(str, Enum):
    ADMIN = "admin"
    TRAINER = "trainer"
    USER = "user"

class UserBase(SQLModel):
    email: str = Field(unique=True, index=True)
    full_name: str
    document_id: str = Field(unique=True, index=True, description="Document ID number for user identification")
    phone_number: str = Field(description="User's phone number")
    gym_id: int = Field(foreign_key="gyms.id", description="Gym where the user belongs")
    role: UserRole = UserRole.USER
    is_active: bool = True

class User(UserBase, table=True):
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: Optional[str] = None  # Only for admin and trainer users
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships
    gym: "Gym" = Relationship(back_populates="users")
    user_plans: List["UserPlan"] = Relationship(back_populates="user", sa_relationship_kwargs={"foreign_keys": "[UserPlan.user_id]", "order_by": "[UserPlan.purchased_at]"})
    created_user_plans: List["UserPlan"] = Relationship(back_populates="created_by", sa_relationship_kwargs={"foreign_keys": "[UserPlan.created_by_id]"})
    sales: List["Sale"] = Relationship(back_populates="sold_by")
    measurements: List["Measurement"] = Relationship(back_populates="user", sa_relationship_kwargs={"foreign_keys": "[Measurement.user_id]"})
    recorded_measurements: List["Measurement"] = Relationship(back_populates="recorded_by", sa_relationship_kwargs={"foreign_keys": "[Measurement.recorded_by_id]"})
    attendance_records: List["Attendance"] = Relationship(back_populates="user", sa_relationship_kwargs={"foreign_keys": "[Attendance.user_id]"})
    recorded_attendance: List["Attendance"] = Relationship(back_populates="recorded_by", sa_relationship_kwargs={"foreign_keys": "[Attendance.recorded_by_id]"})

# Schema for creating admin/trainer users (need password)
class UserCreateWithPassword(UserBase):
    password: str

# Schema for creating regular users (no password needed)
class UserCreateWithoutPassword(UserBase):
    pass

class UserCreateWithPlan(UserCreateWithoutPassword):
    plan_id: int
    purchased_price: Optional[float] = None  # If not provided, will use plan's base_price

class UserUpdate(SQLModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    document_id: Optional[str] = None
    phone_number: Optional[str] = None
    gym_id: Optional[int] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class UserRead(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    gym: Optional["GymRead"] = Field(default=None)
    active_plan: Optional["UserPlanRead"] = Field(default=None)


class UserReadWithPlans(UserRead):
    user_plans: List["UserPlanRead"] = Field(default=[])
    pass 