
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models import Job
from sqlalchemy import or_, func

STALE_TIMEOUT_MINUTES = 30
MAX_TRANSCRIPTION_ATTEMPTS = 3
PENDING_AUDIO_TIMEOUT_MINUTES = 5


def recover_stale_transcriptions(db: Session) -> dict:
    """
    Find stuck or failed transcription jobs and prepare them for recovery.

    Jobs with fewer than 3 attempts become eligible for retry.
    Jobs that have reached 3 attempts are marked permanently failed.
    """

    cutoff_time = datetime.now(timezone.utc) - timedelta(
        minutes=STALE_TIMEOUT_MINUTES
    )

    recoverable_jobs = (
        db.query(Job)
        .filter(
            Job.status.in_(["transcribing", "transcription_failed"]),
            Job.updated_at.isnot(None),
            Job.updated_at < cutoff_time,
            or_(
                Job.transcript_text.is_(None),
                func.trim(Job.transcript_text) == "",
            )
        )
        
        .with_for_update(skip_locked=True)
        .all()
    )

    retry_job_ids = []
    permanently_failed_ids = []

    for job in recoverable_jobs:
        if (job.transcription_attempts or 0) < MAX_TRANSCRIPTION_ATTEMPTS:
            job.status = "transcription_failed"
            job.error_message = "Transcription timed out. Retry required."
            retry_job_ids.append(job.id)

        else:
            job.status = "failed_permanently"
            job.error_message = "Maximum transcription attempts reached."
            permanently_failed_ids.append(job.id)

        # Reset the recovery timer
        job.updated_at = datetime.now(timezone.utc)

    db.commit()

    return {
        "recovered_count": len(retry_job_ids),
        "permanently_failed_count": len(permanently_failed_ids),
        "retry_job_ids": retry_job_ids,
        "permanently_failed_ids": permanently_failed_ids,
    }
    


def find_pending_audio_jobs(db: Session) -> dict:
    """
    Find audio jobs that may not have reached n8n.
    Return their IDs for retry by the n8n workflow.
    """

    cutoff_time = datetime.now(timezone.utc) - timedelta(
        minutes=PENDING_AUDIO_TIMEOUT_MINUTES
    )

    pending_jobs = (
        db.query(Job)
        .filter(
            Job.status == "audio_processed",
            Job.created_at < cutoff_time,
            Job.processed_path.isnot(None),
            Job.transcription_attempts < MAX_TRANSCRIPTION_ATTEMPTS,
            or_(
                Job.transcript_text.is_(None),
                func.trim(Job.transcript_text) == "",
            ),
        )
        .all()
    )

    pending_job_ids = [job.id for job in pending_jobs]

    return {
        "pending_count": len(pending_job_ids),
        "pending_job_ids": pending_job_ids,
    }

