"""
Pydantic Schemas for Request/Response Validation
File: backend/schemas/schemas.py
"""

from pydantic import BaseModel, EmailStr, Field, validator
from datetime import date, datetime
from typing import Optional, List
from enum import Enum


# ============================================
# ENUMS
# ============================================

class UserRole(str, Enum):
    admin = "admin"
    doctor = "doctor"
    pharmacist = "pharmacist"
    receptionist = "receptionist"
    therapist = "therapist"


class OrderStatus(str, Enum):
    draft = "draft"
    approved = "approved"
    ordered = "ordered"
    partially_received = "partially_received"
    received = "received"
    cancelled = "cancelled"


class StockStatus(str, Enum):
    available = "available"
    low_stock = "low_stock"
    out_of_stock = "out_of_stock"
    near_expiry = "near_expiry"
    expired = "expired"


# ============================================
# AUTHENTICATION SCHEMAS
# ============================================

class UserLogin(BaseModel):
    """Login request schema"""
    username: str
    password: str


class Token(BaseModel):
    """JWT token response schema"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Data stored in JWT token"""
    username: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[str] = None


# ============================================
# USER SCHEMAS
# ============================================

class UserBase(BaseModel):
    """Base user schema"""
    username: str
    full_name: str
    role: UserRole
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating new user"""
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    """Schema for updating user"""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """User response schema"""
    user_id: int
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserWithToken(BaseModel):
    """User info with authentication token"""
    user: UserResponse
    access_token: str
    token_type: str = "bearer"


# ============================================
# PATIENT SCHEMAS
# ============================================

class PatientBase(BaseModel):
    """Base patient schema"""
    unique_id: str
    name: str
    gender: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    date_of_birth: Optional[date] = None


class PatientCreate(PatientBase):
    """Schema for creating new patient"""
    pass


class PatientUpdate(BaseModel):
    """Schema for updating patient"""
    name: Optional[str] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    date_of_birth: Optional[date] = None


class PatientResponse(PatientBase):
    """Patient response schema"""
    patient_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================
# MEDICINE SCHEMAS
# ============================================

class MedicineBase(BaseModel):
    """Base medicine schema"""
    medicine_name: str
    category: Optional[str] = None
    company: Optional[str] = None
    unit_type: Optional[str] = None
    unit_quantity: Optional[int] = None
    mrp_per_unit: Optional[float] = None
    cost_per_unit: Optional[float] = None
    reorder_level: int = 10
    storage_location: Optional[str] = None


class MedicineCreate(MedicineBase):
    """Schema for creating new medicine"""
    pass


class MedicineUpdate(BaseModel):
    """Schema for updating medicine"""
    medicine_name: Optional[str] = None
    category: Optional[str] = None
    company: Optional[str] = None
    mrp_per_unit: Optional[float] = None
    cost_per_unit: Optional[float] = None
    reorder_level: Optional[int] = None
    storage_location: Optional[str] = None
    is_active: Optional[bool] = None


class MedicineResponse(MedicineBase):
    """Medicine response schema"""
    medicine_id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================
# INVENTORY SCHEMAS
# ============================================

class InventoryStockBase(BaseModel):
    """Base inventory stock schema"""
    medicine_id: int
    batch_number: str
    quantity_available: int
    expiry_date: date
    purchase_date: Optional[date] = None
    purchase_price: Optional[float] = None
    vendor_id: Optional[int] = None


class InventoryStockCreate(InventoryStockBase):
    """Schema for creating stock entry"""
    pass


class InventoryStockUpdate(BaseModel):
    """Schema for updating stock"""
    quantity_available: Optional[int] = None
    status: Optional[StockStatus] = None


class InventoryStockResponse(InventoryStockBase):
    """Inventory stock response schema"""
    stock_id: int
    status: StockStatus
    alert_sent: bool
    last_updated: datetime
    
    class Config:
        from_attributes = True


class InventoryStockWithMedicine(InventoryStockResponse):
    """Stock with medicine details"""
    medicine_name: str
    medicine_category: Optional[str] = None


# ============================================
# VENDOR SCHEMAS
# ============================================

class VendorBase(BaseModel):
    """Base vendor schema"""
    vendor_name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    gstin: Optional[str] = None
    payment_terms: Optional[str] = None
    lead_time_days: Optional[int] = None


class VendorCreate(VendorBase):
    """Schema for creating vendor"""
    pass


class VendorUpdate(BaseModel):
    """Schema for updating vendor"""
    vendor_name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    payment_terms: Optional[str] = None
    lead_time_days: Optional[int] = None
    is_active: Optional[bool] = None


class VendorResponse(VendorBase):
    """Vendor response schema"""
    vendor_id: int
    rating: float
    total_orders: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================
# PURCHASE ORDER SCHEMAS
# ============================================

class PurchaseOrderItemBase(BaseModel):
    """Base PO item schema"""
    medicine_id: int
    quantity_ordered: int
    unit_price: float


class PurchaseOrderItemCreate(PurchaseOrderItemBase):
    """Schema for creating PO item"""
    pass


class PurchaseOrderItemResponse(PurchaseOrderItemBase):
    """PO item response schema"""
    item_id: int
    quantity_received: int
    total_price: float
    batch_number: Optional[str] = None
    expiry_date: Optional[date] = None
    
    class Config:
        from_attributes = True


class PurchaseOrderBase(BaseModel):
    """Base purchase order schema"""
    vendor_id: int
    expected_delivery_date: Optional[date] = None
    notes: Optional[str] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating purchase order"""
    items: List[PurchaseOrderItemCreate]


class PurchaseOrderUpdate(BaseModel):
    """Schema for updating purchase order"""
    status: Optional[OrderStatus] = None
    actual_delivery_date: Optional[date] = None
    notes: Optional[str] = None


class PurchaseOrderResponse(PurchaseOrderBase):
    """Purchase order response schema"""
    po_id: int
    po_number: str
    order_date: date
    total_amount: float
    status: OrderStatus
    created_at: datetime
    
    class Config:
        from_attributes = True


class PurchaseOrderDetailResponse(PurchaseOrderResponse):
    """Detailed PO with items"""
    items: List[PurchaseOrderItemResponse]
    vendor_name: str


# ============================================
# CHATBOT SCHEMAS
# ============================================

class ChatMessage(BaseModel):
    """Chatbot message request"""
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chatbot response"""
    response: str
    session_id: str
    intent: Optional[str] = None
    confidence: Optional[float] = None
    timestamp: datetime
    suggested_actions: Optional[List[dict]] = None


# ============================================
# ALERT/NOTIFICATION SCHEMAS
# ============================================

class AlertResponse(BaseModel):
    """Alert notification response"""
    alert_id: int
    alert_type: str
    title: str
    message: str
    severity: str
    is_read: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================
# REPORT SCHEMAS
# ============================================

class InventoryReportRequest(BaseModel):
    """Request for inventory report"""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    category: Optional[str] = None
    status: Optional[StockStatus] = None


class FinancialReportRequest(BaseModel):
    """Request for financial report"""
    start_date: date
    end_date: date
    report_type: str = Field(..., description="daily, weekly, monthly, custom")


class FinancialSummary(BaseModel):
    """Financial summary response"""
    total_revenue: float
    total_expenses: float
    consultation_revenue: float
    medicine_revenue: float
    treatment_revenue: float
    profit: float
    period: str