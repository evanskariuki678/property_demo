from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import init_db, get_db, async_session
from app.models.models import User, UserRole, Property, Unit, UnitStatus, Lease, LeaseStatus, Payment, PaymentStatus, PaymentMethod, MaintenanceRequest, TicketStatus, TicketPriority
from app.utils.auth import get_password_hash
from app.routers import auth, properties, units, leases, payments, maintenance, documents, expenses, mpesa, reports
from sqlalchemy import select
from datetime import date, datetime, timedelta
import uuid


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    async with async_session() as db:
        result = await db.execute(select(User).limit(1))
        if not result.scalars().first():
            await seed_demo_data(db)
    yield


app = FastAPI(title="Kenya Rental Management System", version="1.0.0", lifespan=lifespan)

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(auth.router)
app.include_router(properties.router)
app.include_router(units.router)
app.include_router(leases.router)
app.include_router(payments.router)
app.include_router(maintenance.router)
app.include_router(documents.router)
app.include_router(expenses.router)
app.include_router(mpesa.router)
app.include_router(reports.router)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


async def seed_demo_data(db):
    """Seed the database with demo data for testing."""
    admin = User(
        id=str(uuid.uuid4()),
        email="admin@kenyanrentals.co.ke",
        hashed_password=get_password_hash("admin123"),
        full_name="System Admin",
        phone="+254700000000",
        role=UserRole.ADMIN,
        language="en",
    )
    db.add(admin)

    landlord = User(
        id=str(uuid.uuid4()),
        email="landlord@kenyanrentals.co.ke",
        hashed_password=get_password_hash("landlord123"),
        full_name="James Kamau",
        phone="+254711222333",
        role=UserRole.LANDLORD,
        id_number="12345678",
        kra_pin="A001234567B",
        language="en",
    )
    db.add(landlord)

    agent = User(
        id=str(uuid.uuid4()),
        email="agent@kenyanrentals.co.ke",
        hashed_password=get_password_hash("agent123"),
        full_name="Grace Wanjiku",
        phone="+254722333444",
        role=UserRole.AGENT,
        language="en",
    )
    db.add(agent)

    tenant1 = User(
        id=str(uuid.uuid4()),
        email="tenant@kenyanrentals.co.ke",
        hashed_password=get_password_hash("tenant123"),
        full_name="Peter Omondi",
        phone="+254733444555",
        role=UserRole.TENANT,
        id_number="87654321",
        language="en",
    )
    db.add(tenant1)

    tenant2 = User(
        id=str(uuid.uuid4()),
        email="mary@kenyanrentals.co.ke",
        hashed_password=get_password_hash("tenant123"),
        full_name="Mary Akinyi",
        phone="+254744555666",
        role=UserRole.TENANT,
        id_number="11223344",
        language="sw",
    )
    db.add(tenant2)

    tenant3 = User(
        id=str(uuid.uuid4()),
        email="john@kenyanrentals.co.ke",
        hashed_password=get_password_hash("tenant123"),
        full_name="John Mwangi",
        phone="+254755666777",
        role=UserRole.TENANT,
        language="en",
    )
    db.add(tenant3)

    await db.flush()

    prop1 = Property(
        id=str(uuid.uuid4()),
        name="Sunset Apartments",
        address="123 Kenyatta Avenue, Westlands",
        city="Nairobi",
        county="Nairobi",
        description="Modern apartment complex in the heart of Westlands with 24hr security, ample parking, and backup water supply.",
        property_type="residential",
        total_units=6,
        owner_id=landlord.id,
        manager_id=agent.id,
    )
    db.add(prop1)

    prop2 = Property(
        id=str(uuid.uuid4()),
        name="Green Valley Estate",
        address="45 Ngong Road, Karen",
        city="Nairobi",
        county="Nairobi",
        description="Gated community with spacious units, garden, and children's play area.",
        property_type="residential",
        total_units=4,
        owner_id=landlord.id,
    )
    db.add(prop2)

    prop3 = Property(
        id=str(uuid.uuid4()),
        name="Mombasa Heights",
        address="78 Digo Road, Nyali",
        city="Mombasa",
        county="Mombasa",
        description="Beachside apartments with ocean views.",
        property_type="residential",
        total_units=3,
        owner_id=landlord.id,
        manager_id=agent.id,
    )
    db.add(prop3)

    await db.flush()

    units_data = [
        ("A1", prop1.id, 0, 1, 1, 45.0, 25000, 25000, UnitStatus.OCCUPIED),
        ("A2", prop1.id, 0, 2, 1, 65.0, 35000, 35000, UnitStatus.OCCUPIED),
        ("B1", prop1.id, 1, 1, 1, 45.0, 27000, 27000, UnitStatus.OCCUPIED),
        ("B2", prop1.id, 1, 2, 1, 65.0, 37000, 37000, UnitStatus.VACANT),
        ("C1", prop1.id, 2, 3, 2, 90.0, 55000, 55000, UnitStatus.VACANT),
        ("C2", prop1.id, 2, 3, 2, 90.0, 55000, 55000, UnitStatus.MAINTENANCE),
    ]

    created_units = []
    for unit_num, pid, floor, beds, baths, size, rent, deposit, status in units_data:
        u = Unit(
            id=str(uuid.uuid4()),
            unit_number=unit_num,
            property_id=pid,
            floor=floor,
            bedrooms=beds,
            bathrooms=baths,
            size_sqm=size,
            rent_amount=rent,
            deposit_amount=deposit,
            status=status,
        )
        db.add(u)
        created_units.append(u)

    gv_units = [
        ("GV-1", prop2.id, 0, 3, 2, 120.0, 65000, 65000, UnitStatus.VACANT),
        ("GV-2", prop2.id, 0, 3, 2, 120.0, 65000, 65000, UnitStatus.VACANT),
        ("GV-3", prop2.id, 1, 4, 3, 150.0, 85000, 85000, UnitStatus.VACANT),
        ("GV-4", prop2.id, 1, 4, 3, 150.0, 85000, 85000, UnitStatus.VACANT),
    ]
    for unit_num, pid, floor, beds, baths, size, rent, deposit, status in gv_units:
        u = Unit(
            id=str(uuid.uuid4()),
            unit_number=unit_num,
            property_id=pid,
            floor=floor,
            bedrooms=beds,
            bathrooms=baths,
            size_sqm=size,
            rent_amount=rent,
            deposit_amount=deposit,
            status=status,
        )
        db.add(u)
        created_units.append(u)

    mh_units = [
        ("MH-1", prop3.id, 0, 2, 1, 70.0, 40000, 40000, UnitStatus.VACANT),
        ("MH-2", prop3.id, 1, 2, 1, 70.0, 42000, 42000, UnitStatus.VACANT),
        ("MH-3", prop3.id, 2, 3, 2, 95.0, 60000, 60000, UnitStatus.VACANT),
    ]
    for unit_num, pid, floor, beds, baths, size, rent, deposit, status in mh_units:
        u = Unit(
            id=str(uuid.uuid4()),
            unit_number=unit_num,
            property_id=pid,
            floor=floor,
            bedrooms=beds,
            bathrooms=baths,
            size_sqm=size,
            rent_amount=rent,
            deposit_amount=deposit,
            status=status,
        )
        db.add(u)
        created_units.append(u)

    await db.flush()

    today = date.today()
    lease1 = Lease(
        id=str(uuid.uuid4()),
        unit_id=created_units[0].id,
        tenant_id=tenant1.id,
        start_date=today - timedelta(days=180),
        end_date=today + timedelta(days=185),
        rent_amount=25000,
        deposit_amount=25000,
        deposit_paid=True,
        status=LeaseStatus.ACTIVE,
        terms="12-month lease. Rent due on 1st of every month.",
    )
    db.add(lease1)

    lease2 = Lease(
        id=str(uuid.uuid4()),
        unit_id=created_units[1].id,
        tenant_id=tenant2.id,
        start_date=today - timedelta(days=90),
        end_date=today + timedelta(days=275),
        rent_amount=35000,
        deposit_amount=35000,
        deposit_paid=True,
        status=LeaseStatus.ACTIVE,
    )
    db.add(lease2)

    lease3 = Lease(
        id=str(uuid.uuid4()),
        unit_id=created_units[2].id,
        tenant_id=tenant3.id,
        start_date=today - timedelta(days=30),
        end_date=today + timedelta(days=335),
        rent_amount=27000,
        deposit_amount=27000,
        deposit_paid=False,
        status=LeaseStatus.ACTIVE,
    )
    db.add(lease3)

    await db.flush()

    payment_records = [
        (lease1.id, tenant1.id, 25000, today - timedelta(days=60), PaymentStatus.COMPLETED, PaymentMethod.MPESA, "QKJ3X7Y9Z1"),
        (lease1.id, tenant1.id, 25000, today - timedelta(days=30), PaymentStatus.COMPLETED, PaymentMethod.MPESA, "RHL4W8X2A3"),
        (lease1.id, tenant1.id, 25000, today - timedelta(days=5), PaymentStatus.COMPLETED, PaymentMethod.MPESA, "SMN5V9Y3B4"),
        (lease2.id, tenant2.id, 35000, today - timedelta(days=60), PaymentStatus.COMPLETED, PaymentMethod.MPESA, "TNP6U0Z4C5"),
        (lease2.id, tenant2.id, 35000, today - timedelta(days=30), PaymentStatus.COMPLETED, PaymentMethod.BANK_TRANSFER, None),
        (lease2.id, tenant2.id, 35000, today, PaymentStatus.PENDING, PaymentMethod.MPESA, None),
        (lease3.id, tenant3.id, 27000, today - timedelta(days=2), PaymentStatus.COMPLETED, PaymentMethod.MPESA, "VQR8S2B6E7"),
    ]

    for lease_id, tenant_id, amount, pdate, pstatus, method, receipt in payment_records:
        p = Payment(
            id=str(uuid.uuid4()),
            lease_id=lease_id,
            paid_by=tenant_id,
            amount=amount,
            payment_date=datetime.combine(pdate, datetime.min.time()),
            due_date=pdate,
            payment_method=method,
            status=pstatus,
            mpesa_receipt=receipt,
            transaction_id=str(uuid.uuid4())[:12].upper() if pstatus == PaymentStatus.COMPLETED else None,
        )
        db.add(p)

    maint1 = MaintenanceRequest(
        id=str(uuid.uuid4()),
        unit_id=created_units[0].id,
        submitted_by=tenant1.id,
        title="Leaking Kitchen Faucet",
        description="The kitchen faucet has been dripping constantly for the past week.",
        priority=TicketPriority.HIGH,
        status=TicketStatus.IN_PROGRESS,
        assigned_vendor="Kamau Plumbing Services",
        cost=3500,
    )
    db.add(maint1)

    maint2 = MaintenanceRequest(
        id=str(uuid.uuid4()),
        unit_id=created_units[1].id,
        submitted_by=tenant2.id,
        title="Broken Window Lock",
        description="The bedroom window lock is broken and cannot be secured.",
        priority=TicketPriority.URGENT,
        status=TicketStatus.OPEN,
    )
    db.add(maint2)

    maint3 = MaintenanceRequest(
        id=str(uuid.uuid4()),
        unit_id=created_units[2].id,
        submitted_by=tenant3.id,
        title="Paint Peeling in Bathroom",
        description="The bathroom ceiling paint is peeling due to moisture.",
        priority=TicketPriority.LOW,
        status=TicketStatus.COMPLETED,
        assigned_vendor="Quality Painters Ltd",
        cost=8000,
        resolved_at=datetime.utcnow() - timedelta(days=5),
    )
    db.add(maint3)

    await db.commit()
