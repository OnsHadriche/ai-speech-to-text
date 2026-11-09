
import logging
import uuid
from pathlib import Path
from typing import Literal

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
from app.schemas import JobResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])


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
    audio_dir = settings.storage_dir / "audio"/"originals"
    audio_dir.mkdir(parents=True, exist_ok=True)

    job_id = str(uuid.uuid4())
    stored_filename = f"{job_id}{extension}"
    final_path = audio_dir / stored_filename

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

        # 6. Create database record
        job = Job(
            id=job_id,
            original_name=original_name,
            stored_filename=stored_filename,
            content_type=file.content_type or "application/octet-stream",
            size_byte=file_size,
            storage_path=str(final_path),
            source_type=source_type,
            duration_seconds=None,
            status="uploaded",
            error_message=None,
        )

        db.add(job)
        db.commit()
        db.refresh(job)

        # 7. Return created job
        return JobResponse.model_validate(job)

    except HTTPException:
        db.rollback()
        final_path.unlink(missing_ok=True)
        raise

    except Exception as exc:
        db.rollback()
        final_path.unlink(missing_ok=True)

        logger.exception("Audio upload failed")

        raise HTTPException(
            status_code=500,
            detail="Could not save the audio file.",
        ) from exc

    finally:
        await file.close()
