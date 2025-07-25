from datetime import datetime
from typing import Optional
from sqlmodel import Field

from app.models.attendance import AttendanceBase
from app.models.gym import GymBase
from app.models.user_plan import UserPlanBase
from app.models.user import UserBase
from app.models.plan import PlanBase
from app.models.sale import SaleBase
from app.models.product import ProductBase
from app.models.measurement import MeasurementBase

class AttendanceRead(AttendanceBase):
    id: int
    created_at: datetime
    updated_at: datetime 

class GymRead(GymBase):
    id: int
    created_at: datetime
    updated_at: datetime

class PlanRead(PlanBase):
    id: int
    created_at: datetime
    updated_at: datetime
    gym: Optional["GymRead"] = Field(default=None)

class UserPlanRead(UserPlanBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime 
    plan: Optional[ "PlanRead" ] = Field( default = None )
    created_by_user: Optional["UserBase"] = Field(default=None)
    user: Optional["UserRead"] = Field(default=None)
    
class UserRead(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    gym: Optional["GymRead"] = Field(default=None)
    active_plan: Optional["UserPlanRead"] = Field(default=None)

class SaleRead(SaleBase):
    id: int
    created_at: datetime
    updated_at: datetime
    product: Optional["ProductRead"] = Field(default=None)
    gym: Optional["GymRead"] = Field(default=None)
    sold_by: Optional["UserRead"] = Field(default=None)
    
class ProductRead(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime
    gym: Optional["GymRead"] = Field(default=None)
    
class MeasurementRead(MeasurementBase):
    id: int
    created_at: datetime
    updated_at: datetime
    user: Optional["UserRead"] = None
    recorded_by_user: Optional["UserRead"] = None 