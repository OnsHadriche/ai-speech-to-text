
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models import Job


STALE_TIMEOUT_MINUTES = 30
MAX_TRANSCRIPTION_ATTEMPTS = 3


def recover_stale_transcriptions(db: Session) -> dict:
    """
    Find jobs stuck in transcription and prepare them for recovery.

    Jobs with fewer than 3 attempts become eligible for retry.
    Jobs with 3 attempts are marked permanently failed.
    """

    cutoff_time = datetime.now(timezone.utc) - timedelta(
        minutes=STALE_TIMEOUT_MINUTES
    )

    stale_jobs = (
        db.query(Job)
        .filter(
            Job.status == "transcribing",
            Job.updated_at.isnot(None),
            Job.updated_at < cutoff_time,
        )
        .with_for_update(skip_locked=True)
        .all()
    )

    retry_job_ids = []
    permanently_failed_ids = []

    for job in stale_jobs:
        if job.transcription_attempts < MAX_TRANSCRIPTION_ATTEMPTS:
            job.status = "transcription_failed"
            job.error_message = "Transcription timed out. Retry required."

            retry_job_ids.append(job.id)

        else:
            job.status = "failed_permanently"
            job.error_message = (
                "Maximum transcription attempts reached."
            )

            permanently_failed_ids.append(job.id)

    db.commit()

    return {
        "recovered_count": len(retry_job_ids),
        "permanently_failed_count": len(permanently_failed_ids),
        "retry_job_ids": retry_job_ids,
        "permanently_failed_ids": permanently_failed_ids,
    }
