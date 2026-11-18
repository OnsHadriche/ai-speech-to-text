from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_segment import DocumentSegment
from app.models.document_batch import DocumentBatch
from app.models.document_revision import DocumentRevision

from app.core.constants import REVISION_ACTIONS


def classify_segment(
    db: Session,
    document_id: str,
    segment_id: str,
    selected_type: str,
    comment: str | None = None,
) -> DocumentSegment:
    """
    Save the user's classification decision.

    Preserve the original AI suggestion.
    Record the user's decision in the revision history.
    """

    # 1. Retrieve the segment
    segment = db.scalar(
        select(DocumentSegment).where(
            DocumentSegment.id == segment_id,
            DocumentSegment.document_id == document_id,
        )
    )

    if segment is None:
        raise ValueError("Segment not found.")

    # 2. Validate classification type
    allowed_types = {
        "title",
        "subtitle",
        "heading",
        "subheading",
        "paragraph",
        "definition",
        "example",
        "quotation",
        "list_item",
        "question",
        "answer",
        "exercise_instruction",
        "table",
        "conclusion",
        "other",
    }

    if selected_type not in allowed_types:
        raise ValueError("Invalid classification type.")

    # 3. Retrieve document
    document = db.get(Document, document_id)

    if document is None:
        raise ValueError("Document not found.")

    # 4. Save the user's decision
    old_value = {
        "selected_type": segment.selected_type,
        "classification_source": segment.classification_source,
        "classification_status": segment.classification_status,
    }

    segment.selected_type = selected_type
    segment.classification_source = "user"
    segment.classification_status = "confirmed"

    new_value = {
        "selected_type": selected_type,
        "classification_source": "user",
        "classification_status": "confirmed",
    }

    # 5. Record the modification
    revision = DocumentRevision(
        document_id=document_id,
        segment_id=segment_id,
        action="classification_changed",
        old_value=old_value,
        new_value=new_value,
        description=comment or "User confirmed segment classification.",
    )

    db.add(revision)

    try:
        db.commit()
        db.refresh(segment)
        return segment

    except Exception:
        db.rollback()
        raise