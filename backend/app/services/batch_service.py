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

    if not 3 <= batch_size <= 5:
        raise ValueError("Batch size must be between 3 and 5.")

    document = db.scalar(
        select(Document).where(Document.id == document_id)
    )

    if document is None:
        raise ValueError("Document not found.")

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

    # Calculate balanced batch sizes.
    total = len(segments)
    number_of_batches = (total + batch_size - 1) // batch_size

    base_size, remainder = divmod(total, number_of_batches)

    batch_sizes = [
        base_size + (1 if i < remainder else 0)
        for i in range(number_of_batches)
    ]

    # If fewer than 3 segments exist, keep them in one batch.
    if total < 3:
        batch_sizes = [total]

    try:
        last_batch_number = db.scalar(
            select(func.max(DocumentBatch.batch_number))
            .where(DocumentBatch.document_id == document_id)
        ) or 0

        created_batches = []
        segment_index = 0

        for size in batch_sizes:
            batch = DocumentBatch(
                document_id=document_id,
                batch_number=last_batch_number + 1,
                status="pending",
            )

            db.add(batch)
            db.flush()

            batch_segments = segments[
                segment_index:segment_index + size
            ]

            for segment in batch_segments:
                segment.batch_id = batch.id

            created_batches.append(batch)
            segment_index += size
            last_batch_number += 1

        db.commit()

        for batch in created_batches:
            db.refresh(batch)

        return created_batches

    except Exception:
        db.rollback()
        raise