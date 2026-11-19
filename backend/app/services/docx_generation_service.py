from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document
from app.models.document_segment import DocumentSegment
from app.models.document_revision import DocumentRevision
from app.services.generator.docx_generator import generate_docx


def generate_document(
    db: Session,
    document_id: str,
) -> dict:
    """
    Generate an editable DOCX from a finalized educational document.

    Only user-confirmed classifications are used.
    The original segment text is preserved.
    """

    output_path = (
        settings.storage_dir
        / "documents"
        / f"{document_id}.docx"
    )

    try:
        # 1. Retrieve document
        document = db.scalar(
            select(Document).where(
                Document.id == document_id
            )
        )

        if document is None:
            raise ValueError("Document not found.")

        # 2. Validate document status
        if document.status != "ready_for_generation":
            raise ValueError(
                "Document is not ready for generation."
            )

        # 3. Retrieve segments in original order
        segments = list(
            db.scalars(
                select(DocumentSegment)
                .where(
                    DocumentSegment.document_id == document_id
                )
                .order_by(DocumentSegment.position)
            ).all()
        )

        if not segments:
            raise ValueError(
                "Cannot generate a document without segments."
            )

        # 4. Validate classifications
        unconfirmed_segments = [
            segment.id
            for segment in segments
            if (
                segment.classification_status != "confirmed"
                or not segment.selected_type
            )
        ]

        if unconfirmed_segments:
            raise ValueError(
                f"{len(unconfirmed_segments)} segments "
                "are not confirmed."
            )

        # 5. Prepare generator input
        generator_segments = [
            {
                "original_text": segment.original_text,
                "selected_type": segment.selected_type,
            }
            for segment in segments
        ]

        document_title = (
            document.title
            or document.topic
            or document.subject
            or "Arabic Educational Document"
        )

        # 6. Generate DOCX file
        generated_path = generate_docx(
            title=document_title,
            segments=generator_segments,
            output_path=output_path,
        )

        # 7. Update document status
        previous_status = document.status
        document.status = "generated"

        # 8. Record generation revision
        revision = DocumentRevision(
            document_id=document.id,
            segment_id=None,
            action="document_generated",
            old_value={
                "status": previous_status,
            },
            new_value={
                "status": "generated",
                "file_path": str(generated_path),
                "file_name": generated_path.name,
                "total_segments": len(segments),
            },
            description=(
                "DOCX generated from user-confirmed "
                "educational document segments."
            ),
        )

        db.add(revision)

        # 9. Commit database changes
        db.commit()
        db.refresh(document)

        return {
            "document_id": document.id,
            "status": document.status,
            "file_path": str(generated_path),
            "file_name": generated_path.name,
            "total_segments": len(segments),
        }

    except Exception:
        db.rollback()
        raise