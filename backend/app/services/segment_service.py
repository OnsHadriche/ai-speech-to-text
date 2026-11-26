from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_segment import DocumentSegment


STRUCTURAL_SEGMENT_TYPES = {
    "title",
    "subtitle",
    "heading",
    "subheading",
}


def create_segments_from_analysis(
    db: Session,
    document_id,
    segments: list[dict],
) -> list[DocumentSegment]:
    """
    Create document segments and persist their hierarchical relationships.

    AI parent references use zero-based segment indexes.
    Database relationships use parent UUIDs.
    """

    document = db.scalar(
        select(Document).where(Document.id == document_id)
    )

    if document is None:
        raise ValueError(f"Document {document_id} not found")

    if not segments:
        raise ValueError("Cannot create segments from empty analysis")

    created_segments: list[DocumentSegment] = []

    try:
        # --------------------------------------------------
        # PASS 1: Create all segments
        # --------------------------------------------------
        for position, item in enumerate(segments, start=1):
            original_text = item.get("original_text")

            if not original_text or not original_text.strip():
                raise ValueError(
                    f"Segment at position {position} has empty text"
                )

            confidence = item.get("suggestion_confidence")

            if confidence is not None and not 0 <= confidence <= 1:
                raise ValueError(
                    f"Invalid confidence score at position {position}"
                )

            segment = DocumentSegment(
                document_id=document_id,
                position=position,
                original_text=original_text,
                suggested_type=item.get("suggested_type"),
                suggestion_confidence=confidence,
                suggestion_reason=item.get("suggestion_reason"),
                classification_status="awaiting_confirmation",
                selected_type=None,
                classification_source=None,
                parent_id=None,
            )

            db.add(segment)
            created_segments.append(segment)

        # Generate database IDs before assigning parent relationships.
        db.flush()

        # --------------------------------------------------
        # PASS 2: Assign hierarchical parent relationships
        # --------------------------------------------------
        for child_index, item in enumerate(segments):
            parent_index = item.get("parent_segment_index")

            # No parent means the segment is top-level.
            if parent_index is None:
                continue

            # Validate the parent index.
            if not isinstance(parent_index, int):
                raise ValueError(
                    f"Invalid parent index for segment {child_index}"
                )

            if parent_index < 0 or parent_index >= len(segments):
                raise ValueError(
                    f"Parent index {parent_index} is out of range "
                    f"for segment {child_index}"
                )

            if parent_index == child_index:
                raise ValueError(
                    f"Segment {child_index} cannot be its own parent"
                )

            # Parent must appear before the child.
            if parent_index >= child_index:
                raise ValueError(
                    f"Parent segment {parent_index} must appear before "
                    f"child segment {child_index}"
                )

            parent_item = segments[parent_index]
            parent_type = parent_item.get("suggested_type")

            # Normalize enum values if necessary.
            parent_type = getattr(parent_type, "value", parent_type)

            if parent_type not in STRUCTURAL_SEGMENT_TYPES:
                raise ValueError(
                    f"Segment {parent_index} is not a valid structural parent"
                )

            child_segment = created_segments[child_index]
            parent_segment = created_segments[parent_index]

            child_segment.parent_id = parent_segment.id

        # --------------------------------------------------
        # COMMIT
        # --------------------------------------------------
        db.commit()

        for segment in created_segments:
            db.refresh(segment)

        return created_segments

    except Exception:
        db.rollback()
        raise