"""
Patient Management API Routes
File: backend/api/routes/patients.py
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional

from backend.config.database import get_db
from backend.models.database import Patient
from backend.schemas.schemas import PatientCreate, PatientUpdate, PatientResponse
from backend.auth.security import get_current_user
from backend.models.database import User


router = APIRouter(prefix="/patients", tags=["Patient Management"])


@router.post("/", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    patient_data: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new patient record.
    
    **Request Body:**
    ```json
    {
        "unique_id": "PAT12345",
        "name": "Rajesh Kumar",
        "gender": "M",
        "phone": "+919876543210",
        "email": "rajesh@example.com",
        "address": "Mumbai, Maharashtra",
        "date_of_birth": "1985-05-15"
    }
    ```
    
    **Returns:**
    - Created patient information
    """
    # Check if unique_id already exists
    existing_patient = db.query(Patient).filter(
        Patient.unique_id == patient_data.unique_id
    ).first()
    
    if existing_patient:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Patient with unique_id {patient_data.unique_id} already exists"
        )
    
    # Create new patient
    new_patient = Patient(**patient_data.dict())
    
    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)
    
    return PatientResponse.from_orm(new_patient)


@router.get("/", response_model=List[PatientResponse])
async def get_all_patients(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None, description="Search by name, phone, or unique_id"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all patients with optional search and pagination.
    
    **Query Parameters:**
    - skip: Number of records to skip (default: 0)
    - limit: Maximum records to return (default: 100, max: 1000)
    - search: Search term for name, phone, or unique_id
    
    **Example:**
    ```
    GET /api/v1/patients/?skip=0&limit=50&search=kumar
    ```
    """
    query = db.query(Patient)
    
    # Apply search filter if provided
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Patient.name.ilike(search_term),
                Patient.phone.ilike(search_term),
                Patient.unique_id.ilike(search_term),
                Patient.email.ilike(search_term)
            )
        )
    
    # Apply pagination
    patients = query.offset(skip).limit(limit).all()
    
    return [PatientResponse.from_orm(patient) for patient in patients]


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient_by_id(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get specific patient by ID.
    
    **Path Parameters:**
    - patient_id: Database ID of the patient
    
    **Example:**
    ```
    GET /api/v1/patients/1
    ```
    """
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID {patient_id} not found"
        )
    
    return PatientResponse.from_orm(patient)


@router.get("/unique/{unique_id}", response_model=PatientResponse)
async def get_patient_by_unique_id(
    unique_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get patient by unique_id (e.g., PAT12345).
    
    **Path Parameters:**
    - unique_id: Patient's unique identifier
    
    **Example:**
    ```
    GET /api/v1/patients/unique/PAT12345
    ```
    """
    patient = db.query(Patient).filter(Patient.unique_id == unique_id).first()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with unique_id {unique_id} not found"
        )
    
    return PatientResponse.from_orm(patient)


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: int,
    patient_update: PatientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update patient information.
    
    **Path Parameters:**
    - patient_id: Database ID of the patient
    
    **Request Body (all fields optional):**
    ```json
    {
        "name": "Updated Name",
        "phone": "+919999999999",
        "email": "newemail@example.com",
        "address": "New Address"
    }
    ```
    """
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID {patient_id} not found"
        )
    
    # Update fields if provided
    update_data = patient_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(patient, field, value)
    
    db.commit()
    db.refresh(patient)
    
    return PatientResponse.from_orm(patient)


@router.delete("/{patient_id}")
async def delete_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a patient record.
    
    **Path Parameters:**
    - patient_id: Database ID of the patient
    
    **Note:** This is a hard delete. Use with caution.
    """
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID {patient_id} not found"
        )
    
    db.delete(patient)
    db.commit()
    
    return {"message": f"Patient {patient.name} deleted successfully"}


@router.get("/stats/count")
async def get_patient_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get total patient count.
    
    **Returns:**
    - Total number of patients in database
    """
    total_patients = db.query(Patient).count()
    
    return {
        "total_patients": total_patients
    }