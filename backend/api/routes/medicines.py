"""
Medicine Management API Routes
File: backend/api/routes/medicines.py
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional

from backend.config.database import get_db
from backend.models.database import Medicine
from backend.schemas.schemas import MedicineCreate, MedicineUpdate, MedicineResponse
from backend.auth.security import get_current_user, require_pharmacist
from backend.models.database import User


router = APIRouter(prefix="/medicines", tags=["Medicine Management"])


@router.post("/", response_model=MedicineResponse, status_code=status.HTTP_201_CREATED)
async def create_medicine(
    medicine_data: MedicineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pharmacist)
):
    """
    Create a new medicine entry (Pharmacist/Admin only).
    
    **Request Body:**
    ```json
    {
        "medicine_name": "Triphala Churna",
        "category": "choorna",
        "company": "Dabur",
        "unit_type": "gm",
        "unit_quantity": 100,
        "mrp_per_unit": 150.00,
        "cost_per_unit": 105.00,
        "reorder_level": 10,
        "storage_location": "Shelf-A3"
    }
    ```
    """
    # Check if medicine with same name already exists
    existing = db.query(Medicine).filter(
        Medicine.medicine_name == medicine_data.medicine_name,
        Medicine.company == medicine_data.company
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Medicine '{medicine_data.medicine_name}' from {medicine_data.company} already exists"
        )
    
    # Create new medicine
    new_medicine = Medicine(**medicine_data.dict())
    
    db.add(new_medicine)
    db.commit()
    db.refresh(new_medicine)
    
    return MedicineResponse.from_orm(new_medicine)


@router.get("/", response_model=List[MedicineResponse])
async def get_all_medicines(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None, description="Search by medicine name or company"),
    category: Optional[str] = Query(None, description="Filter by category"),
    active_only: bool = Query(True, description="Show only active medicines"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all medicines with filters and pagination.
    
    **Query Parameters:**
    - skip: Records to skip
    - limit: Max records to return
    - search: Search in medicine name or company
    - category: Filter by category (tablet, oil, kashaya, etc.)
    - active_only: Show only active medicines (default: true)
    
    **Example:**
    ```
    GET /api/v1/medicines/?search=triphala&category=choorna&active_only=true
    ```
    """
    query = db.query(Medicine)
    
    # Filter by active status
    if active_only:
        query = query.filter(Medicine.is_active == True)
    
    # Filter by category
    if category:
        query = query.filter(Medicine.category == category)
    
    # Search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Medicine.medicine_name.ilike(search_term),
                Medicine.company.ilike(search_term)
            )
        )
    
    # Apply pagination
    medicines = query.offset(skip).limit(limit).all()
    
    return [MedicineResponse.from_orm(medicine) for medicine in medicines]


@router.get("/categories")
async def get_medicine_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of all medicine categories.
    
    **Returns:**
    - List of unique categories with counts
    """
    from sqlalchemy import func
    
    categories = db.query(
        Medicine.category,
        func.count(Medicine.medicine_id).label('count')
    ).filter(
        Medicine.is_active == True
    ).group_by(
        Medicine.category
    ).all()
    
    return [
        {"category": cat, "count": count}
        for cat, count in categories if cat
    ]


@router.get("/{medicine_id}", response_model=MedicineResponse)
async def get_medicine_by_id(
    medicine_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get specific medicine by ID.
    
    **Path Parameters:**
    - medicine_id: Database ID of the medicine
    """
    medicine = db.query(Medicine).filter(
        Medicine.medicine_id == medicine_id
    ).first()
    
    if not medicine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Medicine with ID {medicine_id} not found"
        )
    
    return MedicineResponse.from_orm(medicine)


@router.put("/{medicine_id}", response_model=MedicineResponse)
async def update_medicine(
    medicine_id: int,
    medicine_update: MedicineUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pharmacist)
):
    """
    Update medicine information (Pharmacist/Admin only).
    
    **Path Parameters:**
    - medicine_id: Database ID of the medicine
    
    **Request Body (all fields optional):**
    ```json
    {
        "mrp_per_unit": 175.00,
        "cost_per_unit": 120.00,
        "reorder_level": 15,
        "is_active": true
    }
    ```
    """
    medicine = db.query(Medicine).filter(
        Medicine.medicine_id == medicine_id
    ).first()
    
    if not medicine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Medicine with ID {medicine_id} not found"
        )
    
    # Update fields
    update_data = medicine_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(medicine, field, value)
    
    db.commit()
    db.refresh(medicine)
    
    return MedicineResponse.from_orm(medicine)


@router.delete("/{medicine_id}")
async def delete_medicine(
    medicine_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pharmacist)
):
    """
    Soft delete a medicine (sets is_active to False).
    
    **Path Parameters:**
    - medicine_id: Database ID of the medicine
    """
    medicine = db.query(Medicine).filter(
        Medicine.medicine_id == medicine_id
    ).first()
    
    if not medicine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Medicine with ID {medicine_id} not found"
        )
    
    # Soft delete
    medicine.is_active = False
    db.commit()
    
    return {"message": f"Medicine '{medicine.medicine_name}' deactivated successfully"}


@router.get("/stats/summary")
async def get_medicine_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get medicine inventory statistics.
    
    **Returns:**
    - Total medicines
    - Active medicines
    - Inactive medicines
    - Category breakdown
    """
    from sqlalchemy import func
    
    total_medicines = db.query(Medicine).count()
    active_medicines = db.query(Medicine).filter(Medicine.is_active == True).count()
    inactive_medicines = total_medicines - active_medicines
    
    # Category breakdown
    categories = db.query(
        Medicine.category,
        func.count(Medicine.medicine_id).label('count')
    ).filter(
        Medicine.is_active == True
    ).group_by(
        Medicine.category
    ).all()
    
    return {
        "total_medicines": total_medicines,
        "active_medicines": active_medicines,
        "inactive_medicines": inactive_medicines,
        "by_category": {cat: count for cat, count in categories if cat}
    }