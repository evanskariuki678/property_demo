from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.models import Property, Unit, UnitStatus, User, UserRole
from app.schemas.schemas import PropertyCreate, PropertyUpdate, PropertyResponse
from app.utils.auth import get_current_user, require_roles

router = APIRouter(prefix="/api/properties", tags=["properties"])


async def enrich_property(prop: Property, db: AsyncSession) -> PropertyResponse:
    owner_result = await db.execute(select(User.full_name).where(User.id == prop.owner_id))
    owner_name = owner_result.scalar_one_or_none()

    manager_name = None
    if prop.manager_id:
        mgr_result = await db.execute(select(User.full_name).where(User.id == prop.manager_id))
        manager_name = mgr_result.scalar_one_or_none()

    total_result = await db.execute(select(func.count()).where(Unit.property_id == prop.id))
    total_units = total_result.scalar() or 0

    occupied_result = await db.execute(
        select(func.count()).where(Unit.property_id == prop.id, Unit.status == UnitStatus.OCCUPIED)
    )
    occupied = occupied_result.scalar() or 0

    resp = PropertyResponse.model_validate(prop)
    resp.owner_name = owner_name
    resp.manager_name = manager_name
    resp.total_units = total_units
    resp.occupied_units = occupied
    resp.vacant_units = total_units - occupied
    return resp


@router.get("", response_model=list[PropertyResponse])
async def list_properties(
    search: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Property)
    if current_user.role == UserRole.LANDLORD:
        query = query.where(Property.owner_id == current_user.id)
    elif current_user.role == UserRole.AGENT:
        query = query.where(
            (Property.manager_id == current_user.id) | (Property.owner_id == current_user.id)
        )
    elif current_user.role == UserRole.TENANT:
        # Tenants see properties where they have active leases
        from app.models.models import Lease, LeaseStatus
        query = (
            select(Property)
            .join(Unit, Unit.property_id == Property.id)
            .join(Lease, Lease.unit_id == Unit.id)
            .where(Lease.tenant_id == current_user.id)
        )

    if search:
        query = query.where(
            (Property.name.ilike(f"%{search}%")) | (Property.address.ilike(f"%{search}%"))
        )
    query = query.order_by(Property.created_at.desc())
    result = await db.execute(query)
    properties = result.scalars().all()
    return [await enrich_property(p, db) for p in properties]


@router.post("", response_model=PropertyResponse)
async def create_property(
    data: PropertyCreate,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.LANDLORD, UserRole.AGENT)),
    db: AsyncSession = Depends(get_db)
):
    prop = Property(
        name=data.name,
        address=data.address,
        city=data.city,
        county=data.county,
        description=data.description,
        property_type=data.property_type,
        owner_id=current_user.id,
        manager_id=data.manager_id,
        photo_url=data.photo_url,
    )
    db.add(prop)
    await db.commit()
    await db.refresh(prop)
    return await enrich_property(prop, db)


@router.get("/{property_id}", response_model=PropertyResponse)
async def get_property(
    property_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Property).where(Property.id == property_id))
    prop = result.scalar_one_or_none()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return await enrich_property(prop, db)


@router.put("/{property_id}", response_model=PropertyResponse)
async def update_property(
    property_id: str,
    data: PropertyUpdate,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.LANDLORD, UserRole.AGENT)),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Property).where(Property.id == property_id))
    prop = result.scalar_one_or_none()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    if current_user.role != UserRole.ADMIN and prop.owner_id != current_user.id and prop.manager_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(prop, key, value)
    await db.commit()
    await db.refresh(prop)
    return await enrich_property(prop, db)


@router.delete("/{property_id}")
async def delete_property(
    property_id: str,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.LANDLORD)),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Property).where(Property.id == property_id))
    prop = result.scalar_one_or_none()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    if current_user.role != UserRole.ADMIN and prop.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    await db.delete(prop)
    await db.commit()
    return {"detail": "Property deleted"}
