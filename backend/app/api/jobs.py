
import logging
import uuid
from pathlib import Path
from typing import Literal
from app.services.audio_processing import (
    process_audio,
    AudioProcessingError,
)
import httpx
from app.services.transcription import TranscriptionService, TranscriptionError
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database import get_db
from app.models import Job
from app.schemas import JobResponse, TranscriptionResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])

# N8N Webhook Notification Function
async def notify_n8n_audio_processed(
    job_id: str,
    source_type: str,
) -> None:
    """
    Notify n8n after audio preprocessing and database persistence.
    """

    if not settings.n8n_webhook_url:
        logger.warning("n8n webhook URL is not configured.")
        return

    payload = {
        "job_id": job_id,
        "event": "audio_processed",
        "source_type": source_type,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                settings.n8n_webhook_url,
                json=payload,
            )
            response.raise_for_status()

        logger.info(
            "n8n notified successfully for job %s",
            job_id,
        )

    except httpx.HTTPError:
        logger.exception(
            "Could not notify n8n for job %s",
            job_id,
        )
# Upload Audio Endpoint
@router.post(
    "/upload",
    response_model=JobResponse,
    status_code=201,
)
async def upload_audio(
    file: UploadFile = File(...),
    source_type: Literal["upload", "microphone"] = Form(...),
    db: Session = Depends(get_db),
):
    """Upload an audio file, process it, and create a job record in the database."""
    # 1. Validate filename
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required.",
        )

    original_name = Path(file.filename).name
    extension = Path(original_name).suffix.lower()

    # 2. Validate extension
    if extension not in settings.allowed_audio_extensions:
        raise HTTPException(
            status_code=400,
            detail="Unsupported audio file extension.",
        )

    # 3. Prepare storage
    audio_original_dir = settings.storage_dir / "audio" / "originals"
    audio_processed_dir = settings.storage_dir / "audio" / "processed"

    audio_original_dir.mkdir(parents=True, exist_ok=True)
    audio_processed_dir.mkdir(parents=True, exist_ok=True)

    job_id = str(uuid.uuid4())
    stored_filename = f"{job_id}{extension}"
    final_path = audio_original_dir / stored_filename
    processed_path = audio_processed_dir / f"{job_id}.wav"

    file_size = 0
    max_size = settings.max_upload_size_mb * 1024 * 1024

    try:
        # 4. Save audio in chunks
        with final_path.open("wb") as destination:
            while True:
                chunk = file.file.read(
                    settings.upload_chunk_size
                )

                if not chunk:
                    break

                file_size += len(chunk)

                if file_size > max_size:
                    raise HTTPException(
                        status_code=413,
                        detail="Audio file exceeds maximum allowed size.",
                    )

                destination.write(chunk)

        # 5. Reject empty files
        if file_size == 0:
            raise HTTPException(
                status_code=400,
                detail="Audio file is empty.",
            )
        try:
            # Process the audio file and get metadata
            metadata = process_audio(
                input_path=final_path,
                output_path=processed_path,
            )
            print(f"Audio processed successfully: {metadata}")
        except AudioProcessingError as e:
            logger.error(f"Audio processing failed: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Audio processing failed: {e}",
            )
            
        
        # 6. Create database record
        job = Job(
            id=job_id,
            original_name=original_name,
            stored_filename=stored_filename,
            content_type=file.content_type or "application/octet-stream",
            size_byte=file_size,
            storage_path=str(final_path),
            processed_path=str(processed_path) if metadata else None,
            source_type=source_type,
            duration_seconds=metadata.duration_seconds if metadata else None,
            status="audio_processed" if metadata else "uploaded",
            error_message=None,
        )

        db.add(job)
        db.commit()
        db.refresh(job)

        await notify_n8n_audio_processed(job_id=job.id, source_type=source_type)
        # 7. Return created job
        return JobResponse.model_validate(job)

    except HTTPException:
        db.rollback()
        final_path.unlink(missing_ok=True)
        processed_path.unlink(missing_ok=True)
        raise
    except Exception as exc:
        db.rollback()
        final_path.unlink(missing_ok=True)
        processed_path.unlink(missing_ok=True)

        logger.exception("Audio upload failed")

        raise HTTPException(
            status_code=500,
            detail="Could not save the audio file.",
        ) from exc

    finally:
        await file.close()

@router.post(
    "/{job_id}/transcribe", response_model=TranscriptionResponse)
def transcribe_audio(
    job_id: str,
    db: Session = Depends(get_db),
):
    # Retrieve the job from the database
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found.",
        )
    if job.status == "transcribed":
        return TranscriptionResponse(
            job_id=job.id,
            status=job.status,
            language=job.detected_language,
            language_probability=job.language_probability,
            duration_seconds=job.duration_seconds,
            text=job.transcript_text,
            segments=job.transcription_segments or [],
        )
    if job.status not in ("audio_processed", "transcription_failed"):
        raise HTTPException(
            status_code=400,
            detail=f"Job is not ready for transcription. Current status: {job.status}",
        )
    if not job.processed_path:
        raise HTTPException(
            status_code=400,
            detail="Processed audio file not found.",
        )
    processed_path = Path(job.processed_path)
    if not processed_path.exists() or not processed_path.is_file():
        raise HTTPException(
            status_code=400,
            detail="Processed audio file is missing or invalid.",
        )
    try:
        transcription_service = TranscriptionService()
        transcription_result = transcription_service.transcribe(
            audio_path=job.processed_path
        )

        # Update the job with transcription results
        job.transcript_text = transcription_result.text
        job.detected_language = transcription_result.language
        job.language_probability = transcription_result.language_probability
        job.duration_seconds = transcription_result.duration_seconds
        job.transcription_segments = [
            segment.__dict__ for segment in transcription_result.segments
        ]
        job.status = "transcribed"
        db.commit()
        db.refresh(job)

        return TranscriptionResponse(
            job_id=job.id,
            status=job.status,
            language=job.detected_language,
            language_probability=job.language_probability,
            duration_seconds=job.duration_seconds,
            text=job.transcript_text,
            segments=job.transcription_segments or [],
        )

    except TranscriptionError as e:
        logger.error(f"Transcription failed for job {job_id}: {e}")
        job.status = "transcription_failed"
        job.error_message = str(e)
        db.commit()
        db.refresh(job)

        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {e}",
        )
    except Exception as exc:
        print(f"TRANSCRIPTION DEBUG ERROR: {type(exc).__name__}: {exc!r}")
        db.rollback()

        logger.exception(
            "Transcription failed for job %s",
            job_id,
        )

        job = db.get(Job, job_id)
        if job is not None:
            job.status = "transcription_failed"
            job.error_message = "Internal transcription error."
            db.commit()

        raise HTTPException(
            status_code=500,
            detail="An internal transcription error occurred.",
        ) from exc
