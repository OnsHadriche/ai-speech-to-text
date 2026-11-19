import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.document import Document
from app.schemas.document import DocumentCreate, DocumentResponse
from app.services.document_service import create_document_from_job
from app.services.document_analysis_service import analyze_document
from app.services.batch_service import get_next_batch_for_review
from app.services.ai.graph import educational_agent

from app.schemas.batch import BatchSubmissionRequest
from app.services.classification_service import (
    submit_batch_classifications,
)
from app.services.ai.batch_response_node import (
    process_batch_response_node,
)
from app.services.document_validation_service import finalize_document

logger = logging.getLogger(__name__)

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

@router.post("/{document_id}/analyze")
def analyze_document_endpoint(
    document_id: str,
    batch_size: int = Query(default=4, ge=3, le=5),
    db: Session = Depends(get_db),
):
    try:
        result = analyze_document(
            db=db,
            document_id=document_id,
            batch_size=batch_size,
        )

        document = result["document"]

        return {
            "message": "Educational document analyzed successfully.",
            "document": {
                "id": document.id,
                "title": document.title,
                "subject": document.subject,
                "topic": document.topic,
                "document_type": document.document_type,
                "language": document.language,
                "status": document.status,
            },
            "total_segments": result["total_segments"],
            "total_batches": result["total_batches"],
            "batches": [
                {
                    "id": batch.id,
                    "batch_number": batch.batch_number,
                    "status": batch.status,
                }
                for batch in result["batches"]
            ],
        }

    except ValueError as error:
        message = str(error)
        status_code = (
            status.HTTP_404_NOT_FOUND
            if "not found" in message.lower()
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(
            status_code=status_code,
            detail=message,
        )

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Educational document analysis failed.",
        ) from error


@router.get("/{document_id}/batches/next")
def get_next_classification_batch(
    document_id: str,
    db: Session = Depends(get_db),
):
    try:
        # 1. Retrieve the next batch from PostgreSQL
        result = get_next_batch_for_review(
            db=db,
            document_id=document_id,
        )

        # 2. No more batches to review
        if result is None:
            document = db.scalar(
                select(Document).where(Document.id == document_id)
            )

            if document is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found.",
                )

            document.status = "classification_completed"

            try:
                db.commit()
                db.refresh(document)
            except Exception:
                db.rollback()
                raise

            return {
                "document_id": document_id,
                "status": document.status,
                "message": "All classification batches have been completed.",
                "batch": None,
                "segments": [],
            }

        batch = result["batch"]
        segments = result["segments"]

        # 3. Prepare data for LangGraph
        graph_input = {
            "document_id": document_id,
            "current_mode": "PRESENT_BATCH",
            "current_batch_index": 0,
            "batches": [
                {
                    "id": batch.id,
                    "batch_number": batch.batch_number,
                    "status": batch.status,
                    "segments": [
                        {
                            "id": segment.id,
                            "position": segment.position,
                            "original_text": segment.original_text,
                            "suggested_type": segment.suggested_type,
                            "suggestion_confidence": (
                                segment.suggestion_confidence
                            ),
                            "suggestion_reason": (
                                segment.suggestion_reason
                            ),
                            "selected_type": segment.selected_type,
                            "classification_status": (
                                segment.classification_status
                            ),
                        }
                        for segment in segments
                    ],
                }
            ],
        }

        # 4. Invoke the LangGraph presentation node
        agent_result = educational_agent.invoke(graph_input)

        # 5. Return the presentation data
        review_segments = agent_result.get("review_segments", [])

        return {
            "document_id": document_id,
            "status": batch.status,
            "batch": {
                "id": batch.id,
                "batch_number": batch.batch_number,
                "status": batch.status,
            },
            "total_segments": len(review_segments),
            "segments": review_segments,
        }

    except ValueError as error:
        message = str(error)

        status_code = (
            status.HTTP_404_NOT_FOUND
            if "not found" in message.lower()
            else status.HTTP_400_BAD_REQUEST
        )

        raise HTTPException(
            status_code=status_code,
            detail=message,
        )

    except Exception as error:
        logger.exception(
            "Failed to retrieve classification batch."
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve classification batch.",
        ) from error


@router.post("/{document_id}/batches/{batch_id}/classifications")
def submit_classification_batch(
    document_id: str,
    batch_id: str,
    payload: BatchSubmissionRequest,
    db: Session = Depends(get_db),
):
    """
    Submit user classifications for every segment in a batch.

    Validation is performed by LangGraph and the database service.
    User classifications are persisted in PostgreSQL.
    """

    from app.models.document_batch import DocumentBatch
    from app.models.document_segment import DocumentSegment

    try:
        # 1. Verify the batch belongs to the document
        batch = db.scalar(
            select(DocumentBatch).where(
                DocumentBatch.id == batch_id,
                DocumentBatch.document_id == document_id,
            )
        )

        if batch is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Batch not found for this document.",
            )

        # 2. Reject batches that cannot receive classifications
        if batch.status in ("completed", "skipped"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Batch cannot be submitted because its status is '{batch.status}'.",
            )

        # 3. Load all segments belonging to the batch
        batch_segments = list(
            db.scalars(
                select(DocumentSegment)
                .where(
                    DocumentSegment.document_id == document_id,
                    DocumentSegment.batch_id == batch_id,
                )
                .order_by(DocumentSegment.position)
            ).all()
        )

        if not batch_segments:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This batch contains no segments.",
            )

        # 4. Convert request to dictionaries
        classifications = [
            item.model_dump()
            for item in payload.classifications
        ]

        # 5. Build LangGraph validation state
        graph_state = {
            "document_id": document_id,
            "current_batch_id": batch_id,
            "current_batch_index": 0,
            "current_mode": "PROCESS_BATCH_RESPONSE",
            "review_segments": [
                {
                    "id": segment.id,
                    "position": segment.position,
                    "original_text": segment.original_text,
                    "suggested_type": segment.suggested_type,
                    "suggestion_confidence": (
                        segment.suggestion_confidence
                    ),
                    "suggestion_reason": (
                        segment.suggestion_reason
                    ),
                    "selected_type": segment.selected_type,
                    "classification_status": (
                        segment.classification_status
                    ),
                }
                for segment in batch_segments
            ],
            "user_classifications": classifications,
        }

        # 6. Validate completeness and classification types using LangGraph
        validated_state = process_batch_response_node(
            graph_state
        )

        validated_classifications = (
            validated_state["user_classifications"]
        )

        # 7. Persist validated decisions in PostgreSQL
        updated_segments = submit_batch_classifications(
            db=db,
            document_id=document_id,
            batch_id=batch_id,
            classifications=classifications,
        )

        # 8. Retrieve updated batch status
        db.refresh(batch)

        # 9. Return the result
        return {
            "message": "Classifications submitted successfully.",
            "document_id": document_id,
            "batch": {
                "id": batch.id,
                "batch_number": batch.batch_number,
                "status": batch.status,
            },
            "submitted_count": len(updated_segments),
            "confirmed_count": sum(
                1
                for segment in batch_segments
                if segment.classification_status == "confirmed"
            ),
            "classifications": [
                {
                    "segment_id": segment.id,
                    "selected_type": segment.selected_type,
                    "classification_source": (
                        segment.classification_source
                    ),
                    "classification_status": (
                        segment.classification_status
                    ),
                }
                for segment in updated_segments
            ],
            "next_batch_index": validated_state[
                "current_batch_index"
            ],
        }

    except HTTPException:
        raise

    except ValueError as error:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )

    except Exception as error:
        db.rollback()

        logger.exception(
            "Failed to submit batch classifications."
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit batch classifications.",
        ) from error

@router.post("/{document_id}/finalize")
def finalize_document_endpoint(
    document_id: str,
    db: Session = Depends(get_db),
):
    try:
        document = finalize_document(
            db=db,
            document_id=document_id,
        )

        return {
            "document_id": document.id,
            "status": document.status,
            "message": "Document successfully finalized and ready for generation.",
        }

    except ValueError as error:
        message = str(error)

        status_code = (
            status.HTTP_404_NOT_FOUND
            if "not found" in message.lower()
            else status.HTTP_400_BAD_REQUEST
        )

        raise HTTPException(
            status_code=status_code,
            detail=message,
        )

    except Exception as error:
        logger.exception("Failed to finalize document.")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to finalize document.",
        ) from error