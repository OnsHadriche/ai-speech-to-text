
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.document import Document
from app.schemas.document import DocumentCreate, DocumentResponse
from app.services.document_service import create_document_from_job


router = APIRouter(
    prefix="/api/documents",
    tags=["Documents"],
)


@router.post(
    "/",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_document(
    payload: DocumentCreate,
    db: Session = Depends(get_db),
):
    """
    Create an educational document from an existing transcription job.
    """

    if payload.language != "ar":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only Arabic educational documents are currently supported.",
        )

    try:
        document = create_document_from_job(
            db=db,
            job_id=payload.job_id,
            language=payload.language,
        )

        return document

    except ValueError as error:
        message = str(error)

        if "not found" in message.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message,
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )


@router.get(
    "/",
    response_model=list[DocumentResponse],
)
def list_documents(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Retrieve educational documents with pagination.
    """

    statement = (
        select(Document)
        .order_by(Document.created_at.desc())
        .offset(skip)
        .limit(limit)
    )

    documents = db.scalars(statement).all()

    return documents


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
)
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
):
    """
    Retrieve one educational document by its ID.
    """

    document = db.scalar(
        select(Document).where(Document.id == document_id)
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Educational document not found.",
        )

    return document
