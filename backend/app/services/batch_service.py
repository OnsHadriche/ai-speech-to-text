from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_segment import DocumentSegment
from app.models.document_batch import DocumentBatch


def create_classification_batches(
    db: Session,
    document_id: str,
    batch_size: int = 4,
) -> list[DocumentBatch]:
    """
    Divide unassigned document segments into classification batches.

    Batch size must be between 3 and 5.
    Existing batches are preserved.
    """

    if not 3 <= batch_size <= 5:
        raise ValueError("Batch size must be between 3 and 5.")

    document = db.scalar(
        select(Document).where(Document.id == document_id)
    )

    if document is None:
        raise ValueError("Document not found.")

    # Retrieve segments that do not belong to a batch yet.
    segments = list(
        db.scalars(
            select(DocumentSegment)
            .where(
                DocumentSegment.document_id == document_id,
                DocumentSegment.batch_id.is_(None),
            )
            .order_by(DocumentSegment.position)
        ).all()
    )

    if not segments:
        return []

    try:
        # Find the last existing batch number.
        last_batch_number = db.scalar(
            select(func.max(DocumentBatch.batch_number))
            .where(DocumentBatch.document_id == document_id)
        ) or 0

        created_batches = []

        # Divide segments into groups.
        for index in range(0, len(segments), batch_size):
            batch_segments = segments[index:index + batch_size]

            batch = DocumentBatch(
                document_id=document_id,
                batch_number=last_batch_number + 1,
                status="pending",
            )

            db.add(batch)

            # Generate the batch ID before assigning it to segments.
            db.flush()

            for segment in batch_segments:
                segment.batch_id = batch.id

            created_batches.append(batch)
            last_batch_number += 1

        db.commit()

        for batch in created_batches:
            db.refresh(batch)

        return created_batches

    except Exception:
        db.rollback()
        raise