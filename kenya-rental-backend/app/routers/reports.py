from datetime import datetime, timedelta, date
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.database import get_db
from app.models.models import (
    Property, Unit, Lease, Payment, MaintenanceRequest, User, UserRole,
    UnitStatus, LeaseStatus, PaymentStatus, TicketStatus
)
from app.schemas.schemas import DashboardStats
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/reports", tags=["reports"])


def _get_prop_ids_subquery(user: User):
    """Return a subquery of property IDs visible to the user."""
    q = select(Property.id)
    if user.role == UserRole.LANDLORD:
        q = q.where(Property.owner_id == user.id)
    elif user.role == UserRole.AGENT:
        q = q.where((Property.manager_id == user.id) | (Property.owner_id == user.id))
    return q


def _get_unit_ids_subquery(user: User):
    """Return a subquery of unit IDs visible to the user."""
    prop_ids = _get_prop_ids_subquery(user).subquery()
    return select(Unit.id).where(Unit.property_id.in_(select(prop_ids)))


def _get_lease_ids_subquery(user: User):
    """Return a subquery of lease IDs visible to the user."""
    unit_ids = _get_unit_ids_subquery(user).subquery()
    return select(Lease.id).where(Lease.unit_id.in_(select(unit_ids)))


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    today = date.today()
    is_tenant = current_user.role == UserRole.TENANT
    is_admin = current_user.role == UserRole.ADMIN

    # Property IDs subquery for non-admin/non-tenant
    prop_ids_sq = _get_prop_ids_subquery(current_user).subquery()

    # Total properties
    if is_tenant:
        total_properties = 0
    else:
        pq = select(func.count()).select_from(Property)
        if not is_admin:
            pq = pq.where(Property.id.in_(select(prop_ids_sq)))
        total_properties = (await db.execute(pq)).scalar() or 0

    # Units
    uq_total = select(func.count()).select_from(Unit)
    uq_occupied = select(func.count()).select_from(Unit).where(Unit.status == UnitStatus.OCCUPIED)
    if not is_admin:
        uq_total = uq_total.where(Unit.property_id.in_(select(prop_ids_sq)))
        uq_occupied = uq_occupied.where(Unit.property_id.in_(select(prop_ids_sq)))
    if is_tenant:
        total_units = 0
        occupied_units = 0
    else:
        total_units = (await db.execute(uq_total)).scalar() or 0
        occupied_units = (await db.execute(uq_occupied)).scalar() or 0

    vacant_units = total_units - occupied_units
    occupancy_rate = (occupied_units / total_units * 100) if total_units > 0 else 0

    # Tenants
    if is_tenant:
        total_tenants = 1
    else:
        tq = select(func.count(func.distinct(Lease.tenant_id))).select_from(Lease).where(
            Lease.status == LeaseStatus.ACTIVE
        )
        if not is_admin:
            unit_ids_sq = _get_unit_ids_subquery(current_user).subquery()
            tq = tq.where(Lease.unit_id.in_(select(unit_ids_sq)))
        total_tenants = (await db.execute(tq)).scalar() or 0

    # Revenue (completed payments)
    rev_q = select(func.coalesce(func.sum(Payment.amount), 0)).select_from(Payment).where(
        Payment.status == PaymentStatus.COMPLETED
    )
    if is_tenant:
        rev_q = rev_q.where(Payment.paid_by == current_user.id)
    elif not is_admin:
        lease_ids_sq = _get_lease_ids_subquery(current_user).subquery()
        rev_q = rev_q.where(Payment.lease_id.in_(select(lease_ids_sq)))
    total_revenue = (await db.execute(rev_q)).scalar() or 0

    # Pending payments
    pend_q = select(func.coalesce(func.sum(Payment.amount), 0)).select_from(Payment).where(
        Payment.status == PaymentStatus.PENDING
    )
    if is_tenant:
        pend_q = pend_q.where(Payment.paid_by == current_user.id)
    elif not is_admin:
        lease_ids_sq = _get_lease_ids_subquery(current_user).subquery()
        pend_q = pend_q.where(Payment.lease_id.in_(select(lease_ids_sq)))
    pending_payments = (await db.execute(pend_q)).scalar() or 0

    # Overdue payments
    overdue_q = select(func.count()).select_from(Payment).where(
        Payment.status == PaymentStatus.PENDING,
        Payment.due_date < today
    )
    if is_tenant:
        overdue_q = overdue_q.where(Payment.paid_by == current_user.id)
    overdue_payments = (await db.execute(overdue_q)).scalar() or 0

    # Active leases
    active_q = select(func.count()).select_from(Lease).where(Lease.status == LeaseStatus.ACTIVE)
    if is_tenant:
        active_q = active_q.where(Lease.tenant_id == current_user.id)
    elif not is_admin:
        unit_ids_sq = _get_unit_ids_subquery(current_user).subquery()
        active_q = active_q.where(Lease.unit_id.in_(select(unit_ids_sq)))
    active_leases = (await db.execute(active_q)).scalar() or 0

    # Expiring leases (within 30 days)
    thirty_days = today + timedelta(days=30)
    exp_q = select(func.count()).select_from(Lease).where(
        Lease.status == LeaseStatus.ACTIVE,
        Lease.end_date <= thirty_days,
        Lease.end_date >= today
    )
    if not is_admin:
        unit_ids_sq = _get_unit_ids_subquery(current_user).subquery()
        exp_q = exp_q.where(Lease.unit_id.in_(select(unit_ids_sq)))
    expiring_leases = (await db.execute(exp_q)).scalar() or 0

    # Open maintenance requests
    maint_q = select(func.count()).select_from(MaintenanceRequest).where(
        MaintenanceRequest.status.in_([TicketStatus.OPEN, TicketStatus.IN_PROGRESS])
    )
    if is_tenant:
        maint_q = maint_q.where(MaintenanceRequest.submitted_by == current_user.id)
    elif not is_admin:
        unit_ids_sq = _get_unit_ids_subquery(current_user).subquery()
        maint_q = maint_q.where(MaintenanceRequest.unit_id.in_(select(unit_ids_sq)))
    open_maintenance = (await db.execute(maint_q)).scalar() or 0

    # Monthly revenue (last 6 months)
    monthly_revenue = []
    for i in range(5, -1, -1):
        month_start = (today.replace(day=1) - timedelta(days=30 * i)).replace(day=1)
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1)

        mr_q = select(func.coalesce(func.sum(Payment.amount), 0)).select_from(Payment).where(
            Payment.status == PaymentStatus.COMPLETED,
            Payment.payment_date >= datetime.combine(month_start, datetime.min.time()),
            Payment.payment_date < datetime.combine(month_end, datetime.min.time()),
        )
        if is_tenant:
            mr_q = mr_q.where(Payment.paid_by == current_user.id)
        month_rev = (await db.execute(mr_q)).scalar() or 0
        monthly_revenue.append({
            "month": month_start.strftime("%b %Y"),
            "revenue": float(month_rev)
        })

    # Recent payments (last 5)
    recent_pay_q = select(Payment).where(
        Payment.status == PaymentStatus.COMPLETED
    ).order_by(Payment.payment_date.desc()).limit(5)
    if is_tenant:
        recent_pay_q = recent_pay_q.where(Payment.paid_by == current_user.id)
    recent_pay_result = await db.execute(recent_pay_q)
    recent_payments = []
    for p in recent_pay_result.scalars().all():
        tenant_result = await db.execute(select(User.full_name).where(User.id == p.paid_by))
        tenant_name = tenant_result.scalar_one_or_none() or "Unknown"
        recent_payments.append({
            "id": p.id,
            "tenant": tenant_name,
            "amount": p.amount,
            "date": p.payment_date.isoformat() if p.payment_date else "",
            "method": p.payment_method.value if p.payment_method else "mpesa",
            "status": p.status.value if p.status else "completed",
        })

    # Recent maintenance (last 5)
    recent_maint_q = select(MaintenanceRequest).order_by(
        MaintenanceRequest.created_at.desc()
    ).limit(5)
    if is_tenant:
        recent_maint_q = recent_maint_q.where(MaintenanceRequest.submitted_by == current_user.id)
    recent_maint_result = await db.execute(recent_maint_q)
    recent_maintenance = []
    for m in recent_maint_result.scalars().all():
        user_result = await db.execute(select(User.full_name).where(User.id == m.submitted_by))
        user_name = user_result.scalar_one_or_none() or "Unknown"
        recent_maintenance.append({
            "id": m.id,
            "title": m.title,
            "submitted_by": user_name,
            "status": m.status.value,
            "priority": m.priority.value,
            "date": m.created_at.isoformat() if m.created_at else "",
        })

    return DashboardStats(
        total_properties=total_properties,
        total_units=total_units,
        occupied_units=occupied_units,
        vacant_units=vacant_units,
        occupancy_rate=round(occupancy_rate, 1),
        total_tenants=total_tenants,
        total_revenue=float(total_revenue),
        pending_payments=float(pending_payments),
        overdue_payments=overdue_payments,
        active_leases=active_leases,
        expiring_leases=expiring_leases,
        open_maintenance=open_maintenance,
        monthly_revenue=monthly_revenue,
        recent_payments=recent_payments,
        recent_maintenance=recent_maintenance,
    )
