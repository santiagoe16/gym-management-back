from datetime import datetime
from typing import Optional, TYPE_CHECKING, Union
from sqlmodel import Field

from app.models.attendance import AttendanceBase
from app.models.gym import GymBase
from app.models.user_plan import UserPlanBase
from app.models.user import UserBase
from app.models.plan import PlanBase, PlanRole
from app.models.sale import SaleBase
from app.models.product import ProductBase
from app.models.measurement import MeasurementBase

if TYPE_CHECKING:
    from app.models.read_models import UserRead, PlanRead, GymRead, UserPlanRead, ProductRead

class GymRead(GymBase):
    id: int
    created_at: datetime
    updated_at: datetime

class PlanRead(PlanBase):
    id: int
    created_at: datetime
    updated_at: datetime
    gym: Union["GymRead", None] = Field(default=None)
    role: PlanRole = PlanRole.REGULAR
    days: Optional[int] = None

class ProductRead(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime
    gym: Union["GymRead", None] = Field(default=None)

class UserRead(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    gym: Union["GymRead", None] = Field(default=None)
    active_plan: Union["UserPlanRead", None] = Field(default=None)
    schedule_start: Optional[str] = None
    schedule_end: Optional[str] = None

class AttendanceRead(AttendanceBase):
    id: int
    created_at: datetime
    updated_at: datetime
    user: Union["UserRead", None] = Field(default=None)
    recorded_by: Union["UserBase", None] = Field(default=None)
    gym: Union["GymRead", None] = Field(default=None)

class UserPlanRead(UserPlanBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    duration_days: int
    plan: Union["PlanRead", None] = Field(default=None)
    created_by: Union["UserBase", None] = Field(default=None)
    user: Union["UserRead", None] = Field(default=None)

class SaleRead(SaleBase):
    id: int
    created_at: datetime
    updated_at: datetime
    product: Union["ProductRead", None] = Field(default=None)
    gym: Union["GymRead", None] = Field(default=None)
    sold_by: Union["UserRead", None] = Field(default=None)
    
class MeasurementRead(MeasurementBase):
    id: int
    created_at: datetime
    updated_at: datetime
    user: Union["UserRead", None] = None
    recorded_by: Union["UserRead", None] = None 