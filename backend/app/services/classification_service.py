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

def submit_batch_classifications(
    db: Session,
    document_id: str,
    batch_id: str,
    classifications: list[dict],
) -> list[DocumentSegment]:
    """
    Submit user classifications for all segments in a batch.

    Each decision is saved separately.
    AI suggestions remain unchanged.
    """

    # 1. Retrieve batch
    batch = db.scalar(
        select(DocumentBatch).where(
            DocumentBatch.id == batch_id,
            DocumentBatch.document_id == document_id,
        )
    )

    if batch is None:
        raise ValueError("Batch not found.")

    if batch.status == "completed":
        raise ValueError("This batch has already been completed.")

    # 2. Validate batch size
    if not 1 <= len(classifications) <= 5:
        raise ValueError("A submission must contain between 1 and 5 classifications.")

    # 3. Check for duplicate segment IDs
    segment_ids = [item["segment_id"] for item in classifications]

    if len(segment_ids) != len(set(segment_ids)):
        raise ValueError("Duplicate segment IDs are not allowed.")

    # 4. Retrieve all segments belonging to this batch
    segments = list(
        db.scalars(
            select(DocumentSegment).where(
                DocumentSegment.document_id == document_id,
                DocumentSegment.batch_id == batch_id,
            )
        ).all()
    )

    segment_map = {segment.id: segment for segment in segments}

    # 5. Validate every classification before changing anything
    allowed_types = {
        "title", "subtitle", "heading", "subheading",
        "paragraph", "definition", "example", "quotation",
        "list_item", "question", "answer",
        "exercise_instruction", "table", "conclusion", "other",
    }

    for item in classifications:
        if item["segment_id"] not in segment_map:
            raise ValueError(
                f"Segment {item['segment_id']} does not belong to this batch."
            )

        if item["selected_type"] not in allowed_types:
            raise ValueError("Invalid classification type.")

    try:
        updated_segments = []

        # 6. Apply user decisions and record revisions
        for item in classifications:
            segment = segment_map[item["segment_id"]]
            selected_type = item["selected_type"]

            old_value = {
                "selected_type": segment.selected_type,
                "classification_source": segment.classification_source,
                "classification_status": segment.classification_status,
            }

            segment.selected_type = selected_type
            segment.classification_source = "user"
            segment.classification_status = "confirmed"

            revision = DocumentRevision(
                document_id=document_id,
                segment_id=segment.id,
                action="classification_changed",
                old_value=old_value,
                new_value={
                    "selected_type": selected_type,
                    "classification_source": "user",
                    "classification_status": "confirmed",
                },
                description=item.get("comment"),
            )

            db.add(revision)
            updated_segments.append(segment)

        # 7. Mark batch completed only if every segment is confirmed
        all_confirmed = all(
            segment.classification_status == "confirmed"
            for segment in segments
        )

        if all_confirmed:
            batch.status = "completed"
        else:
            batch.status = "in_progress"

        db.commit()

        for segment in updated_segments:
            db.refresh(segment)

        return updated_segments

    except Exception:
        db.rollback()
        raise