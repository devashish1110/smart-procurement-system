"""
Billing Management API Routes
File: backend/api/routes/billing.py
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from datetime import date, datetime

from backend.config.database import get_db
from backend.models.database import Bill, Patient, Appointment, User
from backend.auth.security import get_current_user


router = APIRouter(prefix="/billing", tags=["Billing Management"])


# Pydantic schemas for billing
from pydantic import BaseModel

class BillCreate(BaseModel):
    patient_id: int
    appointment_id: Optional[int] = None
    bill_date: date
    consultation_charge: float = 0.0
    medicine_charge: float = 0.0
    treatment_charge: float = 0.0
    payment_mode: str = "cash"
    is_online: bool = False

class BillUpdate(BaseModel):
    amount_paid: Optional[float] = None
    payment_mode: Optional[str] = None
    is_online: Optional[bool] = None

class BillResponse(BaseModel):
    bill_id: int
    bill_number: str
    patient_id: int
    appointment_id: Optional[int]
    bill_date: date
    consultation_charge: float
    medicine_charge: float
    treatment_charge: float
    total_amount: float
    amount_paid: float
    balance: float
    payment_mode: str
    is_online: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


@router.post("/", response_model=BillResponse, status_code=status.HTTP_201_CREATED)
async def create_bill(
    bill_data: BillCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify patient exists
    patient = db.query(Patient).filter(
        Patient.patient_id == bill_data.patient_id
    ).first()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID {bill_data.patient_id} not found"
        )
    
    # Generate bill number
    year = datetime.now().year
    last_bill = db.query(Bill).filter(
        Bill.bill_number.like(f"BILL{year}%")
    ).order_by(Bill.bill_id.desc()).first()
    
    if last_bill:
        last_number = int(last_bill.bill_number[8:])
        new_number = last_number + 1
    else:
        new_number = 1
    
    bill_number = f"BILL{year}{new_number:05d}"
    
    # Calculate total and balance
    total_amount = (
        bill_data.consultation_charge + 
        bill_data.medicine_charge + 
        bill_data.treatment_charge
    )
    
    # Create bill
    new_bill = Bill(
        bill_number=bill_number,
        patient_id=bill_data.patient_id,
        appointment_id=bill_data.appointment_id,
        bill_date=bill_data.bill_date,
        consultation_charge=bill_data.consultation_charge,
        medicine_charge=bill_data.medicine_charge,
        treatment_charge=bill_data.treatment_charge,
        total_amount=total_amount,
        amount_paid=total_amount,  # Assume full payment initially
        balance=0.0,
        payment_mode=bill_data.payment_mode,
        is_online=bill_data.is_online,
        created_by=current_user.user_id
    )
    
    db.add(new_bill)
    db.commit()
    db.refresh(new_bill)
    
    return BillResponse.from_orm(new_bill)


@router.get("/", response_model=List[BillResponse])
async def get_all_bills(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    patient_id: Optional[int] = Query(None, description="Filter by patient"),
    start_date: Optional[date] = Query(None, description="Filter from date"),
    end_date: Optional[date] = Query(None, description="Filter to date"),
    payment_mode: Optional[str] = Query(None, description="Filter by payment mode"),
    has_balance: Optional[bool] = Query(None, description="Filter unpaid bills"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Bill)
    
    # Apply filters
    if patient_id:
        query = query.filter(Bill.patient_id == patient_id)
    
    if start_date:
        query = query.filter(Bill.bill_date >= start_date)
    
    if end_date:
        query = query.filter(Bill.bill_date <= end_date)
    
    if payment_mode:
        query = query.filter(Bill.payment_mode == payment_mode)
    
    if has_balance is not None:
        if has_balance:
            query = query.filter(Bill.balance > 0)
        else:
            query = query.filter(Bill.balance == 0)
    
    # Order by most recent first
    query = query.order_by(Bill.bill_date.desc())
    
    # Apply pagination
    bills = query.offset(skip).limit(limit).all()
    
    return [BillResponse.from_orm(bill) for bill in bills]


@router.get("/today")
async def get_todays_bills(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get today's bills with patient details.
    """
    # Use left join to avoid errors if patient missing
    results = db.query(
        Bill,
        Patient.name,
        Patient.phone
    ).join(
        Patient, Bill.patient_id == Patient.patient_id, isouter=True
    ).filter(
        Bill.bill_date == date.today()
    ).order_by(
        Bill.created_at.desc()
    ).all()
    
    return [
        {
            "bill_id": bill.bill_id,
            "bill_number": bill.bill_number,
            "patient_name": patient_name,
            "patient_phone": patient_phone,
            "total_amount": bill.total_amount or 0,
            "amount_paid": bill.amount_paid or 0,
            "balance": bill.balance or 0,
            "payment_mode": bill.payment_mode,
            "created_at": bill.created_at
        }
        for bill, patient_name, patient_phone in results
    ]


@router.get("/{bill_id}", response_model=BillResponse)
async def get_bill_by_id(
    bill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    bill = db.query(Bill).filter(Bill.bill_id == bill_id).first()
    
    if not bill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bill with ID {bill_id} not found"
        )
    
    return BillResponse.from_orm(bill)


@router.get("/number/{bill_number}", response_model=BillResponse)
async def get_bill_by_number(
    bill_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    bill = db.query(Bill).filter(Bill.bill_number == bill_number).first()
    
    if not bill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bill with number {bill_number} not found"
        )
    
    return BillResponse.from_orm(bill)


@router.put("/{bill_id}/payment", response_model=BillResponse)
async def update_payment(
    bill_id: int,
    amount_paid: float = Query(..., ge=0),
    payment_mode: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    bill = db.query(Bill).filter(Bill.bill_id == bill_id).first()
    
    if not bill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bill with ID {bill_id} not found"
        )
    
    # Update payment
    bill.amount_paid += amount_paid
    bill.balance = (bill.total_amount or 0) - (bill.amount_paid or 0)
    
    if payment_mode:
        bill.payment_mode = payment_mode
    
    if bill.amount_paid > bill.total_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount paid cannot exceed total bill amount"
        )
    
    db.commit()
    db.refresh(bill)
    
    return BillResponse.from_orm(bill)


@router.get("/patient/{patient_id}/history")
async def get_patient_billing_history(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID {patient_id} not found"
        )
    
    bills = db.query(Bill).filter(
        Bill.patient_id == patient_id
    ).order_by(
        Bill.bill_date.desc()
    ).all()
    
    total_billed = sum(bill.total_amount or 0 for bill in bills)
    total_paid = sum(bill.amount_paid or 0 for bill in bills)
    total_balance = sum(bill.balance or 0 for bill in bills)
    
    return {
        "patient_id": patient_id,
        "patient_name": patient.name,
        "total_bills": len(bills),
        "total_billed": total_billed,
        "total_paid": total_paid,
        "total_outstanding": total_balance,
        "bills": [BillResponse.from_orm(bill) for bill in bills]
    }


@router.get("/stats/summary")
async def get_billing_statistics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Bill)
    
    if start_date:
        query = query.filter(Bill.bill_date >= start_date)
    
    if end_date:
        query = query.filter(Bill.bill_date <= end_date)
    
    bills = query.all()
    
    total_revenue = sum(bill.total_amount or 0 for bill in bills)
    total_collected = sum(bill.amount_paid or 0 for bill in bills)
    total_outstanding = sum(bill.balance or 0 for bill in bills)
    
    consultation_revenue = sum(bill.consultation_charge or 0 for bill in bills)
    medicine_revenue = sum(bill.medicine_charge or 0 for bill in bills)
    treatment_revenue = sum(bill.treatment_charge or 0 for bill in bills)
    
    # Payment mode breakdown
    payment_modes = db.query(
        Bill.payment_mode,
        func.count(Bill.bill_id).label('count'),
        func.sum(Bill.amount_paid).label('total')
    ).group_by(Bill.payment_mode)
    
    if start_date:
        payment_modes = payment_modes.filter(Bill.bill_date >= start_date)
    if end_date:
        payment_modes = payment_modes.filter(Bill.bill_date <= end_date)
    
    payment_modes = payment_modes.all()
    
    return {
        "total_bills": len(bills),
        "total_revenue": round(total_revenue, 2),
        "total_collected": round(total_collected, 2),
        "total_outstanding": round(total_outstanding, 2),
        "revenue_breakdown": {
            "consultation": round(consultation_revenue, 2),
            "medicine": round(medicine_revenue, 2),
            "treatment": round(treatment_revenue, 2)
        },
        "payment_modes": {
            mode: {
                "count": count,
                "total": round(float(total or 0), 2)
            }
            for mode, count, total in payment_modes
        }
    }
