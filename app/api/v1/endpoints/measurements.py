from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func
from sqlalchemy.orm import selectinload
from app.core.database import get_session
from app.core.deps import require_trainer_or_admin
from app.core.methods import check_gym, check_trainer_gym, check_user_by_id
from app.models.measurement import Measurement, MeasurementCreate, MeasurementUpdate
from app.models.user import User, UserRole
from datetime import date
from app.models.read_models import MeasurementRead

router = APIRouter()

trainer_message = "You can only view measurements for users in your gym"

@router.get("/", response_model=List[MeasurementRead])
def read_measurements(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    start_date: Optional[date] = Query(None, description="Filter measurements from this date"),
    end_date: Optional[date] = Query(None, description="Filter measurements until this date"),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Get all measurements - Admin and Trainer access only"""
    query = select( Measurement ).options( selectinload( Measurement.user ), selectinload( Measurement.recorded_by ) )
    
    # Apply filters
    if user_id:
        query = query.where(Measurement.user_id == user_id)
    if start_date:
        query = query.where(func.date(Measurement.measurement_date) >= start_date)
    if end_date:
        query = query.where(func.date(Measurement.measurement_date) <= end_date)
    
    measurements = session.exec(query.offset(skip).limit(limit)).all()
    
    return measurements

@router.get("/user/{user_id}", response_model=List[MeasurementRead])
def read_user_measurements(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Get all measurements for a specific user - Admin and Trainer access only"""
    check_user_by_id( session, user_id )
    
    measurements = session.exec(
        select(Measurement).options(selectinload(Measurement.user), selectinload(Measurement.recorded_by))
        .where(Measurement.user_id == user_id)
        .order_by(Measurement.measurement_date.desc())
        .offset(skip)
        .limit(limit)
    ).all()
    
    return measurements

@router.get("/user/{user_id}/latest", response_model=MeasurementRead)
def get_latest_measurement(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Get the latest measurement for a specific user - Admin and Trainer access only"""
    check_user_by_id( session, user_id )
    
    measurement = session.exec(
        select(Measurement).options(selectinload(Measurement.user), selectinload(Measurement.recorded_by))
        .where(Measurement.user_id == user_id)
        .order_by(Measurement.measurement_date.desc())
    ).first()
    
    if not measurement:
        raise HTTPException(status_code=404, detail="No measurements found for this user")
    
    return measurement

@router.get("/user/{user_id}/progress")
def get_user_progress(
    user_id: int,
    start_date: Optional[date] = Query(None, description="Start date for progress calculation"),
    end_date: Optional[date] = Query(None, description="End date for progress calculation"),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Get progress summary for a specific user - Admin and Trainer access only"""
    check_user_by_id( session, user_id )
    
    query = select(Measurement).options(selectinload(Measurement.user), selectinload(Measurement.recorded_by)).where(Measurement.user_id == user_id)
    
    if start_date:
        query = query.where(func.date(Measurement.measurement_date) >= start_date)
    if end_date:
        query = query.where(func.date(Measurement.measurement_date) <= end_date)
    
    measurements = session.exec(query.order_by(Measurement.measurement_date)).all()
    
    if len(measurements) < 2:
        return {
            "message": "Need at least 2 measurements to calculate progress",
            "measurements_count": len(measurements)
        }
    
    # Calculate progress
    first_measurement = measurements[0]
    last_measurement = measurements[-1]
    
    progress = {}
    
    # Weight progress
    if first_measurement.weight and last_measurement.weight:
        progress["weight"] = {
            "start": float(first_measurement.weight),
            "current": float(last_measurement.weight),
            "change": float(last_measurement.weight - first_measurement.weight),
            "change_percentage": float(((last_measurement.weight - first_measurement.weight) / first_measurement.weight) * 100)
        }
    
    # Circumference measurements progress
    circumference_fields = [
        "chest", "shoulders", "biceps_left", "biceps_right", "forearms_left", "forearms_right",
        "abdomen", "hips", "thighs_left", "thighs_right", "calves_left", "calves_right"
    ]
    
    for field in circumference_fields:
        first_val = getattr(first_measurement, field)
        last_val = getattr(last_measurement, field)
        if first_val and last_val:
            progress[field] = {
                "start": float(first_val),
                "current": float(last_val),
                "change": float(last_val - first_val),
                "change_percentage": float(((last_val - first_val) / first_val) * 100)
            }
    
    return {
        "user_id": user_id,
        "user_name": measurements[0].user.full_name,
        "period": {
            "start_date": first_measurement.measurement_date.isoformat(),
            "end_date": last_measurement.measurement_date.isoformat(),
            "days": (last_measurement.measurement_date - first_measurement.measurement_date).days
        },
        "measurements_count": len(measurements),
        "progress": progress
    }

@router.post("/", response_model=MeasurementRead)
def create_measurement(
    measurement: MeasurementCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Create a new measurement - Admin and Trainer access only"""
    check_user_by_id( session, measurement.user_id )

    measurement.recorded_by_id = current_user.id
    
    db_measurement = Measurement.model_validate(measurement)
    
    session.add(db_measurement)
    session.commit()
    session.refresh(db_measurement)
    return db_measurement

@router.get("/{measurement_id}", response_model=MeasurementRead)
def read_measurement(
    measurement_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Get a specific measurement - Admin and Trainer access only"""
    measurement = session.exec(select(Measurement).options(selectinload(Measurement.user), selectinload(Measurement.recorded_by)).where(Measurement.id == measurement_id)).first()
    if measurement is None:
        raise HTTPException(status_code=404, detail="Measurement not found")
    
    return measurement

@router.put("/{measurement_id}", response_model=MeasurementRead)
def update_measurement(
    measurement_id: int,
    measurement_update: MeasurementUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Update a measurement - Admin and Trainer access only"""
    measurement = session.exec(select(Measurement).where(Measurement.id == measurement_id)).first()
    if measurement is None:
        raise HTTPException(status_code=404, detail="Measurement not found")
    
    # Update measurement data
    measurement_data = measurement_update.model_dump(exclude_unset=True)
    for key, value in measurement_data.items():
        setattr(measurement, key, value)
    
    session.add(measurement)
    session.commit()
    session.refresh(measurement)
    return measurement

@router.delete("/{measurement_id}")
def delete_measurement(
    measurement_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Delete a measurement - Admin and Trainer access only"""
    measurement = session.exec(select(Measurement).where(Measurement.id == measurement_id)).first()
    if measurement is None:
        raise HTTPException(status_code=404, detail="Measurement not found")
    
    session.delete(measurement)
    session.commit()
    
    return {"message": "Measurement deleted successfully"} 