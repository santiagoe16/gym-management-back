from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from sqlalchemy.orm import joinedload
from sqlalchemy import func
from app.core.database import get_session
from app.core.deps import require_admin, require_trainer_or_admin
from app.models.user import User, UserRole
from app.models.attendance import Attendance, AttendanceCreate, AttendanceUpdate
from app.models.user_plan import UserPlan
from app.models.plan import PlanRole
from datetime import datetime, date
from app.models.read_models import AttendanceRead
from app.core.methods import check_gym, check_user_by_id, get_last_plan
from datetime import datetime, timezone

import pytz

router = APIRouter()

@router.get("/", response_model = List[ AttendanceRead ] )
def read_attendance(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    gym_id: Optional[int] = Query(None, description="Filter by gym ID"),
    trainer_id: Optional[int] = Query(None, description="Filter by trainer ID"),
    start_date: Optional[date] = Query(None, description="Start date for summary"),
    end_date: Optional[date] = Query(None, description="End date for summary"),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Get all attendance records - Admin and Trainer access only"""
    query = select( Attendance ).options( joinedload( Attendance.user ), joinedload( Attendance.recorded_by ), joinedload( Attendance.gym ) )
    
    if user_id:
        query = query.where( Attendance.user_id == user_id )
    
    if gym_id:
        query = query.where( Attendance.gym_id == gym_id )
    
    if current_user.role == UserRole.TRAINER:
        query = query.where( Attendance.gym_id == current_user.gym_id )
    
    if trainer_id:
        query = query.where( Attendance.recorded_by_id == trainer_id )
    
    if start_date:
        query = query.where( func.date( Attendance.check_in_time ) >= start_date )
    
    if end_date:
        query = query.where( func.date( Attendance.check_in_time ) <= end_date )
    
    attendance_records = session.exec( query.offset( skip ).limit( limit ) ).all()

    result = []

    for record in attendance_records:
        attendance = AttendanceRead.model_validate( record )

        user = session.exec( select( User ).options( joinedload( User.user_plans ).selectinload( UserPlan.plan ) ).where( User.id == record.user_id ) ).first()
        
        if user.user_plans:
            current_time = attendance.check_in_time

            if current_time.tzinfo is None:
                current_time = current_time.replace( tzinfo = pytz.timezone( 'America/Bogota' ) )

            valid_plans = []
            
            for up in user.user_plans:
                if not up.is_active:
                    continue
                    
                expires_at = up.expires_at

                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace( tzinfo = pytz.timezone( 'America/Bogota' ) )
                
                if expires_at > current_time:
                    valid_plans.append( up )
            
            if valid_plans:
                attendance.user.active_plan = max( valid_plans, key = lambda up: up.purchased_at )

        result.append( attendance )

    return result

@router.get( "/user/{user_id}/summary" )
def get_user_attendance_summary(
    user_id: int,
    start_date: Optional[date] = Query(None, description="Start date for summary"),
    end_date: Optional[date] = Query(None, description="End date for summary"),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Get attendance summary for a specific user - Admin and Trainer access only"""
    check_gym( session, current_user.gym_id )
    
    user = check_user_by_id( session, user_id )
    active_plan = get_last_plan( user )

    query = select( Attendance ).options( 
        joinedload( Attendance.user ), 
        joinedload( Attendance.gym ), 
        joinedload( Attendance.recorded_by ) 
    ).where( Attendance.user_id == user_id, Attendance.gym_id == current_user.gym_id )
    
    # Filter by date range if specified
    if start_date:
        query = query.where(func.date(Attendance.check_in_time) >= start_date)
    if end_date:
        query = query.where(func.date(Attendance.check_in_time) <= end_date)
    
    attendance_records = session.exec(query).all()
    
    # Calculate summary
    total_visits = len(attendance_records)
    total_hours = 0
    
    for record in attendance_records:
        duration = record.check_in_time - record.check_in_time
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
        },
        "active_plan": active_plan
    }

@router.get("/daily/{attendance_date}", response_model=List[AttendanceRead])
def get_daily_attendance(
    attendance_date: date,
    trainer_id: Optional[int] = Query(None, description="Filter by trainer ID"),
    gym_id: Optional[int] = Query(None, description="Filter by gym ID"),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Get attendance records for a specific date - Admin and Trainer access only"""
    query = select( Attendance ).options( joinedload( Attendance.user ), joinedload( Attendance.gym ), joinedload( Attendance.recorded_by ) ).where( 
        func.date( Attendance.check_in_time ) == attendance_date
    )
    
    if trainer_id:
        query = query.where( Attendance.recorded_by_id == trainer_id )
    
    if gym_id:
        query = query.where( Attendance.gym_id == gym_id )
    
    if current_user.role == UserRole.TRAINER:
        query = query.where( Attendance.gym_id == current_user.gym_id )
    
    attendance_records = session.exec( query ).all()
    
    result = []

    for record in attendance_records:
        attendance = AttendanceRead.model_validate( record )

        user = session.exec( select( User ).options( joinedload( User.user_plans ).selectinload( UserPlan.plan ) ).where( User.id == record.user_id ) ).first()

        attendance.user.active_plan = get_last_plan( user )

        result.append( attendance )

    return result

@router.post("/{document_id}", response_model=AttendanceRead)
def create_attendance(
    document_id: str,
    attendance: AttendanceCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Create a new attendance record - Admin and Trainer access only"""
    # Get the user
    user = session.exec( 
        select( User ).options( joinedload( User.user_plans ).selectinload( UserPlan.plan ) ).where( User.document_id == document_id )
    ).first()

    if not user:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Usuario no encontrado"
        )
    
    today = datetime.now(pytz.timezone('America/Bogota')).date()
    
    existing_attendance = session.exec(
        select(Attendance).where(
            Attendance.user_id == user.id,
            func.date(Attendance.check_in_time) == today
        )
    ).first()
    
    if existing_attendance:
        result = AttendanceRead.model_validate( existing_attendance )

        result.user.active_plan = get_last_plan( user )

        return result

    
    active_plan = get_last_plan(user)
    
    if not active_plan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario no tiene un plan activo válido"
        )
    
    if active_plan.plan.role == PlanRole.TAQUILLERO:
        if active_plan.days == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El plan taquillero del usuario se quedó sin días"
            )
        
        for user_plan in user.user_plans:
            if user_plan.id == active_plan.id:
                user_plan.days -= 1

                session.add(user_plan)
                session.commit()
                session.refresh(user_plan)

                break

    else:
        # Ensure expires_at is timezone-aware for comparison
        expires_at = active_plan.expires_at

        if expires_at.tzinfo is None:
            expires_at = expires_at.replace( tzinfo = pytz.timezone('America/Bogota') )
        
        if expires_at.date() <= today:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El plan del usuario ha expirado"
            )
       
    # Create attendance record with all required fields
    attendance_data = attendance.model_dump()
    attendance_data.update({
        "recorded_by_id": current_user.id,
        "gym_id": current_user.gym_id,
        "user_id": user.id
    })
    
    db_attendance = Attendance.model_validate(attendance_data)
    
    session.add(db_attendance)
    session.commit()
    session.refresh(db_attendance)

    result = AttendanceRead.model_validate( db_attendance )

    result.user.active_plan = active_plan

    return result

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
            detail="Registro de asistencia no encontrado"
        )
    
    # If trainer, only allow updating attendance for users in their gym
    if current_user.role == UserRole.TRAINER and db_attendance.gym_id != current_user.gym_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo puedes actualizar registros de asistencia de usuarios en tu propio gimnasio"
        )
    
    # Update attendance record
    update_data = attendance_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_attendance, field, value)
    
    db_attendance.updated_at = datetime.now(pytz.timezone('America/Bogota'))
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
            detail="Registro de asistencia no encontrado"
        )
    
    session.delete(db_attendance)
    session.commit()
    return {"message": "Registro de asistencia eliminado exitosamente"} 