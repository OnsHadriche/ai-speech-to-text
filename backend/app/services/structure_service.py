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
def merge_segments(
    db: Session,
    document_id: str,
    segment_ids: list[str],
    separator: str = "\n\n",
) -> DocumentSegment:
    """
    Merge adjacent segments into one segment.

    The first segment is preserved.
    Other merged segments are deleted.
    The original transcription remains unchanged.
    """

    # 1. Validate input
    if len(segment_ids) < 2:
        raise ValueError("At least two segments are required.")

    if len(segment_ids) != len(set(segment_ids)):
        raise ValueError("Duplicate segment IDs are not allowed.")

    # 2. Retrieve segments in document order
    segments = list(
        db.scalars(
            select(DocumentSegment)
            .where(
                DocumentSegment.document_id == document_id,
                DocumentSegment.id.in_(segment_ids),
            )
            .order_by(DocumentSegment.position)
        ).all()
    )

    if len(segments) != len(segment_ids):
        raise ValueError("One or more segments were not found.")

    # 3. Verify adjacency and hierarchy
    positions = [segment.position for segment in segments]

    if positions != list(range(positions[0], positions[0] + len(positions))):
        raise ValueError("Only adjacent segments can be merged.")

    parent_ids = {segment.parent_id for segment in segments}

    if len(parent_ids) > 1:
        raise ValueError("Segments must have the same parent.")

    if any(
        segment.id in {other.parent_id for other in segments}
        for segment in segments
    ):
        raise ValueError("Parent and child segments cannot be merged.")

    first_segment = segments[0]
    old_values = [
        {
            "id": segment.id,
            "original_text": segment.original_text,
            "position": segment.position,
        }
        for segment in segments
    ]

    # 4. Combine the text in document order
    merged_text = separator.join(
        segment.original_text for segment in segments
    )

    old_batch_ids = {
        segment.batch_id for segment in segments
        if segment.batch_id is not None
    }

    try:
        # 5. Invalidate affected batches and release their segments
        for batch_id in old_batch_ids:
            batch = db.get(DocumentBatch, batch_id)

            if batch:
                batch.status = "skipped"

            affected_segments = list(
                db.scalars(
                    select(DocumentSegment).where(
                        DocumentSegment.batch_id == batch_id
                    )
                ).all()
            )

            for affected in affected_segments:
                affected.batch_id = None

        # 6. Update the first segment
        first_segment.original_text = merged_text
        first_segment.batch_id = None
        first_segment.suggested_type = None
        first_segment.suggestion_confidence = None
        first_segment.suggestion_reason = None
        first_segment.selected_type = None
        first_segment.classification_source = None
        first_segment.classification_status = "awaiting_confirmation"

        # 7. Delete the remaining segments
        removed_ids = {
            segment.id for segment in segments[1:]
        }

        for segment in segments[1:]:
            db.delete(segment)

        # 8. Shift following positions
        shift = len(segments) - 1

        following_segments = list(
            db.scalars(
                select(DocumentSegment)
                .where(
                    DocumentSegment.document_id == document_id,
                    DocumentSegment.position > positions[-1],
                )
                .order_by(DocumentSegment.position)
            ).all()
        )

        for following in following_segments:
            following.position -= shift

        # 9. Record revision history
        revision = DocumentRevision(
            document_id=document_id,
            segment_id=first_segment.id,
            action="segments_merged",
            old_value={"segments": old_values},
            new_value={
                "original_text": merged_text,
                "position": first_segment.position,
                "removed_segment_ids": list(removed_ids),
            },
            description="User merged adjacent document segments.",
        )

        db.add(revision)

        # 10. Commit changes
        db.commit()
        db.refresh(first_segment)

        return first_segment

    except Exception:
        db.rollback()
        raise