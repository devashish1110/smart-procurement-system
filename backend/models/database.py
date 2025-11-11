"""
SQLAlchemy ORM Models
File: backend/models/database.py
"""

from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, 
    Boolean, ForeignKey, Text, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from backend.config.database import Base


# ============================================
# ENUMS
# ============================================

class UserRole(str, enum.Enum):
    """User role enumeration"""
    admin = "admin"
    doctor = "doctor"
    pharmacist = "pharmacist"
    receptionist = "receptionist"
    therapist = "therapist"


class OrderStatus(str, enum.Enum):
    """Purchase order status enumeration"""
    draft = "draft"
    approved = "approved"
    ordered = "ordered"
    partially_received = "partially_received"
    received = "received"
    cancelled = "cancelled"


class StockStatus(str, enum.Enum):
    """Inventory stock status enumeration"""
    available = "available"
    low_stock = "low_stock"
    out_of_stock = "out_of_stock"
    near_expiry = "near_expiry"
    expired = "expired"


class AppointmentStatus(str, enum.Enum):
    """Appointment status enumeration"""
    scheduled = "scheduled"
    confirmed = "confirmed"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"
    no_show = "no_show"


# ============================================
# USER MODEL
# ============================================

class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False)
    email = Column(String(100), unique=True)
    phone = Column(String(15))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    last_login = Column(DateTime)
    
    def __repr__(self):
        return f"<User(id={self.user_id}, username='{self.username}', role='{self.role}')>"


# ============================================
# PATIENT MODEL
# ============================================

class Patient(Base):
    """Patient model for clinic management"""
    __tablename__ = "patients"
    
    patient_id = Column(Integer, primary_key=True, index=True)
    unique_id = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    gender = Column(String(1))
    phone = Column(String(15))
    email = Column(String(100))
    address = Column(Text)
    date_of_birth = Column(Date)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    appointments = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")
    bills = relationship("Bill", back_populates="patient", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Patient(id={self.patient_id}, name='{self.name}', unique_id='{self.unique_id}')>"


# ============================================
# MEDICINE MODEL
# ============================================

class Medicine(Base):
    """Medicine catalog model"""
    __tablename__ = "medicines"
    
    medicine_id = Column(Integer, primary_key=True, index=True)
    medicine_name = Column(String(200), nullable=False, index=True)
    category = Column(String(50), index=True)
    company = Column(String(100))
    unit_type = Column(String(20))
    unit_quantity = Column(Integer)
    mrp_per_unit = Column(Float)
    cost_per_unit = Column(Float)
    reorder_level = Column(Integer, default=10)
    storage_location = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    stock_items = relationship("InventoryStock", back_populates="medicine", cascade="all, delete-orphan")
    po_items = relationship("PurchaseOrderItem", back_populates="medicine")
    
    def __repr__(self):
        return f"<Medicine(id={self.medicine_id}, name='{self.medicine_name}')>"


# ============================================
# VENDOR MODEL
# ============================================

class Vendor(Base):
    """Vendor/Supplier model"""
    __tablename__ = "vendors"
    
    vendor_id = Column(Integer, primary_key=True, index=True)
    vendor_name = Column(String(150), nullable=False, index=True)
    contact_person = Column(String(100))
    phone = Column(String(15))
    email = Column(String(100))
    address = Column(Text)
    gstin = Column(String(15))
    payment_terms = Column(String(50))
    lead_time_days = Column(Integer)
    rating = Column(Float, default=0.0)
    total_orders = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    purchase_orders = relationship("PurchaseOrder", back_populates="vendor")
    stock_items = relationship("InventoryStock", back_populates="vendor")
    
    def __repr__(self):
        return f"<Vendor(id={self.vendor_id}, name='{self.vendor_name}')>"


# ============================================
# INVENTORY STOCK MODEL
# ============================================

class InventoryStock(Base):
    """Inventory stock tracking model"""
    __tablename__ = "inventory_stock"
    
    stock_id = Column(Integer, primary_key=True, index=True)
    medicine_id = Column(Integer, ForeignKey("medicines.medicine_id"), nullable=False)
    batch_number = Column(String(50), nullable=False, index=True)
    quantity_available = Column(Integer, nullable=False)
    expiry_date = Column(Date, nullable=False, index=True)
    purchase_date = Column(Date)
    purchase_price = Column(Float)
    vendor_id = Column(Integer, ForeignKey("vendors.vendor_id"))
    alert_sent = Column(Boolean, default=False)
    status = Column(SQLEnum(StockStatus), default=StockStatus.available)
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    medicine = relationship("Medicine", back_populates="stock_items")
    vendor = relationship("Vendor", back_populates="stock_items")
    
    def __repr__(self):
        return f"<InventoryStock(id={self.stock_id}, medicine_id={self.medicine_id}, batch='{self.batch_number}')>"


# Continue in next artifact...
# ============================================
# TREATMENT MODEL
# ============================================

class Treatment(Base):
    """Treatment types model"""
    __tablename__ = "treatments"
    
    treatment_id = Column(Integer, primary_key=True, index=True)
    treatment_code = Column(String(10), unique=True, nullable=False)
    treatment_name = Column(String(150), nullable=False)
    category = Column(String(50))
    base_price = Column(Float)
    duration_minutes = Column(Integer)
    requires_therapist = Column(Boolean, default=False)
    requires_doctor = Column(Boolean, default=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    appointments = relationship("Appointment", back_populates="treatment")
    
    def __repr__(self):
        return f"<Treatment(id={self.treatment_id}, name='{self.treatment_name}')>"


# ============================================
# APPOINTMENT MODEL
# ============================================

class Appointment(Base):
    """Patient appointment model"""
    __tablename__ = "appointments"
    
    appointment_id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.patient_id"), nullable=False)
    appointment_date = Column(Date, nullable=False, index=True)
    time_slot = Column(String(1))  # 'M' for Morning, 'E' for Evening
    treatment_id = Column(Integer, ForeignKey("treatments.treatment_id"))
    assigned_therapist = Column(Integer, ForeignKey("users.user_id"))
    assigned_doctor = Column(Integer, ForeignKey("users.user_id"))
    status = Column(SQLEnum(AppointmentStatus), default=AppointmentStatus.scheduled)
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    patient = relationship("Patient", back_populates="appointments")
    treatment = relationship("Treatment", back_populates="appointments")
    bills = relationship("Bill", back_populates="appointment")
    
    def __repr__(self):
        return f"<Appointment(id={self.appointment_id}, patient_id={self.patient_id}, date={self.appointment_date})>"


# ============================================
# BILL MODEL
# ============================================

class Bill(Base):
    """Billing and invoicing model"""
    __tablename__ = "bills"
    
    bill_id = Column(Integer, primary_key=True, index=True)
    bill_number = Column(String(20), unique=True, nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.patient_id"), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.appointment_id"))
    bill_date = Column(Date, nullable=False, index=True)
    consultation_charge = Column(Float, default=0.0)
    medicine_charge = Column(Float, default=0.0)
    treatment_charge = Column(Float, default=0.0)
    total_amount = Column(Float, nullable=False)
    amount_paid = Column(Float, default=0.0)
    balance = Column(Float, default=0.0)
    payment_mode = Column(String(20))  # cash, card, upi, online
    is_online = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey("users.user_id"))
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    patient = relationship("Patient", back_populates="bills")
    appointment = relationship("Appointment", back_populates="bills")
    
    def __repr__(self):
        return f"<Bill(id={self.bill_id}, number='{self.bill_number}', amount={self.total_amount})>"


# ============================================
# PURCHASE ORDER MODEL
# ============================================

class PurchaseOrder(Base):
    """Purchase order model"""
    __tablename__ = "purchase_orders"
    
    po_id = Column(Integer, primary_key=True, index=True)
    po_number = Column(String(20), unique=True, nullable=False, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.vendor_id"), nullable=False)
    order_date = Column(Date, nullable=False, index=True)
    expected_delivery_date = Column(Date)
    actual_delivery_date = Column(Date)
    total_amount = Column(Float, default=0.0)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.draft)
    created_by = Column(Integer, ForeignKey("users.user_id"))
    approved_by = Column(Integer, ForeignKey("users.user_id"))
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    vendor = relationship("Vendor", back_populates="purchase_orders")
    items = relationship("PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<PurchaseOrder(id={self.po_id}, number='{self.po_number}', status='{self.status}')>"


# ============================================
# PURCHASE ORDER ITEM MODEL
# ============================================

class PurchaseOrderItem(Base):
    """Individual items in a purchase order"""
    __tablename__ = "purchase_order_items"
    
    po_item_id = Column(Integer, primary_key=True, index=True)
    po_id = Column(Integer, ForeignKey("purchase_orders.po_id"), nullable=False)
    medicine_id = Column(Integer, ForeignKey("medicines.medicine_id"), nullable=False)
    quantity_ordered = Column(Integer, nullable=False)
    quantity_received = Column(Integer, default=0)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    batch_number = Column(String(50))
    expiry_date = Column(Date)
    
    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="items")
    medicine = relationship("Medicine", back_populates="po_items")
    
    def __repr__(self):
        return f"<PurchaseOrderItem(id={self.po_item_id}, po_id={self.po_id}, medicine_id={self.medicine_id})>"


# ============================================
# CHATBOT CONVERSATION MODEL (New)
# ============================================

class ChatConversation(Base):
    """Store chatbot conversation history"""
    __tablename__ = "chat_conversations"
    
    conversation_id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    intent = Column(String(50))
    confidence = Column(Float)
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<ChatConversation(id={self.conversation_id}, user_id={self.user_id})>"


# ============================================
# ALERT/NOTIFICATION MODEL (New)
# ============================================

class Alert(Base):
    """System alerts and notifications"""
    __tablename__ = "alerts"
    
    alert_id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String(50), nullable=False)  # low_stock, expiry, payment_due
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(20))  # info, warning, critical
    target_user_id = Column(Integer, ForeignKey("users.user_id"))
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    read_at = Column(DateTime)
    
    def __repr__(self):
        return f"<Alert(id={self.alert_id}, type='{self.alert_type}', severity='{self.severity}')>"