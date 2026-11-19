
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_segment import DocumentSegment
from app.models.job import Job

from backend.ai.analysis_service import (
    analyze_educational_transcript,
)
from app.services.segment_service import (
    create_segments_from_analysis,
)
from app.services.batch_service import (
    create_classification_batches,
)


def analyze_document(
    db: Session,
    document_id: str,
    batch_size: int = 4,
) -> dict:
    """
    Analyze an educational document and persist its segments and batches.

    Groq handles semantic analysis.
    PostgreSQL stores the permanent document structure.
    """

    # 1. Retrieve document
    document = db.scalar(
        select(Document).where(Document.id == document_id)
    )

    if document is None:
        raise ValueError("Document not found.")

    if document.status == "analyzing":
        raise ValueError("Document analysis is already in progress.")

    # 2. Prevent duplicate analysis
    existing_segments = db.scalars(
        select(DocumentSegment).where(
            DocumentSegment.document_id == document_id
        )
    ).first()

    if existing_segments is not None:
        raise ValueError(
            "This document has already been analyzed."
        )

    # 3. Retrieve original transcription
    job = db.scalar(
        select(Job).where(Job.id == document.job_id)
    )

    if job is None:
        raise ValueError("Transcription job not found.")

    transcript = job.transcript_text

    if not transcript or not transcript.strip():
        raise ValueError(
            "The transcription is empty or unavailable."
        )

    # 4. Update document status
    document.status = "analyzing"
    db.commit()

    try:
        # 5. Analyze transcription using Groq
        analysis = analyze_educational_transcript(transcript)

        # 6. Save document metadata
        document.title = analysis.document_title
        document.subject = analysis.subject
        document.topic = analysis.topic
        document.document_type = analysis.document_type

        db.commit()

        # 7. Persist detected segments
        segments_data = [
            segment.model_dump()
            for segment in analysis.segments
        ]

        segments = create_segments_from_analysis(
            db=db,
            document_id=document_id,
            segments=segments_data,
        )

        # 8. Create classification batches
        batches = create_classification_batches(
            db=db,
            document_id=document_id,
            batch_size=batch_size,
        )

        # 9. Update final analysis status
        document = db.scalar(
            select(Document).where(Document.id == document_id)
        )

        document.status = "classification_in_progress"
        db.commit()
        db.refresh(document)

        return {
            "document": document,
            "segments": segments,
            "batches": batches,
            "total_segments": len(segments),
            "total_batches": len(batches),
        }

    except Exception:
        db.rollback()

        document = db.scalar(
            select(Document).where(Document.id == document_id)
        )

        if document is not None:
            document.status = "failed"
            db.commit()

        raise
