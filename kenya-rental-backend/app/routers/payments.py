import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.models import Payment, Lease, Unit, Property, User, UserRole, PaymentStatus
from app.schemas.schemas import PaymentCreate, PaymentUpdate, PaymentResponse
from app.utils.auth import get_current_user, require_roles

router = APIRouter(prefix="/api/payments", tags=["payments"])


async def enrich_payment(payment: Payment, db: AsyncSession) -> PaymentResponse:
    tenant_result = await db.execute(select(User.full_name).where(User.id == payment.paid_by))
    tenant_name = tenant_result.scalar_one_or_none()

    lease_result = await db.execute(select(Lease).where(Lease.id == payment.lease_id))
    lease = lease_result.scalar_one_or_none()

    unit_number = None
    property_name = None
    if lease:
        unit_result = await db.execute(select(Unit).where(Unit.id == lease.unit_id))
        unit = unit_result.scalar_one_or_none()
        if unit:
            unit_number = unit.unit_number
            prop_result = await db.execute(select(Property.name).where(Property.id == unit.property_id))
            property_name = prop_result.scalar_one_or_none()

    resp = PaymentResponse.model_validate(payment)
    resp.tenant_name = tenant_name
    resp.unit_number = unit_number
    resp.property_name = property_name
    return resp


@router.get("", response_model=list[PaymentResponse])
async def list_payments(
    lease_id: str | None = None,
    status: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Payment)

    if current_user.role == UserRole.TENANT:
        query = query.where(Payment.paid_by == current_user.id)
    elif current_user.role == UserRole.LANDLORD:
        query = query.join(Lease).join(Unit).join(Property).where(Property.owner_id == current_user.id)
    elif current_user.role == UserRole.AGENT:
        query = query.join(Lease).join(Unit).join(Property).where(
            (Property.manager_id == current_user.id) | (Property.owner_id == current_user.id)
        )

    if lease_id:
        query = query.where(Payment.lease_id == lease_id)
    if status:
        query = query.where(Payment.status == status)

    query = query.order_by(Payment.created_at.desc())
    result = await db.execute(query)
    payments = result.scalars().all()
    return [await enrich_payment(p, db) for p in payments]


@router.post("", response_model=PaymentResponse)
async def create_payment(
    data: PaymentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify lease exists
    lease_result = await db.execute(select(Lease).where(Lease.id == data.lease_id))
    lease = lease_result.scalar_one_or_none()
    if not lease:
        raise HTTPException(status_code=404, detail="Lease not found")

    payment = Payment(
        lease_id=data.lease_id,
        paid_by=current_user.id,
        amount=data.amount,
        due_date=data.due_date,
        payment_method=data.payment_method,
        mpesa_phone=data.mpesa_phone,
        reference=data.reference,
        notes=data.notes,
        transaction_id=str(uuid.uuid4())[:12].upper(),
        status=PaymentStatus.COMPLETED,
        payment_date=datetime.utcnow(),
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return await enrich_payment(payment, db)


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return await enrich_payment(payment, db)


@router.put("/{payment_id}", response_model=PaymentResponse)
async def update_payment(
    payment_id: str,
    data: PaymentUpdate,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.LANDLORD, UserRole.AGENT)),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(payment, key, value)
    await db.commit()
    await db.refresh(payment)
    return await enrich_payment(payment, db)
