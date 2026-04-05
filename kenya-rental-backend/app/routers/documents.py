from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.models import Document, User, UserRole
from app.schemas.schemas import DocumentCreate, DocumentResponse
from app.utils.auth import get_current_user, require_roles

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    category: str | None = None,
    property_id: str | None = None,
    unit_id: str | None = None,
    lease_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Document)
    if category:
        query = query.where(Document.category == category)
    if property_id:
        query = query.where(Document.property_id == property_id)
    if unit_id:
        query = query.where(Document.unit_id == unit_id)
    if lease_id:
        query = query.where(Document.lease_id == lease_id)

    if current_user.role == UserRole.TENANT:
        query = query.where(Document.uploaded_by == current_user.id)

    query = query.order_by(Document.created_at.desc())
    result = await db.execute(query)
    docs = result.scalars().all()
    return [DocumentResponse.model_validate(d) for d in docs]


@router.post("", response_model=DocumentResponse)
async def create_document(
    data: DocumentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    doc = Document(
        name=data.name,
        file_url=data.file_url,
        file_type=data.file_type,
        file_size=data.file_size,
        category=data.category,
        property_id=data.property_id,
        unit_id=data.unit_id,
        lease_id=data.lease_id,
        uploaded_by=current_user.id,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return DocumentResponse.model_validate(doc)


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if current_user.role != UserRole.ADMIN and doc.uploaded_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    await db.delete(doc)
    await db.commit()
    return {"detail": "Document deleted"}
