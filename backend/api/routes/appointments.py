"""
Appointment Management API Routes
File: backend/api/routes/appointments.py
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from datetime import date, datetime

from backend.config.database import get_db
from backend.models.database import (
    Appointment, Patient, Treatment, User, AppointmentStatus
)
from backend.auth.security import get_current_user


router = APIRouter(prefix="/appointments", tags=["Appointment Management"])


# Pydantic schemas for appointments
from pydantic import BaseModel

class AppointmentCreate(BaseModel):
    patient_id: int
    appointment_date: date
    time_slot: str  # M or E
    treatment_id: Optional[int] = None
    assigned_therapist: Optional[int] = None
    assigned_doctor: Optional[int] = None
    notes: Optional[str] = None

class AppointmentUpdate(BaseModel):
    appointment_date: Optional[date] = None
    time_slot: Optional[str] = None
    treatment_id: Optional[int] = None
    assigned_therapist: Optional[int] = None
    assigned_doctor: Optional[int] = None
    status: Optional[AppointmentStatus] = None
    notes: Optional[str] = None

class AppointmentResponse(BaseModel):
    appointment_id: int
    patient_id: int
    appointment_date: date
    time_slot: str
    treatment_id: Optional[int]
    assigned_therapist: Optional[int]
    assigned_doctor: Optional[int]
    status: AppointmentStatus
    notes: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


@router.post("/", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    appointment_data: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new appointment.
    
    **Request Body:**
    ```json
    {
        "patient_id": 1,
        "appointment_date": "2024-11-15",
        "time_slot": "M",
        "treatment_id": 1,
        "assigned_doctor": 2,
        "assigned_therapist": 5,
        "notes": "Regular checkup"
    }
    ```
    """
    # Verify patient exists
    patient = db.query(Patient).filter(
        Patient.patient_id == appointment_data.patient_id
    ).first()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID {appointment_data.patient_id} not found"
        )
    
    # Verify treatment if provided
    if appointment_data.treatment_id:
        treatment = db.query(Treatment).filter(
            Treatment.treatment_id == appointment_data.treatment_id
        ).first()
        
        if not treatment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Treatment with ID {appointment_data.treatment_id} not found"
            )
    
    # Check if slot is available
    existing = db.query(Appointment).filter(
        and_(
            Appointment.appointment_date == appointment_data.appointment_date,
            Appointment.time_slot == appointment_data.time_slot,
            Appointment.status.in_(['scheduled', 'confirmed', 'in_progress'])
        )
    ).count()
    
    # Allow max 10 appointments per slot
    if existing >= 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Time slot {appointment_data.time_slot} on {appointment_data.appointment_date} is full"
        )
    
    # Create appointment
    new_appointment = Appointment(
        **appointment_data.dict(),
        status=AppointmentStatus.scheduled
    )
    
    db.add(new_appointment)
    db.commit()
    db.refresh(new_appointment)
    
    return AppointmentResponse.from_orm(new_appointment)


@router.get("/", response_model=List[AppointmentResponse])
async def get_all_appointments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    appointment_date: Optional[date] = Query(None, description="Filter by date"),
    patient_id: Optional[int] = Query(None, description="Filter by patient"),
    status: Optional[AppointmentStatus] = Query(None, description="Filter by status"),
    time_slot: Optional[str] = Query(None, description="Filter by time slot (M/E)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all appointments with filters.
    
    **Query Parameters:**
    - appointment_date: Filter by specific date
    - patient_id: Filter by patient
    - status: Filter by status
    - time_slot: Filter by time slot (M for morning, E for evening)
    
    **Example:**
    ```
    GET /api/v1/appointments/?appointment_date=2024-11-15&status=scheduled
    ```
    """
    query = db.query(Appointment)
    
    # Apply filters
    if appointment_date:
        query = query.filter(Appointment.appointment_date == appointment_date)
    
    if patient_id:
        query = query.filter(Appointment.patient_id == patient_id)
    
    if status:
        query = query.filter(Appointment.status == status)
    
    if time_slot:
        query = query.filter(Appointment.time_slot == time_slot)
    
    # Order by date and time slot
    query = query.order_by(
        Appointment.appointment_date.desc(),
        Appointment.time_slot
    )
    
    # Apply pagination
    appointments = query.offset(skip).limit(limit).all()
    
    return [AppointmentResponse.from_orm(apt) for apt in appointments]


@router.get("/today")
async def get_todays_appointments(
    time_slot: Optional[str] = Query(None, description="M or E"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get today's appointments with patient details.
    
    **Query Parameters:**
    - time_slot: Filter by time slot (optional)
    """
    query = db.query(
        Appointment,
        Patient.name,
        Patient.phone,
        Treatment.treatment_name
    ).join(
        Patient, Appointment.patient_id == Patient.patient_id
    ).outerjoin(
        Treatment, Appointment.treatment_id == Treatment.treatment_id
    ).filter(
        Appointment.appointment_date == date.today()
    )
    
    if time_slot:
        query = query.filter(Appointment.time_slot == time_slot)
    
    query = query.order_by(Appointment.time_slot)
    
    results = query.all()
    
    return [
        {
            "appointment_id": apt.appointment_id,
            "patient_id": apt.patient_id,
            "patient_name": patient_name,
            "patient_phone": patient_phone,
            "time_slot": apt.time_slot,
            "treatment_name": treatment_name,
            "status": apt.status,
            "notes": apt.notes
        }
        for apt, patient_name, patient_phone, treatment_name in results
    ]


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment_by_id(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get specific appointment by ID.
    
    **Path Parameters:**
    - appointment_id: Database ID of the appointment
    """
    appointment = db.query(Appointment).filter(
        Appointment.appointment_id == appointment_id
    ).first()
    
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Appointment with ID {appointment_id} not found"
        )
    
    return AppointmentResponse.from_orm(appointment)


@router.put("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: int,
    appointment_update: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update appointment details.
    
    **Path Parameters:**
    - appointment_id: Database ID of the appointment
    
    **Request Body (all fields optional):**
    ```json
    {
        "appointment_date": "2024-11-20",
        "time_slot": "E",
        "status": "confirmed",
        "notes": "Patient confirmed attendance"
    }
    ```
    """
    appointment = db.query(Appointment).filter(
        Appointment.appointment_id == appointment_id
    ).first()
    
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Appointment with ID {appointment_id} not found"
        )
    
    # Update fields
    update_data = appointment_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(appointment, field, value)
    
    db.commit()
    db.refresh(appointment)
    
    return AppointmentResponse.from_orm(appointment)


@router.put("/{appointment_id}/status/{new_status}")
async def update_appointment_status(
    appointment_id: int,
    new_status: AppointmentStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update appointment status.
    
    **Path Parameters:**
    - appointment_id: Database ID of the appointment
    - new_status: New status (scheduled, confirmed, in_progress, completed, cancelled, no_show)
    """
    appointment = db.query(Appointment).filter(
        Appointment.appointment_id == appointment_id
    ).first()
    
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Appointment with ID {appointment_id} not found"
        )
    
    old_status = appointment.status
    appointment.status = new_status
    
    db.commit()
    db.refresh(appointment)
    
    return {
        "message": f"Appointment status updated from {old_status} to {new_status}",
        "appointment": AppointmentResponse.from_orm(appointment)
    }


@router.delete("/{appointment_id}")
async def delete_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete an appointment.
    
    **Path Parameters:**
    - appointment_id: Database ID of the appointment
    """
    appointment = db.query(Appointment).filter(
        Appointment.appointment_id == appointment_id
    ).first()
    
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Appointment with ID {appointment_id} not found"
        )
    
    db.delete(appointment)
    db.commit()
    
    return {"message": f"Appointment {appointment_id} deleted successfully"}


@router.get("/stats/summary")
async def get_appointment_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get appointment statistics.
    
    **Returns:**
    - Today's appointments count
    - Upcoming appointments
    - Appointments by status
    - Monthly appointment trend
    """
    today = date.today()
    
    # Today's appointments
    todays_count = db.query(Appointment).filter(
        Appointment.appointment_date == today
    ).count()
    
    # Upcoming appointments (next 7 days)
    from datetime import timedelta
    upcoming_count = db.query(Appointment).filter(
        and_(
            Appointment.appointment_date > today,
            Appointment.appointment_date <= today + timedelta(days=7),
            Appointment.status.in_(['scheduled', 'confirmed'])
        )
    ).count()
    
    # By status
    status_counts = db.query(
        Appointment.status,
        func.count(Appointment.appointment_id).label('count')
    ).group_by(Appointment.status).all()
    
    return {
        "todays_appointments": todays_count,
        "upcoming_appointments": upcoming_count,
        "by_status": {str(status): count for status, count in status_counts}
    }