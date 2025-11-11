"""
Vendor Management API Routes
File: backend/api/routes/vendors.py
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional

from backend.config.database import get_db
from backend.models.database import Vendor, PurchaseOrder
from backend.schemas.schemas import VendorCreate, VendorUpdate, VendorResponse
from backend.auth.security import get_current_user, require_pharmacist
from backend.models.database import User


router = APIRouter(prefix="/vendors", tags=["Vendor Management"])


@router.post("/", response_model=VendorResponse, status_code=status.HTTP_201_CREATED)
async def create_vendor(
    vendor_data: VendorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pharmacist)
):
    """
    Create a new vendor (Pharmacist/Admin only).
    
    **Request Body:**
    ```json
    {
        "vendor_name": "Ayurved Pharmaceuticals Ltd",
        "contact_person": "Ramesh Sharma",
        "phone": "+919876543210",
        "email": "sales@ayurvedpharma.com",
        "address": "Mumbai, Maharashtra",
        "gstin": "27AABCU9603R1ZX",
        "payment_terms": "Net 30",
        "lead_time_days": 7
    }
    ```
    """
    # Check if vendor already exists
    existing = db.query(Vendor).filter(
        or_(
            Vendor.vendor_name == vendor_data.vendor_name,
            Vendor.email == vendor_data.email
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vendor with this name or email already exists"
        )
    
    # Create new vendor
    new_vendor = Vendor(**vendor_data.dict())
    
    db.add(new_vendor)
    db.commit()
    db.refresh(new_vendor)
    
    return VendorResponse.from_orm(new_vendor)


@router.get("/", response_model=List[VendorResponse])
async def get_all_vendors(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None, description="Search by vendor name or contact"),
    active_only: bool = Query(True, description="Show only active vendors"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="Minimum rating filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all vendors with filters.
    
    **Query Parameters:**
    - skip: Records to skip
    - limit: Max records to return
    - search: Search in vendor name or contact person
    - active_only: Show only active vendors (default: true)
    - min_rating: Minimum vendor rating (0-5)
    
    **Example:**
    ```
    GET /api/v1/vendors/?active_only=true&min_rating=4.0
    ```
    """
    query = db.query(Vendor)
    
    # Filter by active status
    if active_only:
        query = query.filter(Vendor.is_active == True)
    
    # Filter by minimum rating
    if min_rating is not None:
        query = query.filter(Vendor.rating >= min_rating)
    
    # Search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Vendor.vendor_name.ilike(search_term),
                Vendor.contact_person.ilike(search_term)
            )
        )
    
    # Order by rating (highest first)
    query = query.order_by(Vendor.rating.desc())
    
    # Apply pagination
    vendors = query.offset(skip).limit(limit).all()
    
    return [VendorResponse.from_orm(vendor) for vendor in vendors]


@router.get("/{vendor_id}", response_model=VendorResponse)
async def get_vendor_by_id(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get specific vendor by ID.
    
    **Path Parameters:**
    - vendor_id: Database ID of the vendor
    """
    vendor = db.query(Vendor).filter(Vendor.vendor_id == vendor_id).first()
    
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vendor with ID {vendor_id} not found"
        )
    
    return VendorResponse.from_orm(vendor)


@router.get("/{vendor_id}/performance")
async def get_vendor_performance(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get vendor performance metrics.
    
    **Path Parameters:**
    - vendor_id: Database ID of the vendor
    
    **Returns:**
    - Total orders
    - Completed orders
    - Pending orders
    - Average delivery time
    - On-time delivery rate
    """
    vendor = db.query(Vendor).filter(Vendor.vendor_id == vendor_id).first()
    
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vendor with ID {vendor_id} not found"
        )
    
    # Get order statistics
    total_orders = db.query(PurchaseOrder).filter(
        PurchaseOrder.vendor_id == vendor_id
    ).count()
    
    completed_orders = db.query(PurchaseOrder).filter(
        PurchaseOrder.vendor_id == vendor_id,
        PurchaseOrder.status == 'received'
    ).count()
    
    pending_orders = db.query(PurchaseOrder).filter(
        PurchaseOrder.vendor_id == vendor_id,
        PurchaseOrder.status.in_(['approved', 'ordered', 'partially_received'])
    ).count()
    
    # Calculate average delivery time for completed orders
    from sqlalchemy import extract
    
    completed_pos = db.query(PurchaseOrder).filter(
        PurchaseOrder.vendor_id == vendor_id,
        PurchaseOrder.status == 'received',
        PurchaseOrder.actual_delivery_date.isnot(None)
    ).all()
    
    if completed_pos:
        delivery_times = [
            (po.actual_delivery_date - po.order_date).days 
            for po in completed_pos
        ]
        avg_delivery_time = sum(delivery_times) / len(delivery_times)
        
        # On-time delivery (delivered on or before expected date)
        on_time_deliveries = sum(
            1 for po in completed_pos 
            if po.actual_delivery_date <= po.expected_delivery_date
        )
        on_time_rate = (on_time_deliveries / len(completed_pos)) * 100
    else:
        avg_delivery_time = None
        on_time_rate = None
    
    return {
        "vendor_id": vendor_id,
        "vendor_name": vendor.vendor_name,
        "rating": vendor.rating,
        "total_orders": total_orders,
        "completed_orders": completed_orders,
        "pending_orders": pending_orders,
        "cancelled_orders": total_orders - completed_orders - pending_orders,
        "average_delivery_days": round(avg_delivery_time, 1) if avg_delivery_time else None,
        "on_time_delivery_rate": round(on_time_rate, 1) if on_time_rate else None,
        "lead_time_days": vendor.lead_time_days,
        "payment_terms": vendor.payment_terms
    }


@router.put("/{vendor_id}", response_model=VendorResponse)
async def update_vendor(
    vendor_id: int,
    vendor_update: VendorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pharmacist)
):
    """
    Update vendor information (Pharmacist/Admin only).
    
    **Path Parameters:**
    - vendor_id: Database ID of the vendor
    
    **Request Body (all fields optional):**
    ```json
    {
        "contact_person": "New Contact Name",
        "phone": "+919999999999",
        "payment_terms": "Net 45",
        "lead_time_days": 5
    }
    ```
    """
    vendor = db.query(Vendor).filter(Vendor.vendor_id == vendor_id).first()
    
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vendor with ID {vendor_id} not found"
        )
    
    # Update fields
    update_data = vendor_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(vendor, field, value)
    
    db.commit()
    db.refresh(vendor)
    
    return VendorResponse.from_orm(vendor)


@router.put("/{vendor_id}/rating")
async def update_vendor_rating(
    vendor_id: int,
    rating: float = Query(..., ge=0, le=5, description="Rating from 0 to 5"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pharmacist)
):
    """
    Update vendor rating (Pharmacist/Admin only).
    
    **Path Parameters:**
    - vendor_id: Database ID of the vendor
    
    **Query Parameters:**
    - rating: New rating (0.0 to 5.0)
    """
    vendor = db.query(Vendor).filter(Vendor.vendor_id == vendor_id).first()
    
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vendor with ID {vendor_id} not found"
        )
    
    vendor.rating = rating
    db.commit()
    db.refresh(vendor)
    
    return {"message": f"Vendor rating updated to {rating}", "vendor": VendorResponse.from_orm(vendor)}


@router.delete("/{vendor_id}")
async def delete_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pharmacist)
):
    """
    Soft delete a vendor (sets is_active to False).
    
    **Path Parameters:**
    - vendor_id: Database ID of the vendor
    """
    vendor = db.query(Vendor).filter(Vendor.vendor_id == vendor_id).first()
    
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vendor with ID {vendor_id} not found"
        )
    
    # Check if vendor has pending orders
    pending_orders = db.query(PurchaseOrder).filter(
        PurchaseOrder.vendor_id == vendor_id,
        PurchaseOrder.status.in_(['approved', 'ordered', 'partially_received'])
    ).count()
    
    if pending_orders > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot deactivate vendor with {pending_orders} pending orders"
        )
    
    # Soft delete
    vendor.is_active = False
    db.commit()
    
    return {"message": f"Vendor '{vendor.vendor_name}' deactivated successfully"}


@router.get("/stats/summary")
async def get_vendor_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get vendor statistics summary.
    
    **Returns:**
    - Total vendors
    - Active vendors
    - Inactive vendors
    - Average rating
    - Top rated vendors
    """
    total_vendors = db.query(Vendor).count()
    active_vendors = db.query(Vendor).filter(Vendor.is_active == True).count()
    inactive_vendors = total_vendors - active_vendors
    
    # Average rating
    avg_rating = db.query(func.avg(Vendor.rating)).filter(
        Vendor.is_active == True
    ).scalar() or 0
    
    # Top 5 vendors by rating
    top_vendors = db.query(Vendor).filter(
        Vendor.is_active == True
    ).order_by(
        Vendor.rating.desc()
    ).limit(5).all()
    
    return {
        "total_vendors": total_vendors,
        "active_vendors": active_vendors,
        "inactive_vendors": inactive_vendors,
        "average_rating": round(float(avg_rating), 2),
        "top_vendors": [
            {
                "vendor_id": v.vendor_id,
                "vendor_name": v.vendor_name,
                "rating": v.rating,
                "total_orders": v.total_orders
            }
            for v in top_vendors
        ]
    }