from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date
from app.models.models import (
    UserRole, UnitStatus, LeaseStatus, PaymentStatus,
    PaymentMethod, TicketStatus, TicketPriority
)


# ---- Auth ----
class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    phone: Optional[str] = None
    role: UserRole = UserRole.TENANT
    id_number: Optional[str] = None
    kra_pin: Optional[str] = None
    language: Optional[str] = "en"


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    id_number: Optional[str] = None
    kra_pin: Optional[str] = None
    language: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    phone: Optional[str] = None
    role: UserRole
    id_number: Optional[str] = None
    kra_pin: Optional[str] = None
    is_active: bool
    language: str
    created_at: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ---- Property ----
class PropertyCreate(BaseModel):
    name: str
    address: str
    city: str = "Nairobi"
    county: Optional[str] = None
    description: Optional[str] = None
    property_type: str = "residential"
    photo_url: Optional[str] = None
    manager_id: Optional[str] = None


class PropertyUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    county: Optional[str] = None
    description: Optional[str] = None
    property_type: Optional[str] = None
    photo_url: Optional[str] = None
    manager_id: Optional[str] = None
    is_active: Optional[bool] = None


class PropertyResponse(BaseModel):
    id: str
    name: str
    address: str
    city: str
    county: Optional[str] = None
    description: Optional[str] = None
    property_type: str
    total_units: int
    owner_id: str
    manager_id: Optional[str] = None
    photo_url: Optional[str] = None
    is_active: bool
    created_at: datetime
    owner_name: Optional[str] = None
    manager_name: Optional[str] = None
    occupied_units: Optional[int] = 0
    vacant_units: Optional[int] = 0

    class Config:
        from_attributes = True


# ---- Unit ----
class UnitCreate(BaseModel):
    unit_number: str
    property_id: str
    floor: Optional[int] = None
    bedrooms: int = 1
    bathrooms: int = 1
    size_sqm: Optional[float] = None
    rent_amount: float
    deposit_amount: float = 0
    status: UnitStatus = UnitStatus.VACANT
    description: Optional[str] = None
    amenities: Optional[str] = None
    photo_url: Optional[str] = None


class UnitUpdate(BaseModel):
    unit_number: Optional[str] = None
    floor: Optional[int] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    size_sqm: Optional[float] = None
    rent_amount: Optional[float] = None
    deposit_amount: Optional[float] = None
    status: Optional[UnitStatus] = None
    description: Optional[str] = None
    amenities: Optional[str] = None
    photo_url: Optional[str] = None


class UnitResponse(BaseModel):
    id: str
    unit_number: str
    property_id: str
    floor: Optional[int] = None
    bedrooms: int
    bathrooms: int
    size_sqm: Optional[float] = None
    rent_amount: float
    deposit_amount: float
    status: UnitStatus
    description: Optional[str] = None
    amenities: Optional[str] = None
    photo_url: Optional[str] = None
    created_at: datetime
    property_name: Optional[str] = None
    tenant_name: Optional[str] = None

    class Config:
        from_attributes = True


# ---- Lease ----
class LeaseCreate(BaseModel):
    unit_id: str
    tenant_id: str
    start_date: date
    end_date: date
    rent_amount: float
    deposit_amount: float = 0
    deposit_paid: bool = False
    status: LeaseStatus = LeaseStatus.ACTIVE
    terms: Optional[str] = None


class LeaseUpdate(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    rent_amount: Optional[float] = None
    deposit_amount: Optional[float] = None
    deposit_paid: Optional[bool] = None
    status: Optional[LeaseStatus] = None
    terms: Optional[str] = None


class LeaseResponse(BaseModel):
    id: str
    unit_id: str
    tenant_id: str
    start_date: date
    end_date: date
    rent_amount: float
    deposit_amount: float
    deposit_paid: bool
    status: LeaseStatus
    terms: Optional[str] = None
    created_at: datetime
    tenant_name: Optional[str] = None
    unit_number: Optional[str] = None
    property_name: Optional[str] = None

    class Config:
        from_attributes = True


# ---- Payment ----
class PaymentCreate(BaseModel):
    lease_id: str
    amount: float
    due_date: Optional[date] = None
    payment_method: PaymentMethod = PaymentMethod.MPESA
    mpesa_phone: Optional[str] = None
    reference: Optional[str] = None
    notes: Optional[str] = None


class PaymentUpdate(BaseModel):
    status: Optional[PaymentStatus] = None
    mpesa_receipt: Optional[str] = None
    transaction_id: Optional[str] = None
    notes: Optional[str] = None


class PaymentResponse(BaseModel):
    id: str
    lease_id: str
    paid_by: str
    amount: float
    payment_date: datetime
    due_date: Optional[date] = None
    payment_method: PaymentMethod
    status: PaymentStatus
    mpesa_receipt: Optional[str] = None
    mpesa_phone: Optional[str] = None
    transaction_id: Optional[str] = None
    reference: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    tenant_name: Optional[str] = None
    unit_number: Optional[str] = None
    property_name: Optional[str] = None

    class Config:
        from_attributes = True


# ---- M-Pesa ----
class MpesaSTKPushRequest(BaseModel):
    phone_number: str
    amount: float
    lease_id: str
    account_reference: Optional[str] = None


class MpesaSTKPushResponse(BaseModel):
    checkout_request_id: str
    response_code: str
    response_description: str
    merchant_request_id: str


class MpesaC2BCallback(BaseModel):
    TransactionType: Optional[str] = None
    TransID: Optional[str] = None
    TransTime: Optional[str] = None
    TransAmount: Optional[float] = None
    BusinessShortCode: Optional[str] = None
    BillRefNumber: Optional[str] = None
    InvoiceNumber: Optional[str] = None
    OrgAccountBalance: Optional[float] = None
    ThirdPartyTransID: Optional[str] = None
    MSISDN: Optional[str] = None
    FirstName: Optional[str] = None
    MiddleName: Optional[str] = None
    LastName: Optional[str] = None


# ---- Maintenance ----
class MaintenanceCreate(BaseModel):
    unit_id: str
    title: str
    description: str
    priority: TicketPriority = TicketPriority.MEDIUM
    photo_url: Optional[str] = None


class MaintenanceUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[TicketPriority] = None
    status: Optional[TicketStatus] = None
    assigned_vendor: Optional[str] = None
    cost: Optional[float] = None
    notes: Optional[str] = None


class MaintenanceResponse(BaseModel):
    id: str
    unit_id: str
    submitted_by: str
    title: str
    description: str
    priority: TicketPriority
    status: TicketStatus
    assigned_vendor: Optional[str] = None
    cost: Optional[float] = None
    photo_url: Optional[str] = None
    resolved_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    submitted_by_name: Optional[str] = None
    unit_number: Optional[str] = None
    property_name: Optional[str] = None

    class Config:
        from_attributes = True


# ---- Document ----
class DocumentCreate(BaseModel):
    name: str
    file_url: str
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    category: str = "general"
    property_id: Optional[str] = None
    unit_id: Optional[str] = None
    lease_id: Optional[str] = None


class DocumentResponse(BaseModel):
    id: str
    name: str
    file_url: str
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    category: str
    property_id: Optional[str] = None
    unit_id: Optional[str] = None
    lease_id: Optional[str] = None
    uploaded_by: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---- Expense ----
class ExpenseCreate(BaseModel):
    property_id: str
    category: str
    description: Optional[str] = None
    amount: float
    expense_date: date
    vendor: Optional[str] = None
    receipt_url: Optional[str] = None


class ExpenseResponse(BaseModel):
    id: str
    property_id: str
    category: str
    description: Optional[str] = None
    amount: float
    expense_date: date
    vendor: Optional[str] = None
    receipt_url: Optional[str] = None
    created_by: str
    created_at: datetime
    property_name: Optional[str] = None

    class Config:
        from_attributes = True


# ---- Reports / Dashboard ----
class DashboardStats(BaseModel):
    total_properties: int = 0
    total_units: int = 0
    occupied_units: int = 0
    vacant_units: int = 0
    occupancy_rate: float = 0.0
    total_tenants: int = 0
    total_revenue: float = 0.0
    pending_payments: float = 0.0
    overdue_payments: int = 0
    active_leases: int = 0
    expiring_leases: int = 0
    open_maintenance: int = 0
    monthly_revenue: List[dict] = []
    recent_payments: List[dict] = []
    recent_maintenance: List[dict] = []
