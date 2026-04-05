from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.models import MaintenanceRequest, Unit, Property, User, UserRole, TicketStatus
from app.schemas.schemas import MaintenanceCreate, MaintenanceUpdate, MaintenanceResponse
from app.utils.auth import get_current_user, require_roles

router = APIRouter(prefix="/api/maintenance", tags=["maintenance"])


async def enrich_maintenance(req: MaintenanceRequest, db: AsyncSession) -> MaintenanceResponse:
    user_result = await db.execute(select(User.full_name).where(User.id == req.submitted_by))
    submitted_by_name = user_result.scalar_one_or_none()

    unit_result = await db.execute(select(Unit).where(Unit.id == req.unit_id))
    unit = unit_result.scalar_one_or_none()
    unit_number = unit.unit_number if unit else None

    property_name = None
    if unit:
        prop_result = await db.execute(select(Property.name).where(Property.id == unit.property_id))
        property_name = prop_result.scalar_one_or_none()

    resp = MaintenanceResponse.model_validate(req)
    resp.submitted_by_name = submitted_by_name
    resp.unit_number = unit_number
    resp.property_name = property_name
    return resp


@router.get("", response_model=list[MaintenanceResponse])
async def list_maintenance(
    status: str | None = None,
    unit_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(MaintenanceRequest)

    if current_user.role == UserRole.TENANT:
        query = query.where(MaintenanceRequest.submitted_by == current_user.id)
    elif current_user.role == UserRole.LANDLORD:
        query = query.join(Unit).join(Property).where(Property.owner_id == current_user.id)
    elif current_user.role == UserRole.AGENT:
        query = query.join(Unit).join(Property).where(
            (Property.manager_id == current_user.id) | (Property.owner_id == current_user.id)
        )

    if status:
        query = query.where(MaintenanceRequest.status == status)
    if unit_id:
        query = query.where(MaintenanceRequest.unit_id == unit_id)

    query = query.order_by(MaintenanceRequest.created_at.desc())
    result = await db.execute(query)
    requests = result.scalars().all()
    return [await enrich_maintenance(r, db) for r in requests]


@router.post("", response_model=MaintenanceResponse)
async def create_maintenance(
    data: MaintenanceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    req = MaintenanceRequest(
        unit_id=data.unit_id,
        submitted_by=current_user.id,
        title=data.title,
        description=data.description,
        priority=data.priority,
        photo_url=data.photo_url,
    )
    db.add(req)
    await db.commit()
    await db.refresh(req)
    return await enrich_maintenance(req, db)


@router.get("/{request_id}", response_model=MaintenanceResponse)
async def get_maintenance(
    request_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(MaintenanceRequest).where(MaintenanceRequest.id == request_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Maintenance request not found")
    return await enrich_maintenance(req, db)


@router.put("/{request_id}", response_model=MaintenanceResponse)
async def update_maintenance(
    request_id: str,
    data: MaintenanceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(MaintenanceRequest).where(MaintenanceRequest.id == request_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Maintenance request not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(req, key, value)

    if data.status == TicketStatus.COMPLETED:
        req.resolved_at = datetime.utcnow()

    await db.commit()
    await db.refresh(req)
    return await enrich_maintenance(req, db)


@router.delete("/{request_id}")
async def delete_maintenance(
    request_id: str,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.LANDLORD, UserRole.AGENT)),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(MaintenanceRequest).where(MaintenanceRequest.id == request_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Maintenance request not found")
    await db.delete(req)
    await db.commit()
    return {"detail": "Maintenance request deleted"}
