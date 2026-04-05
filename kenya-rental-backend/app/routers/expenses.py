from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.models import Expense, Property, User, UserRole
from app.schemas.schemas import ExpenseCreate, ExpenseResponse
from app.utils.auth import get_current_user, require_roles

router = APIRouter(prefix="/api/expenses", tags=["expenses"])


async def enrich_expense(expense: Expense, db: AsyncSession) -> ExpenseResponse:
    prop_result = await db.execute(select(Property.name).where(Property.id == expense.property_id))
    property_name = prop_result.scalar_one_or_none()
    resp = ExpenseResponse.model_validate(expense)
    resp.property_name = property_name
    return resp


@router.get("", response_model=list[ExpenseResponse])
async def list_expenses(
    property_id: str | None = None,
    category: str | None = None,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.LANDLORD, UserRole.AGENT)),
    db: AsyncSession = Depends(get_db)
):
    query = select(Expense)
    if property_id:
        query = query.where(Expense.property_id == property_id)
    if category:
        query = query.where(Expense.category == category)

    if current_user.role == UserRole.LANDLORD:
        query = query.join(Property).where(Property.owner_id == current_user.id)
    elif current_user.role == UserRole.AGENT:
        query = query.join(Property).where(
            (Property.manager_id == current_user.id) | (Property.owner_id == current_user.id)
        )

    query = query.order_by(Expense.created_at.desc())
    result = await db.execute(query)
    expenses = result.scalars().all()
    return [await enrich_expense(e, db) for e in expenses]


@router.post("", response_model=ExpenseResponse)
async def create_expense(
    data: ExpenseCreate,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.LANDLORD, UserRole.AGENT)),
    db: AsyncSession = Depends(get_db)
):
    expense = Expense(
        property_id=data.property_id,
        category=data.category,
        description=data.description,
        amount=data.amount,
        expense_date=data.expense_date,
        vendor=data.vendor,
        receipt_url=data.receipt_url,
        created_by=current_user.id,
    )
    db.add(expense)
    await db.commit()
    await db.refresh(expense)
    return await enrich_expense(expense, db)


@router.delete("/{expense_id}")
async def delete_expense(
    expense_id: str,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.LANDLORD)),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Expense).where(Expense.id == expense_id))
    expense = result.scalar_one_or_none()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    await db.delete(expense)
    await db.commit()
    return {"detail": "Expense deleted"}
