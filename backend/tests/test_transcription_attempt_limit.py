
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db
from app.models import Job
from app.services.transcription import (
    TranscriptionService,
    TranscriptionError,
)


# --------------------------------------------------
# Database and API fixtures
# --------------------------------------------------

@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# --------------------------------------------------
# Test job factory
# --------------------------------------------------

def create_test_job(db_session, tmp_path, attempts):
    audio_file = tmp_path / f"test_audio_{attempts}.wav"

    # Create a temporary audio file
    audio_file.write_bytes(b"test audio data")

    job = Job(
        id=f"test-attempt-{attempts}",
        original_name="test.wav",
        stored_filename="test.wav",
        content_type="audio/wav",
        source_type="upload",
        size_byte=100,
        storage_path=str(audio_file),
        processed_path=str(audio_file),
        status="transcription_failed",
        transcription_attempts=attempts,
        transcript_text=None,
    )

    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    return job


# --------------------------------------------------
# Test 1: Reject transcription after 3 attempts
# --------------------------------------------------

def test_reject_transcription_after_three_attempts(
    client, db_session, tmp_path
):
    job = create_test_job(
        db_session,
        tmp_path,
        attempts=3,
    )

    response = client.post(
        f"/api/jobs/{job.id}/transcribe"
    )

    db_session.refresh(job)

    assert response.status_code == 409
    assert job.status == "transcription_failed"
    assert job.transcription_attempts == 3


# --------------------------------------------------
# Test 2: Third failed attempt becomes permanent
# --------------------------------------------------

def test_third_failed_attempt_becomes_permanently_failed(
    client, db_session, tmp_path, monkeypatch
):
    job = create_test_job(
        db_session,
        tmp_path,
        attempts=2,
    )

    # Simulate a transcription failure
    def simulate_transcription_failure(self, audio_path):
        raise TranscriptionError(
            "Simulated transcription failure"
        )

    monkeypatch.setattr(
        TranscriptionService,
        "transcribe",
        simulate_transcription_failure,
    )

    response = client.post(
        f"/api/jobs/{job.id}/transcribe"
    )

    db_session.refresh(job)

    assert response.status_code == 500
    assert job.transcription_attempts == 3
    assert job.status == "failed_permanently"
    assert job.error_message is not None

@pytest.mark.parametrize(
    "initial_status",
    ["transcribed", "failed_permanently"],
)
def test_failure_endpoint_cannot_overwrite_final_status(
    client, db_session, tmp_path, initial_status
):
    from uuid import uuid4

    job_id = str(uuid4())
    audio_file = tmp_path / f"{job_id}.wav"
    audio_file.write_bytes(b"test audio")

    job = Job(
        id=job_id,
        original_name="test.wav",
        stored_filename=f"{job_id}.wav",
        content_type="audio/wav",
        source_type="upload",
        size_byte=100,
        storage_path=str(audio_file),
        processed_path=str(audio_file),
        status=initial_status,
        transcription_attempts=3,
        transcript_text=(
            "Existing transcript."
            if initial_status == "transcribed"
            else None
        ),
    )

    db_session.add(job)
    db_session.commit()

    response = client.post(
        f"/api/jobs/{job_id}/transcription-failed",
        json={"error_message": "Simulated n8n failure"},
    )

    db_session.refresh(job)

    assert response.status_code == 409
    assert job.status == initial_status

from sqlalchemy import update, func


def test_atomic_claim_allows_only_one_claim(
    db_session, tmp_path
):
    """Only one atomic update can claim the same job."""

    job = create_test_job(
        db_session,
        tmp_path,
        attempts=0,
    )

    # First request claims the job.
    first_claim = db_session.execute(
        update(Job)
        .where(
            Job.id == job.id,
            Job.status.in_([
                "audio_processed",
                "transcription_failed",
            ]),
            Job.transcription_attempts < 3,
        )
        .values(
            status="transcribing",
            transcription_attempts=(
                Job.transcription_attempts + 1
            ),
            updated_at=func.now(),
        )
    )

    db_session.commit()

    # Second request attempts to claim the same job.
    second_claim = db_session.execute(
        update(Job)
        .where(
            Job.id == job.id,
            Job.status.in_([
                "audio_processed",
                "transcription_failed",
            ]),
            Job.transcription_attempts < 3,
        )
        .values(
            status="transcribing",
            transcription_attempts=(
                Job.transcription_attempts + 1
            ),
            updated_at=func.now(),
        )
    )

    db_session.commit()
    db_session.refresh(job)

    assert first_claim.rowcount == 1
    assert second_claim.rowcount == 0
    assert job.status == "transcribing"
    assert job.transcription_attempts == 1
