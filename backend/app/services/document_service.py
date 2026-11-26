from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.document import Document


def create_document_from_job(
    db: Session,
    job_id: str,
    language: str = "ar",
    reviewed_transcript: str | None = None
) -> Document:
    """
    Create an educational document from an existing transcription job.

    The original transcription remains unchanged.
    """

    # 1. Retrieve the transcription job
    job = db.scalar(
        select(Job).where(Job.id == job_id)
    )

    if job is None:
        raise ValueError("Transcription job not found.")

    # 2. Verify that transcription exists
    if not job.transcript_text or not job.transcript_text.strip():
        raise ValueError(
            "The job does not contain a valid transcription."
        )
    transcript = reviewed_transcript or job.transcript_text

    if not transcript or not transcript.strip():
        raise ValueError("Transcript cannot be empty")

    # 3. Prevent duplicate documents
    existing_document = db.scalar(
        select(Document).where(
            Document.job_id == job_id
        )
    )

    if existing_document is not None:
        return existing_document

    # 4. Create the educational document
    document = Document(
        job_id=job.id,
        language=language,
        status="transcribed",
        reviewed_transcript=transcript
    )

    db.add(document)

    try:
        db.commit()
        db.refresh(document)
    except Exception:
        db.rollback()
        raise

    return document