from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_segment import DocumentSegment


def finalize_document(
    db: Session,
    document_id: str,
) -> Document:
    """
    Validate the document before allowing DOCX generation.

    Every segment must have a user-confirmed classification.
    """

    # 1. Retrieve document
    document = db.scalar(
        select(Document).where(Document.id == document_id)
    )

    if document is None:
        raise ValueError("Document not found.")

    # 2. Retrieve all document segments
    segments = list(
        db.scalars(
            select(DocumentSegment)
            .where(DocumentSegment.document_id == document_id)
            .order_by(DocumentSegment.position)
        ).all()
    )

    if not segments:
        raise ValueError("Cannot finalize a document without segments.")

    # 3. Check classifications
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
            f"{len(unclassified_segments)} segments still require classification."
        )

    # 4. Update document status
    try:
        document.status = "ready_for_generation"

        db.commit()
        db.refresh(document)

        return document

    except Exception:
        db.rollback()
        raise