"""
Inventory Management API Routes
File: backend/api/routes/inventory.py
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from datetime import date, timedelta

from backend.config.database import get_db
from backend.models.database import InventoryStock, Medicine, Vendor, StockStatus
from backend.schemas.schemas import (
    InventoryStockCreate, InventoryStockUpdate, 
    InventoryStockResponse, InventoryStockWithMedicine
)
from backend.auth.security import get_current_user, require_pharmacist
from backend.models.database import User


router = APIRouter(prefix="/inventory", tags=["Inventory Management"])


@router.post("/", response_model=InventoryStockResponse, status_code=status.HTTP_201_CREATED)
async def add_stock(
    stock_data: InventoryStockCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pharmacist)
):
    """
    Add new stock entry (Pharmacist/Admin only).
    
    **Request Body:**
    ```json
    {
        "medicine_id": 1,
        "batch_number": "BATCH2024001",
        "quantity_available": 50,
        "expiry_date": "2025-12-31",
        "purchase_date": "2024-11-10",
        "purchase_price": 5000.00,
        "vendor_id": 1
    }
    ```
    """
    # Verify medicine exists
    medicine = db.query(Medicine).filter(
        Medicine.medicine_id == stock_data.medicine_id
    ).first()
    
    if not medicine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Medicine with ID {stock_data.medicine_id} not found"
        )
    
    # Check if batch already exists
    existing_batch = db.query(InventoryStock).filter(
        and_(
            InventoryStock.medicine_id == stock_data.medicine_id,
            InventoryStock.batch_number == stock_data.batch_number
        )
    ).first()
    
    if existing_batch:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Batch {stock_data.batch_number} already exists for this medicine"
        )
    
    # Determine stock status
    days_to_expiry = (stock_data.expiry_date - date.today()).days
    
    if days_to_expiry < 0:
        stock_status = StockStatus.expired
    elif days_to_expiry < 30:
        stock_status = StockStatus.near_expiry
    elif stock_data.quantity_available == 0:
        stock_status = StockStatus.out_of_stock
    elif stock_data.quantity_available <= medicine.reorder_level:
        stock_status = StockStatus.low_stock
    else:
        stock_status = StockStatus.available
    
    # Create new stock entry
    new_stock = InventoryStock(
        **stock_data.dict(),
        status=stock_status
    )
    
    db.add(new_stock)
    db.commit()
    db.refresh(new_stock)
    
    return InventoryStockResponse.from_orm(new_stock)


@router.get("/", response_model=List[InventoryStockResponse])
async def get_all_stock(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    medicine_id: Optional[int] = Query(None, description="Filter by medicine ID"),
    status: Optional[StockStatus] = Query(None, description="Filter by status"),
    vendor_id: Optional[int] = Query(None, description="Filter by vendor ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all inventory stock with filters.
    
    **Query Parameters:**
    - skip: Records to skip
    - limit: Max records to return
    - medicine_id: Filter by specific medicine
    - status: Filter by status (available, low_stock, out_of_stock, near_expiry, expired)
    - vendor_id: Filter by vendor
    
    **Example:**
    ```
    GET /api/v1/inventory/?status=low_stock&limit=50
    ```
    """
    query = db.query(InventoryStock)
    
    # Apply filters
    if medicine_id:
        query = query.filter(InventoryStock.medicine_id == medicine_id)
    
    if status:
        query = query.filter(InventoryStock.status == status)
    
    if vendor_id:
        query = query.filter(InventoryStock.vendor_id == vendor_id)
    
    # Apply pagination
    stocks = query.offset(skip).limit(limit).all()
    
    return [InventoryStockResponse.from_orm(stock) for stock in stocks]


@router.get("/with-details", response_model=List[dict])
async def get_stock_with_medicine_details(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[StockStatus] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get inventory stock with medicine and vendor details.
    
    **Returns:**
    - Stock information with medicine name, category, vendor name
    """
    query = db.query(
        InventoryStock,
        Medicine.medicine_name,
        Medicine.category,
        Vendor.vendor_name
    ).join(
        Medicine, InventoryStock.medicine_id == Medicine.medicine_id
    ).outerjoin(
        Vendor, InventoryStock.vendor_id == Vendor.vendor_id
    )
    
    if status:
        query = query.filter(InventoryStock.status == status)
    
    results = query.offset(skip).limit(limit).all()
    
    return [
        {
            "stock_id": stock.stock_id,
            "medicine_id": stock.medicine_id,
            "medicine_name": med_name,
            "category": category,
            "batch_number": stock.batch_number,
            "quantity_available": stock.quantity_available,
            "expiry_date": stock.expiry_date,
            "purchase_date": stock.purchase_date,
            "purchase_price": stock.purchase_price,
            "vendor_name": vendor_name,
            "status": stock.status,
            "alert_sent": stock.alert_sent,
            "last_updated": stock.last_updated
        }
        for stock, med_name, category, vendor_name in results
    ]


@router.get("/alerts/low-stock")
async def get_low_stock_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all medicines with low stock or out of stock.
    
    **Returns:**
    - List of medicines needing restock with current quantity and reorder level
    """
    # Get medicines with total stock below reorder level
    results = db.query(
        Medicine.medicine_id,
        Medicine.medicine_name,
        Medicine.category,
        Medicine.reorder_level,
        func.sum(InventoryStock.quantity_available).label('total_quantity')
    ).join(
        InventoryStock, Medicine.medicine_id == InventoryStock.medicine_id
    ).filter(
        Medicine.is_active == True
    ).group_by(
        Medicine.medicine_id,
        Medicine.medicine_name,
        Medicine.category,
        Medicine.reorder_level
    ).having(
        func.sum(InventoryStock.quantity_available) <= Medicine.reorder_level
    ).all()
    
    return [
        {
            "medicine_id": med_id,
            "medicine_name": name,
            "category": category,
            "current_quantity": int(total_qty) if total_qty else 0,
            "reorder_level": reorder,
            "shortage": reorder - (int(total_qty) if total_qty else 0),
            "status": "out_of_stock" if (total_qty or 0) == 0 else "low_stock"
        }
        for med_id, name, category, reorder, total_qty in results
    ]


@router.get("/alerts/expiring")
async def get_expiring_medicines(
    days: int = Query(90, ge=1, le=365, description="Days until expiry"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get medicines expiring within specified days.
    
    **Query Parameters:**
    - days: Number of days to check (default: 90)
    
    **Returns:**
    - List of medicines expiring soon
    """
    expiry_threshold = date.today() + timedelta(days=days)
    
    results = db.query(
        InventoryStock,
        Medicine.medicine_name,
        Medicine.category
    ).join(
        Medicine, InventoryStock.medicine_id == Medicine.medicine_id
    ).filter(
        and_(
            InventoryStock.expiry_date <= expiry_threshold,
            InventoryStock.expiry_date >= date.today(),
            InventoryStock.quantity_available > 0
        )
    ).order_by(
        InventoryStock.expiry_date.asc()
    ).all()
    
    return [
        {
            "stock_id": stock.stock_id,
            "medicine_name": med_name,
            "category": category,
            "batch_number": stock.batch_number,
            "quantity_available": stock.quantity_available,
            "expiry_date": stock.expiry_date,
            "days_until_expiry": (stock.expiry_date - date.today()).days,
            "status": stock.status
        }
        for stock, med_name, category in results
    ]


@router.get("/alerts/expired")
async def get_expired_medicines(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all expired medicines.
    
    **Returns:**
    - List of expired medicines that need disposal
    """
    results = db.query(
        InventoryStock,
        Medicine.medicine_name,
        Medicine.category
    ).join(
        Medicine, InventoryStock.medicine_id == Medicine.medicine_id
    ).filter(
        and_(
            InventoryStock.expiry_date < date.today(),
            InventoryStock.quantity_available > 0
        )
    ).order_by(
        InventoryStock.expiry_date.desc()
    ).all()
    
    return [
        {
            "stock_id": stock.stock_id,
            "medicine_name": med_name,
            "category": category,
            "batch_number": stock.batch_number,
            "quantity_available": stock.quantity_available,
            "expiry_date": stock.expiry_date,
            "days_expired": (date.today() - stock.expiry_date).days
        }
        for stock, med_name, category in results
    ]


@router.put("/{stock_id}", response_model=InventoryStockResponse)
async def update_stock(
    stock_id: int,
    stock_update: InventoryStockUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pharmacist)
):
    """
    Update stock quantity or status (Pharmacist/Admin only).
    
    **Path Parameters:**
    - stock_id: Database ID of the stock entry
    
    **Request Body:**
    ```json
    {
        "quantity_available": 25,
        "status": "low_stock"
    }
    ```
    """
    stock = db.query(InventoryStock).filter(
        InventoryStock.stock_id == stock_id
    ).first()
    
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock entry with ID {stock_id} not found"
        )
    
    # Update fields
    update_data = stock_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(stock, field, value)
    
    db.commit()
    db.refresh(stock)
    
    return InventoryStockResponse.from_orm(stock)


@router.get("/stats/summary")
async def get_inventory_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive inventory statistics.
    
    **Returns:**
    - Total items in stock
    - Low stock items
    - Out of stock items
    - Expiring soon
    - Expired items
    - Total inventory value
    """
    from sqlalchemy import case
    
    # Get counts by status
    status_counts = db.query(
        InventoryStock.status,
        func.count(InventoryStock.stock_id).label('count')
    ).group_by(
        InventoryStock.status
    ).all()
    
    # Calculate total inventory value
    total_value = db.query(
        func.sum(InventoryStock.quantity_available * InventoryStock.purchase_price)
    ).scalar() or 0
    
    # Count expiring in 30 days
    expiring_soon = db.query(InventoryStock).filter(
        and_(
            InventoryStock.expiry_date <= date.today() + timedelta(days=30),
            InventoryStock.expiry_date >= date.today(),
            InventoryStock.quantity_available > 0
        )
    ).count()
    
    status_dict = {status: count for status, count in status_counts}
    
    return {
        "total_stock_items": sum(status_dict.values()),
        "available": status_dict.get(StockStatus.available, 0),
        "low_stock": status_dict.get(StockStatus.low_stock, 0),
        "out_of_stock": status_dict.get(StockStatus.out_of_stock, 0),
        "near_expiry": status_dict.get(StockStatus.near_expiry, 0),
        "expired": status_dict.get(StockStatus.expired, 0),
        "expiring_in_30_days": expiring_soon,
        "total_inventory_value": round(float(total_value), 2)
    }