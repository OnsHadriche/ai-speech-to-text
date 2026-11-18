from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document_segment import DocumentSegment
from app.models.document_revision import DocumentRevision


def correct_segment_text(
    db: Session,
    document_id: str,
    segment_id: str,
    corrected_text: str,
) -> DocumentSegment:
    """
    Correct a document segment while preserving revision history.

    The original transcription in the jobs table remains unchanged.
    """

    # 1. Validate corrected text
    if not isinstance(corrected_text, str) or not corrected_text.strip():
        raise ValueError("Corrected text cannot be empty.")

    # 2. Retrieve segment
    segment = db.scalar(
        select(DocumentSegment).where(
            DocumentSegment.id == segment_id,
            DocumentSegment.document_id == document_id,
        )
    )

    if segment is None:
        raise ValueError("Segment not found.")

    old_text = segment.original_text

    if old_text == corrected_text:
        return segment

    try:
        # 3. Update segment text
        segment.original_text = corrected_text

        # 4. Record the correction
        revision = DocumentRevision(
            document_id=document_id,
            segment_id=segment_id,
            action="text_corrected",
            old_value={"original_text": old_text},
            new_value={"original_text": corrected_text},
            description="User corrected segment transcription.",
        )

        db.add(revision)

        # 5. Save atomically
        db.commit()
        db.refresh(segment)

        return segment

    except Exception:
        db.rollback()
        raise