from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_segment import DocumentSegment
from app.models.document_batch import DocumentBatch
from app.models.document_revision import DocumentRevision


def finalize_document(
    db: Session,
    document_id: str,
) -> Document:
    """
    Validate and finalize an educational document before DOCX generation.

    Requirements:
    - Document must exist.
    - Document must contain segments.
    - Every segment must have a confirmed classification.
    - Every segment must have a selected type.
    - All classification batches must be completed.
    - Document must not already be finalized.

    Finalization is recorded in the revision history.
    """

    try:
        # 1. Retrieve document
        document = db.scalar(
            select(Document).where(Document.id == document_id)
        )

        if document is None:
            raise ValueError("Document not found.")

        # 2. Prevent duplicate finalization
        if document.status == "ready_for_generation":
            raise ValueError("Document is already finalized.")

        # 3. Retrieve all document segments
        segments = list(
            db.scalars(
                select(DocumentSegment)
                .where(DocumentSegment.document_id == document_id)
                .order_by(DocumentSegment.position)
            ).all()
        )

        if not segments:
            raise ValueError(
                "Cannot finalize a document without segments."
            )

        # 4. Validate classifications
        unclassified_segments = [
            segment.id
            for segment in segments
            if (
                segment.classification_status != "confirmed"
                or not segment.selected_type
            )
        ]

        if unclassified_segments:
            raise ValueError(
                f"{len(unclassified_segments)} segments still "
                "require classification."
            )

        # 5. Retrieve document batches
        batches = list(
            db.scalars(
                select(DocumentBatch)
                .where(DocumentBatch.document_id == document_id)
                .order_by(DocumentBatch.batch_number)
            ).all()
        )

        if not batches:
            raise ValueError(
                "Cannot finalize document without classification batches."
            )

        # 6. Validate all batches
        incomplete_batches = [
            batch.batch_number
            for batch in batches
            if batch.status != "completed"
        ]

        if incomplete_batches:
            raise ValueError(
                f"{len(incomplete_batches)} batches are not completed."
            )

        # 7. Validate workflow status
        if document.status != "classification_completed":
            raise ValueError(
                "Document classification workflow is not completed."
            )

        # 8. Save previous status
        previous_status = document.status

        # 9. Update document status
        document.status = "ready_for_generation"

        # 10. Record finalization revision
        revision = DocumentRevision(
            document_id=document.id,
            segment_id=None,
            action="document_finalized",
            old_value={
                "status": previous_status,
            },
            new_value={
                "status": "ready_for_generation",
                "total_segments": len(segments),
                "total_batches": len(batches),
            },
            description=(
                "Document finalized after successful classification "
                "and validation of all segments and batches."
            ),
        )

        db.add(revision)

        # 11. Commit atomically
        db.commit()
        db.refresh(document)

        return document

    except Exception:
        db.rollback()
        raise