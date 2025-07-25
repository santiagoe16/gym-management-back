from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from app.core.database import get_session
from app.core.deps import require_admin, require_trainer_or_admin
from app.models.user import User, UserRole
from app.models.attendance import Attendance, AttendanceCreate, AttendanceUpdate
from datetime import datetime, date, timezone
from app.models.read_models import AttendanceRead
from app.core.methods import check_gym, check_user_by_id, get_user_by_id

router = APIRouter()

@router.get("/", response_model=List[AttendanceRead])
def read_attendance(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    gym_id: Optional[int] = Query(None, description="Filter by gym ID"),
    attendance_date: Optional[date] = Query(None, description="Filter by attendance date"),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Get all attendance records - Admin and Trainer access only"""
    query = select(Attendance)
    
    # Filter by user if specified
    if user_id:
        query = query.where(Attendance.user_id == user_id)
    
    # Filter by date if specified
    if attendance_date:
        query = query.where(Attendance.attendance_date == attendance_date)
    
    # Filter by gym if specified
    if gym_id:
        query = query.join(User).where(User.gym_id == gym_id)
    
    # If trainer, only show attendance from their gym
    if current_user.role == UserRole.TRAINER:
        query = query.join(User).where(User.gym_id == current_user.gym_id)
    
    attendance_records = session.exec(query.offset(skip).limit(limit)).all()
    return attendance_records

@router.get("/user/{user_id}", response_model=List[AttendanceRead])
def read_user_attendance(
    user_id: int,
    start_date: Optional[date] = Query(None, description="Start date for attendance records"),
    end_date: Optional[date] = Query(None, description="End date for attendance records"),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Get attendance records for a specific user - Admin and Trainer access only"""
    check_gym( session, current_user.gym_id )

    # If trainer, only allow access to users in their gym
    if current_user.role == UserRole.TRAINER and user.gym_id != current_user.gym_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access users in your own gym"
        )
    
    user = get_user_by_id( session, user_id, current_user.gym_id )
    
    query = select( Attendance ).where( Attendance.user_id == user_id, Attendance.gym_id == current_user.gym_id )
    
    # Filter by date range if specified
    if start_date:
        query = query.where(Attendance.attendance_date >= start_date)
    if end_date:
        query = query.where(Attendance.attendance_date <= end_date)
    
    attendance_records = session.exec(query.order_by(Attendance.attendance_date.desc())).all()
    return attendance_records

@router.get("/user/{user_id}/summary")
def get_user_attendance_summary(
    user_id: int,
    start_date: Optional[date] = Query(None, description="Start date for summary"),
    end_date: Optional[date] = Query(None, description="End date for summary"),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Get attendance summary for a specific user - Admin and Trainer access only"""
    check_gym( session, current_user.gym_id )
    
    user = get_user_by_id( session, user_id, current_user.gym_id )

    # If trainer, only allow access to users in their gym
    if current_user.role == UserRole.TRAINER and user.gym_id != current_user.gym_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access users in your own gym"
        )
    
    query = select( Attendance ).where( Attendance.user_id == user_id, Attendance.gym_id == current_user.gym_id )
    
    # Filter by date range if specified
    if start_date:
        query = query.where(Attendance.attendance_date >= start_date)
    if end_date:
        query = query.where(Attendance.attendance_date <= end_date)
    
    attendance_records = session.exec(query).all()
    
    # Calculate summary
    total_visits = len(attendance_records)
    total_hours = 0
    
    for record in attendance_records:
        if record.check_out_time and record.check_in_time:
            duration = record.check_out_time - record.check_in_time
            total_hours += duration.total_seconds() / 3600
    
    return {
        "user_id": user_id,
        "user_name": user.full_name,
        "total_visits": total_visits,
        "total_hours": round(total_hours, 2),
        "average_session_hours": round(total_hours / total_visits, 2) if total_visits > 0 else 0,
        "period": {
            "start_date": start_date,
            "end_date": end_date
        }
    }

@router.get("/daily/{attendance_date}")
def get_daily_attendance(
    attendance_date: date,
    gym_id: Optional[int] = Query(None, description="Filter by gym ID"),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Get attendance records for a specific date - Admin and Trainer access only"""
    query = select(Attendance).where(Attendance.attendance_date == attendance_date)
    
    # Filter by gym if specified
    if gym_id:
        query = query.join(User).where(User.gym_id == gym_id)
    
    # If trainer, only show attendance from their gym
    if current_user.role == UserRole.TRAINER:
        query = query.join(User).where(User.gym_id == current_user.gym_id)
    
    attendance_records = session.exec(query).all()
    
    # Get user details for each attendance record
    result = []
    for record in attendance_records:
        user = session.exec(select(User).where(User.id == record.user_id)).first()
        result.append({
            "attendance_id": record.id,
            "user_id": record.user_id,
            "user_name": user.full_name if user else "Unknown",
            "check_in_time": record.check_in_time,
            "check_out_time": record.check_out_time,
            "notes": record.notes,
            "recorded_by": record.recorded_by_id
        })
    
    return {
        "date": attendance_date,
        "total_attendance": len(result),
        "records": result
    }

@router.post("/", response_model=AttendanceRead)
def create_attendance(
    attendance: AttendanceCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Create a new attendance record - Admin and Trainer access only"""
    # Get the user
    user = session.exec(select(User).where(User.id == attendance.user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # If trainer, only allow creating attendance for users in their gym
    if current_user.role == UserRole.TRAINER and user.gym_id != current_user.gym_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create attendance records for users in your own gym"
        )
    
    # Check if attendance record already exists for this user on this date
    existing_attendance = session.exec(
        select(Attendance).where(
            Attendance.user_id == attendance.user_id,
            Attendance.attendance_date == attendance.attendance_date
        )
    ).first()
    
    if existing_attendance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attendance record already exists for this user on this date"
        )
    
    # Create attendance record with all required fields
    attendance_data = attendance.model_dump()
    attendance_data.update({
        "recorded_by_id": current_user.id
    })
    
    db_attendance = Attendance.model_validate(attendance_data)
    
    session.add(db_attendance)
    session.commit()
    session.refresh(db_attendance)
    return db_attendance

@router.put("/{attendance_id}", response_model=AttendanceRead)
def update_attendance(
    attendance_id: int,
    attendance_update: AttendanceUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Update an attendance record - Admin and Trainer access only"""
    # Get the attendance record
    db_attendance = session.exec(select(Attendance).where(Attendance.id == attendance_id)).first()
    if not db_attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found"
        )
    
    # Get the user
    user = session.exec(select(User).where(User.id == db_attendance.user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # If trainer, only allow updating attendance for users in their gym
    if current_user.role == UserRole.TRAINER and user.gym_id != current_user.gym_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update attendance records for users in your own gym"
        )
    
    # Update attendance record
    update_data = attendance_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_attendance, field, value)
    
    db_attendance.updated_at = datetime.now(timezone.utc)
    session.add(db_attendance)
    session.commit()
    session.refresh(db_attendance)
    return db_attendance

@router.delete("/{attendance_id}")
def delete_attendance(
    attendance_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin)
):
    """Delete an attendance record - Admin access only"""
    # Get the attendance record
    db_attendance = session.exec(select(Attendance).where(Attendance.id == attendance_id)).first()
    if not db_attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found"
        )
    
    session.delete(db_attendance)
    session.commit()
    return {"message": "Attendance record deleted successfully"} 