from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.models import Unit, Property, Lease, LeaseStatus, User, UserRole
from app.schemas.schemas import UnitCreate, UnitUpdate, UnitResponse
from app.utils.auth import get_current_user, require_roles

router = APIRouter(prefix="/api/units", tags=["units"])


async def enrich_unit(unit: Unit, db: AsyncSession) -> UnitResponse:
    prop_result = await db.execute(select(Property.name).where(Property.id == unit.property_id))
    property_name = prop_result.scalar_one_or_none()

    tenant_name = None
    lease_result = await db.execute(
        select(Lease).where(Lease.unit_id == unit.id, Lease.status == LeaseStatus.ACTIVE)
    )
    active_lease = lease_result.scalar_one_or_none()
    if active_lease:
        tenant_result = await db.execute(select(User.full_name).where(User.id == active_lease.tenant_id))
        tenant_name = tenant_result.scalar_one_or_none()

    resp = UnitResponse.model_validate(unit)
    resp.property_name = property_name
    resp.tenant_name = tenant_name
    return resp


@router.get("", response_model=list[UnitResponse])
async def list_units(
    property_id: str | None = None,
    status: str | None = None,
    search: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Unit)
    if property_id:
        query = query.where(Unit.property_id == property_id)
    if status:
        query = query.where(Unit.status == status)
    if search:
        query = query.where(Unit.unit_number.ilike(f"%{search}%"))

    if current_user.role == UserRole.LANDLORD:
        query = query.join(Property).where(Property.owner_id == current_user.id)
    elif current_user.role == UserRole.AGENT:
        query = query.join(Property).where(
            (Property.manager_id == current_user.id) | (Property.owner_id == current_user.id)
        )
    elif current_user.role == UserRole.TENANT:
        query = (
            query.join(Lease, Lease.unit_id == Unit.id)
            .where(Lease.tenant_id == current_user.id)
        )

    query = query.order_by(Unit.created_at.desc())
    result = await db.execute(query)
    units = result.scalars().all()
    return [await enrich_unit(u, db) for u in units]


@router.post("", response_model=UnitResponse)
async def create_unit(
    data: UnitCreate,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.LANDLORD, UserRole.AGENT)),
    db: AsyncSession = Depends(get_db)
):
    unit = Unit(**data.model_dump())
    db.add(unit)
    await db.commit()
    await db.refresh(unit)

    # Update property total_units
    prop_result = await db.execute(select(Property).where(Property.id == data.property_id))
    prop = prop_result.scalar_one_or_none()
    if prop:
        count_result = await db.execute(select(func.count()).where(Unit.property_id == prop.id))
        prop.total_units = count_result.scalar() or 0
        await db.commit()

    return await enrich_unit(unit, db)


@router.get("/{unit_id}", response_model=UnitResponse)
async def get_unit(
    unit_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Unit).where(Unit.id == unit_id))
    unit = result.scalar_one_or_none()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    return await enrich_unit(unit, db)


@router.put("/{unit_id}", response_model=UnitResponse)
async def update_unit(
    unit_id: str,
    data: UnitUpdate,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.LANDLORD, UserRole.AGENT)),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Unit).where(Unit.id == unit_id))
    unit = result.scalar_one_or_none()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(unit, key, value)
    await db.commit()
    await db.refresh(unit)
    return await enrich_unit(unit, db)


@router.delete("/{unit_id}")
async def delete_unit(
    unit_id: str,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.LANDLORD)),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Unit).where(Unit.id == unit_id))
    unit = result.scalar_one_or_none()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    prop_id = unit.property_id
    await db.delete(unit)
    await db.commit()

    prop_result = await db.execute(select(Property).where(Property.id == prop_id))
    prop = prop_result.scalar_one_or_none()
    if prop:
        count_result = await db.execute(select(func.count()).where(Unit.property_id == prop.id))
        prop.total_units = count_result.scalar() or 0
        await db.commit()

    return {"detail": "Unit deleted"}
