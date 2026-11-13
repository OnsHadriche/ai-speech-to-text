
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models import Job
from sqlalchemy import or_, func

STALE_TIMEOUT_MINUTES = 30
MAX_TRANSCRIPTION_ATTEMPTS = 3


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
