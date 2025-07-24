from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select, func
from app.core.database import get_session
from app.core.deps import require_trainer_or_admin
from app.models.measurement import Measurement, MeasurementCreate, MeasurementUpdate
from app.models.user import User, UserRole
from datetime import date
from app.models.read_models import MeasurementRead

router = APIRouter()

@router.get("/", response_model=List[MeasurementRead])
def read_measurements(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    gym_id: Optional[int] = Query(None, description="Filter by gym ID"),
    start_date: Optional[date] = Query(None, description="Filter measurements from this date"),
    end_date: Optional[date] = Query(None, description="Filter measurements until this date"),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Get all measurements - Admin and Trainer access only"""
    query = select(Measurement)
    
    # Apply filters
    if user_id:
        query = query.where(Measurement.user_id == user_id)
    if start_date:
        query = query.where(func.date(Measurement.measurement_date) >= start_date)
    if end_date:
        query = query.where(func.date(Measurement.measurement_date) <= end_date)
    
    # If trainer, only show measurements from their gym
    if current_user.role == UserRole.TRAINER:
        query = query.join(User, Measurement.user_id == User.id).where(User.gym_id == current_user.gym_id)
    
    # If gym_id filter is specified, apply it
    if gym_id:
        query = query.join(User, Measurement.user_id == User.id).where(User.gym_id == gym_id)
    
    measurements = session.exec(query.offset(skip).limit(limit)).all()
    
    # Add user and recorded_by names
    result = []
    for measurement in measurements:
        measurement_dict = measurement.model_dump()
        measurement_dict["user_name"] = measurement.user.full_name if measurement.user else None
        measurement_dict["recorded_by_name"] = measurement.recorded_by.full_name if measurement.recorded_by else None
        result.append(MeasurementRead(**measurement_dict))
    
    return result

@router.get("/user/{user_id}", response_model=List[MeasurementRead])
def read_user_measurements(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Get all measurements for a specific user - Admin and Trainer access only"""
    # Verify user exists
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # If trainer, only allow access to users in their gym
    if current_user.role == UserRole.TRAINER and user.gym_id != current_user.gym_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view measurements for users in your gym"
        )
    
    measurements = session.exec(
        select(Measurement)
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
    # Verify user exists
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # If trainer, only allow access to users in their gym
    if current_user.role == UserRole.TRAINER and user.gym_id != current_user.gym_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view measurements for users in your gym"
        )
    
    measurement = session.exec(
        select(Measurement)
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
    # Verify user exists
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # If trainer, only allow access to users in their gym
    if current_user.role == UserRole.TRAINER and user.gym_id != current_user.gym_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view measurements for users in your gym"
        )
    
    query = select(Measurement).where(Measurement.user_id == user_id)
    
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
        "user_name": user.full_name,
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
    # Verify user exists
    user = session.exec(select(User).where(User.id == measurement.user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # If trainer, only allow creating measurements for users in their gym
    if current_user.role == UserRole.TRAINER and user.gym_id != current_user.gym_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create measurements for users in your gym"
        )
    
    # Create new measurement
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
    measurement = session.exec(select(Measurement).where(Measurement.id == measurement_id)).first()
    if measurement is None:
        raise HTTPException(status_code=404, detail="Measurement not found")
    
    # If trainer, only allow access to measurements from their gym
    if current_user.role == UserRole.TRAINER:
        user = session.exec(select(User).where(User.id == measurement.user_id)).first()
        if user and user.gym_id != current_user.gym_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view measurements for users in your gym"
            )
    
    return measurement

@router.put("/{measurement_id}", response_model=MeasurementRead)
def update_measurement(
    measurement_id: int,
    measurement_update: MeasurementUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Update a measurement - Admin and Trainer access only"""
    db_measurement = session.exec(select(Measurement).where(Measurement.id == measurement_id)).first()
    if db_measurement is None:
        raise HTTPException(status_code=404, detail="Measurement not found")
    
    # If trainer, only allow updating measurements from their gym
    if current_user.role == UserRole.TRAINER:
        user = session.exec(select(User).where(User.id == db_measurement.user_id)).first()
        if user and user.gym_id != current_user.gym_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update measurements for users in your gym"
            )
    
    # Update measurement data
    measurement_data = measurement_update.dict(exclude_unset=True)
    for key, value in measurement_data.items():
        setattr(db_measurement, key, value)
    
    session.add(db_measurement)
    session.commit()
    session.refresh(db_measurement)
    return db_measurement

@router.delete("/{measurement_id}")
def delete_measurement(
    measurement_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_trainer_or_admin)
):
    """Delete a measurement - Admin and Trainer access only"""
    db_measurement = session.exec(select(Measurement).where(Measurement.id == measurement_id)).first()
    if db_measurement is None:
        raise HTTPException(status_code=404, detail="Measurement not found")
    
    # If trainer, only allow deleting measurements from their gym
    if current_user.role == UserRole.TRAINER:
        user = session.exec(select(User).where(User.id == db_measurement.user_id)).first()
        if user and user.gym_id != current_user.gym_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete measurements for users in your gym"
            )
    
    session.delete(db_measurement)
    session.commit()
    return {"message": "Measurement deleted successfully"} 