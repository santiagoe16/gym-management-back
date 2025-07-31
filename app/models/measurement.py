from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime, timezone
from decimal import Decimal
from pydantic import field_serializer

class MeasurementBase(SQLModel):
    user_id: int = Field(foreign_key="users.id", description="User whose measurements are being recorded")
    
    # Body measurements (in cm)
    height: Optional[Decimal] = Field(None, description="Height in cm")
    weight: Optional[Decimal] = Field(None, description="Weight in kg")
    
    # Upper body measurements
    chest: Optional[Decimal] = Field(None, description="Chest circumference in cm")
    shoulders: Optional[Decimal] = Field(None, description="Shoulder width in cm")
    biceps_left: Optional[Decimal] = Field(None, description="Left biceps circumference in cm")
    biceps_right: Optional[Decimal] = Field(None, description="Right biceps circumference in cm")
    forearms_left: Optional[Decimal] = Field(None, description="Left forearm circumference in cm")
    forearms_right: Optional[Decimal] = Field(None, description="Right forearm circumference in cm")
    
    # Core measurements
    abdomen: Optional[Decimal] = Field(None, description="Abdomen/waist circumference in cm")
    hips: Optional[Decimal] = Field(None, description="Hip circumference in cm")
    
    # Lower body measurements
    thighs_left: Optional[Decimal] = Field(None, description="Left thigh circumference in cm")
    thighs_right: Optional[Decimal] = Field(None, description="Right thigh circumference in cm")
    calves_left: Optional[Decimal] = Field(None, description="Left calf circumference in cm")
    calves_right: Optional[Decimal] = Field(None, description="Right calf circumference in cm")
    
    # Additional notes
    notes: Optional[str] = Field(None, description="Additional notes about the measurements")
    measurement_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Date when measurements were taken")

    # Custom serializers for Decimal fields
    @field_serializer('height', 'weight', 'chest', 'shoulders', 'biceps_left', 'biceps_right', 
                     'forearms_left', 'forearms_right', 'abdomen', 'hips', 'thighs_left', 
                     'thighs_right', 'calves_left', 'calves_right')
    def serialize_decimal(self, value: Optional[Decimal]) -> Optional[float]:
        if value is not None:
            return float(value)
        return None

class Measurement(MeasurementBase, table=True):
    __tablename__ = "measurements"
    
    recorded_by_id: int = Field(foreign_key="users.id", description="Admin or trainer who recorded the measurements")
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user: "User" = Relationship(back_populates="measurements", sa_relationship_kwargs={"foreign_keys": "[Measurement.user_id]"})
    recorded_by: "User" = Relationship(back_populates="recorded_measurements", sa_relationship_kwargs={"foreign_keys": "[Measurement.recorded_by_id]"})

class MeasurementCreate(MeasurementBase):
    recorded_by_id: Optional[int] = None

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

    # Custom serializers for Decimal fields
    @field_serializer('height', 'weight', 'chest', 'shoulders', 'biceps_left', 'biceps_right', 
                     'forearms_left', 'forearms_right', 'abdomen', 'hips', 'thighs_left', 
                     'thighs_right', 'calves_left', 'calves_right')
    def serialize_decimal(self, value: Optional[Decimal]) -> Optional[float]:
        if value is not None:
            return float(value)
        return None
