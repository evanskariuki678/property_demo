from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.models import Lease, Unit, Property, User, UserRole, UnitStatus, LeaseStatus
from app.schemas.schemas import LeaseCreate, LeaseUpdate, LeaseResponse
from app.utils.auth import get_current_user, require_roles

router = APIRouter(prefix="/api/leases", tags=["leases"])


async def enrich_lease(lease: Lease, db: AsyncSession) -> LeaseResponse:
    tenant_result = await db.execute(select(User.full_name).where(User.id == lease.tenant_id))
    tenant_name = tenant_result.scalar_one_or_none()

    unit_result = await db.execute(select(Unit).where(Unit.id == lease.unit_id))
    unit = unit_result.scalar_one_or_none()
    unit_number = unit.unit_number if unit else None

    property_name = None
    if unit:
        prop_result = await db.execute(select(Property.name).where(Property.id == unit.property_id))
        property_name = prop_result.scalar_one_or_none()

    resp = LeaseResponse.model_validate(lease)
    resp.tenant_name = tenant_name
    resp.unit_number = unit_number
    resp.property_name = property_name
    return resp


@router.get("", response_model=list[LeaseResponse])
async def list_leases(
    status: str | None = None,
    tenant_id: str | None = None,
    unit_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Lease)

    if current_user.role == UserRole.TENANT:
        query = query.where(Lease.tenant_id == current_user.id)
    elif current_user.role == UserRole.LANDLORD:
        query = query.join(Unit).join(Property).where(Property.owner_id == current_user.id)
    elif current_user.role == UserRole.AGENT:
        query = query.join(Unit).join(Property).where(
            (Property.manager_id == current_user.id) | (Property.owner_id == current_user.id)
        )

    if status:
        query = query.where(Lease.status == status)
    if tenant_id:
        query = query.where(Lease.tenant_id == tenant_id)
    if unit_id:
        query = query.where(Lease.unit_id == unit_id)

    query = query.order_by(Lease.created_at.desc())
    result = await db.execute(query)
    leases = result.scalars().all()
    return [await enrich_lease(l, db) for l in leases]


@router.post("", response_model=LeaseResponse)
async def create_lease(
    data: LeaseCreate,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.LANDLORD, UserRole.AGENT)),
    db: AsyncSession = Depends(get_db)
):
    # Verify unit exists
    unit_result = await db.execute(select(Unit).where(Unit.id == data.unit_id))
    unit = unit_result.scalar_one_or_none()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")

    # Verify tenant exists
    tenant_result = await db.execute(select(User).where(User.id == data.tenant_id))
    tenant = tenant_result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    lease = Lease(**data.model_dump())
    db.add(lease)

    # Update unit status
    if data.status == LeaseStatus.ACTIVE:
        unit.status = UnitStatus.OCCUPIED

    await db.commit()
    await db.refresh(lease)
    return await enrich_lease(lease, db)


@router.get("/{lease_id}", response_model=LeaseResponse)
async def get_lease(
    lease_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Lease).where(Lease.id == lease_id))
    lease = result.scalar_one_or_none()
    if not lease:
        raise HTTPException(status_code=404, detail="Lease not found")
    return await enrich_lease(lease, db)


@router.put("/{lease_id}", response_model=LeaseResponse)
async def update_lease(
    lease_id: str,
    data: LeaseUpdate,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.LANDLORD, UserRole.AGENT)),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Lease).where(Lease.id == lease_id))
    lease = result.scalar_one_or_none()
    if not lease:
        raise HTTPException(status_code=404, detail="Lease not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(lease, key, value)

    # Update unit status based on lease status
    if data.status:
        unit_result = await db.execute(select(Unit).where(Unit.id == lease.unit_id))
        unit = unit_result.scalar_one_or_none()
        if unit:
            if data.status == LeaseStatus.ACTIVE:
                unit.status = UnitStatus.OCCUPIED
            elif data.status in [LeaseStatus.EXPIRED, LeaseStatus.TERMINATED]:
                unit.status = UnitStatus.VACANT

    await db.commit()
    await db.refresh(lease)
    return await enrich_lease(lease, db)


@router.delete("/{lease_id}")
async def delete_lease(
    lease_id: str,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.LANDLORD)),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Lease).where(Lease.id == lease_id))
    lease = result.scalar_one_or_none()
    if not lease:
        raise HTTPException(status_code=404, detail="Lease not found")

    unit_result = await db.execute(select(Unit).where(Unit.id == lease.unit_id))
    unit = unit_result.scalar_one_or_none()
    if unit:
        unit.status = UnitStatus.VACANT

    await db.delete(lease)
    await db.commit()
    return {"detail": "Lease deleted"}
