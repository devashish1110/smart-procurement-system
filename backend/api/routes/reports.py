"""
Reports & Analytics API Routes
File: backend/api/routes/reports.py
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, extract
from typing import Optional
from datetime import date, timedelta

from backend.config.database import get_db
from backend.models.database import (
    Bill, Patient, Medicine, InventoryStock, 
    PurchaseOrder, Appointment, Vendor
)
from backend.auth.security import get_current_user, require_doctor
from backend.models.database import User

router = APIRouter(prefix="/reports", tags=["Reports & Analytics"])


@router.get("/dashboard")
async def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    today = date.today()
    
    # Patient Stats
    total_patients = db.query(Patient).count()
    new_patients_this_month = db.query(Patient).filter(
        extract('month', Patient.created_at) == today.month,
        extract('year', Patient.created_at) == today.year
    ).count()
    
    # Financial Stats (Current Month)
    month_start = date(today.year, today.month, 1)
    month_bills = db.query(Bill).filter(Bill.bill_date >= month_start).all()
    
    monthly_revenue = sum(bill.total_amount or 0 for bill in month_bills)
    monthly_collected = sum(bill.amount_paid or 0 for bill in month_bills)
    
    todays_bills = db.query(Bill).filter(Bill.bill_date == today).all()
    todays_revenue = sum(bill.total_amount or 0 for bill in todays_bills)
    
    # Inventory Alerts
    low_stock_count = db.query(InventoryStock).filter(InventoryStock.status == 'low_stock').count()
    
    expiring_soon = db.query(InventoryStock).filter(
        and_(
            InventoryStock.expiry_date <= today + timedelta(days=30),
            InventoryStock.expiry_date >= today,
            InventoryStock.quantity_available > 0
        )
    ).count()
    
    # Today's Appointments
    todays_appointments = db.query(Appointment).filter(
        Appointment.appointment_date == today
    ).count()
    
    # Pending Purchase Orders
    pending_pos = db.query(PurchaseOrder).filter(
        PurchaseOrder.status.in_(['approved', 'ordered'])
    ).count()
    
    return {
        "patients": {
            "total": total_patients,
            "new_this_month": new_patients_this_month
        },
        "financial": {
            "monthly_revenue": round(monthly_revenue, 2),
            "monthly_collected": round(monthly_collected, 2),
            "todays_revenue": round(todays_revenue, 2),
            "todays_bills": len(todays_bills)
        },
        "inventory": {
            "low_stock_items": low_stock_count,
            "expiring_in_30_days": expiring_soon
        },
        "appointments": {
            "today": todays_appointments
        },
        "procurement": {
            "pending_orders": pending_pos
        }
    }


@router.get("/financial")
async def get_financial_report(
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor)
):
    bills = db.query(Bill).filter(
        and_(
            Bill.bill_date >= start_date,
            Bill.bill_date <= end_date
        )
    ).all()
    
    total_revenue = sum(bill.total_amount or 0 for bill in bills)
    total_collected = sum(bill.amount_paid or 0 for bill in bills)
    total_outstanding = sum(bill.balance or 0 for bill in bills)
    
    consultation_revenue = sum(bill.consultation_charge or 0 for bill in bills)
    medicine_revenue = sum(bill.medicine_charge or 0 for bill in bills)
    treatment_revenue = sum(bill.treatment_charge or 0 for bill in bills)
    
    daily_revenue = db.query(
        Bill.bill_date,
        func.sum(Bill.total_amount).label('revenue'),
        func.count(Bill.bill_id).label('bill_count')
    ).filter(
        and_(
            Bill.bill_date >= start_date,
            Bill.bill_date <= end_date
        )
    ).group_by(Bill.bill_date).order_by(Bill.bill_date).all()
    
    expenses = db.query(
        func.sum(PurchaseOrder.total_amount)
    ).filter(
        and_(
            PurchaseOrder.order_date >= start_date,
            PurchaseOrder.order_date <= end_date,
            PurchaseOrder.status == 'received'
        )
    ).scalar() or 0
    
    profit = total_collected - expenses
    
    return {
        "period": {
            "start_date": start_date,
            "end_date": end_date,
            "days": (end_date - start_date).days + 1
        },
        "revenue": {
            "total_billed": round(total_revenue, 2),
            "total_collected": round(total_collected, 2),
            "outstanding": round(total_outstanding, 2),
            "breakdown": {
                "consultation": round(consultation_revenue, 2),
                "medicine": round(medicine_revenue, 2),
                "treatment": round(treatment_revenue, 2)
            }
        },
        "expenses": {
            "procurement": round(float(expenses), 2)
        },
        "profit": {
            "gross_profit": round(profit, 2),
            "profit_margin": round((profit / total_collected * 100) if total_collected > 0 else 0, 2)
        },
        "daily_trend": [
            {
                "date": str(bill_date),
                "revenue": float(revenue or 0),
                "bill_count": bill_count
            }
            for bill_date, revenue, bill_count in daily_revenue
        ],
        "total_bills": len(bills)
    }


@router.get("/inventory")
async def get_inventory_report(
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(
        Medicine.medicine_id,
        Medicine.medicine_name,
        Medicine.category,
        Medicine.reorder_level,
        func.sum(InventoryStock.quantity_available).label('total_stock'),
        func.sum(InventoryStock.quantity_available * InventoryStock.purchase_price).label('stock_value')
    ).join(
        InventoryStock, Medicine.medicine_id == InventoryStock.medicine_id
    ).filter(
        Medicine.is_active == True
    )
    
    if category:
        query = query.filter(Medicine.category == category)
    
    results = query.group_by(
        Medicine.medicine_id,
        Medicine.medicine_name,
        Medicine.category,
        Medicine.reorder_level
    ).all()
    
    inventory_data = []
    total_value = 0
    low_stock_items = 0
    
    for med_id, name, cat, reorder, stock, value in results:
        stock_qty = int(stock or 0)
        stock_val = float(value or 0)
        
        total_value += stock_val
        
        status = "adequate"
        if stock_qty == 0:
            status = "out_of_stock"
        elif stock_qty <= reorder:
            status = "low_stock"
            low_stock_items += 1
        
        inventory_data.append({
            "medicine_id": med_id,
            "medicine_name": name,
            "category": cat,
            "current_stock": stock_qty,
            "reorder_level": reorder,
            "stock_value": round(stock_val, 2),
            "status": status
        })
    
    return {
        "summary": {
            "total_medicines": len(results),
            "total_inventory_value": round(total_value, 2),
            "low_stock_items": low_stock_items
        },
        "inventory": sorted(inventory_data, key=lambda x: x['stock_value'], reverse=True)
    }
