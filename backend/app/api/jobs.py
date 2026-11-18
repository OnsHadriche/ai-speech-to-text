
import logging
import uuid
from pathlib import Path
from typing import Literal
from app.services.audio_processing import (
    process_audio,
    AudioProcessingError,
)
import httpx
import time
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
from sqlalchemy import update, func
from app.core.config import settings
from app.database import get_db
from app.models import Job
from app.schemas import JobResponse, TranscriptionResponse, TranscriptionFailureRequest
from app.services.transcription_recovery import (
    recover_stale_transcriptions,
    find_pending_audio_jobs,
)
from app.core.security import verify_recovery_api_key




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
            logger.info("Audio processed successfully| Job ID: %s, job_id| duration=%.2fs", job_id, metadata.duration_seconds)
        except AudioProcessingError as e:
            logger.exception("Audio processing failed | Job ID: %s, error=%s", job_id, str(e))
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

        logger.exception(
            "Audio upload failed | job_id=%s | filename=%s",
            job_id,
            original_name,
        )
        raise HTTPException(
            status_code=500,
            detail="Could not save the audio file.",
        ) from exc

    finally:
        await file.close()


@router.post(
    "/{job_id}/transcribe",
    response_model=TranscriptionResponse,
)
def transcribe_audio(
    job_id: str,
    db: Session = Depends(get_db),
):
    # 1. Retrieve job
    job = db.query(Job).filter(Job.id == job_id).first()

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found.",
        )

    # 2. Return existing result if already transcribed
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

    # 3. Validate job status
    if job.status not in ("audio_processed", "transcription_failed"):
        raise HTTPException(
            status_code=409,
            detail=f"Job cannot be transcribed. Current status: {job.status}",
        )

    # 4. Validate processed audio
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

    # 5. Atomically claim the job
    claim = db.execute(
        update(Job)
        .where(
            Job.id == job_id,
            Job.status.in_(["audio_processed", "transcription_failed"]),
            Job.transcription_attempts < settings.max_transcription_attempts,
        )
        .values(
            status="transcribing",
            error_message=None,
            transcription_attempts=Job.transcription_attempts + 1,
            updated_at=func.now(),
        )
        .execution_options(synchronize_session=False)
    )

    if claim.rowcount != 1:
        db.rollback()

        db.expire_all()
        current_job = db.query(Job).filter(Job.id == job_id).first()

        if current_job and current_job.status == "transcribed":
            return TranscriptionResponse(
                job_id=current_job.id,
                status=current_job.status,
                language=current_job.detected_language,
                language_probability=current_job.language_probability,
                duration_seconds=current_job.duration_seconds,
                text=current_job.transcript_text,
                segments=current_job.transcription_segments or [],
            )
        if current_job and current_job.transcription_attempts >= settings.max_transcription_attempts:
            raise HTTPException(
                status_code=409,
                detail="Maximum transcription attempts reached for this job.",
            )

        raise HTTPException(
            status_code=409,
            detail="This job is already being processed or cannot be claimed.",
        )

    # Commit the status before starting the model
    db.commit()

    try:
        # 6. Run transcription
        transcription_service = TranscriptionService()
        transcription_start = time.perf_counter()
        transcription_result = transcription_service.transcribe(
            audio_path=str(processed_path),
        )

        # 7. Save transcription results
        job = db.query(Job).filter(Job.id == job_id).first()

        if job is None:
            raise RuntimeError("Job disappeared during transcription.")

        job.transcript_text = transcription_result.text
        job.detected_language = transcription_result.language
        job.language_probability = transcription_result.language_probability
        job.duration_seconds = transcription_result.duration_seconds

        job.transcription_segments = [
            segment.__dict__
            for segment in transcription_result.segments
        ]
        job.status = "transcribed"
        job.error_message = None

        db.commit()
        db.refresh(job)

        transcription_duration = time.perf_counter() - transcription_start

        logger.info(
            "Transcription completed | job_id=%s | duration=%.2fs | detected_language=%s | language_probability=%.4f",
            job_id,
            transcription_duration,
            job.detected_language,
            job.language_probability,
        )

        return TranscriptionResponse(
            job_id=job.id,
            status=job.status,
            language=job.detected_language,
            language_probability=job.language_probability,
            duration_seconds=job.duration_seconds,
            text=job.transcript_text,
            segments=job.transcription_segments or [],
        )

    except TranscriptionError as exc:
        db.rollback()

        logger.exception(
            "Transcription failed | job_id=%s | error_type=%s",
            job_id,
            type(exc).__name__,
        )

        job = db.query(Job).filter(Job.id == job_id).first()

        if job:
            job.status = ("transcription_failed" if job.transcription_attempts < settings.max_transcription_attempts else "failed_permanently")
            job.error_message = str(exc)
            job.updated_at = func.now()
            db.commit()

        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {exc}",
        ) from exc

    except Exception as exc:
        db.rollback()

        logger.exception(
            "Unexpected transcription error | job_id=%s | error_type=%s",
            job_id,
            type(exc).__name__,
        )

        job = db.query(Job).filter(Job.id == job_id).first()

        if job:
            job.status = ("transcription_failed" if job.transcription_attempts < settings.max_transcription_attempts else "failed_permanently")
            job.error_message = "Internal transcription error."
            job.updated_at = func.now()
            db.commit()

        raise HTTPException(
            status_code=500,
            detail="An internal transcription error occurred.",
        ) from exc





@router.post("/{job_id}/transcription-failed")
def mark_transcription_failed(
    job_id: str,
    payload: TranscriptionFailureRequest,
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == job_id).first()

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    if job.status in ("transcribed", "failed_permanently"):
        raise HTTPException(
            status_code=409,
            detail="Job is already transcribed or permanently failed.",
        )

    job.status = "transcription_failed"
    job.error_message = payload.error_message

    db.commit()
    db.refresh(job)

    return {
        "job_id": job.id,
        "status": job.status,
        "error_message": job.error_message,
    }

@router.post("/maintenance/recover-stale-transcriptions", dependencies=[Depends(verify_recovery_api_key)])
def recover_stale_transcriptions_endpoint(
    db: Session = Depends(get_db),
):
    try:
        result = recover_stale_transcriptions(db)

        logger.info(
            "Transcription recovery completed: %s",
            result,
        )

        return {
            "success": True,
            **result,
        }

    except Exception:
        db.rollback()
        logger.exception("Transcription recovery failed")

        raise HTTPException(
            status_code=500,
            detail="Transcription recovery failed.",
        )

@router.post(
    "/maintenance/recover-pending-audio",
    dependencies=[Depends(verify_recovery_api_key)],
)
def recover_pending_audio_endpoint(
    db: Session = Depends(get_db),
):
    try:
        result = find_pending_audio_jobs(db)

        logger.info(
            "Pending audio recovery check completed: %s",
            result,
        )

        return {
            "success": True,
            **result,
        }

    except Exception:
        db.rollback()

        logger.exception("Pending audio recovery check failed")

        raise HTTPException(
            status_code=500,
            detail="Pending audio recovery failed.",
        )
