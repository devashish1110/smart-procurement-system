"""
Purchase Order Management API Routes
File: backend/api/routes/procurement.py
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from datetime import date, datetime

from backend.config.database import get_db
from backend.models.database import (
    PurchaseOrder, PurchaseOrderItem, Medicine, 
    Vendor, User, OrderStatus
)
from backend.schemas.schemas import (
    PurchaseOrderCreate, PurchaseOrderUpdate, 
    PurchaseOrderResponse, PurchaseOrderDetailResponse
)
from backend.auth.security import get_current_user, require_pharmacist, require_doctor


router = APIRouter(prefix="/procurement", tags=["Purchase Orders & Procurement"])


@router.post("/", response_model=PurchaseOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_purchase_order(
    po_data: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pharmacist)
):
    """
    Create a new purchase order (Pharmacist/Admin only).
    
    **Request Body:**
    ```json
    {
        "vendor_id": 1,
        "expected_delivery_date": "2024-12-01",
        "notes": "Urgent order for Triphala",
        "items": [
            {
                "medicine_id": 1,
                "quantity_ordered": 50,
                "unit_price": 100.0
            },
            {
                "medicine_id": 2,
                "quantity_ordered": 30,
                "unit_price": 200.0
            }
        ]
    }
    ```
    """
    # Verify vendor exists
    vendor = db.query(Vendor).filter(Vendor.vendor_id == po_data.vendor_id).first()
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vendor with ID {po_data.vendor_id} not found"
        )
    
    if not vendor.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Vendor {vendor.vendor_name} is inactive"
        )
    
    # Verify all medicines exist
    medicine_ids = [item.medicine_id for item in po_data.items]
    medicines = db.query(Medicine).filter(Medicine.medicine_id.in_(medicine_ids)).all()
    
    if len(medicines) != len(medicine_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more medicines not found"
        )
    
    # Generate PO number
    year = datetime.now().year
    last_po = db.query(PurchaseOrder).filter(
        PurchaseOrder.po_number.like(f"PO{year}%")
    ).order_by(PurchaseOrder.po_id.desc()).first()
    
    if last_po:
        last_number = int(last_po.po_number[6:])
        new_number = last_number + 1
    else:
        new_number = 1
    
    po_number = f"PO{year}{new_number:04d}"
    
    # Calculate total amount
    total_amount = sum(
        item.quantity_ordered * item.unit_price 
        for item in po_data.items
    )
    
    # Create purchase order
    new_po = PurchaseOrder(
        po_number=po_number,
        vendor_id=po_data.vendor_id,
        order_date=date.today(),
        expected_delivery_date=po_data.expected_delivery_date,
        total_amount=total_amount,
        status=OrderStatus.draft,
        created_by=current_user.user_id,
        notes=po_data.notes
    )
    
    db.add(new_po)
    db.flush()  # Get the PO ID
    
    # Create PO items
    for item_data in po_data.items:
        po_item = PurchaseOrderItem(
            po_id=new_po.po_id,
            medicine_id=item_data.medicine_id,
            quantity_ordered=item_data.quantity_ordered,
            quantity_received=0,
            unit_price=item_data.unit_price,
            total_price=item_data.quantity_ordered * item_data.unit_price
        )
        db.add(po_item)
    
    # Update vendor total orders
    vendor.total_orders += 1
    
    db.commit()
    db.refresh(new_po)
    
    return PurchaseOrderResponse.from_orm(new_po)


@router.get("/", response_model=List[PurchaseOrderResponse])
async def get_all_purchase_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[OrderStatus] = Query(None, description="Filter by status"),
    vendor_id: Optional[int] = Query(None, description="Filter by vendor"),
    start_date: Optional[date] = Query(None, description="Filter from date"),
    end_date: Optional[date] = Query(None, description="Filter to date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all purchase orders with filters.
    
    **Query Parameters:**
    - skip: Records to skip
    - limit: Max records to return
    - status: Filter by status
    - vendor_id: Filter by vendor
    - start_date: Filter orders from this date
    - end_date: Filter orders to this date
    
    **Example:**
    ```
    GET /api/v1/procurement/?status=approved&vendor_id=1
    ```
    """
    query = db.query(PurchaseOrder)
    
    # Apply filters
    if status:
        query = query.filter(PurchaseOrder.status == status)
    
    if vendor_id:
        query = query.filter(PurchaseOrder.vendor_id == vendor_id)
    
    if start_date:
        query = query.filter(PurchaseOrder.order_date >= start_date)
    
    if end_date:
        query = query.filter(PurchaseOrder.order_date <= end_date)
    
    # Order by most recent first
    query = query.order_by(PurchaseOrder.order_date.desc())
    
    # Apply pagination
    pos = query.offset(skip).limit(limit).all()
    
    return [PurchaseOrderResponse.from_orm(po) for po in pos]


@router.get("/{po_id}", response_model=PurchaseOrderDetailResponse)
async def get_purchase_order_detail(
    po_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get purchase order with full details including items.
    
    **Path Parameters:**
    - po_id: Database ID of the purchase order
    """
    po = db.query(PurchaseOrder).filter(PurchaseOrder.po_id == po_id).first()
    
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order with ID {po_id} not found"
        )
    
    # Get vendor name
    vendor = db.query(Vendor).filter(Vendor.vendor_id == po.vendor_id).first()
    
    # Get items with medicine details
    items = db.query(PurchaseOrderItem).filter(
        PurchaseOrderItem.po_id == po_id
    ).all()
    
    # Build response
    from backend.schemas.schemas import PurchaseOrderItemResponse
    
    po_dict = {
        "po_id": po.po_id,
        "po_number": po.po_number,
        "vendor_id": po.vendor_id,
        "vendor_name": vendor.vendor_name if vendor else "Unknown",
        "order_date": po.order_date,
        "expected_delivery_date": po.expected_delivery_date,
        "actual_delivery_date": po.actual_delivery_date,
        "total_amount": po.total_amount,
        "status": po.status,
        "notes": po.notes,
        "created_at": po.created_at,
        "items": [PurchaseOrderItemResponse.from_orm(item) for item in items]
    }
    
    return po_dict


@router.put("/{po_id}/approve", response_model=PurchaseOrderResponse)
async def approve_purchase_order(
    po_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor)
):
    """
    Approve a purchase order (Doctor/Admin only).
    Changes status from draft to approved.
    
    **Path Parameters:**
    - po_id: Database ID of the purchase order
    """
    po = db.query(PurchaseOrder).filter(PurchaseOrder.po_id == po_id).first()
    
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order with ID {po_id} not found"
        )
    
    if po.status != OrderStatus.draft:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Can only approve draft orders. Current status: {po.status}"
        )
    
    po.status = OrderStatus.approved
    po.approved_by = current_user.user_id
    
    db.commit()
    db.refresh(po)
    
    return PurchaseOrderResponse.from_orm(po)


@router.put("/{po_id}/mark-ordered", response_model=PurchaseOrderResponse)
async def mark_purchase_order_ordered(
    po_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pharmacist)
):
    """
    Mark purchase order as ordered (sent to vendor).
    
    **Path Parameters:**
    - po_id: Database ID of the purchase order
    """
    po = db.query(PurchaseOrder).filter(PurchaseOrder.po_id == po_id).first()
    
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order with ID {po_id} not found"
        )
    
    if po.status != OrderStatus.approved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Can only mark approved orders as ordered. Current status: {po.status}"
        )
    
    po.status = OrderStatus.ordered
    
    db.commit()
    db.refresh(po)
    
    return PurchaseOrderResponse.from_orm(po)


@router.put("/{po_id}/receive", response_model=PurchaseOrderResponse)
async def receive_purchase_order(
    po_id: int,
    received_items: List[dict],  # [{"po_item_id": 1, "quantity_received": 50, "batch_number": "BATCH001", "expiry_date": "2025-12-31"}]
    db: Session = Depends(get_db),
    current_user: User = Depends(require_pharmacist)
):
    """
    Mark items as received and update inventory.
    
    **Path Parameters:**
    - po_id: Database ID of the purchase order
    
    **Request Body:**
    ```json
    [
        {
            "po_item_id": 1,
            "quantity_received": 50,
            "batch_number": "BATCH2024001",
            "expiry_date": "2025-12-31"
        },
        {
            "po_item_id": 2,
            "quantity_received": 30,
            "batch_number": "BATCH2024002",
            "expiry_date": "2026-06-30"
        }
    ]
    ```
    """
    from backend.models.database import InventoryStock
    
    po = db.query(PurchaseOrder).filter(PurchaseOrder.po_id == po_id).first()
    
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order with ID {po_id} not found"
        )
    
    if po.status not in [OrderStatus.ordered, OrderStatus.partially_received]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Can only receive ordered items. Current status: {po.status}"
        )
    
    # Update each item
    all_received = True
    for item_data in received_items:
        po_item = db.query(PurchaseOrderItem).filter(
            PurchaseOrderItem.po_item_id == item_data["po_item_id"]
        ).first()
        
        if not po_item or po_item.po_id != po_id:
            continue
        
        # Update quantity received
        po_item.quantity_received += item_data["quantity_received"]
        po_item.batch_number = item_data.get("batch_number")
        po_item.expiry_date = item_data.get("expiry_date")
        
        # Check if fully received
        if po_item.quantity_received < po_item.quantity_ordered:
            all_received = False
        
        # Add to inventory
        new_stock = InventoryStock(
            medicine_id=po_item.medicine_id,
            batch_number=item_data.get("batch_number", "UNKNOWN"),
            quantity_available=item_data["quantity_received"],
            expiry_date=item_data.get("expiry_date"),
            purchase_date=date.today(),
            purchase_price=po_item.unit_price * item_data["quantity_received"],
            vendor_id=po.vendor_id,
            status="available"
        )
        db.add(new_stock)
    
    # Update PO status
    if all_received:
        po.status = OrderStatus.received
        po.actual_delivery_date = date.today()
    else:
        po.status = OrderStatus.partially_received
    
    db.commit()
    db.refresh(po)
    
    return PurchaseOrderResponse.from_orm(po)


@router.put("/{po_id}/cancel", response_model=PurchaseOrderResponse)
async def cancel_purchase_order(
    po_id: int,
    reason: str = Query(..., description="Reason for cancellation"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor)
):
    """
    Cancel a purchase order (Doctor/Admin only).
    
    **Path Parameters:**
    - po_id: Database ID of the purchase order
    
    **Query Parameters:**
    - reason: Reason for cancellation
    """
    po = db.query(PurchaseOrder).filter(PurchaseOrder.po_id == po_id).first()
    
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order with ID {po_id} not found"
        )
    
    if po.status in [OrderStatus.received, OrderStatus.cancelled]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel order with status: {po.status}"
        )
    
    po.status = OrderStatus.cancelled
    po.notes = f"{po.notes or ''}\nCancellation reason: {reason}"
    
    db.commit()
    db.refresh(po)
    
    return PurchaseOrderResponse.from_orm(po)


@router.get("/stats/summary")
async def get_procurement_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get procurement statistics summary.
    
    **Returns:**
    - Total purchase orders
    - Orders by status
    - Total procurement value
    - Pending orders value
    """
    # Count by status
    status_counts = db.query(
        PurchaseOrder.status,
        func.count(PurchaseOrder.po_id).label('count'),
        func.sum(PurchaseOrder.total_amount).label('total_value')
    ).group_by(PurchaseOrder.status).all()
    
    total_pos = sum(count for _, count, _ in status_counts)
    total_value = sum(value or 0 for _, _, value in status_counts)
    
    status_breakdown = {
        str(status): {
            "count": count,
            "total_value": float(value or 0)
        }
        for status, count, value in status_counts
    }
    
    # Pending orders (approved + ordered + partially_received)
    pending_value = sum(
        status_breakdown.get(status, {}).get("total_value", 0)
        for status in ["approved", "ordered", "partially_received"]
    )
    
    return {
        "total_purchase_orders": total_pos,
        "total_procurement_value": round(total_value, 2),
        "pending_orders_value": round(pending_value, 2),
        "by_status": status_breakdown
    }