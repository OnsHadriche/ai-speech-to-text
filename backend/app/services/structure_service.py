from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document_segment import DocumentSegment
from app.models.document_revision import DocumentRevision
from app.models.document_batch import DocumentBatch

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

def split_segment(
    db: Session,
    document_id: str,
    segment_id: str,
    split_texts: list[str],
) -> list[DocumentSegment]:
    """
    Split one segment into multiple ordered segments.

    New pieces require classification again.
    The original transcription remains unchanged.
    """

    # 1. Validate input
    if len(split_texts) < 2:
        raise ValueError("At least two text parts are required.")

    if any(
        not isinstance(text, str) or not text.strip()
        for text in split_texts
    ):
        raise ValueError("All split parts must contain valid text.")

    # 2. Retrieve original segment
    segment = db.scalar(
        select(DocumentSegment).where(
            DocumentSegment.id == segment_id,
            DocumentSegment.document_id == document_id,
        )
    )

    if segment is None:
        raise ValueError("Segment not found.")

    old_text = segment.original_text
    old_position = segment.position
    old_batch_id = segment.batch_id

    try:
        # 3. If the segment belongs to a batch,
        # release that batch for rebuilding.
        if old_batch_id:
            batch = db.get(DocumentBatch, old_batch_id)

            if batch:
                batch.status = "skipped"

                affected_segments = list(
                    db.scalars(
                        select(DocumentSegment).where(
                            DocumentSegment.batch_id == old_batch_id
                        )
                    ).all()
                )

                for affected in affected_segments:
                    affected.batch_id = None

        # 4. Shift following segments to make room
        following_segments = list(
            db.scalars(
                select(DocumentSegment)
                .where(
                    DocumentSegment.document_id == document_id,
                    DocumentSegment.position > old_position,
                )
                .order_by(DocumentSegment.position.desc())
            ).all()
        )

        shift = len(split_texts) - 1

        for following in following_segments:
            following.position += shift

        # 5. Update the original segment with the first part
        segment.original_text = split_texts[0]
        segment.batch_id = None
        segment.suggested_type = None
        segment.suggestion_confidence = None
        segment.suggestion_reason = None
        segment.selected_type = None
        segment.classification_source = None
        segment.classification_status = "awaiting_confirmation"

        # 6. Create the remaining segments
        new_segments = []

        for index, text in enumerate(split_texts[1:], start=1):
            new_segment = DocumentSegment(
                document_id=document_id,
                position=old_position + index,
                original_text=text,
                classification_status="awaiting_confirmation",
            )

            db.add(new_segment)
            new_segments.append(new_segment)

        db.flush()

        # 7. Record the split operation
        revision = DocumentRevision(
            document_id=document_id,
            segment_id=segment_id,
            action="segment_split",
            old_value={
                "original_text": old_text,
                "position": old_position,
            },
            new_value={
                "parts": split_texts,
                "positions": list(
                    range(old_position, old_position + len(split_texts))
                ),
            },
            description="User split a document segment.",
        )

        db.add(revision)

        # 8. Save all changes
        db.commit()

        db.refresh(segment)

        for new_segment in new_segments:
            db.refresh(new_segment)

        return [segment, *new_segments]

    except Exception:
        db.rollback()
        raise