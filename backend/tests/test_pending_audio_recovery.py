
from datetime import datetime, timedelta, timezone
import uuid

from app.models import Job
from app.services.transcription_recovery import (
    find_pending_audio_jobs,
)


def create_pending_job(
    db_session,
    *,
    attempts=0,
    transcript_text=None,
    processed_path="/tmp/test.wav",
    stale=True,
    status="audio_processed",
):
    job_id = str(uuid.uuid4())

    created_at = (
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
        storage_path="/tmp/test_original.wav",
        processed_path=processed_path,
        status=status,
        transcription_attempts=attempts,
        transcript_text=transcript_text,
        created_at=created_at,
    )

    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    return job


def test_detect_pending_audio_job(db_session):
    job = create_pending_job(db_session)

    result = find_pending_audio_jobs(db_session)

    assert result["pending_count"] == 1
    assert job.id in result["pending_job_ids"]


def test_ignore_job_with_existing_transcript(db_session):
    job = create_pending_job(
        db_session,
        transcript_text="Existing transcript.",
    )

    result = find_pending_audio_jobs(db_session)

    assert result["pending_count"] == 0
    assert job.id not in result["pending_job_ids"]


def test_ignore_job_without_processed_audio(db_session):
    job = create_pending_job(
        db_session,
        processed_path=None,
    )

    result = find_pending_audio_jobs(db_session)

    assert result["pending_count"] == 0
    assert job.id not in result["pending_job_ids"]


def test_ignore_job_after_maximum_attempts(db_session):
    job = create_pending_job(
        db_session,
        attempts=3,
    )

    result = find_pending_audio_jobs(db_session)

    assert result["pending_count"] == 0
    assert job.id not in result["pending_job_ids"]


def test_ignore_recently_created_job(db_session):
    job = create_pending_job(
        db_session,
        stale=False,
    )

    result = find_pending_audio_jobs(db_session)

    assert result["pending_count"] == 0
    assert job.id not in result["pending_job_ids"]


def test_ignore_job_with_unsupported_status(db_session):
    job = create_pending_job(
        db_session,
        status="transcribing",
    )

    result = find_pending_audio_jobs(db_session)

    assert result["pending_count"] == 0
    assert job.id not in result["pending_job_ids"]
