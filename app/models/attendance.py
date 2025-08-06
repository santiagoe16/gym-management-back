from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime, date, timezone

class AttendanceBase(SQLModel):
    user_id: int = Field(foreign_key="users.id", description="User who attended")
    gym_id: int = Field(foreign_key="gyms.id", description="Gym where the attendance was recorded")
    check_in_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Time when user checked in")
    recorded_by_id: int = Field(foreign_key="users.id", description="Admin/Trainer who recorded the attendance")
    notes: Optional[str] = Field(default=None, description="Additional notes about the attendance")

class Attendance(AttendanceBase, table=True):
    __tablename__ = "attendance"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user: "User" = Relationship(back_populates="attendance_records", sa_relationship_kwargs={"foreign_keys": "[Attendance.user_id]"})
    recorded_by: "User" = Relationship(back_populates="recorded_attendance", sa_relationship_kwargs={"foreign_keys": "[Attendance.recorded_by_id]"})
    gym: "Gym" = Relationship(back_populates="attendance", sa_relationship_kwargs={"foreign_keys": "[Attendance.gym_id]"})

class AttendanceCreate(SQLModel):
    notes: Optional[str] = None

class AttendanceUpdate(SQLModel):
    notes: Optional[str] = None
