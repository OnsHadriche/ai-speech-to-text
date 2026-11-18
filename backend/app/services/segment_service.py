from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_segment import DocumentSegment


def create_segments_from_analysis(
    db: Session,
    document_id: str,
    segments: list[dict],
) -> list[DocumentSegment]:
    """
    Save AI-generated segments for an educational document.

    AI suggestions are stored separately from user decisions.
    Original transcription text is preserved.
    """

    # 1. Retrieve document
    document = db.scalar(
        select(Document).where(Document.id == document_id)
    )

    if document is None:
        raise ValueError("Document not found.")

    if not segments:
        raise ValueError("No segments were provided.")

    created_segments = []

    try:
        # 2. Create segment records
        for position, item in enumerate(segments, start=1):

            original_text = item.get("original_text")

            if not isinstance(original_text, str) or not original_text.strip():
                raise ValueError(
                    f"Segment {position} has invalid original_text."
                )

            confidence = item.get("suggestion_confidence")

            if confidence is not None and not 0 <= confidence <= 1:
                raise ValueError(
                    f"Segment {position} has invalid confidence."
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
            )

            db.add(segment)
            created_segments.append(segment)

        # 3. Save all segments together
        db.commit()

        for segment in created_segments:
            db.refresh(segment)

        return created_segments

    except Exception:
        db.rollback()
        raise