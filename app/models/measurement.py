from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime
from decimal import Decimal

class MeasurementBase(SQLModel):
    user_id: int = Field(foreign_key="users.id", description="User whose measurements are being recorded")
    recorded_by_id: int = Field(foreign_key="users.id", description="Admin or trainer who recorded the measurements")
    
    # Body measurements (in cm)
    height: Optional[Decimal] = Field(None, max_digits=5, decimal_places=2, description="Height in cm")
    weight: Optional[Decimal] = Field(None, max_digits=5, decimal_places=2, description="Weight in kg")
    
    # Upper body measurements
    chest: Optional[Decimal] = Field(None, max_digits=5, decimal_places=2, description="Chest circumference in cm")
    shoulders: Optional[Decimal] = Field(None, max_digits=5, decimal_places=2, description="Shoulder width in cm")
    biceps_left: Optional[Decimal] = Field(None, max_digits=5, decimal_places=2, description="Left biceps circumference in cm")
    biceps_right: Optional[Decimal] = Field(None, max_digits=5, decimal_places=2, description="Right biceps circumference in cm")
    forearms_left: Optional[Decimal] = Field(None, max_digits=5, decimal_places=2, description="Left forearm circumference in cm")
    forearms_right: Optional[Decimal] = Field(None, max_digits=5, decimal_places=2, description="Right forearm circumference in cm")
    
    # Core measurements
    abdomen: Optional[Decimal] = Field(None, max_digits=5, decimal_places=2, description="Abdomen/waist circumference in cm")
    hips: Optional[Decimal] = Field(None, max_digits=5, decimal_places=2, description="Hip circumference in cm")
    
    # Lower body measurements
    thighs_left: Optional[Decimal] = Field(None, max_digits=5, decimal_places=2, description="Left thigh circumference in cm")
    thighs_right: Optional[Decimal] = Field(None, max_digits=5, decimal_places=2, description="Right thigh circumference in cm")
    calves_left: Optional[Decimal] = Field(None, max_digits=5, decimal_places=2, description="Left calf circumference in cm")
    calves_right: Optional[Decimal] = Field(None, max_digits=5, decimal_places=2, description="Right calf circumference in cm")
    
    # Additional notes
    notes: Optional[str] = Field(None, description="Additional notes about the measurements")
    measurement_date: datetime = Field(default_factory=datetime.utcnow, description="Date when measurements were taken")

class Measurement(MeasurementBase, table=True):
    __tablename__ = "measurements"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user: "User" = Relationship(back_populates="measurements")
    recorded_by: "User" = Relationship(back_populates="recorded_measurements")

class MeasurementCreate(MeasurementBase):
    pass

class MeasurementUpdate(SQLModel):
    height: Optional[Decimal] = None
    weight: Optional[Decimal] = None
    chest: Optional[Decimal] = None
    shoulders: Optional[Decimal] = None
    biceps_left: Optional[Decimal] = None
    biceps_right: Optional[Decimal] = None
    forearms_left: Optional[Decimal] = None
    forearms_right: Optional[Decimal] = None
    abdomen: Optional[Decimal] = None
    hips: Optional[Decimal] = None
    thighs_left: Optional[Decimal] = None
    thighs_right: Optional[Decimal] = None
    calves_left: Optional[Decimal] = None
    calves_right: Optional[Decimal] = None
    notes: Optional[str] = None
    measurement_date: Optional[datetime] = None

class MeasurementRead(MeasurementBase):
    id: int
    created_at: datetime
    updated_at: datetime

class MeasurementReadWithUser(MeasurementRead):
    user_name: Optional[str] = None
    recorded_by_name: Optional[str] = None 