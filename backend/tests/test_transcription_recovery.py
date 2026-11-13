
from datetime import datetime, timedelta, timezone
import uuid

from app.models import Job
from app.services.transcription_recovery import (
    recover_stale_transcriptions,
)


def create_job(
    db_session,
    *,
    status="transcribing",
    attempts=1,
    transcript_text=None,
    stale=True,
):
    job_id = str(uuid.uuid4())

    audio_path = f"/tmp/{job_id}.wav"

    updated_at = (
        datetime.now(timezone.utc) - timedelta(hours=1)
        if stale
        else datetime.now(timezone.utc)
    )

    job = Job(
        id=job_id,
        original_name="test.wav",
        stored_filename=f"{job_id}.wav",
        content_type="audio/wav",
        source_type="upload",
        size_byte=100,
        storage_path=audio_path,
        processed_path=audio_path,
        status=status,
        transcription_attempts=attempts,
        transcript_text=transcript_text,
        updated_at=updated_at,
    )

    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    return job


def test_recover_stale_transcription_job(db_session):
    job = create_job(db_session, attempts=1)

    result = recover_stale_transcriptions(db_session)

    db_session.refresh(job)

    assert result["recovered_count"] == 1
    assert job.id in result["retry_job_ids"]
    assert job.status == "transcription_failed"
    assert job.error_message == "Transcription timed out. Retry required."


def test_mark_job_permanently_failed_after_max_attempts(db_session):
    job = create_job(db_session, attempts=3)

    result = recover_stale_transcriptions(db_session)

    db_session.refresh(job)

    assert result["permanently_failed_count"] == 1
    assert job.id in result["permanently_failed_ids"]
    assert job.status == "failed_permanently"
    assert job.error_message == "Maximum transcription attempts reached."


def test_ignore_job_with_existing_transcript(db_session):
    job = create_job(
        db_session,
        status="transcription_failed",
        attempts=1,
        transcript_text="This transcript already exists.",
    )

    result = recover_stale_transcriptions(db_session)

    db_session.refresh(job)

    assert result["recovered_count"] == 0
    assert result["permanently_failed_count"] == 0
    assert job.status == "transcription_failed"
    assert job.transcript_text == "This transcript already exists."


def test_ignore_recently_updated_job(db_session):
    job = create_job(
        db_session,
        attempts=1,
        stale=False,
    )

    result = recover_stale_transcriptions(db_session)

    db_session.refresh(job)

    assert result["recovered_count"] == 0
    assert result["permanently_failed_count"] == 0
    assert job.status == "transcribing"
