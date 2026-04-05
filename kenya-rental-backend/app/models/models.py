import uuid
from datetime import datetime, date
from sqlalchemy import (
    Column, String, Float, Integer, Boolean, DateTime, Date, Text,
    ForeignKey, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from app.database import Base
import enum


def gen_uuid():
    return str(uuid.uuid4())


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    LANDLORD = "landlord"
    AGENT = "agent"
    TENANT = "tenant"


class UnitStatus(str, enum.Enum):
    VACANT = "vacant"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"


class LeaseStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"
    PENDING = "pending"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class PaymentMethod(str, enum.Enum):
    MPESA = "mpesa"
    BANK_TRANSFER = "bank_transfer"
    CARD = "card"
    CASH = "cash"


class TicketStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TicketPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.TENANT)
    id_number = Column(String, nullable=True)
    kra_pin = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    language = Column(String, default="en")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    properties_owned = relationship("Property", back_populates="owner", foreign_keys="Property.owner_id")
    properties_managed = relationship("Property", back_populates="manager", foreign_keys="Property.manager_id")
    leases = relationship("Lease", back_populates="tenant", foreign_keys="Lease.tenant_id")
    maintenance_requests = relationship("MaintenanceRequest", back_populates="submitted_by_user", foreign_keys="MaintenanceRequest.submitted_by")
    payments = relationship("Payment", back_populates="paid_by_user", foreign_keys="Payment.paid_by")


class Property(Base):
    __tablename__ = "properties"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    city = Column(String, nullable=False, default="Nairobi")
    county = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    property_type = Column(String, default="residential")
    total_units = Column(Integer, default=0)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    manager_id = Column(String, ForeignKey("users.id"), nullable=True)
    photo_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="properties_owned", foreign_keys=[owner_id])
    manager = relationship("User", back_populates="properties_managed", foreign_keys=[manager_id])
    units = relationship("Unit", back_populates="property", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="property", cascade="all, delete-orphan")


class Unit(Base):
    __tablename__ = "units"

    id = Column(String, primary_key=True, default=gen_uuid)
    unit_number = Column(String, nullable=False)
    property_id = Column(String, ForeignKey("properties.id"), nullable=False)
    floor = Column(Integer, nullable=True)
    bedrooms = Column(Integer, default=1)
    bathrooms = Column(Integer, default=1)
    size_sqm = Column(Float, nullable=True)
    rent_amount = Column(Float, nullable=False)
    deposit_amount = Column(Float, default=0)
    status = Column(SQLEnum(UnitStatus), default=UnitStatus.VACANT)
    description = Column(Text, nullable=True)
    amenities = Column(Text, nullable=True)
    photo_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    property = relationship("Property", back_populates="units")
    leases = relationship("Lease", back_populates="unit", cascade="all, delete-orphan")
    maintenance_requests = relationship("MaintenanceRequest", back_populates="unit", cascade="all, delete-orphan")


class Lease(Base):
    __tablename__ = "leases"

    id = Column(String, primary_key=True, default=gen_uuid)
    unit_id = Column(String, ForeignKey("units.id"), nullable=False)
    tenant_id = Column(String, ForeignKey("users.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    rent_amount = Column(Float, nullable=False)
    deposit_amount = Column(Float, default=0)
    deposit_paid = Column(Boolean, default=False)
    status = Column(SQLEnum(LeaseStatus), default=LeaseStatus.PENDING)
    terms = Column(Text, nullable=True)
    document_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    unit = relationship("Unit", back_populates="leases")
    tenant = relationship("User", back_populates="leases", foreign_keys=[tenant_id])
    payments = relationship("Payment", back_populates="lease", cascade="all, delete-orphan")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True, default=gen_uuid)
    lease_id = Column(String, ForeignKey("leases.id"), nullable=False)
    paid_by = Column(String, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    payment_date = Column(DateTime, default=datetime.utcnow)
    due_date = Column(Date, nullable=True)
    payment_method = Column(SQLEnum(PaymentMethod), default=PaymentMethod.MPESA)
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING)
    mpesa_receipt = Column(String, nullable=True)
    mpesa_phone = Column(String, nullable=True)
    transaction_id = Column(String, nullable=True, unique=True)
    reference = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    lease = relationship("Lease", back_populates="payments")
    paid_by_user = relationship("User", back_populates="payments", foreign_keys=[paid_by])


class MaintenanceRequest(Base):
    __tablename__ = "maintenance_requests"

    id = Column(String, primary_key=True, default=gen_uuid)
    unit_id = Column(String, ForeignKey("units.id"), nullable=False)
    submitted_by = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(SQLEnum(TicketPriority), default=TicketPriority.MEDIUM)
    status = Column(SQLEnum(TicketStatus), default=TicketStatus.OPEN)
    assigned_vendor = Column(String, nullable=True)
    cost = Column(Float, nullable=True)
    photo_url = Column(String, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    unit = relationship("Unit", back_populates="maintenance_requests")
    submitted_by_user = relationship("User", back_populates="maintenance_requests", foreign_keys=[submitted_by])


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    file_url = Column(String, nullable=False)
    file_type = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    category = Column(String, default="general")
    property_id = Column(String, ForeignKey("properties.id"), nullable=True)
    unit_id = Column(String, ForeignKey("units.id"), nullable=True)
    lease_id = Column(String, ForeignKey("leases.id"), nullable=True)
    uploaded_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(String, primary_key=True, default=gen_uuid)
    property_id = Column(String, ForeignKey("properties.id"), nullable=False)
    category = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    amount = Column(Float, nullable=False)
    expense_date = Column(Date, nullable=False)
    vendor = Column(String, nullable=True)
    receipt_url = Column(String, nullable=True)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    property = relationship("Property", back_populates="expenses")
